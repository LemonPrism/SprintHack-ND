"""Local provider (Ollama). Free, on-device, no API key. Stdlib only.

Talks to a running Ollama server (`ollama serve`, default http://localhost:11434)
via its /api/chat endpoint. This is the "on-device local models" extension point
from ARCHITECTURE.md — nothing else in the codebase needs to know it exists.
"""
from __future__ import annotations
import json
import urllib.error
import urllib.request

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, host: str = "http://localhost:11434",
                 temperature: float = 0.0, seed: int = 0, timeout: float = 300.0):
        self._model = model
        self._url = host.rstrip("/") + "/api/chat"
        self._temperature = temperature
        self._seed = seed          # fixed seed + temperature 0 => same input, same output
        self._timeout = timeout    # local CPU/iGPU generation (and first model load) can be slow

    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        temp = self._temperature if temperature is None else temperature
        body = json.dumps({
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temp, "seed": self._seed},
        }).encode("utf-8")
        req = urllib.request.Request(
            self._url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama returned HTTP {e.code} for model {self._model!r}: {detail}. "
                f"Is the model pulled? Try: ollama pull {self._model}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Could not reach Ollama at {self._url} ({e.reason}). Is `ollama serve` running?"
            ) from e

        text = (data.get("message") or {}).get("content", "").strip()
        if not text:
            raise RuntimeError(f"Ollama model {self._model!r} returned an empty reply.")
        return text
