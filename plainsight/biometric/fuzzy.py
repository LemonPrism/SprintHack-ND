"""Fuzzy commitment: turn a *noisy* face embedding into an *exact*, repeatable secret.

A face embedding is never identical twice, so it cannot be hashed into a key
directly. Instead (Juels & Wattenberg's fuzzy commitment):

  enroll : face -> bits b.  Pick a random secret k.  Store h = Repeat(k) XOR b.
  unlock : face' -> bits b'.  h XOR b' = Repeat(k) XOR (b XOR b'); a majority vote
           in each repetition block removes the bits where b' differs from b.

What is stored ("helper data") is h, the projection seed, the chosen bit
positions and an HMAC check value. No face image, embedding or template is
stored, and k itself never touches disk.

Bits come from random hyperplanes (SimHash): bit i = sign(<r_i, e>). Two
embeddings at angle t disagree on a bit with probability t/pi, so the vote
succeeds only when the new face is close to the enrolled one. We keep the half
of the projections with the largest |<r_i, e>| at enrollment: those bits are
the least likely to flip under capture noise.

Defaults (4096 projections, keep 50%, 128-bit secret, 15x repetition) were
tuned by simulation: cosine >= 0.7 unlocks ~97%, cosine <= 0.4 unlocks ~0%.
SFace's own same-person threshold is cosine 0.363.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
from dataclasses import asdict, dataclass

import numpy as np

EMBED_DIM = 128
CHECK_LABEL = b"plainsight-face-check-v1"


@dataclass(frozen=True)
class FuzzyParams:
    n_proj: int = 4096       # random hyperplanes
    keep: float = 0.5        # fraction of most reliable bits kept
    key_bits: int = 128      # length of the recovered secret
    repeat: int = 15         # repetition-code length (odd, for a clean majority)


@dataclass
class Helper:
    """Public helper data. Safe to store; useless without a matching face."""
    version: int
    n_proj: int
    key_bits: int
    repeat: int
    proj_seed: int
    positions: list[int]     # which projections feed the code, in block order
    code: str                # base64 of packed bits h = Repeat(k) XOR b
    salt: str                # base64
    check: str               # base64 HMAC(k, label + salt): detects a wrong face

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Helper":
        return cls(**d)


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("zero embedding")
    return v / n


def summarize(embeddings: list[np.ndarray] | np.ndarray, min_cos: float = 0.6) -> np.ndarray:
    """One robust embedding from several frames: mean, drop outlier frames, re-mean."""
    E = np.atleast_2d(np.asarray(embeddings, dtype=np.float64))
    if E.shape[1] != EMBED_DIM:
        raise ValueError(f"expected {EMBED_DIM}-d embeddings, got {E.shape[1]}")
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    mean = _unit(E.mean(axis=0))
    keep = E[E @ mean >= min_cos]
    return _unit(keep.mean(axis=0)) if len(keep) else mean


def _projections(seed: int, n_proj: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((n_proj, EMBED_DIM))


def _check(secret: bytes, salt: bytes) -> bytes:
    return hmac.new(secret, CHECK_LABEL + salt, hashlib.sha256).digest()


def enroll(embeddings, params: FuzzyParams = FuzzyParams()) -> tuple[bytes, Helper]:
    """Create a fresh random secret bound to this face. Returns (secret, helper)."""
    if params.repeat % 2 == 0:
        raise ValueError("repeat must be odd")
    e = summarize(embeddings)
    seed = secrets.randbits(63)
    proj = _projections(seed, params.n_proj) @ e
    n_keep = int(params.n_proj * params.keep)
    need = params.key_bits * params.repeat
    if need > n_keep:
        raise ValueError(f"need {need} reliable bits but only keep {n_keep}")
    reliable = np.argsort(-np.abs(proj))[:n_keep]
    # Shuffle so each repetition block mixes bits of different reliability.
    order = np.random.default_rng(secrets.randbits(63)).permutation(reliable)[:need]
    b = proj[order] > 0

    secret = secrets.token_bytes(params.key_bits // 8)
    k_bits = np.unpackbits(np.frombuffer(secret, dtype=np.uint8)).astype(bool)
    h = np.repeat(k_bits, params.repeat) ^ b
    salt = secrets.token_bytes(16)
    helper = Helper(
        version=1, n_proj=params.n_proj, key_bits=params.key_bits, repeat=params.repeat,
        proj_seed=seed, positions=[int(i) for i in order],
        code=base64.b64encode(np.packbits(h).tobytes()).decode(),
        salt=base64.b64encode(salt).decode(),
        check=base64.b64encode(_check(secret, salt)).decode(),
    )
    return secret, helper


def reproduce(embeddings, helper: Helper) -> bytes | None:
    """Rebuild the enrolled secret from a new capture, or None if the face doesn't match."""
    e = summarize(embeddings)
    pos = np.asarray(helper.positions)
    b2 = (_projections(helper.proj_seed, helper.n_proj)[pos] @ e) > 0
    n = helper.key_bits * helper.repeat
    h = np.unpackbits(np.frombuffer(base64.b64decode(helper.code), dtype=np.uint8))[:n].astype(bool)
    votes = (h ^ b2).reshape(helper.key_bits, helper.repeat).sum(axis=1) > helper.repeat // 2
    secret = np.packbits(votes).tobytes()
    salt = base64.b64decode(helper.salt)
    if hmac.compare_digest(_check(secret, salt), base64.b64decode(helper.check)):
        return secret
    return None
