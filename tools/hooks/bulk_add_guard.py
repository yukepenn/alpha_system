"""Guard against bulk staging mistakes."""

from __future__ import annotations

import argparse


MAX_STAGED_FILES = 200


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block suspiciously large staged changes.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    if len(args.paths) > MAX_STAGED_FILES:
        print(f"Too many staged files ({len(args.paths)}). Stage curated paths only.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
