"""GroqProvider plumbing, with the HTTP call faked (no key, no network)."""
import io
import json
import urllib.error

import pytest

from plainsight.config import Settings
from plainsight.providers import get_provider
from plainsight.providers import groq_provider
from plainsight.providers.groq_provider import GroqProvider


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_urlopen(captured, reply):
    def urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = req.headers
        captured["body"] = json.loads(req.data.decode("utf-8"))
        payload = {"choices": [{"message": {"role": "assistant", "content": reply}}]}
        return _FakeResp(json.dumps(payload).encode())
    return urlopen


def test_complete_sends_openai_shaped_request_and_returns_text(monkeypatch):
    captured = {}
    monkeypatch.setattr(groq_provider.urllib.request, "urlopen", _fake_urlopen(captured, "  hi \n"))
    p = GroqProvider(api_key="gsk-test", model="llama-3.3-70b-versatile",
                     host="https://api.groq.com/openai/v1/")

    assert p.complete("SYS", "USER", temperature=0.0) == "hi"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"].get("Authorization") == "Bearer gsk-test"
    body = captured["body"]
    assert body["model"] == "llama-3.3-70b-versatile"
    assert body["stream"] is False
    assert body["temperature"] == 0.0
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]


def test_missing_key_raises():
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        GroqProvider(api_key="", model="llama-3.3-70b-versatile")


def test_empty_reply_raises(monkeypatch):
    monkeypatch.setattr(groq_provider.urllib.request, "urlopen", _fake_urlopen({}, "   "))
    with pytest.raises(RuntimeError, match="empty reply"):
        GroqProvider(api_key="gsk-test", model="m").complete("s", "u")


def test_unreachable_server_raises(monkeypatch):
    def urlopen(req, timeout=None):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(groq_provider.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError, match="Could not reach Groq"):
        GroqProvider(api_key="gsk-test", model="m").complete("s", "u")


def test_factory_builds_groq_provider():
    s = Settings(provider="groq", model="llama-3.3-70b-versatile", temperature=0.0,
                 anthropic_api_key=None, openai_api_key=None, groq_api_key="gsk-test")
    assert isinstance(get_provider(s), GroqProvider)
