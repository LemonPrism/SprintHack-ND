"""Settings loaded from environment / .env. See .env.example."""
from __future__ import annotations
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # dotenv optional; env vars still work without it
    pass


@dataclass
class Settings:
    provider: str
    model: str
    temperature: float
    anthropic_api_key: str | None
    openai_api_key: str | None
    ollama_host: str = "http://localhost:11434"
    claude_bin: str | None = None   # path to the `claude` CLI (claude-cli provider)
    xai_api_key: str | None = None  # xAI Grok API key (grok provider)


# Model used when PLAINSIGHT_MODEL is unset, per provider.
_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5-5",
    "ollama": "qwen2.5:7b",
    "claude-cli": "sonnet",   # CLI model alias (e.g. opus / sonnet)
    "grok": "grok-3",         # confirm the current id at console.x.ai
}


def get_settings() -> Settings:
    provider = os.getenv("PLAINSIGHT_PROVIDER", "anthropic")
    return Settings(
        provider=provider,
        model=os.getenv("PLAINSIGHT_MODEL") or _DEFAULT_MODELS.get(provider, ""),
        temperature=float(os.getenv("PLAINSIGHT_TEMPERATURE", "0.0")),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        claude_bin=os.getenv("PLAINSIGHT_CLAUDE_BIN"),
        xai_api_key=os.getenv("XAI_API_KEY"),
    )
