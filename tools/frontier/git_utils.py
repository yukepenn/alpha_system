"""Small safe Git helpers for Frontier runtime tools."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tools.frontier.artifact_policy import curate_commit_paths


ROOT = Path(__file__).resolve().parents[2]
SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class GitPhaseResult:
    dry_run: bool
    branch: str
    changed_files: list[str]
    staged_files: list[str]
    blocked_files: list[str]
    commit_sha: str | None = None
    pushed: bool = False
    commands: list[list[str]] = field(default_factory=list)
    status_before: str = ""
    status_after: str = ""
    diff_stat: str = ""
    message: str = ""

    @property
    def ok(self) -> bool:
        return not self.blocked_files

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    blocked = {
        ("reset", "--hard"),
        ("clean", "-fd"),
        ("clean", "-fdx"),
        ("push", "--force"),
        ("push", "-f"),
    }
    if len(args) >= 2 and tuple(args[:2]) in blocked:
        raise ValueError(f"Refusing destructive git command: git {' '.join(args)}")
    if len(args) >= 2 and args[0] == "add" and args[1] in {".", "-A"}:
        raise ValueError(f"Refusing broad git staging command: git {' '.join(args)}")
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def current_branch(root: Path = ROOT) -> str:
    result = git(root, "branch", "--show-current")
    return result.stdout.strip()


def repo_name(root: Path = ROOT) -> str:
    return root.resolve().name


def sanitize_component(value: str, *, fallback: str = "frontier") -> str:
    cleaned = SLUG_RE.sub("-", value.strip()).strip(".-_/").lower()
    return cleaned[:80] or fallback


def _status_paths(status_text: str) -> list[str]:
    paths: list[str] = []
    for line in status_text.splitlines():
        if not line:
            continue
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        paths.append(payload.strip())
    return paths


def status_porcelain(root: Path = ROOT) -> str:
    result = git(root, "status", "--porcelain")
    return result.stdout if result.returncode == 0 else ""


def changed_files(root: Path = ROOT) -> list[str]:
    return _status_paths(status_porcelain(root))


def staged_files(root: Path = ROOT) -> list[str]:
    result = git(root, "diff", "--cached", "--name-only")
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def diff_stat(root: Path = ROOT) -> str:
    result = git(root, "diff", "--stat", "HEAD")
    return result.stdout if result.returncode == 0 else ""


def remote_url(root: Path = ROOT, remote: str = "origin") -> str | None:
    result = git(root, "remote", "get-url", remote)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def checkout_or_create_branch(root: Path, branch: str, *, dry_run: bool = False) -> list[list[str]]:
    commands = [["git", "checkout", "-B", branch]]
    if not dry_run:
        result = git(root, "checkout", "-B", branch)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return commands


def stage_paths(root: Path, paths: list[str], *, dry_run: bool = False) -> list[list[str]]:
    commands: list[list[str]] = []
    for path in paths:
        command = ["git", "add", "--", path]
        commands.append(command)
        if not dry_run:
            result = git(root, "add", "--", path)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return commands


def commit_staged(root: Path, message: str, *, dry_run: bool = False) -> tuple[str | None, list[list[str]]]:
    command = ["git", "commit", "-m", message]
    if dry_run:
        return None, [command]
    result = git(root, "commit", "-m", message)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    sha = git(root, "rev-parse", "HEAD").stdout.strip()
    return sha or None, [command]


def push_branch(root: Path, branch: str, *, dry_run: bool = False) -> tuple[bool, list[list[str]]]:
    command = ["git", "push", "-u", "origin", branch]
    if dry_run:
        return False, [command]
    result = git(root, "push", "-u", "origin", branch)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return True, [command]


def commit_phase_changes(
    *,
    root: Path,
    campaign_id: str,
    phase_id: str,
    summary: str,
    branch: str,
    config: Mapping[str, Any],
    dry_run: bool,
    push: bool,
) -> GitPhaseResult:
    artifacts = config.get("artifacts") if isinstance(config.get("artifacts"), Mapping) else {}
    allow_patterns = list(artifacts.get("allow_commit", [])) if isinstance(artifacts, Mapping) else []
    forbid_patterns = list(artifacts.get("forbid_commit", [])) if isinstance(artifacts, Mapping) else []
    status_before = status_porcelain(root)
    files = changed_files(root)
    allowed, blocked = curate_commit_paths(
        files,
        allow_patterns=allow_patterns,
        forbid_patterns=forbid_patterns,
    )
    commands: list[list[str]] = []
    commands.extend(checkout_or_create_branch(root, branch, dry_run=dry_run))
    commands.extend(stage_paths(root, allowed, dry_run=dry_run))
    stat = diff_stat(root)
    sha: str | None = None
    pushed = False
    message = f"{campaign_id}/{phase_id}: {summary}"
    if allowed:
        commit_sha, commit_commands = commit_staged(root, message, dry_run=dry_run)
        sha = commit_sha
        commands.extend(commit_commands)
        if push:
            pushed, push_commands = push_branch(root, branch, dry_run=dry_run)
            commands.extend(push_commands)
    status_after = status_porcelain(root)
    return GitPhaseResult(
        dry_run=dry_run,
        branch=branch,
        changed_files=files,
        staged_files=allowed,
        blocked_files=blocked,
        commit_sha=sha,
        pushed=pushed,
        commands=commands,
        status_before=status_before,
        status_after=status_after,
        diff_stat=stat,
        message=message,
    )


def write_git_phase_artifacts(phase_dir: Path, result: GitPhaseResult) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "git_phase.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (phase_dir / "changed_files.txt").write_text("\n".join(result.changed_files) + "\n", encoding="utf-8")
    (phase_dir / "diff_stat.txt").write_text(result.diff_stat, encoding="utf-8")
    (phase_dir / "git_status_before_commit.txt").write_text(result.status_before, encoding="utf-8")
    (phase_dir / "git_status_after_commit.txt").write_text(result.status_after, encoding="utf-8")
    (phase_dir / "branch.txt").write_text(result.branch + "\n", encoding="utf-8")
    if result.commit_sha:
        (phase_dir / "commit_sha.txt").write_text(result.commit_sha + "\n", encoding="utf-8")
    else:
        (phase_dir / "commit_sha.txt").write_text("", encoding="utf-8")
