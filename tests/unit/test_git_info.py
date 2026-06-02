from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_capture_git_info_reports_commit_when_git_is_available() -> None:
    info = capture_git_info(REPO_ROOT)

    if info.available:
        assert info.commit
        assert info.root
        assert isinstance(info.dirty, bool)
        assert info.status_message == "ok"
    else:
        assert info.commit is None
        assert info.dirty is None
        assert info.status_message


def test_capture_git_info_degrades_when_git_executable_is_unavailable(
    monkeypatch: Any,
) -> None:
    def raise_missing_git(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", raise_missing_git)

    info = capture_git_info(REPO_ROOT)

    assert info.available is False
    assert info.commit is None
    assert info.dirty is None
    assert "unavailable" in info.status_message
