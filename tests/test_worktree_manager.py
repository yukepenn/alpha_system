from __future__ import annotations

from pathlib import Path

import pytest

from tools.frontier.worktree_manager import (
    WorktreeManager,
    is_frontier_owned_worktree,
    phase_branch_name,
    phase_worktree_path,
    validate_worktree_root,
)
from tools.frontier.git_utils import git


def init_repo_with_origin(root: Path, remote: Path) -> None:
    remote.mkdir()
    assert git(remote, "init", "--bare").returncode == 0
    assert git(root, "init", "-b", "main").returncode == 0
    assert git(root, "config", "user.email", "frontier@example.invalid").returncode == 0
    assert git(root, "config", "user.name", "Frontier Test").returncode == 0
    (root / "README.md").write_text("# Base\n", encoding="utf-8")
    assert git(root, "add", "--", "README.md").returncode == 0
    assert git(root, "commit", "-m", "test: base").returncode == 0
    assert git(root, "remote", "add", "origin", str(remote)).returncode == 0
    assert git(root, "push", "-u", "origin", "main").returncode == 0


def test_branch_name_sanitization(tmp_path) -> None:
    branch = phase_branch_name("Campaign 1", "P 01", "Build Thing!")

    assert branch == "auto/campaign-1/p-01-build-thing"


def test_safe_worktree_path_creation(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    path = phase_worktree_path(repo, "Campaign 1", "P01")

    assert path.parent == tmp_path
    assert path.name == "repo-campaign-1-p01"


def test_dry_run_worktree_plan(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    plan = WorktreeManager(repo).plan("C1", "P1", "Slug")

    assert plan.dry_run
    assert plan.branch == "auto/c1/p1-slug"
    assert Path(plan.path).parent == tmp_path


def test_protects_non_frontier_paths(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert not is_frontier_owned_worktree(repo, tmp_path / "other")
    with pytest.raises(ValueError):
        validate_worktree_root(repo, tmp_path.parent)


def test_remove_refuses_non_frontier_path(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    manager = WorktreeManager(repo)

    with pytest.raises(ValueError):
        manager.remove(tmp_path / "other", "main", dry_run=True)


def test_cleanup_after_merge_removes_worktree_and_auto_branches(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    worktree = tmp_path / "repo-c1-p00"
    repo.mkdir()
    init_repo_with_origin(repo, remote)
    branch = "auto/c1/p00"
    assert git(repo, "worktree", "add", "-b", branch, str(worktree), "main").returncode == 0
    (worktree / "docs").mkdir()
    (worktree / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    assert git(worktree, "add", "--", "docs/a.md").returncode == 0
    assert git(worktree, "commit", "-m", "C1/P00: phase").returncode == 0
    assert git(worktree, "push", "-u", "origin", f"HEAD:refs/heads/{branch}").returncode == 0

    result = WorktreeManager(repo).cleanup_after_merge(worktree, branch, dry_run=False)

    assert result["ok"] is True
    assert not worktree.exists()
    assert git(repo, "show-ref", "--verify", f"refs/heads/{branch}").returncode != 0
    remote_check = git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    assert remote_check.returncode == 0
    assert remote_check.stdout.strip() == ""
