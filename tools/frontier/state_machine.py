"""Formal Frontier Workflow 2 phase state machine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "frontier-run-state-v3"

PENDING = "PENDING"
SPEC_READY = "SPEC_READY"
EXECUTED = "EXECUTED"
VALIDATED = "VALIDATED"
REVIEWED = "REVIEWED"
REWORK = "REWORK"
REPAIRED = "REPAIRED"
PASS = "PASS"
PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
BLOCKED = "BLOCKED"
PUSH_BLOCKED = "PUSH_BLOCKED"
REMOTE_BRANCH_BLOCKED = "REMOTE_BRANCH_BLOCKED"
PR_CREATE_BLOCKED = "PR_CREATE_BLOCKED"
CI_BLOCKED = "CI_BLOCKED"
MERGE_GATE_BLOCKED = "MERGE_GATE_BLOCKED"
STOPPED = "STOPPED"
SKIPPED = "SKIPPED"

PHASE_STATUSES = {
    PENDING,
    SPEC_READY,
    EXECUTED,
    VALIDATED,
    REVIEWED,
    REWORK,
    REPAIRED,
    PASS,
    PASS_WITH_WARNINGS,
    BLOCKED,
    PUSH_BLOCKED,
    REMOTE_BRANCH_BLOCKED,
    PR_CREATE_BLOCKED,
    CI_BLOCKED,
    MERGE_GATE_BLOCKED,
    STOPPED,
    SKIPPED,
}

TERMINAL_STATUSES = {
    PASS,
    PASS_WITH_WARNINGS,
    BLOCKED,
    PUSH_BLOCKED,
    REMOTE_BRANCH_BLOCKED,
    PR_CREATE_BLOCKED,
    CI_BLOCKED,
    MERGE_GATE_BLOCKED,
    STOPPED,
    SKIPPED,
}
ACTIVE_STATUSES = PHASE_STATUSES - TERMINAL_STATUSES

LEGAL_TRANSITIONS: dict[str, set[str]] = {
    PENDING: {SPEC_READY},
    SPEC_READY: {EXECUTED},
    EXECUTED: {VALIDATED},
    VALIDATED: {REVIEWED},
    REVIEWED: {
        PASS,
        PASS_WITH_WARNINGS,
        REWORK,
        BLOCKED,
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
    },
    REWORK: {REPAIRED},
    REPAIRED: {VALIDATED},
    PUSH_BLOCKED: {
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        PASS,
        PASS_WITH_WARNINGS,
    },
    REMOTE_BRANCH_BLOCKED: {
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        PASS,
        PASS_WITH_WARNINGS,
    },
    PR_CREATE_BLOCKED: {
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        PASS,
        PASS_WITH_WARNINGS,
    },
    CI_BLOCKED: {
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        PASS,
        PASS_WITH_WARNINGS,
    },
    MERGE_GATE_BLOCKED: {
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        PASS,
        PASS_WITH_WARNINGS,
    },
}


class InvalidTransition(ValueError):
    """Raised when a phase transition is not legal."""


@dataclass(frozen=True)
class Transition:
    phase_id: str
    previous_status: str
    next_status: str
    timestamp: str
    reason: str | None = None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_transition(previous: str, next_status: str, *, stop_requested: bool = False) -> None:
    if previous not in PHASE_STATUSES:
        raise InvalidTransition(f"Unknown previous phase status: {previous}")
    if next_status not in PHASE_STATUSES:
        raise InvalidTransition(f"Unknown next phase status: {next_status}")
    if stop_requested and previous in ACTIVE_STATUSES and next_status == STOPPED:
        return
    allowed = LEGAL_TRANSITIONS.get(previous, set())
    if next_status not in allowed:
        raise InvalidTransition(f"Invalid Workflow 2 transition: {previous} -> {next_status}")


def transition_phase(
    phase: dict[str, Any],
    next_status: str,
    *,
    stop_requested: bool = False,
    reason: str | None = None,
) -> Transition:
    previous = str(phase.get("status", PENDING))
    validate_transition(previous, next_status, stop_requested=stop_requested)
    timestamp = utc_now()
    phase["status"] = next_status
    phase["updated_at"] = timestamp
    if next_status in TERMINAL_STATUSES:
        phase["completed_at"] = timestamp
    if reason:
        phase["status_reason"] = reason
    return Transition(str(phase["phase_id"]), previous, next_status, timestamp, reason)


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path} has unsupported schema_version {data.get('schema_version')!r}.")
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(run_dir: Path, state: dict[str, Any], event: str, **details: Any) -> None:
    event_id = int(state.get("last_event_id", 0)) + 1
    state["last_event_id"] = event_id
    record = {
        "event_id": event_id,
        "timestamp": utc_now(),
        "event": event,
        **details,
    }
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def phase_by_id(state: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in state.get("phases", []):
        if phase.get("phase_id") == phase_id:
            return phase
    raise KeyError(f"State is missing phase {phase_id}.")


def write_run_summary(run_dir: Path, state: dict[str, Any], note: str | None = None) -> None:
    phases = state.get("phases", [])
    passing = [phase for phase in phases if phase.get("status") in {PASS, PASS_WITH_WARNINGS}]
    blocked_statuses = {
        BLOCKED,
        PUSH_BLOCKED,
        REMOTE_BRANCH_BLOCKED,
        PR_CREATE_BLOCKED,
        CI_BLOCKED,
        MERGE_GATE_BLOCKED,
        STOPPED,
        REWORK,
    }
    blocked = [phase for phase in phases if phase.get("status") in blocked_statuses]
    lines = [
        "# Run Summary",
        "",
        f"Run: {state.get('run_id')}",
        f"Campaign: {state.get('campaign_id')}",
        f"Workflow: {state.get('workflow')}",
        f"Driver: {state.get('driver')}",
        f"Status: {state.get('status')}",
        f"Provider mode: {state.get('provider_mode', 'unknown')}",
        f"Passing phases: {len(passing)}/{len(phases)}",
        "",
        "## Phase Results",
        "",
    ]
    for phase in phases:
        lane = f" [{phase.get('lane')}]" if phase.get("lane") else ""
        name = f" - {phase.get('name')}" if phase.get("name") else ""
        lines.append(f"- {phase.get('phase_id')}{lane}: {phase.get('status')}{name}")
    if blocked:
        lines.extend(["", "## Attention", ""])
        for phase in blocked:
            reason = f" - {phase.get('status_reason')}" if phase.get("status_reason") else ""
            lines.append(f"- {phase.get('phase_id')}: {phase.get('status')}{reason}")
    if note:
        lines.extend(["", "## Note", "", note])
    run_dir.joinpath("RUN_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_transition(
    run_dir: Path,
    state: dict[str, Any],
    phase_id: str,
    next_status: str,
    *,
    stop_requested: bool = False,
    reason: str | None = None,
    event: str | None = None,
) -> Transition:
    phase = phase_by_id(state, phase_id)
    transition = transition_phase(
        phase,
        next_status,
        stop_requested=stop_requested,
        reason=reason,
    )
    state["current_phase_id"] = None if next_status in TERMINAL_STATUSES else phase_id
    append_event(
        run_dir,
        state,
        event or next_status,
        phase_id=phase_id,
        previous_status=transition.previous_status,
        next_status=transition.next_status,
        reason=reason,
    )
    save_state(run_dir / "state.json", state)
    write_run_summary(run_dir, state, reason)
    return transition


def new_run_state(
    *,
    run_id: str,
    campaign_id: str,
    workflow: str,
    driver: str,
    phases: list[dict[str, Any]],
    provider_mode: str,
    lane_policy_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    created_at = utc_now()
    attempts = {str(phase.get("phase_id")): 0 for phase in phases}
    repair_attempts = {str(phase.get("phase_id")): 0 for phase in phases}
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "campaign_id": campaign_id,
        "workflow": workflow,
        "driver": driver,
        "status": "RUNNING",
        "current_phase_id": None,
        "phases": phases,
        "stop_requested": False,
        "created_at": created_at,
        "updated_at": created_at,
        "attempts": attempts,
        "repair_attempts": repair_attempts,
        "last_error": None,
        "provider_mode": provider_mode,
        "lane_policy_snapshot": lane_policy_snapshot or {},
        "last_event_id": 0,
    }


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES
