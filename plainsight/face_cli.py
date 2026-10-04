"""Face key CLI. Uses the webcam (with a live tracking window) or image files.

    python -m plainsight.face_cli track                         # live landmark tracking, q to quit
    python -m plainsight.face_cli enroll --shared-key "sprinthack-demo" [--pin 1234]
    python -m plainsight.face_cli unlock [--pin 1234] [--show]
    python -m plainsight.face_cli encrypt "meet at noon" [--pin 1234]
    python -m plainsight.face_cli decrypt psf1:... [--pin 1234]
    python -m plainsight.face_cli forget
    python -m plainsight.face_cli selftest [--impostor other_person.jpg]   # live end-to-end check

Add --images a.jpg b.jpg ... to any capture command to use photos instead of the
camera, and --no-window to capture without the preview window.
"""
from __future__ import annotations
import argparse
import sys

from .biometric import FaceVault, FaceNotRecognized, WrongPin, default_vault_path

WINDOW = "PlainSight face key  (q to cancel)"


def capture_embeddings(images: list[str] | None, n: int, window: bool, camera: int = 0, timeout: float = 20.0):
    import cv2
    from .biometric.face import FaceTracker, Camera

    tracker = FaceTracker()
    if images:
        frames = []
        for p in images:
            img = cv2.imread(p)
            if img is None:
                raise SystemExit(f"could not read image {p}")
            frames.append(img)
        got = tracker.embeddings_from_images(frames)
        print(f"usable faces: {len(got)}/{len(frames)} images", file=sys.stderr)
        return got

    def show(img, got, need):
        cv2.imshow(WINDOW, img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            raise KeyboardInterrupt

    with Camera(camera) as cam:
        try:
            got = tracker.capture(cam.frames(), n=n, timeout=timeout, on_frame=show if window else None)
        finally:
            if window:
                cv2.destroyAllWindows()
    print(f"usable frames: {len(got)}/{n}", file=sys.stderr)
    return got


def unlock_vault(args):
    vault = FaceVault(args.vault)
    if not vault.exists():
        raise SystemExit(f"No face vault at {args.vault}. Run: python -m plainsight.face_cli enroll ...")
    emb = capture_embeddings(args.images, args.frames, not args.no_window, args.camera)
    if len(emb) < max(1, min(3, args.frames)):
        raise SystemExit("Not enough clear frames of one face. Face the camera in good light and retry.")
    try:
        return vault.unlock(emb, args.pin)
    except FaceNotRecognized:
        raise SystemExit("Face not recognized. Vault stays locked.")
    except WrongPin:
        raise SystemExit("Face recognized, but the PIN is wrong. Vault stays locked.")


def track(args) -> int:
    import cv2
    from .biometric.face import FaceTracker, Camera
    tracker = FaceTracker()
    with Camera(args.camera) as cam:
        for frame in cam.frames():
            faces = tracker.detect(frame)
            problem = tracker.quality(faces)
            cv2.imshow(WINDOW, tracker.annotate(frame, faces, problem or "tracking: ready for a key", problem is None))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cv2.destroyAllWindows()
    return 0


def selftest(args) -> int:
    """Live end-to-end check with a throwaway vault: enroll, unlock x3, encrypt/decrypt, impostor."""
    import os
    import tempfile
    import numpy as np
    from .biometric import fuzzy

    vault = FaceVault(os.path.join(tempfile.mkdtemp(prefix="plainsight-selftest-"), "vault.json"))
    window = not args.no_window
    results: list[tuple[str, bool, str]] = []

    print("1/4  Enroll: look at the camera.", file=sys.stderr)
    enroll_emb = capture_embeddings(args.images, 20, window, args.camera)
    if len(enroll_emb) < 10:
        raise SystemExit("FAIL: could not get 10 clear frames of one face to enroll.")
    unlocked = vault.enroll(enroll_emb, {"shared_key": "selftest-key"}, args.pin)
    token = unlocked.encrypt_text("The book swap is Saturday.")
    results.append(("enroll", True, f"{len(enroll_emb)} frames"))
    ref = fuzzy.summarize(enroll_emb)

    for i in range(3):
        print(f"2/4  Unlock {i + 1}/3: look at the camera (move a little between tries).", file=sys.stderr)
        emb = capture_embeddings(args.images, 12, window, args.camera)
        cos = float(fuzzy.summarize(emb) @ ref) if emb else float("nan")
        try:
            ok = vault.unlock(emb, args.pin).decrypt_text(token) == "The book swap is Saturday."
        except (FaceNotRecognized, WrongPin, ValueError):
            ok = False
        results.append((f"unlock {i + 1}", ok, f"similarity to enrollment {cos:.2f}"))

    print("3/4  Wrong PIN must fail.", file=sys.stderr)
    try:
        vault.unlock(enroll_emb, args.pin + "x")
        results.append(("wrong PIN rejected", False, "unlocked with a wrong PIN"))
    except WrongPin:
        results.append(("wrong PIN rejected", True, ""))

    if args.impostor:
        print("4/4  Impostor photo(s) must fail.", file=sys.stderr)
        imp = capture_embeddings(args.impostor, len(args.impostor), False)
        if not imp:
            results.append(("impostor rejected", False, "no usable face in the impostor image(s)"))
        else:
            cos = float(fuzzy.summarize(imp) @ ref)
            try:
                vault.unlock(imp, args.pin)
                results.append(("impostor rejected", False, f"UNLOCKED (similarity {cos:.2f})"))
            except FaceNotRecognized:
                results.append(("impostor rejected", True, f"similarity {cos:.2f}"))
    else:
        print("4/4  Skipped impostor check (pass --impostor photo.jpg to run it).", file=sys.stderr)

    vault.delete()
    print()
    for name, ok, note in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<20} {note}")
    passed = all(ok for _, ok, _ in results)
    print("\nSELFTEST:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plainsight.face_cli")
    ap.add_argument("action", choices=["track", "enroll", "unlock", "encrypt", "decrypt", "forget", "selftest"])
    ap.add_argument("text", nargs="?", help="text to encrypt, or token to decrypt")
    ap.add_argument("--shared-key", help="enroll: the PlainSight shared passphrase to lock in the vault")
    ap.add_argument("--pin", default="", help="optional PIN mixed into the key (must match at unlock)")
    ap.add_argument("--images", nargs="+", help="use these photos instead of the camera")
    ap.add_argument("--frames", type=int, default=15, help="usable frames to collect (camera)")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--no-window", action="store_true", help="capture without the live preview window")
    ap.add_argument("--vault", default=default_vault_path())
    ap.add_argument("--force", action="store_true", help="enroll: overwrite an existing vault")
    ap.add_argument("--show", action="store_true", help="unlock: print the stored shared key")
    ap.add_argument("--impostor", nargs="+", help="selftest: photo(s) of someone else, must NOT unlock")
    args = ap.parse_args(argv)

    if args.action == "track":
        return track(args)
    if args.action == "selftest":
        return selftest(args)

    if args.action == "forget":
        FaceVault(args.vault).delete()
        print(f"Deleted {args.vault}")
        return 0

    if args.action == "enroll":
        if not args.shared_key:
            raise SystemExit("enroll needs --shared-key (the passphrase your partner also holds)")
        vault = FaceVault(args.vault)
        if vault.exists() and not args.force:
            raise SystemExit(f"A vault already exists at {args.vault}. Use --force to replace it.")
        emb = capture_embeddings(args.images, max(args.frames, 20) if not args.images else args.frames,
                                 not args.no_window, args.camera)
        if len(emb) < (1 if args.images else 10):
            raise SystemExit("Not enough clear frames of one face to enroll. Face the camera in good light.")
        vault.enroll(emb, {"shared_key": args.shared_key}, args.pin)
        print(f"Enrolled from {len(emb)} frames. Vault written to {args.vault}"
              + (" (PIN required)" if args.pin else ""))
        return 0

    unlocked = unlock_vault(args)
    if args.action == "unlock":
        key = unlocked.secrets.get("shared_key", "")
        print("Unlocked. Shared key: " + (key if args.show else "*" * len(key) + "  (use --show to print)"))
    elif args.action == "encrypt":
        if args.text is None:
            raise SystemExit("encrypt needs the text to encrypt")
        print(unlocked.encrypt_text(args.text))
    elif args.action == "decrypt":
        if args.text is None:
            raise SystemExit("decrypt needs a psf1: token")
        try:
            print(unlocked.decrypt_text(args.text))
        except ValueError as e:
            raise SystemExit(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
