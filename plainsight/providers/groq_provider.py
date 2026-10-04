"""Groq provider. Free, fast inference over open models. OpenAI-compatible. Stdlib only.

NOTE: Groq (console.groq.com) is an inference host, NOT xAI's paid "Grok". The
free tier needs no credit card. It serves open-weight models (e.g. Llama 3.3 70B,
Qwen) that are far more capable than a local 7B and rarely refuse the Stage 1
disguise task. Endpoint is OpenAI-compatible:
https://api.groq.com/openai/v1/chat/completions.

Just another LLMProvider behind the seam — nothing else knows it exists.
"""
from __future__ import annotations
import json
import re
import time
import urllib.error
import urllib.request

from .base import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b",
                 host: str = "https://api.groq.com/openai/v1", temperature: float = 0.0,
                 timeout: float = 120.0, max_retries: int = 4):
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Create a free key at console.groq.com and put it in .env."
            )
        self._key = api_key
        self._model = model
        self._url = host.rstrip("/") + "/chat/completions"
        self._temperature = temperature
        self._timeout = timeout
        self._max_retries = max_retries

    def complete(self, system: str, user: str, *, temperature: float | None = None) -> str:
        temp = self._temperature if temperature is None else temperature
        body = json.dumps({
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temp,   # 0 => deterministic, matching the MVP rule
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            self._url, data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
                # Cloudflare fronts the Groq API and 403s urllib's default UA
                # ("error code: 1010"); a normal UA avoids the browser-signature ban.
                "User-Agent": "PlainSight/0.1",
            },
        )
        for attempt in range(self._max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                # Free tier has tight per-minute limits; honor the "try again in Xs"
                # hint (default to a short backoff) instead of crashing the demo/eval.
                if e.code == 429 and attempt < self._max_retries:
                    m = re.search(r"try again in ([0-9.]+)s", detail)
                    time.sleep(min(float(m.group(1)) + 0.5 if m else 2.0 * (attempt + 1), 30.0))
                    continue
                raise RuntimeError(
                    f"Groq returned HTTP {e.code} for model {self._model!r}: {detail}. "
                    f"Check the key and the model id at console.groq.com (model names change)."
                ) from e
            except urllib.error.URLError as e:
                raise RuntimeError(
                    f"Could not reach Groq at {self._url} ({e.reason})."
                ) from e

        choices = data.get("choices") or []
        text = (choices[0].get("message", {}).get("content", "") if choices else "").strip()
        if not text:
            raise RuntimeError(f"Groq model {self._model!r} returned an empty reply.")
        return text
