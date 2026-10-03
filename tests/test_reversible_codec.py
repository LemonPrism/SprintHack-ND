from plainsight.key import SharedKey
from plainsight.codecs import get_codec
from evaluation.run_eval import run


def test_mock_codec_roundtrips_exactly():
    key = SharedKey.from_passphrase("k", theme="party")
    codec = get_codec("mock")
    secret = "Meet at pier 7 at 2300 on Friday with the documents."
    assert codec.unmask(codec.mask(secret, key=key), key=key) == secret


def test_harness_self_test_is_perfect():
    # The lossless mock codec must give 100% recovery on every frozen case.
    results = run("mock", theme="party", passphrase="k")
    assert results, "no cases loaded"
    assert all(r.recovery == 1.0 for r in results)
    assert all(r.benign_ok for r in results)
