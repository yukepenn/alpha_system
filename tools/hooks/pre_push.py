"""Frontier pre-push hook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    checks = [
        [sys.executable, "tools/verify.py", "--smoke"],
        [sys.executable, "tools/hooks/canary_runner.py"],
    ]
    for command in checks:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
