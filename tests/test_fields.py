from plainsight.codecs.fields import extract_fields, pack_fields, unpack_fields


def test_extract_coords_and_names():
    s = "Swap at 41.7056 N, 86.2353 W. Host is Maria Lopez. Open Saturday 0900."
    f = extract_fields(s)
    assert any("41.7056" in c for c in f["coords"])
    assert "Maria Lopez" in f["names"]
    assert "Saturday" in f["days"]
    assert "0900" in f["times"]


def test_pack_unpack_is_lossless():
    f = {"coords": ["41.7056 N"], "times": ["0900"], "days": ["Saturday"], "names": ["Maria Lopez"]}
    assert unpack_fields(pack_fields(f)) == f
