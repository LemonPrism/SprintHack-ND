"""Face key: a personal key rebuilt from your face, used to lock a local vault.

The PlainSight shared key must be identical on both ends, so a face cannot BE
that key (your partner doesn't have your face). Instead the face unlocks a
local vault that holds the shared passphrase, and can encrypt/decrypt text.
A seized device then reveals nothing without the enrolled face (and PIN).

- fuzzy.py : noisy face embedding -> exact secret (fuzzy commitment)
- vault.py : face secret (+ PIN) -> AES-GCM vault and text encryption
- face.py  : OpenCV YuNet landmarks tracking + SFace embeddings, webcam capture
"""
import os

from .vault import FaceVault, FaceNotRecognized, WrongPin, UnlockedVault  # noqa: F401


def default_vault_path() -> str:
    return os.getenv("PLAINSIGHT_FACE_VAULT", os.path.join(os.getcwd(), ".plainsight", "face_vault.json"))
