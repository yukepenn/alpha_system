"""Detect obvious test weakening unless exact paths are authorized."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


SELF_PATH = "tools/hooks/test_tamper_guard.py"
HARNESS_SELF_TESTS = {
    "tests/test_hooks.py",
    "tests/test_canaries.py",
}
FORBIDDEN_PATTERNS = [
    re.compile(r"pytest\.skip\s*\("),
    re.compile(r"@pytest\.mark\.skip"),
    re.compile(r"@pytest\.mark\.xfail"),
    re.compile(r"\.only\s*\("),
    re.compile(r"\bit\.only\s*\("),
    re.compile(r"\bdescribe\.only\s*\("),
    re.compile(r"assert\s+True\b"),
    re.compile(r"assert\s+1\s*==\s*1\b"),
]


def normalized(path: str | Path) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def allowed_paths() -> set[str]:
    raw = os.environ.get("FRONTIER_ALLOWED_TEST_PATHS", "")
    return {normalized(part.strip()) for part in raw.split(",") if part.strip()}


def should_check(path: Path) -> bool:
    clean = normalized(path)
    if clean == SELF_PATH or clean in HARNESS_SELF_TESTS or clean in allowed_paths():
        return False
    return "test" in path.parts or path.name.startswith("test_") or path.name.endswith("_test.py")


def file_has_violation(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect obvious test weakening.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    violations: list[str] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not should_check(path):
            continue
        if path.exists() and path.is_file() and file_has_violation(path):
            violations.append(raw_path)
    for violation in violations:
        print(f"Possible test tamper pattern: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
