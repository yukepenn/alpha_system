"""Local Ralph Workflow 2 driver for alpha_system.

This module performs generic harness orchestration only. GitHub and merge
operations go through local ``gh`` helpers and lane gates; deployment, live
trading, paper trading, broker calls, browser access, and destructive cleanup
are intentionally out of scope.

It includes a deterministic local toy campaign for Workflow 2 readiness, a
generic ledger-only mode, and a generic provider-wired local conductor that can
be exercised with deterministic mock providers.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.command_runner import CommandRunner
from tools.frontier.config import load_config
from tools.frontier.git_utils import commit_phase_changes, write_git_phase_artifacts
from tools.frontier.github_utils import (
    CI_SUCCESS,
    classify_ci_checks,
    create_pr,
    detect_default_branch,
    inspect_branch_protection,
    wait_for_ci,
    write_branch_protection_artifacts,
    write_ci_status_artifacts,
)
from tools.frontier.merge_gate import evaluate_merge_gate, perform_merge, write_merge_gate_artifacts
from tools.frontier.provider_adapters import ClaudeProviderAdapter, CodexProviderAdapter
from tools.frontier.provider_config import ProviderRuntimeConfig, load_provider_config
from tools.frontier.verdict import ReviewVerdict, parse_done_check_text, parse_review_text
from tools.frontier.worktree_manager import WorktreeManager, phase_branch_name, worktree_mode_enabled

TOY_CAMPAIGN_ID = "G005_WORKFLOW2_TOY"
LEDGER_ONLY_DRIVER = "ralph_frontier_strict_ledger_only_v1"
PROVIDER_WIRED_DRIVER = "ralph_frontier_provider_wired_mvc_v1"
SCAFFOLD_DRIVER = "ralph_frontier_strict_scaffold"
DEFAULT_MAX_REPAIR_ATTEMPTS = 1
REQUIRED_CAMPAIGN_FILES = (
    "GOAL.md",
    "PHASE_PLAN.md",
    "campaign.yaml",
    "ACCEPTANCE.md",
    "RISK_REGISTER.md",
    "RUNBOOK.md",
)
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
    return load_provider_config(ROOT).mock_providers


def runtime_config() -> ProviderRuntimeConfig:
    return load_provider_config(ROOT)


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


def campaign_phase_limit(campaign: LedgerCampaign) -> int:
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
    campaign: LedgerCampaign,
    explicit_max_phases: int | None,
) -> tuple[int, str]:
    if explicit_max_phases is not None:
        return parse_positive_int(explicit_max_phases, "--max-phases"), "cli"
    env_limit = env_max_phases()
    if env_limit is not None:
        return env_limit, "env"
    return campaign_phase_limit(campaign), "campaign"


def run_local_command(command: list[str], *, root: Path = ROOT) -> CommandResult:
    result = CommandRunner(root).run(command)
    return CommandResult(tuple(result.command), result.return_code, result.stdout, result.stderr)


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
    write_heartbeat(run_dir, state)


def progress(run_dir: Path, message: str) -> None:
    with (run_dir / "progress.txt").open("a", encoding="utf-8") as handle:
        handle.write(f"{utc_now()} {message}\n")


def write_heartbeat(run_dir: Path, state: dict[str, Any]) -> None:
    heartbeat = {
        "run_id": state.get("run_id"),
        "campaign_id": state.get("campaign_id"),
        "status": state.get("status"),
        "current_phase_id": state.get("current_phase_id"),
        "updated_at": utc_now(),
        "pid": os.getpid(),
    }
    write_json(run_dir / "heartbeat.json", heartbeat)


@contextlib.contextmanager
def run_lock(run_dir: Path):
    lock_path = run_dir / "RUN.lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(f"Run lock already exists: {lock_path}") from error
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created_at": utc_now()}, sort_keys=True) + "\n")
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def env_or_config_number(env_name: str, config_value: Any, default: float) -> float:
    raw = os.environ.get(env_name)
    value = raw if raw not in {None, ""} else config_value
    if value in {None, ""}:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def provider_budget_limits() -> dict[str, float]:
    workflow2 = runtime_config().raw.get("workflow2", {})
    if not isinstance(workflow2, dict):
        workflow2 = {}
    return {
        "max_run_minutes": env_or_config_number(
            "FRONTIER_MAX_RUN_MINUTES", workflow2.get("max_run_minutes"), 720
        ),
        "max_phase_minutes": env_or_config_number(
            "FRONTIER_MAX_PHASE_MINUTES", workflow2.get("max_phase_minutes"), 120
        ),
        "max_estimated_usd": env_or_config_number(
            "FRONTIER_MAX_ESTIMATED_USD", workflow2.get("max_estimated_usd"), 0
        ),
    }


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def elapsed_minutes_since(value: str | None) -> float:
    started = parse_timestamp(value)
    if started is None:
        return 0.0
    return (datetime.now(UTC) - started).total_seconds() / 60


def stop_requested(run_dir: Path) -> bool:
    return (run_dir / "STOP").exists()


def check_run_budget(run_dir: Path, state: dict[str, Any]) -> str | None:
    limits = provider_budget_limits()
    if elapsed_minutes_since(state.get("started_at")) > limits["max_run_minutes"]:
        return f"Max run minutes exceeded: {limits['max_run_minutes']}."
    if float(state.get("estimated_cost_usd", 0.0)) > limits["max_estimated_usd"] > 0:
        return f"Max estimated cost exceeded: {limits['max_estimated_usd']}."
    if stop_requested(run_dir):
        return "STOP file exists."
    return None


def phase_elapsed_minutes(phase: dict[str, Any]) -> float:
    return elapsed_minutes_since(phase.get("started_at"))


def check_phase_budget(phase: dict[str, Any]) -> str | None:
    limits = provider_budget_limits()
    if phase_elapsed_minutes(phase) > limits["max_phase_minutes"]:
        return f"Max phase minutes exceeded: {limits['max_phase_minutes']}."
    return None


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
        raise ValueError("PyYAML is required to parse campaign.yaml for Workflow 2 runs.") from error

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
    if not phases:
        raise ValueError(f"Campaign {campaign_id} campaign.yaml must contain at least one phase.")
    return data


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("`", "").split()).strip()
    return cleaned or None


def parse_phase_dependencies(raw: Any, *, campaign_id: str, phase_id: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"Campaign {campaign_id} dependencies for {phase_id} must be a list.")
    dependencies: list[str] = []
    for dependency in raw:
        cleaned = clean_text(dependency)
        if cleaned:
            dependencies.append(cleaned)
    return tuple(dependencies)


def parse_campaign_phases(campaign_yaml: dict[str, Any], campaign_id: str) -> tuple[LedgerPhase, ...]:
    raw_phases = campaign_yaml.get("phases")
    if not isinstance(raw_phases, list):
        raise ValueError(f"Campaign {campaign_id} campaign.yaml must contain a phases list.")

    default_lane = clean_text(campaign_yaml.get("default_lane"))
    phases: list[LedgerPhase] = []
    seen: set[str] = set()
    for offset, raw_phase in enumerate(raw_phases, start=1):
        if not isinstance(raw_phase, dict):
            raise ValueError(f"Campaign {campaign_id} phase entry {offset} must be a mapping.")
        phase_id = clean_text(raw_phase.get("id") or raw_phase.get("phase_id"))
        if not phase_id:
            raise ValueError(f"Campaign {campaign_id} phase entry {offset} is missing an id.")
        if phase_id in seen:
            raise ValueError(f"Campaign {campaign_id} campaign.yaml repeats phase id {phase_id}.")
        seen.add(phase_id)

        dependencies = parse_phase_dependencies(
            raw_phase.get("dependencies", raw_phase.get("depends_on", [])),
            campaign_id=campaign_id,
            phase_id=phase_id,
        )
        phases.append(
            LedgerPhase(
                phase_id=phase_id,
                name=clean_text(raw_phase.get("name") or raw_phase.get("title")),
                lane=clean_text(raw_phase.get("lane")) or default_lane,
                dependencies=dependencies,
            )
        )

    phase_ids = {phase.phase_id for phase in phases}
    for phase in phases:
        unknown = [dependency for dependency in phase.dependencies if dependency not in phase_ids]
        if unknown:
            raise ValueError(
                f"Campaign {campaign_id} phase {phase.phase_id} has unknown dependencies: "
                f"{', '.join(unknown)}."
            )
        if phase.phase_id in phase.dependencies:
            raise ValueError(f"Campaign {campaign_id} phase {phase.phase_id} depends on itself.")
    return tuple(phases)


def load_ledger_campaign(campaign_id: str) -> LedgerCampaign:
    campaign_dir = require_campaign_files(campaign_id)
    goal_text = (campaign_dir / "GOAL.md").read_text(encoding="utf-8")
    phase_plan_text = (campaign_dir / "PHASE_PLAN.md").read_text(encoding="utf-8")
    campaign_yaml = load_campaign_yaml(campaign_id, campaign_dir)
    phases = parse_campaign_phases(campaign_yaml, campaign_id)
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
            "review_prompt": f"{phase_artifact_root}/review_prompt.md",
            "review": f"{phase_artifact_root}/review.md",
            "verdict": f"{phase_artifact_root}/verdict.json",
            "done_check_prompt": f"{phase_artifact_root}/done_check_prompt.md",
            "done_check": f"{phase_artifact_root}/done_check.md",
            "done_check_json": f"{phase_artifact_root}/done_check.json",
            "handoff": f"{phase_artifact_root}/handoff.md",
            "git_phase": f"{phase_artifact_root}/git_phase.json",
            "ci_status": f"{phase_artifact_root}/ci_status.json",
            "merge_gate": f"{phase_artifact_root}/merge_gate.json",
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
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "attempts": {phase.phase_id: 0 for phase in TOY_PHASES},
        "provider_mode": "none",
        "lane_policy_snapshot": {},
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
        "attempts": {phase.phase_id: 0 for phase in campaign.phases},
        "provider_mode": "none",
        "lane_policy_snapshot": runtime_config().lane_policies,
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
    state["estimated_cost_usd"] = float(state.get("estimated_cost_usd", 0.0))
    record = {
        "timestamp": utc_now(),
        "run_id": state["run_id"],
        "campaign_id": state["campaign_id"],
        "phase_id": phase_id,
        "driver": PROVIDER_WIRED_DRIVER,
        "provider": provider,
        "model": model,
        "cost_usd": 0.0,
        "estimated_usd": 0.0,
        "note": note,
    }
    with (run_dir / "costs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def initialize_provider_wired_run(
    campaign: LedgerCampaign,
    max_phases: int,
    max_phases_source: str,
    *,
    worktree_mode: bool | None = None,
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

    config = runtime_config()
    mock_enabled = config.mock_providers
    resolved_worktree_mode = worktree_mode_enabled(worktree_mode, ROOT)
    workflow2 = config.raw.get("workflow2", {}) if isinstance(config.raw.get("workflow2"), dict) else {}
    max_repairs = int(os.environ.get("FRONTIER_MAX_REPAIR_ATTEMPTS") or workflow2.get("max_repair_attempts_default", 2))
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
        "provider_mode": config.provider_mode,
        "provider_timeout_seconds": config.provider_timeout_seconds,
        "worktree_mode": resolved_worktree_mode,
        "worktree_root": str(config.worktree_root) if config.worktree_root else None,
        "max_phases_requested": max_phases,
        "max_phases_source": max_phases_source,
        "campaign_phase_limit": campaign_phase_limit(campaign),
        "max_repair_attempts": max_repairs,
        "estimated_cost_usd": 0.0,
        "attempts": {phase.phase_id: 0 for phase in campaign.phases},
        "repair_attempts": {phase.phase_id: 0 for phase in campaign.phases},
        "lane_policy_snapshot": config.lane_policies,
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
    resumable = {"SPEC_READY", "EXECUTED", "VALIDATED", "REVIEWED", "REWORK", "REPAIRED"}
    current = state.get("current_phase_id")
    if current:
        for phase in state["phases"]:
            if phase["phase_id"] == current and phase.get("status") in resumable:
                return phase
    for phase in state["phases"]:
        if phase["status"] in resumable:
            return phase
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
        f"Provider mode: {state.get('provider_mode', 'unknown')}",
        f"Worktree mode: {str(state.get('worktree_mode', False)).lower()}",
        f"Max phases requested: {state.get('max_phases_requested', len(state['phases']))}",
        f"Max phases source: {state.get('max_phases_source', 'unknown')}",
        f"Max repair attempts: {state.get('max_repair_attempts', DEFAULT_MAX_REPAIR_ATTEMPTS)}",
        f"Estimated cost USD: {state.get('estimated_cost_usd', 0.0)}",
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
            f"- GitHub operations performed: {str(state.get('github_operations_performed', False)).lower()}",
            f"- PRs created: {str(state.get('prs_created', False)).lower()}",
            f"- Auto-merge performed: {str(state.get('auto_merge_performed', False)).lower()}",
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


def campaign_file_list(campaign_id: str) -> str:
    return "\n".join(f"- campaigns/{campaign_id}/{name}" for name in REQUIRED_CAMPAIGN_FILES)


def spec_generation_prompt(phase: dict[str, Any], campaign_id: str) -> str:
    dependencies = ", ".join(phase.get("dependencies") or []) or "none"
    return f"""You are Claude running in headless mode for Frontier Workflow 2.

Read these repository files before producing output:
- AGENTS.md
- CLAUDE.md
- frontier.yaml
{campaign_file_list(campaign_id)}

Generate a concrete phase spec for exactly one phase:
- Campaign: {campaign_id}
- Phase: {phase_label(phase)}
- Lane: {phase.get("lane") or "unknown"}
- Dependencies: {dependencies}

Requirements:
- Obey the allowed and forbidden scope in the campaign files.
- Keep the spec local-first and safe.
- Do not implement anything.
- Do not introduce live trading, paper trading, broker calls, destructive cleanup, deployment, PR creation, or auto-merge.
- Make validation commands explicit and safe for this phase.
- Require explicit staging only; forbid `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, and force push.
- Output markdown only.
"""


def executor_prompt(phase: dict[str, Any], spec_text: str, phase_dir: Path) -> str:
    return f"""You are Codex running as the executor for Frontier Workflow 2.

Execute exactly the generated phase spec below for {phase_label(phase)}. Do not broaden scope.

Safety rules:
- Do not perform live trading, paper trading, broker operations, order routing, production deployment, PR creation, auto-merge, or destructive cleanup.
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


def review_prompt(
    phase: dict[str, Any],
    campaign_id: str,
    spec_text: str,
    executor_text: str,
    validation_text: str,
) -> str:
    return f"""You are Claude reviewing one Frontier Workflow 2 phase.

Review phase {phase_label(phase)} against:
- AGENTS.md
- CLAUDE.md
- frontier.yaml
- campaigns/{campaign_id} files
- the generated phase spec
- executor output
- validation output

Return markdown. Include exactly one verdict line using one of:
VERDICT: PASS
VERDICT: PASS_WITH_WARNINGS
VERDICT: REWORK
VERDICT: BLOCKED

Be conservative. Block broker/live/paper scope, destructive operations, hidden failed runs, test weakening, artifact policy violations, unsupported claims, and scope drift.

Generated spec:

{spec_text}

Executor output:

{executor_text}

Validation output:

{validation_text}
"""


def done_check_prompt(
    phase: dict[str, Any],
    campaign_id: str,
    spec_text: str,
    executor_text: str,
    validation_text: str,
    review_text: str,
    verdict: str,
    handoff_text: str,
) -> str:
    return f"""You are Claude performing a semantic done-check for one Frontier Workflow 2 phase.

Compare:
- AGENTS.md
- frontier.yaml
- campaigns/{campaign_id} files
- generated phase spec
- changed files and executor output
- validation output
- review output and verdict
- handoff

Return markdown. Include exactly one done-check line using one of:
DONE_CHECK: PASS
DONE_CHECK: PASS_WITH_WARNINGS
DONE_CHECK: REWORK
DONE_CHECK: BLOCKED

Be conservative. Require rework for missed phase requirements, incomplete validation, scope drift, or unsupported handoff claims. Block broker/live/paper scope, destructive operations, hidden failed runs, and unsafe automation.

Phase: {phase_label(phase)}
Review verdict: {verdict}

Generated spec:

{spec_text}

Executor output:

{executor_text}

Validation output:

{validation_text}

Review output:

{review_text}

Handoff:

{handoff_text}
"""


def campaign_done_check_prompt(campaign_id: str, state: dict[str, Any], run_summary: str) -> str:
    phase_lines = "\n".join(f"- {phase['phase_id']}: {phase['status']}" for phase in state.get("phases", []))
    return f"""You are Claude performing the final semantic campaign done-check for Frontier Workflow 2.

Compare:
- campaigns/{campaign_id}/GOAL.md
- campaigns/{campaign_id}/ACCEPTANCE.md
- campaigns/{campaign_id}/PHASE_PLAN.md
- all phase verdicts and done-checks
- RUN_SUMMARY.md
- docs/PROJECT_STATUS or PROGRESS if present

Return markdown. Include exactly one done-check line using one of:
DONE_CHECK: PASS
DONE_CHECK: PASS_WITH_WARNINGS
DONE_CHECK: REWORK
DONE_CHECK: BLOCKED

Campaign: {campaign_id}

Phase statuses:

{phase_lines}

Current RUN_SUMMARY:

{run_summary}
"""


def repair_prompt(phase: dict[str, Any], spec_text: str, review_text: str, validation_text: str) -> str:
    return f"""You are Codex performing one bounded repair attempt for Frontier Workflow 2.

Repair only valid in-scope findings for {phase_label(phase)}. Do not broaden scope.

Safety rules:
- Do not perform live trading, paper trading, broker operations, order routing, production deployment, PR creation, auto-merge, or destructive cleanup.
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
- Live trading, paper trading, broker operations, order routing, deployment, PR creation, auto-merge, or destructive cleanup.

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


def mock_done_check_text(phase: dict[str, Any]) -> str:
    return (
        f"# Mock Done Check: {phase['phase_id']}\n\n"
        "Deterministic mock-provider artifacts satisfy the mock phase contract.\n\n"
        "DONE_CHECK: PASS\n"
    )


def mock_campaign_done_check_text(campaign_id: str) -> str:
    return (
        f"# Mock Campaign Done Check: {campaign_id}\n\n"
        "All executed mock-provider phases reached a passing terminal status.\n\n"
        "DONE_CHECK: PASS\n"
    )


def provider_handoff_text(phase: dict[str, Any], verdict: str, mock_enabled: bool) -> str:
    mode = "mock-provider" if mock_enabled else "provider-wired"
    automation = (
        "Mock mode did not perform GitHub, PR, merge, deployment, broker, paper, or live trading operations."
        if mock_enabled
        else "GitHub PR, CI, and merge-gate automation may run only when frontier.yaml lane policy and local CLI auth allow it."
    )
    return f"""# {phase['phase_id']} Handoff

## Scope Completed

- Ran the Workflow 2 conductor for `{phase['phase_id']}` in {mode} mode.
- Wrote required run artifacts under `runs/<run_id>/phases/{phase['phase_id']}/`.
- Recorded review verdict `{verdict}`.

## Safety

- {automation}

## Validation

- Validation output is recorded in `validation.md`.
"""


def claude_headless(prompt: str, *, root: Path = ROOT) -> CommandResult:
    config = load_provider_config(root)
    response = ClaudeProviderAdapter(config, CommandRunner(root)).run_prompt(prompt)
    return CommandResult(tuple(response.command), response.return_code, response.stdout, response.stderr)


def codex_noninteractive(prompt: str, *, root: Path = ROOT) -> CommandResult:
    config = load_provider_config(root)
    response = CodexProviderAdapter(config, CommandRunner(root)).run_prompt(prompt)
    return CommandResult(tuple(response.command), response.return_code, response.stdout, response.stderr)


def write_provider_failure(path: Path, title: str, result: CommandResult) -> None:
    path.write_text(f"# {title}\n\n{command_block(result)}\n", encoding="utf-8")


def run_validation_commands(*, root: Path = ROOT) -> tuple[bool, str]:
    results = [
        run_local_command(["just", "frontier-doctor"], root=root),
        run_local_command(["just", "verify-canaries"], root=root),
    ]
    ok = all(result.returncode == 0 for result in results)
    body = ["# Validation", ""]
    for result in results:
        body.append(command_block(result))
    return ok, "\n".join(body)


def run_phase_validation(root: Path) -> tuple[bool, str]:
    try:
        return run_validation_commands(root=root)
    except TypeError:
        return run_validation_commands()


def parse_review_verdict(text: str) -> str:
    return parse_review_text(text).verdict


def write_provider_verdict(
    phase_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    source: str,
    parsed: ReviewVerdict | None = None,
) -> None:
    findings = parsed.findings if parsed else []
    required_repairs = parsed.required_repairs if parsed else []
    warnings = parsed.warnings if parsed else []
    severity = parsed.severity if parsed else ("critical" if verdict == "BLOCKED" else "none")
    write_json(
        phase_dir / "verdict.json",
        {
            "schema_version": "frontier-review-verdict-v1",
            "campaign_id": state["campaign_id"],
            "run_id": state["run_id"],
            "phase_id": phase["phase_id"],
            "verdict": verdict,
            "severity": severity,
            "findings": findings,
            "required_repairs": required_repairs,
            "warnings": warnings,
            "raw_review_path": parsed.raw_review_path if parsed else None,
            "source": source,
            "mock_providers": state.get("mock_providers", False),
            "external_providers_called": state.get("external_providers_called", False),
            "network_used": state.get("network_used", False),
            "auto_merge_performed": False,
            "parsed_at": utc_now(),
        },
    )


def write_done_check_result(
    phase_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    text: str,
) -> str:
    path = phase_dir / "done_check.md"
    path.write_text(text, encoding="utf-8")
    parsed = parse_done_check_text(text, path)
    write_json(
        phase_dir / "done_check.json",
        {
            "schema_version": "frontier-done-check-v1",
            "campaign_id": state["campaign_id"],
            "run_id": state["run_id"],
            "phase_id": phase["phase_id"],
            "verdict": parsed.verdict,
            "findings": parsed.findings,
            "warnings": parsed.warnings,
            "raw_path": parsed.raw_path,
            "mock_providers": state.get("mock_providers", False),
            "parsed_at": utc_now(),
        },
    )
    return parsed.verdict


def phase_required_checks(phase: dict[str, Any], config: dict[str, Any]) -> list[str]:
    github = config.get("github") if isinstance(config.get("github"), dict) else {}
    checks = github.get("required_checks") or []
    return [str(check) for check in checks if check]


def max_repair_attempts_for_phase(state: dict[str, Any], phase: dict[str, Any]) -> int:
    override = os.environ.get("FRONTIER_MAX_REPAIR_ATTEMPTS")
    if override:
        return parse_positive_int(override, "FRONTIER_MAX_REPAIR_ATTEMPTS")
    lane = str(phase.get("lane") or "green").lower()
    policy = state.get("lane_policy_snapshot", {}).get(lane, {})
    if isinstance(policy, dict) and policy.get("max_repair_attempts") is not None:
        return parse_positive_int(policy["max_repair_attempts"], f"lanes.{lane}.max_repair_attempts")
    return parse_positive_int(state.get("max_repair_attempts", DEFAULT_MAX_REPAIR_ATTEMPTS), "max_repair_attempts")


def pr_body_text(
    run_dir: Path,
    phase_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    merge_gate_summary: str,
) -> str:
    validation = (phase_dir / "validation.md").read_text(encoding="utf-8") if (phase_dir / "validation.md").exists() else ""
    review = (phase_dir / "review.md").read_text(encoding="utf-8") if (phase_dir / "review.md").exists() else ""
    handoff = phase_dir / "handoff.md"
    return f"""## Phase Summary

- Campaign: `{state['campaign_id']}`
- Phase: `{phase['phase_id']}`
- Run: `{state['run_id']}`
- Verdict: `{verdict}`

## Validation Summary

Validation artifacts are in `{phase_dir.relative_to(ROOT)}/validation.md`.

```text
{validation[:2000]}
```

## Review Verdict

```text
{review[:2000]}
```

## Merge Gate Summary

{merge_gate_summary}

## Handoff

`{handoff.relative_to(ROOT)}`

## Run Artifacts

- `{run_dir.relative_to(ROOT)}/RUN_SUMMARY.md`
- `{phase_dir.relative_to(ROOT)}/verdict.json`
- `{phase_dir.relative_to(ROOT)}/done_check.json`
- `{phase_dir.relative_to(ROOT)}/ci_status.json`
- `{phase_dir.relative_to(ROOT)}/merge_gate.json`

## Non-Runs

- No live trading, paper trading, broker operation, or production deployment is part of this generic harness.

## Limitations

- Provider execution uses local Claude/Codex CLIs; no direct API keys are handled by the harness.
- Real merge remains gated by frontier.yaml, CI, branch protection validation, and local `gh` authentication.
"""


def phase_auto_pr_allowed(config: dict[str, Any], phase: dict[str, Any]) -> bool:
    workflow2 = config.get("workflow2") if isinstance(config.get("workflow2"), dict) else {}
    git_config = config.get("git") if isinstance(config.get("git"), dict) else {}
    lane = str(phase.get("lane") or "green").lower()
    lanes = config.get("lanes") if isinstance(config.get("lanes"), dict) else {}
    lane_policy = lanes.get(lane, {}) if isinstance(lanes, dict) else {}
    return bool(workflow2.get("auto_pr", workflow2.get("allow_auto_pr", True))) and bool(
        git_config.get("auto_create_pr", True)
    ) and bool(lane_policy.get("auto_pr", False))


def write_github_result(path: Path, result: Any) -> None:
    if hasattr(result, "to_dict"):
        data = result.to_dict()
    else:
        data = result
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def post_phase_git_github(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    execution_root: Path = ROOT,
) -> bool:
    phase_dir = provider_phase_dir(run_dir, phase)
    config = load_config(ROOT / "frontier.yaml")
    lane = str(phase.get("lane") or "green").lower()
    branch = phase.get("branch") or phase_branch_name(state["campaign_id"], phase["phase_id"], phase.get("name"))
    mock_enabled = bool(state.get("mock_providers"))
    dry_git = mock_enabled and os.environ.get("FRONTIER_MOCK_COMMIT") != "1"
    push_enabled = not mock_enabled and os.environ.get("FRONTIER_PUSH", "1") != "0"

    git_result = commit_phase_changes(
        root=execution_root,
        campaign_id=state["campaign_id"],
        phase_id=phase["phase_id"],
        summary=phase.get("name") or phase["phase_id"],
        branch=branch,
        config=config,
        dry_run=dry_git,
        push=push_enabled,
    )
    write_git_phase_artifacts(phase_dir, git_result)
    phase["branch"] = branch
    phase["commit_sha"] = git_result.commit_sha
    append_event(run_dir, state, "GIT_PHASE_RECORDED", phase_id=phase["phase_id"], dry_run=git_result.dry_run)

    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    project_config = config.get("project") if isinstance(config.get("project"), dict) else {}
    required_checks = phase_required_checks(phase, config)
    ci_status = CI_SUCCESS if mock_enabled else "NOT_FOUND"
    pr_number: str | int | None = None
    pr_result = None
    pr_dry_run = mock_enabled or os.environ.get("FRONTIER_CREATE_PR") == "0" or not phase_auto_pr_allowed(config, phase)
    if os.environ.get("FRONTIER_CREATE_PR") == "1":
        pr_dry_run = False
    if phase_auto_pr_allowed(config, phase) or os.environ.get("FRONTIER_CREATE_PR") == "1":
        state["github_operations_performed"] = True
        base = str(project_config.get("default_branch") or "main") if mock_enabled else detect_default_branch(root=execution_root)
        title = f"{state['campaign_id']}/{phase['phase_id']}: {phase.get('name') or phase['phase_id']}"
        provisional_gate = f"Merge gate will be evaluated after PR/CI. Verdict: {verdict}."
        body = pr_body_text(run_dir, phase_dir, state, phase, verdict, provisional_gate)
        pr_result = create_pr(title=title, body=body, base=base, head=branch, root=execution_root, dry_run=pr_dry_run)
        write_github_result(phase_dir / "pr_create.json", pr_result)
        if pr_result.ok and not pr_result.dry_run:
            state["prs_created"] = True
            pr_meta = pr_result.metadata.get("pr") if isinstance(pr_result.metadata, dict) else {}
            pr_number = pr_result.metadata.get("number") or (pr_meta or {}).get("number")
            phase["pr_number"] = pr_number
        elif pr_result.blocked:
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="pr_create_blocked")
            block_provider_run(run_dir, state, phase, "BLOCKED", "PR_CREATE_BLOCKED: " + (pr_result.instructions or pr_result.stderr))
            return False

    if pr_number is not None and not mock_enabled:
        ci_result = wait_for_ci(
            pr_number,
            timeout_seconds=int(github_config.get("ci_timeout_seconds", 900)),
            poll_seconds=int(github_config.get("ci_poll_seconds", 15)),
            required_checks=required_checks,
            root=execution_root,
        )
    elif mock_enabled:
        ci_result = classify_ci_checks(
            [{"name": check or "mock-ci", "state": "COMPLETED", "conclusion": "success"} for check in (required_checks or ["mock-ci"])],
            required_checks=required_checks,
        )
    else:
        ci_result = classify_ci_checks([], required_checks=required_checks)
    ci_status = ci_result.state
    write_ci_status_artifacts(phase_dir, ci_result)
    phase["ci_status"] = ci_status
    if github_config.get("require_ci", True) and ci_status != CI_SUCCESS:
        block_provider_run(run_dir, state, phase, "BLOCKED", f"CI status was {ci_status}.")
        return False

    base_branch = str(project_config.get("default_branch") or "main") if mock_enabled else detect_default_branch(root=execution_root)
    merge_dry_run = mock_enabled or os.environ.get("FRONTIER_MERGE_DRY_RUN") == "1"
    bp_result = inspect_branch_protection(
        branch=base_branch,
        required_checks=required_checks,
        require_branch_protection=bool(github_config.get("require_branch_protection", True)),
        root=execution_root,
        dry_run=merge_dry_run and bool(github_config.get("allow_unprotected_dry_run", True)),
    )
    write_branch_protection_artifacts(phase_dir, bp_result)

    critical = []
    verdict_path = phase_dir / "verdict.json"
    if verdict_path.exists():
        verdict_data = read_json(verdict_path)
        if verdict_data.get("severity") == "critical":
            critical = list(verdict_data.get("findings", []))
    merge_changed_files = [] if dry_git else git_result.changed_files
    gate = evaluate_merge_gate(
        campaign_id=state["campaign_id"],
        phase_id=phase["phase_id"],
        lane=lane,
        verdict=verdict,
        ci_status=ci_status,
        changed_files=merge_changed_files,
        artifact_policy={"ok": dry_git or not git_result.blocked_files, "blocked_files": git_result.blocked_files},
        config=config,
        env=os.environ,
        dry_run=merge_dry_run or pr_number is None,
        branch_protection=bp_result,
        critical_findings=critical,
        stop_requested=stop_requested(run_dir),
    )
    write_merge_gate_artifacts(phase_dir, gate)
    phase["merge_gate_status"] = gate.status
    if gate.status not in PASSING_VERDICTS:
        block_provider_run(run_dir, state, phase, "BLOCKED", "Merge gate blocked: " + "; ".join(gate.reasons))
        return False
    if pr_number is not None:
        merge_result = perform_merge(pr_number=pr_number, gate=gate, root=execution_root)
        write_github_result(phase_dir / "merge_result.json", merge_result)
        if merge_result.ok and not merge_result.dry_run:
            state["auto_merge_performed"] = True
            append_event(run_dir, state, "PR_MERGED", phase_id=phase["phase_id"], pr_number=pr_number)
        elif merge_result.blocked and gate.merge_allowed:
            block_provider_run(run_dir, state, phase, "BLOCKED", merge_result.instructions or merge_result.stderr)
            return False
    return True


def _read_phase_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def execute_provider_phase(run_dir: Path, state: dict[str, Any], phase: dict[str, Any]) -> bool:
    mock_enabled = bool(state.get("mock_providers"))
    phase_id = phase["phase_id"]
    phase_dir = provider_phase_dir(run_dir, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)
    execution_root = ROOT

    if state.get("worktree_mode"):
        manager = WorktreeManager(ROOT, runtime_config().worktree_root)
        plan = manager.create(state["campaign_id"], phase_id, phase.get("name"), dry_run=mock_enabled)
        phase["branch"] = plan.branch
        phase["worktree_path"] = plan.path
        if not mock_enabled:
            execution_root = Path(plan.path)
        (phase_dir / "worktree_plan.json").write_text(
            json.dumps(plan.__dict__, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        append_event(run_dir, state, "WORKTREE_PLAN", phase_id=phase_id, branch=plan.branch, path=plan.path)

    reason = check_run_budget(run_dir, state)
    if reason:
        block_provider_run(run_dir, state, phase, "BLOCKED", reason)
        return False

    status = phase.get("status", "PENDING")
    if status == "PENDING":
        state["status"] = "RUNNING"
        state["current_phase_id"] = phase_id
        state["current_micro_attempt"] = 1
        state.setdefault("attempts", {})
        state["attempts"][phase_id] = int(state["attempts"].get(phase_id, 0)) + 1
        phase["started_at"] = utc_now()
        append_event(run_dir, state, "PHASE_SELECT", phase_id=phase_id)
        write_state(run_dir, state)
        progress(run_dir, f"Selected {phase_id}.")
    else:
        append_event(run_dir, state, "PHASE_RESUME", phase_id=phase_id, status=status)

    if phase.get("status") == "PENDING":
        if stop_requested(run_dir):
            block_provider_run(run_dir, state, phase, "BLOCKED", "STOP file exists before spec generation.")
            return False
        spec_prompt_text = spec_generation_prompt(phase, state["campaign_id"])
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
        write_provider_summary(run_dir, state, f"{phase_id} spec ready.")
    else:
        spec_text = _read_phase_text(phase_dir / "spec.md")

    if phase.get("status") == "SPEC_READY":
        if stop_requested(run_dir):
            block_provider_run(run_dir, state, phase, "BLOCKED", "STOP file exists before execution.")
            return False
        phase_reason = check_phase_budget(phase)
        if phase_reason:
            block_provider_run(run_dir, state, phase, "BLOCKED", phase_reason)
            return False
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
            result = codex_noninteractive(exec_prompt_text, root=execution_root)
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
        write_provider_summary(run_dir, state, f"{phase_id} executed.")
    else:
        executor_text = _read_phase_text(phase_dir / "executor_output.md")

    if phase.get("status") in {"EXECUTED", "REPAIRED"}:
        if stop_requested(run_dir):
            block_provider_run(run_dir, state, phase, "BLOCKED", "STOP file exists before validation.")
            return False
        validation_ok, validation_text = run_phase_validation(execution_root)
        (phase_dir / "validation.md").write_text(validation_text, encoding="utf-8")
        if not validation_ok:
            write_provider_verdict(phase_dir, state, phase, "REWORK", source="validation")
            set_provider_phase_status(phase, "REWORK")
            verdict = run_provider_repair_loop(
                run_dir,
                state,
                phase,
                spec_text,
                "Validation failed before Claude review.",
                validation_text,
                execution_root=execution_root,
            )
            if verdict not in PASSING_VERDICTS:
                block_provider_run(run_dir, state, phase, "BLOCKED", "Repair attempts exhausted after validation failure.")
                return False
        else:
            set_provider_phase_status(phase, "VALIDATED")
            append_event(run_dir, state, "VALIDATED", phase_id=phase_id)
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, f"{phase_id} validated.")
    validation_text = _read_phase_text(phase_dir / "validation.md")

    if phase.get("status") == "VALIDATED":
        if stop_requested(run_dir):
            block_provider_run(run_dir, state, phase, "BLOCKED", "STOP file exists before review.")
            return False
        review_prompt_text = review_prompt(
            phase,
            state["campaign_id"],
            spec_text,
            executor_text,
            validation_text,
        )
        (phase_dir / "review_prompt.md").write_text(review_prompt_text, encoding="utf-8")
        if mock_enabled:
            review_text = mock_review_text(phase)
            append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_review")
        else:
            append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="phase_review")
            result = claude_headless(review_prompt_text, root=execution_root)
            review_text = result.stdout if result.returncode == 0 else command_block(result)
            if result.returncode != 0:
                (phase_dir / "review.md").write_text(review_text, encoding="utf-8")
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="claude_review_error")
                block_provider_run(run_dir, state, phase, "BLOCKED", "Claude review returned nonzero.")
                return False
        review_path = phase_dir / "review.md"
        review_path.write_text(review_text, encoding="utf-8")
        parsed_verdict = parse_review_text(review_text, review_path)
        verdict = parsed_verdict.verdict
        write_provider_verdict(phase_dir, state, phase, verdict, source="review", parsed=parsed_verdict)
        set_provider_phase_status(phase, "REVIEWED")
        append_event(run_dir, state, "REVIEWED", phase_id=phase_id, verdict=verdict)
        write_state(run_dir, state)
        write_provider_summary(run_dir, state, f"{phase_id} reviewed with {verdict}.")
    else:
        review_text = _read_phase_text(phase_dir / "review.md")
        verdict = read_json(phase_dir / "verdict.json").get("verdict", "BLOCKED") if (phase_dir / "verdict.json").exists() else "BLOCKED"

    if verdict == "REWORK" or phase.get("status") == "REWORK":
        verdict = run_provider_repair_loop(
            run_dir, state, phase, spec_text, review_text, validation_text, execution_root=execution_root
        )
    if verdict not in PASSING_VERDICTS:
        block_provider_run(run_dir, state, phase, "BLOCKED", f"Review verdict was {verdict}.")
        return False

    handoff_text = provider_handoff_text(phase, verdict, mock_enabled)
    (phase_dir / "handoff.md").write_text(handoff_text, encoding="utf-8")
    workflow2 = runtime_config().raw.get("workflow2", {})
    if not isinstance(workflow2, dict) or bool(workflow2.get("semantic_done_check_required", True)):
        if stop_requested(run_dir):
            block_provider_run(run_dir, state, phase, "BLOCKED", "STOP file exists before done-check.")
            return False
        done_prompt = done_check_prompt(
            phase,
            state["campaign_id"],
            spec_text,
            executor_text,
            validation_text,
            review_text,
            verdict,
            handoff_text,
        )
        (phase_dir / "done_check_prompt.md").write_text(done_prompt, encoding="utf-8")
        if mock_enabled:
            done_text = mock_done_check_text(phase)
            append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_done_check")
        else:
            append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="phase_done_check")
            result = claude_headless(done_prompt, root=execution_root)
            done_text = result.stdout if result.returncode == 0 else command_block(result)
            if result.returncode != 0:
                (phase_dir / "done_check.md").write_text(done_text, encoding="utf-8")
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="done_check_error")
                block_provider_run(run_dir, state, phase, "BLOCKED", "Claude done-check returned nonzero.")
                return False
        done_verdict = write_done_check_result(phase_dir, state, phase, done_text)
        append_event(run_dir, state, "DONE_CHECK", phase_id=phase_id, verdict=done_verdict)
        if done_verdict == "REWORK":
            verdict = run_provider_repair_loop(
                run_dir, state, phase, spec_text, done_text, validation_text, execution_root=execution_root
            )
            if verdict not in PASSING_VERDICTS:
                block_provider_run(run_dir, state, phase, "BLOCKED", "Repair attempts exhausted after done-check.")
                return False
        elif done_verdict == "BLOCKED":
            block_provider_run(run_dir, state, phase, "BLOCKED", "Done-check returned BLOCKED.")
            return False
        elif done_verdict == "PASS_WITH_WARNINGS" and verdict == "PASS":
            verdict = "PASS_WITH_WARNINGS"
            write_provider_verdict(phase_dir, state, phase, verdict, source="done_check_warning")

    if not post_phase_git_github(run_dir, state, phase, verdict, execution_root=execution_root):
        return False
    finish_provider_phase(run_dir, state, phase, verdict, event="PHASE_PASS")
    return True


def run_provider_repair_loop(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    spec_text: str,
    review_text: str,
    validation_text: str,
    *,
    execution_root: Path = ROOT,
) -> str:
    phase_id = phase["phase_id"]
    phase_dir = provider_phase_dir(run_dir, phase)
    mock_enabled = bool(state.get("mock_providers"))
    max_attempts = max_repair_attempts_for_phase(state, phase)
    state.setdefault("repair_attempts", {})
    start_attempt = int(state["repair_attempts"].get(phase_id, 0))
    current_review_text = review_text
    current_validation_text = validation_text

    for attempt in range(start_attempt + 1, max_attempts + 1):
        if stop_requested(run_dir):
            write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_stop")
            return "BLOCKED"
        state["repair_attempts"][phase_id] = attempt
        state["current_micro_attempt"] = attempt + 1
        set_provider_phase_status(phase, "REWORK")
        attempt_dir = phase_dir / "repair_attempts" / f"{attempt:03d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        repair_prompt_text = repair_prompt(phase, spec_text, current_review_text, current_validation_text)
        (attempt_dir / "repair_prompt.md").write_text(repair_prompt_text, encoding="utf-8")
        (phase_dir / "repair_prompt.md").write_text(repair_prompt_text, encoding="utf-8")
        append_event(run_dir, state, "REPAIR_START", phase_id=phase_id, attempt=attempt)
        write_state(run_dir, state)

        if mock_enabled:
            repair_text = f"# Mock Repair Output: {phase_id}\n\nMock repair attempt {attempt} completed.\n"
            append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_codex_repair")
        else:
            state["codex_called_by_driver"] = True
            state["external_providers_called"] = True
            state["network_used"] = True
            append_cost_record(run_dir, state, provider="codex", model=None, phase_id=phase_id, note="repair_execution")
            result = codex_noninteractive(repair_prompt_text, root=execution_root)
            repair_text = command_block(result)
            if result.returncode != 0:
                (attempt_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")
                (phase_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_error")
                return "BLOCKED"
        (attempt_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")
        (phase_dir / "repair_output.md").write_text(repair_text, encoding="utf-8")

        validation_ok, repair_validation_text = run_phase_validation(execution_root)
        (attempt_dir / "repair_validation.md").write_text(repair_validation_text, encoding="utf-8")
        (phase_dir / "repair_validation.md").write_text(repair_validation_text, encoding="utf-8")
        if not validation_ok:
            write_json(
                attempt_dir / "repair_verdict.json",
                {
                    "verdict": "REWORK",
                    "source": "repair_validation",
                    "attempt": attempt,
                    "parsed_at": utc_now(),
                },
            )
            current_validation_text = repair_validation_text
            append_event(run_dir, state, "REPAIR_VALIDATION_REWORK", phase_id=phase_id, attempt=attempt)
            continue

        review_prompt_text = review_prompt(
            phase,
            state["campaign_id"],
            spec_text,
            repair_text,
            repair_validation_text,
        )
        (attempt_dir / "repair_review_prompt.md").write_text(review_prompt_text, encoding="utf-8")
        if mock_enabled:
            repaired_review_text = mock_review_text(phase)
            append_cost_record(run_dir, state, provider="mock", model=None, phase_id=phase_id, note="mock_claude_repair_review")
        else:
            append_cost_record(run_dir, state, provider="claude", model=None, phase_id=phase_id, note="repair_review")
            result = claude_headless(review_prompt_text, root=execution_root)
            repaired_review_text = result.stdout if result.returncode == 0 else command_block(result)
            if result.returncode != 0:
                (attempt_dir / "repair_review.md").write_text(repaired_review_text, encoding="utf-8")
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_review_error")
                return "BLOCKED"
        review_path = attempt_dir / "repair_review.md"
        review_path.write_text(repaired_review_text, encoding="utf-8")
        (phase_dir / "review.md").write_text(repaired_review_text, encoding="utf-8")
        parsed_verdict = parse_review_text(repaired_review_text, review_path)
        verdict = parsed_verdict.verdict
        write_json(
            attempt_dir / "repair_verdict.json",
            {
                **parsed_verdict.to_dict(),
                "campaign_id": state["campaign_id"],
                "run_id": state["run_id"],
                "phase_id": phase_id,
                "attempt": attempt,
                "parsed_at": utc_now(),
            },
        )
        write_provider_verdict(phase_dir, state, phase, verdict, source="repair_review", parsed=parsed_verdict)
        append_event(run_dir, state, "REPAIR_REVIEWED", phase_id=phase_id, attempt=attempt, verdict=verdict)
        write_state(run_dir, state)
        current_review_text = repaired_review_text
        current_validation_text = repair_validation_text
        if verdict in PASSING_VERDICTS:
            set_provider_phase_status(phase, "REVIEWED")
            return verdict

    write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="repair_exhausted")
    append_event(run_dir, state, "REPAIR_EXHAUSTED", phase_id=phase_id, max_attempts=max_attempts)
    write_state(run_dir, state)
    return "BLOCKED"


def run_campaign_done_check(run_dir: Path, state: dict[str, Any]) -> str:
    mock_enabled = bool(state.get("mock_providers"))
    run_summary = _read_phase_text(run_dir / "RUN_SUMMARY.md")
    prompt = campaign_done_check_prompt(state["campaign_id"], state, run_summary)
    (run_dir / "campaign_done_check_prompt.md").write_text(prompt, encoding="utf-8")
    if mock_enabled:
        text = mock_campaign_done_check_text(state["campaign_id"])
        append_cost_record(run_dir, state, provider="mock", model=None, phase_id=None, note="mock_campaign_done_check")
    else:
        append_cost_record(run_dir, state, provider="claude", model=None, phase_id=None, note="campaign_done_check")
        result = claude_headless(prompt)
        text = result.stdout if result.returncode == 0 else command_block(result)
        if result.returncode != 0:
            text = text + "\n\nDONE_CHECK: BLOCKED\n"
    path = run_dir / "campaign_done_check.md"
    path.write_text(text, encoding="utf-8")
    parsed = parse_done_check_text(text, path)
    write_json(
        run_dir / "campaign_done_check.json",
        {
            "schema_version": "frontier-campaign-done-check-v1",
            "campaign_id": state["campaign_id"],
            "run_id": state["run_id"],
            "verdict": parsed.verdict,
            "findings": parsed.findings,
            "warnings": parsed.warnings,
            "raw_path": parsed.raw_path,
            "mock_providers": mock_enabled,
            "parsed_at": utc_now(),
        },
    )
    append_event(run_dir, state, "CAMPAIGN_DONE_CHECK", verdict=parsed.verdict)
    return parsed.verdict


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
    state.setdefault("provider_mode", "mock" if state.get("mock_providers") else "external")
    state.setdefault("attempts", {phase.get("phase_id"): 0 for phase in state.get("phases", [])})
    state.setdefault("repair_attempts", {phase.get("phase_id"): 0 for phase in state.get("phases", [])})
    state.setdefault("lane_policy_snapshot", runtime_config().lane_policies)
    state.setdefault("estimated_cost_usd", 0.0)
    executed = 0

    while True:
        if (run_dir / "STOP").exists():
            return provider_stop_without_execution(run_dir, state, "STOP file exists before next phase.")
        budget_reason = check_run_budget(run_dir, state)
        if budget_reason:
            state["status"] = "STOPPED"
            state["stop_requested"] = True
            append_event(run_dir, state, "RUN_BUDGET_STOP", reason=budget_reason)
            write_provider_stop(run_dir, state, budget_reason)
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, budget_reason)
            print(f"Stopped provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
            return 0

        phase = next_pending_provider_phase(state)
        if phase is None:
            done_verdict = run_campaign_done_check(run_dir, state)
            if done_verdict not in PASSING_VERDICTS:
                state["status"] = "BLOCKED"
                state["stop_requested"] = True
                write_provider_stop(run_dir, state, f"Campaign done-check returned {done_verdict}.")
                write_state(run_dir, state)
                write_provider_summary(run_dir, state, f"Campaign done-check returned {done_verdict}.")
                print(f"Campaign done-check blocked run at {run_dir.relative_to(ROOT)}")
                return 0
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


def run_provider_wired_campaign(
    campaign_id: str,
    max_phases: int | None,
    *,
    worktree_mode: bool | None = None,
) -> int:
    try:
        campaign = load_ledger_campaign(campaign_id)
        resolved_max_phases, source = resolve_max_phases(campaign, max_phases)
        run_dir = initialize_provider_wired_run(
            campaign,
            resolved_max_phases,
            source,
            worktree_mode=worktree_mode,
        )
        state = read_json(run_dir / "state.json")
        with run_lock(run_dir):
            return continue_provider_wired_run(run_dir, state, resolved_max_phases, source)
    except RuntimeError as error:
        print(error)
        return 1
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
        "- Auto-merge: not exercised by the local toy path\n"
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
        "driver": SCAFFOLD_DRIVER,
        "status": "RUNNING",
        "current_phase_id": None,
        "current_micro_attempt": 0,
        "lane": lane,
        "phases": [],
        "stop_requested": False,
        "created_at": utc_now(),
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "attempts": {},
        "provider_mode": "none",
        "lane_policy_snapshot": runtime_config().lane_policies,
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
    (run_dir / "prd.json").write_text(
        json.dumps({"goal": goal, "campaign_id": campaign_id}, indent=2) + "\n",
        encoding="utf-8",
    )
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
    worktree_mode: bool | None = None,
) -> int:
    if ledger_only:
        if not campaign_id:
            print("Ledger-only mode requires --campaign-id.")
            return 2
        return run_ledger_only_campaign(campaign_id)
    if provider_wired:
        if not campaign_id:
            print("Provider-wired mode requires --campaign-id.")
            return 2
        return run_provider_wired_campaign(campaign_id, max_phases, worktree_mode=worktree_mode)
    if campaign_id == TOY_CAMPAIGN_ID:
        return run_toy_campaign(campaign_id)

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


def resume_provider_wired_run(
    run_dir: Path,
    state: dict[str, Any],
    max_phases: int | None,
    worktree_mode: bool | None = None,
) -> int:
    if state.get("status") == "COMPLETED":
        print(f"Run {state['run_id']} is already completed.")
        return 0
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
    state.setdefault("provider_mode", "mock" if state.get("mock_providers") else "external")
    state.setdefault("attempts", {phase.get("phase_id"): 0 for phase in state.get("phases", [])})
    state.setdefault("repair_attempts", {phase.get("phase_id"): 0 for phase in state.get("phases", [])})
    state.setdefault("lane_policy_snapshot", runtime_config().lane_policies)
    if worktree_mode is not None:
        state["worktree_mode"] = worktree_mode
    append_event(run_dir, state, "RUN_RESUME", mode="provider_wired", max_phases=resolved_max_phases)
    write_state(run_dir, state)
    progress(run_dir, "Provider-wired run resumed.")
    try:
        with run_lock(run_dir):
            return continue_provider_wired_run(run_dir, state, resolved_max_phases, source)
    except RuntimeError as error:
        print(error)
        return 1


def resume(
    run_id: str,
    *,
    provider_wired: bool = False,
    max_phases: int | None = None,
    worktree_mode: bool | None = None,
) -> int:
    run_dir = ROOT / "runs" / run_id
    state_path = run_dir / "state.json"
    if not state_path.exists():
        print(f"Unknown run id: {run_id}")
        return 1

    state = read_json(state_path)
    if state.get("driver") == PROVIDER_WIRED_DRIVER or (
        provider_wired and state.get("provider_wired") is True
    ):
        return resume_provider_wired_run(run_dir, state, max_phases, worktree_mode)
    if state.get("driver") == LEDGER_ONLY_DRIVER:
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
    worktree_group = run_parser.add_mutually_exclusive_group()
    worktree_group.add_argument("--worktree-mode", action="store_true")
    worktree_group.add_argument("--no-worktree", action="store_true")
    resume_parser = subparsers.add_parser("resume", help="Resume a stopped toy run or inspect a scaffold run.")
    resume_parser.add_argument("--run-id", required=True)
    resume_parser.add_argument("--provider-wired", action="store_true")
    resume_parser.add_argument("--max-phases", type=int)
    resume_worktree_group = resume_parser.add_mutually_exclusive_group()
    resume_worktree_group.add_argument("--worktree-mode", action="store_true")
    resume_worktree_group.add_argument("--no-worktree", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_campaign(
            args.campaign_id,
            args.goal,
            args.lane,
            ledger_only=args.ledger_only,
            provider_wired=args.provider_wired,
            max_phases=args.max_phases,
            worktree_mode=True if args.worktree_mode else False if args.no_worktree else None,
        )
    if args.command == "resume":
        return resume(
            args.run_id,
            provider_wired=args.provider_wired,
            max_phases=args.max_phases,
            worktree_mode=True if args.worktree_mode else False if args.no_worktree else None,
        )
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
