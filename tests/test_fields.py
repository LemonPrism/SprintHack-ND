from plainsight.codecs.fields import extract_fields, pack_fields, unpack_fields


def test_extract_coords_and_names():
    s = "Factory at 48.4647 N, 35.0462 E. Manager Viktor Orlov. Destroy Sunday 0800."
    f = extract_fields(s)
    assert any("48.4647" in c for c in f["coords"])
    assert "Viktor Orlov" in f["names"]
    assert "Sunday" in f["days"]
    assert "0800" in f["times"]


def test_extract_places():
    f = extract_fields("Checkpoint on Highway 7. Meet at the north dock.")
    assert "Highway 7" in f["places"]
    assert any("north dock" == p.lower() for p in f["places"])


def test_pack_unpack_is_lossless():
    f = {"coords": ["48.4647 N"], "times": ["0800"], "days": ["Sunday"],
         "names": ["Viktor Orlov"], "places": ["Highway 7"]}
    assert unpack_fields(pack_fields(f)) == f
