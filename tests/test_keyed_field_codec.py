"""KeyedFieldCodec: lossless by construction and key-dependent.

The payload carries the secret independently of the cover text, so these run
offline with a canned provider — no LLM/server needed.
"""
import pytest

from plainsight.key import SharedKey
from plainsight.codecs.keyed_field_codec import KeyedFieldCodec
from plainsight.providers.mock_provider import MockProvider

SECRET = ("The weapons facility is at 48.4647 N, 35.0462 E. Workday 0800-1700. "
          "Commander is Viktor Orlov. Reach it Sunday via the north dock on Highway 7.")


def _codec(reply="Looking forward to the party!"):
    return KeyedFieldCodec(MockProvider(reply=reply))


def test_roundtrip_is_lossless():
    key = SharedKey.from_passphrase("k", theme="party")
    codec = _codec()
    assert codec.unmask(codec.mask(SECRET, key=key), key=key) == SECRET


def test_cover_is_benign_and_hides_the_secret():
    key = SharedKey.from_passphrase("k", theme="party")
    cover = _codec().mask(SECRET, key=key)
    # The disguised payload is hex, so no alphabetic trigger word can appear in it,
    # and the plaintext secret must not leak into the cover.
    assert "48.4647" not in cover
    assert "Viktor Orlov" not in cover


def test_wrong_key_does_not_recover_the_secret():
    good = SharedKey.from_passphrase("right-key", theme="party")
    bad = SharedKey.from_passphrase("wrong-key", theme="party")
    cover = _codec().mask(SECRET, key=good)
    assert _codec().unmask(cover, key=bad) != SECRET


def test_missing_payload_falls_back_to_cover():
    key = SharedKey.from_passphrase("k", theme="party")
    assert _codec().unmask("just a normal message, no payload", key=key) == \
        "just a normal message, no payload"


def test_needs_a_provider():
    with pytest.raises(ValueError):
        KeyedFieldCodec(None)
