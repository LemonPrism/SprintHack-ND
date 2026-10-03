"""LLM providers: WHERE text comes from. Swap freely behind LLMProvider."""
from __future__ import annotations
from .base import LLMProvider


def get_provider(settings=None) -> LLMProvider:
    """Factory. Callers use this, never a concrete provider class."""
    if settings is None:
        from ..config import get_settings
        settings = get_settings()

    name = settings.provider
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add a key."
            )
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.model,
            temperature=settings.temperature,
        )
    if name == "mock":
        from .mock_provider import MockProvider
        return MockProvider()
    # To add local models later: elif name == "ollama": from .ollama_provider import ...
    raise ValueError(f"Unknown provider: {name!r}")
