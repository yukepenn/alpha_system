"""Tests for the completed Claude PreToolUse/PostToolUse guard modes.

These lock the behavior that the guards (a) actually inspect the tool path from
Claude's stdin payload, (b) only enforce on write-class tools so outside-repo
reads are never blocked, (c) fail OPEN on malformed input, and (d) still serve
pre_commit's explicit-path mode unchanged.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ["python", "tools/hooks/boundary_guard.py", "--claude-pre-tool-use"]
ARTIFACT = ["python", "tools/hooks/artifact_guard.py", "--claude-post-tool-use"]

IN_REPO = str(ROOT / "src" / "alpha_system" / "x.py")
OUTSIDE = "/home/nobody/.ssh/evil"
FORBIDDEN_ARTIFACT = str(ROOT / "runs" / "demo" / "state.parquet")


def _run(cmd: list[str], payload) -> int:
    stdin = "" if payload is None else json.dumps(payload)
    return subprocess.run(cmd, input=stdin, text=True, capture_output=True, cwd=ROOT).returncode


# --- boundary guard (PreToolUse) -------------------------------------------------

def test_boundary_allows_in_repo_write() -> None:
    assert _run(BOUNDARY, {"tool_name": "Write", "tool_input": {"file_path": IN_REPO}}) == 0


def test_boundary_allows_outside_repo_read() -> None:
    # Read is not write-class; reading outside the repo (e.g. ~/.claude memory) is fine.
    assert _run(BOUNDARY, {"tool_name": "Read", "tool_input": {"file_path": OUTSIDE}}) == 0


def test_boundary_blocks_outside_repo_write() -> None:
    assert _run(BOUNDARY, {"tool_name": "Write", "tool_input": {"file_path": OUTSIDE}}) == 2


def test_boundary_fails_open_on_malformed_stdin() -> None:
    assert _run(BOUNDARY, None) == 0
    proc = subprocess.run(BOUNDARY, input="not json", text=True, capture_output=True, cwd=ROOT)
    assert proc.returncode == 0


# --- artifact guard (PostToolUse) ------------------------------------------------

def test_artifact_blocks_forbidden_write() -> None:
    assert _run(ARTIFACT, {"tool_name": "Write", "tool_input": {"file_path": FORBIDDEN_ARTIFACT}}) == 2


def test_artifact_allows_source_write() -> None:
    assert _run(ARTIFACT, {"tool_name": "Write", "tool_input": {"file_path": IN_REPO}}) == 0


# --- explicit-path mode (pre_commit) still works ---------------------------------

def test_pre_commit_explicit_mode_unchanged() -> None:
    outside = subprocess.run(
        ["python", "tools/hooks/boundary_guard.py", "../escape.txt"],
        text=True, capture_output=True, cwd=ROOT,
    )
    assert outside.returncode == 1  # nonzero, but not the Claude-mode 2
    good = subprocess.run(
        ["python", "tools/hooks/boundary_guard.py", "src/alpha_system/__init__.py"],
        text=True, capture_output=True, cwd=ROOT,
    )
    assert good.returncode == 0
