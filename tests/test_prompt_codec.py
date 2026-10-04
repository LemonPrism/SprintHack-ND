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


def test_bidi_codec_uses_one_system_prompt_for_both_directions():
    provider = MockProvider(reply='MESSAGE: "hello"')
    codec = get_codec("bidi", provider)
    key = SharedKey.from_passphrase("k", theme="party")
    assert codec.mask("secret", key=key) == "hello"   # label + quotes stripped
    codec.unmask("cover", key=key)
    (sys_mask, user_mask, _), (sys_unmask, user_unmask, _) = provider.calls
    assert sys_mask == sys_unmask
    assert user_mask.startswith("MODE: MASK") and user_unmask.startswith("MODE: UNMASK")
