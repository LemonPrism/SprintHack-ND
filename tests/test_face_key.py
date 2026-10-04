"""Face key: fuzzy commitment + vault, on synthetic embeddings (no camera, no models)."""
import json

import numpy as np
import pytest

from plainsight.biometric import FaceVault, FaceNotRecognized, WrongPin
from plainsight.biometric import fuzzy

rng = np.random.default_rng(7)


def unit(v):
    return v / np.linalg.norm(v)


def near(e, cos, n=10):
    """n noisy captures of the same face, each at cosine `cos` from e."""
    out = []
    for _ in range(n):
        noise = rng.standard_normal(128)
        noise = unit(noise - (noise @ e) * e)
        out.append(unit(cos * e + np.sqrt(1 - cos ** 2) * noise))
    return out


@pytest.fixture
def face():
    return unit(rng.standard_normal(128))


def test_same_face_reproduces_exact_secret(face):
    secret, helper = fuzzy.enroll(near(face, 0.9, 20))
    for _ in range(5):
        assert fuzzy.reproduce(near(face, 0.85), helper) == secret


def test_different_face_is_rejected(face):
    _, helper = fuzzy.enroll(near(face, 0.9, 20))
    for _ in range(20):
        other = unit(rng.standard_normal(128))
        assert fuzzy.reproduce(near(other, 0.9), helper) is None


def test_helper_data_does_not_contain_secret_or_embedding(face):
    secret, helper = fuzzy.enroll(near(face, 0.9, 20))
    blob = json.dumps(helper.to_dict())
    assert secret.hex() not in blob
    assert f"{face[0]:.6f}" not in blob


def test_vault_roundtrip_and_text_encryption(face, tmp_path):
    vault = FaceVault(str(tmp_path / "v.json"))
    enrolled = vault.enroll(near(face, 0.9, 20), {"shared_key": "sprinthack-demo"})
    token = enrolled.encrypt_text("The book swap is Saturday.")
    assert token.startswith("psf1:") and "book" not in token

    unlocked = vault.unlock(near(face, 0.85))
    assert unlocked.secrets == {"shared_key": "sprinthack-demo"}
    assert unlocked.decrypt_text(token) == "The book swap is Saturday."
    assert "sprinthack-demo" not in (tmp_path / "v.json").read_text()


def test_vault_rejects_wrong_face_and_wrong_pin(face, tmp_path):
    vault = FaceVault(str(tmp_path / "v.json"))
    vault.enroll(near(face, 0.9, 20), {"shared_key": "k"}, pin="2468")
    with pytest.raises(FaceNotRecognized):
        vault.unlock(near(unit(rng.standard_normal(128)), 0.9), pin="2468")
    with pytest.raises(WrongPin):
        vault.unlock(near(face, 0.85), pin="0000")
    assert vault.unlock(near(face, 0.85), pin="2468").secrets["shared_key"] == "k"


def test_tampered_token_fails(face, tmp_path):
    v = FaceVault(str(tmp_path / "v.json")).enroll(near(face, 0.9, 20), {"shared_key": "k"})
    token = v.encrypt_text("hello")
    bad = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(ValueError):
        v.decrypt_text(bad)
