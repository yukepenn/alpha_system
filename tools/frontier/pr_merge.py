#!/usr/bin/env python3
"""Safe coordinator PR merge wrapper for Frontier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.github_utils import merge_pr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge a PR through the Frontier auto-first gh wrapper.")
    parser.add_argument("number", help="Pull request number.")
    parser.add_argument("--method", default="squash", choices=("squash", "merge", "rebase"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = merge_pr(args.number, method=args.method, root=ROOT, dry_run=args.dry_run)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
