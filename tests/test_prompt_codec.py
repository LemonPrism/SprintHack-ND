from plainsight.key import SharedKey
from plainsight.codecs import get_codec
from plainsight.providers.mock_provider import MockProvider


def test_prompt_codec_defers_temperature_to_provider():
    # None => the provider uses its configured temperature (PLAINSIGHT_TEMPERATURE).
    provider = MockProvider()
    codec = get_codec("prompt", provider)
    key = SharedKey.from_passphrase("k", theme="party")
    codec.mask("secret", key=key)
    codec.unmask("cover", key=key)
    assert [temp for _, _, temp in provider.calls] == [None, None]
