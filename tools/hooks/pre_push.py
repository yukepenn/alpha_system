"""Frontier pre-push hook."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def strict_artifacts_present() -> bool:
    handoffs = ROOT / "handoffs"
    reviews = ROOT / "reviews"
    if not handoffs.exists() or not reviews.exists():
        return False
    has_handoff = any(path.suffix == ".md" for path in handoffs.rglob("*") if path.is_file())
    has_review = any(path.suffix in {".md", ".json"} for path in reviews.rglob("*") if path.is_file())
    return has_handoff and has_review


def main() -> int:
    if os.environ.get("FRONTIER_STRICT_PRE_PUSH") == "1" and not strict_artifacts_present():
        print("Strict pre-push requires handoff and review artifacts.")
        return 1
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
