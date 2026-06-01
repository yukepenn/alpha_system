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


def has_python_tests() -> bool:
    tests_dir = ROOT / "tests"
    if not tests_dir.exists():
        return False
    return any(
        path.is_file() and (path.name.startswith("test_") or path.name.endswith("_test.py"))
        for path in tests_dir.rglob("*.py")
    )


def check_required_files() -> int:
    missing = [path for path in REQUIRED_HARNESS_FILES if not (ROOT / path).exists()]
    if missing:
        print("Missing required harness files: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


def check_artifacts() -> int:
    forbidden_parts = {
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        ".venv",
        "cache",
    }
    tracked_result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if tracked_result.returncode or staged_result.returncode:
        print("Could not inspect git-tracked artifacts.", file=sys.stderr)
        return 1

    violations: list[str] = []
    paths = set(tracked_result.stdout.splitlines()) | set(staged_result.stdout.splitlines())
    for raw_path in paths:
        path = Path(raw_path)
        if any(part in forbidden_parts for part in path.parts):
            violations.append(raw_path)
    if violations:
        print("Forbidden tracked or staged artifacts found:")
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
        if has_python_tests():
            status |= run([sys.executable, "-m", "pytest"])
        else:
            print("No Python tests configured; skipping pytest.")
    if args.boundaries or selected:
        status |= check_boundaries()
    if args.artifacts or selected:
        status |= check_artifacts()

    if not any(vars(args).values()):
        parser.print_help()
    return 1 if status else 0


if __name__ == "__main__":
    raise SystemExit(main())
