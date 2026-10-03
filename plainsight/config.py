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
    ollama_host: str


def get_settings() -> Settings:
    return Settings(
        provider=os.getenv("PLAINSIGHT_PROVIDER", "anthropic"),
        model=os.getenv("PLAINSIGHT_MODEL", "claude-sonnet-5-5"),
        temperature=float(os.getenv("PLAINSIGHT_TEMPERATURE", "0.0")),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        ollama_host=os.getenv("OLLAMA_HOST_URL", "http://localhost:11434"),
    )
