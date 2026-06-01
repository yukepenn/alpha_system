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
