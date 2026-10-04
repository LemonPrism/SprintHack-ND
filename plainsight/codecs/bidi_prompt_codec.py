"""Stage 1 (fancy) — one bidirectional system prompt; the mode rides in the user turn."""
from __future__ import annotations
from .base import Codec
from ..key import SharedKey
from ..prompts import BIDI_SYSTEM, render_bidi_user, render_codebook


class BidiPromptCodec(Codec):
    def __init__(self, provider):
        if provider is None:
            raise ValueError("BidiPromptCodec needs an LLMProvider.")
        self._p = provider

    def _system(self, key: SharedKey) -> str:
        return BIDI_SYSTEM.format(key=key.passphrase, theme=key.theme,
                                  codebook=render_codebook("both"))

    def mask(self, secret: str, *, key: SharedKey) -> str:
        return _clean(self._p.complete(self._system(key), render_bidi_user("mask", secret),
                                       temperature=None))

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        return _clean(self._p.complete(self._system(key), render_bidi_user("unmask", cover),
                                       temperature=None))


def _clean(text: str) -> str:
    """Drop a stray '->' / 'NOTE:' / 'MESSAGE:' label or wrapping quotes the model may echo."""
    t = text.strip()
    for label in ("->", "NOTE:", "MESSAGE:"):
        if t.upper().startswith(label):
            t = t[len(label):].strip()
    if len(t) >= 2 and t[0] == t[-1] == '"':
        t = t[1:-1].strip()
    return t
