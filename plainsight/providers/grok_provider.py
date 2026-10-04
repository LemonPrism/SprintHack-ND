"""xAI Grok provider. OpenAI-compatible HTTP API. Stdlib only.

Talks to xAI's chat-completions endpoint (https://api.x.ai/v1/chat/completions),
which mirrors the OpenAI schema. Needs a paid xAI API key (XAI_API_KEY) — there
is no subscription-auth route like the Claude CLI. Grok is less likely than a
frontier model to refuse the Stage 1 prompt codec (where the model is shown the
secret and asked to disguise it); that is the only reason to reach for it here.

This is just another LLMProvider behind the seam — nothing else knows it exists.
"""
from __future__ import annotations
import json
import urllib.error
import urllib.request

from .base import LLMProvider


class GrokProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "grok-3",
                 host: str = "https://api.x.ai/v1", temperature: float = 0.0,
                 timeout: float = 120.0):
        if not api_key:
            raise RuntimeError(
                "XAI_API_KEY is not set. Create a key at console.x.ai and put it in .env."
            )
        self._key = api_key
        self._model = model
        self._url = host.rstrip("/") + "/chat/completions"
        self._temperature = temperature
        self._timeout = timeout

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
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"xAI returned HTTP {e.code} for model {self._model!r}: {detail}. "
                f"Check the key, your credits/billing, and the model id at console.x.ai."
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Could not reach xAI at {self._url} ({e.reason})."
            ) from e

        choices = data.get("choices") or []
        text = (choices[0].get("message", {}).get("content", "") if choices else "").strip()
        if not text:
            raise RuntimeError(f"xAI model {self._model!r} returned an empty reply.")
        return text
