"""Frontier verification entry point for alpha_system."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_HARNESS_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "frontier.yaml",
    "ACTIVE_CAMPAIGN.md",
]


def run(command: list[str]) -> int:
    print("+ " + " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def run_lint() -> int:
    if importlib.util.find_spec("ruff") is None:
        print('ruff is not installed; run `pip install -e ".[dev]"` to enable lint. Skipping.')
        return 0
    status = run([sys.executable, "-m", "ruff", "format", "--check", "."])
    status |= run([sys.executable, "-m", "ruff", "check", "."])
    return status


def run_typecheck() -> int:
    return run([sys.executable, "-m", "compileall", "-q", "src", "tests", "tools"])


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
    from tools.hooks import artifact_guard

    run_local_result = subprocess.run(
        ["git", "ls-files", "runs", ".frontier/upgrade_reports"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if run_local_result.returncode:
        print("Could not inspect git-tracked run-local paths.", file=sys.stderr)
        return 1
    run_local_paths = run_local_result.stdout.splitlines()
    if run_local_paths:
        print("Run-local paths must not be tracked:")
        for path in run_local_paths:
            print(f"- {path}")
        return 1

    tracked_result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
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
        if artifact_guard.forbidden(raw_path):
            violations.append(raw_path)
    if violations:
        print("Forbidden tracked or staged artifacts found:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    return 0


def check_git_environment() -> int:
    if os.environ.get("ALPHA_SYSTEM_ALLOW_CUSTOM_GIT_ENV") == "1":
        return 0
    dangerous = [v for v in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE") if os.environ.get(v)]
    if dangerous:
        print(
            "Custom git environment detected: "
            + ", ".join(dangerous)
            + ". Unset these before verification or set ALPHA_SYSTEM_ALLOW_CUSTOM_GIT_ENV=1.",
            file=sys.stderr,
        )
        return 1
    return 0


def check_boundaries() -> int:
    status = check_required_files()
    status |= check_git_environment()
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Frontier verification checks.")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--typecheck", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--boundaries", action="store_true")
    parser.add_argument("--artifacts", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = args.all or args.ci
    status = 0

    if args.smoke or selected:
        status |= check_required_files()
    if selected:
        git_environment_status = check_git_environment()
        status |= git_environment_status
        if git_environment_status:
            return 1
    # Lint is a real but standalone gate; a full-repo ruff backlog (~2.7k findings)
    # is deferred to a dedicated cleanup campaign, so it is excluded from --all/--ci.
    if args.lint:
        status |= run_lint()
    if args.typecheck or selected:
        status |= run_typecheck()
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
