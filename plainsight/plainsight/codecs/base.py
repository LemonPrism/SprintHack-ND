"""The Codec interface: mask() and unmask(), nothing else."""
from __future__ import annotations
from abc import ABC, abstractmethod
from ..key import SharedKey


class Codec(ABC):
    @abstractmethod
    def mask(self, secret: str, *, key: SharedKey) -> str:
        """Turn a clandestine message into benign-looking cover text."""
        raise NotImplementedError

    @abstractmethod
    def unmask(self, cover: str, *, key: SharedKey) -> str:
        """Recover the original (or close-enough) secret from cover text."""
        raise NotImplementedError
