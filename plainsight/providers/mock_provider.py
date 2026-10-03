"""A canned provider for unit-testing plumbing WITHOUT an API key.

It does NOT do real masking. For a lossless round-trip test double, use
ReversibleMockCodec instead (that is what the eval harness self-test uses).
"""
from __future__ import annotations
from .base import LLMProvider


class MockProvider(LLMProvider):
    def __init__(self, reply: str = "[[mock reply]]"):
        self.reply = reply
        self.calls: list[tuple[str, str, float | None]] = []

    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        self.calls.append((system, user, temperature))
        return self.reply
