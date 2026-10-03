"""Turn a run_eval JSON report into slide-ready tables (Markdown + CSV).

    python -m evaluation.run_eval --codec prompt --report out.json
    python -m evaluation.export_table out.json --md evaluation/results.md --csv evaluation/results.csv
"""
from __future__ import annotations
import argparse
import csv
import json
import sys


def _md_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def to_markdown(results: list[dict], title: str, note: str | None = None) -> str:
    agg = sum(r["recovery"] for r in results) / len(results)
    benign = sum(1 for r in results if r["benign_ok"])
    lines = [
        f"# {title}",
        "",
        f"**Aggregate recovery:** {agg:.0%} · **Benign covers:** {benign}/{len(results)}",
        "",
        *([f"> {note}", ""] if note else []),
        "| Case | Recovery | Benign | Missing | Leaked |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['recovery']:.0%} | {'yes' if r['benign_ok'] else 'no'} | "
            f"{_md_cell(', '.join(r['missing']) or '-')} | {_md_cell(', '.join(r['leaked']) or '-')} |"
        )
    lines += ["", "## Messages", ""]
    for r in results:
        lines += [
            f"### {r['id']}",
            f"- **Cover (what an eavesdropper sees):** {_md_cell(r['cover'])}",
            f"- **Recovered:** {_md_cell(r['recovered'])}",
            "",
        ]
    return "\n".join(lines)


def to_csv(results: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "recovery", "benign_ok", "missing", "leaked", "cover", "recovered"])
        for r in results:
            w.writerow([r["id"], f"{r['recovery']:.2f}", r["benign_ok"], "; ".join(r["missing"]),
                        "; ".join(r["leaked"]), r["cover"], r["recovered"]])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_table")
    ap.add_argument("report", help="JSON written by run_eval --report")
    ap.add_argument("--md", help="write a Markdown table here")
    ap.add_argument("--csv", help="write a CSV table here")
    ap.add_argument("--title", default="PlainSight evaluation results")
    ap.add_argument("--note", default=None, help="caveat line shown under the headline numbers")
    args = ap.parse_args(argv)

    with open(args.report, encoding="utf-8") as f:
        results = json.load(f)
    if not results:
        print("report is empty", file=sys.stderr)
        return 1

    md = to_markdown(results, args.title, args.note)
    if args.md:
        with open(args.md, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
        print(f"wrote {args.md}")
    if args.csv:
        to_csv(results, args.csv)
        print(f"wrote {args.csv}")
    if not args.md and not args.csv:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
