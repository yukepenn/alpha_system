"""Regression tests for the parallel-Workflow-2 (dag_wave) harness hardening.

Covers the behaviors introduced/changed for parallel build + serial merge so they
cannot silently regress: codex service_tier config, thread-safe state snapshots,
narrowly-scoped README union-merge, pre-merge base-sync conflict classification,
in-tree remote-branch cleanup, core.bare restoration after gh, and
wait_pr_mergeable polling.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.frontier import github_utils, ralph_driver
from tools.frontier.command_runner import CommandResult
from tools.frontier.provider_config import (
    ProviderConfigError,
    _resolve_service_tier,
    load_provider_config,
)


# --------------------------------------------------------------------------- #
# codex service_tier config (provider_config / provider_adapters / frontier.yaml)
# --------------------------------------------------------------------------- #


def test_resolve_service_tier_alias_and_identity() -> None:
    assert _resolve_service_tier("fast") == "priority"
    assert _resolve_service_tier("FAST") == "priority"  # case-insensitive alias
    for tier in ("auto", "default", "flex", "priority", "scale"):
        assert _resolve_service_tier(tier) == tier


@pytest.mark.parametrize("bad", ["turbo", "", "   ", "fastest"])
def test_resolve_service_tier_rejects_unknown(bad: str) -> None:
    with pytest.raises(ProviderConfigError):
        _resolve_service_tier(bad)


def test_load_provider_config_service_tier_default_and_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_CODEX_SERVICE_TIER", raising=False)
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")

    # No env, no yaml under tmp_path -> default "fast" resolves to "priority".
    assert load_provider_config(tmp_path).codex_service_tier == "priority"

    # Env override wins and is validated.
    monkeypatch.setenv("FRONTIER_CODEX_SERVICE_TIER", "flex")
    assert load_provider_config(tmp_path).codex_service_tier == "flex"

    monkeypatch.setenv("FRONTIER_CODEX_SERVICE_TIER", "nonsense")
    with pytest.raises(ProviderConfigError):
        load_provider_config(tmp_path)


def test_codex_adapter_wires_service_tier_into_exec(tmp_path, monkeypatch) -> None:
    from tools.frontier.provider_adapters import CodexProviderAdapter

    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CODEX_CMD", "codex")
    monkeypatch.setenv("FRONTIER_CODEX_SANDBOX", "workspace-write")
    monkeypatch.setenv("FRONTIER_CODEX_SERVICE_TIER", "flex")
    config = load_provider_config(tmp_path)

    command = CodexProviderAdapter(config).build_command("prompt")
    assert command == ["codex", "exec", "-c", "service_tier=flex", "--sandbox", "workspace-write", "-"]


# --------------------------------------------------------------------------- #
# thread-safe state snapshot
# --------------------------------------------------------------------------- #


def test_state_snapshot_copies_nested_mutables() -> None:
    state = {
        "attempts": {"P0": 1},
        "repair_attempts": {"P0": 2},
        "phases": [{"phase_id": "P0", "status": "PASS"}],
        "scalar": 7,
    }
    snap = ralph_driver.state_snapshot_for_serialization(state)

    # The worker-mutated nested containers must be distinct objects.
    assert snap["attempts"] == {"P0": 1} and snap["attempts"] is not state["attempts"]
    assert snap["repair_attempts"] is not state["repair_attempts"]
    assert snap["phases"][0] is not state["phases"][0]

    # Mutating the live state after snapshotting must not bleed into the snapshot.
    state["attempts"]["P1"] = 9
    state["repair_attempts"]["P1"] = 9
    state["phases"][0]["status"] = "REWORK"
    assert "P1" not in snap["attempts"]
    assert "P1" not in snap["repair_attempts"]
    assert snap["phases"][0]["status"] == "PASS"


# --------------------------------------------------------------------------- #
# README-only union-merge scope
# --------------------------------------------------------------------------- #


def test_union_merge_attributes_are_scoped_to_readme(tmp_path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)

    ralph_driver.ensure_union_merge_attributes(tmp_path)
    attrs_path = tmp_path / ".git" / "info" / "attributes"
    text = attrs_path.read_text(encoding="utf-8")

    assert "README.md merge=union" in text
    # A blanket markdown union would hide real conflicts in load-bearing docs.
    assert "**/*.md merge=union" not in text

    # Idempotent: a second call does not duplicate the entry.
    ralph_driver.ensure_union_merge_attributes(tmp_path)
    assert attrs_path.read_text(encoding="utf-8").count("README.md merge=union") == 1


# --------------------------------------------------------------------------- #
# presync base-sync: real conflict vs. non-conflict merge failure
# --------------------------------------------------------------------------- #


def _git_stub(merge_rc: int, merge_out: str, unmerged: str):
    def fake_git(root, *args):
        if args and args[0] == "merge" and "--abort" not in args:
            return SimpleNamespace(returncode=merge_rc, stdout=merge_out, stderr="")
        if args[:2] == ("ls-files", "-u"):
            return SimpleNamespace(returncode=0, stdout=unmerged, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return fake_git


def test_presync_reports_true_conflict(monkeypatch) -> None:
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root: "main")
    monkeypatch.setattr(
        ralph_driver, "git", _git_stub(1, "CONFLICT (content): merge conflict in x", "100644 abc 1\tx\n")
    )
    report = ralph_driver.presync_phase_branch_with_base(Path("/x"), "auto/c/p")
    assert report["conflict"] is True
    assert report["merge_failed"] is False
    assert report["synced"] is False


def test_presync_reports_non_conflict_merge_failure_distinctly(monkeypatch) -> None:
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root: "main")
    monkeypatch.setattr(
        ralph_driver,
        "git",
        _git_stub(1, "error: Your local changes would be overwritten by merge", ""),
    )
    report = ralph_driver.presync_phase_branch_with_base(Path("/x"), "auto/c/p")
    assert report["merge_failed"] is True
    assert report["conflict"] is False
    assert report.get("error")


def test_presync_success_syncs_and_pushes(monkeypatch) -> None:
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root: "main")
    monkeypatch.setattr(ralph_driver, "git", _git_stub(0, "", ""))
    report = ralph_driver.presync_phase_branch_with_base(Path("/x"), "auto/c/p")
    assert report["synced"] is True
    assert report["pushed"] is True
    assert report["conflict"] is False
    assert report["merge_failed"] is False


# --------------------------------------------------------------------------- #
# in-tree (non-worktree) post-merge remote-branch deletion
# --------------------------------------------------------------------------- #


def _patch_cleanup_env(monkeypatch, tmp_path, calls):
    monkeypatch.setattr(ralph_driver, "git", lambda root, *args: (calls.append(list(args)), SimpleNamespace(returncode=0, stdout="", stderr=""))[1])
    monkeypatch.setattr(ralph_driver, "restore_local_repo_after_merge", lambda *a, **k: {})
    monkeypatch.setattr(ralph_driver, "provider_phase_dir", lambda rd, ph: tmp_path)
    monkeypatch.setattr(ralph_driver, "append_event", lambda *a, **k: None)


def test_in_tree_merge_deletes_frontier_remote_branch(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []
    _patch_cleanup_env(monkeypatch, tmp_path, calls)
    state = {"worktree_mode": False, "mock_providers": False}
    phase = {"merged": True, "branch": "auto/camp/p00", "phase_id": "P00"}

    ralph_driver.cleanup_phase_worktree_after_merge(tmp_path, state, phase)

    assert ["push", "origin", "--delete", "auto/camp/p00"] in calls


def test_in_tree_merge_skips_non_frontier_branch(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []
    _patch_cleanup_env(monkeypatch, tmp_path, calls)
    state = {"worktree_mode": False, "mock_providers": False}
    phase = {"merged": True, "branch": "feature/manual", "phase_id": "P00"}

    ralph_driver.cleanup_phase_worktree_after_merge(tmp_path, state, phase)

    assert not any(c[:1] == ["push"] for c in calls)


def test_in_tree_merge_skips_remote_delete_under_mock(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []
    _patch_cleanup_env(monkeypatch, tmp_path, calls)
    state = {"worktree_mode": False, "mock_providers": True}
    phase = {"merged": True, "branch": "auto/camp/p00", "phase_id": "P00"}

    ralph_driver.cleanup_phase_worktree_after_merge(tmp_path, state, phase)

    assert not any(c[:1] == ["push"] for c in calls)


# --------------------------------------------------------------------------- #
# core.bare restoration after a gh call
# --------------------------------------------------------------------------- #


class _OkRunner:
    def run(self, command, **kwargs):
        del kwargs
        return CommandResult(command=list(command), return_code=0, stdout="ok", stderr="", duration_ms=1)


def test_run_gh_restores_core_bare_when_flipped(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_git(root, *args):
        calls.append(list(args))
        bare = args[:2] == ("rev-parse", "--is-bare-repository")
        return SimpleNamespace(returncode=0, stdout=("true" if bare else ""), stderr="")

    monkeypatch.setattr(github_utils, "git", fake_git)
    github_utils._run_gh(["gh", "pr", "view", "3"], root=Path("/x"), runner=_OkRunner())

    assert ["config", "core.bare", "false"] in calls


def test_run_gh_leaves_core_bare_untouched_when_not_bare(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_git(root, *args):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="false", stderr="")

    monkeypatch.setattr(github_utils, "git", fake_git)
    github_utils._run_gh(["gh", "pr", "view", "3"], root=Path("/x"), runner=_OkRunner())

    assert ["config", "core.bare", "false"] not in calls


# --------------------------------------------------------------------------- #
# wait_pr_mergeable polling
# --------------------------------------------------------------------------- #


def _patch_mergeable(monkeypatch, *, blocked=False, merged=False, state="CLEAN"):
    monkeypatch.setattr(github_utils.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(github_utils, "view_pr", lambda *a, **k: SimpleNamespace(blocked=blocked))
    monkeypatch.setattr(github_utils, "_pr_is_merged", lambda data: merged)
    monkeypatch.setattr(github_utils, "_pr_data_from_result", lambda v: {"mergeStateStatus": state})


def test_wait_pr_mergeable_true_when_clean(monkeypatch) -> None:
    _patch_mergeable(monkeypatch, state="CLEAN")
    assert github_utils.wait_pr_mergeable(3, initial_delay_seconds=0) is True


def test_wait_pr_mergeable_true_when_already_merged(monkeypatch) -> None:
    _patch_mergeable(monkeypatch, merged=True, state="BLOCKED")
    assert github_utils.wait_pr_mergeable(3, initial_delay_seconds=0) is True


def test_wait_pr_mergeable_false_on_dirty_conflict(monkeypatch) -> None:
    _patch_mergeable(monkeypatch, state="DIRTY")
    assert github_utils.wait_pr_mergeable(3, initial_delay_seconds=0) is False
