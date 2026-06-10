"""Frontier pre-push hook.

Git feeds pre-push hooks one line per ref update on stdin:

    <local_ref> <local_sha> <remote_ref> <remote_sha>

Force pushes are forbidden (AGENTS.md Git rules). A force push is a
non-fast-forward update: the remote sha exists and is not an ancestor of the
local sha. Branch deletions (local sha all zeros) stay allowed for non-main
refs; deleting ``refs/heads/main`` is blocked. New remote refs (remote sha all
zeros) are always fast-forward. stdin is only consumed when it is not a TTY so
manual invocation keeps the historical smoke+canary behavior.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTECTED_DELETE_REFS = ("refs/heads/main",)


def strict_artifacts_present() -> bool:
    handoffs = ROOT / "handoffs"
    reviews = ROOT / "reviews"
    if not handoffs.exists() or not reviews.exists():
        return False
    has_handoff = any(path.suffix == ".md" for path in handoffs.rglob("*") if path.is_file())
    has_review = any(path.suffix in {".md", ".json"} for path in reviews.rglob("*") if path.is_file())
    return has_handoff and has_review


def _is_zero_sha(sha: str) -> bool:
    return set(sha) == {"0"}


def git_is_ancestor(ancestor_sha: str, descendant_sha: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def force_push_violations(
    lines: list[str],
    is_ancestor: Callable[[str, str], bool] = git_is_ancestor,
) -> list[str]:
    """Return policy violations for the pre-push stdin ref-update lines.

    An unknown remote sha makes ``is_ancestor`` False, which is the
    conservative (blocking) answer: the remote is ahead of us and only a force
    push could win.
    """
    violations: list[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, remote_ref, remote_sha = parts
        if _is_zero_sha(remote_sha):
            continue  # creating a new remote ref is always fast-forward
        if _is_zero_sha(local_sha):
            if remote_ref in PROTECTED_DELETE_REFS:
                violations.append(f"Deleting protected ref {remote_ref} is forbidden.")
            continue  # deleting non-main remote branches stays allowed
        if not is_ancestor(remote_sha, local_sha):
            violations.append(
                f"Non-fast-forward push to {remote_ref}: remote {remote_sha[:12]} is not an "
                f"ancestor of local {local_sha[:12]}. Force push is forbidden (AGENTS.md Git rules)."
            )
    return violations


def main() -> int:
    if not sys.stdin.isatty():
        ref_lines = [line.strip() for line in sys.stdin if line.strip()]
        violations = force_push_violations(ref_lines)
        if violations:
            for violation in violations:
                print(violation)
            return 1
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
