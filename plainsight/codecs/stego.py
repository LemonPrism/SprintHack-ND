"""Invisible payload embedding via zero-width characters.

Encodes bytes as a run of zero-width Unicode codepoints that render as nothing, so
the carrier message looks like ordinary text to the naked eye. Pure, deterministic,
and losslessly reversible (unit-tested).

Scope note: this clears the "benign to a casual human" bar. It does NOT survive
channels that strip/normalize Unicode (some SMS gateways, Twitter) and is trivially
visible at the byte level — defeating those is the NeuralStegoCodec / better-model
future work in ARCHITECTURE.md. WhatsApp (full Unicode) is the reliable carrier today.
"""
from __future__ import annotations

# Four zero-width codepoints -> 2 bits each -> 4 symbols per byte.
_ZW = "​‌‍⁠"   # ZWSP, ZWNJ, ZWJ, WORD JOINER
_ZW_SET = set(_ZW)
_ZW_INDEX = {c: i for i, c in enumerate(_ZW)}


def encode_payload(data: bytes) -> str:
    """bytes -> an invisible zero-width string (base-4, 4 chars per byte)."""
    out = []
    for b in data:
        out.append(_ZW[(b >> 6) & 3])
        out.append(_ZW[(b >> 4) & 3])
        out.append(_ZW[(b >> 2) & 3])
        out.append(_ZW[b & 3])
    return "".join(out)


def decode_payload(s: str) -> bytes:
    """Inverse of encode_payload. Ignores any non-zero-width characters."""
    syms = [_ZW_INDEX[c] for c in s if c in _ZW_SET]
    out = bytearray()
    for i in range(0, len(syms) - 3, 4):
        out.append((syms[i] << 6) | (syms[i + 1] << 4) | (syms[i + 2] << 2) | syms[i + 3])
    return bytes(out)


def hide(cover: str, data: bytes) -> str:
    """Tuck the invisible payload just after the cover's first character."""
    zw = encode_payload(data)
    if not cover:
        return zw
    return cover[0] + zw + cover[1:]


def reveal(cover: str) -> bytes:
    """Pull the payload bytes back out of a carrier message."""
    return decode_payload(cover)


def visible(cover: str) -> str:
    """The cover with the invisible payload stripped — what the eye actually reads."""
    return "".join(c for c in cover if c not in _ZW_SET)
