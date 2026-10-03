"""OllamaProvider plumbing, with the HTTP call faked (no server needed)."""
import io
import json
import urllib.error

import pytest

from plainsight.config import Settings
from plainsight.providers import get_provider
from plainsight.providers import ollama_provider
from plainsight.providers.ollama_provider import OllamaProvider


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_urlopen(captured, reply):
    def urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResp(json.dumps({"message": {"role": "assistant", "content": reply}}).encode())
    return urlopen


def test_complete_sends_chat_request_and_returns_text(monkeypatch):
    captured = {}
    monkeypatch.setattr(ollama_provider.urllib.request, "urlopen", _fake_urlopen(captured, "  hi there \n"))
    p = OllamaProvider(model="qwen2.5:7b", host="http://localhost:11434/")

    assert p.complete("SYS", "USER", temperature=0.0) == "hi there"
    assert captured["url"] == "http://localhost:11434/api/chat"
    body = captured["body"]
    assert body["model"] == "qwen2.5:7b"
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]
    assert body["options"]["temperature"] == 0.0
    assert "seed" in body["options"]


def test_empty_reply_raises(monkeypatch):
    monkeypatch.setattr(ollama_provider.urllib.request, "urlopen", _fake_urlopen({}, "   "))
    with pytest.raises(RuntimeError, match="empty reply"):
        OllamaProvider(model="m").complete("s", "u")


def test_unreachable_server_raises_helpful_error(monkeypatch):
    def urlopen(req, timeout=None):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(ollama_provider.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError, match="ollama serve"):
        OllamaProvider(model="m").complete("s", "u")


def test_factory_builds_ollama_provider():
    s = Settings(provider="ollama", model="qwen2.5:7b", temperature=0.0,
                 anthropic_api_key=None, openai_api_key=None)
    assert isinstance(get_provider(s), OllamaProvider)
