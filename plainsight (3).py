#!/usr/bin/env python3
"""
plainsight.py — zero-width Unicode steganography, CLI tool

Technique
---------
Four invisible Unicode characters each encode 2 bits:
  U+200B  (zero width space)         → 00
  U+200C  (zero width non-joiner)    → 01
  U+200D  (zero width joiner)        → 10
  U+2060  (word joiner)              → 11

These are woven between the visible characters of a cover sentence.
Eve sees only the natural sentence — no codes, no numbers, no patterns.
Bob extracts the invisible characters and recovers the original exactly.

Capacity: 2 bits per visible character of cover text.

Usage
-----
  python plainsight.py encode "meet me at the usual spot tonight"
  python plainsight.py decode "So I was thinking we could grab..."

  # pipe a long message
  echo "secret message here" | python plainsight.py encode

  # round-trip test
  python plainsight.py test "any message you like"

  # use a custom cover sentence
  python plainsight.py encode "secret" --cover "Hey just wanted to check in!"

Requirements
------------
  pip install anthropic   # optional — only needed for AI-generated cover sentences
  Python 3.8+, no other dependencies
"""

import sys
import os
import struct
import random
import argparse
import time

# ── Zero-width characters ──────────────────────────────────────────────────────
# Each encodes 2 bits (00, 01, 10, 11)
ZW = ["\u200B", "\u200C", "\u200D", "\u2060"]
ZW_SET = set(ZW)
ZW_IDX = {c: i for i, c in enumerate(ZW)}


# ── Codec ──────────────────────────────────────────────────────────────────────

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
            v = (v << 1) | (bits[i + j] if i + j < len(bits) else 0)
        out.append(v)
    return bytes(out)


def encode(plaintext: str, cover: str) -> tuple[str, str]:
    """
    Encode `plaintext` into `cover` using zero-width steganography.

    Returns
    -------
    (encoded, visual)
        encoded : the cover sentence with invisible ZW characters woven in
        visual  : the clean cover sentence (what Eve sees)
    """
    payload = plaintext.encode("utf-8")
    # 2-byte big-endian length header so decoder knows where to stop
    header  = struct.pack(">H", len(payload))
    data    = header + payload
    bits    = _bytes_to_bits(data)

    # Strip any existing ZW chars from the cover (defensive)
    clean = "".join(c for c in cover if c not in ZW_SET)

    slots_available = len(clean)
    slots_needed    = (len(bits) + 1) // 2   # 2 bits per slot, round up

    if slots_available < slots_needed:
        raise ValueError(
            f"Cover sentence is too short: needs {slots_needed} character slots "
            f"for {len(bits)} bits, but cover has only {slots_available} characters.\n"
            f"Use a longer cover sentence (--cover) or a shorter message."
        )

    result  = []
    bit_pos = 0
    for i, ch in enumerate(clean):
        result.append(ch)
        if bit_pos < len(bits):
            b0   = bits[bit_pos]
            b1   = bits[bit_pos + 1] if bit_pos + 1 < len(bits) else 0
            sym  = (b0 << 1) | b1
            result.append(ZW[sym])
            bit_pos += 2

    return "".join(result), clean


def decode(text: str) -> str:
    """
    Extract the hidden message from a zero-width-steganographic string.
    """
    symbols = [ZW_IDX[c] for c in text if c in ZW_SET]

    if len(symbols) < 8:
        raise ValueError("No hidden data found — not enough invisible characters.")

    bits  = []
    for sym in symbols:
        bits.append((sym >> 1) & 1)
        bits.append(sym & 1)

    raw = _bits_to_bytes(bits)

    if len(raw) < 2:
        raise ValueError("Corrupt payload: header too short.")

    length = struct.unpack(">H", raw[:2])[0]

    if length > len(raw) - 2:
        raise ValueError(
            f"Corrupt payload: header says {length} bytes "
            f"but only {len(raw) - 2} bytes are available."
        )

    return raw[2:2 + length].decode("utf-8")


# ── Cover sentence generation ──────────────────────────────────────────────────

BUILTIN_COVERS = [
    "So I was thinking we could grab some food or coffee later this week, "
    "maybe Thursday or Friday if that works for you?",

    "Hey, just wanted to check in and see how things are going on your end, "
    "hope everything has been good lately!",

    "Quick update on my side, got that sorted out today so we should be all "
    "good now, let me know if you need anything else!",

    "I was actually just thinking about reaching out, it has been way too long "
    "since we last caught up properly, we should fix that!",

    "Honestly I keep meaning to message you and then something comes up, but "
    "hope you are doing well and we can chat soon!",

    "Just a heads-up that I am running a bit behind schedule today but still "
    "planning to make it, should be there shortly after the hour!",

    "Not sure if you saw my last message but wanted to follow up and check "
    "whether you had a chance to look at what I sent over earlier this week.",
]

EXTENDERS = [
    " Let me know what you think!",
    " Hope to hear from you soon!",
    " Miss hanging out honestly.",
    " Would love to catch up properly.",
    " Anyway, hope all is well!",
]


def _get_cover_ai(slots_needed: int, api_key: str | None = None) -> str | None:
    """Ask Claude to write a natural cover sentence of sufficient length."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        prompt = (
            f"Write a single casual, natural sentence a person might text to a friend. "
            f"It must be at least {slots_needed + 10} characters long "
            f"(use a compound sentence or add detail if needed). "
            f"No lists, no quotes. Return only the sentence."
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip().strip('"\'')
        return text.split("\n")[0].strip()
    except Exception:
        return None


def get_cover(slots_needed: int, use_ai: bool = True) -> str:
    """Return a cover sentence long enough to hold `slots_needed` ZW slots."""
    if use_ai:
        cover = _get_cover_ai(slots_needed)
        if cover and len(cover) >= slots_needed:
            return cover

    # Fallback to built-in sentences
    cover = random.choice(BUILTIN_COVERS)
    ext_i = 0
    while len(cover) < slots_needed + 5:
        cover += EXTENDERS[ext_i % len(EXTENDERS)]
        ext_i += 1
    return cover


# ── CLI ────────────────────────────────────────────────────────────────────────

def cmd_encode(args):
    plaintext = args.message or sys.stdin.read().rstrip("\n")
    if not plaintext:
        print("Error: no message provided.", file=sys.stderr)
        sys.exit(1)

    payload_bytes = plaintext.encode("utf-8")
    bits_needed   = (len(payload_bytes) + 2) * 8
    slots_needed  = (bits_needed + 1) // 2

    t0 = time.perf_counter()

    if args.cover:
        cover = args.cover
    else:
        use_ai = not args.no_ai
        cover  = get_cover(slots_needed, use_ai=use_ai)

    encoded, visual = encode(plaintext, cover)
    elapsed = (time.perf_counter() - t0) * 1000

    slots_used = sum(1 for c in encoded if c in ZW_SET)

    print("\n── Plainsight encode ─────────────────────────────────")
    print(f"  Message  : {plaintext!r}")
    print(f"  Payload  : {len(payload_bytes)} bytes, {bits_needed} bits")
    print(f"  Slots    : {slots_used} invisible chars used / {len(visual)} visible")
    print(f"  Time     : {elapsed:.1f} ms")
    print(f"\n── What Eve sees (plain text, no hidden content visible) ──")
    print(f"  {visual}")
    print(f"\n── Encoded string (copy this to send / decode later) ──")
    print(encoded)
    print()


def cmd_decode(args):
    text = args.message or sys.stdin.read()
    if not text:
        print("Error: no text provided.", file=sys.stderr)
        sys.exit(1)

    t0 = time.perf_counter()
    try:
        recovered = decode(text)
    except ValueError as e:
        print(f"Decode failed: {e}", file=sys.stderr)
        sys.exit(1)
    elapsed = (time.perf_counter() - t0) * 1000

    print("\n── Plainsight decode ─────────────────────────────────")
    print(f"  Recovered: {recovered!r}")
    print(f"  Time     : {elapsed:.2f} ms")
    print()


def cmd_test(args):
    plaintext = args.message or "hey, meet me at the usual spot tonight"
    print(f"\n── Round-trip test: {plaintext!r} ──")

    payload_bytes = plaintext.encode("utf-8")
    bits_needed   = (len(payload_bytes) + 2) * 8
    slots_needed  = (bits_needed + 1) // 2

    cover = args.cover or get_cover(slots_needed, use_ai=not args.no_ai)
    print(f"  Cover ({len(cover)} chars): {cover[:60]}{'...' if len(cover)>60 else ''}")

    encoded, visual = encode(plaintext, cover)
    recovered       = decode(encoded)

    slots = sum(1 for c in encoded if c in ZW_SET)
    ok    = recovered == plaintext

    print(f"  Slots used  : {slots} invisible / {len(visual)} visible chars")
    print(f"  Recovered   : {recovered!r}")
    print(f"  Match       : {'✓ PASS' if ok else '✗ FAIL'}")
    if not ok:
        sys.exit(1)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Plainsight — zero-width Unicode steganography",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--no-ai", action="store_true",
                        help="skip Claude API call, use built-in cover sentences")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encode", help="hide a message in a cover sentence")
    p_enc.add_argument("message", nargs="?", help="message to hide (or pipe via stdin)")
    p_enc.add_argument("--cover", help="use a specific cover sentence instead of generating one")

    p_dec = sub.add_parser("decode", help="recover a hidden message")
    p_dec.add_argument("message", nargs="?", help="encoded text (or pipe via stdin)")

    p_tst = sub.add_parser("test", help="encode then decode and verify round-trip")
    p_tst.add_argument("message", nargs="?", help="message to test")
    p_tst.add_argument("--cover", help="use a specific cover sentence")

    args = parser.parse_args()

    if args.cmd == "encode":
        cmd_encode(args)
    elif args.cmd == "decode":
        cmd_decode(args)
    elif args.cmd == "test":
        cmd_test(args)


if __name__ == "__main__":
    main()
