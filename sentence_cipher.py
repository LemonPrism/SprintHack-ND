#!/usr/bin/env python3
"""
Sentence Cipher
---------------
Turns a short message into a paragraph of ordinary-looking casual sentences,
and turns that paragraph back into the original message.

This is NOT encryption. It's a reversible lookup: fixed word lists and
sentence templates are built into this script, so anyone with a copy of it
can decode anything it produces. It disguises a message's format; it does
not keep it confidential.

Usage:
    python sentence_cipher.py encode "meet me at 9pm"
    python sentence_cipher.py decode "Mom texted dinner tonight. ..."
"""

import sys
import argparse

WORDS = {
    "subject": ["mom","dad","sister","brother","aunt","uncle","cousin","grandma",
                "grandpa","boss","neighbor","landlord","roommate","doctor","dentist",
                "mechanic","plumber","electrician","courier","driver","coworker",
                "manager","intern","team","kids","dog","cat","traffic","weather",
                "flight","train","bus","subway","cab","bank","gym","school","office",
                "kitchen","garage","printer","router","laptop","phone","charger",
                "wallet","keys","mailbox","fridge","washer","dryer","thermostat",
                "alarm","calendar","inbox","server","app","website","account",
                "password","card","wifi","parking","insurance"],
    "verb": ["called","texted","emailed","messaged","missed","canceled","rescheduled",
             "forgot","remembered","finished","started","grabbed","ordered","fixed",
             "broke","found","lost","booked","confirmed","arrived","delayed","left",
             "returned","borrowed","lent","paid","charged","refunded","renewed",
             "updated","installed","uninstalled","cleaned","packed","unpacked",
             "cooked","baked","washed","dried","folded","ironed","mowed","watered",
             "parked","towed","repaired","replaced","upgraded","downloaded",
             "uploaded","synced","scheduled","postponed","approved","rejected",
             "submitted","reviewed","signed","mailed","shipped","delivered",
             "tracked","restarted","rebooted"],
    "object": ["coffee","lunch","dinner","breakfast","groceries","laundry","dishes",
               "trash","mail","package","rent","bill","invoice","meeting","interview",
               "flight","train","bus","gym","yoga","haircut","car","bike","keys",
               "wallet","charger","wifi","printer","router","parking","subscription",
               "insurance","contract","resume","report","presentation","spreadsheet",
               "slides","budget","taxes","paycheck","deposit","withdrawal","transfer",
               "refund","warranty","receipt","coupon","voucher","ticket","reservation",
               "appointment","prescription","medication","checkup","filter","battery",
               "tire","oil","brakes","software","update","license","membership"],
    "time": ["today","tonight","tomorrow","yesterday","later","soon","now","shortly",
             "morning","afternoon","evening","overnight","weekend","monday","tuesday",
             "wednesday","thursday","friday","saturday","sunday","monthly","weekly",
             "daily","hourly","briefly","promptly","early","late","immediately",
             "eventually","periodically","occasionally","january","february","march",
             "april","may","june","july","august","september","october","november",
             "december","spring","summer","fall","winter","quarterly","annually",
             "biweekly","nightly","midday","midnight","noon","dusk","dawn","sometime",
             "whenever","meanwhile","afterward","beforehand","recently","upcoming"],
}

# Each template: (category order, build-function)
TEMPLATES = [
    (["subject", "verb", "object", "time"],
     lambda w: f"{w[0]} {w[1]} {w[2]} {w[3]}."),
    (["subject", "verb", "object", "time"],
     lambda w: f"{w[0]} {w[1]} {w[2]} before {w[3]}."),
    (["subject", "verb", "time"],
     lambda w: f"{w[0]} {w[1]} {w[2]}."),
    (["time", "subject", "verb", "object"],
     lambda w: f"{w[0]} {w[1]} {w[2]} {w[3]} again."),
]
SEL_BITS = 2
WORD_BITS = 6  # 64 words per list = 6 bits of info each


# ---------- bit helpers ----------

def bytes_to_bits(data: bytes):
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def bits_to_bytes(bits):
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            bit = bits[i + j] if i + j < len(bits) else 0
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out)


def read_bits(bits, pos, n):
    v = 0
    for i in range(n):
        bit = bits[pos + i] if pos + i < len(bits) else 0
        v = (v << 1) | bit
    return v


def push_bits(bits, val, n):
    for i in range(n - 1, -1, -1):
        bits.append((val >> i) & 1)


# ---------- encode ----------

def encode(message: str) -> str:
    text_bytes = message.encode("utf-8")
    length_header = [(len(text_bytes) >> 8) & 0xFF, len(text_bytes) & 0xFF]
    payload = bytes(length_header) + text_bytes

    bits = bytes_to_bits(payload)
    sentences = []
    pos = 0
    while pos < len(bits):
        t_idx = read_bits(bits, pos, SEL_BITS)
        pos += SEL_BITS
        cats, build = TEMPLATES[t_idx]
        words = []
        for cat in cats:
            v = read_bits(bits, pos, WORD_BITS)
            pos += WORD_BITS
            words.append(WORDS[cat][v])
        sentence = build(words)
        sentence = sentence[0].upper() + sentence[1:]
        sentences.append(sentence)
    return " ".join(sentences)


# ---------- decode ----------

def decode(text: str) -> str:
    sentences = [s.strip() for s in text.strip().split(".") if s.strip()]
    bits = []
    for raw in sentences:
        tokens = raw.lower().strip().split()
        n = len(tokens)
        if n == 3:
            t_idx, cats, values = 2, TEMPLATES[2][0], tokens
        elif n == 4:
            t_idx, cats, values = 0, TEMPLATES[0][0], tokens
        elif n == 5 and tokens[4] == "again":
            t_idx, cats, values = 3, TEMPLATES[3][0], tokens[:4]
        elif n == 5 and tokens[3] == "before":
            t_idx, cats, values = 1, TEMPLATES[1][0], [tokens[0], tokens[1], tokens[2], tokens[4]]
        else:
            raise ValueError(f"Unrecognized sentence shape: {raw!r}")

        idxs = []
        for cat, word in zip(cats, values):
            if word not in WORDS[cat]:
                raise ValueError(f"Unrecognized word {word!r} in: {raw!r}")
            idxs.append(WORDS[cat].index(word))

        push_bits(bits, t_idx, SEL_BITS)
        for v in idxs:
            push_bits(bits, v, WORD_BITS)

    all_bytes = bits_to_bytes(bits)
    length = (all_bytes[0] << 8) | all_bytes[1]
    text_bytes = all_bytes[2:2 + length]
    return text_bytes.decode("utf-8")


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description="Encode/decode text as casual-sounding sentences.")
    parser.add_argument("mode", choices=["encode", "decode"])
    parser.add_argument("text", nargs="?", help="Text to encode/decode. If omitted, reads from stdin.")
    args = parser.parse_args()

    input_text = args.text if args.text is not None else sys.stdin.read()

    if args.mode == "encode":
        print(encode(input_text))
    else:
        try:
            print(decode(input_text))
        except Exception as e:
            print(f"Failed to decode: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
