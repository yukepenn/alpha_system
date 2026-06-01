"""Local Ralph Workflow 2 driver for alpha_system.

This module intentionally avoids GitHub operations, merge operations,
deployment, trading, broker calls, browser access, and destructive cleanup.

It includes a deterministic local toy campaign for Workflow 2 readiness, a
ledger-only ALPHA_SYSTEM_V1 mode, and a provider-wired local conductor for
ALPHA_SYSTEM_V1 that can be exercised with deterministic mock providers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOY_CAMPAIGN_ID = "G005_WORKFLOW2_TOY"
ALPHA_SYSTEM_V1_CAMPAIGN_ID = "ALPHA_SYSTEM_V1"
LEDGER_ONLY_DRIVER = "ralph_frontier_strict_ledger_only_v1"
PROVIDER_WIRED_DRIVER = "ralph_frontier_provider_wired_mvc_v1"
DEFAULT_MAX_REPAIR_ATTEMPTS = 1
REQUIRED_CAMPAIGN_FILES = (
    "GOAL.md",
    "PHASE_PLAN.md",
    "campaign.yaml",
    "ACCEPTANCE.md",
    "RISK_REGISTER.md",
    "RUNBOOK.md",
)
ASV1_PHASE_RE = re.compile(r"ASV1-P\d{2}")
ASV1_TABLE_ROW_RE = re.compile(
    r"^\|\s*(ASV1-P\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)
ASV1_SECTION_RE = re.compile(r"^##\s+(ASV1-P\d{2})\s+[\u2014-]\s+(.+?)\s*$", re.MULTILINE)
EXPECTED_ASV1_PHASE_IDS = tuple(f"ASV1-P{index:02d}" for index in range(30))
PASSING_VERDICTS = {"PASS", "PASS_WITH_WARNINGS"}
FORBIDDEN_GIT_ADD_DOT = "git add" + " ."
FORBIDDEN_GIT_ADD_ALL = "git add" + " -A"


@dataclass(frozen=True)
class ToyPhase:
    phase_id: str
    title: str
    output_path: Path


@dataclass(frozen=True)
class LedgerPhase:
    phase_id: str
    name: str | None
    lane: str | None
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class LedgerCampaign:
    campaign_id: str
    goal_text: str
    phase_plan_text: str
    campaign_yaml: dict[str, Any]
    phases: tuple[LedgerPhase, ...]


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


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


def mock_providers_enabled() -> bool:
    return os.environ.get("FRONTIER_MOCK_PROVIDERS") == "1"


def parse_positive_int(value: str | int, source: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{source} must be a positive integer.") from error
    if parsed < 1:
        raise ValueError(f"{source} must be at least 1.")
    return parsed


def env_max_phases() -> int | None:
    raw = os.environ.get("FRONTIER_MAX_PHASES")
    if raw is None or raw == "":
        return None
    return parse_positive_int(raw, "FRONTIER_MAX_PHASES")


def nested_int(data: dict[str, Any], path: tuple[str, ...]) -> int | None:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    return parse_positive_int(current, ".".join(path))


def campaign_phase_limit(campaign: "LedgerCampaign") -> int:
    for path in (
        ("workflow2", "max_phases"),
        ("workflow", "max_phases"),
        ("runtime", "max_phases"),
        ("limits", "max_phases"),
    ):
        configured = nested_int(campaign.campaign_yaml, path)
        if configured is not None:
            return min(configured, len(campaign.phases))
    return len(campaign.phases)


def resolve_max_phases(
    campaign: "LedgerCampaign",
    explicit_max_phases: int | None,
) -> tuple[int, str]:
    if explicit_max_phases is not None:
        return parse_positive_int(explicit_max_phases, "--max-phases"), "cli"
    env_limit = env_max_phases()
    if env_limit is not None:
        return env_limit, "env"
    return campaign_phase_limit(campaign), "campaign"


def run_local_command(command: list[str]) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        return CommandResult(tuple(command), 127, "", str(error))
    return CommandResult(tuple(command), result.returncode, result.stdout, result.stderr)


def command_block(result: CommandResult) -> str:
    command = " ".join(result.command)
    return (
        f"## `{command}`\n\n"
        f"Exit code: {result.returncode}\n\n"
        "### stdout\n\n"
        "```text\n"
        f"{result.stdout}"
        "\n```\n\n"
        "### stderr\n\n"
        "```text\n"
        f"{result.stderr}"
        "\n```\n"
    )


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


def require_campaign_files(campaign_id: str) -> Path:
    campaign_dir = ROOT / "campaigns" / campaign_id
    missing = [name for name in REQUIRED_CAMPAIGN_FILES if not (campaign_dir / name).exists()]
    if missing:
        raise ValueError(f"Campaign {campaign_id} is missing required files: {', '.join(missing)}")
    return campaign_dir


def load_campaign_yaml(campaign_id: str, campaign_dir: Path) -> dict[str, Any]:
    yaml_path = campaign_dir / "campaign.yaml"
    try:
        import yaml
    except ImportError as error:
        raise ValueError("PyYAML is required to parse campaign.yaml for ledger-only runs.") from error

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"Campaign {campaign_id} campaign.yaml is malformed: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"Campaign {campaign_id} campaign.yaml must parse to a mapping.")
    if data.get("campaign_id") != campaign_id:
        raise ValueError(
            f"Campaign {campaign_id} campaign.yaml has campaign_id {data.get('campaign_id')!r}."
        )
    phases = data.get("phases")
    if not isinstance(phases, list):
        raise ValueError(f"Campaign {campaign_id} campaign.yaml must contain a phases list.")
    return data


def yaml_phase_index(campaign_yaml: dict[str, Any], campaign_id: str) -> dict[str, dict[str, Any]]:
    phases = campaign_yaml.get("phases")
    if not isinstance(phases, list):
        raise ValueError(f"Campaign {campaign_id} campaign.yaml must contain a phases list.")

    indexed: dict[str, dict[str, Any]] = {}
    for offset, phase in enumerate(phases, start=1):
        if not isinstance(phase, dict):
            raise ValueError(f"Campaign {campaign_id} phase entry {offset} must be a mapping.")
        phase_id = phase.get("id") or phase.get("phase_id")
        if not isinstance(phase_id, str) or not phase_id:
            raise ValueError(f"Campaign {campaign_id} phase entry {offset} is missing an id.")
        if phase_id in indexed:
            raise ValueError(f"Campaign {campaign_id} campaign.yaml repeats phase id {phase_id}.")
        indexed[phase_id] = phase
    return indexed


def clean_cell(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value.replace("`", "")).strip()
    return cleaned or None


def parse_dependencies(raw: str | None, *, phase_id: str) -> tuple[str, ...]:
    cleaned = clean_cell(raw)
    if cleaned is None:
        return ()
    normalized = cleaned.lower().strip(".")
    if normalized in {"none", "n/a", "na", "[]"}:
        return ()
    dependencies = tuple(ASV1_PHASE_RE.findall(cleaned))
    if not dependencies:
        raise ValueError(f"Could not parse dependencies for {phase_id}: {raw!r}")
    return dependencies


def section_field(section_text: str, heading: str) -> str | None:
    heading_match = re.search(rf"^###\s+{re.escape(heading)}\s*$", section_text, re.MULTILINE)
    if not heading_match:
        return None
    start = heading_match.end()
    next_heading = re.search(r"^###\s+", section_text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(section_text)
    return section_text[start:end].strip()


def first_content_line(text: str | None) -> str | None:
    if text is None:
        return None
    for line in text.splitlines():
        cleaned = clean_cell(line.lstrip("*- "))
        if cleaned:
            return cleaned
    return None


def parse_asv1_phase_plan(
    phase_plan_text: str,
    campaign_yaml: dict[str, Any] | None = None,
) -> tuple[LedgerPhase, ...]:
    yaml_phases = yaml_phase_index(campaign_yaml, ALPHA_SYSTEM_V1_CAMPAIGN_ID) if campaign_yaml else {}
    phases: list[LedgerPhase] = []

    for match in ASV1_TABLE_ROW_RE.finditer(phase_plan_text):
        phase_id = match.group(1).strip()
        name = clean_cell(match.group(2))
        lane = clean_cell(match.group(3))
        dependencies = parse_dependencies(match.group(4), phase_id=phase_id)
        phases.append(LedgerPhase(phase_id, name, lane, dependencies))

    if not phases:
        matches = list(ASV1_SECTION_RE.finditer(phase_plan_text))
        for index, match in enumerate(matches):
            phase_id = match.group(1).strip()
            section_start = match.end()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(phase_plan_text)
            section_text = phase_plan_text[section_start:section_end]
            name = first_content_line(section_field(section_text, "Phase Name")) or clean_cell(match.group(2))
            lane = first_content_line(section_field(section_text, "Lane"))
            dependencies = parse_dependencies(section_field(section_text, "Dependencies"), phase_id=phase_id)
            phases.append(LedgerPhase(phase_id, name, lane, dependencies))

    if not phases:
        raise ValueError("PHASE_PLAN.md does not contain any ASV1-PXX phase entries.")

    seen: set[str] = set()
    for phase in phases:
        if phase.phase_id in seen:
            raise ValueError(f"PHASE_PLAN.md repeats phase id {phase.phase_id}.")
        seen.add(phase.phase_id)

        yaml_phase = yaml_phases.get(phase.phase_id)
        if campaign_yaml is not None and yaml_phase is None:
            raise ValueError(f"PHASE_PLAN.md lists {phase.phase_id}, but campaign.yaml does not.")
        if yaml_phase is None:
            continue

        yaml_name = clean_cell(str(yaml_phase.get("name"))) if yaml_phase.get("name") is not None else None
        yaml_lane = clean_cell(str(yaml_phase.get("lane"))) if yaml_phase.get("lane") is not None else None
        yaml_dependencies_raw = yaml_phase.get("dependencies", [])
        if not isinstance(yaml_dependencies_raw, list):
            raise ValueError(f"campaign.yaml dependencies for {phase.phase_id} must be a list.")
        yaml_dependencies = tuple(str(dependency) for dependency in yaml_dependencies_raw)

        if phase.name and yaml_name and phase.name != yaml_name:
            raise ValueError(
                f"PHASE_PLAN.md and campaign.yaml disagree on name for {phase.phase_id}: "
                f"{phase.name!r} != {yaml_name!r}."
            )
        if phase.lane and yaml_lane and phase.lane.upper() != yaml_lane.upper():
            raise ValueError(
                f"PHASE_PLAN.md and campaign.yaml disagree on lane for {phase.phase_id}: "
                f"{phase.lane!r} != {yaml_lane!r}."
            )
        if phase.dependencies != yaml_dependencies:
            raise ValueError(
                f"PHASE_PLAN.md and campaign.yaml disagree on dependencies for {phase.phase_id}: "
                f"{list(phase.dependencies)!r} != {list(yaml_dependencies)!r}."
            )

    return tuple(phases)


def validate_asv1_phase_sequence(phases: tuple[LedgerPhase, ...]) -> None:
    phase_ids = tuple(phase.phase_id for phase in phases)
    if phase_ids != EXPECTED_ASV1_PHASE_IDS:
        raise ValueError(
            "ALPHA_SYSTEM_V1 PHASE_PLAN.md must contain ASV1-P00 through ASV1-P29 in order."
        )


def load_ledger_campaign(campaign_id: str) -> LedgerCampaign:
    if campaign_id != ALPHA_SYSTEM_V1_CAMPAIGN_ID:
        raise ValueError(f"Ledger-only support is implemented only for {ALPHA_SYSTEM_V1_CAMPAIGN_ID}.")
    campaign_dir = require_campaign_files(campaign_id)
    goal_text = (campaign_dir / "GOAL.md").read_text(encoding="utf-8")
    phase_plan_text = (campaign_dir / "PHASE_PLAN.md").read_text(encoding="utf-8")
    campaign_yaml = load_campaign_yaml(campaign_id, campaign_dir)
    phases = parse_asv1_phase_plan(phase_plan_text, campaign_yaml)
    validate_asv1_phase_sequence(phases)
    return LedgerCampaign(campaign_id, goal_text, phase_plan_text, campaign_yaml, phases)


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


def ledger_phase_state(phase: LedgerPhase, run_id: str) -> dict[str, Any]:
    phase_artifact_root = f"runs/{run_id}/phases/{phase.phase_id}"
    return {
        "phase_id": phase.phase_id,
        "name": phase.name,
        "lane": phase.lane,
        "dependencies": list(phase.dependencies),
        "status": "PENDING",
        "execution_mode": "ledger_only",
        "artifact_paths": {
            "spec": f"{phase_artifact_root}/spec.md",
            "handoff": f"{phase_artifact_root}/handoff.md",
            "review": f"{phase_artifact_root}/review.md",
            "verdict": f"{phase_artifact_root}/verdict.json",
        },
    }


def provider_phase_state(phase: LedgerPhase, run_id: str) -> dict[str, Any]:
    phase_artifact_root = f"runs/{run_id}/phases/{phase.phase_id}"
    return {
        "phase_id": phase.phase_id,
        "name": phase.name,
        "lane": phase.lane,
        "dependencies": list(phase.dependencies),
        "status": "PENDING",
        "execution_mode": "provider_wired",
        "artifact_paths": {
            "spec_prompt": f"{phase_artifact_root}/spec_prompt.md",
            "spec": f"{phase_artifact_root}/spec.md",
            "executor_prompt": f"{phase_artifact_root}/executor_prompt.md",
            "executor_output": f"{phase_artifact_root}/executor_output.md",
            "validation": f"{phase_artifact_root}/validation.md",
            "handoff": f"{phase_artifact_root}/handoff.md",
            "review_prompt": f"{phase_artifact_root}/review_prompt.md",
            "review": f"{phase_artifact_root}/review.md",
            "verdict": f"{phase_artifact_root}/verdict.json",
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


def write_zero_cost_ledger(run_dir: Path, campaign_id: str) -> None:
    record = {
        "timestamp": utc_now(),
        "campaign_id": campaign_id,
        "driver": LEDGER_ONLY_DRIVER,
        "provider": "none",
        "model": None,
        "cost_usd": 0.0,
        "note": "ledger_only_no_provider_calls",
    }
    (run_dir / "costs.jsonl").write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def stop_message(campaign_id: str) -> str:
    return (
        f"Ledger-only run completed for {campaign_id}.\n"
        "No phase implementation, provider calls, GitHub operations, PR creation, auto-merge, "
        "deployment, live trading, paper trading, broker calls, or network operations were performed.\n"
        "This STOP marker prevents resume from executing phase bodies until real Ralph execution is "
        "implemented, reviewed, and authorized.\n"
    )


def write_ledger_summary(run_dir: Path, state: dict[str, Any], note: str | None = None) -> None:
    lines = [
        "# Run Summary",
        "",
        f"Run: {state['run_id']}",
        f"Campaign: {state['campaign_id']}",
        f"Workflow: {state['workflow']}",
        f"Driver: {state['driver']}",
        f"Status: {state['status']}",
        f"Phases ledgered: {len(state['phases'])}",
        "Phase bodies executed: false",
        "",
        "## Artifacts",
        "",
        "- RUN_GOAL.md: copied from campaign GOAL.md",
        "- PHASE_PLAN.md: copied from campaign PHASE_PLAN.md",
        "- state.json: durable ledger state",
        "- events.jsonl: run event ledger",
        "- progress.txt: local progress log",
        "- costs.jsonl: zero-cost ledger entry",
        "- STOP: present by default to prevent execution",
        "",
        "## Phase Ledger",
        "",
    ]
    for phase in state["phases"]:
        lane = f" [{phase['lane']}]" if phase.get("lane") else ""
        name = f" - {phase['name']}" if phase.get("name") else ""
        lines.append(f"- {phase['phase_id']}{lane}: {phase['status']}{name}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- External providers called: false",
            "- Network used: false",
            "- Codex execution called by driver: false",
            "- Claude execution called by driver: false",
            "- GitHub operations performed: false",
            "- PRs created: false",
            "- Auto-merge performed: false",
            "- Deployment performed: false",
            "- Live or paper trading performed: false",
            "- Broker calls performed: false",
        ]
    )
    if note:
        lines.extend(["", "## Note", "", note])
    run_dir.joinpath("RUN_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def initialize_ledger_only_run(campaign_id: str) -> Path:
    campaign = load_ledger_campaign(campaign_id)
    run_id = run_id_for(campaign_id)
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True)

    created_at = utc_now()
    (run_dir / "RUN_GOAL.md").write_text(campaign.goal_text, encoding="utf-8")
    (run_dir / "PHASE_PLAN.md").write_text(campaign.phase_plan_text, encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("Ledger-only Workflow 2 run initialized.\n", encoding="utf-8")
    write_zero_cost_ledger(run_dir, campaign_id)

    state: dict[str, Any] = {
        "schema_version": "frontier-run-state-v3",
        "run_id": run_id,
        "campaign_id": campaign_id,
        "workflow": "workflow2",
        "driver": LEDGER_ONLY_DRIVER,
        "status": "LEDGER_ONLY_READY",
        "current_phase_id": None,
        "current_micro_attempt": 0,
        "phases": [ledger_phase_state(phase, run_id) for phase in campaign.phases],
        "stop_requested": False,
        "created_at": created_at,
        "started_at": created_at,
        "updated_at": created_at,
        "completed_at": None,
        "last_event_id": 0,
        "phase_execution_performed": False,
        "external_providers_called": False,
        "network_used": False,
        "codex_called_by_driver": False,
        "claude_called_by_driver": False,
        "github_operations_performed": False,
        "prs_created": False,
        "auto_merge_performed": False,
        "deployment_performed": False,
        "broker_or_trading_operations_performed": False,
        "required_campaign_files": list(REQUIRED_CAMPAIGN_FILES),
    }

    append_event(run_dir, state, "RUN_INIT", campaign_id=campaign_id, driver=LEDGER_ONLY_DRIVER)
    append_event(
        run_dir,
        state,
        "CAMPAIGN_LOAD",
        files=list(REQUIRED_CAMPAIGN_FILES),
        phase_count=len(campaign.phases),
    )
    append_event(run_dir, state, "PHASES_LEDGERED", phase_ids=[phase.phase_id for phase in campaign.phases])
    (run_dir / "STOP").write_text(stop_message(campaign_id), encoding="utf-8")
    append_event(run_dir, state, "STOP_WRITTEN", reason="ledger_only_completed_no_execution")
    write_state(run_dir, state)
    write_ledger_summary(run_dir, state, "Ledger-only run completed. No phase bodies were executed.")
    progress(run_dir, "Ledger-only run completed without phase execution.")
    return run_dir


def append_cost_record(
    run_dir: Path,
    state: dict[str, Any],
    *,
    provider: str,
    model: str | None,
    phase_id: str | None,
    note: str,
) -> None:
    record = {
        "timestamp": utc_now(),
        "run_id": state["run_id"],
        "campaign_id": state["campaign_id"],
        "phase_id": phase_id,
        "driver": PROVIDER_WIRED_DRIVER,
        "provider": provider,
        "model": model,
        "cost_usd": 0.0,
        "note": note,
    }
    with (run_dir / "costs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def initialize_provider_wired_run(
    campaign: LedgerCampaign,
    max_phases: int,
    max_phases_source: str,
) -> Path:
    campaign_id = campaign.campaign_id
    run_id = run_id_for(campaign_id)
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "phases").mkdir()

    created_at = utc_now()
    (run_dir / "RUN_GOAL.md").write_text(campaign.goal_text, encoding="utf-8")
    (run_dir / "PHASE_PLAN.md").write_text(campaign.phase_plan_text, encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "progress.txt").write_text("Provider-wired Workflow 2 run initialized.\n", encoding="utf-8")
    (run_dir / "costs.jsonl").write_text("", encoding="utf-8")

    mock_enabled = mock_providers_enabled()
    state: dict[str, Any] = {
        "schema_version": "frontier-run-state-v3",
        "run_id": run_id,
        "campaign_id": campaign_id,
        "workflow": "workflow2",
        "driver": PROVIDER_WIRED_DRIVER,
        "status": "RUNNING",
        "current_phase_id": None,
        "current_micro_attempt": 0,
        "phases": [provider_phase_state(phase, run_id) for phase in campaign.phases],
        "stop_requested": False,
        "created_at": created_at,
        "started_at": created_at,
        "updated_at": created_at,
        "completed_at": None,
        "last_event_id": 0,
        "provider_wired": True,
        "mock_providers": mock_enabled,
        "max_phases_requested": max_phases,
        "max_phases_source": max_phases_source,
        "campaign_phase_limit": campaign_phase_limit(campaign),
        "max_repair_attempts": DEFAULT_MAX_REPAIR_ATTEMPTS,
        "phase_execution_performed": False,
        "external_providers_called": False,
        "network_used": False,
        "codex_called_by_driver": False,
        "claude_called_by_driver": False,
        "github_operations_performed": False,
        "prs_created": False,
        "auto_merge_performed": False,
        "deployment_performed": False,
        "broker_or_trading_operations_performed": False,
        "required_campaign_files": list(REQUIRED_CAMPAIGN_FILES),
    }

    append_event(run_dir, state, "RUN_INIT", campaign_id=campaign_id, driver=PROVIDER_WIRED_DRIVER)
    append_event(
        run_dir,
        state,
        "CAMPAIGN_LOAD",
        files=list(REQUIRED_CAMPAIGN_FILES),
        phase_count=len(campaign.phases),
    )
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, "Run initialized. No phase has executed yet.")
    return run_dir


def provider_phase_dir(run_dir: Path, phase: dict[str, Any]) -> Path:
    return run_dir / "phases" / phase["phase_id"]


def next_pending_provider_phase(state: dict[str, Any]) -> dict[str, Any] | None:
    for phase in state["phases"]:
        if phase["status"] == "PENDING":
            return phase
    return None


def write_provider_summary(run_dir: Path, state: dict[str, Any], note: str | None = None) -> None:
    passing = [phase for phase in state["phases"] if phase["status"] in PASSING_VERDICTS]
    blocked = [phase for phase in state["phases"] if phase["status"] in {"BLOCKED", "REWORK"}]
    pending = [phase for phase in state["phases"] if phase["status"] == "PENDING"]
    lines = [
        "# Run Summary",
        "",
        f"Run: {state['run_id']}",
        f"Campaign: {state['campaign_id']}",
        f"Workflow: {state['workflow']}",
        f"Driver: {state['driver']}",
        f"Status: {state['status']}",
        f"Provider-wired: {str(state.get('provider_wired', False)).lower()}",
        f"Mock providers: {str(state.get('mock_providers', False)).lower()}",
        f"Max phases requested: {state.get('max_phases_requested', len(state['phases']))}",
        f"Max phases source: {state.get('max_phases_source', 'unknown')}",
        f"Passing phases: {len(passing)}/{len(state['phases'])}",
        f"Pending phases: {len(pending)}",
        "",
        "## Phase Results",
        "",
    ]
    for phase in state["phases"]:
        lane = f" [{phase['lane']}]" if phase.get("lane") else ""
        name = f" - {phase['name']}" if phase.get("name") else ""
        lines.append(f"- {phase['phase_id']}{lane}: {phase['status']}{name}")
    if blocked:
        lines.extend(["", "## Blocked Or Rework", ""])
        for phase in blocked:
            lines.append(f"- {phase['phase_id']}: {phase['status']}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- External providers called: {str(state.get('external_providers_called', False)).lower()}",
            f"- Network used: {str(state.get('network_used', False)).lower()}",
            f"- Codex execution called by driver: {str(state.get('codex_called_by_driver', False)).lower()}",
            f"- Claude execution called by driver: {str(state.get('claude_called_by_driver', False)).lower()}",
            "- GitHub operations performed: false",
            "- PRs created: false",
            "- Auto-merge performed: false",
            "- Deployment performed: false",
            "- Live or paper trading performed: false",
            "- Broker calls performed: false",
        ]
    )
    if note:
        lines.extend(["", "## Note", "", note])
    run_dir.joinpath("RUN_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_provider_stop(run_dir: Path, state: dict[str, Any], reason: str) -> None:
    (run_dir / "STOP").write_text(
        f"Workflow 2 provider-wired run stopped safely.\nReason: {reason}\n",
        encoding="utf-8",
    )
    append_event(run_dir, state, "STOP_WRITTEN", reason=reason)


def provider_stop_without_execution(run_dir: Path, state: dict[str, Any], reason: str) -> int:
    if state.get("status") != "COMPLETED":
        state["status"] = "STOPPED"
        state["stop_requested"] = True
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    append_event(run_dir, state, "RUN_RESUME_STOP_FILE_PRESENT", reason=reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, "STOP existed before resume. No execution was performed.")
    progress(run_dir, "Resume inspected STOP file and performed no execution.")
    print(f"Run {state['run_id']} is stopped by STOP. No execution was performed.")
    return 0


def set_provider_phase_status(phase: dict[str, Any], status: str) -> None:
    phase["status"] = status
    phase["updated_at"] = utc_now()


def finish_provider_phase(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    status: str,
    *,
    event: str,
    reason: str | None = None,
) -> None:
    set_provider_phase_status(phase, status)
    phase["completed_at"] = utc_now()
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    if status in PASSING_VERDICTS:
        state["phase_execution_performed"] = True
    append_event(run_dir, state, event, phase_id=phase["phase_id"], status=status, reason=reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, reason)
    progress(run_dir, f"{phase['phase_id']} finished with {status}.")


def block_provider_run(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    status: str,
    reason: str,
) -> None:
    finish_provider_phase(run_dir, state, phase, status, event="PHASE_STOPPED", reason=reason)
    state["status"] = "STOPPED"
    state["stop_requested"] = True
    write_provider_stop(run_dir, state, reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, reason)


def phase_label(phase: dict[str, Any]) -> str:
    name = phase.get("name")
    return f"{phase['phase_id']} - {name}" if name else phase["phase_id"]


def spec_generation_prompt(phase: dict[str, Any]) -> str:
    dependencies = ", ".join(phase.get("dependencies") or []) or "none"
    return f"""You are Claude running in headless mode for Frontier Workflow 2.

Read these repository files before producing output:
- AGENTS.md
- CLAUDE.md
- frontier.yaml
- campaigns/ALPHA_SYSTEM_V1/GOAL.md
- campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
- campaigns/ALPHA_SYSTEM_V1/campaign.yaml
- campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
- campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
- campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md

Generate a concrete phase spec for exactly one phase:
- Phase: {phase_label(phase)}
- Lane: {phase.get("lane") or "unknown"}
- Dependencies: {dependencies}

Requirements:
- Obey the allowed and forbidden scope in the campaign files.
- Keep the spec local-first and safe.
- Do not implement anything.
- Do not introduce live trading, paper trading, broker calls, IBKR actions, destructive cleanup, deployment, PR creation, or auto-merge.
- Make validation commands explicit and safe for this phase.
- Require explicit staging only; forbid `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, and force push.
- Output markdown only.
"""


def executor_prompt(phase: dict[str, Any], spec_text: str, phase_dir: Path) -> str:
    return f"""You are Codex running as the executor for Frontier Workflow 2.

Execute exactly the generated phase spec below for {phase_label(phase)}. Do not broaden scope.

Safety rules:
- Do not perform live trading, paper trading, broker operations, IBKR actions, order routing, production deployment, PR creation, auto-merge, or destructive cleanup.
- Do not use `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, or force push.
- Do not weaken tests or add visible test-only branches.
- Keep generated local-only artifacts out of git.
- Run only validation that is safe and requested by the spec.
- Write or update required files, and write a phase handoff if the phase requires one.

Run artifact directory available to you:
{phase_dir.relative_to(ROOT)}

Generated spec:

{spec_text}
"""


def review_prompt(phase: dict[str, Any], spec_text: str, executor_text: str, validation_text: str) -> str:
    return f"""You are Claude reviewing one Frontier Workflow 2 phase.

Review phase {phase_label(phase)} against:
- AGENTS.md
- CLAUDE.md
- frontier.yaml
- campaigns/ALPHA_SYSTEM_V1 files
- the generated phase spec
- executor output
- validation output

Return markdown. Include exactly one verdict line using one of:
VERDICT: PASS
VERDICT: PASS_WITH_WARNINGS
VERDICT: REWORK
VERDICT: BLOCKED

Be conservative. Block broker/live/paper/IBKR scope, destructive operations, hidden failed runs, test weakening, artifact policy violations, unsupported alpha claims, and scope drift.

Generated spec:

{spec_text}

Executor output:

{executor_text}

Validation output:

{validation_text}
"""


def repair_prompt(phase: dict[str, Any], spec_text: str, review_text: str, validation_text: str) -> str:
    return f"""You are Codex performing one bounded repair attempt for Frontier Workflow 2.

Repair only valid in-scope findings for {phase_label(phase)}. Do not broaden scope.

Safety rules:
- Do not perform live trading, paper trading, broker operations, IBKR actions, order routing, production deployment, PR creation, auto-merge, or destructive cleanup.
- Do not use `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, or force push.
- Do not weaken tests or add visible test-only branches.

Generated spec:

{spec_text}

Review findings:

{review_text}

Validation output:

{validation_text}
"""


def mock_spec_text(phase: dict[str, Any]) -> str:
    dependencies = ", ".join(phase.get("dependencies") or []) or "none"
    return f"""# Mock Spec: {phase_label(phase)}

Lane: {phase.get("lane") or "unknown"}

Dependencies: {dependencies}

## Purpose

Exercise the provider-wired Workflow 2 conductor in deterministic mock-provider mode for one phase.

## Scope

Allowed:
- Write run artifacts under `runs/<run_id>/phases/{phase['phase_id']}/`.
- Create a harmless mock execution marker in that phase artifact directory.

Forbidden:
- Production source changes.
- Live trading, paper trading, broker operations, IBKR actions, order routing, deployment, PR creation, auto-merge, or destructive cleanup.

## Validation

- `just frontier-doctor`
- `just verify-canaries`
"""


def mock_executor_text(phase: dict[str, Any], phase_dir: Path) -> str:
    marker = phase_dir / "mock_execution.txt"
    marker.write_text(
        f"Mock provider execution for {phase['phase_id']} at {utc_now()}.\n",
        encoding="utf-8",
    )
    return (
        f"# Mock Executor Output: {phase['phase_id']}\n\n"
        "- FRONTIER_MOCK_PROVIDERS=1 was set, so Codex was not called.\n"
        f"- Wrote harmless marker `{marker.relative_to(ROOT)}`.\n"
        "- No production source, GitHub, merge, deployment, broker, paper, or live trading operation was performed.\n"
    )


def mock_review_text(phase: dict[str, Any]) -> str:
    return (
        f"# Mock Review: {phase['phase_id']}\n\n"
        "The deterministic mock-provider phase artifacts are present and validation completed.\n\n"
        "VERDICT: PASS\n"
    )


def provider_handoff_text(phase: dict[str, Any], verdict: str, mock_enabled: bool) -> str:
    mode = "mock-provider" if mock_enabled else "provider-wired"
    return f"""# {phase['phase_id']} Handoff

## Scope Completed

- Ran the Workflow 2 conductor for `{phase['phase_id']}` in {mode} mode.
- Wrote required run artifacts under `runs/<run_id>/phases/{phase['phase_id']}/`.
- Recorded review verdict `{verdict}`.

## Safety

- No GitHub operation, PR creation, auto-merge, deployment, broker operation, paper trading, live trading, or IBKR action was performed by the conductor.

## Validation

- Validation output is recorded in `validation.md`.
"""


def claude_headless(prompt: str) -> CommandResult:
    return run_local_command(["claude", "-p", prompt])


def codex_noninteractive(prompt: str) -> CommandResult:
    return run_local_command(["codex", "exec", "--sandbox", "workspace-write", prompt])


def write_provider_failure(path: Path, title: str, result: CommandResult) -> None:
    path.write_text(f"# {title}\n\n{command_block(result)}\n", encoding="utf-8")


def run_validation_commands() -> tuple[bool, str]:
    results = [
        run_local_command(["just", "frontier-doctor"]),
        run_local_command(["just", "verify-canaries"]),
    ]
    ok = all(result.returncode == 0 for result in results)
    body = ["# Validation", ""]
    for result in results:
        body.append(command_block(result))
    return ok, "\n".join(body)


def parse_review_verdict(text: str) -> str:
    if "VERDICT: PASS_WITH_WARNINGS" in text:
        return "PASS_WITH_WARNINGS"
    if "VERDICT: PASS" in text:
        return "PASS"
    if "VERDICT: REWORK" in text:
        return "REWORK"
    return "BLOCKED"


def write_provider_verdict(
    phase_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    source: str,
) -> None:
    write_json(
        phase_dir / "verdict.json",
        {
            "schema_version": "frontier-review-verdict-v1",
            "campaign_id": state["campaign_id"],
            "run_id": state["run_id"],
            "phase_id": phase["phase_id"],
            "verdict": verdict,
            "source": source,
            "mock_providers": state.get("mock_providers", False),
            "external_providers_called": state.get("external_providers_called", False),
            "network_used": state.get("network_used", False),
            "auto_merge_performed": False,
            "parsed_at": utc_now(),
        },
    )


def execute_provider_phase(run_dir: Path, state: dict[str, Any], phase: dict[str, Any]) -> bool:
    mock_enabled = bool(state.get("mock_providers"))
    phase_id = phase["phase_id"]
    phase_dir = provider_phase_dir(run_dir, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)

    state["status"] = "RUNNING"
    state["current_phase_id"] = phase_id
    state["current_micro_attempt"] = 1
    phase["started_at"] = utc_now()
    append_event(run_dir, state, "PHASE_SELECT", phase_id=phase_id)
    write_state(run_dir, state)
    progress(run_dir, f"Selected {phase_id}.")

    spec_prompt_text = spec_generation_prompt(phase)
    (phase_dir / "spec_prompt.md").write_text(spec_prompt_text, encoding="utf-8")
    if mock_enabled:
        spec_text = mock_spec_text(phase)
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_spec")
    else:
        state["claude_called_by_driver"] = True
        state["external_providers_called"] = True
        state["network_used"] = True
        append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="spec_generation")
        result = claude_headless(spec_prompt_text)
        if result.returncode != 0:
            write_provider_failure(phase_dir / "spec.md", "Claude Spec Generation Failed", result)
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="spec_generation_error")
            block_provider_run(run_dir, state, phase, "BLOCKED", "Claude spec generation failed.")
            return False
        spec_text = result.stdout
    (phase_dir / "spec.md").write_text(spec_text, encoding="utf-8")
    set_provider_phase_status(phase, "SPEC_READY")
    append_event(run_dir, state, "SPEC_READY", phase_id=phase_id)
    write_state(run_dir, state)

    exec_prompt_text = executor_prompt(phase, spec_text, phase_dir)
    (phase_dir / "executor_prompt.md").write_text(exec_prompt_text, encoding="utf-8")
    if mock_enabled:
        executor_text = mock_executor_text(phase, phase_dir)
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_codex_execute")
    else:
        state["codex_called_by_driver"] = True
        state["external_providers_called"] = True
        state["network_used"] = True
        append_cost_record(run_dir, state, provider="codex", model=None, phase_id=phase_id, note="phase_execution")
        result = codex_noninteractive(exec_prompt_text)
        executor_text = command_block(result)
        if result.returncode != 0:
            (phase_dir / "executor_output.md").write_text(executor_text, encoding="utf-8")
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="executor_error")
            block_provider_run(run_dir, state, phase, "BLOCKED", "Codex executor returned nonzero.")
            return False
    (phase_dir / "executor_output.md").write_text(executor_text, encoding="utf-8")
    set_provider_phase_status(phase, "EXECUTED")
    append_event(run_dir, state, "EXECUTED", phase_id=phase_id)
    write_state(run_dir, state)

    validation_ok, validation_text = run_validation_commands()
    (phase_dir / "validation.md").write_text(validation_text, encoding="utf-8")
    if not validation_ok:
        write_provider_verdict(phase_dir, state, phase, "REWORK", source="validation")
        block_provider_run(run_dir, state, phase, "REWORK", "Validation failed.")
        return False
    set_provider_phase_status(phase, "VALIDATED")
    append_event(run_dir, state, "VALIDATED", phase_id=phase_id)
    write_state(run_dir, state)

    review_prompt_text = review_prompt(phase, spec_text, executor_text, validation_text)
    (phase_dir / "review_prompt.md").write_text(review_prompt_text, encoding="utf-8")
    if mock_enabled:
        review_text = mock_review_text(phase)
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_review")
    else:
        append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="phase_review")
        result = claude_headless(review_prompt_text)
        review_text = result.stdout if result.returncode == 0 else command_block(result)
        if result.returncode != 0:
            (phase_dir / "review.md").write_text(review_text, encoding="utf-8")
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="claude_review_error")
            block_provider_run(run_dir, state, phase, "BLOCKED", "Claude review returned nonzero.")
            return False
    (phase_dir / "review.md").write_text(review_text, encoding="utf-8")
    verdict = parse_review_verdict(review_text)
    write_provider_verdict(phase_dir, state, phase, verdict, source="review")
    set_provider_phase_status(phase, "REVIEWED")
    append_event(run_dir, state, "REVIEWED", phase_id=phase_id, verdict=verdict)
    write_state(run_dir, state)

    if verdict == "REWORK":
        verdict = run_provider_repair_once(run_dir, state, phase, spec_text, review_text, validation_text)
    if verdict not in PASSING_VERDICTS:
        block_provider_run(run_dir, state, phase, "BLOCKED", f"Review verdict was {verdict}.")
        return False

    (phase_dir / "handoff.md").write_text(provider_handoff_text(phase, verdict, mock_enabled), encoding="utf-8")
    finish_provider_phase(run_dir, state, phase, verdict, event="PHASE_PASS")
    return True


def run_provider_repair_once(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    spec_text: str,
    review_text: str,
    validation_text: str,
) -> str:
    phase_id = phase["phase_id"]
    phase_dir = provider_phase_dir(run_dir, phase)
    mock_enabled = bool(state.get("mock_providers"))
    repair_prompt_text = repair_prompt(phase, spec_text, review_text, validation_text)
    (phase_dir / "repair_prompt.md").write_text(repair_prompt_text, encoding="utf-8")
    append_event(run_dir, state, "REPAIR_START", phase_id=phase_id, attempt=1)
    write_state(run_dir, state)

    if mock_enabled:
        repair_text = f"# Mock Repair Output: {phase_id}\n\nNo repair was needed in mock mode.\n"
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_codex_repair")
    else:
        state["codex_called_by_driver"] = True
        state["external_providers_called"] = True
        state["network_used"] = True
        append_cost_record(run_dir, state, provider="codex", model=None, phase_id=phase_id, note="repair_execution")
        result = codex_noninteractive(repair_prompt_text)
        repair_text = command_block(result)
        if result.returncode != 0:
            (phase_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_error")
            return "BLOCKED"
    (phase_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")

    validation_ok, repair_validation_text = run_validation_commands()
    (phase_dir / "repair_validation.md").write_text(repair_validation_text, encoding="utf-8")
    if not validation_ok:
        write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_validation")
        return "BLOCKED"

    review_prompt_text = review_prompt(phase, spec_text, repair_text, repair_validation_text)
    (phase_dir / "review_prompt.md").write_text(review_prompt_text, encoding="utf-8")
    if mock_enabled:
        repaired_review_text = mock_review_text(phase)
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_repair_review")
    else:
        append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="repair_review")
        result = claude_headless(review_prompt_text)
        repaired_review_text = result.stdout if result.returncode == 0 else command_block(result)
        if result.returncode != 0:
            (phase_dir / "review.md").write_text(repaired_review_text, encoding="utf-8")
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_review_error")
            return "BLOCKED"
    (phase_dir / "review.md").write_text(repaired_review_text, encoding="utf-8")
    verdict = parse_review_verdict(repaired_review_text)
    if verdict not in PASSING_VERDICTS:
        verdict = "BLOCKED"
    write_provider_verdict(phase_dir, state, phase, verdict, source="repair_review")
    append_event(run_dir, state, "REPAIR_REVIEWED", phase_id=phase_id, verdict=verdict)
    write_state(run_dir, state)
    return verdict


def continue_provider_wired_run(
    run_dir: Path,
    state: dict[str, Any],
    max_phases: int,
    max_phases_source: str | None = None,
) -> int:
    state["max_phases_requested"] = max_phases
    if max_phases_source is not None:
        state["max_phases_source"] = max_phases_source
    state.setdefault("mock_providers", mock_providers_enabled())
    executed = 0

    while True:
        if (run_dir / "STOP").exists():
            return provider_stop_without_execution(run_dir, state, "STOP file exists before next phase.")

        phase = next_pending_provider_phase(state)
        if phase is None:
            state["status"] = "COMPLETED"
            state["stop_requested"] = False
            state["current_phase_id"] = None
            state["current_micro_attempt"] = 0
            state["completed_at"] = utc_now()
            append_event(run_dir, state, "RUN_COMPLETE")
            write_provider_stop(run_dir, state, "All parsed phases completed.")
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, "All parsed phases completed.")
            progress(run_dir, "Run completed.")
            print(f"Completed provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
            return 0

        if executed >= max_phases:
            state["status"] = "STOPPED"
            state["stop_requested"] = True
            state["current_phase_id"] = None
            state["current_micro_attempt"] = 0
            write_provider_stop(run_dir, state, f"Requested max phases reached: {max_phases}.")
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, f"Requested max phases reached: {max_phases}.")
            progress(run_dir, f"Stopped after requested max phases: {max_phases}.")
            print(f"Stopped after {executed} provider-wired phase(s) at {run_dir.relative_to(ROOT)}")
            return 0

        if not execute_provider_phase(run_dir, state, phase):
            print(f"Stopped provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
            return 0
        executed += 1


def run_provider_wired_campaign(campaign_id: str, max_phases: int | None) -> int:
    try:
        if campaign_id != ALPHA_SYSTEM_V1_CAMPAIGN_ID:
            raise ValueError(f"Provider-wired support is implemented only for {ALPHA_SYSTEM_V1_CAMPAIGN_ID}.")
        campaign = load_ledger_campaign(campaign_id)
        resolved_max_phases, source = resolve_max_phases(campaign, max_phases)
        run_dir = initialize_provider_wired_run(campaign, resolved_max_phases, source)
        state = read_json(run_dir / "state.json")
        return continue_provider_wired_run(run_dir, state, resolved_max_phases, source)
    except ValueError as error:
        print(error)
        return 2


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


def run_ledger_only_campaign(campaign_id: str) -> int:
    try:
        run_dir = initialize_ledger_only_run(campaign_id)
    except ValueError as error:
        print(error)
        return 2
    print(f"Created ledger-only Workflow 2 run at {run_dir.relative_to(ROOT)}")
    print("No phase bodies, providers, GitHub operations, PRs, merges, network calls, or trading operations were performed.")
    return 0


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


def run_campaign(
    campaign_id: str | None,
    goal: str | None,
    lane: str,
    *,
    ledger_only: bool = False,
    provider_wired: bool = False,
    max_phases: int | None = None,
) -> int:
    if campaign_id == TOY_CAMPAIGN_ID:
        return run_toy_campaign(campaign_id)
    if campaign_id == ALPHA_SYSTEM_V1_CAMPAIGN_ID:
        if ledger_only:
            return run_ledger_only_campaign(campaign_id)
        if provider_wired or not ledger_only:
            return run_provider_wired_campaign(campaign_id, max_phases)

    resolved_campaign = campaign_id or "AD_HOC_GOAL"
    run_dir = init_scaffold_run(resolved_campaign, goal, lane)
    print(f"Initialized Workflow 2 scaffold run at {run_dir.relative_to(ROOT)}")
    print("No external provider, GitHub, network, or merge operation was performed.")
    return 0


def resume_ledger_only_run(run_dir: Path, state: dict[str, Any]) -> int:
    stop_path = run_dir / "STOP"
    if stop_path.exists():
        state["status"] = "STOPPED"
        state["stop_requested"] = True
        state["current_phase_id"] = None
        state["current_micro_attempt"] = 0
        append_event(run_dir, state, "RUN_RESUME_STOP_FILE_PRESENT")
        write_state(run_dir, state)
        write_ledger_summary(run_dir, state, "STOP existed before resume. No execution was performed.")
        progress(run_dir, "Resume inspected STOP file and performed no execution.")
        print(f"Run {state['run_id']} is stopped by STOP. No execution was performed.")
        return 0

    state["status"] = "LEDGER_ONLY_READY"
    state["stop_requested"] = False
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    append_event(run_dir, state, "RUN_RESUME_LEDGER_ONLY")
    stop_path.write_text(stop_message(state["campaign_id"]), encoding="utf-8")
    append_event(run_dir, state, "STOP_WRITTEN", reason="ledger_only_resume_safety")
    write_state(run_dir, state)
    write_ledger_summary(run_dir, state, "Ledger-only resume refreshed summary and STOP. No execution was performed.")
    progress(run_dir, "Ledger-only resume refreshed summary and STOP.")
    print(f"Ledger-only run {state['run_id']} inspected. No execution was performed.")
    return 0


def resume_provider_wired_run(run_dir: Path, state: dict[str, Any], max_phases: int | None) -> int:
    if (run_dir / "STOP").exists():
        return provider_stop_without_execution(run_dir, state, "STOP file exists on resume.")
    try:
        campaign = load_ledger_campaign(state["campaign_id"])
        resolved_max_phases, source = resolve_max_phases(campaign, max_phases)
    except ValueError as error:
        print(error)
        return 2
    state["status"] = "RUNNING"
    state["stop_requested"] = False
    state["completed_at"] = None
    state.setdefault("provider_wired", True)
    state.setdefault("mock_providers", mock_providers_enabled())
    append_event(run_dir, state, "RUN_RESUME", mode="provider_wired", max_phases=resolved_max_phases)
    write_state(run_dir, state)
    progress(run_dir, "Provider-wired run resumed.")
    return continue_provider_wired_run(run_dir, state, resolved_max_phases, source)


def resume(run_id: str, *, provider_wired: bool = False, max_phases: int | None = None) -> int:
    run_dir = ROOT / "runs" / run_id
    state_path = run_dir / "state.json"
    if not state_path.exists():
        print(f"Unknown run id: {run_id}")
        return 1

    state = read_json(state_path)
    if state.get("driver") == PROVIDER_WIRED_DRIVER or (
        provider_wired and state.get("campaign_id") == ALPHA_SYSTEM_V1_CAMPAIGN_ID
    ):
        return resume_provider_wired_run(run_dir, state, max_phases)
    if state.get("campaign_id") == ALPHA_SYSTEM_V1_CAMPAIGN_ID or state.get("driver") == LEDGER_ONLY_DRIVER:
        return resume_ledger_only_run(run_dir, state)
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
    run_mode = run_parser.add_mutually_exclusive_group()
    run_mode.add_argument("--ledger-only", action="store_true")
    run_mode.add_argument("--provider-wired", action="store_true")
    run_parser.add_argument("--max-phases", type=int)
    resume_parser = subparsers.add_parser("resume", help="Resume a stopped toy run or inspect a scaffold run.")
    resume_parser.add_argument("--run-id", required=True)
    resume_parser.add_argument("--provider-wired", action="store_true")
    resume_parser.add_argument("--max-phases", type=int)
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_campaign(
            args.campaign_id,
            args.goal,
            args.lane,
            ledger_only=args.ledger_only,
            provider_wired=args.provider_wired,
            max_phases=args.max_phases,
        )
    if args.command == "resume":
        return resume(args.run_id, provider_wired=args.provider_wired, max_phases=args.max_phases)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
