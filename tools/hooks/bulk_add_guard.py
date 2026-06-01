"""Guard against accidental bulk staging."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAX_STAGED_FILES = 200


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def threshold() -> int:
    raw = os.environ.get("FRONTIER_BULK_ADD_MAX")
    if not raw:
        return DEFAULT_MAX_STAGED_FILES
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MAX_STAGED_FILES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block suspiciously large staged additions.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    files = args.paths or staged_files()
    max_files = threshold()
    if len(files) > max_files:
        print(f"Too many staged additions ({len(files)}). Stage curated paths only; limit is {max_files}.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
