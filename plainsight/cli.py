"""Command-line round-trip tester.

    python -m plainsight.cli mask   "secret text" --theme "dinner plans"
    python -m plainsight.cli unmask "benign text" --theme "dinner plans"
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
    args = ap.parse_args(argv)

    key = SharedKey.from_passphrase(args.key, theme=args.theme)

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
