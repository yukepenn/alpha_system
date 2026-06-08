"""Repository boundary guard.

Two call modes:

* ``boundary_guard.py <path>...`` - explicit-path mode used by ``pre_commit.py``.
  Returns 1 if any path escapes the repository root.
* ``boundary_guard.py --claude-pre-tool-use`` - Claude Code PreToolUse hook mode.
  Claude passes the tool payload as JSON on stdin; this mode extracts the target
  file path for *write-class* tools (Edit/Write/MultiEdit/NotebookEdit) and blocks
  (exit 2, per Claude hook semantics) if the write would land outside the repo.
  It is deliberately scoped to write-class tools so legitimate reads/searches of
  paths outside the repo (e.g. ``~/.claude`` memory) are never blocked, and it
  fails OPEN on any malformed/empty payload so a parse hiccup cannot brick a session.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# Tools that create or modify files on disk. Only these are boundary-enforced in
# Claude hook mode; read/search/exec tools are intentionally exempt.
WRITE_CLASS_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def inside_root(path: str) -> bool:
    try:
        resolved = (ROOT / path).resolve()
    except OSError:
        return False
    return resolved == ROOT or ROOT in resolved.parents


def _paths_from_claude_stdin() -> list[str]:
    """Extract write-target paths from a Claude PreToolUse stdin payload.

    Fails open (returns ``[]``) on any error so the hook never blocks on a parse
    problem. Only returns paths for write-class tools.
    """
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    if payload.get("tool_name") not in WRITE_CLASS_TOOLS:
        return []
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    paths: list[str] = []
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paths stay inside the repository.")
    parser.add_argument("--claude-pre-tool-use", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)

    paths = list(args.paths)
    if args.claude_pre_tool_use:
        paths.extend(_paths_from_claude_stdin())

    violations = [path for path in paths if not inside_root(path)]
    for violation in violations:
        print(f"Path escapes repository boundary: {violation}", file=sys.stderr)
    if not violations:
        return 0
    # Claude blocks the tool call on exit code 2; pre_commit treats any nonzero as fail.
    return 2 if args.claude_pre_tool_use else 1


if __name__ == "__main__":
    raise SystemExit(main())
