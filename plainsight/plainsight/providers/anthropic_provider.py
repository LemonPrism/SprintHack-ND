"""Cloud provider (Anthropic). MVP default. Lazy-imports the SDK."""
from __future__ import annotations
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, temperature: float = 0.0,
                 max_tokens: int = 1024):
        import anthropic  # lazy: only needed when this provider is actually used
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        temp = self._temperature if temperature is None else temperature
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=temp,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()
