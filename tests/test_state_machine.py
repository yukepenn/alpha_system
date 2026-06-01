from __future__ import annotations

import json

import pytest

from tools.frontier.state_machine import (
    BLOCKED,
    EXECUTED,
    PASS,
    PENDING,
    REPAIRED,
    REVIEWED,
    REWORK,
    SPEC_READY,
    STOPPED,
    VALIDATED,
    InvalidTransition,
    load_state,
    new_run_state,
    record_transition,
    save_state,
    transition_phase,
)


def test_legal_transitions() -> None:
    phase = {"phase_id": "P01", "status": PENDING}
    for status in [SPEC_READY, EXECUTED, VALIDATED, REVIEWED, REWORK, REPAIRED, VALIDATED, REVIEWED, PASS]:
        transition_phase(phase, status)
    assert phase["status"] == PASS


def test_illegal_transition_raises() -> None:
    with pytest.raises(InvalidTransition):
        transition_phase({"phase_id": "P01", "status": PENDING}, PASS)


def test_active_status_can_stop_when_requested() -> None:
    phase = {"phase_id": "P01", "status": SPEC_READY}
    transition_phase(phase, STOPPED, stop_requested=True)
    assert phase["status"] == STOPPED


def test_state_load_save_and_resume(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "run1"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    state = new_run_state(
        run_id="run1",
        campaign_id="C1",
        workflow="workflow2",
        driver="test",
        phases=[{"phase_id": "P01", "status": PENDING}],
        provider_mode="mock",
    )
    save_state(run_dir / "state.json", state)
    loaded = load_state(run_dir / "state.json")
    assert loaded["run_id"] == "run1"
    assert loaded["repair_attempts"]["P01"] == 0
    assert loaded["last_error"] is None
    record_transition(run_dir, loaded, "P01", SPEC_READY)

    reloaded = load_state(run_dir / "state.json")
    assert reloaded["phases"][0]["status"] == SPEC_READY
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == SPEC_READY
    assert (run_dir / "RUN_SUMMARY.md").is_file()
