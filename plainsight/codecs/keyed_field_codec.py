"""Stage 2 — the fidelity layer (SCAFFOLD).

Goal: exact data survives the round trip losslessly. Strategy:
  mask:   extract_fields(secret) -> pack_fields -> (key-dependent disguise)
          -> prompt the LLM to weave the disguised payload into benign cover.
  unmask: pull the disguised payload back out -> undo disguise -> unpack_fields
          -> rebuild the exact secret.

The deterministic halves (extract/pack/unpack) already exist and are tested.
The TODOs below are the LLM-weaving + the key-dependent disguise. See TASKS.md
Stage 2 and ARCHITECTURE.md ("Key separation / seized-model safety").
"""
from __future__ import annotations
from .base import Codec
from .fields import extract_fields, pack_fields, unpack_fields  # noqa: F401 (used once implemented)
from ..key import SharedKey


class KeyedFieldCodec(Codec):
    def __init__(self, provider):
        if provider is None:
            raise ValueError("KeyedFieldCodec needs an LLMProvider.")
        self._p = provider

    def mask(self, secret: str, *, key: SharedKey) -> str:
        # fields = extract_fields(secret)
        # payload = pack_fields(fields)
        # disguised = self._disguise(payload, key)        # TODO: key-dependent
        # cover = self._p.complete(<weave prompt with disguised + key.theme>, secret)
        # return cover
        raise NotImplementedError(
            "Stage 2: implement the field-weaving mask. See TASKS.md / ARCHITECTURE.md."
        )

    def unmask(self, cover: str, *, key: SharedKey) -> str:
        # disguised = self._extract_payload(cover, key)   # TODO: mirror of _disguise
        # payload = self._undisguise(disguised, key)
        # fields = unpack_fields(payload)
        # return self._p.complete(<rebuild prompt with fields + key.theme>, cover)
        raise NotImplementedError(
            "Stage 2: implement the field-recovery unmask. See TASKS.md / ARCHITECTURE.md."
        )

    # def _disguise(self, payload: str, key: SharedKey) -> str: ...
    # def _undisguise(self, disguised: str, key: SharedKey) -> str: ...
