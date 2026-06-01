from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path

import pytest

from tools.frontier import ralph_driver
from tools.frontier.git_utils import GitPhaseResult, PushBranchResult, RemoteBranchResult
from tools.frontier.github_utils import BranchProtectionResult, GitHubResult


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CAMPAIGN_ID = "SAMPLE_WORKFLOW2_CAMPAIGN"


def copy_campaign(tmp_root: Path, campaign_id: str) -> None:
    source = REPO_ROOT / "campaigns" / campaign_id
    target = tmp_root / "campaigns" / campaign_id
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def write_sample_campaign(tmp_root: Path, campaign_id: str = SAMPLE_CAMPAIGN_ID) -> None:
    (tmp_root / "frontier.yaml").write_text(
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
  max_phases: 2
  max_micro_loops_default: 1
  max_repair_attempts_default: 1
  max_run_minutes: 60
  max_phase_minutes: 60
  max_estimated_usd: 0
  semantic_done_check_required: true
  worktree_mode: false
  worktree_mode_recommended: true
github:
  auto_create_pr: true
  ci_timeout_seconds: 1
  ci_poll_seconds: 1
  required_checks: []
  require_ci: true
  require_branch_protection: true
  allow_unprotected_green_merge: false
  allow_unprotected_dry_run: true
  merge_method: "squash"
git:
  auto_create_pr: true
  explicit_add_only: true
  forbid_git_add_dot: true
  forbid_git_add_A: true
  forbid_force_push: true
artifacts:
  allow_commit: ["docs/**", "src/**", "tests/**"]
  forbid_commit: ["runs/**", "**/.env"]
lanes:
  green:
    required_checks: []
    require_claude_review: false
    auto_pr: true
    auto_merge: true
    max_micro_loops: 1
    max_repair_attempts: 1
    max_phase_minutes: 60
    max_changed_files: 50
    merge_policy:
      allow_pass_with_warnings: true
  yellow:
    required_checks: []
    require_claude_review: true
    auto_pr: true
    auto_merge: true
    max_micro_loops: 1
    max_repair_attempts: 1
    max_phase_minutes: 60
    max_changed_files: 50
    merge_policy:
      allow_pass_with_warnings: true
  red:
    required_checks: []
    require_claude_review: true
    auto_pr: false
    auto_merge: false
    max_micro_loops: 1
    max_repair_attempts: 1
    max_phase_minutes: 60
    merge_policy:
      allow_pass_with_warnings: false
""",
        encoding="utf-8",
    )
    campaign_dir = tmp_root / "campaigns" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "GOAL.md").write_text(f"# {campaign_id}\n\nExercise generic Workflow 2.\n", encoding="utf-8")
    (campaign_dir / "PHASE_PLAN.md").write_text(
        "# Phase Plan\n\n| Phase | Name | Lane | Dependencies |\n"
        "| --- | --- | --- | --- |\n"
        "| P00 | Prepare fixture | YELLOW | none |\n"
        "| P01 | Validate fixture | GREEN | P00 |\n",
        encoding="utf-8",
    )
    (campaign_dir / "campaign.yaml").write_text(
        f"""campaign_id: "{campaign_id}"
workflow: "workflow2"
default_lane: "yellow"
limits:
  max_phases: 2
phases:
  - id: "P00"
    name: "Prepare fixture"
    lane: "YELLOW"
    dependencies: []
  - id: "P01"
    name: "Validate fixture"
    lane: "GREEN"
    dependencies: ["P00"]
""",
        encoding="utf-8",
    )
    for name in ("ACCEPTANCE.md", "RISK_REGISTER.md", "RUNBOOK.md"):
        (campaign_dir / name).write_text(f"# {name}\n\nLocal test fixture.\n", encoding="utf-8")


def latest_run(tmp_root: Path, campaign_id: str) -> Path:
    matches = sorted((tmp_root / "runs").glob(f"*{campaign_id}*"))
    assert matches
    return matches[-1]


def pass_count(run_dir: Path) -> int:
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    return sum(1 for phase in state["phases"] if phase["status"] == "PASS")


def state_json(run_dir: Path) -> dict:
    return json.loads((run_dir / "state.json").read_text(encoding="utf-8"))


def write_passed_phase_artifacts(run_dir: Path, phase_id: str = "P00") -> Path:
    phase_dir = run_dir / "phases" / phase_id
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    (phase_dir / "executor_output.md").write_text("# Existing Execution\n", encoding="utf-8")
    (phase_dir / "validation.md").write_text("# Validation\n\nPassed.\n", encoding="utf-8")
    (phase_dir / "review.md").write_text("# Review\n\nVERDICT: PASS\n", encoding="utf-8")
    ralph_driver.write_json(
        phase_dir / "verdict.json",
        {
            "schema_version": "frontier-review-verdict-v1",
            "verdict": "PASS",
            "severity": "none",
            "findings": [],
            "source": "review",
        },
    )
    (phase_dir / "done_check.md").write_text("# Done Check\n\nDONE_CHECK: PASS\n", encoding="utf-8")
    ralph_driver.write_json(phase_dir / "done_check.json", {"verdict": "PASS"})
    return phase_dir


def write_merge_resume_artifacts(
    run_dir: Path,
    phase_id: str = "P00",
    *,
    branch: str = "auto/sample/p00-fixture",
    sha: str = "c" * 40,
    pr_number: int = 7,
    changed_files: list[str] | None = None,
) -> Path:
    changed_files = changed_files or ["docs/a.md"]
    phase_dir = write_passed_phase_artifacts(run_dir, phase_id)
    ralph_driver.write_json(
        phase_dir / "git_phase.json",
        {
            "dry_run": False,
            "branch": branch,
            "commit_sha": sha,
            "changed_files": changed_files,
            "blocked_files": [],
        },
    )
    (phase_dir / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    (phase_dir / "branch.txt").write_text(branch + "\n", encoding="utf-8")
    (phase_dir / "commit_sha.txt").write_text(sha + "\n", encoding="utf-8")
    ralph_driver.write_json(
        phase_dir / "push_branch.json",
        {
            "dry_run": False,
            "branch": branch,
            "remote": "origin",
            "return_code": 0,
            "pushed": True,
        },
    )
    ralph_driver.write_json(
        phase_dir / "remote_branch.json",
        {
            "exists": True,
            "remote_sha": sha,
            "local_sha": sha,
            "matches": True,
            "return_code": 0,
            "branch": branch,
            "remote": "origin",
        },
    )
    ralph_driver.write_json(
        phase_dir / "pr_create.json",
        {
            "action": "create_pr",
            "dry_run": False,
            "blocked": False,
            "return_code": 0,
            "metadata": {"number": pr_number, "head": branch, "base": "main"},
        },
    )
    ralph_driver.write_json(
        phase_dir / "ci_status.json",
        {
            "state": "SUCCESS",
            "checks": [{"name": "validate", "state": "SUCCESS", "bucket": "pass"}],
            "required_checks": [],
            "missing_required": [],
            "blocking_checks": [],
        },
    )
    ralph_driver.write_json(
        phase_dir / "branch_protection.json",
        {
            "status": "PASS",
            "protected": True,
            "branch": "main",
            "required_checks": [],
            "configured_required_checks": [],
            "missing_required_checks": [],
        },
    )
    return phase_dir


def stub_live_pr(
    monkeypatch,
    *,
    sha: str = "c" * 40,
    diff_files: list[str] | None = None,
    state: str = "OPEN",
) -> None:
    diff_files = diff_files or ["docs/a.md"]

    def fake_view_pr(pr_number, root=ralph_driver.ROOT):
        del root
        return GitHubResult(
            "view_pr",
            False,
            ["gh", "pr", "view", str(pr_number), "--json", "headRefOid"],
            stdout=json.dumps({"number": pr_number, "state": state, "headRefOid": sha}),
            metadata={"pr": {"number": pr_number, "state": state, "headRefOid": sha}},
        )

    def fake_pr_diff(pr_number, root=ralph_driver.ROOT):
        del root
        return GitHubResult(
            "pr_diff",
            False,
            ["gh", "pr", "diff", str(pr_number), "--name-only"],
            stdout="\n".join(diff_files) + "\n",
            metadata={"artifact_source": "pr_diff", "files": diff_files},
        )

    monkeypatch.setattr(ralph_driver, "view_pr", fake_view_pr)
    monkeypatch.setattr(ralph_driver, "list_pr_diff_files", fake_pr_diff)


def prepare_merge_gate_resume_run(
    tmp_path: Path,
    monkeypatch,
    *,
    sha: str = "c" * 40,
    changed_files: list[str] | None = None,
) -> tuple[Path, Path]:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_ALLOW_AUTOMERGE", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = ralph_driver.MERGE_GATE_BLOCKED
    phase["branch"] = "auto/sample/p00-fixture"
    phase["commit_sha"] = sha
    phase["pr_number"] = 7
    state["status"] = ralph_driver.MERGE_GATE_BLOCKED
    state["current_phase_id"] = "P00"
    state["codex_called_by_driver"] = False
    state["claude_called_by_driver"] = False
    phase_dir = write_merge_resume_artifacts(run_dir, sha=sha, changed_files=changed_files)
    ralph_driver.write_state(run_dir, state)
    (run_dir / "STOP").write_text("previous merge gate stop\n", encoding="utf-8")
    return run_dir, phase_dir


def stub_successful_resume_gates(monkeypatch, *, order: list[str] | None = None) -> None:
    order = order if order is not None else []
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root=ralph_driver.ROOT: "main")
    monkeypatch.setattr(
        ralph_driver,
        "wait_for_ci",
        lambda *args, **kwargs: order.append("ci")
        or ralph_driver.classify_ci_checks(
            [{"name": "validate", "state": "SUCCESS", "bucket": "pass"}],
            required_checks=[],
        ),
    )
    monkeypatch.setattr(
        ralph_driver,
        "inspect_branch_protection",
        lambda **kwargs: order.append("branch_protection")
        or BranchProtectionResult(
            "PASS",
            True,
            kwargs["branch"],
            [],
            [],
            [],
            message="test",
        ),
    )
    real_gate = ralph_driver.evaluate_merge_gate

    def recording_gate(**kwargs):
        order.append("merge_gate")
        return real_gate(**kwargs)

    monkeypatch.setattr(ralph_driver, "evaluate_merge_gate", recording_gate)
    monkeypatch.setattr(
        ralph_driver,
        "perform_merge",
        lambda **kwargs: order.append("merge")
        or GitHubResult(
            "merge_pr",
            False,
            ["gh", "pr", "merge", str(kwargs["pr_number"])],
            return_code=0,
        ),
    )


def run_merge_gate_resume(run_dir: Path) -> int:
    return ralph_driver.main(
        [
            "resume",
            "--campaign-id",
            SAMPLE_CAMPAIGN_ID,
            "--run-dir",
            str(run_dir),
            "--phase-id",
            "P00",
            "--from-stage",
            "merge_gate",
            "--provider-wired",
            "--no-provider-replay",
        ]
    )


def stub_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        ralph_driver,
        "run_validation_commands",
        lambda: (True, "# Validation\n\nMock validation passed.\n"),
    )


def test_executor_prompt_declares_review_boundary() -> None:
    phase = {"phase_id": "P00", "name": "Prepare fixture", "lane": "YELLOW"}
    phase_dir = ralph_driver.ROOT / "runs/run1/phases/P00"

    prompt = ralph_driver.executor_prompt(phase, "# Spec\n", phase_dir)

    assert "Do not call Claude." in prompt
    assert "Do not run reviewer." in prompt
    assert "Do not create `review.md`." in prompt
    assert "Do not create `verdict.json`." in prompt
    assert "Do not create a PR." in prompt
    assert "Do not merge." in prompt
    assert "Do not mark the phase PASS." in prompt
    assert "Write execution output and handoff only." in prompt
    assert (
        "The Ralph driver owns validation, review, done-check, verdict, repair, "
        "PR, CI, and merge gate."
        in prompt
    )


def test_executor_created_review_and_verdict_are_quarantined(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    run_dir = tmp_path / "runs/run1"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    state = {"last_event_id": 0}
    phase = {"phase_id": "P00"}
    (phase_dir / "review.md").write_text("executor review\n", encoding="utf-8")
    (phase_dir / "verdict.json").write_text('{"verdict": "PASS"}\n', encoding="utf-8")

    ralph_driver.quarantine_executor_review_artifacts(phase_dir, run_dir, state, phase)

    assert not (phase_dir / "review.md").exists()
    assert not (phase_dir / "verdict.json").exists()
    assert (phase_dir / "executor_notes_review.md").read_text(encoding="utf-8") == "executor review\n"
    assert (phase_dir / "executor_notes_verdict.json").is_file()
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "EXECUTOR_REVIEW_ARTIFACT_QUARANTINED" in events


def test_generic_campaign_yaml_phases_are_loaded(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)

    assert campaign.campaign_id == SAMPLE_CAMPAIGN_ID
    assert [phase.phase_id for phase in campaign.phases] == ["P00", "P01"]
    assert campaign.phases[0].name == "Prepare fixture"
    assert campaign.phases[0].lane == "YELLOW"
    assert campaign.phases[1].dependencies == ("P00",)


def test_ledger_only_run_creates_required_artifacts(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", ledger_only=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    for name in (
        "RUN_GOAL.md",
        "PHASE_PLAN.md",
        "state.json",
        "events.jsonl",
        "progress.txt",
        "costs.jsonl",
        "RUN_SUMMARY.md",
        "STOP",
    ):
        assert (run_dir / name).is_file(), name

    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["campaign_id"] == SAMPLE_CAMPAIGN_ID
    assert state["workflow"] == "workflow2"
    assert state["driver"] == ralph_driver.LEDGER_ONLY_DRIVER
    assert state["status"] == "LEDGER_ONLY_READY"
    assert len(state["phases"]) == 2
    assert all(phase["status"] == "PENDING" for phase in state["phases"])
    assert all(phase["execution_mode"] == "ledger_only" for phase in state["phases"])
    assert state["phase_execution_performed"] is False
    assert state["external_providers_called"] is False
    assert state["network_used"] is False
    assert state["github_operations_performed"] is False
    assert state["auto_merge_performed"] is False
    assert state["broker_or_trading_operations_performed"] is False


def test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    stub_validation(monkeypatch)

    status = ralph_driver.main(
        [
            "run",
            "--campaign-id",
            SAMPLE_CAMPAIGN_ID,
            "--provider-wired",
        ]
    )

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["driver"] == ralph_driver.PROVIDER_WIRED_DRIVER
    assert state["max_phases_requested"] == 1
    assert state["max_phases_source"] == "env"
    assert state["status"] == "STOPPED"
    assert pass_count(run_dir) == 1
    assert state["phases"][0]["status"] == "PASS"
    assert state["phases"][1]["status"] == "PENDING"
    assert (run_dir / "STOP").is_file()
    assert (run_dir / "phases/P00/spec_prompt.md").is_file()
    assert (run_dir / "phases/P00/executor_output.md").is_file()
    assert (run_dir / "phases/P00/validation.md").is_file()
    assert (run_dir / "phases/P00/review.md").is_file()
    assert (run_dir / "phases/P00/verdict.json").is_file()
    assert (run_dir / "phases/P00/done_check.json").is_file()
    assert (run_dir / "phases/P00/ci_status.json").is_file()
    assert (run_dir / "phases/P00/merge_gate.json").is_file()
    assert (run_dir / "heartbeat.json").is_file()


def test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MAX_PHASES", raising=False)
    stub_validation(monkeypatch)

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["max_phases_source"] == "campaign"
    assert state["max_phases_requested"] == 2
    assert state["status"] == "COMPLETED"
    assert pass_count(run_dir) == 2
    assert (run_dir / "STOP").is_file()
    assert (run_dir / "campaign_done_check.json").is_file()


def test_mock_review_rework_then_repair_passes(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    stub_validation(monkeypatch)
    responses = iter(
        [
            "# Review\n\n- Must repair mock issue.\n\nVERDICT: REWORK\n",
            "# Review\n\n- Repair accepted.\n\nVERDICT: PASS\n",
        ]
    )
    monkeypatch.setattr(ralph_driver, "mock_review_text", lambda phase: next(responses))

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = state_json(run_dir)
    assert state["repair_attempts"]["P00"] == 1
    assert state["phases"][0]["status"] == "PASS"
    assert (run_dir / "phases/P00/repair_attempts/001/repair_verdict.json").is_file()


def test_repair_attempts_are_capped(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    monkeypatch.setenv("FRONTIER_MAX_REPAIR_ATTEMPTS", "1")
    stub_validation(monkeypatch)
    monkeypatch.setattr(
        ralph_driver,
        "mock_review_text",
        lambda phase: "# Review\n\n- Still incomplete.\n\nVERDICT: REWORK\n",
    )

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    state = state_json(run_dir)
    assert state["status"] == "STOPPED"
    assert state["phases"][0]["status"] == "BLOCKED"
    assert state["repair_attempts"]["P00"] == 1


def test_resume_from_spec_ready_continues_without_regenerating_spec(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    stub_validation(monkeypatch)
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "SPEC_READY"
    state["current_phase_id"] = "P00"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert (phase_dir / "spec.md").read_text(encoding="utf-8") == "# Existing Spec\n"
    assert state_json(run_dir)["phases"][0]["status"] == "PASS"


def test_resume_from_executed_continues_to_review(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    stub_validation(monkeypatch)
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "EXECUTED"
    state["current_phase_id"] = "P00"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    (phase_dir / "executor_output.md").write_text("# Existing Execution\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert (phase_dir / "validation.md").is_file()
    assert state_json(run_dir)["phases"][0]["status"] == "PASS"


def test_push_failure_blocks_before_pr_create_and_preserves_review_verdict(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "REVIEWED"
    phase["branch"] = "auto/sample/p00-fixture"
    phase_dir = write_passed_phase_artifacts(run_dir)
    ralph_driver.write_state(run_dir, state)
    sha = "a" * 40

    monkeypatch.setattr(
        ralph_driver,
        "commit_phase_changes",
        lambda **kwargs: GitPhaseResult(
            dry_run=False,
            branch=kwargs["branch"],
            changed_files=["docs/a.md"],
            staged_files=["docs/a.md"],
            blocked_files=[],
            commit_sha=sha,
        ),
    )
    monkeypatch.setattr(ralph_driver, "ensure_phase_head", lambda root, branch, commit_sha: None)
    monkeypatch.setattr(
        ralph_driver,
        "push_phase_branch",
        lambda root, branch, remote="origin", dry_run=False: PushBranchResult(
            dry_run=False,
            branch=branch,
            remote=remote,
            command=["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"],
            return_code=1,
            stderr="auth failed",
            instructions="Network/auth push failed. Fix git push output and resume the run.",
        ),
    )
    pr_calls = []

    def fail_if_pr_called(**kwargs):
        pr_calls.append(kwargs)
        raise AssertionError("PR creation must not run when push fails.")

    monkeypatch.setattr(ralph_driver, "create_pr", fail_if_pr_called)

    ok = ralph_driver.post_phase_git_github(run_dir, state, phase, "PASS", execution_root=tmp_path)

    assert ok is False
    updated = state_json(run_dir)
    assert updated["status"] == ralph_driver.PUSH_BLOCKED
    assert updated["phases"][0]["status"] == ralph_driver.PUSH_BLOCKED
    assert pr_calls == []
    assert (phase_dir / "push_branch.json").is_file()
    assert not (phase_dir / "pr_create.json").exists()
    verdict = json.loads((phase_dir / "verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "PASS"
    assert verdict["source"] == "review"
    assert "push branch failed" in (run_dir / "RUN_SUMMARY.md").read_text(encoding="utf-8")
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "BRANCH_PUSH_BLOCKED" in events


def test_resume_from_push_block_retries_gates_without_provider_or_new_commit(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_CREATE_PR", "1")
    monkeypatch.setenv("FRONTIER_MERGE_DRY_RUN", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    branch = "auto/sample/p00-fixture"
    sha = "b" * 40
    phase.update(
        {
            "status": ralph_driver.PUSH_BLOCKED,
            "branch": branch,
            "commit_sha": sha,
            "status_reason": "PUSH_BLOCKED: previous push failed.",
        }
    )
    state["status"] = ralph_driver.PUSH_BLOCKED
    state["current_phase_id"] = "P00"
    phase_dir = write_passed_phase_artifacts(run_dir)
    ralph_driver.write_json(
        phase_dir / "git_phase.json",
        {
            "branch": branch,
            "commit_sha": sha,
            "changed_files": ["docs/a.md"],
            "blocked_files": [],
        },
    )
    (phase_dir / "branch.txt").write_text(branch + "\n", encoding="utf-8")
    (phase_dir / "commit_sha.txt").write_text(sha + "\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)
    (run_dir / "STOP").write_text("Workflow 2 provider-wired run stopped safely.\nReason: PUSH_BLOCKED\n", encoding="utf-8")

    def provider_called(*args, **kwargs):
        raise AssertionError("Resume from a PR gate must not call Claude or Codex.")

    monkeypatch.setattr(ralph_driver, "claude_headless", provider_called)
    monkeypatch.setattr(ralph_driver, "codex_noninteractive", provider_called)
    monkeypatch.setattr(
        ralph_driver,
        "commit_phase_changes",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("Resume must not create a new commit.")),
    )
    monkeypatch.setattr(ralph_driver, "ensure_phase_head", lambda root, branch, commit_sha: None)
    order: list[str] = []

    def fake_push(root, branch, remote="origin", dry_run=False):
        del root, dry_run
        order.append("push")
        return PushBranchResult(
            dry_run=False,
            branch=branch,
            remote=remote,
            command=["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"],
            return_code=0,
            stdout="pushed",
            pushed=True,
        )

    def fake_verify(root, branch, remote="origin"):
        del root
        order.append("verify")
        return RemoteBranchResult(
            exists=True,
            remote_sha=sha,
            local_sha=sha,
            matches=True,
            stdout=f"{sha}\trefs/heads/{branch}\n",
            stderr="",
            return_code=0,
            branch=branch,
            remote=remote,
            command=["git", "ls-remote", "--heads", remote, f"refs/heads/{branch}"],
        )

    def fake_create_pr(**kwargs):
        order.append("create_pr")
        assert kwargs["body_file"].name == "pr_body.md"
        assert kwargs["body_file"].exists()
        return GitHubResult(
            "create_pr",
            False,
            ["gh", "pr", "create", "--body-file", str(kwargs["body_file"])],
            metadata={
                "base": kwargs["base"],
                "head": kwargs["head"],
                "existing": True,
                "number": 7,
                "branch_pushed": kwargs["branch_pushed"],
                "remote_sha": kwargs["remote_sha"],
                "local_sha": kwargs["local_sha"],
            },
        )

    monkeypatch.setattr(ralph_driver, "push_phase_branch", fake_push)
    monkeypatch.setattr(ralph_driver, "verify_remote_branch", fake_verify)
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root=tmp_path: "main")
    monkeypatch.setattr(ralph_driver, "create_pr", fake_create_pr)
    monkeypatch.setattr(
        ralph_driver,
        "wait_for_ci",
        lambda *args, **kwargs: ralph_driver.classify_ci_checks(
            [{"name": "validate", "state": "SUCCESS", "bucket": "pass"}],
            required_checks=[],
        ),
    )
    monkeypatch.setattr(
        ralph_driver,
        "inspect_branch_protection",
        lambda **kwargs: BranchProtectionResult(
            "DRY_RUN",
            False,
            kwargs["branch"],
            [],
            [],
            [],
            dry_run=True,
            message="test",
        ),
    )
    monkeypatch.setattr(
        ralph_driver,
        "perform_merge",
        lambda **kwargs: GitHubResult("merge_pr", True, ["gh", "pr", "merge", str(kwargs["pr_number"])]),
    )

    status = ralph_driver.resume_provider_wired_run(run_dir, state, 1)

    assert status == 0
    updated = state_json(run_dir)
    assert updated["phases"][0]["status"] == "PASS"
    assert order[:3] == ["push", "verify", "create_pr"]
    assert (phase_dir / "remote_branch.json").is_file()
    assert (phase_dir / "pr_body.md").is_file()
    assert (phase_dir / "pr_create.md").is_file()


def test_provider_usage_limit_writes_waiting_handoff_not_blocked(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    monkeypatch.setattr(
        ralph_driver,
        "claude_headless",
        lambda *args, **kwargs: ralph_driver.CommandResult(("claude",), 0, "# Spec\n", ""),
    )
    monkeypatch.setattr(
        ralph_driver,
        "codex_noninteractive",
        lambda *args, **kwargs: ralph_driver.CommandResult(
            ("codex", "exec"),
            1,
            "",
            "Codex limit reached; retry after reset.",
        ),
    )

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    phase_dir = run_dir / "phases/P00"
    updated = state_json(run_dir)
    assert updated["status"] == ralph_driver.WAITING_CODEX_LIMIT
    assert updated["phases"][0]["status"] == ralph_driver.WAITING_CODEX_LIMIT
    assert updated["phases"][0]["resume_stage"] == "execute"
    assert (phase_dir / "provider_limit.json").is_file()
    assert (phase_dir / "provider_limit_handoff.md").is_file()
    assert not (phase_dir / "verdict.json").exists()
    assert "BLOCKED" not in (phase_dir / "provider_limit.md").read_text(encoding="utf-8")


def test_generic_provider_nonzero_remains_blocked(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_MAX_PHASES", "1")
    monkeypatch.setattr(
        ralph_driver,
        "claude_headless",
        lambda *args, **kwargs: ralph_driver.CommandResult(("claude",), 0, "# Spec\n", ""),
    )
    monkeypatch.setattr(
        ralph_driver,
        "codex_noninteractive",
        lambda *args, **kwargs: ralph_driver.CommandResult(("codex", "exec"), 1, "", "syntax error"),
    )

    status = ralph_driver.run_campaign(SAMPLE_CAMPAIGN_ID, None, "yellow", provider_wired=True)

    assert status == 0
    run_dir = latest_run(tmp_path, SAMPLE_CAMPAIGN_ID)
    phase_dir = run_dir / "phases/P00"
    updated = state_json(run_dir)
    assert updated["status"] == "STOPPED"
    assert updated["phases"][0]["status"] == "BLOCKED"
    assert not (phase_dir / "provider_limit.json").exists()
    assert json.loads((phase_dir / "verdict.json").read_text(encoding="utf-8"))["verdict"] == "BLOCKED"


def test_resume_from_merge_gate_no_provider_replay_runs_only_deterministic_gates(
    tmp_path,
    monkeypatch,
) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_ALLOW_AUTOMERGE", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = ralph_driver.MERGE_GATE_BLOCKED
    phase["branch"] = "auto/sample/p00-fixture"
    phase["commit_sha"] = "c" * 40
    phase["pr_number"] = 7
    state["status"] = ralph_driver.MERGE_GATE_BLOCKED
    state["current_phase_id"] = "P00"
    state["codex_called_by_driver"] = False
    state["claude_called_by_driver"] = False
    phase_dir = write_merge_resume_artifacts(run_dir)
    ralph_driver.write_state(run_dir, state)
    (run_dir / "STOP").write_text("previous merge gate stop\n", encoding="utf-8")
    stub_live_pr(monkeypatch, sha="c" * 40, diff_files=["docs/a.md"])

    def provider_called(*args, **kwargs):
        raise AssertionError("resume from merge_gate must not call Claude or Codex")

    monkeypatch.setattr(ralph_driver, "claude_headless", provider_called)
    monkeypatch.setattr(ralph_driver, "codex_noninteractive", provider_called)
    monkeypatch.setattr(ralph_driver, "detect_default_branch", lambda root=tmp_path: "main")
    order: list[str] = []

    monkeypatch.setattr(
        ralph_driver,
        "wait_for_ci",
        lambda *args, **kwargs: order.append("ci")
        or ralph_driver.classify_ci_checks(
            [{"name": "validate", "state": "SUCCESS", "bucket": "pass"}],
            required_checks=[],
        ),
    )
    monkeypatch.setattr(
        ralph_driver,
        "inspect_branch_protection",
        lambda **kwargs: order.append("branch_protection")
        or BranchProtectionResult(
            "PASS",
            True,
            kwargs["branch"],
            [],
            [],
            [],
            message="test",
        ),
    )
    real_gate = ralph_driver.evaluate_merge_gate

    def recording_gate(**kwargs):
        order.append("merge_gate")
        return real_gate(**kwargs)

    monkeypatch.setattr(ralph_driver, "evaluate_merge_gate", recording_gate)
    monkeypatch.setattr(
        ralph_driver,
        "perform_merge",
        lambda **kwargs: order.append("merge")
        or GitHubResult(
            "merge_pr",
            False,
            ["gh", "pr", "merge", str(kwargs["pr_number"])],
            return_code=0,
        ),
    )

    status = ralph_driver.main(
        [
            "resume",
            "--campaign-id",
            SAMPLE_CAMPAIGN_ID,
            "--run-dir",
            str(run_dir),
            "--phase-id",
            "P00",
            "--from-stage",
            "merge_gate",
            "--provider-wired",
            "--no-provider-replay",
        ]
    )

    assert status == 0
    assert order == ["ci", "branch_protection", "merge_gate", "merge"]
    updated = state_json(run_dir)
    assert updated["phases"][0]["status"] == "PASS"
    assert updated["status"] == "STOPPED"
    assert updated["auto_merge_performed"] is True
    assert updated["codex_called_by_driver"] is False
    assert updated["claude_called_by_driver"] is False
    assert (phase_dir / "merge_result.json").is_file()
    artifact_policy = json.loads((phase_dir / "resume_artifact_policy.json").read_text(encoding="utf-8"))
    assert artifact_policy["artifact_source"] == "pr_diff"
    assert artifact_policy["changed_files"] == ["docs/a.md"]
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "RUN_RESUME_STAGE" in events
    assert "RESUME_CI_RERUN" in events
    assert "RESUME_BRANCH_PROTECTION_RERUN" in events
    assert "RESUME_MERGE_GATE_RERUN" in events
    assert "RESUME_PERFORM_MERGE" in events
    assert "Targeted resume from merge_gate completed" in (run_dir / "RUN_SUMMARY.md").read_text(encoding="utf-8")


def test_merge_gate_resume_ignores_untracked_upgrade_reports_not_in_pr_diff(tmp_path, monkeypatch) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(tmp_path, monkeypatch)
    (tmp_path / ".frontier/upgrade_reports").mkdir(parents=True)
    (tmp_path / ".frontier/upgrade_reports/local.json").write_text("{}\n", encoding="utf-8")
    stub_live_pr(monkeypatch, diff_files=["docs/a.md"])
    stub_successful_resume_gates(monkeypatch)

    status = run_merge_gate_resume(run_dir)

    assert status == 0
    artifact_policy = json.loads((phase_dir / "resume_artifact_policy.json").read_text(encoding="utf-8"))
    assert artifact_policy["artifact_source"] == "pr_diff"
    assert artifact_policy["blocked_files"] == []
    assert state_json(run_dir)["phases"][0]["status"] == "PASS"


def test_merge_gate_resume_ignores_stale_run_changed_files_when_pr_diff_succeeds(tmp_path, monkeypatch) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(
        tmp_path,
        monkeypatch,
        changed_files=[".frontier/upgrade_reports/stale.json"],
    )
    stub_live_pr(monkeypatch, diff_files=["docs/a.md"])
    stub_successful_resume_gates(monkeypatch)

    status = run_merge_gate_resume(run_dir)

    assert status == 0
    artifact_policy = json.loads((phase_dir / "resume_artifact_policy.json").read_text(encoding="utf-8"))
    assert artifact_policy["artifact_source"] == "pr_diff"
    assert artifact_policy["changed_files"] == ["docs/a.md"]
    assert artifact_policy["blocked_files"] == []


def test_merge_gate_resume_falls_back_to_run_artifacts_when_pr_diff_unavailable(
    tmp_path,
    monkeypatch,
) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(
        tmp_path,
        monkeypatch,
        changed_files=["docs/fallback.md"],
    )
    stub_live_pr(monkeypatch, diff_files=["docs/a.md"])

    def fake_pr_diff(pr_number, root=ralph_driver.ROOT):
        del root
        return GitHubResult(
            "pr_diff",
            False,
            ["gh", "pr", "diff", str(pr_number), "--name-only"],
            return_code=1,
            stderr="temporary gh failure",
            blocked=True,
        )

    monkeypatch.setattr(ralph_driver, "list_pr_diff_files", fake_pr_diff)
    stub_successful_resume_gates(monkeypatch)

    status = run_merge_gate_resume(run_dir)

    assert status == 0
    artifact_policy = json.loads((phase_dir / "resume_artifact_policy.json").read_text(encoding="utf-8"))
    assert artifact_policy["artifact_source"] == "run_artifacts_fallback"
    assert artifact_policy["changed_files"] == ["docs/fallback.md"]
    assert artifact_policy["blocked_files"] == []
    assert "RESUME_PR_DIFF_FALLBACK" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_merge_gate_resume_blocks_live_pr_diff_upgrade_report(tmp_path, monkeypatch) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(tmp_path, monkeypatch)
    stub_live_pr(monkeypatch, diff_files=[".frontier/upgrade_reports/report.json"])
    order: list[str] = []
    stub_successful_resume_gates(monkeypatch, order=order)

    status = run_merge_gate_resume(run_dir)

    assert status == 1
    artifact_policy = json.loads((phase_dir / "resume_artifact_policy.json").read_text(encoding="utf-8"))
    assert artifact_policy["artifact_source"] == "pr_diff"
    assert ".frontier/upgrade_reports/report.json" in artifact_policy["blocked_files"]
    assert order == ["ci", "branch_protection", "merge_gate"]
    assert state_json(run_dir)["phases"][0]["status"] == ralph_driver.MERGE_GATE_BLOCKED


def test_merge_gate_resume_head_ref_mismatch_blocks_by_default(tmp_path, monkeypatch) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(tmp_path, monkeypatch, sha="c" * 40)
    stub_live_pr(monkeypatch, sha="d" * 40, diff_files=["docs/a.md"])
    monkeypatch.setattr(
        ralph_driver,
        "wait_for_ci",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CI must not run on head mismatch.")),
    )

    status = run_merge_gate_resume(run_dir)

    assert status == 1
    updated = state_json(run_dir)
    assert updated["status"] == ralph_driver.RESUME_PRECONDITION_FAILED
    head_check = json.loads((phase_dir / "resume_head_check.json").read_text(encoding="utf-8"))
    assert head_check["status"] == "MISMATCH"
    assert "headRefOid does not match" in (phase_dir / "resume_precondition_failed.md").read_text(encoding="utf-8")


def test_merge_gate_resume_head_ref_mismatch_requires_override(tmp_path, monkeypatch) -> None:
    run_dir, phase_dir = prepare_merge_gate_resume_run(tmp_path, monkeypatch, sha="c" * 40)
    monkeypatch.setenv("FRONTIER_ALLOW_RESUME_HEAD_MISMATCH", "1")
    stub_live_pr(monkeypatch, sha="d" * 40, diff_files=["docs/a.md"])
    stub_successful_resume_gates(monkeypatch)

    status = run_merge_gate_resume(run_dir)

    assert status == 0
    head_check = json.loads((phase_dir / "resume_head_check.json").read_text(encoding="utf-8"))
    assert head_check["status"] == "MISMATCH"
    assert head_check["override_allowed"] is True
    assert "RESUME_HEAD_MISMATCH_OVERRIDDEN" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_merge_gate_resume_already_merged_pr_marks_phase_complete(tmp_path, monkeypatch) -> None:
    run_dir, _phase_dir = prepare_merge_gate_resume_run(tmp_path, monkeypatch)
    stub_live_pr(monkeypatch, state="MERGED", diff_files=[".frontier/upgrade_reports/report.json"])
    monkeypatch.setattr(
        ralph_driver,
        "wait_for_ci",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CI must not run for an already merged PR.")),
    )
    monkeypatch.setattr(
        ralph_driver,
        "perform_merge",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("Merge must not run for an already merged PR.")),
    )

    status = run_merge_gate_resume(run_dir)

    assert status == 0
    updated = state_json(run_dir)
    assert updated["phases"][0]["status"] == "PASS"
    assert updated["phases"][0]["merged"] is True
    assert "RESUME_PR_ALREADY_MERGED" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_resume_from_merge_gate_refuses_missing_prior_artifacts(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = ralph_driver.MERGE_GATE_BLOCKED
    state["status"] = ralph_driver.MERGE_GATE_BLOCKED
    state["current_phase_id"] = "P00"
    phase_dir = run_dir / "phases/P00"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    (phase_dir / "executor_output.md").write_text("# Existing Execution\n", encoding="utf-8")
    (phase_dir / "validation.md").write_text("# Validation\n", encoding="utf-8")
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.main(
        [
            "resume",
            "--campaign-id",
            SAMPLE_CAMPAIGN_ID,
            "--run-dir",
            str(run_dir),
            "--phase-id",
            "P00",
            "--from-stage",
            "merge_gate",
            "--provider-wired",
            "--no-provider-replay",
        ]
    )

    assert status == 1
    updated = state_json(run_dir)
    assert updated["status"] == ralph_driver.RESUME_PRECONDITION_FAILED
    failure = (phase_dir / "resume_precondition_failed.md").read_text(encoding="utf-8")
    assert "review: review.md" in failure
    assert "review: verdict.json" in failure
    assert "done_check: done_check.json" in failure
    assert "pr: pr_create.json" in failure


def test_claude_headless_streams_large_review_prompt(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("FRONTIER_MOCK_PROVIDERS", raising=False)
    monkeypatch.setenv("FRONTIER_CLAUDE_CMD", "claude")
    calls = []

    class FakeRunner:
        def __init__(self, root: Path) -> None:
            self.root = root

        def run(self, command, **kwargs):
            from tools.frontier.command_runner import CommandResult as RunnerResult

            calls.append((list(command), kwargs))
            return RunnerResult(
                command=list(command),
                return_code=0,
                stdout="# Review\n\nVERDICT: PASS\n",
                stderr="",
                duration_ms=0,
            )

    monkeypatch.setattr(ralph_driver, "CommandRunner", FakeRunner)
    prompt = "# Review Prompt\n\n" + ("x" * 200_000)

    result = ralph_driver.claude_headless(prompt, root=tmp_path)

    assert result.returncode == 0
    command, kwargs = calls[0]
    assert kwargs["stdin_text"] == prompt
    assert prompt not in command
    assert sum(len(part) for part in command) < 1000


def test_run_lock_prevents_duplicate_driver(tmp_path) -> None:
    run_dir = tmp_path / "runs/run1"
    run_dir.mkdir(parents=True)

    with ralph_driver.run_lock(run_dir):
        with pytest.raises(RuntimeError):
            with ralph_driver.run_lock(run_dir):
                pass


def test_stop_prevents_next_phase(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    (run_dir / "STOP").write_text("stop\n", encoding="utf-8")

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert state_json(run_dir)["status"] == "STOPPED"
    assert pass_count(run_dir) == 0


def test_budget_stop(tmp_path, monkeypatch) -> None:
    write_sample_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("FRONTIER_MAX_RUN_MINUTES", "1")
    campaign = ralph_driver.load_ledger_campaign(SAMPLE_CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = state_json(run_dir)
    state["started_at"] = "2000-01-01T00:00:00Z"
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    assert status == 0
    assert state_json(run_dir)["status"] == "STOPPED"


def test_g005_toy_campaign_still_completes(tmp_path, monkeypatch) -> None:
    copy_campaign(tmp_path, ralph_driver.TOY_CAMPAIGN_ID)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)

    status = ralph_driver.run_campaign(ralph_driver.TOY_CAMPAIGN_ID, None, "green")

    assert status == 0
    run_dir = latest_run(tmp_path, ralph_driver.TOY_CAMPAIGN_ID)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["campaign_id"] == ralph_driver.TOY_CAMPAIGN_ID
    assert state["driver"] == "ralph_local_toy_v1"
    assert state["status"] == "COMPLETED"
    assert [phase["status"] for phase in state["phases"]] == ["PASS", "PASS", "PASS"]
    assert (tmp_path / "docs/toy_workflow2/phase_a.md").is_file()
    assert (tmp_path / "docs/toy_workflow2/phase_b.md").is_file()
    assert (tmp_path / "docs/toy_workflow2/summary.md").is_file()


def recipe_body(justfile_text: str, recipe_name: str) -> str:
    pattern = re.compile(rf"^{re.escape(recipe_name)}(?:\s[^:]*)?:\n((?:    .+\n)+)", re.MULTILINE)
    match = pattern.search(justfile_text)
    assert match is not None, recipe_name
    return match.group(1)


def test_just_command_semantics_are_provider_wired() -> None:
    text = (REPO_ROOT / "justfile").read_text(encoding="utf-8")

    run_campaign = recipe_body(text, "frontier-run-campaign")
    run_next = recipe_body(text, "frontier-run-next")
    run_mock = recipe_body(text, "frontier-run-campaign-mock")
    next_mock = recipe_body(text, "frontier-run-next-mock")
    resume_campaign = recipe_body(text, "frontier-resume-campaign")
    ledger = recipe_body(text, "frontier-run-campaign-ledger")
    overnight = recipe_body(text, "frontier-run-overnight")
    heartbeat = recipe_body(text, "frontier-heartbeat")
    acceptance = recipe_body(text, "frontier-acceptance")

    assert "--provider-wired" in run_campaign
    assert "FRONTIER_MAX_PHASES=1" not in run_campaign
    assert "--provider-wired" in run_next
    assert "FRONTIER_MAX_PHASES=1" in run_next
    assert "FRONTIER_MOCK_PROVIDERS=1" in run_mock
    assert "--provider-wired" in run_mock
    assert "FRONTIER_MOCK_PROVIDERS=1" in next_mock
    assert "FRONTIER_MAX_PHASES=1" in next_mock
    assert "--from-stage" in resume_campaign
    assert "--no-provider-replay" in resume_campaign
    assert "FRONTIER_NO_PROVIDER_REPLAY=1" in resume_campaign
    assert "--ledger-only" in ledger
    assert "FRONTIER_RUN_MODE=overnight" in overnight
    assert "heartbeat.json" in heartbeat
    assert "tools/frontier/acceptance.py" in acceptance


def test_frontier_ci_installs_test_dependencies_and_handles_no_tests() -> None:
    workflow = (REPO_ROOT / ".github/workflows/frontier-ci.yml").read_text(encoding="utf-8")

    assert "python -m pip install pytest pyyaml jinja2" in workflow
    assert "find tests -type f" in workflow
    assert "python -m pytest" in workflow
    assert "No tests configured yet" in workflow


def test_ralph_driver_has_no_provider_or_network_imports() -> None:
    source = (REPO_ROOT / "tools/frontier/ralph_driver.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {
        "anthropic",
        "github",
        "ghapi",
        "httpx",
        "ibapi",
        "openai",
        "requests",
        "socket",
        "urllib",
        "urllib3",
        "webbrowser",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert forbidden_roots.isdisjoint(imported_roots)
