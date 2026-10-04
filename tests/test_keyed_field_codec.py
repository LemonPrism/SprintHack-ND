"""KeyedFieldCodec: lossless, key-dependent, and visibly benign.

Recovery carries the secret in an invisible payload independent of the cover text,
so these run offline with a canned provider — no LLM/server needed.
"""
import pytest

from plainsight.key import SharedKey
from plainsight.codecs import stego
from plainsight.codecs.keyed_field_codec import KeyedFieldCodec
from plainsight.providers.mock_provider import MockProvider

SECRET = ("The weapons facility is at 48.4647 N, 35.0462 E. Workday 0800-1700. "
          "Commander is Viktor Orlov. Reach it Sunday via the north dock on Highway 7.")
COVER = "Hey, hope you're having a good week!"  # a generic benign cover


def _codec(reply=COVER):
    return KeyedFieldCodec(MockProvider(reply=reply))


def test_roundtrip_is_lossless():
    key = SharedKey.from_passphrase("k", theme="party")
    codec = _codec()
    assert codec.unmask(codec.mask(SECRET, key=key), key=key) == SECRET


def test_visible_cover_is_clean_and_leaks_nothing():
    key = SharedKey.from_passphrase("k", theme="party")
    carrier = _codec().mask(SECRET, key=key)
    seen = stego.visible(carrier)       # what a human actually reads
    assert seen == COVER                # exactly the generic cover, nothing appended
    for leak in ["48.4647", "Viktor Orlov", "Highway 7", "0800", "::ps1::"]:
        assert leak not in seen


def test_wrong_key_does_not_recover_the_secret():
    good = SharedKey.from_passphrase("right-key", theme="party")
    bad = SharedKey.from_passphrase("wrong-key", theme="party")
    carrier = _codec().mask(SECRET, key=good)
    assert _codec().unmask(carrier, key=bad) != SECRET


def test_missing_payload_falls_back_to_visible_cover():
    key = SharedKey.from_passphrase("k", theme="party")
    assert _codec().unmask("a normal message, no payload", key=key) == \
        "a normal message, no payload"


def test_needs_a_provider():
    with pytest.raises(ValueError):
        KeyedFieldCodec(None)
