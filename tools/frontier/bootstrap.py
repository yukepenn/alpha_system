"""Frontier bootstrap diagnostics for alpha_system."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.config import FrontierConfigError, assert_valid_config, load_config


def doctor() -> int:
    required = ["AGENTS.md", "CLAUDE.md", "frontier.yaml", "campaigns", "specs", "handoffs", "reviews", "runs"]
    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        print("Frontier doctor found missing paths:")
        for item in missing:
            print(f"- {item}")
        return 1
    print("Frontier doctor passed.")
    return 0


def check_config() -> int:
    config = ROOT / "frontier.yaml"
    if not config.exists():
        print("frontier.yaml is missing.")
        return 1
    try:
        assert_valid_config(load_config(config), root=ROOT, check_commands=False)
    except FrontierConfigError as error:
        print(f"frontier.yaml is invalid: {error}")
        return 1
    print("frontier.yaml is valid.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frontier bootstrap helper.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check required harness files.")
    subparsers.add_parser("check-config", help="Check frontier.yaml has required sections.")
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return doctor()
    if args.command == "check-config":
        return check_config()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
