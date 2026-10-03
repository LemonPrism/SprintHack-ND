"""Deterministic field extraction + lossless pack/unpack.

This is the exact-fidelity core of Stage 2: the data that MUST survive a round
trip (coordinates, times, dates, names) is handled deterministically instead of
being trusted to an LLM paraphrase. `pack_fields` and `unpack_fields` are strict
inverses (tested). Extend these patterns as your test cases demand — name
detection in particular is intentionally simple MVP-grade heuristics.
"""
from __future__ import annotations
import json
import re

# --- extraction patterns (extend these as your test cases need) -------------
_COORD = re.compile(r"\d{1,3}\.\d+\s*[NSEW]?", re.IGNORECASE)
_CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b|(?<![\d.])\b\d{3,4}\b")  # 23:00 or 2300/0800, not coord digits
_DAY = re.compile(r"\b(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b", re.IGNORECASE)
# A run of 2+ Titlecase words; we then trim leading role/verb words.
_NAME_RUN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")

# Words that often precede a name or start a sentence but are not part of it.
_NAME_STOPWORDS = {
    "manager", "plant", "factory", "director", "officer", "agent", "guard",
    "destroy", "avoid", "bring", "meet", "new", "the", "extraction", "workday",
}
# Day names shouldn't be mistaken for a surname.
_DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def _clean_name(run: str) -> str | None:
    tokens = run.split()
    while tokens and tokens[0].lower() in _NAME_STOPWORDS:
        tokens.pop(0)
    while tokens and tokens[-1].lower() in _DAYS:
        tokens.pop()
    return " ".join(tokens) if len(tokens) >= 2 else None


def extract_fields(text: str) -> dict[str, list[str]]:
    """Pull the critical, must-survive values out of a secret message."""
    names = [n for n in (_clean_name(m.group(0)) for m in _NAME_RUN.finditer(text)) if n]
    return {
        "coords": _COORD.findall(text),
        "times": _CLOCK.findall(text),
        "days": [m.group(0) for m in _DAY.finditer(text)],
        "names": names,
    }


def pack_fields(fields: dict[str, list[str]]) -> str:
    """Serialize fields into a compact payload string (lossless)."""
    return json.dumps(fields, separators=(",", ":"), ensure_ascii=False)


def unpack_fields(payload: str) -> dict[str, list[str]]:
    """Exact inverse of pack_fields."""
    return json.loads(payload)
