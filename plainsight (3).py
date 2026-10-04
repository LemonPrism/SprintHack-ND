#!/usr/bin/env python3
"""
plainsight.py — zero-width Unicode steganography with layered encryption

Encryption stack (when --key is provided)
------------------------------------------
1. PBKDF2-SHA256 (200,000 iterations, 16-byte random salt per message)
   Converts your passphrase into a 256-bit AES key.
   Brute-forcing 200k iterations per guess makes dictionary attacks impractical.

2. AES-256-GCM (12-byte random nonce per message)
   Encrypts the payload. Even if Eve extracts every invisible character,
   she gets ciphertext she cannot read or modify without the key.
   The GCM authentication tag detects tampering.

3. Zero-width Unicode steganography
   The encrypted bytes are encoded as invisible Unicode characters and
   woven between the letters of a natural-looking cover sentence.
   Eve sees ordinary text and has no visible indication a message exists.

Wire format (what's hidden in the cover sentence)
--------------------------------------------------
  WITHOUT --key:  [2-byte length header] [plaintext bytes]
  WITH    --key:  [2-byte length header] [16-byte salt] [12-byte nonce]
                  [AES-256-GCM ciphertext] [16-byte GCM auth tag]

Charset (--chars / --chars auto)
---------------------------------
Derived separately from the encryption key so the two layers are
independent. Knowing the charset mapping does not help decrypt the payload.

Usage
-----
  python plainsight.py encode "secret"
  python plainsight.py --key "passphrase" encode "secret"
  python plainsight.py --key "passphrase" --chars auto encode "secret"
  python plainsight.py --key "passphrase" decode "<encoded text>"
  python plainsight.py --key "passphrase" test "secret"
  python plainsight.py charset

Requirements
------------
  pip install cryptography   # for AES-256-GCM and PBKDF2
  pip install anthropic      # optional — AI-generated cover sentences
"""

import sys, os, struct, random, hashlib, argparse, time, math

# ── Optional dependencies ──────────────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2   import PBKDF2HMAC
    from cryptography.hazmat.primitives               import hashes as _hashes
    _HAVE_CRYPTO = True
except ImportError:
    _HAVE_CRYPTO = False

# ── Invisible Unicode pool (16 chars, all render as nothing) ───────────────────
FULL_POOL: list[str] = [
    "\u200B","\u200C","\u200D","\u2060",
    "\uFEFF","\u2061","\u2062","\u2063",
    "\u2064","\u206A","\u206B","\u206C",
    "\u206D","\u206E","\u206F","\uFFFE",
]
FULL_POOL_SET = set(FULL_POOL)
DEFAULT_CHARS = ["\u200B","\u200C","\u200D","\u2060"]

_CP_NAMES = {
    0x200B:"Zero Width Space",     0x200C:"Zero Width Non-Joiner",
    0x200D:"Zero Width Joiner",    0x2060:"Word Joiner",
    0xFEFF:"ZW No-Break Space",    0x2061:"Function Application",
    0x2062:"Invisible Times",      0x2063:"Invisible Separator",
    0x2064:"Invisible Plus",       0x206A:"Inhibit Sym Swapping",
    0x206B:"Activate Sym Swapping",0x206C:"Inhibit Arabic Form Shaping",
    0x206D:"Activate Arabic Form Shaping",
    0x206E:"National Digit Shapes",0x206F:"Nominal Digit Shapes",
    0xFFFE:"Reverse BOM",
}


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 1 — Charset resolution (key-derived if --chars auto)
# ══════════════════════════════════════════════════════════════════════════════

def resolve_chars(chars_arg, key, pool_size):
    if not chars_arg:
        return list(DEFAULT_CHARS)
    if chars_arg.lower() == "auto":
        return _derive_chars(key, pool_size or 4)
    charset = [chr(int(cp.strip(), 16)) for cp in chars_arg.split(",")]
    _validate_charset(charset)
    return charset

def _derive_chars(key, n):
    if not key:
        raise ValueError("--chars auto requires --key <passphrase>")
    today  = __import__("datetime").date.today().isoformat()
    # Separate HMAC path from the encryption key derivation
    seed   = int.from_bytes(
        hashlib.pbkdf2_hmac("sha256", f"charset:{key}:{today}".encode(), b"plainsight-charset", 1),
        "big"
    )
    pool   = list(FULL_POOL)
    random.Random(seed).shuffle(pool)
    return pool[:n]

def _validate_charset(cs):
    n = len(cs)
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError(f"Charset must have 2, 4, 8, or 16 chars (got {n})")
    if len(set(cs)) != n:
        raise ValueError("Charset contains duplicate codepoints")

def bits_per_slot(charset):
    return int(math.log2(len(charset)))

def charset_info(charset):
    bps   = bits_per_slot(charset)
    parts = [f"U+{ord(c):04X}({_CP_NAMES.get(ord(c),'?')})" for c in charset]
    return f"{len(charset)} chars, {bps} bits/slot: {', '.join(parts)}"


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 2 — AES-256-GCM encryption (requires --key and cryptography library)
# ══════════════════════════════════════════════════════════════════════════════

PBKDF2_ITERS = 200_000   # cost factor — increase for even stronger brute-force resistance
SALT_LEN     = 16        # random per-message salt
NONCE_LEN    = 12        # AES-GCM nonce (96 bits, NIST recommended)
TAG_LEN      = 16        # GCM authentication tag (128 bits)

def _derive_aes_key(passphrase: str, salt: bytes) -> bytes:
    """PBKDF2-SHA256 with high iteration count → 256-bit AES key."""
    if not _HAVE_CRYPTO:
        raise RuntimeError("pip install cryptography  to use --key encryption")
    kdf = PBKDF2HMAC(
        algorithm=_hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERS,
    )
    return kdf.derive(passphrase.encode("utf-8"))

def encrypt_payload(plaintext: str, passphrase: str) -> bytes:
    """
    Returns: salt(16) + nonce(12) + AES-256-GCM( plaintext ) + tag(16)
    Every call produces a different ciphertext even for identical messages
    (random salt + random nonce), preventing pattern analysis.
    """
    salt  = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key   = _derive_aes_key(passphrase, salt)
    ct    = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    # ct already includes the 16-byte GCM tag appended by the library
    return salt + nonce + ct

def decrypt_payload(data: bytes, passphrase: str) -> str:
    """
    Authenticate then decrypt. Raises ValueError on wrong key or tampered data.
    """
    if len(data) < SALT_LEN + NONCE_LEN + TAG_LEN:
        raise ValueError("Ciphertext too short — truncated or wrong --key?")
    salt    = data[:SALT_LEN]
    nonce   = data[SALT_LEN:SALT_LEN + NONCE_LEN]
    ct_tag  = data[SALT_LEN + NONCE_LEN:]
    key     = _derive_aes_key(passphrase, salt)
    try:
        pt = AESGCM(key).decrypt(nonce, ct_tag, None)
    except Exception:
        raise ValueError("Decryption failed — wrong --key or message was tampered with.")
    return pt.decode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 3 — Zero-width Unicode steganography
# ══════════════════════════════════════════════════════════════════════════════

def _bytes_to_bits(data: bytes) -> list[int]:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def _bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for j in range(8):
            bit = bits[i + j] if i + j < len(bits) else 0
            v   = (v << 1) | bit
        out.append(v)
    return bytes(out)

def stego_encode(raw_bytes: bytes, cover: str, charset: list[str]) -> tuple[str, str]:
    """Weave raw_bytes into cover as invisible Unicode characters."""
    bps    = bits_per_slot(charset)
    zw_set = set(charset)

    header  = struct.pack(">H", len(raw_bytes))
    payload = header + raw_bytes
    bits    = _bytes_to_bits(payload)

    clean         = "".join(c for c in cover if c not in zw_set)
    slots_needed  = math.ceil(len(bits) / bps)

    if len(clean) < slots_needed:
        raise ValueError(
            f"Cover too short: need {slots_needed} slots "
            f"({len(bits)} bits ÷ {bps} bits/slot), "
            f"cover has {len(clean)} chars."
        )

    result, bit_pos = [], 0
    for ch in clean:
        result.append(ch)
        if bit_pos < len(bits):
            sym = 0
            for b in range(bps):
                sym = (sym << 1) | (bits[bit_pos + b] if bit_pos + b < len(bits) else 0)
            result.append(charset[sym])
            bit_pos += bps

    return "".join(result), clean

def stego_decode(text: str, charset: list[str]) -> bytes:
    """Extract and return the raw bytes hidden in text."""
    bps    = bits_per_slot(charset)
    zw_idx = {c: i for i, c in enumerate(charset)}

    symbols = [zw_idx[c] for c in text if c in zw_idx]

    if len(symbols) < math.ceil(16 / bps):
        raise ValueError("No hidden data found — not enough invisible characters.")

    bits = []
    for sym in symbols:
        for i in range(bps - 1, -1, -1):
            bits.append((sym >> i) & 1)

    raw    = _bits_to_bytes(bits)
    length = struct.unpack(">H", raw[:2])[0]

    if length > len(raw) - 2:
        raise ValueError(
            f"Corrupt payload: header says {length} bytes but "
            f"only {len(raw) - 2} available. Wrong --chars or --key?"
        )
    return raw[2:2 + length]


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 3b — Homoglyph transport  (SMS / Twitter safe)
#
#  Instead of inserting invisible characters, this transport encodes data by
#  substituting certain Latin letters with visually identical Cyrillic
#  lookalikes.  Every character in the output is fully visible — no platform
#  has any reason to strip or alter them.
#
#  Encoding rule:  Latin letter at an eligible position  →  bit 0
#                  Cyrillic lookalike at same position   →  bit 1
#
#  Trade-off:  ~25 % of English letters are eligible, so the cover sentence
#  needs to be about 4× longer than in ZW mode for the same payload size.
#  The AI generates the cover fresh each time — no fixed phrases are used.
# ══════════════════════════════════════════════════════════════════════════════

# Verified visually identical pairs: Latin (key) → Cyrillic lookalike (value)
HOMO: dict[str, str] = {
    # Lowercase
    "a": "\u0430",   # а  Cyrillic Small Letter A
    "c": "\u0441",   # с  Cyrillic Small Letter Es
    "e": "\u0435",   # е  Cyrillic Small Letter Ie
    "o": "\u043E",   # о  Cyrillic Small Letter O
    "p": "\u0440",   # р  Cyrillic Small Letter Er
    "x": "\u0445",   # х  Cyrillic Small Letter Ha
    # Uppercase
    "A": "\u0410",   # А  Cyrillic Capital Letter A
    "B": "\u0412",   # В  Cyrillic Capital Letter Ve
    "C": "\u0421",   # С  Cyrillic Capital Letter Es
    "E": "\u0415",   # Е  Cyrillic Capital Letter Ie
    "H": "\u041D",   # Н  Cyrillic Capital Letter En
    "I": "\u0406",   # І  Ukrainian Capital Letter I
    "K": "\u041A",   # К  Cyrillic Capital Letter Ka
    "M": "\u041C",   # М  Cyrillic Capital Letter Em
    "O": "\u041E",   # О  Cyrillic Capital Letter O
    "P": "\u0420",   # Р  Cyrillic Capital Letter Er
    "T": "\u0422",   # Т  Cyrillic Capital Letter Te
    "X": "\u0425",   # Х  Cyrillic Capital Letter Ha
}

_HOMO_INV  = {v: k for k, v in HOMO.items()}  # Cyrillic → Latin
_HOMO_LAT  = set(HOMO.keys())                  # eligible Latin chars
_HOMO_CYR  = set(HOMO.values())                # Cyrillic lookalikes
_HOMO_ALL  = _HOMO_LAT | _HOMO_CYR


def homo_eligible(cover: str) -> int:
    """Count positions in cover that can carry a bit."""
    return sum(1 for c in cover if c in _HOMO_LAT)


def homo_cover_chars(n_bits: int) -> int:
    """
    Estimate how many cover characters are needed to hide n_bits via homogyph
    substitution.  Assumes ~22 % eligibility rate (conservative), with a 20 %
    safety margin.
    """
    return math.ceil(n_bits / 0.22 * 1.20)


def homo_encode(raw_bytes: bytes, cover: str) -> str:
    """
    Encode raw_bytes into cover using homoglyph substitution.
    Returns a string where every character is visible — safe on any platform.
    Latin at an eligible position = bit 0.
    Cyrillic lookalike at that position = bit 1.
    """
    header  = struct.pack(">H", len(raw_bytes))
    payload = header + raw_bytes
    bits    = _bytes_to_bits(payload)

    eligible = homo_eligible(cover)
    if eligible < len(bits):
        raise ValueError(
            f"Cover too short for homo transport: need {len(bits)} eligible "
            f"positions but cover only has {eligible}. "
            f"Use a longer cover (try --no-ai with a longer --cover)."
        )

    result, bp = [], 0
    for ch in cover:
        if ch in _HOMO_LAT and bp < len(bits):
            result.append(HOMO[ch] if bits[bp] == 1 else ch)
            bp += 1
        else:
            result.append(ch)

    return "".join(result)


def homo_decode(text: str) -> bytes | None:
    """
    Attempt to decode a homoglyph-encoded string.
    Returns raw bytes if a valid payload is found, or None if the text does
    not appear to be homo-encoded.
    """
    bits: list[int] = []
    for ch in text:
        if ch in _HOMO_LAT:
            bits.append(0)
        elif ch in _HOMO_CYR:
            bits.append(1)

    if len(bits) < 16:
        return None

    raw    = _bits_to_bytes(bits)
    length = struct.unpack(">H", raw[:2])[0]

    if length > len(raw) - 2 or length > 100_000:
        return None

    return raw[2 : 2 + length]


def homo_detect(text: str) -> bool:
    """Return True if text contains any Cyrillic lookalikes — likely homo-encoded."""
    return any(c in _HOMO_CYR for c in text)


# ══════════════════════════════════════════════════════════════════════════════
#  Cover sentence generation
# ══════════════════════════════════════════════════════════════════════════════

BUILTIN_COVERS = [
    "So I was thinking we could grab some food or coffee later this week, "
    "maybe Thursday or Friday if that works for you?",
    "Hey, just wanted to check in and see how things are going on your end, "
    "hope everything has been good lately!",
    "Quick update on my side, got that sorted out today so we should be all "
    "good now, let me know if you need anything else!",
    "I was actually just thinking about reaching out, it has been way too long "
    "since we last caught up properly, we should fix that soon!",
    "Honestly I keep meaning to message you and then something always comes up, "
    "but hope you are doing well and we can chat soon!",
    "Just a heads-up that I am running a bit behind schedule today but still "
    "planning to make it, should be there shortly after the hour!",
    "Not sure if you saw my last message but wanted to follow up and check "
    "whether you had a chance to look at what I sent over earlier this week.",
]
EXTENDERS = [
    " Let me know what you think!", " Hope to hear from you soon!",
    " Miss hanging out honestly.",  " Would love to catch up properly.",
]

def get_cover(min_chars: int, use_ai: bool = True, multi_sentence: bool = False) -> str:
    """
    Return a natural-sounding cover text with at least `min_chars` characters.
    When `multi_sentence` is True (homo transport), the AI is asked for 2-3
    sentences so the cover is long enough to hold the payload.
    No fixed extender phrases are added when AI is available.
    """
    if use_ai:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            if multi_sentence:
                prompt = (
                    f"Write 2-3 casual natural sentences a person might text to a friend. "
                    f"Total length must be at least {min_chars + 20} characters. "
                    f"Return only the sentences, no labels."
                )
            else:
                prompt = (
                    f"Write a single casual natural sentence a person might text to a friend. "
                    f"At least {min_chars + 10} characters. Return only the sentence."
                )
            msg   = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            cover = msg.content[0].text.strip().strip('"\'')
            if len(cover) >= min_chars:
                return cover
        except Exception:
            pass

    # Offline fallback: concatenate random built-in covers until long enough
    covers = list(BUILTIN_COVERS)
    random.shuffle(covers)
    cover = covers[0]
    idx   = 1
    while len(cover) < min_chars + 5:
        cover += " " + covers[idx % len(covers)]
        idx += 1
    return cover


# ══════════════════════════════════════════════════════════════════════════════
#  CLI commands
# ══════════════════════════════════════════════════════════════════════════════

def cmd_encode(args, charset):
    plaintext  = args.message or sys.stdin.read().rstrip("\n")
    if not plaintext:
        sys.exit("Error: no message provided.")

    transport = getattr(args, "transport", "zw")
    t_start   = time.perf_counter()

    # ── Encryption layer (optional) ──
    if args.key:
        if not _HAVE_CRYPTO:
            sys.exit("Error: pip install cryptography  to use --key")
        payload   = encrypt_payload(plaintext, args.key)
        encrypted = True
    else:
        payload   = plaintext.encode("utf-8")
        encrypted = False

    bits_needed = (len(payload) + 2) * 8

    # ── Transport layer ──
    if transport == "homo":
        min_chars = homo_cover_chars(bits_needed)
        cover     = args.cover or get_cover(min_chars, use_ai=not args.no_ai,
                                            multi_sentence=True)
        encoded   = homo_encode(payload, cover)
        # visual is cover with all Cyrillic chars mapped back to Latin
        visual    = "".join(_HOMO_INV.get(c, c) for c in encoded)
        slots_used = sum(1 for c in encoded if c in _HOMO_CYR)
        transport_info = "homoglyph (SMS / Twitter safe) — all chars visible"
    else:
        bps          = bits_per_slot(charset)
        min_chars    = math.ceil(bits_needed / bps)
        cover        = args.cover or get_cover(min_chars, use_ai=not args.no_ai)
        encoded, visual = stego_encode(payload, cover, charset)
        slots_used   = sum(1 for c in encoded if c in set(charset))
        transport_info = f"zero-width chars — {charset_info(charset)}"

    elapsed = (time.perf_counter() - t_start) * 1000

    print("\n── Plainsight encode ─────────────────────────────────────────")
    print(f"  Transport    : {transport_info}")
    if encrypted:
        print(f"  Encryption   : AES-256-GCM / PBKDF2-SHA256 ({PBKDF2_ITERS:,} iterations)")
        print(f"  Payload      : {len(plaintext.encode())}B plain → {len(payload)}B encrypted")
    else:
        print(f"  Encryption   : none  (add --key for AES-256-GCM)")
        print(f"  Payload      : {len(plaintext.encode())} bytes")
    print(f"  Carrier      : {slots_used} {'substituted letters' if transport == 'homo' else 'invisible chars'}")
    print(f"  Time         : {elapsed:.1f} ms")
    print(f"\n── Encoded output ────────────────────────────────────────────")
    print(encoded)
    print()


def cmd_decode(args, charset):
    text = args.message or sys.stdin.read()
    if not text:
        sys.exit("Error: no text provided.")

    transport = getattr(args, "transport", "auto")
    t_start   = time.perf_counter()
    raw       = None
    used      = "?"

    # ── Auto-detect or use specified transport ──
    if transport in ("homo", "auto") and homo_detect(text):
        raw  = homo_decode(text)
        used = "homoglyph"

    if raw is None and transport in ("zw", "auto"):
        try:
            raw  = stego_decode(text, charset)
            used = "zero-width"
        except ValueError:
            pass

    if raw is None:
        sys.exit(
            "Decode failed — no hidden data found.\n"
            "Check that you are using the same --transport, --chars, and --key as the sender."
        )

    # ── Decryption layer (optional) ──
    if args.key:
        if not _HAVE_CRYPTO:
            sys.exit("Error: pip install cryptography  to use --key")
        try:
            recovered = decrypt_payload(raw, args.key)
        except ValueError as e:
            sys.exit(f"Decrypt failed: {e}")
    else:
        try:
            recovered = raw.decode("utf-8")
        except UnicodeDecodeError:
            sys.exit(
                "Could not read as text — the message was probably encrypted.\n"
                "Add --key <passphrase> to decrypt."
            )

    elapsed = (time.perf_counter() - t_start) * 1000
    print("\n── Plainsight decode ─────────────────────────────────────────")
    print(f"  Transport    : {used} (auto-detected)")
    print(f"  Encryption   : {'AES-256-GCM / PBKDF2' if args.key else 'none'}")
    print(f"  Recovered    : {recovered!r}")
    print(f"  Time         : {elapsed:.2f} ms")
    print()


def cmd_test(args, charset):
    plaintext = args.message or "hey, meet me at the usual spot tonight"
    transport = getattr(args, "transport", "zw")

    print(f"\n── Round-trip test ───────────────────────────────────────────")
    print(f"  Transport  : {transport}")
    print(f"  Key        : {'yes (AES-256-GCM + PBKDF2)' if args.key else 'none'}")
    print(f"  Message    : {plaintext!r}")

    if args.key and not _HAVE_CRYPTO:
        sys.exit("Error: pip install cryptography  to use --key")

    t0      = time.perf_counter()
    payload = encrypt_payload(plaintext, args.key) if args.key else plaintext.encode()
    bits_needed = (len(payload) + 2) * 8

    if transport == "homo":
        min_chars = homo_cover_chars(bits_needed)
        cover     = args.cover or get_cover(min_chars, use_ai=not args.no_ai,
                                            multi_sentence=True)
        encoded   = homo_encode(payload, cover)
        raw       = homo_decode(encoded)
        carrier   = sum(1 for c in encoded if c in _HOMO_CYR)
        visible   = sum(1 for c in encoded if c not in _HOMO_ALL)
    else:
        bps       = bits_per_slot(charset)
        min_chars = math.ceil(bits_needed / bps)
        cover     = args.cover or get_cover(min_chars, use_ai=not args.no_ai)
        encoded, _ = stego_encode(payload, cover, charset)
        raw        = stego_decode(encoded, charset)
        carrier    = sum(1 for c in encoded if c in set(charset))
        visible    = sum(1 for c in encoded if c not in set(charset))

    if raw is None:
        sys.exit("Test FAILED — decode returned None")

    recovered = decrypt_payload(raw, args.key) if args.key else raw.decode()
    elapsed   = (time.perf_counter() - t0) * 1000
    ok        = recovered == plaintext

    print(f"  Carrier    : {carrier} {'substituted letters' if transport == 'homo' else 'invisible chars'} / {visible} visible chars")
    print(f"  Payload    : {len(plaintext.encode())}B plain → {len(payload)}B encoded")
    print(f"  Recovered  : {recovered!r}")
    print(f"  Time       : {elapsed:.1f} ms")
    print(f"  Result     : {'✓ PASS' if ok else '✗ FAIL'}")
    print()
    if not ok:
        sys.exit(1)


def cmd_charset(args, charset):
    bps = bits_per_slot(charset)
    fmt = f"{{:0{bps}b}}"
    print(f"\n── Active charset ────────────────────────────────────────────")
    print(f"  {len(charset)} chars, {bps} bits per slot")
    for i, ch in enumerate(charset):
        cp = ord(ch)
        print(f"  {fmt.format(i)} → U+{cp:04X}  {_CP_NAMES.get(cp, 'Unknown')}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  Argument parsing
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Plainsight — zero-width Unicode steganography + AES-256-GCM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--key","-k", metavar="PASSPHRASE",
        help="Encrypt with AES-256-GCM (PBKDF2-SHA256, 200k iterations). "
             "Both sides must use the same key.")
    parser.add_argument("--chars", metavar="HEX,HEX,...|auto",
        help="Comma-separated hex codepoints or 'auto' (daily key-derived). "
             "Must be 2/4/8/16 chars. Default: 200B,200C,200D,2060")
    parser.add_argument("--pool-size", type=int, choices=[2,4,8,16], metavar="N",
        help="When --chars auto: how many chars to derive (default 4)")
    parser.add_argument("--transport", choices=["zw", "homo"], default="zw",
        help=(
            "zw   (default) — zero-width Unicode chars, works on WhatsApp/Telegram/email. "
            "homo — homoglyph substitution, fully visible chars, works on SMS/Twitter/everywhere. "
            "Decode auto-detects which was used."
        ))
    parser.add_argument("--no-ai", action="store_true",
        help="Skip Claude API; use built-in cover sentences")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encode", help="Hide a message in a cover sentence")
    p_enc.add_argument("message", nargs="?")
    p_enc.add_argument("--cover", help="Use this exact cover sentence")

    p_dec = sub.add_parser("decode", help="Recover a hidden message")
    p_dec.add_argument("message", nargs="?")

    p_tst = sub.add_parser("test", help="Encode → decode and verify")
    p_tst.add_argument("message", nargs="?")
    p_tst.add_argument("--cover")

    sub.add_parser("charset", help="Show which invisible chars are active")

    args = parser.parse_args()

    try:
        charset = resolve_chars(args.chars, args.key, getattr(args, "pool_size", None))
    except ValueError as e:
        sys.exit(f"Error: {e}")

    {"encode": cmd_encode, "decode": cmd_decode,
     "test":   cmd_test,   "charset": cmd_charset}[args.cmd](args, charset)


if __name__ == "__main__":
    main()
