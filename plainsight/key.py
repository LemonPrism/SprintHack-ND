"""The shared secret both sides hold.

MVP: a passphrase + a cover theme. Already exposes a deterministic, passphrase-
seeded RNG so later keyed schemes (pattern mitigation, field disguise, key
separation) have a stable source of shared randomness without an interface change.
"""
from __future__ import annotations
import hashlib
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class SharedKey:
    passphrase: str
    theme: str = "everyday chat"
    language: str = "en"   # reserved for the multilingual feature

    def seed(self) -> int:
        """Deterministic integer seed derived from the passphrase."""
        digest = hashlib.sha256(self.passphrase.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")

    def rng(self) -> random.Random:
        """A reproducible RNG shared by both endpoints (same passphrase => same stream)."""
        return random.Random(self.seed())

    @classmethod
    def from_passphrase(cls, passphrase: str, theme: str = "everyday chat",
                        language: str = "en") -> "SharedKey":
        return cls(passphrase=passphrase, theme=theme, language=language)
