"""Run the eval harness.

    cd backend
    uv run python -m eval.run_eval --provider rules
    uv run python -m eval.run_eval --provider ollama --provider rules
    uv run python -m eval.run_eval --dataset arrivals --provider rules

Results land in ``backend/eval/results/`` (JSON + Markdown). ``GET /ai/eval``
serves the latest file, so the app can show the table.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import harness


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Yammic extraction eval harness")
    ap.add_argument("--provider", action="append", choices=["rules", "ollama", "claude"],
                    help="repeatable; default rules")
    ap.add_argument("--dataset", default="all", choices=["all", "gold", "arrivals"])
    ap.add_argument("--doc", action="append", help="limit to these document ids")
    ap.add_argument("--prompt-version", default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="print the full result JSON")
    ap.add_argument("--no-latest", action="store_true",
                    help="do not make this run the default latest.json (keep per-provider latest)")
    args = ap.parse_args(argv)
    names = args.provider or ["rules"]

    failed = 0
    for name in names:
        try:
            result = harness.evaluate(name, dataset=args.dataset,
                                      prompt_version=args.prompt_version, docs_subset=args.doc)
        except RuntimeError as exc:
            print(f"[{name}] unavailable: {exc}", file=sys.stderr)
            failed += 1
            continue
        run_path, md_path = harness.save(result, args.out, update_latest=not args.no_latest)
        print(harness.to_markdown(result))
        print(f"[{name}] wrote {run_path} and {md_path}")
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        hard = result["hardCases"].get("allPass")
        if not hard or result["summary"]["spanErrors"]:
            failed += 1
        if result["summary"]["f1"] is not None and result["summary"]["f1"] < 0.9:
            print(f"[{name}] WARNING: F1 below 0.9", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
