"""Frontier verification entry point for alpha_system."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HARNESS_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "frontier.yaml",
    "ACTIVE_CAMPAIGN.md",
]


def run(command: list[str]) -> int:
    print("+ " + " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def check_required_files() -> int:
    missing = [path for path in REQUIRED_HARNESS_FILES if not (ROOT / path).exists()]
    if missing:
        print("Missing required harness files: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


def check_artifacts() -> int:
    forbidden_parts = {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        ".venv",
        "cache",
    }
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if any(part in forbidden_parts for part in path.parts):
            violations.append(str(path.relative_to(ROOT)))
    if violations:
        print("Forbidden local artifacts found:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


def check_boundaries() -> int:
    return check_required_files()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Frontier verification checks.")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--typecheck", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--boundaries", action="store_true")
    parser.add_argument("--artifacts", action="store_true")
    args = parser.parse_args(argv)

    selected = args.all or args.ci
    status = 0

    if args.smoke or selected:
        status |= check_required_files()
    if args.lint or selected:
        print("Lint check scaffold: configure project-specific lint command in frontier.yaml.")
    if args.typecheck or selected:
        print("Typecheck scaffold: configure project-specific typecheck command in frontier.yaml.")
    if args.test or selected:
        if (ROOT / "tests").exists():
            status |= run([sys.executable, "-m", "pytest"])
        else:
            print("No tests directory found; skipping pytest.")
    if args.boundaries or selected:
        status |= check_boundaries()
    if args.artifacts or selected:
        status |= check_artifacts()

    if not any(vars(args).values()):
        parser.print_help()
    return 1 if status else 0


if __name__ == "__main__":
    raise SystemExit(main())
