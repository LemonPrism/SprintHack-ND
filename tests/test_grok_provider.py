"""GrokProvider plumbing, with the HTTP call faked (no key, no network)."""
import io
import json
import urllib.error

import pytest

from plainsight.config import Settings
from plainsight.providers import get_provider
from plainsight.providers import grok_provider
from plainsight.providers.grok_provider import GrokProvider


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
    monkeypatch.setattr(grok_provider.urllib.request, "urlopen", _fake_urlopen(captured, "  hi \n"))
    p = GrokProvider(api_key="xai-test", model="grok-3", host="https://api.x.ai/v1/")

    assert p.complete("SYS", "USER", temperature=0.0) == "hi"
    assert captured["url"] == "https://api.x.ai/v1/chat/completions"
    # key goes in the Authorization header (urllib title-cases header names)
    assert captured["headers"].get("Authorization") == "Bearer xai-test"
    body = captured["body"]
    assert body["model"] == "grok-3"
    assert body["stream"] is False
    assert body["temperature"] == 0.0
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]


def test_missing_key_raises():
    with pytest.raises(RuntimeError, match="XAI_API_KEY"):
        GrokProvider(api_key="", model="grok-3")


def test_empty_reply_raises(monkeypatch):
    monkeypatch.setattr(grok_provider.urllib.request, "urlopen", _fake_urlopen({}, "   "))
    with pytest.raises(RuntimeError, match="empty reply"):
        GrokProvider(api_key="xai-test", model="grok-3").complete("s", "u")


def test_unreachable_server_raises(monkeypatch):
    def urlopen(req, timeout=None):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(grok_provider.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError, match="Could not reach xAI"):
        GrokProvider(api_key="xai-test", model="grok-3").complete("s", "u")


def test_factory_builds_grok_provider():
    s = Settings(provider="grok", model="grok-3", temperature=0.0,
                 anthropic_api_key=None, openai_api_key=None, xai_api_key="xai-test")
    assert isinstance(get_provider(s), GrokProvider)
