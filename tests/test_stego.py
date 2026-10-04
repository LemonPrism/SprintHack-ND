"""Zero-width stego embedding: lossless, invisible, and ignores normal text."""
from plainsight.codecs import stego


def test_encode_decode_roundtrip_bytes():
    for data in [b"", b"A", bytes(range(256)), "coords 48.4647".encode("utf-8")]:
        assert stego.decode_payload(stego.encode_payload(data)) == data


def test_hide_reveal_roundtrip():
    cover = "Hey, see you later!"
    payload = b"secret bytes \x00\xff"
    carrier = stego.hide(cover, payload)
    assert stego.reveal(carrier) == payload


def test_payload_is_invisible():
    cover = "Hey, see you later!"
    carrier = stego.hide(cover, b"hidden")
    # Strip the zero-width chars -> exactly the original visible text.
    assert stego.visible(carrier) == cover
    # The visible text is unchanged; the carrier is longer only by invisible chars.
    assert len(carrier) > len(cover)


def test_reveal_ignores_plain_text():
    assert stego.reveal("just an ordinary message, nothing hidden") == b""
