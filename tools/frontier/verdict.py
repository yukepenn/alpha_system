"""Frontier review verdict helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_VERDICTS = {"PASS", "PASS_WITH_WARNINGS", "REWORK", "BLOCKED"}


def validate(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    verdict = data.get("verdict")
    if verdict not in VALID_VERDICTS:
        print(f"Invalid verdict {verdict!r}. Expected one of {sorted(VALID_VERDICTS)}")
        return 1
    print(f"Verdict {verdict} is valid.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Frontier review verdict JSON.")
    parser.add_argument("path", type=Path, nargs="?")
    args = parser.parse_args(argv)
    if not args.path:
        parser.print_help()
        return 0
    return validate(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
