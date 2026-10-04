"""Stage 2 — the fidelity layer.

The Stage 1 PromptCodec trusts the LLM to carry exact details through a paraphrase.
The judge predicted this "gets awkward very quick", and our eval confirmed it on a
7B model. This codec removes that trust entirely:

  mask:   the exact secret is encrypted with a KEY-DEPENDENT keystream and hidden in
          INVISIBLE zero-width characters inside a generic, benign cover message.
  unmask: the invisible payload is pulled back out and decrypted with the same key,
          rebuilding the secret EXACTLY (lossless) — independent of the cover text.

Why this shape (documented honestly for the deck):

- The visible cover is written by a dedicated generic prompt (COVER_SYSTEM) that is
  never shown the secret, so no specifics leak into what a human reads. The cover
  carries no information; the invisible payload does.
- Recovery does not depend on the model at all. A weak local model only affects how
  natural the cover reads, never whether the secret comes back intact.
- Key dependence (the "a seized model is not enough" story): the payload is XORed
  with a SHA-256 keystream derived from `key.passphrase`. Wrong key -> garbage.

Known limits (slide-deck "future work"): zero-width embedding is invisible to the eye
but does not survive channels that normalize Unicode (some SMS/Twitter) and is visible
at the byte level. A better on-device model + linguistic steganography (NeuralStegoCodec,
ARCHITECTURE.md) is where true byte-level/statistical deniability comes from.
"""
from __future__ import annotations
import hashlib

from . import stego
from .base import Codec
from ..key import SharedKey
from ..prompts import COVER_SYSTEM


class KeyedFieldCodec(Codec):
    def __init__(self, provider):
        if provider is None:
            raise ValueError("KeyedFieldCodec needs an LLMProvider.")
        self._p = provider

    # --- key-dependent keystream cipher ---------------------------------------
    @staticmethod
    def _keystream(passphrase: str, n: int) -> bytes:
        """Deterministic SHA-256 counter-mode keystream, seeded by the passphrase."""
        out = bytearray()
        base = passphrase.encode("utf-8")
        counter = 0
        while len(out) < n:
            out += hashlib.sha256(base + counter.to_bytes(8, "big")).digest()
            counter += 1
        return bytes(out[:n])

    def _xor(self, data: bytes, key: SharedKey) -> bytes:
        ks = self._keystream(key.passphrase, len(data))
        return bytes(b ^ k for b, k in zip(data, ks))

    # --- Codec interface -------------------------------------------------------
    def mask(self, secret: str, *, key: SharedKey) -> str:
        cipher = self._xor(secret.encode("utf-8"), key)
        # The model never sees the secret — it only writes a generic benign cover.
        system = COVER_SYSTEM.format(theme=key.theme)
        cover = self._p.complete(system, "Write the message.", temperature=0.0)
        return stego.hide(cover, cipher)

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        cipher = stego.reveal(cover)
        if not cipher:
            return stego.visible(cover)  # no payload (stripped in transit) — best effort
        return self._xor(cipher, key).decode("utf-8", errors="replace")
