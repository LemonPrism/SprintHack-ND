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
    if name == "claude-cli":
        from .claude_cli_provider import ClaudeCliProvider
        return ClaudeCliProvider(model=settings.model, binary=settings.claude_bin)
    if name == "grok":
        from .grok_provider import GrokProvider
        return GrokProvider(
            api_key=settings.xai_api_key,
            model=settings.model,
            temperature=settings.temperature,
        )
    if name == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=settings.temperature,
        )
    if name == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(
            model=settings.model,
            host=settings.ollama_host,
            temperature=settings.temperature,
        )
    if name == "mock":
        from .mock_provider import MockProvider
        return MockProvider()
    raise ValueError(f"Unknown provider: {name!r}")
