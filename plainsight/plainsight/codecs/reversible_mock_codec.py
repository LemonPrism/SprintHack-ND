"""A LOSSLESS test double used to validate the eval harness without an API key.

It is not a real masker: it hides the payload in an obvious marker and base64.
Its only job is to round-trip perfectly so that `run_eval --codec mock` reports
100% recovery. If it ever drops below 100%, the HARNESS is broken, not the model.
"""
from __future__ import annotations
import base64
from .base import Codec
from ..key import SharedKey


class ReversibleMockCodec(Codec):
    MARK = "::PS::"

    def mask(self, secret: str, *, key: SharedKey) -> str:
        token = base64.urlsafe_b64encode(secret.encode("utf-8")).decode("ascii")
        return f"Hey! Looking forward to the {key.theme}. Quick note {self.MARK}{token}{self.MARK} — talk soon!"

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        start = cover.index(self.MARK) + len(self.MARK)
        end = cover.index(self.MARK, start)
        return base64.urlsafe_b64decode(cover[start:end].encode("ascii")).decode("utf-8")
