"""Frontier pre-commit hook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    files = staged_files()
    checks = [
        [sys.executable, "tools/hooks/secret_scan.py", *files],
        [sys.executable, "tools/hooks/artifact_guard.py", *files],
        [sys.executable, "tools/hooks/bulk_add_guard.py", *files],
        [sys.executable, "tools/hooks/test_tamper_guard.py", *files],
        [sys.executable, "tools/hooks/forbidden_pattern_guard.py", *files],
        [sys.executable, "tools/hooks/boundary_guard.py", *files],
    ]
    for command in checks:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
