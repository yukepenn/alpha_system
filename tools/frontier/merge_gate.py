"""Frontier merge-gate scaffold."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview Frontier merge policy. Does not merge.")
    parser.add_argument("--phase")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    phase = args.phase or "current"
    print(f"Merge gate scaffold for {phase}: no real merge was performed.")
    print("Wire CI status, verdict JSON, branch protection, and explicit authorization before enabling merges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
