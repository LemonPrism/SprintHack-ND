"""Command-line round-trip tester.

    python -m plainsight.cli mask   "secret text" --theme "dinner plans"
    python -m plainsight.cli unmask "benign text" --theme "dinner plans"
    python -m plainsight.cli mask "secret text" --face [--pin 1234]   # shared key from the face vault
"""
from __future__ import annotations
import argparse
import sys

from .config import get_settings
from .key import SharedKey
from .providers import get_provider
from .codecs import get_codec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plainsight")
    ap.add_argument("action", choices=["mask", "unmask"])
    ap.add_argument("text", help="the message to mask or unmask")
    ap.add_argument("--theme", default="everyday chat", help="cover theme / persona")
    ap.add_argument("--key", default="sprinthack-demo", help="shared passphrase")
    ap.add_argument("--codec", default="prompt", choices=["prompt", "bidi", "keyed", "mock"])
    ap.add_argument("--face", action="store_true",
                    help="unlock the shared key from the face vault with the webcam (see face_cli)")
    ap.add_argument("--pin", default="", help="PIN for the face vault, if one was set")
    args = ap.parse_args(argv)

    passphrase = args.key
    if args.face:
        from .face_cli import unlock_vault
        from .biometric import default_vault_path
        face_args = argparse.Namespace(vault=default_vault_path(), images=None, frames=15,
                                       no_window=False, camera=0, pin=args.pin)
        passphrase = unlock_vault(face_args).secrets["shared_key"]
        print("Face recognized; using the shared key from the vault.", file=sys.stderr)

    key = SharedKey.from_passphrase(passphrase, theme=args.theme)

    # mock codec needs no provider; others do.
    provider = None if args.codec == "mock" else get_provider(get_settings())
    codec = get_codec(args.codec, provider)

    if args.action == "mask":
        print(codec.mask(args.text, key=key))
    else:
        print(codec.unmask(args.text, key=key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
