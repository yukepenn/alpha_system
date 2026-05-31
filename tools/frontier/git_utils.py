"""Small Git helpers for Frontier scaffolding."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def current_branch(root: Path) -> str:
    result = git(root, "branch", "--show-current")
    return result.stdout.strip()
