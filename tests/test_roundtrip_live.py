"""Live smoke test against the configured real provider.

Skipped unless that provider is usable: Anthropic needs ANTHROPIC_API_KEY;
Ollama needs a reachable server (`ollama serve`).
"""
import urllib.request

import pytest

from plainsight.config import get_settings


def _live_provider_available() -> bool:
    s = get_settings()
    if s.provider == "anthropic":
        return bool(s.anthropic_api_key)
    if s.provider == "ollama":
        try:
            urllib.request.urlopen(s.ollama_host.rstrip("/") + "/api/tags", timeout=2)
            return True
        except Exception:
            return False
    return False


pytestmark = pytest.mark.skipif(
    not _live_provider_available(),
    reason="configured provider not available (no API key / Ollama not running); live test skipped",
)


def test_prompt_codec_live_roundtrip():
    from plainsight.key import SharedKey
    from plainsight.providers import get_provider
    from plainsight.codecs import get_codec

    key = SharedKey.from_passphrase("sprinthack-demo", theme="dinner plans")
    codec = get_codec("prompt", get_provider(get_settings()))
    # Place names ("north dock") are carried verbatim by design (see the
    # extraction-meet eval case); the sensitive concept is what must be hidden.
    cover = codec.mask("Extraction point is the north dock. Be there at 2300 on Friday.", key=key)
    assert cover and "extraction" not in cover.lower()    # should look benign
    recovered = codec.unmask(cover, key=key)
    assert "2300" in recovered and "Friday" in recovered  # details survive
