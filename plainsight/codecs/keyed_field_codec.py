"""Stage 2 — the fidelity layer.

The Stage 1 PromptCodec trusts the LLM to carry exact details (coordinates,
times, names) through a paraphrase. The judge predicted this "gets awkward very
quick", and our eval confirmed it on a 7B model. This codec removes that trust:

  mask:   the exact secret is packed and hidden in a KEY-DEPENDENT payload, which
          is embedded in a benign LLM-written cover about `key.theme`.
  unmask: the payload is pulled back out and decoded with the same key, rebuilding
          the secret EXACTLY (lossless) — independent of how the model paraphrased.

Two deliberate design choices, documented honestly for the deck:

1. We transport the WHOLE secret, not only `extract_fields()` output. Place names
   and plain nouns ("north dock", "Highway 7", "documents") in the frozen cases
   are not reliably extractable; carrying the full text guarantees recovery while
   `extract_fields` still drives the human-readable "fields" view (Stage 3 demo).
2. The payload is EMBEDDED deterministically, not woven by the LLM. Asking a model
   to reproduce an exact opaque token verbatim is unreliable and would break
   losslessness; the codec inserts it. A future NeuralStegoCodec (ARCHITECTURE.md)
   is where true in-text hiding belongs.

Key dependence (the "seized model is not enough" story): the payload is XORed with
a SHA-256 keystream derived from `key.passphrase`. The model and the cover alone
cannot decode it — only a holder of the key can. Wrong key -> garbage, not plaintext.
"""
from __future__ import annotations
import hashlib
import json

from .base import Codec
from .fields import extract_fields, pack_fields, unpack_fields
from ..key import SharedKey
from ..prompts import ENCODE_SYSTEM

_MARK = "::ps1::"  # payload delimiter; PoC-grade (a later codec hides this in-text)


class KeyedFieldCodec(Codec):
    def __init__(self, provider):
        if provider is None:
            raise ValueError("KeyedFieldCodec needs an LLMProvider.")
        self._p = provider

    # --- key-dependent disguise ------------------------------------------------
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

    def _disguise(self, plaintext: str, key: SharedKey) -> str:
        data = plaintext.encode("utf-8")
        ks = self._keystream(key.passphrase, len(data))
        cipher = bytes(b ^ k for b, k in zip(data, ks))
        return cipher.hex()  # hex: no a-f combination spells a trigger word

    def _undisguise(self, disguised: str, key: SharedKey) -> str:
        cipher = bytes.fromhex(disguised)
        ks = self._keystream(key.passphrase, len(cipher))
        data = bytes(b ^ k for b, k in zip(cipher, ks))
        return data.decode("utf-8", errors="replace")

    # --- Codec interface -------------------------------------------------------
    def mask(self, secret: str, *, key: SharedKey) -> str:
        fields = extract_fields(secret)
        # Envelope carries the full secret (lossless) plus the packed fields view.
        envelope = json.dumps({"full": secret, "packed": pack_fields(fields)},
                              ensure_ascii=False)
        disguised = self._disguise(envelope, key)

        system = ENCODE_SYSTEM.format(key=key.passphrase, theme=key.theme)
        cover = self._p.complete(system, secret, temperature=0.0)
        return f"{cover} {_MARK}{disguised}{_MARK}"

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        start = cover.find(_MARK)
        if start == -1:
            return cover  # no payload (e.g. stripped in transit) — best effort
        start += len(_MARK)
        end = cover.find(_MARK, start)
        if end == -1:
            return cover
        envelope = self._undisguise(cover[start:end], key)
        try:
            data = json.loads(envelope)
            unpack_fields(data["packed"])  # validates the fields view round-trips
            return data["full"]
        except (ValueError, KeyError):
            return envelope  # wrong key / corrupted payload -> not the secret
