"""The verification gate. Runs every frozen case through mask -> unmask and scores
field recovery + benign-ness. Exits non-zero if below threshold so Claude Code (or
CI) can gate on it.

    python -m evaluation.run_eval --codec mock                 # harness self-test -> 1.00
    python -m evaluation.run_eval --codec prompt               # real masking (needs API key)
    python -m evaluation.run_eval --codec keyed --min-recovery 0.98
    python -m evaluation.run_eval --codec prompt --report out.json
"""
from __future__ import annotations
import argparse
import json
import os
import sys

from plainsight.config import get_settings
from plainsight.key import SharedKey
from plainsight.providers import get_provider
from plainsight.codecs import get_codec
from evaluation.score import score_case, CaseResult

CASES_PATH = os.path.join(os.path.dirname(__file__), "cases.json")


def _load_cases() -> list[dict]:
    with open(CASES_PATH, encoding="utf-8") as f:
        return json.load(f)


def run(codec_name: str, theme: str, passphrase: str) -> list[CaseResult]:
    provider = None if codec_name == "mock" else get_provider(get_settings())
    codec = get_codec(codec_name, provider)
    results: list[CaseResult] = []
    for case in _load_cases():
        key = SharedKey.from_passphrase(passphrase, theme=theme)
        cover = codec.mask(case["secret"], key=key)
        recovered = codec.unmask(cover, key=key)
        results.append(score_case(case, cover, recovered))
    return results


def _print(results: list[CaseResult]) -> None:
    print(f"{'case':<18} {'recovery':>9} {'benign':>7}   missing / leaked")
    print("-" * 70)
    for r in results:
        notes = []
        if r.missing:
            notes.append("missing=" + ",".join(r.missing))
        if r.leaked:
            notes.append("leaked=" + ",".join(r.leaked))
        print(f"{r.id:<18} {r.recovery:>8.0%} {('ok' if r.benign_ok else 'FAIL'):>7}   {'; '.join(notes)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="run_eval")
    ap.add_argument("--codec", default="prompt", choices=["prompt", "bidi", "keyed", "mock"])
    ap.add_argument("--theme", default="party and gift planning")
    ap.add_argument("--key", default="sprinthack-demo")
    ap.add_argument("--min-recovery", type=float, default=0.90)
    ap.add_argument("--report", default=None, help="optional path to write a JSON report")
    args = ap.parse_args(argv)

    results = run(args.codec, args.theme, args.key)
    _print(results)

    agg = sum(r.recovery for r in results) / len(results)
    all_benign = all(r.benign_ok for r in results)
    print("-" * 70)
    print(f"aggregate recovery: {agg:.0%}   all benign: {all_benign}   "
          f"(threshold {args.min_recovery:.0%})")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump([r.__dict__ for r in results], f, indent=2, ensure_ascii=False)
        print(f"wrote report -> {args.report}")

    ok = agg >= args.min_recovery and all_benign
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
