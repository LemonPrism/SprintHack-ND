"""Live smoke test against the real provider. Skipped unless an API key is set."""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="no ANTHROPIC_API_KEY; live test skipped",
)


def test_prompt_codec_live_roundtrip():
    from plainsight.config import get_settings
    from plainsight.key import SharedKey
    from plainsight.providers import get_provider
    from plainsight.codecs import get_codec

    key = SharedKey.from_passphrase("sprinthack-demo", theme="dinner plans")
    codec = get_codec("prompt", get_provider(get_settings()))
    cover = codec.mask("Meet at the north dock at 2300 on Friday.", key=key)
    assert cover and "dock" not in cover.lower()          # should look benign
    recovered = codec.unmask(cover, key=key)
    assert recovered                                       # should return something
