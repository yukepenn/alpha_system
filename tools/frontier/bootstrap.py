"""Frontier bootstrap diagnostics for alpha_system."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
    text = config.read_text(encoding="utf-8")
    required_tokens = ["schema_version:", "workflow1:", "workflow2:", "lanes:"]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        print("frontier.yaml is missing required sections: " + ", ".join(missing))
        return 1
    print("frontier.yaml looks like a Frontier v3 control plane.")
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
