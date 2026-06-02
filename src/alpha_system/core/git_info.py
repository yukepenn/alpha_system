"""Best-effort git metadata capture for reproducible registry records."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class GitInfo:
    """Captured git state, or a well-defined unavailable result."""

    commit: str | None
    dirty: bool | None
    available: bool
    root: str | None
    status_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def capture_git_info(repo_path: str | Path = ".") -> GitInfo:
    """Capture commit and dirty state without failing when git is unavailable."""
    path = Path(repo_path)
    try:
        root = _git(path, "rev-parse", "--show-toplevel").stdout.strip()
        commit = _git(path, "rev-parse", "HEAD").stdout.strip()
        status = _git(path, "status", "--porcelain").stdout
    except FileNotFoundError as exc:
        return GitInfo(
            commit=None,
            dirty=None,
            available=False,
            root=None,
            status_message=f"git executable unavailable: {exc}",
        )
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        return GitInfo(
            commit=None,
            dirty=None,
            available=False,
            root=None,
            status_message=f"git metadata unavailable: {message}",
        )

    return GitInfo(
        commit=commit,
        dirty=bool(status.strip()),
        available=True,
        root=root,
        status_message="ok",
    )
