"""Local Ralph Workflow 2 driver for alpha_system.

This module intentionally avoids provider orchestration, GitHub operations,
merge operations, deployment, trading, browser access, and network calls.

It includes a deterministic local toy campaign for Workflow 2 readiness and a
generic scaffold path for other ad hoc campaign ledgers.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOY_CAMPAIGN_ID = "G005_WORKFLOW2_TOY"
REQUIRED_CAMPAIGN_FILES = (
    "GOAL.md",
    "PHASE_PLAN.md",
    "campaign.yaml",
    "ACCEPTANCE.md",
    "RISK_REGISTER.md",
    "RUNBOOK.md",
)


@dataclass(frozen=True)
class ToyPhase:
    phase_id: str
    title: str
    output_path: Path


TOY_PHASES = (
    ToyPhase(
        phase_id="P01_CREATE_TOY_DOC_A",
        title="Create toy Workflow 2 document A",
        output_path=Path("docs/toy_workflow2/phase_a.md"),
    ),
    ToyPhase(
        phase_id="P02_CREATE_TOY_DOC_B",
        title="Create toy Workflow 2 document B",
        output_path=Path("docs/toy_workflow2/phase_b.md"),
    ),
    ToyPhase(
        phase_id="P03_CREATE_TOY_SUMMARY",
        title="Create toy Workflow 2 summary",
        output_path=Path("docs/toy_workflow2/summary.md"),
    ),
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_id_for(campaign_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    base = f"{stamp}_{campaign_id}"
    candidate = base
    suffix = 2
    while (ROOT / "runs" / candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def write_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(run_dir / "state.json", state)


def progress(run_dir: Path, message: str) -> None:
    with (run_dir / "progress.txt").open("a", encoding="utf-8") as handle:
        handle.write(f"{utc_now()} {message}\n")


def require_toy_campaign(campaign_id: str | None) -> str:
    if campaign_id != TOY_CAMPAIGN_ID:
        expected = f"Only {TOY_CAMPAIGN_ID} is implemented by this local toy path."
        if campaign_id:
            raise ValueError(f"Unsupported toy campaign id {campaign_id!r}. {expected}")
        raise ValueError(f"Missing campaign id. {expected}")
    campaign_dir = ROOT / "campaigns" / campaign_id
    missing = [name for name in REQUIRED_CAMPAIGN_FILES if not (campaign_dir / name).exists()]
    if missing:
        raise ValueError(f"Campaign {campaign_id} is missing required files: {', '.join(missing)}")
    return campaign_id


def phase_state(phase: ToyPhase) -> dict[str, Any]:
    return {
        "phase_id": phase.phase_id,
        "title": phase.title,
        "status": "PENDING",
        "output_path": str(phase.output_path),
        "artifacts": {
            "spec": f"phases/{phase.phase_id}/spec.md",
            "handoff": f"phases/{phase.phase_id}/handoff.md",
            "review": f"phases/{phase.phase_id}/review.md",
            "verdict": f"phases/{phase.phase_id}/verdict.json",
        },
    }


def initialize_toy_run(campaign_id: str) -> Path:
    campaign_dir = ROOT / "campaigns" / campaign_id
    run_id = run_id_for(campaign_id)
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "phases").mkdir()
    (run_dir / "RUN_GOAL.md").write_text(
        (campaign_dir / "GOAL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (run_dir / "PHASE_PLAN.md").write_text(
        (campaign_dir / "PHASE_PLAN.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    state: dict[str, Any] = {
        "schema_version": "frontier-run-state-v3",
        "run_id": run_id,
        "campaign_id": campaign_id,
        "workflow": "workflow2",
        "driver": "ralph_local_toy_v1",
        "status": "RUNNING",
        "lane": "green",
        "current_phase_id": None,
        "current_micro_attempt": 0,
        "phases": [phase_state(phase) for phase in TOY_PHASES],
        "stop_requested": False,
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "completed_at": None,
        "last_event_id": 0,
        "external_providers_called": False,
        "network_used": False,
        "auto_merge_performed": False,
    }
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("Workflow 2 toy run initialized.\n", encoding="utf-8")
    append_event(run_dir, state, "RUN_INIT", campaign_id=campaign_id)
    write_state(run_dir, state)
    write_summary(run_dir, state, "Run initialized.")
    return run_dir


def doc_body(phase: ToyPhase) -> str:
    if phase.phase_id == "P01_CREATE_TOY_DOC_A":
        return (
            "# Toy Workflow 2 Phase A\n\n"
            "This document was created by the deterministic local Ralph toy campaign.\n\n"
            "- Campaign: G005_WORKFLOW2_TOY\n"
            "- Phase: P01_CREATE_TOY_DOC_A\n"
            "- External providers: none\n"
        )
    if phase.phase_id == "P02_CREATE_TOY_DOC_B":
        return (
            "# Toy Workflow 2 Phase B\n\n"
            "This document was created after Phase A by the deterministic local Ralph toy campaign.\n\n"
            "- Campaign: G005_WORKFLOW2_TOY\n"
            "- Phase: P02_CREATE_TOY_DOC_B\n"
            "- External providers: none\n"
        )
    return (
        "# Toy Workflow 2 Summary\n\n"
        "The deterministic local Ralph toy campaign completed all three phases.\n\n"
        "- Phase A output: docs/toy_workflow2/phase_a.md\n"
        "- Phase B output: docs/toy_workflow2/phase_b.md\n"
        "- Summary output: docs/toy_workflow2/summary.md\n"
        "- External providers: none\n"
        "- Auto-merge: not implemented\n"
    )


def spec_body(phase: ToyPhase) -> str:
    return (
        f"# {phase.phase_id}\n\n"
        "Lane: green\n\n"
        "## Purpose\n\n"
        f"{phase.title}.\n\n"
        "## Scope\n\n"
        "Allowed:\n"
        f"- create or update {phase.output_path}\n"
        f"- write run artifacts under runs/<run_id>/phases/{phase.phase_id}/\n\n"
        "Forbidden:\n"
        "- provider calls\n"
        "- GitHub API calls\n"
        "- browser or network access\n"
        "- auto-merge, deployment, live trading, or paper trading\n\n"
        "## Validation\n\n"
        f"- {phase.output_path} exists\n"
        f"- runs/<run_id>/phases/{phase.phase_id}/handoff.md exists\n"
        f"- runs/<run_id>/phases/{phase.phase_id}/review.md exists\n"
        f"- runs/<run_id>/phases/{phase.phase_id}/verdict.json records PASS\n"
    )


def handoff_body(phase: ToyPhase) -> str:
    return (
        f"# {phase.phase_id} Handoff\n\n"
        "## Scope Completed\n\n"
        f"- Created `{phase.output_path}` using deterministic local content.\n"
        "- Wrote phase spec, review, handoff, and verdict artifacts in this run directory.\n\n"
        "## Validation\n\n"
        f"- `{phase.output_path}` exists.\n"
        "- No external providers, network calls, auto-merge, deployment, live trading, or paper trading were used.\n\n"
        "## Risks\n\n"
        "- This is a toy local workflow and does not validate real multi-agent execution.\n"
    )


def review_body(phase: ToyPhase) -> str:
    return (
        f"# {phase.phase_id} Review\n\n"
        "## Findings\n\n"
        "- No findings. The expected deterministic toy output was produced.\n\n"
        "## Questions\n\n"
        "- None.\n\n"
        "## Validation Notes\n\n"
        f"- Confirmed `{phase.output_path}` is the expected output for this phase.\n"
        "- Confirmed the phase stayed local-only.\n\n"
        "## Verdict\n\n"
        "PASS\n"
    )


def verdict_data(phase: ToyPhase) -> dict[str, Any]:
    return {
        "schema_version": "frontier-review-verdict-v1",
        "campaign_id": TOY_CAMPAIGN_ID,
        "phase_id": phase.phase_id,
        "verdict": "PASS",
        "findings": [],
        "validated_outputs": [str(phase.output_path)],
        "external_providers_called": False,
        "network_used": False,
        "auto_merge_performed": False,
    }


def phase_entry(state: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in state["phases"]:
        if phase["phase_id"] == phase_id:
            return phase
    raise ValueError(f"State is missing phase {phase_id}")


def execute_phase(run_dir: Path, state: dict[str, Any], phase: ToyPhase) -> None:
    entry = phase_entry(state, phase.phase_id)
    if entry["status"] == "PASS":
        return

    phase_dir = run_dir / "phases" / phase.phase_id
    phase_dir.mkdir(parents=True, exist_ok=True)
    state["status"] = "RUNNING"
    state["current_phase_id"] = phase.phase_id
    state["current_micro_attempt"] = 1
    entry["status"] = "RUNNING"
    entry["started_at"] = utc_now()
    append_event(run_dir, state, "PHASE_START", phase_id=phase.phase_id)
    write_state(run_dir, state)
    progress(run_dir, f"Starting {phase.phase_id}.")

    (phase_dir / "spec.md").write_text(spec_body(phase), encoding="utf-8")
    target = ROOT / phase.output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc_body(phase), encoding="utf-8")
    (phase_dir / "handoff.md").write_text(handoff_body(phase), encoding="utf-8")
    (phase_dir / "review.md").write_text(review_body(phase), encoding="utf-8")
    write_json(phase_dir / "verdict.json", verdict_data(phase))

    entry["status"] = "PASS"
    entry["completed_at"] = utc_now()
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    append_event(run_dir, state, "PHASE_PASS", phase_id=phase.phase_id, output_path=str(phase.output_path))
    write_state(run_dir, state)
    progress(run_dir, f"Completed {phase.phase_id}.")


def write_summary(run_dir: Path, state: dict[str, Any], note: str | None = None) -> None:
    completed = [phase for phase in state["phases"] if phase["status"] == "PASS"]
    pending = [phase for phase in state["phases"] if phase["status"] != "PASS"]
    lines = [
        "# Run Summary",
        "",
        f"Run: {state['run_id']}",
        f"Campaign: {state['campaign_id']}",
        f"Status: {state['status']}",
        f"Completed phases: {len(completed)}/{len(state['phases'])}",
        "",
        "## Phase Results",
        "",
    ]
    for phase in state["phases"]:
        lines.append(f"- {phase['phase_id']}: {phase['status']}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- External providers called: false",
            "- Network used: false",
            "- Auto-merge performed: false",
            "- Deployment performed: false",
            "- Live or paper trading performed: false",
        ]
    )
    if pending:
        lines.extend(["", "## Pending", ""])
        for phase in pending:
            lines.append(f"- {phase['phase_id']}")
    if note:
        lines.extend(["", "## Note", "", note])
    run_dir.joinpath("RUN_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def stop_run(run_dir: Path, state: dict[str, Any], reason: str) -> None:
    state["status"] = "STOPPED"
    state["stop_requested"] = True
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    state["completed_at"] = utc_now()
    append_event(run_dir, state, "RUN_STOPPED", reason=reason)
    write_state(run_dir, state)
    write_summary(run_dir, state, reason)
    progress(run_dir, f"Stopped: {reason}")


def complete_run(run_dir: Path, state: dict[str, Any]) -> None:
    state["status"] = "COMPLETED"
    state["stop_requested"] = False
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    state["completed_at"] = utc_now()
    append_event(run_dir, state, "RUN_COMPLETE")
    (run_dir / "STOP").write_text("Run completed. No further phases are pending.\n", encoding="utf-8")
    append_event(run_dir, state, "STOP_WRITTEN", reason="completed")
    write_state(run_dir, state)
    write_summary(run_dir, state, "Run completed successfully.")
    progress(run_dir, "Run completed.")


def continue_toy_run(run_dir: Path, state: dict[str, Any]) -> int:
    for phase in TOY_PHASES:
        entry = phase_entry(state, phase.phase_id)
        if entry["status"] == "PASS":
            continue
        if (run_dir / "STOP").exists():
            stop_run(run_dir, state, f"STOP file exists before starting {phase.phase_id}.")
            print(f"Stopped before {phase.phase_id}; inspect {run_dir.relative_to(ROOT)}")
            return 0
        execute_phase(run_dir, state, phase)

    complete_run(run_dir, state)
    print(f"Completed Workflow 2 toy run at {run_dir.relative_to(ROOT)}")
    return 0


def run_toy_campaign(campaign_id: str | None) -> int:
    try:
        resolved_campaign = require_toy_campaign(campaign_id)
        run_dir = initialize_toy_run(resolved_campaign)
        state = read_json(run_dir / "state.json")
        return continue_toy_run(run_dir, state)
    except ValueError as error:
        print(error)
        return 2


def init_scaffold_run(campaign_id: str, goal: str | None, lane: str) -> Path:
    run_id = run_id_for(campaign_id)
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "phases").mkdir(exist_ok=True)
    state = {
        "schema_version": "frontier-run-state-v3",
        "run_id": run_id,
        "campaign_id": campaign_id,
        "workflow": "workflow2",
        "driver": "ralph_frontier_strict_scaffold",
        "status": "RUNNING",
        "current_phase_id": None,
        "current_micro_attempt": 0,
        "lane": lane,
        "phases": [],
        "stop_requested": False,
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "completed_at": None,
        "last_event_id": 1,
        "external_providers_called": False,
        "network_used": False,
        "auto_merge_performed": False,
    }
    write_json(run_dir / "state.json", state)
    (run_dir / "events.jsonl").write_text(
        json.dumps({"event_id": 1, "event": "RUN_INIT", "timestamp": utc_now()}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "costs.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("Run initialized. Provider execution is not wired yet.\n", encoding="utf-8")
    (run_dir / "prd.json").write_text(json.dumps({"goal": goal, "campaign_id": campaign_id}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "RUN_GOAL.md").write_text(f"# Run Goal\n\n{goal or campaign_id}\n", encoding="utf-8")
    (run_dir / "RUN_SUMMARY.md").write_text(
        "# Run Summary\n\nStatus: initialized scaffold. No provider execution was performed.\n",
        encoding="utf-8",
    )
    return run_dir


def run_campaign(campaign_id: str | None, goal: str | None, lane: str) -> int:
    if campaign_id == TOY_CAMPAIGN_ID:
        return run_toy_campaign(campaign_id)

    resolved_campaign = campaign_id or "AD_HOC_GOAL"
    run_dir = init_scaffold_run(resolved_campaign, goal, lane)
    print(f"Initialized Workflow 2 scaffold run at {run_dir.relative_to(ROOT)}")
    print("No external provider, GitHub, network, or merge operation was performed.")
    return 0


def resume(run_id: str) -> int:
    run_dir = ROOT / "runs" / run_id
    state_path = run_dir / "state.json"
    if not state_path.exists():
        print(f"Unknown run id: {run_id}")
        return 1

    state = read_json(state_path)
    if state.get("campaign_id") != TOY_CAMPAIGN_ID:
        print(f"Resume scaffold for {run_id}. Inspect {run_dir / 'state.json'}")
        return 0
    if state.get("status") == "COMPLETED":
        print(f"Run {run_id} is already completed.")
        return 0

    stop_path = run_dir / "STOP"
    if stop_path.exists():
        stop_path.unlink()
    state["status"] = "RUNNING"
    state["stop_requested"] = False
    state["completed_at"] = None
    append_event(run_dir, state, "RUN_RESUME")
    write_state(run_dir, state)
    progress(run_dir, "Run resumed.")
    return continue_toy_run(run_dir, state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run or resume the local Frontier Ralph Workflow 2 driver.")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run a local Workflow 2 campaign or scaffold ledger.")
    run_parser.add_argument("--campaign-id")
    run_parser.add_argument("--goal")
    run_parser.add_argument("--lane", default="yellow")
    resume_parser = subparsers.add_parser("resume", help="Resume a stopped toy run or inspect a scaffold run.")
    resume_parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_campaign(args.campaign_id, args.goal, args.lane)
    if args.command == "resume":
        return resume(args.run_id)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
