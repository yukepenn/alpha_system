from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from tools.frontier import ralph_driver
from tools.frontier.cleanup import run_frontier_cleanup
from tools.frontier.runs_retention import RunsRetentionPolicy, apply_runs_retention, plan_runs_retention
from tools.frontier.runtime_paths import persistent_tmp_root


def _completed_run(root: Path, name: str, *, status: str = "COMPLETED", stop: bool = False, age_days: int = 0) -> Path:
    run_dir = root / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / "state.json"
    state_path.write_text(json.dumps({"run_id": name, "status": status, "phases": []}) + "\n", encoding="utf-8")
    if stop:
        (run_dir / "STOP").write_text("stop\n", encoding="utf-8")
    mtime = (datetime.now(UTC) - timedelta(days=age_days)).timestamp()
    os.utime(state_path, (mtime, mtime))
    os.utime(run_dir, (mtime, mtime))
    return run_dir


def _result(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _write_frontier_yaml(root: Path) -> None:
    (root / "frontier.yaml").write_text(
        """schema_version: "frontier-harness-v3"
project:
  default_branch: "main"
providers:
  mock:
    enabled: false
workflow2:
  enabled: true
  auto_pr: true
  auto_merge: true
  max_phases: 1
  max_micro_loops_default: 1
  max_repair_attempts_default: 1
  max_run_minutes: 60
  max_phase_minutes: 60
  max_estimated_usd: 0
  semantic_done_check_required: true
  worktree_mode: false
github:
  auto_create_pr: true
  ci_timeout_seconds: 1
  ci_poll_seconds: 1
  required_checks: []
  require_ci: true
  require_branch_protection: true
  allow_unprotected_dry_run: true
  merge_method: "squash"
git:
  auto_create_pr: true
  explicit_add_only: true
  forbid_git_add_dot: true
  forbid_git_add_A: true
  forbid_force_push: true
artifacts:
  allow_commit: ["docs/**"]
  forbid_commit: ["runs/**"]
lanes:
  green:
    require_claude_review: false
    auto_pr: true
    auto_merge: true
    max_repair_attempts: 1
    merge_policy:
      allow_pass_with_warnings: true
  yellow:
    require_claude_review: true
    auto_pr: true
    auto_merge: true
    max_repair_attempts: 1
    merge_policy:
      allow_pass_with_warnings: true
  red:
    require_claude_review: true
    auto_pr: false
    auto_merge: false
    max_repair_attempts: 1
    merge_policy:
      allow_pass_with_warnings: false
""",
        encoding="utf-8",
    )


def test_persistent_tmp_root_uses_alpha_system_root_outside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {"ALPHA_SYSTEM_ROOT": str(tmp_path.parent / f"{tmp_path.name}_alpha_root")}

    tmp = persistent_tmp_root(repo_root=repo, env=env)

    assert tmp == (Path(env["ALPHA_SYSTEM_ROOT"]) / ".tmp").resolve()
    assert tmp.is_dir()
    assert repo.resolve() not in tmp.parents


def test_runs_retention_protects_active_and_unresolved_stop_then_rotates_completed_run(tmp_path: Path) -> None:
    env = {"ALPHA_SYSTEM_ROOT": str(tmp_path.parent / f"{tmp_path.name}_alpha_root")}
    active = _completed_run(tmp_path, "2026-01-03T000000Z_ACTIVE", age_days=1)
    old_completed = _completed_run(tmp_path, "2026-01-01T000000Z_DONE", stop=True, age_days=60)
    halted = _completed_run(tmp_path, "2026-01-02T000000Z_STOPPED", status="STOPPED", stop=True, age_days=60)
    policy = RunsRetentionPolicy(keep_last=1, max_age_days=30, backup_keep_last=2)

    plan = plan_runs_retention(repo_root=tmp_path, active_run_dir=active, policy=policy, env=env)

    protected = {(item["run_id"], item["reason"]) for item in plan["protected"]}
    assert (active.name, "active_run") in protected
    assert (halted.name, "unresolved_stop") in protected
    assert [item["run_id"] for item in plan["rotated"]] == [old_completed.name]

    applied = apply_runs_retention(
        repo_root=tmp_path,
        active_run_dir=active,
        policy=policy,
        dry_run=False,
        env=env,
    )
    assert not old_completed.exists()
    assert Path(applied["rotated"][0]["to"]).is_dir()
    assert active.is_dir()
    assert halted.is_dir()


def test_post_merge_cleanup_uses_existing_worktree_seam_and_shared_retention(monkeypatch, tmp_path: Path) -> None:
    _write_frontier_yaml(tmp_path)
    run_dir = tmp_path / "runs" / "RUN1"
    phase_dir = run_dir / "phases" / "P00"
    phase_dir.mkdir(parents=True)
    state = {"worktree_mode": False, "mock_providers": False, "last_event_id": 0, "run_id": "RUN1"}
    phase = {"phase_id": "P00", "merged": True, "branch": "auto/camp/p00"}
    calls: list[list[str]] = []
    cleanup_calls: list[dict[str, object]] = []

    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setattr(ralph_driver, "provider_phase_dir", lambda _run, _phase: phase_dir)
    monkeypatch.setattr(ralph_driver, "restore_local_repo_after_merge", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(ralph_driver, "runtime_config", lambda: SimpleNamespace(worktree_root=None))
    monkeypatch.setattr(ralph_driver, "local_branch_exists", lambda _root, _branch: True)

    def fake_git(_root: Path, *args: str) -> SimpleNamespace:
        calls.append(list(args))
        if args == ("branch", "--show-current"):
            return _result(stdout="main\n")
        return _result()

    def fake_cleanup(**kwargs) -> dict[str, object]:
        cleanup_calls.append(dict(kwargs))
        return {
            "schema_version": "frontier-cleanup-v1",
            "dry_run": kwargs["dry_run"],
            "worktrees": {"stale": [{"path": "x"}]},
            "runs_retention": {"rotated": [{"run_id": "old"}]},
        }

    monkeypatch.setattr(ralph_driver, "git", fake_git)
    monkeypatch.setattr(ralph_driver, "run_frontier_cleanup", fake_cleanup)

    ralph_driver.cleanup_phase_worktree_after_merge(run_dir, state, phase)

    assert ["branch", "-D", "auto/camp/p00"] in calls
    assert ["push", "origin", "--delete", "auto/camp/p00"] in calls
    assert cleanup_calls and cleanup_calls[0]["active_run_dir"] == run_dir
    assert cleanup_calls[0]["dry_run"] is False
    report = json.loads((phase_dir / "post_merge_cleanup.json").read_text(encoding="utf-8"))
    assert report["worktrees"]["stale"]
    assert report["runs_retention"]["rotated"]


def test_shared_frontier_cleanup_is_dry_run_by_default(monkeypatch, tmp_path: Path) -> None:
    env = {"ALPHA_SYSTEM_ROOT": str(tmp_path.parent / f"{tmp_path.name}_alpha_root")}
    _completed_run(tmp_path, "2026-01-01T000000Z_DONE", age_days=60)
    monkeypatch.setenv("ALPHA_SYSTEM_ROOT", env["ALPHA_SYSTEM_ROOT"])
    monkeypatch.setattr("tools.frontier.cleanup.WorktreeManager.clean_stale", lambda self, dry_run=True: [])

    report = run_frontier_cleanup(
        repo_root=tmp_path,
        dry_run=True,
        policy=RunsRetentionPolicy(keep_last=1, max_age_days=30, backup_keep_last=2),
    )

    assert report["dry_run"] is True
    assert report["runs_retention"]["dry_run"] is True
    assert report["runs_retention"]["rotated"]


def test_done_check_warning_does_not_rewrite_reviewer_verdict(monkeypatch, tmp_path: Path) -> None:
    _write_frontier_yaml(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MOCK_COMMIT", raising=False)
    monkeypatch.setattr(ralph_driver, "run_phase_validation", lambda _root: (True, "# Validation\n"))
    monkeypatch.setattr(
        ralph_driver,
        "mock_done_check_text",
        lambda phase: "# Done\n\nFound a non-blocking warning.\n\nDONE_CHECK: PASS_WITH_WARNINGS\n",
    )
    campaign_dir = tmp_path / "campaigns" / "CLEANUP_PROVENANCE_TEST"
    campaign_dir.mkdir(parents=True)
    for name in ("GOAL.md", "PHASE_PLAN.md", "ACCEPTANCE.md", "RISK_REGISTER.md", "RUNBOOK.md"):
        (campaign_dir / name).write_text("# fixture\n", encoding="utf-8")
    (campaign_dir / "campaign.yaml").write_text(
        """campaign_id: CLEANUP_PROVENANCE_TEST
workflow: workflow2
phases:
  - id: P00
    name: Provenance fixture
    lane: GREEN
    dependencies: []
""",
        encoding="utf-8",
    )

    status = ralph_driver.run_provider_wired_campaign("CLEANUP_PROVENANCE_TEST", max_phases=1)

    assert status == 0
    run_dir = sorted((tmp_path / "runs").glob("*CLEANUP_PROVENANCE_TEST*"))[-1]
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    verdict = json.loads((run_dir / "phases" / "P00" / "verdict.json").read_text(encoding="utf-8"))
    done = json.loads((run_dir / "phases" / "P00" / "done_check.json").read_text(encoding="utf-8"))
    assert state["phases"][0]["status"] == "PASS_WITH_WARNINGS"
    assert verdict["verdict"] == "PASS"
    assert verdict["source"] == "review"
    assert done["verdict"] == "PASS_WITH_WARNINGS"
