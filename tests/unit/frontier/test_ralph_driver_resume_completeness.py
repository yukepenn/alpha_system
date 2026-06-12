from __future__ import annotations

import json
from pathlib import Path

from tools.frontier import ralph_driver


CAMPAIGN_ID = "WF2_RESUME_COMPLETENESS_TEST"


def _write_frontier_config(root: Path) -> None:
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
  max_phases: 2
  max_run_minutes: 60
  max_phase_minutes: 60
  max_estimated_usd: 0
  semantic_done_check_required: true
  worktree_mode: false
github:
  auto_create_pr: true
  ci_timeout_seconds: 1
  ci_poll_seconds: 0
  required_checks: []
  require_ci: true
  require_branch_protection: true
  allow_unprotected_dry_run: true
  merge_method: "squash"
git:
  auto_create_pr: true
artifacts:
  allow_commit: ["docs/**", "tools/**", "tests/**"]
  forbid_commit: ["runs/**"]
lanes:
  green:
    required_checks: []
    require_claude_review: false
    auto_pr: true
    auto_merge: true
    max_repair_attempts: 1
    merge_policy:
      allow_pass_with_warnings: true
  yellow:
    required_checks: []
    require_claude_review: true
    auto_pr: true
    auto_merge: true
    max_repair_attempts: 1
    merge_policy:
      allow_pass_with_warnings: true
""",
        encoding="utf-8",
    )


def _write_parallel_campaign(root: Path) -> None:
    _write_frontier_config(root)
    campaign_dir = root / "campaigns" / CAMPAIGN_ID
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "GOAL.md").write_text(f"# {CAMPAIGN_ID}\n", encoding="utf-8")
    (campaign_dir / "PHASE_PLAN.md").write_text("# Phase Plan\n", encoding="utf-8")
    (campaign_dir / "campaign.yaml").write_text(
        f"""campaign_id: "{CAMPAIGN_ID}"
workflow: "workflow2"
default_lane: "yellow"
limits:
  max_phases: 2
workflow2:
  scheduler:
    mode: "dag_wave"
    parallel_execution: true
    max_parallel_phases: 2
phases:
  - id: "P00"
    name: "Resume current"
    lane: "YELLOW"
    dependencies: []
  - id: "P01"
    name: "Dependent"
    lane: "GREEN"
    dependencies: ["P00"]
    parallel_safe: true
""",
        encoding="utf-8",
    )
    for name in ("ACCEPTANCE.md", "RISK_REGISTER.md", "RUNBOOK.md"):
        (campaign_dir / name).write_text(f"# {name}\n", encoding="utf-8")


def _state_json(run_dir: Path) -> dict:
    return json.loads((run_dir / "state.json").read_text(encoding="utf-8"))


def _events(run_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _repair_run(tmp_path: Path, *, review_text: str) -> tuple[Path, dict, dict]:
    run_dir = tmp_path / "runs" / "2099Z_REPAIR"
    phase = {"phase_id": "P00", "name": "Repair", "lane": "yellow", "status": "REWORK"}
    state = {
        "run_id": "2099Z_REPAIR",
        "campaign_id": CAMPAIGN_ID,
        "workflow": "workflow2",
        "driver": ralph_driver.PROVIDER_WIRED_DRIVER,
        "status": "RUNNING",
        "current_phase_id": "P00",
        "current_micro_attempt": 2,
        "phases": [phase],
        "stop_requested": False,
        "last_event_id": 0,
        "mock_providers": True,
        "provider_wired": True,
        "provider_mode": "mock",
        "max_repair_attempts": 1,
        "repair_attempts": {"P00": 1},
        "lane_policy_snapshot": {"yellow": {"max_repair_attempts": 1}},
        "estimated_cost_usd": 0.0,
    }
    phase_dir = run_dir / "phases" / "P00"
    attempt_dir = phase_dir / "repair_attempts" / "001"
    attempt_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("", encoding="utf-8")
    (attempt_dir / "repair_review.md").write_text(review_text, encoding="utf-8")
    (phase_dir / "review.md").write_text(review_text, encoding="utf-8")
    return run_dir, state, phase


def test_repair_exhaustion_uses_passing_final_review_verdict(tmp_path: Path) -> None:
    run_dir, state, phase = _repair_run(
        tmp_path,
        review_text=(
            "# Fresh Review\n\n- Warning: minor follow-up.\n\nVERDICT: PASS_WITH_WARNINGS\n"
        ),
    )

    verdict = ralph_driver.run_provider_repair_loop(
        run_dir,
        state,
        phase,
        "# Spec\n",
        "# Previous Review\n\nVERDICT: REWORK\n",
        "# Validation\n",
        execution_root=tmp_path,
    )

    verdict_data = json.loads((run_dir / "phases/P00/verdict.json").read_text(encoding="utf-8"))
    exhausted = [event for event in _events(run_dir) if event["event"] == "REPAIR_EXHAUSTED"]
    assert verdict == "PASS_WITH_WARNINGS"
    assert phase["status"] == "REVIEWED"
    assert verdict_data["verdict"] == "PASS_WITH_WARNINGS"
    assert verdict_data["source"] == "repair_exhausted_final_review"
    assert exhausted[-1]["source"] == "repair_exhausted_final_review"


def test_repair_exhaustion_unparseable_final_review_stays_synthetic_blocked(
    tmp_path: Path,
) -> None:
    run_dir, state, phase = _repair_run(
        tmp_path,
        review_text="# Fresh Review\n\nNo verdict line.\n",
    )

    verdict = ralph_driver.run_provider_repair_loop(
        run_dir,
        state,
        phase,
        "# Spec\n",
        "# Previous Review\n\nVERDICT: REWORK\n",
        "# Validation\n",
        execution_root=tmp_path,
    )

    verdict_data = json.loads((run_dir / "phases/P00/verdict.json").read_text(encoding="utf-8"))
    exhausted = [event for event in _events(run_dir) if event["event"] == "REPAIR_EXHAUSTED"]
    assert verdict == "BLOCKED"
    assert verdict_data["verdict"] == "BLOCKED"
    assert verdict_data["source"] == "repair_exhausted"
    assert verdict_data["raw_review_path"] is None
    assert "source" not in exhausted[-1]


def test_repair_exhaustion_parseable_rework_final_review_stays_synthetic_blocked(
    tmp_path: Path,
) -> None:
    run_dir, state, phase = _repair_run(
        tmp_path,
        review_text="# Fresh Review\n\nVERDICT: REWORK\n",
    )

    verdict = ralph_driver.run_provider_repair_loop(
        run_dir,
        state,
        phase,
        "# Spec\n",
        "# Previous Review\n\nVERDICT: REWORK\n",
        "# Validation\n",
        execution_root=tmp_path,
    )

    verdict_data = json.loads((run_dir / "phases/P00/verdict.json").read_text(encoding="utf-8"))
    exhausted = [event for event in _events(run_dir) if event["event"] == "REPAIR_EXHAUSTED"]
    assert verdict == "BLOCKED"
    assert phase["status"] == "REWORK"
    assert verdict_data["verdict"] == "BLOCKED"
    assert verdict_data["source"] == "repair_exhausted"
    assert verdict_data["raw_review_path"] is None
    assert "source" not in exhausted[-1]
    assert "verdict" not in exhausted[-1]


def test_targeted_done_check_resume_finishes_midpipeline_phase_before_wave_scheduling(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_parallel_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    monkeypatch.delenv("FRONTIER_MOCK_COMMIT", raising=False)
    monkeypatch.setattr(
        ralph_driver,
        "run_phase_validation",
        lambda _root: (True, "# Validation\n"),
    )
    campaign = ralph_driver.load_ledger_campaign(CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = _state_json(run_dir)
    phase = state["phases"][0]
    phase["status"] = "BLOCKED"
    state["status"] = "STOPPED"
    state["stop_requested"] = True
    (run_dir / "STOP").write_text("stopped\n", encoding="utf-8")
    phase_dir = run_dir / "phases" / "P00"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "spec.md").write_text("# Existing Spec\n", encoding="utf-8")
    (phase_dir / "executor_output.md").write_text("# Existing Execution\n", encoding="utf-8")
    (phase_dir / "validation.md").write_text("# Existing Validation\n", encoding="utf-8")
    (phase_dir / "review.md").write_text("# Existing Review\n\nVERDICT: PASS\n", encoding="utf-8")
    ralph_driver.write_json(phase_dir / "verdict.json", {"verdict": "PASS"})
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.resume_provider_wired_stage(
        run_dir,
        state,
        campaign_id=CAMPAIGN_ID,
        phase_id="P00",
        from_stage="done_check",
        no_provider_replay=False,
    )

    updated = _state_json(run_dir)
    scheduler = ralph_driver.scheduler_settings_for_state(updated)
    ready = ralph_driver.ready_wave_phases(updated, scheduler)
    checkpoints = [
        json.loads(line)["stage"]
        for line in (phase_dir / "stage_checkpoints.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert status == 0
    assert updated["phases"][0]["status"] == "PASS"
    assert updated["phases"][1]["status"] == "PENDING"
    assert "done_check" in checkpoints
    assert "commit" in checkpoints
    assert (phase_dir / "git_phase.json").is_file()
    assert ready and ready[0]["phase_id"] == "P01"
    assert "SCHEDULE_DEADLOCK" not in [event["event"] for event in _events(run_dir)]


def test_dag_wave_deadlock_still_fires_without_midpipeline_phase(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_parallel_campaign(tmp_path)
    monkeypatch.setattr(ralph_driver, "ROOT", tmp_path)
    monkeypatch.setenv("FRONTIER_MOCK_PROVIDERS", "1")
    campaign = ralph_driver.load_ledger_campaign(CAMPAIGN_ID)
    run_dir = ralph_driver.initialize_provider_wired_run(campaign, 1, "test")
    state = _state_json(run_dir)
    state["phases"][0]["status"] = "BLOCKED"
    state["current_phase_id"] = None
    ralph_driver.write_state(run_dir, state)

    status = ralph_driver.continue_provider_wired_run(run_dir, state, 1, "test")

    updated = _state_json(run_dir)
    assert status == 0
    assert updated["status"] == "BLOCKED"
    assert "SCHEDULE_DEADLOCK" in [event["event"] for event in _events(run_dir)]
