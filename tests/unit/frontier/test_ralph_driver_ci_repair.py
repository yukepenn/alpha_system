from __future__ import annotations

import json
from pathlib import Path

from tools.frontier import ralph_driver
from tools.frontier.git_utils import GitPhaseResult, PushBranchResult, RemoteBranchResult
from tools.frontier.github_utils import CIStatusResult, GitHubResult


def _run_state(tmp_path: Path, *, repair_attempts: int = 0, max_repairs: int = 1) -> tuple[Path, dict, dict]:
    run_dir = tmp_path / "runs" / "2099Z_TEST"
    phase = {"phase_id": "TEST-P00", "name": "demo", "lane": "yellow", "status": "REVIEWED"}
    state = {
        "run_id": "2099Z_TEST",
        "campaign_id": "TEST",
        "workflow": "workflow2",
        "driver": ralph_driver.PROVIDER_WIRED_DRIVER,
        "status": "RUNNING",
        "current_phase_id": "TEST-P00",
        "current_micro_attempt": 1,
        "phases": [phase],
        "stop_requested": False,
        "last_event_id": 0,
        "mock_providers": False,
        "provider_wired": True,
        "provider_mode": "external",
        "max_repair_attempts": max_repairs,
        "repair_attempts": {"TEST-P00": repair_attempts},
        "lane_policy_snapshot": {"yellow": {"max_repair_attempts": max_repairs}},
        "estimated_cost_usd": 0.0,
        "required_campaign_files": [],
    }
    phase_dir = run_dir / "phases" / "TEST-P00"
    phase_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("", encoding="utf-8")
    (run_dir / "costs.jsonl").write_text("", encoding="utf-8")
    (phase_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (phase_dir / "validation.md").write_text("# Validation\n", encoding="utf-8")
    (phase_dir / "verdict.json").write_text(json.dumps({"verdict": "PASS"}), encoding="utf-8")
    return run_dir, state, phase


def _patch_post_phase_deps(monkeypatch, ci_results: list[CIStatusResult]) -> dict[str, int]:
    config = {
        "github": {"require_ci": True, "required_checks": ["validate"], "ci_timeout_seconds": 1, "ci_poll_seconds": 0},
        "project": {"default_branch": "main"},
        "workflow2": {"auto_pr": True},
        "git": {"auto_create_pr": True},
        "lanes": {"yellow": {"auto_pr": True, "auto_merge": True, "max_repair_attempts": 1}},
        "artifacts": {"allow_commit": ["tools/**", "tests/**"], "forbid_commit": ["runs/**"]},
    }
    counts = {"ci_waits": 0, "codex": 0, "logs": 0}

    monkeypatch.setattr(ralph_driver, "load_config", lambda _path: config)
    monkeypatch.setattr(ralph_driver, "write_active_campaign_for_phase_commit", lambda *a, **k: None)
    monkeypatch.setattr(ralph_driver, "phase_branch_from_artifacts", lambda *a, **k: "auto/test-p00")
    monkeypatch.setattr(ralph_driver, "phase_base_sha_from_artifacts", lambda *a, **k: "b" * 40)
    monkeypatch.setattr(ralph_driver, "ensure_phase_head", lambda *a, **k: None)
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda **_k: "main")
    monkeypatch.setattr(ralph_driver, "pr_body_text", lambda *a, **k: "body")
    monkeypatch.setattr(ralph_driver, "run_phase_validation", lambda _root: (True, "# repair validation\n"))

    def fake_commit_phase_changes(**kwargs):
        return GitPhaseResult(
            dry_run=False,
            branch=kwargs["branch"],
            changed_files=["tools/frontier/ralph_driver.py"],
            staged_files=["tools/frontier/ralph_driver.py"],
            blocked_files=[],
            commit_sha="a" * 40,
            pushed=False,
            base_sha=kwargs.get("base_sha"),
        )

    def fake_wait_for_ci(*_args, **_kwargs):
        counts["ci_waits"] += 1
        return ci_results.pop(0)

    def fake_collect_failed_ci_logs(*_args, **_kwargs):
        counts["logs"] += 1
        return GitHubResult("ci_failed_logs", False, ["gh", "run", "view", "1", "--log-failed"], stdout="failed log")

    def fake_codex(*_args, **_kwargs):
        counts["codex"] += 1
        return ralph_driver.CommandResult(("codex",), 0, "fixed", "")

    monkeypatch.setattr(ralph_driver, "commit_phase_changes", fake_commit_phase_changes)
    monkeypatch.setattr(ralph_driver, "push_phase_branch", lambda root, branch, remote, dry_run: PushBranchResult(False, branch, remote, ["git", "push"], pushed=True))
    monkeypatch.setattr(ralph_driver, "verify_remote_branch", lambda root, branch, remote: RemoteBranchResult(True, "a" * 40, "a" * 40, True, "", "", 0, branch, remote))
    monkeypatch.setattr(ralph_driver, "create_pr", lambda **_k: GitHubResult("create_pr", False, ["gh", "pr", "create"], metadata={"number": 7}))
    monkeypatch.setattr(ralph_driver, "wait_for_ci", fake_wait_for_ci)
    monkeypatch.setattr(ralph_driver, "collect_failed_ci_logs", fake_collect_failed_ci_logs)
    monkeypatch.setattr(ralph_driver, "codex_noninteractive", fake_codex)
    return counts


def _events(run_dir: Path) -> list[str]:
    return [json.loads(line)["event"] for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def _failed_ci() -> CIStatusResult:
    return CIStatusResult(
        "FAILURE",
        [{"name": "validate", "state": "FAILURE", "bucket": "fail", "link": "https://github.com/o/r/actions/runs/1"}],
        ["validate"],
        [],
        ["validate"],
        False,
        "failed",
    )


def test_ci_failure_with_remaining_budget_routes_repair_and_reenters_ci_wait(monkeypatch, tmp_path: Path) -> None:
    run_dir, state, phase = _run_state(tmp_path)
    counts = _patch_post_phase_deps(monkeypatch, [_failed_ci(), CIStatusResult("SUCCESS", [], ["validate"], [], [])])

    ok = ralph_driver.post_phase_git_github(
        run_dir, state, phase, "PASS", execution_root=tmp_path, defer_merge=True
    )

    assert ok is True
    assert counts["ci_waits"] == 2
    assert counts["codex"] == 1
    assert counts["logs"] == 1
    events = _events(run_dir)
    assert "CI_REPAIR_ROUTED" in events
    assert "CI_BLOCKED" not in events
    assert phase["status"] == ralph_driver.MERGE_READY
    assert (run_dir / "phases" / "TEST-P00" / "repair_attempts" / "ci_attempt_1" / "ci_failure.log").exists()


def test_ci_failure_with_exhausted_budget_stops_with_ci_blocked(monkeypatch, tmp_path: Path) -> None:
    run_dir, state, phase = _run_state(tmp_path, repair_attempts=1, max_repairs=1)
    counts = _patch_post_phase_deps(monkeypatch, [_failed_ci()])

    ok = ralph_driver.post_phase_git_github(
        run_dir, state, phase, "PASS", execution_root=tmp_path, defer_merge=True
    )

    assert ok is False
    assert counts["ci_waits"] == 1
    assert counts["codex"] == 0
    events = _events(run_dir)
    assert "CI_REPAIR_ROUTED" not in events
    assert "CI_BLOCKED" in events
    assert state["status"] == ralph_driver.CI_BLOCKED


def test_stop_file_prevents_ci_repair_routing(monkeypatch, tmp_path: Path) -> None:
    run_dir, state, phase = _run_state(tmp_path)
    (run_dir / "STOP").write_text("stop\n", encoding="utf-8")
    counts = _patch_post_phase_deps(monkeypatch, [_failed_ci()])

    ok = ralph_driver.post_phase_git_github(
        run_dir, state, phase, "PASS", execution_root=tmp_path, defer_merge=True
    )

    assert ok is False
    assert counts["ci_waits"] == 1
    assert counts["codex"] == 0
    assert "CI_REPAIR_ROUTED" not in _events(run_dir)
