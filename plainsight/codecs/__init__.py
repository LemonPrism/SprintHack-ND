"""Codecs: HOW masking works. Swap freely behind Codec."""
from __future__ import annotations
from .base import Codec


def get_codec(name: str, provider=None) -> Codec:
    """Factory. Callers use this, never a concrete codec class."""
    if name == "prompt":
        from .prompt_codec import PromptCodec
        return PromptCodec(provider)
    if name == "bidi":
        from .bidi_prompt_codec import BidiPromptCodec
        return BidiPromptCodec(provider)
    if name == "mock":
        from .reversible_mock_codec import ReversibleMockCodec
        return ReversibleMockCodec()
    if name == "keyed":
        from .keyed_field_codec import KeyedFieldCodec
        return KeyedFieldCodec(provider)
    raise ValueError(f"Unknown codec: {name!r}")
