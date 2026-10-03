import io
import json

from plainsight.config import Settings
from plainsight.providers import get_provider
from plainsight.providers import ollama_provider


def test_factory_builds_ollama_and_sends_chat_request(monkeypatch):
    sent = {}

    def fake_urlopen(req, timeout):
        sent["url"] = req.full_url
        sent["body"] = json.loads(req.data.decode("utf-8"))
        return io.BytesIO(json.dumps({"message": {"content": "  hi there \n"}}).encode())

    monkeypatch.setattr(ollama_provider.urllib.request, "urlopen", fake_urlopen)
    settings = Settings(provider="ollama", model="qwen2.5:7b", temperature=0.0,
                        anthropic_api_key=None, openai_api_key=None,
                        ollama_host="http://localhost:11434/")
    reply = get_provider(settings).complete("SYS", "USER", temperature=0.0)

    assert reply == "hi there"
    assert sent["url"] == "http://localhost:11434/api/chat"
    assert sent["body"]["model"] == "qwen2.5:7b"
    assert sent["body"]["messages"] == [{"role": "system", "content": "SYS"},
                                        {"role": "user", "content": "USER"}]
    assert sent["body"]["options"]["temperature"] == 0.0
