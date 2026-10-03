"""The LLMProvider interface. One method; that is the whole contract."""
from __future__ import annotations
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        """Return the model's text reply to `user`, steered by `system`."""
        raise NotImplementedError
