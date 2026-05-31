"""Frontier worktree helper."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def list_worktrees() -> int:
    return subprocess.run(["git", "worktree", "list"], cwd=ROOT, check=False).returncode


def clean() -> int:
    print("Worktree cleanup is a scaffold. Review `git worktree list` before removing paths.")
    return list_worktrees()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Frontier worktrees.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("list")
    subparsers.add_parser("clean")
    args = parser.parse_args(argv)
    if args.command == "list":
        return list_worktrees()
    if args.command == "clean":
        return clean()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
