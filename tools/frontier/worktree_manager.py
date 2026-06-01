"""Safe Frontier-owned Git worktree manager."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.git_utils import git, repo_name, sanitize_component
from tools.frontier.provider_config import load_provider_config


@dataclass(frozen=True)
class WorktreePlan:
    campaign_id: str
    phase_id: str
    branch: str
    path: str
    dry_run: bool


def phase_branch_name(campaign_id: str, phase_id: str, slug: str | None = None) -> str:
    campaign = sanitize_component(campaign_id, fallback="campaign")
    phase = sanitize_component(phase_id, fallback="phase")
    suffix = sanitize_component(slug or phase_id, fallback="phase")
    return f"auto/{campaign}/{phase}-{suffix}"[:180]


def validate_worktree_root(repo_root: Path, requested_root: Path | None = None) -> Path:
    repo_root = repo_root.resolve()
    allowed_parent = repo_root.parent
    root = (requested_root or allowed_parent).resolve()
    if root != allowed_parent and allowed_parent not in root.parents:
        raise ValueError("Worktree root must be the repository parent or a directory below it.")
    return root


def phase_worktree_path(
    repo_root: Path,
    campaign_id: str,
    phase_id: str,
    requested_root: Path | None = None,
) -> Path:
    root = validate_worktree_root(repo_root, requested_root)
    name = "-".join(
        [
            sanitize_component(repo_name(repo_root), fallback="repo"),
            sanitize_component(campaign_id, fallback="campaign"),
            sanitize_component(phase_id, fallback="phase"),
        ]
    )
    return (root / name).resolve()


def is_frontier_branch(branch: str) -> bool:
    return branch.startswith("auto/")


def is_frontier_owned_worktree(repo_root: Path, path: Path, branch: str | None = None) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    allowed_parent = repo_root.resolve().parent
    if resolved == repo_root.resolve():
        return False
    if allowed_parent not in resolved.parents:
        return False
    prefix = sanitize_component(repo_name(repo_root), fallback="repo") + "-"
    if not resolved.name.startswith(prefix):
        return False
    return branch is None or is_frontier_branch(branch)


class WorktreeManager:
    def __init__(self, repo_root: Path | None = None, worktree_root: Path | None = None) -> None:
        self.repo_root = (repo_root or ROOT).resolve()
        self.worktree_root = validate_worktree_root(self.repo_root, worktree_root)

    def plan(self, campaign_id: str, phase_id: str, slug: str | None = None, *, dry_run: bool = True) -> WorktreePlan:
        branch = phase_branch_name(campaign_id, phase_id, slug)
        path = phase_worktree_path(self.repo_root, campaign_id, phase_id, self.worktree_root)
        return WorktreePlan(campaign_id, phase_id, branch, str(path), dry_run)

    def create(self, campaign_id: str, phase_id: str, slug: str | None = None, *, dry_run: bool = True) -> WorktreePlan:
        plan = self.plan(campaign_id, phase_id, slug, dry_run=dry_run)
        if dry_run:
            return plan
        path = Path(plan.path)
        if path.exists():
            raise FileExistsError(f"Worktree path already exists: {path}")
        result = git(self.repo_root, "worktree", "add", "-b", plan.branch, plan.path)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return plan

    def remove(self, path: Path, branch: str, *, dry_run: bool = True) -> dict[str, Any]:
        if not is_frontier_owned_worktree(self.repo_root, path, branch):
            raise ValueError(f"Refusing to remove non-Frontier worktree: {path}")
        action: dict[str, Any] = {"path": str(path), "branch": branch, "dry_run": dry_run}
        if not dry_run:
            result = git(self.repo_root, "worktree", "remove", str(path))
            action["return_code"] = result.returncode
            action["stderr"] = result.stderr
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return action

    def list(self) -> list[dict[str, str]]:
        result = git(self.repo_root, "worktree", "list", "--porcelain")
        if result.returncode != 0:
            return []
        entries: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if not line:
                if current:
                    entries.append(current)
                    current = {}
                continue
            key, _, value = line.partition(" ")
            current[key] = value
        if current:
            entries.append(current)
        return entries

    def clean_stale(self, *, dry_run: bool = True) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for entry in self.list():
            path = Path(entry.get("worktree", ""))
            branch = entry.get("branch", "").removeprefix("refs/heads/")
            if not is_frontier_owned_worktree(self.repo_root, path, branch):
                continue
            if path.exists():
                continue
            action = {"path": str(path), "branch": branch, "dry_run": dry_run}
            actions.append(action)
            if not dry_run:
                result = git(self.repo_root, "worktree", "remove", str(path))
                action["return_code"] = result.returncode
                action["stderr"] = result.stderr
        return actions


def worktree_mode_enabled(explicit: bool | None = None, root: Path | None = None) -> bool:
    if explicit is not None:
        return explicit
    return load_provider_config(root or ROOT).default_worktree_mode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Frontier-owned Git worktrees.")
    subparsers = parser.add_subparsers(dest="command")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--campaign-id", required=True)
    plan_parser.add_argument("--phase-id", required=True)
    plan_parser.add_argument("--slug")
    subparsers.add_parser("list")
    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    manager = WorktreeManager(ROOT, load_provider_config(ROOT).worktree_root)
    if args.command == "plan":
        print(json.dumps(asdict(manager.plan(args.campaign_id, args.phase_id, args.slug)), indent=2, sort_keys=True))
        return 0
    if args.command == "list":
        print(json.dumps(manager.list(), indent=2, sort_keys=True))
        return 0
    if args.command == "clean":
        print(json.dumps(manager.clean_stale(dry_run=not args.apply), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
