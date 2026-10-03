"""Local provider (Ollama). Runs a small model on-device — no API key, no cloud.

Talks to the Ollama server's HTTP API with the standard library only, so no extra
dependency. Start the server with the Ollama app (or `ollama serve`) and pull a
model first, e.g. `ollama pull qwen2.5:7b`.
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
        self._seed = seed          # fixed seed + temperature 0 => reproducible output
        self._timeout = timeout    # CPU inference can be slow

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
        req = urllib.request.Request(self._url, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Could not reach Ollama at {self._url} ({e}). Is the Ollama app running, "
                f"and is the model pulled (`ollama pull {self._model}`)?"
            ) from e
        return data["message"]["content"].strip()
