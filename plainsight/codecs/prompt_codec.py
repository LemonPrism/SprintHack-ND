"""Stage 1 — the MVP. Pure-LLM mask/unmask via the two system prompts."""
from __future__ import annotations
from .base import Codec
from ..key import SharedKey
from ..prompts import ENCODE_SYSTEM, DECODE_SYSTEM, render_codebook


class PromptCodec(Codec):
    def __init__(self, provider):
        if provider is None:
            raise ValueError("PromptCodec needs an LLMProvider.")
        self._p = provider

    def mask(self, secret: str, *, key: SharedKey) -> str:
        system = ENCODE_SYSTEM.format(key=key.passphrase, theme=key.theme,
                                      codebook=render_codebook("encode"))
        return self._p.complete(system, secret, temperature=None)

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        system = DECODE_SYSTEM.format(key=key.passphrase, theme=key.theme,
                                      codebook=render_codebook("decode"))
        return self._p.complete(system, cover, temperature=None)
