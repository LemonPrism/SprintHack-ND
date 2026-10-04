"""Face tracking + identity embeddings with OpenCV's model-zoo networks.

- YuNet (face_detection_yunet_2023mar.onnx): finds faces and tracks 5 landmarks
  (both eyes, nose tip, both mouth corners) every frame.
- SFace (face_recognition_sface_2021dec.onnx): aligns the face on those
  landmarks and maps it to a 128-d identity embedding.

Models are downloaded once from github.com/opencv/opencv_zoo into
PLAINSIGHT_MODEL_DIR (default ./models) and checked against pinned SHA-256s.
"""
from __future__ import annotations
import hashlib
import os
import sys
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable, Iterable

import cv2
import numpy as np

try:  # OpenCV 5 logs a harmless "targets not supported" warning per network
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except AttributeError:
    pass

ZOO = "https://github.com/opencv/opencv_zoo/raw/main/models/"
MODELS = {
    "yunet": ("face_detection_yunet_2023mar.onnx", ZOO + "face_detection_yunet/face_detection_yunet_2023mar.onnx",
              "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"),
    "sface": ("face_recognition_sface_2021dec.onnx", ZOO + "face_recognition_sface/face_recognition_sface_2021dec.onnx",
              "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"),
}
LANDMARK_NAMES = ["right eye", "left eye", "nose", "right mouth", "left mouth"]

# Frame quality gates for a usable capture.
MIN_SCORE = 0.9
MIN_FACE_PX = 110


def model_dir() -> str:
    return os.getenv("PLAINSIGHT_MODEL_DIR", os.path.join(os.getcwd(), "models"))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_models(directory: str | None = None) -> dict[str, str]:
    """Download the two ONNX models if missing; verify their hashes. Returns paths."""
    directory = directory or model_dir()
    os.makedirs(directory, exist_ok=True)
    paths = {}
    for key, (name, url, digest) in MODELS.items():
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            print(f"Downloading {name} ...", file=sys.stderr)
            urllib.request.urlretrieve(url, path + ".part")
            os.replace(path + ".part", path)
        if _sha256(path) != digest:
            raise RuntimeError(f"{path} does not match its pinned SHA-256; delete it and retry")
        paths[key] = path
    return paths


@dataclass
class Face:
    box: tuple[int, int, int, int]       # x, y, w, h
    landmarks: np.ndarray                 # (5, 2) pixel coords
    score: float
    raw: np.ndarray                       # YuNet row, needed by SFace.alignCrop


class FaceTracker:
    def __init__(self, directory: str | None = None):
        paths = ensure_models(directory)
        self._det = cv2.FaceDetectorYN.create(paths["yunet"], "", (320, 320), 0.8, 0.3, 5000)
        self._rec = cv2.FaceRecognizerSF.create(paths["sface"], "")

    def detect(self, frame: np.ndarray) -> list[Face]:
        h, w = frame.shape[:2]
        self._det.setInputSize((w, h))
        _, rows = self._det.detect(frame)
        faces = []
        for r in (rows if rows is not None else []):
            faces.append(Face(box=tuple(int(v) for v in r[:4]), landmarks=r[4:14].reshape(5, 2),
                              score=float(r[14]), raw=r))
        return sorted(faces, key=lambda f: -f.box[2] * f.box[3])

    def embed(self, frame: np.ndarray, face: Face) -> np.ndarray:
        aligned = self._rec.alignCrop(frame, face.raw)
        v = self._rec.feature(aligned).flatten().astype(np.float64)
        return v / np.linalg.norm(v)

    @staticmethod
    def quality(faces: list[Face]) -> str | None:
        """None if the frame is usable for a key, else the reason it isn't."""
        if not faces:
            return "no face"
        if len(faces) > 1:
            return "more than one face"
        f = faces[0]
        if f.score < MIN_SCORE:
            return "face unclear"
        if min(f.box[2], f.box[3]) < MIN_FACE_PX:
            return "move closer"
        return None

    @staticmethod
    def annotate(frame: np.ndarray, faces: list[Face], status: str = "", ok: bool = True) -> np.ndarray:
        """Draw the tracked box, landmarks and a status line (BGR in, BGR out)."""
        out = frame.copy()
        color = (167, 212, 45) if ok else (68, 181, 245)   # teal / amber, BGR
        for f in faces:
            x, y, w, h = f.box
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
            pts = f.landmarks.astype(int)
            for a, b in [(0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (0, 1)]:
                cv2.line(out, tuple(pts[a]), tuple(pts[b]), color, 1, cv2.LINE_AA)
            for p in pts:
                cv2.circle(out, tuple(p), 4, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(out, tuple(p), 4, color, 1, cv2.LINE_AA)
            cv2.putText(out, f"{f.score:.2f}", (x, max(0, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        if status:
            cv2.rectangle(out, (0, out.shape[0] - 34), (out.shape[1], out.shape[0]), (28, 15, 10), -1)
            cv2.putText(out, status, (12, out.shape[0] - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (244, 236, 232), 1,
                        cv2.LINE_AA)
        return out

    def embeddings_from_images(self, frames: Iterable[np.ndarray]) -> list[np.ndarray]:
        out = []
        for frame in frames:
            faces = self.detect(frame)
            if self.quality(faces) is None:
                out.append(self.embed(frame, faces[0]))
        return out

    def capture(self, frames: Iterable[np.ndarray], n: int = 15, timeout: float = 20.0,
                on_frame: Callable[[np.ndarray, int, int], None] | None = None) -> list[np.ndarray]:
        """Pull frames until n usable ones are collected (or timeout). Returns embeddings.

        on_frame(annotated_bgr, collected, n) is called for every frame, for live display.
        """
        got: list[np.ndarray] = []
        t0 = time.time()
        for frame in frames:
            faces = self.detect(frame)
            problem = self.quality(faces)
            if problem is None:
                got.append(self.embed(frame, faces[0]))
            if on_frame:
                status = (f"captured {len(got)}/{n}" if problem is None
                          else f"{problem}  ({len(got)}/{n})")
                on_frame(self.annotate(frame, faces, status, ok=problem is None), len(got), n)
            if len(got) >= n or time.time() - t0 > timeout:
                break
        return got


class Camera:
    """Context manager yielding webcam frames (BGR)."""

    def __init__(self, index: int = 0, width: int = 960, height: int = 540):
        self.index, self.width, self.height = index, width, height
        self._cap = None

    def __enter__(self) -> "Camera":
        api = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(self.index, api)
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open camera {self.index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        for _ in range(5):          # let auto-exposure settle
            self._cap.read()
        return self

    def frames(self):
        while True:
            ok, frame = self._cap.read()
            if not ok:
                raise RuntimeError("camera stopped returning frames")
            yield cv2.flip(frame, 1)   # mirror, like a selfie view

    def __exit__(self, *exc) -> None:
        if self._cap is not None:
            self._cap.release()
