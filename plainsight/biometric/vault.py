"""Face-locked vault: a small encrypted file that only your face (plus optional PIN) opens.

It holds the PlainSight shared passphrase(s), so a seized device reveals nothing
without the enrolled face, and it can encrypt/decrypt arbitrary text.

    face secret (fuzzy.reproduce) + PIN --scrypt--> master key
    master key --HKDF "vault"--> AES-256-GCM key for the vault payload
    master key --HKDF "text"---> AES-256-GCM key for encrypt_text / decrypt_text
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from . import fuzzy

TOKEN_PREFIX = "psf1:"


class FaceNotRecognized(Exception):
    """The capture did not reproduce the enrolled secret."""


class WrongPin(Exception):
    """The face matched but the PIN did not."""


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _unb64(s: str) -> bytes:
    return base64.b64decode(s)


def _master_key(face_secret: bytes, pin: str, salt: bytes) -> bytes:
    # scrypt makes PIN guessing slow for someone who already has the face secret.
    return hashlib.scrypt(face_secret + pin.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


def _subkey(master: bytes, label: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"plainsight-" + label).derive(master)


@dataclass
class UnlockedVault:
    secrets: dict[str, str]
    _text_key: bytes

    def encrypt_text(self, text: str) -> str:
        nonce = os.urandom(12)
        ct = AESGCM(self._text_key).encrypt(nonce, text.encode("utf-8"), TOKEN_PREFIX.encode())
        return TOKEN_PREFIX + base64.urlsafe_b64encode(nonce + ct).decode()

    def decrypt_text(self, token: str) -> str:
        token = token.strip()
        if not token.startswith(TOKEN_PREFIX):
            raise ValueError(f"not a PlainSight face token (expected prefix {TOKEN_PREFIX!r})")
        raw = base64.urlsafe_b64decode(token[len(TOKEN_PREFIX):])
        try:
            pt = AESGCM(self._text_key).decrypt(raw[:12], raw[12:], TOKEN_PREFIX.encode())
        except InvalidTag:
            raise ValueError("token was not encrypted with this face key, or was altered") from None
        return pt.decode("utf-8")


class FaceVault:
    def __init__(self, path: str):
        self.path = path

    def exists(self) -> bool:
        return os.path.isfile(self.path)

    def enroll(self, embeddings, vault_secrets: dict[str, str], pin: str = "",
               params: fuzzy.FuzzyParams = fuzzy.FuzzyParams()) -> UnlockedVault:
        face_secret, helper = fuzzy.enroll(embeddings, params)
        kdf_salt = secrets.token_bytes(16)
        master = _master_key(face_secret, pin, kdf_salt)
        nonce = os.urandom(12)
        payload = json.dumps(vault_secrets).encode("utf-8")
        ct = AESGCM(_subkey(master, b"vault")).encrypt(nonce, payload, b"vault-v1")
        doc = {"version": 1, "pin": bool(pin), "helper": helper.to_dict(),
               "kdf_salt": _b64(kdf_salt), "nonce": _b64(nonce), "ciphertext": _b64(ct)}
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        os.replace(tmp, self.path)
        return UnlockedVault(dict(vault_secrets), _subkey(master, b"text"))

    def needs_pin(self) -> bool:
        return self._load()["pin"]

    def unlock(self, embeddings, pin: str = "") -> UnlockedVault:
        doc = self._load()
        face_secret = fuzzy.reproduce(embeddings, fuzzy.Helper.from_dict(doc["helper"]))
        if face_secret is None:
            raise FaceNotRecognized("face not recognized")
        master = _master_key(face_secret, pin, _unb64(doc["kdf_salt"]))
        try:
            payload = AESGCM(_subkey(master, b"vault")).decrypt(
                _unb64(doc["nonce"]), _unb64(doc["ciphertext"]), b"vault-v1")
        except InvalidTag:
            raise WrongPin("face recognized, but the PIN is wrong") from None
        return UnlockedVault(json.loads(payload), _subkey(master, b"text"))

    def delete(self) -> None:
        if self.exists():
            os.remove(self.path)

    def _load(self) -> dict:
        if not self.exists():
            raise FileNotFoundError(f"no face vault at {self.path}; enroll first")
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)
