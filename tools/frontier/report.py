"""Frontier report helper."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_summary(run_id: str) -> int:
    path = ROOT / "runs" / run_id / "RUN_SUMMARY.md"
    if not path.exists():
        print(f"No summary found for run {run_id}")
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read Frontier reports.")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.run_id:
        return run_summary(args.run_id)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
