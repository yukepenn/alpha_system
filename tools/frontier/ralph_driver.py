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
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.frontier.command_runner import CommandRunner
from tools.frontier.config import load_config
from tools.frontier.git_utils import (
    RemoteBranchResult,
    PushBranchResult,
    commit_phase_changes,
    git,
    local_commit_exists,
    prepare_phase_branch,
    push_phase_branch,
    resolve_base_ref,
    verify_remote_branch,
    write_branch_prepare_artifacts,
    write_git_phase_artifacts,
    write_push_branch_artifacts,
    write_remote_branch_artifacts,
)
from tools.frontier.github_utils import (
    ALREADY_MERGED,
    AUTO_MERGE_ARMED,
    CI_SUCCESS,
    GitHubResult,
    MERGE_EXECUTION_BLOCKED,
    MERGED,
    classify_ci_checks,
    create_pr,
    detect_default_branch,
    inspect_branch_protection,
    list_pr_diff_files,
    wait_for_ci,
    wait_pr_mergeable,
    view_pr,
    write_branch_protection_artifacts,
    write_ci_status_artifacts,
    write_pr_create_artifacts,
)
from tools.frontier.merge_gate import (
    critical_findings_for_gate,
    evaluate_merge_gate,
    perform_merge,
    write_merge_gate_artifacts,
)
from tools.frontier.artifact_policy import curate_commit_paths
from tools.frontier.provider_adapters import (
    WAITING_CLAUDE_LIMIT,
    WAITING_CODEX_LIMIT,
    WAITING_PROVIDER_LIMIT,
    ClaudeProviderAdapter,
    CodexProviderAdapter,
    classify_provider_nonzero,
)
from tools.frontier.provider_config import ProviderRuntimeConfig, load_provider_config
from tools.frontier.resume import (
    RESUME_PRECONDITION_FAILED,
    WORKFLOW2_STAGES,
    changed_files_from_artifacts,
    recover_pr_number,
    stage_index,
    summarize_resume_failure,
    validate_resume_preconditions,
)
from tools.frontier.verdict import ReviewVerdict, parse_done_check_text, parse_review_text
from tools.frontier.worktree_manager import WorktreeManager, phase_branch_name, worktree_mode_enabled
from tools.frontier import dag_scheduler
from tools.frontier.merge_queue import MERGE_READY, serial_merge_order

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
PROMPT_SECTION_MAX_CHARS = 24_000
GIT_PHASE_BLOCKED = "GIT_PHASE_BLOCKED"
PUSH_BLOCKED = "PUSH_BLOCKED"
REMOTE_BRANCH_BLOCKED = "REMOTE_BRANCH_BLOCKED"
PR_CREATE_BLOCKED = "PR_CREATE_BLOCKED"
CI_BLOCKED = "CI_BLOCKED"
MERGE_GATE_BLOCKED = "MERGE_GATE_BLOCKED"
MERGE_PENDING = "MERGE_PENDING"
GATE_BLOCKED_STATUSES = {
    PUSH_BLOCKED,
    REMOTE_BRANCH_BLOCKED,
    PR_CREATE_BLOCKED,
    CI_BLOCKED,
    MERGE_GATE_BLOCKED,
    MERGE_EXECUTION_BLOCKED,
}
MERGE_PENDING_STATUSES = {AUTO_MERGE_ARMED, MERGE_PENDING, MERGE_READY}
PROVIDER_WAITING_STATUSES = {WAITING_PROVIDER_LIMIT, WAITING_CLAUDE_LIMIT, WAITING_CODEX_LIMIT}
ACTIVE_CAMPAIGN_FILE = "ACTIVE_CAMPAIGN.md"
SCHEDULER_MODES = {"sequential", "dag_wave"}
PROVIDER_RESUME_STATUS_BY_STAGE = {
    "spec": "PENDING",
    "execute": "SPEC_READY",
    "validate": "EXECUTED",
    "review": "VALIDATED",
    "done_check": "REVIEWED",
    "repair": "REWORK",
}
FORBIDDEN_GIT_ADD_DOT = "git add" + " ."
FORBIDDEN_GIT_ADD_ALL = "git add" + " -A"

# Serializes run-level file writes (state.json, events.jsonl, costs.jsonl,
# RUN_SUMMARY.md, progress/heartbeat) so concurrent phase builds in a parallel
# wave never interleave a half-written JSON document or drop an event id. The
# lock is reentrant: a thread holding it may call nested guarded writers. In
# sequential runs it is always uncontended, so behaviour is unchanged.
_RUN_WRITE_LOCK = threading.RLock()

# Set True only while the parallel wave coordinator is driving a wave. When set,
# a single phase block records the phase outcome but does NOT stop the whole run
# or write the run STOP file; the coordinator collects per-phase outcomes and
# decides run-level status after the wave joins.
_PARALLEL_MODE_ACTIVE = False


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
    # Optional DAG-wave scheduler metadata. All default to the conservative
    # (sequential, run-alone) choice so campaigns that omit them are unchanged.
    parallel_safe: bool = False
    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    resource_class: tuple[str, ...] = ()
    must_run_alone: bool = False
    merge_group: str | None = None


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


def latest_campaign_run_dir(campaign_id: str, *, provider_wired_only: bool = False) -> Path | None:
    runs_root = ROOT / "runs"
    if not runs_root.exists():
        return None
    candidates: list[tuple[float, str, Path]] = []
    for run_dir in runs_root.glob(f"*_{campaign_id}*"):
        if not run_dir.is_dir():
            continue
        state_path = run_dir / "state.json"
        if not state_path.exists():
            continue
        try:
            state = read_json(state_path)
        except (OSError, json.JSONDecodeError):
            continue
        if state.get("campaign_id") != campaign_id:
            continue
        if state.get("status") == "COMPLETED":
            continue
        if provider_wired_only and not (
            state.get("driver") == PROVIDER_WIRED_DRIVER or state.get("provider_wired") is True
        ):
            continue
        candidates.append((state_path.stat().st_mtime, run_dir.name, run_dir))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


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


@dataclass(frozen=True)
class SchedulerSettings:
    """Resolved Workflow 2 scheduling policy for one run.

    ``sequential`` (default) preserves the historical list-order, one-phase loop.
    ``dag_wave`` selects phases by dependency-satisfied ready-set and, when
    parallel execution is armed, runs a conflict-free wave concurrently in
    isolated worktrees while merging serially.
    """

    mode: str = "sequential"
    max_parallel_phases: int = 1
    merge_queue: str = "serial"
    update_active_campaign: str = "phase_commit"
    parallel_execution: bool = False
    red_authorized: bool = False

    @property
    def is_dag_wave(self) -> bool:
        return self.mode == "dag_wave"

    @property
    def runs_parallel(self) -> bool:
        return self.is_dag_wave and self.parallel_execution and self.max_parallel_phases > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "max_parallel_phases": self.max_parallel_phases,
            "merge_queue": self.merge_queue,
            "update_active_campaign": self.update_active_campaign,
            "parallel_execution": self.parallel_execution,
            "red_authorized": self.red_authorized,
        }


def resolve_scheduler_config(
    campaign_yaml: dict[str, Any] | None,
    *,
    env: dict[str, str] | None = None,
) -> SchedulerSettings:
    """Resolve scheduler policy: frontier.yaml < campaign.yaml < environment.

    The block lives under ``workflow2.scheduler`` in both frontier.yaml and the
    campaign.yaml. Environment overrides (set by the ``--parallel`` CLI flag and
    friends) win last so a run can opt into parallelism without editing files.
    """

    env = env if env is not None else dict(os.environ)
    merged: dict[str, Any] = {}

    raw = runtime_config().raw
    wf2 = raw.get("workflow2") if isinstance(raw.get("workflow2"), dict) else {}
    if isinstance(wf2.get("scheduler"), dict):
        merged.update(wf2["scheduler"])
    if isinstance(campaign_yaml, dict):
        cwf2 = campaign_yaml.get("workflow2") if isinstance(campaign_yaml.get("workflow2"), dict) else {}
        if isinstance(cwf2.get("scheduler"), dict):
            merged.update(cwf2["scheduler"])

    mode = str(env.get("FRONTIER_SCHEDULER_MODE") or merged.get("mode") or "sequential").strip().lower()
    if mode not in SCHEDULER_MODES:
        mode = "sequential"

    raw_parallel = env.get("FRONTIER_MAX_PARALLEL_PHASES") or merged.get("max_parallel_phases") or 1
    try:
        max_parallel = max(1, int(raw_parallel))
    except (TypeError, ValueError):
        max_parallel = 1

    merge_queue = str(merged.get("merge_queue") or "serial").strip().lower() or "serial"
    parallel_exec = parse_phase_bool(merged.get("parallel_execution"))
    if env.get("FRONTIER_PARALLEL_EXECUTION") is not None and env.get("FRONTIER_PARALLEL_EXECUTION") != "":
        parallel_exec = parse_phase_bool(env.get("FRONTIER_PARALLEL_EXECUTION"))

    # The --parallel CLI flag arms dag_wave + concurrent execution in one switch.
    if parse_phase_bool(env.get("FRONTIER_PARALLEL")):
        mode = "dag_wave"
        parallel_exec = True
        if max_parallel < 2:
            max_parallel = max(2, int(merged.get("max_parallel_phases") or 0) or 3)

    red_authorized = parse_phase_bool(env.get("FRONTIER_RED_AUTHORIZED"))

    update_active = str(merged.get("update_active_campaign") or "").strip().lower()
    if update_active not in {"phase_commit", "coordinator_only"}:
        runs_parallel = mode == "dag_wave" and parallel_exec and max_parallel > 1
        update_active = "coordinator_only" if runs_parallel else "phase_commit"

    return SchedulerSettings(
        mode=mode,
        max_parallel_phases=max_parallel,
        merge_queue=merge_queue,
        update_active_campaign=update_active,
        parallel_execution=parallel_exec,
        red_authorized=red_authorized,
    )


def scheduler_settings_for_state(state: dict[str, Any]) -> SchedulerSettings:
    """Resolve scheduler settings for an in-flight run (campaign + env)."""

    campaign_id = state.get("campaign_id")
    campaign_yaml: dict[str, Any] = {}
    if campaign_id:
        try:
            campaign_yaml = load_ledger_campaign(str(campaign_id)).campaign_yaml
        except (ValueError, RuntimeError, OSError):
            campaign_yaml = {}
    settings = resolve_scheduler_config(campaign_yaml)
    state["scheduler"] = settings.to_dict()
    return settings


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
    with _RUN_WRITE_LOCK:
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


def unique_executor_notes_path(phase_dir: Path, source: Path) -> Path:
    target = phase_dir / f"executor_notes_{source.stem}{source.suffix}"
    counter = 2
    while target.exists():
        target = phase_dir / f"executor_notes_{source.stem}_{counter}{source.suffix}"
        counter += 1
    return target


def quarantine_executor_review_artifacts(
    phase_dir: Path,
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
) -> None:
    renamed: list[dict[str, str]] = []
    for name in ("review.md", "verdict.json"):
        path = phase_dir / name
        if not path.exists():
            continue
        target = unique_executor_notes_path(phase_dir, path)
        path.rename(target)
        renamed.append({"from": name, "to": target.name})
    if renamed:
        append_event(
            run_dir,
            state,
            "EXECUTOR_REVIEW_ARTIFACT_QUARANTINED",
            phase_id=phase["phase_id"],
            files=renamed,
        )


def state_snapshot_for_serialization(state: dict[str, Any]) -> dict[str, Any]:
    """A shallow snapshot safe to json.dump while worker threads mutate phases.

    In dag_wave parallel mode the build threads mutate EXISTING phase dicts
    (status, stage checkpoints) concurrently. ``dict(...)`` is a single CPython
    C-level copy with no thread-switch point, so copying the top-level state and
    each phase dict yields stable objects that json.dump can iterate without
    hitting "dictionary changed size during iteration". The phases list itself is
    fixed for a run's lifetime, so a shallow per-phase copy is sufficient.

    Worker threads also mutate the top-level ``attempts`` and ``repair_attempts``
    dicts (execute_provider_phase / run_provider_repair_loop) without holding
    _RUN_WRITE_LOCK, so those nested dicts are copied here too. Any future
    top-level nested mutable value mutated by workers MUST be added to this copy
    list — do not rely on the json encoder's GIL atomicity to hide the race.
    """

    snapshot = dict(state)
    for key in ("attempts", "repair_attempts"):
        value = state.get(key)
        if isinstance(value, dict):
            snapshot[key] = dict(value)
    phases = state.get("phases")
    if isinstance(phases, list):
        snapshot["phases"] = [dict(p) if isinstance(p, dict) else p for p in phases]
    return snapshot


def write_state(run_dir: Path, state: dict[str, Any]) -> None:
    with _RUN_WRITE_LOCK:
        state["updated_at"] = utc_now()
        write_json(run_dir / "state.json", state_snapshot_for_serialization(state))
        write_heartbeat(run_dir, state)


def progress(run_dir: Path, message: str) -> None:
    with _RUN_WRITE_LOCK:
        with (run_dir / "progress.txt").open("a", encoding="utf-8") as handle:
            handle.write(f"{utc_now()} {message}\n")


def write_heartbeat(run_dir: Path, state: dict[str, Any]) -> None:
    with _RUN_WRITE_LOCK:
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
            "FRONTIER_MAX_PHASE_MINUTES", workflow2.get("max_phase_minutes"), 1440
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


def parse_phase_str_list(raw: Any, *, campaign_id: str, phase_id: str, field: str) -> tuple[str, ...]:
    """Parse an optional list-of-strings phase field (allowed_paths, etc.)."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        cleaned = clean_text(raw)
        return (cleaned,) if cleaned else ()
    if not isinstance(raw, list):
        raise ValueError(f"Campaign {campaign_id} {field} for {phase_id} must be a list.")
    items: list[str] = []
    for item in raw:
        cleaned = clean_text(item)
        if cleaned:
            items.append(cleaned)
    return tuple(items)


def parse_phase_bool(raw: Any) -> bool:
    if raw is None:
        return False
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


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
                parallel_safe=parse_phase_bool(raw_phase.get("parallel_safe")),
                allowed_paths=parse_phase_str_list(
                    raw_phase.get("allowed_paths"),
                    campaign_id=campaign_id,
                    phase_id=phase_id,
                    field="allowed_paths",
                ),
                forbidden_paths=parse_phase_str_list(
                    raw_phase.get("forbidden_paths"),
                    campaign_id=campaign_id,
                    phase_id=phase_id,
                    field="forbidden_paths",
                ),
                conflicts_with=parse_phase_str_list(
                    raw_phase.get("conflicts_with"),
                    campaign_id=campaign_id,
                    phase_id=phase_id,
                    field="conflicts_with",
                ),
                resource_class=parse_phase_str_list(
                    raw_phase.get("resource_class"),
                    campaign_id=campaign_id,
                    phase_id=phase_id,
                    field="resource_class",
                ),
                must_run_alone=parse_phase_bool(raw_phase.get("must_run_alone")),
                merge_group=clean_text(raw_phase.get("merge_group")),
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
        unknown_conflicts = [c for c in phase.conflicts_with if c not in phase_ids]
        if unknown_conflicts:
            raise ValueError(
                f"Campaign {campaign_id} phase {phase.phase_id} declares unknown conflicts_with: "
                f"{', '.join(unknown_conflicts)}."
            )
        if phase.phase_id in phase.conflicts_with:
            raise ValueError(f"Campaign {campaign_id} phase {phase.phase_id} conflicts with itself.")
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


def scheduler_phase_fields(phase: LedgerPhase) -> dict[str, Any]:
    """Scheduler metadata persisted into per-phase run state (backward compatible)."""
    return {
        "parallel_safe": bool(getattr(phase, "parallel_safe", False)),
        "allowed_paths": list(getattr(phase, "allowed_paths", ()) or ()),
        "forbidden_paths": list(getattr(phase, "forbidden_paths", ()) or ()),
        "conflicts_with": list(getattr(phase, "conflicts_with", ()) or ()),
        "resource_class": list(getattr(phase, "resource_class", ()) or ()),
        "must_run_alone": bool(getattr(phase, "must_run_alone", False)),
        "merge_group": getattr(phase, "merge_group", None),
    }


def ledger_phase_state(phase: LedgerPhase, run_id: str) -> dict[str, Any]:
    phase_artifact_root = f"runs/{run_id}/phases/{phase.phase_id}"
    return {
        "phase_id": phase.phase_id,
        "name": phase.name,
        "lane": phase.lane,
        "dependencies": list(phase.dependencies),
        **scheduler_phase_fields(phase),
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
        **scheduler_phase_fields(phase),
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
            "branch_prepare": f"{phase_artifact_root}/branch_prepare.json",
            "branch": f"{phase_artifact_root}/branch.txt",
            "base_sha": f"{phase_artifact_root}/base_sha.txt",
            "commit_sha": f"{phase_artifact_root}/commit_sha.txt",
            "push_branch": f"{phase_artifact_root}/push_branch.json",
            "remote_branch": f"{phase_artifact_root}/remote_branch.json",
            "pr_create": f"{phase_artifact_root}/pr_create.json",
            "ci_status": f"{phase_artifact_root}/ci_status.json",
            "branch_protection": f"{phase_artifact_root}/branch_protection.json",
            "merge_gate": f"{phase_artifact_root}/merge_gate.json",
            "merge_result": f"{phase_artifact_root}/merge_result.json",
            "provider_limit": f"{phase_artifact_root}/provider_limit.json",
            "stage_checkpoints": f"{phase_artifact_root}/stage_checkpoints.jsonl",
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
    with _RUN_WRITE_LOCK:
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
    with _RUN_WRITE_LOCK:
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


def provider_replay_disabled() -> bool:
    return os.environ.get("FRONTIER_NO_PROVIDER_REPLAY", "").lower() in {"1", "true", "yes", "on"}


def record_stage_checkpoint(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    stage: str,
    *,
    status: str = "complete",
    details: dict[str, Any] | None = None,
) -> None:
    if stage not in WORKFLOW2_STAGES:
        raise ValueError(f"Unknown Workflow 2 stage: {stage}")
    phase_dir = provider_phase_dir(run_dir, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": utc_now(),
        "run_id": state.get("run_id"),
        "campaign_id": state.get("campaign_id"),
        "phase_id": phase.get("phase_id"),
        "stage": stage,
        "status": status,
        "details": details or {},
    }
    with (phase_dir / "stage_checkpoints.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    phase["current_stage"] = stage
    if status == "complete":
        completed = list(phase.get("completed_stages", []))
        if stage not in completed:
            completed.append(stage)
        phase["completed_stages"] = completed
        phase["last_completed_stage"] = stage
    append_event(
        run_dir,
        state,
        "STAGE_CHECKPOINT",
        phase_id=phase.get("phase_id"),
        stage=stage,
        status=status,
    )


def _resumable_statuses() -> set[str]:
    return (
        {"SPEC_READY", "EXECUTED", "VALIDATED", "REVIEWED", "REWORK", "REPAIRED", GIT_PHASE_BLOCKED}
        | GATE_BLOCKED_STATUSES
        | MERGE_PENDING_STATUSES
        | PROVIDER_WAITING_STATUSES
    )


def next_pending_provider_phase(state: dict[str, Any]) -> dict[str, Any] | None:
    resumable = _resumable_statuses()
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


def next_scheduled_provider_phase(state: dict[str, Any]) -> dict[str, Any] | None:
    """Dependency-aware single-phase selector for ``dag_wave`` mode.

    Resumable in-flight phases are continued first (identical to the sequential
    selector); a fresh phase is only chosen when its dependencies have all
    passed, in declaration order. Returns None when nothing is ready (the caller
    distinguishes "campaign complete" from "dependency deadlock").
    """

    resumable = _resumable_statuses()
    current = state.get("current_phase_id")
    if current:
        for phase in state["phases"]:
            if phase["phase_id"] == current and phase.get("status") in resumable:
                return phase
    for phase in state["phases"]:
        if phase["status"] in resumable:
            return phase
    ready = dag_scheduler.next_ready_phase(state["phases"])
    if ready is None:
        return None
    for phase in state["phases"]:
        if phase["phase_id"] == ready.phase_id:
            return phase
    return None


def select_next_phase(
    state: dict[str, Any], scheduler: SchedulerSettings
) -> dict[str, Any] | None:
    if scheduler.is_dag_wave:
        return next_scheduled_provider_phase(state)
    return next_pending_provider_phase(state)


def pending_phase_ids(state: dict[str, Any]) -> list[str]:
    return [p["phase_id"] for p in state.get("phases", []) if p.get("status") == "PENDING"]


def ready_wave_phases(
    state: dict[str, Any], scheduler: SchedulerSettings
) -> list[dict[str, Any]]:
    """Pick the next conflict-free, parallel-safe wave of PENDING phases.

    Returns the run-state phase dicts (preserving identity) for the first wave of
    a freshly-computed plan over the current state. Empty when no PENDING phase
    is dependency-ready.
    """

    plan = dag_scheduler.compute_waves(
        state.get("phases", []),
        max_parallel=scheduler.max_parallel_phases,
        red_authorized=scheduler.red_authorized,
    )
    if not plan.waves:
        return []
    wave_ids = list(plan.waves[0].phase_ids)
    by_id = {p["phase_id"]: p for p in state.get("phases", [])}
    return [by_id[pid] for pid in wave_ids if pid in by_id]


def active_campaign_phase_label(phase: dict[str, Any] | None) -> str:
    if not phase:
        return "`none`"
    name = f" - {phase['name']}" if phase.get("name") else ""
    return f"`{phase['phase_id']}`{name}"


def projected_phase_status(
    phase: dict[str, Any],
    *,
    completed_phase_id: str | None = None,
    completed_status: str | None = None,
) -> str:
    if completed_phase_id and phase.get("phase_id") == completed_phase_id and completed_status:
        return completed_status
    return str(phase.get("status") or "PENDING")


def render_active_campaign_pointer(
    state: dict[str, Any],
    *,
    completed_phase_id: str | None = None,
    completed_status: str | None = None,
    note: str | None = None,
) -> str:
    phases = list(state.get("phases", []))
    passing = [
        phase
        for phase in phases
        if projected_phase_status(
            phase,
            completed_phase_id=completed_phase_id,
            completed_status=completed_status,
        )
        in PASSING_VERDICTS
    ]
    next_pending = next(
        (
            phase
            for phase in phases
            if projected_phase_status(
                phase,
                completed_phase_id=completed_phase_id,
                completed_status=completed_status,
            )
            == "PENDING"
        ),
        None,
    )
    active_status = "complete" if phases and next_pending is None else "executing"
    current_phase = active_campaign_phase_label(next_pending) if next_pending else "`none` - campaign complete"
    last_completed = active_campaign_phase_label(passing[-1]) if passing else "`none`"
    last_completed_status = (
        projected_phase_status(
            passing[-1],
            completed_phase_id=completed_phase_id,
            completed_status=completed_status,
        )
        if passing
        else "none"
    )
    lines = [
        "# Active Campaign",
        "",
        "Project: `alpha_system`",
        "",
        f"Campaign: `campaigns/{state.get('campaign_id', 'unknown')}`",
        f"Workflow: `{state.get('workflow', 'workflow2')}`",
        f"Run: `{state.get('run_id', 'unknown')}`",
        f"Status: `{active_status}`",
        "",
        f"Current phase: {current_phase}",
        f"Last completed phase: {last_completed}",
        f"Last completed status: `{last_completed_status}`",
        f"Passing phases: `{len(passing)}/{len(phases)}`",
        "",
        "Ralph updates this pointer through reviewed phase commits so the tracked repo stays clean after Workflow 2 stops.",
        "",
        "Broker/live trading, paper trading, order routing, raw data commits, heavy artifact commits, local DB commits, and alpha/tradability claims without evidence remain out of scope.",
    ]
    if note:
        lines.extend(["", f"Note: {note}"])
    return "\n".join(lines) + "\n"


def resolve_active_campaign_id() -> str | None:
    """Read the active campaign id from the tracked ACTIVE_CAMPAIGN.md pointer.

    Powers ``frontier-resume`` / ``frontier-run`` with no campaign id so the
    operator can resume "the campaign I was working on" without retyping ids.
    """

    path = ROOT / ACTIVE_CAMPAIGN_FILE
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("campaign:"):
            value = stripped.split(":", 1)[1].strip().strip("`").strip()
            if value.startswith("campaigns/"):
                value = value[len("campaigns/"):]
            value = value.strip("/").strip()
            return value or None
    return None


def active_campaign_allowed_by_policy(config: dict[str, Any]) -> bool:
    artifacts = config.get("artifacts") if isinstance(config.get("artifacts"), dict) else {}
    allow_patterns = list(artifacts.get("allow_commit", [])) if isinstance(artifacts, dict) else []
    forbid_patterns = list(artifacts.get("forbid_commit", [])) if isinstance(artifacts, dict) else []
    placeholder_exceptions = artifacts.get("placeholder_exceptions") if isinstance(artifacts, dict) else None
    placeholder_dirs = artifacts.get("placeholder_dirs") if isinstance(artifacts, dict) else None
    if not isinstance(placeholder_exceptions, list):
        placeholder_exceptions = None
    if not isinstance(placeholder_dirs, list):
        placeholder_dirs = None
    allowed, blocked = curate_commit_paths(
        [ACTIVE_CAMPAIGN_FILE],
        allow_patterns=allow_patterns,
        forbid_patterns=forbid_patterns,
        placeholder_exceptions=placeholder_exceptions,
        placeholder_dirs=placeholder_dirs,
    )
    return ACTIVE_CAMPAIGN_FILE in allowed and ACTIVE_CAMPAIGN_FILE not in blocked


def phase_has_non_pointer_changes(root: Path, base_sha: str | None) -> bool:
    candidates: set[str] = set()
    status = git(root, "status", "--porcelain")
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            path = line[3:].strip()
            if " -> " in path:
                path = path.rsplit(" -> ", 1)[-1].strip()
            if path:
                candidates.add(path)
    if base_sha:
        head = git(root, "rev-parse", "HEAD")
        current_head = head.stdout.strip() if head.returncode == 0 else ""
        if current_head and current_head != base_sha:
            diff = git(root, "diff", "--name-only", f"{base_sha}..HEAD")
            if diff.returncode == 0:
                candidates.update(path.strip() for path in diff.stdout.splitlines() if path.strip())
    return any(path != ACTIVE_CAMPAIGN_FILE for path in candidates)


def write_active_campaign_for_phase_commit(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    config: dict[str, Any],
    execution_root: Path,
) -> None:
    if verdict not in PASSING_VERDICTS:
        return
    # Coordinator-only mode: in a parallel wave the scheduler (not the phase
    # branch) owns ACTIVE_CAMPAIGN.md so concurrent branches never race on it.
    if phase.get("suppress_active_pointer"):
        return
    if not active_campaign_allowed_by_policy(config):
        return
    base_sha = phase_base_sha_from_artifacts(provider_phase_dir(run_dir, phase), phase)
    if not phase_has_non_pointer_changes(execution_root, base_sha):
        return
    path = execution_root / ACTIVE_CAMPAIGN_FILE
    text = render_active_campaign_pointer(
        state,
        completed_phase_id=phase["phase_id"],
        completed_status=verdict,
        note=f"Projected after {phase['phase_id']} merge.",
    )
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if previous == text:
        return
    path.write_text(text, encoding="utf-8")
    next_phase = next(
        (
            item["phase_id"]
            for item in state.get("phases", [])
            if item.get("phase_id") != phase["phase_id"] and item.get("status") == "PENDING"
        ),
        None,
    )
    append_event(
        run_dir,
        state,
        "ACTIVE_CAMPAIGN_POINTER_WRITTEN",
        phase_id=phase["phase_id"],
        next_phase=next_phase,
    )


def write_provider_summary(run_dir: Path, state: dict[str, Any], note: str | None = None) -> None:
    passing = [phase for phase in state["phases"] if phase["status"] in PASSING_VERDICTS]
    blocked = [
        phase
        for phase in state["phases"]
        if phase["status"]
        in {GIT_PHASE_BLOCKED, "BLOCKED", "REWORK", RESUME_PRECONDITION_FAILED}
        | GATE_BLOCKED_STATUSES
        | MERGE_PENDING_STATUSES
        | PROVIDER_WAITING_STATUSES
    ]
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
            reason = f" - {phase.get('status_reason')}" if phase.get("status_reason") else ""
            lines.append(f"- {phase['phase_id']}: {phase['status']}{reason}")
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
    with _RUN_WRITE_LOCK:
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


def stop_file_is_max_phase_limit(stop_path: Path, state: dict[str, Any]) -> bool:
    if state.get("status") != "STOPPED" or state.get("current_phase_id"):
        return False
    try:
        text = stop_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "Reason: Requested max phases reached:" in text


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
    if status in PASSING_VERDICTS:
        phase.pop("status_reason", None)
    phase["completed_at"] = utc_now()
    state["current_phase_id"] = None
    state["current_micro_attempt"] = 0
    if status in PASSING_VERDICTS:
        state["phase_execution_performed"] = True
        if phase.get("execution_mode") == "provider_wired":
            record_stage_checkpoint(run_dir, state, phase, "complete", details={"phase_status": status})
    append_event(run_dir, state, event, phase_id=phase["phase_id"], status=status, reason=reason)
    if status in PASSING_VERDICTS:
        append_event(run_dir, state, "PHASE_COMPLETED", phase_id=phase["phase_id"], status=status)
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
    if _PARALLEL_MODE_ACTIVE:
        # A single phase block must not stop the whole parallel run; the
        # coordinator inspects per-phase status after the wave joins.
        return
    state["status"] = "STOPPED"
    state["stop_requested"] = True
    write_provider_stop(run_dir, state, reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, reason)


def _excerpt(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]\n"


def provider_limit_safe_resume_stage(stage: str) -> str:
    if stage in {"spec", "execute", "validate", "review", "done_check"}:
        return stage
    if stage.startswith("repair"):
        return "review"
    return "merge_gate"


def write_provider_limit_artifacts(
    phase_dir: Path,
    *,
    provider: str,
    stage: str,
    result: CommandResult,
    safe_resume_stage: str,
    status: str,
) -> None:
    phase_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "frontier-provider-limit-v1",
        "status": status,
        "provider": provider,
        "stage": stage,
        "safe_resume_stage": safe_resume_stage,
        "command": list(result.command),
        "return_code": result.returncode,
        "stdout_excerpt": _excerpt(result.stdout),
        "stderr_excerpt": _excerpt(result.stderr),
        "recorded_at": utc_now(),
    }
    write_json(phase_dir / "provider_limit.json", payload)
    lines = [
        "# Provider Limit",
        "",
        f"Status: {status}",
        f"Provider: {provider}",
        f"Stage: {stage}",
        f"Safe resume stage: {safe_resume_stage}",
        f"Return code: {result.returncode}",
        f"Command: `{' '.join(result.command)}`",
        "",
        "## stdout excerpt",
        "",
        "```text",
        _excerpt(result.stdout).rstrip(),
        "```",
        "",
        "## stderr excerpt",
        "",
        "```text",
        _excerpt(result.stderr).rstrip(),
        "```",
    ]
    (phase_dir / "provider_limit.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    handoff = [
        "# Provider Limit Resume Handoff",
        "",
        f"- Provider: {provider}",
        f"- Stage: {stage}",
        f"- Safe resume stage: {safe_resume_stage}",
        f"- Return code: {result.returncode}",
        f"- Command: `{' '.join(result.command)}`",
        "",
        "Resume after the provider limit resets. Do not mark review, done-check, or phase PASS unless the required artifacts are present and valid.",
    ]
    (phase_dir / "provider_limit_handoff.md").write_text("\n".join(handoff) + "\n", encoding="utf-8")
    handoff_path = phase_dir / "handoff.md"
    if not handoff_path.exists():
        handoff_path.write_text("\n".join(handoff) + "\n", encoding="utf-8")


def wait_provider_limit(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    provider: str,
    stage: str,
    result: CommandResult,
    status: str,
) -> None:
    safe_resume_stage = provider_limit_safe_resume_stage(stage)
    phase_dir = provider_phase_dir(run_dir, phase)
    write_provider_limit_artifacts(
        phase_dir,
        provider=provider,
        stage=stage,
        result=result,
        safe_resume_stage=safe_resume_stage,
        status=status,
    )
    set_provider_phase_status(phase, status)
    phase["status_reason"] = f"{provider} usage limit reached during {stage}."
    phase["provider_limit"] = {
        "status": status,
        "provider": provider,
        "stage": stage,
        "safe_resume_stage": safe_resume_stage,
        "return_code": result.returncode,
    }
    phase["resume_stage"] = safe_resume_stage
    state["status"] = status
    state["stop_requested"] = True
    state["current_phase_id"] = phase["phase_id"]
    state["current_stage"] = safe_resume_stage
    record_stage_checkpoint(
        run_dir,
        state,
        phase,
        safe_resume_stage,
        status="waiting_provider_limit",
        details={"provider": provider, "return_code": result.returncode},
    )
    append_event(
        run_dir,
        state,
        "PROVIDER_LIMIT",
        phase_id=phase["phase_id"],
        provider=provider,
        stage=stage,
        safe_resume_stage=safe_resume_stage,
    )
    write_provider_stop(run_dir, state, f"{provider} usage limit reached during {stage}.")
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, f"Waiting for {provider} provider limit reset at {stage}.")
    progress(run_dir, f"{phase['phase_id']} waiting on {provider} provider limit at {stage}.")


def wait_campaign_provider_limit(
    run_dir: Path,
    state: dict[str, Any],
    *,
    provider: str,
    stage: str,
    result: CommandResult,
    status: str,
) -> None:
    payload = {
        "schema_version": "frontier-provider-limit-v1",
        "status": status,
        "provider": provider,
        "stage": stage,
        "safe_resume_stage": stage,
        "command": list(result.command),
        "return_code": result.returncode,
        "stdout_excerpt": _excerpt(result.stdout),
        "stderr_excerpt": _excerpt(result.stderr),
        "recorded_at": utc_now(),
    }
    write_json(run_dir / "provider_limit.json", payload)
    (run_dir / "provider_limit.md").write_text(
        "\n".join(
            [
                "# Provider Limit",
                "",
                f"Status: {status}",
                f"Provider: {provider}",
                f"Stage: {stage}",
                f"Return code: {result.returncode}",
                f"Command: `{' '.join(result.command)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    state["status"] = status
    state["stop_requested"] = True
    append_event(run_dir, state, "PROVIDER_LIMIT", provider=provider, stage=stage)
    write_provider_stop(run_dir, state, f"{provider} usage limit reached during {stage}.")
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, f"Waiting for {provider} provider limit reset at {stage}.")


def handle_provider_nonzero(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    provider: str,
    stage: str,
    result: CommandResult,
) -> bool:
    status = classify_provider_nonzero(provider, result.stdout, result.stderr, result.returncode)
    if status in PROVIDER_WAITING_STATUSES:
        wait_provider_limit(run_dir, state, phase, provider=provider, stage=stage, result=result, status=status)
        return True
    return False


def current_provider_limit_phase(state: dict[str, Any]) -> dict[str, Any] | None:
    current = state.get("current_phase_id")
    for phase in state.get("phases", []):
        if phase.get("status") in PROVIDER_WAITING_STATUSES and (current in {None, phase.get("phase_id")}):
            return phase
    return None


def current_gate_blocked_phase(state: dict[str, Any]) -> dict[str, Any] | None:
    current = state.get("current_phase_id")
    for phase in state.get("phases", []):
        if phase.get("status") in ({GIT_PHASE_BLOCKED} | GATE_BLOCKED_STATUSES | MERGE_PENDING_STATUSES) and (
            current in {None, phase.get("phase_id")}
        ):
            return phase
    return None


def mark_auto_merge_pending(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    reason: str,
    *,
    event: str = AUTO_MERGE_ARMED,
    pr_number: str | int | None = None,
) -> None:
    set_provider_phase_status(phase, AUTO_MERGE_ARMED)
    phase["status_reason"] = reason
    resume_command = (
        "python tools/frontier/ralph_driver.py resume "
        f"--run-dir {run_dir} --phase-id {phase['phase_id']} --from-stage merge "
        "--provider-wired --no-provider-replay"
    )
    phase["resume_command"] = resume_command
    if _PARALLEL_MODE_ACTIVE:
        append_event(
            run_dir,
            state,
            event,
            phase_id=phase["phase_id"],
            status=AUTO_MERGE_ARMED,
            pr_number=pr_number,
            reason=reason,
            resume_command=resume_command,
        )
        write_state(run_dir, state)
        return
    state["status"] = AUTO_MERGE_ARMED
    state["stop_requested"] = True
    state["current_phase_id"] = phase["phase_id"]
    state["current_stage"] = "merge"
    append_event(
        run_dir,
        state,
        event,
        phase_id=phase["phase_id"],
        status=AUTO_MERGE_ARMED,
        pr_number=pr_number,
        reason=reason,
        resume_command=resume_command,
    )
    write_provider_stop(run_dir, state, f"{reason}\nResume command: {resume_command}")
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, f"{reason}\n\nResume command: `{resume_command}`")
    progress(run_dir, f"{phase['phase_id']} waiting for GitHub auto-merge.")


def block_provider_gate(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    status: str,
    reason: str,
    *,
    event: str,
    source: str,
) -> None:
    set_provider_phase_status(phase, status)
    phase["status_reason"] = reason
    if _PARALLEL_MODE_ACTIVE:
        append_event(
            run_dir, state, event, phase_id=phase["phase_id"], status=status, source=source, reason=reason
        )
        write_state(run_dir, state)
        write_provider_summary(run_dir, state, reason)
        progress(run_dir, f"{phase['phase_id']} stopped at {status}: {reason}")
        return
    state["status"] = status
    state["stop_requested"] = True
    state["current_phase_id"] = phase["phase_id"]
    append_event(run_dir, state, event, phase_id=phase["phase_id"], status=status, source=source, reason=reason)
    write_provider_stop(run_dir, state, reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, reason)
    progress(run_dir, f"{phase['phase_id']} stopped at {status}: {reason}")


def phase_label(phase: dict[str, Any]) -> str:
    name = phase.get("name")
    return f"{phase['phase_id']} - {name}" if name else phase["phase_id"]


def campaign_file_list(campaign_id: str) -> str:
    return "\n".join(f"- campaigns/{campaign_id}/{name}" for name in REQUIRED_CAMPAIGN_FILES)


def run_artifact_spec_policy(phase_id: str) -> str:
    return f"""- `runs/**` is local-only runtime state.
- run_dir artifacts are for local audit only.
- The run-local `handoff.md` under `runs/<run_id>/...` must never be staged or committed.
- Commit-eligible handoff, if needed, must be under `handoffs/{phase_id}.md` (`handoffs/<PHASE_ID>.md`).
- `runs/.gitkeep`, `runs/README.md`, and `runs/**` must not appear in Allowed Paths.
- If a campaign/spec asks for runs placeholders, resolve that as local-only and do not commit it."""


def readme_snapshot_spec_policy() -> str:
    return """- Include `README.md` under commit-eligible Allowed Paths for every non-mock phase.
- Require a concise README update that reflects the phase after merge: current campaign progress, active/next phase, newly added durable modules/docs/commands, and unchanged safety boundaries.
- Keep the README snapshot factual and compact; do not add generated run details, local artifact paths, alpha/profitability claims, broker/live/paper/deployment behavior, or duplicated phase handoff content."""


def executor_run_artifact_policy(phase_id: str) -> str:
    return f"""- Do not stage or commit anything under `runs/`.
- Do not stage run-local `handoff.md` under `runs/<run_id>/...`.
- Before commit, `git diff --cached --name-only` must contain no `runs/` path.
- If a commit-eligible handoff is needed, write it under `handoffs/{phase_id}.md`, not under `runs/`."""


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
- Include this README snapshot policy in the generated spec:
{readme_snapshot_spec_policy()}
- Include a generated spec Artifact Policy section with these exact run-artifact rules:
{run_artifact_spec_policy(phase["phase_id"])}
- Separate commit-eligible Allowed Paths from local-only run artifacts.
- Do not list any `runs/` path under Allowed Paths or any other commit-eligible path section.
- Output markdown only.
"""


def executor_prompt(phase: dict[str, Any], spec_text: str, phase_dir: Path) -> str:
    return f"""You are Codex running as the executor for Frontier Workflow 2.

Execute exactly the generated phase spec below for {phase_label(phase)}. Do not broaden scope.

Safety rules:
- Do not perform live trading, paper trading, broker operations, order routing, production deployment, PR creation, auto-merge, or destructive cleanup.
- Do not call Claude.
- Do not run reviewer.
- Do not create `review.md`.
- Do not create `verdict.json`.
- Do not create a PR.
- Do not merge.
- Do not mark the phase PASS.
- Do not run `git add`, `git commit`, `git push`, `git status`, or `git diff`, and do not stage or commit anything yourself. Leave all your changes UNSTAGED in the working tree.
- OVERRIDE: the spec's "Allowed Paths" / "Commit only" lists exist to tell the Ralph driver which files to stage and commit on your behalf — they are NOT an instruction for you to run git. Just create or edit those files in the working tree and list them by path in your handoff. (In worktree mode the shared `.git` metadata is read-only to you by design; the unsandboxed driver performs the authoritative staging and commit after you finish, so a git failure on your side is expected and must not be treated as a blocker.)
- Do not use `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, or force push.
- Do not weaken tests or add visible test-only branches.
- Keep generated local-only artifacts out of git.
- Run artifact commit rules:
{executor_run_artifact_policy(phase["phase_id"])}
- Run only validation that is safe and requested by the spec.
- Write execution output and handoff only.
- The Ralph driver owns staging, commit, validation, review, done-check, verdict, repair, PR, CI, and merge gate.

Run artifact directory available to you:
{phase_dir.relative_to(ROOT)}

Generated spec:

{spec_text}
"""


def compact_prompt_section(name: str, text: str, *, max_chars: int = PROMPT_SECTION_MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    head_chars = max_chars // 2
    tail_chars = max_chars - head_chars
    omitted = len(text) - max_chars
    return (
        text[:head_chars]
        + f"\n\n[Frontier prompt compaction: omitted {omitted} characters from {name}; "
        "inspect the full run artifact or repository file for complete context.]\n\n"
        + text[-tail_chars:]
    )


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
- executor output summary and full repository/run artifacts as needed
- validation output

Return markdown. Include exactly one verdict line using one of:
VERDICT: PASS
VERDICT: PASS_WITH_WARNINGS
VERDICT: REWORK
VERDICT: BLOCKED

Be conservative. Block broker/live/paper scope, destructive operations, hidden failed runs, test weakening, artifact policy violations, unsupported claims, and scope drift.

Generated spec:

{compact_prompt_section("generated phase spec", spec_text)}

Executor output:

{compact_prompt_section("executor output", executor_text)}

Validation output:

{compact_prompt_section("validation output", validation_text)}
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

{compact_prompt_section("generated phase spec", spec_text)}

Executor output:

{compact_prompt_section("executor output", executor_text)}

Validation output:

{compact_prompt_section("validation output", validation_text)}

Review output:

{compact_prompt_section("review output", review_text)}

Handoff:

{compact_prompt_section("handoff", handoff_text)}
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
- Do not call Claude.
- Do not run reviewer.
- Do not create `review.md`.
- Do not create `verdict.json`.
- Do not create a PR.
- Do not merge.
- Do not mark the phase PASS.
- Do not use `{FORBIDDEN_GIT_ADD_DOT}`, `{FORBIDDEN_GIT_ADD_ALL}`, or force push.
- Do not weaken tests or add visible test-only branches.
- Run artifact commit rules:
{executor_run_artifact_policy(phase["phase_id"])}
- The Ralph driver owns validation, review, done-check, verdict, PR, CI, and merge gate.

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

Commit-Eligible Allowed Paths:
- None for this deterministic mock-provider phase.

Local-Only Run Artifacts:
{run_artifact_spec_policy(phase["phase_id"])}
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
    if provider_replay_disabled():
        return CommandResult(
            ("provider-replay-disabled", "claude"),
            125,
            "",
            "FRONTIER_NO_PROVIDER_REPLAY=1 prevents Claude replay.",
        )
    config = load_provider_config(root)
    response = ClaudeProviderAdapter(config, CommandRunner(root)).run_prompt(prompt)
    return CommandResult(tuple(response.command), response.return_code, response.stdout, response.stderr)


def codex_noninteractive(prompt: str, *, root: Path = ROOT) -> CommandResult:
    if provider_replay_disabled():
        return CommandResult(
            ("provider-replay-disabled", "codex"),
            125,
            "",
            "FRONTIER_NO_PROVIDER_REPLAY=1 prevents Codex replay.",
        )
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


def merge_result_metadata(result: Any) -> dict[str, Any]:
    if hasattr(result, "metadata") and isinstance(result.metadata, dict):
        return result.metadata
    if isinstance(result, dict) and isinstance(result.get("metadata"), dict):
        return result["metadata"]
    return {}


def merge_result_status(result: Any) -> str:
    metadata = merge_result_metadata(result)
    return str(metadata.get("status") or "")


def merge_result_classification(result: Any) -> str:
    metadata = merge_result_metadata(result)
    return str(metadata.get("classification") or "")


def merge_result_is_merged(result: Any) -> bool:
    metadata = merge_result_metadata(result)
    return merge_result_status(result) in {MERGED, ALREADY_MERGED} or bool(metadata.get("merged"))


def merge_result_is_already_merged(result: Any) -> bool:
    metadata = merge_result_metadata(result)
    return merge_result_status(result) == ALREADY_MERGED or bool(metadata.get("already_merged"))


def merge_result_auto_armed(result: Any) -> bool:
    metadata = merge_result_metadata(result)
    return merge_result_status(result) == AUTO_MERGE_ARMED or bool(metadata.get("auto_merge_armed"))


def merge_result_direct_performed(result: Any) -> bool:
    metadata = merge_result_metadata(result)
    return bool(metadata.get("direct_merge_performed"))


def write_merge_result_artifacts(phase_dir: Path, result: GitHubResult) -> None:
    write_github_result(phase_dir / "merge_result.json", result)
    metadata = merge_result_metadata(result)
    retry_command = metadata.get("retry_command")
    lines = [
        "# Merge Result",
        "",
        f"Status: {metadata.get('status', '') or 'UNKNOWN'}",
        f"Classification: {metadata.get('classification', '') or 'unknown'}",
        f"Dry run: {str(result.dry_run).lower()}",
        f"Blocked: {str(result.blocked).lower()}",
        f"Merged: {str(bool(metadata.get('merged'))).lower()}",
        f"Already merged: {str(bool(metadata.get('already_merged'))).lower()}",
        f"Auto-merge armed: {str(bool(metadata.get('auto_merge_armed'))).lower()}",
        f"Return code: {result.return_code}",
        f"Command: `{' '.join(result.command)}`",
    ]
    if retry_command:
        lines.append(f"Retry command: `{' '.join(str(part) for part in retry_command)}`")
    if result.instructions:
        lines.extend(["", "## Instructions", "", result.instructions])
    for label, value in [
        ("stdout", result.stdout),
        ("stderr", result.stderr),
        ("direct stdout", metadata.get("direct_stdout")),
        ("direct stderr", metadata.get("direct_stderr")),
        ("retry stdout", metadata.get("retry_stdout")),
        ("retry stderr", metadata.get("retry_stderr")),
    ]:
        if value:
            lines.extend(["", f"## {label}", "", "```text", str(value).rstrip(), "```"])
    (phase_dir / "merge_result.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cleanup_phase_worktree_after_merge(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    dry_run: bool | None = None,
) -> None:
    if not phase.get("merged"):
        return
    phase_dir = provider_phase_dir(run_dir, phase)
    config = load_config(ROOT / "frontier.yaml")
    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    remote = str(github_config.get("remote") or "origin")
    # Worktree removal + branch delete only apply in worktree mode.
    if state.get("worktree_mode"):
        path_text = str(phase.get("worktree_path") or "").strip()
        branch = str(phase.get("branch") or "").strip()
        if path_text and branch:
            manager = WorktreeManager(ROOT, runtime_config().worktree_root)
            cleanup = manager.cleanup_after_merge(
                Path(path_text),
                branch,
                remote=remote,
                dry_run=bool(state.get("mock_providers")) if dry_run is None else dry_run,
            )
            write_json(phase_dir / "worktree_cleanup.json", cleanup)
            append_event(
                run_dir,
                state,
                "WORKTREE_CLEANUP" if cleanup.get("ok") else "WORKTREE_CLEANUP_BLOCKED",
                phase_id=phase["phase_id"],
                branch=branch,
                path=path_text,
                ok=bool(cleanup.get("ok")),
            )
    else:
        # In-tree (serial default) mode: there is no worktree to remove, but the
        # merged remote branch still needs cleanup. merge_pr no longer passes
        # `--delete-branch` (it can flip core.bare while a branch is checked out),
        # so delete the frontier-owned remote branch directly here. A plain
        # `git push --delete` does not flip core.bare. Guarded to auto/ branches,
        # skipped under mock/dry-run; best-effort, never blocks the merge.
        branch = str(phase.get("branch") or "").strip()
        effective_dry = bool(state.get("mock_providers")) if dry_run is None else bool(dry_run)
        if branch.startswith("auto/") and not effective_dry:
            delete = git(ROOT, "push", remote, "--delete", branch)
            append_event(
                run_dir,
                state,
                "REMOTE_BRANCH_DELETED" if delete.returncode == 0 else "REMOTE_BRANCH_DELETE_FAILED",
                phase_id=phase["phase_id"],
                branch=branch,
                ok=delete.returncode == 0,
            )
    # Post-merge repo hygiene runs in ALL modes (worktree and in-tree).
    repo_hygiene = restore_local_repo_after_merge(state, remote=remote)
    if repo_hygiene.get("core_bare_restored") or repo_hygiene.get("base_synced"):
        append_event(
            run_dir,
            state,
            "POST_MERGE_REPO_HYGIENE",
            phase_id=phase["phase_id"],
            core_bare_restored=bool(repo_hygiene.get("core_bare_restored")),
            base_synced=bool(repo_hygiene.get("base_synced")),
        )


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_stripped_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def phase_branch_from_artifacts(
    phase_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
) -> str:
    git_phase = read_json_if_exists(phase_dir / "git_phase.json")
    branch = (
        phase.get("branch")
        or read_stripped_if_exists(phase_dir / "branch.txt")
        or git_phase.get("branch")
        or phase_branch_name(state["campaign_id"], phase["phase_id"], phase.get("name"))
    )
    return str(branch)


def phase_base_sha_from_artifacts(phase_dir: Path, phase: dict[str, Any]) -> str | None:
    branch_prepare = read_json_if_exists(phase_dir / "branch_prepare.json")
    git_phase = read_json_if_exists(phase_dir / "git_phase.json")
    candidates = [
        phase.get("base_sha"),
        read_stripped_if_exists(phase_dir / "base_sha.txt"),
        branch_prepare.get("base_sha"),
        git_phase.get("base_sha"),
    ]
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return None


def recover_phase_commit_sha(
    phase_dir: Path,
    phase: dict[str, Any],
    *,
    branch: str,
    execution_root: Path,
    allow_head_fallback: bool = False,
) -> str | None:
    git_phase = read_json_if_exists(phase_dir / "git_phase.json")
    candidates = [
        phase.get("commit_sha"),
        read_stripped_if_exists(phase_dir / "commit_sha.txt"),
        git_phase.get("commit_sha"),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    if not allow_head_fallback:
        return None
    for ref in (branch, "HEAD"):
        result = git(execution_root, "rev-parse", ref)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def ensure_phase_head(root: Path, branch: str, commit_sha: str | None) -> str | None:
    if not commit_sha:
        return "No local commit SHA is available for this phase."
    if not local_commit_exists(root, commit_sha):
        return f"Recorded phase commit {commit_sha} is missing locally."
    head = git(root, "rev-parse", "HEAD")
    if head.returncode == 0 and head.stdout.strip() == commit_sha:
        return None
    checkout = git(root, "checkout", branch)
    if checkout.returncode != 0:
        return checkout.stderr.strip() or checkout.stdout.strip() or f"Could not check out {branch} before push."
    head = git(root, "rev-parse", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != commit_sha:
        return f"Local HEAD does not match recorded commit {commit_sha} after checking out {branch}."
    return None


def dry_remote_branch_result(branch: str, *, remote: str, local_sha: str | None) -> RemoteBranchResult:
    return RemoteBranchResult(
        exists=False,
        remote_sha="",
        local_sha=local_sha or "",
        matches=False,
        stdout="",
        stderr="",
        return_code=0,
        branch=branch,
        remote=remote,
        command=["git", "ls-remote", "--heads", remote, f"refs/heads/{branch}"],
        dry_run=True,
    )


def prepare_phase_branch_for_execution(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    execution_root: Path,
) -> bool:
    if (bool(state.get("mock_providers")) and os.environ.get("FRONTIER_MOCK_COMMIT") != "1") or bool(
        state.get("worktree_mode")
    ):
        return True
    phase_dir = provider_phase_dir(run_dir, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)
    existing_branch = phase.get("branch") or read_stripped_if_exists(phase_dir / "branch.txt")
    existing_base = phase_base_sha_from_artifacts(phase_dir, phase)
    if existing_branch and existing_base and (phase_dir / "branch_prepare.json").exists():
        checkout = git(execution_root, "checkout", str(existing_branch))
        if checkout.returncode != 0:
            reason = (
                "GIT_PHASE_BLOCKED: prepared phase branch could not be checked out before executor: "
                f"{checkout.stderr.strip() or checkout.stdout.strip()}"
            )
            block_provider_gate(
                run_dir,
                state,
                phase,
                GIT_PHASE_BLOCKED,
                reason,
                event="GIT_PHASE_BLOCKED",
                source="branch_prepare_checkout_failed",
            )
            return False
        append_event(run_dir, state, "BRANCH_PREPARE_REUSED", phase_id=phase["phase_id"], branch=str(existing_branch))
        return True

    config = load_config(ROOT / "frontier.yaml")
    project_config = config.get("project") if isinstance(config.get("project"), dict) else {}
    default_branch = str(project_config.get("default_branch") or "main")
    try:
        base_ref, _base_sha = resolve_base_ref(execution_root, default_branch)
        requested_branch = phase_branch_from_artifacts(phase_dir, state, phase)
        result = prepare_phase_branch(execution_root, requested_branch, base_ref=base_ref, dry_run=False)
    except RuntimeError as error:
        reason = f"GIT_PHASE_BLOCKED: branch preparation failed before executor: {error}"
        block_provider_gate(
            run_dir,
            state,
            phase,
            GIT_PHASE_BLOCKED,
            reason,
            event="GIT_PHASE_BLOCKED",
            source="branch_prepare_failed",
        )
        return False
    write_branch_prepare_artifacts(phase_dir, result)
    phase["branch"] = result.branch
    phase["base_ref"] = result.base_ref
    phase["base_sha"] = result.base_sha
    append_event(
        run_dir,
        state,
        "BRANCH_PREPARED",
        phase_id=phase["phase_id"],
        branch=result.branch,
        base_ref=result.base_ref,
        base_sha=result.base_sha,
        used_unique_branch=result.used_unique_branch,
    )
    write_state(run_dir, state)
    return True


def post_phase_git_github(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    execution_root: Path = ROOT,
    defer_merge: bool = False,
) -> bool:
    phase_dir = provider_phase_dir(run_dir, phase)
    config = load_config(ROOT / "frontier.yaml")
    lane = str(phase.get("lane") or "green").lower()
    branch = phase_branch_from_artifacts(phase_dir, state, phase)
    mock_enabled = bool(state.get("mock_providers"))
    dry_git = mock_enabled and os.environ.get("FRONTIER_MOCK_COMMIT") != "1"
    resuming_gate = phase.get("status") in (GATE_BLOCKED_STATUSES | MERGE_PENDING_STATUSES)

    if resuming_gate:
        git_result_data = read_json_if_exists(phase_dir / "git_phase.json")
        commit_sha = recover_phase_commit_sha(
            phase_dir,
            phase,
            branch=branch,
            execution_root=execution_root,
            allow_head_fallback=False,
        )
        if commit_sha is None and not dry_git:
            reason = (
                "PUSH_BLOCKED: local commit is missing. Restore the phase branch/commit or rerun the "
                "phase explicitly; resume will not rerun Claude or Codex automatically."
            )
            block_provider_gate(
                run_dir,
                state,
                phase,
                PUSH_BLOCKED,
                reason,
                event="BRANCH_PUSH_BLOCKED",
                source="branch_push_blocked",
            )
            return False
        changed = list(git_result_data.get("changed_files", [])) if isinstance(git_result_data.get("changed_files"), list) else []
        blocked = list(git_result_data.get("blocked_files", [])) if isinstance(git_result_data.get("blocked_files"), list) else []
    else:
        base_sha = phase_base_sha_from_artifacts(phase_dir, phase)
        if not dry_git:
            write_active_campaign_for_phase_commit(
                run_dir,
                state,
                phase,
                verdict,
                config=config,
                execution_root=execution_root,
            )
        git_result = commit_phase_changes(
            root=execution_root,
            campaign_id=state["campaign_id"],
            phase_id=phase["phase_id"],
            summary=phase.get("name") or phase["phase_id"],
            branch=branch,
            config=config,
            dry_run=dry_git,
            push=False,
            base_sha=base_sha,
        )
        write_git_phase_artifacts(phase_dir, git_result)
        commit_sha = git_result.commit_sha
        changed = git_result.changed_files
        blocked = git_result.blocked_files
        if git_result.base_sha:
            phase["base_sha"] = git_result.base_sha
        if not dry_git and blocked:
            reason = "GIT_PHASE_BLOCKED: artifact policy blocked phase commit paths: " + ", ".join(blocked)
            block_provider_gate(
                run_dir,
                state,
                phase,
                GIT_PHASE_BLOCKED,
                reason,
                event="GIT_PHASE_BLOCKED",
                source="git_phase_artifact_policy",
            )
            return False
        if not dry_git and not commit_sha:
            reason = (
                "GIT_PHASE_BLOCKED: fresh git phase produced no phase commit. "
                "The worktree was clean at the recorded base or no commit could be adopted."
            )
            block_provider_gate(
                run_dir,
                state,
                phase,
                GIT_PHASE_BLOCKED,
                reason,
                event="GIT_PHASE_BLOCKED",
                source="git_phase_no_commit",
            )
            return False

    phase["branch"] = branch
    phase["commit_sha"] = commit_sha
    (phase_dir / "branch.txt").write_text(branch + "\n", encoding="utf-8")
    (phase_dir / "commit_sha.txt").write_text((commit_sha or "") + "\n", encoding="utf-8")
    commit_checkpoint_status = "dry_run" if dry_git and not commit_sha else "complete"
    record_stage_checkpoint(
        run_dir,
        state,
        phase,
        "commit",
        status=commit_checkpoint_status,
        details={"branch": branch, "commit_sha": commit_sha, "resuming_gate": resuming_gate},
    )
    append_event(run_dir, state, "GIT_PHASE_RECORDED", phase_id=phase["phase_id"], dry_run=dry_git)

    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    project_config = config.get("project") if isinstance(config.get("project"), dict) else {}
    required_checks = phase_required_checks(phase, config)
    ci_status = CI_SUCCESS if mock_enabled else "NOT_FOUND"
    pr_number: str | int | None = None
    pr_result = None
    auto_pr_requested = phase_auto_pr_allowed(config, phase) or os.environ.get("FRONTIER_CREATE_PR") == "1"
    pr_dry_run = mock_enabled or os.environ.get("FRONTIER_CREATE_PR") == "0" or not phase_auto_pr_allowed(config, phase)
    if os.environ.get("FRONTIER_CREATE_PR") == "1":
        pr_dry_run = False
    if auto_pr_requested:
        state["github_operations_performed"] = True

    remote = str(github_config.get("remote") or "origin")
    branch_pushed = False
    remote_result = dry_remote_branch_result(branch, remote=remote, local_sha=commit_sha)
    branch_push_required = auto_pr_requested and not pr_dry_run
    if auto_pr_requested:
        if branch_push_required and not commit_sha:
            reason = (
                "PUSH_BLOCKED: local commit is missing. Restore the phase branch/commit or rerun the "
                "phase explicitly; resume will not rerun Claude or Codex automatically."
            )
            block_provider_gate(
                run_dir,
                state,
                phase,
                PUSH_BLOCKED,
                reason,
                event="BRANCH_PUSH_BLOCKED",
                source="branch_push_blocked",
            )
            return False
        if branch_push_required and os.environ.get("FRONTIER_PUSH") == "0":
            push_result = PushBranchResult(
                dry_run=True,
                branch=branch,
                remote=remote,
                command=["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"],
                instructions="FRONTIER_PUSH=0 prevented branch push before real PR creation.",
            )
            write_push_branch_artifacts(phase_dir, push_result)
            reason = (
                "PUSH_BLOCKED: FRONTIER_PUSH=0 prevented branch push before PR creation. "
                "Enable push or disable real PR creation, then resume the run."
            )
            block_provider_gate(
                run_dir,
                state,
                phase,
                PUSH_BLOCKED,
                reason,
                event="BRANCH_PUSH_BLOCKED",
                source="branch_push_blocked",
            )
            return False
        if branch_push_required:
            head_error = ensure_phase_head(execution_root, branch, commit_sha)
            if head_error:
                instructions = (
                    "Restore the recorded phase branch/commit locally or rerun the phase explicitly; "
                    "resume will not rerun Claude or Codex automatically."
                )
                push_result = PushBranchResult(
                    dry_run=False,
                    branch=branch,
                    remote=remote,
                    command=["git", "push", "-u", remote, f"HEAD:refs/heads/{branch}"],
                    return_code=1,
                    stderr=head_error,
                    instructions=instructions,
                )
                write_push_branch_artifacts(phase_dir, push_result)
                reason = f"PUSH_BLOCKED: prior local phase commit is missing or not checked out. {head_error}"
                block_provider_gate(
                    run_dir,
                    state,
                    phase,
                    PUSH_BLOCKED,
                    reason,
                    event="BRANCH_PUSH_BLOCKED",
                    source="branch_push_blocked",
                )
                return False
            state["network_used"] = True
            push_result = push_phase_branch(execution_root, branch, remote=remote, dry_run=False)
            write_push_branch_artifacts(phase_dir, push_result)
            if not push_result.ok:
                reason = f"PUSH_BLOCKED: push branch failed. {push_result.instructions or push_result.stderr}"
                block_provider_gate(
                    run_dir,
                    state,
                    phase,
                    PUSH_BLOCKED,
                    reason,
                    event="BRANCH_PUSH_BLOCKED",
                    source="branch_push_blocked",
                )
                return False
            branch_pushed = True
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "push",
                details={"branch": branch, "remote": remote, "dry_run": False},
            )
            append_event(run_dir, state, "BRANCH_PUSHED", phase_id=phase["phase_id"], branch=branch, remote=remote)
            remote_result = verify_remote_branch(execution_root, branch, remote=remote)
            write_remote_branch_artifacts(phase_dir, remote_result)
            if not remote_result.exists:
                reason = "REMOTE_BRANCH_BLOCKED: remote branch missing after push. Fix git remote visibility and resume the run."
                block_provider_gate(
                    run_dir,
                    state,
                    phase,
                    REMOTE_BRANCH_BLOCKED,
                    reason,
                    event="REMOTE_BRANCH_BLOCKED",
                    source="remote_branch_blocked",
                )
                return False
            if not remote_result.matches:
                reason = (
                    "REMOTE_BRANCH_BLOCKED: remote branch SHA mismatch. "
                    f"local={remote_result.local_sha or 'unknown'} remote={remote_result.remote_sha or 'unknown'}."
                )
                block_provider_gate(
                    run_dir,
                    state,
                    phase,
                    REMOTE_BRANCH_BLOCKED,
                    reason,
                    event="REMOTE_BRANCH_BLOCKED",
                    source="remote_branch_blocked",
                )
                return False
        else:
            push_result = push_phase_branch(execution_root, branch, remote=remote, dry_run=True)
            write_push_branch_artifacts(phase_dir, push_result)
            write_remote_branch_artifacts(phase_dir, remote_result)
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "push",
                details={"branch": branch, "remote": remote, "dry_run": True},
            )

    base = (
        str(project_config.get("default_branch") or "main")
        if mock_enabled or pr_dry_run
        else detect_default_branch(root=execution_root)
    )
    title = f"{state['campaign_id']}/{phase['phase_id']}: {phase.get('name') or phase['phase_id']}"
    provisional_gate = f"Merge gate will be evaluated after PR/CI. Verdict: {verdict}."
    body = pr_body_text(run_dir, phase_dir, state, phase, verdict, provisional_gate)
    body_file = phase_dir / "pr_body.md"
    body_file.write_text(body, encoding="utf-8")
    pr_result = create_pr(
        title=title,
        body=body,
        base=base,
        head=branch,
        body_file=body_file,
        branch_pushed=branch_pushed,
        remote_sha=remote_result.remote_sha,
        local_sha=remote_result.local_sha or commit_sha,
        root=execution_root,
        dry_run=pr_dry_run,
    )
    write_pr_create_artifacts(phase_dir, pr_result)
    if auto_pr_requested:
        if pr_result.ok and not pr_result.dry_run:
            state["prs_created"] = True
            pr_meta = pr_result.metadata.get("pr") if isinstance(pr_result.metadata, dict) else {}
            pr_number = pr_result.metadata.get("number") or (pr_meta or {}).get("number")
            phase["pr_number"] = pr_number
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "pr",
                details={"pr_number": pr_number, "dry_run": pr_result.dry_run},
            )
        elif pr_result.blocked:
            reason = "PR_CREATE_BLOCKED: " + (pr_result.instructions or pr_result.stderr)
            block_provider_gate(
                run_dir,
                state,
                phase,
                PR_CREATE_BLOCKED,
                reason,
                event="PR_CREATE_BLOCKED",
                source="pr_create_blocked",
            )
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
            [
                {"name": check or "mock-ci", "state": "SUCCESS", "bucket": "pass"}
                for check in (required_checks or ["mock-ci"])
            ],
            required_checks=required_checks,
        )
    else:
        ci_result = classify_ci_checks([], required_checks=required_checks)
    ci_status = ci_result.state
    write_ci_status_artifacts(phase_dir, ci_result)
    phase["ci_status"] = ci_status
    if ci_status == CI_SUCCESS:
        record_stage_checkpoint(run_dir, state, phase, "ci", details={"pr_number": pr_number})
    if github_config.get("require_ci", True) and ci_status != CI_SUCCESS:
        reason = f"CI_BLOCKED: CI status was {ci_status}."
        block_provider_gate(
            run_dir,
            state,
            phase,
            CI_BLOCKED,
            reason,
            event="CI_BLOCKED",
            source="ci_blocked",
        )
        return False

    if defer_merge:
        # Parallel build pass: stop after CI; the serial merge queue (coordinator)
        # re-evaluates branch protection + merge gate against current main and
        # performs the merge one phase at a time.
        set_provider_phase_status(phase, MERGE_READY)
        phase["merge_ready"] = True
        write_json(
            phase_dir / "merge_ready.json",
            {
                "phase_id": phase["phase_id"],
                "verdict": verdict,
                "pr_number": pr_number,
                "ci_status": ci_status,
                "branch": branch,
                "changed_files": list(changed),
                "blocked_files": list(blocked),
                "dry_git": dry_git,
                "recorded_at": utc_now(),
            },
        )
        append_event(run_dir, state, "MERGE_DEFERRED", phase_id=phase["phase_id"], pr_number=pr_number)
        write_state(run_dir, state)
        return True

    return finalize_phase_merge(
        run_dir,
        state,
        phase,
        verdict,
        phase_dir=phase_dir,
        config=config,
        lane=lane,
        mock_enabled=mock_enabled,
        dry_git=dry_git,
        pr_number=pr_number,
        ci_status=ci_status,
        changed=changed,
        blocked=blocked,
        required_checks=required_checks,
        github_config=github_config,
        project_config=project_config,
        execution_root=execution_root,
    )


def restore_local_repo_after_merge(
    state: dict[str, Any],
    *,
    remote: str = "origin",
) -> dict[str, Any]:
    """Post-merge repo hygiene for both worktree/parallel and in-tree modes.

    A ``gh pr merge`` run with the working directory set to a phase worktree
    (where the merged branch is the checked-out branch) can, on some gh/git
    versions, leave the *shared* repo with ``core.bare = true``. The remote merge
    still succeeds, but every subsequent phase then fails its local git
    (``fatal: this operation must be run in a work tree``) and the wave
    coordinator blocks. This guard repairs the local repository after each
    successful merge:

    1. Restore ``core.bare = false`` if a merge flipped it.
    2. Sync the local base branch to the freshly merged remote so the next phase
       branches off the correct, up-to-date base: fast-forward it when the shared
       repo is on the base branch (worktree mode), or update the base ref directly
       without checkout when it is on a phase branch (in-tree mode).

    It runs in BOTH worktree and in-tree modes; it is a no-op only under mock
    providers. Every step is best-effort: failures are recorded but never raise,
    so they cannot block an otherwise-successful merge.
    """

    report: dict[str, Any] = {"checked": False, "core_bare_restored": False, "base_synced": False}
    if bool(state.get("mock_providers")):
        return report
    report["checked"] = True
    is_bare = git(ROOT, "rev-parse", "--is-bare-repository")
    if is_bare.returncode == 0 and is_bare.stdout.strip() == "true":
        git(ROOT, "config", "core.bare", "false")
        report["core_bare_restored"] = True
    # Sync the local base branch to the freshly merged remote so the next phase
    # builds off the correct base. When the shared repo is on the base branch
    # (worktree mode), fast-forward it; when it is on a phase branch (in-tree
    # mode), update the base ref directly without checking it out.
    base_branch = detect_default_branch(root=ROOT)
    current = git(ROOT, "rev-parse", "--abbrev-ref", "HEAD")
    cur = current.stdout.strip() if current.returncode == 0 else ""
    if cur == base_branch:
        git(ROOT, "fetch", remote, base_branch)
        ff = git(ROOT, "merge", "--ff-only", f"{remote}/{base_branch}")
        report["base_synced"] = ff.returncode == 0
    elif cur:
        fetched = git(ROOT, "fetch", remote, f"{base_branch}:{base_branch}")
        report["base_synced"] = fetched.returncode == 0
    return report


def ensure_union_merge_attributes(root: Path = ROOT) -> None:
    """Union-merge ONLY the append-only README.md snapshot so parallel phases'
    README additions coexist during the pre-merge base sync. Written to the shared
    .git/info/attributes (local, never committed); idempotent and best-effort.

    Scope is deliberately limited to README.md. A blanket ``**/*.md merge=union``
    would silently concatenate conflicting same-region edits in load-bearing docs
    (specs/<ID>/*.md, campaigns/<ID>/ACCEPTANCE.md|GOAL.md|RISK_REGISTER.md,
    decisions/*.md, handoffs/<ID>.md) and, worse, defeat presync_phase_branch_with_base's
    conflict detection (which relies on a non-zero merge return to block truthfully).
    Those docs must keep normal conflict detection; the README snapshot is the only
    file parallel phases append to in the same region, so it is the only union case.
    """

    try:
        common = git(root, "rev-parse", "--git-common-dir")
        raw = common.stdout.strip() if common.returncode == 0 else ""
        gitdir = Path(raw) if raw else (root / ".git")
        if not gitdir.is_absolute():
            gitdir = (root / gitdir).resolve()
        info = gitdir / "info"
        info.mkdir(parents=True, exist_ok=True)
        attrs = info / "attributes"
        marker = "Frontier: union-merge README snapshot"
        existing = attrs.read_text(encoding="utf-8") if attrs.exists() else ""
        if marker not in existing:
            prefix = existing + ("\n" if existing and not existing.endswith("\n") else "")
            attrs.write_text(
                prefix + f"# {marker} (parallel phase README coexistence only)\n"
                "README.md merge=union\n",
                encoding="utf-8",
            )
    except Exception:
        pass


def presync_phase_branch_with_base(
    execution_root: Path,
    branch: str,
    *,
    remote: str = "origin",
) -> dict[str, Any]:
    """Merge the latest base into the phase branch so its PR is mergeable.

    Parallel phases branch off the same base and can both touch shared docs.
    README/markdown are union-merged via .git/info/attributes (written at run
    start), so doc additions from sibling phases coexist instead of colliding.
    This merges the current base into the phase worktree and pushes the result
    (a fast-forward of the phase's own remote branch), so the serial merge always
    operates on an up-to-date, conflict-free branch. A genuine non-union (e.g.
    code) conflict is aborted and reported (``conflict``) so the merge blocks
    truthfully rather than failing at gh. A non-conflict merge failure that starts
    no merge (e.g. local/untracked changes would be overwritten) is reported
    distinctly (``merge_failed`` + ``error``) instead of being mislabeled a
    conflict, so the operator gets an accurate block message.
    """

    report: dict[str, Any] = {"synced": False, "conflict": False, "pushed": False, "merge_failed": False}
    if not branch:
        return report
    base_branch = detect_default_branch(root=execution_root)
    git(execution_root, "fetch", remote, base_branch)
    merge = git(execution_root, "merge", "--no-edit", f"{remote}/{base_branch}")
    if merge.returncode != 0:
        # Distinguish a real merge conflict (leaves unmerged entries / MERGE_HEAD)
        # from a merge that never started (e.g. "would be overwritten by merge").
        # Only `git merge --abort` when a merge is actually in progress.
        combined = f"{merge.stdout}\n{merge.stderr}".upper()
        unmerged = git(execution_root, "ls-files", "-u")
        is_conflict = "CONFLICT" in combined or bool(unmerged.stdout.strip())
        if is_conflict:
            git(execution_root, "merge", "--abort")
            report["conflict"] = True
        else:
            report["merge_failed"] = True
            report["error"] = (merge.stderr or merge.stdout or "merge failed").strip()[:300]
        return report
    report["synced"] = True
    push = git(execution_root, "push", remote, f"HEAD:refs/heads/{branch}")
    report["pushed"] = push.returncode == 0
    return report


def presync_before_merge_or_block(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    execution_root: Path,
    pr_number: str | int | None = None,
) -> bool:
    """Pre-merge base sync for parallel worktree merges.

    Merges the latest base into the phase branch and pushes it, then waits for
    the PR to become mergeable again (the push re-queues required checks). Returns
    True to proceed with the merge, or False after blocking the phase (true
    conflict or push failure). A no-op outside worktree mode / under mock.
    """

    if not state.get("worktree_mode") or bool(state.get("mock_providers")) or Path(execution_root) == ROOT:
        return True
    phase_dir = provider_phase_dir(run_dir, phase)
    branch = str(phase.get("branch") or phase_branch_from_artifacts(phase_dir, state, phase))
    config = load_config(ROOT / "frontier.yaml")
    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    remote = str(github_config.get("remote") or "origin")
    presync = presync_phase_branch_with_base(Path(execution_root), branch, remote=remote)
    if (
        presync.get("conflict")
        or presync.get("merge_failed")
        or (presync.get("synced") and not presync.get("pushed"))
    ):
        if presync.get("conflict"):
            detail = "true merge conflict"
        elif presync.get("merge_failed"):
            detail = f"base sync could not start: {presync.get('error') or 'merge failed'}"
        else:
            detail = "branch push failed"
        reason = (
            f"MERGE_EXECUTION_BLOCKED: pre-merge base sync failed ({detail}); resolve and resume."
        )
        block_provider_gate(
            run_dir,
            state,
            phase,
            MERGE_EXECUTION_BLOCKED,
            reason,
            event=MERGE_EXECUTION_BLOCKED,
            source="presync_failed",
        )
        return False
    if presync.get("synced"):
        append_event(run_dir, state, "PRE_MERGE_BASE_SYNC", phase_id=phase["phase_id"], pushed=bool(presync.get("pushed")))
        # The sync push re-queues the required status checks; wait for the PR to
        # be mergeable again before attempting the merge (else gh reports the
        # check as "queued" and the merge fails).
        if pr_number is not None and not wait_pr_mergeable(pr_number, root=Path(execution_root)):
            block_provider_gate(
                run_dir,
                state,
                phase,
                MERGE_EXECUTION_BLOCKED,
                "MERGE_EXECUTION_BLOCKED: PR still not mergeable after base sync; resolve and resume.",
                event=MERGE_EXECUTION_BLOCKED,
                source="presync_not_mergeable",
            )
            return False
    return True


def finalize_phase_merge(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    verdict: str,
    *,
    phase_dir: Path,
    config: dict[str, Any],
    lane: str,
    mock_enabled: bool,
    dry_git: bool,
    pr_number: str | int | None,
    ci_status: str,
    changed: list[str],
    blocked: list[str],
    required_checks: list[str],
    github_config: dict[str, Any],
    project_config: dict[str, Any],
    execution_root: Path,
) -> bool:
    """Branch-protection -> merge gate -> merge -> cleanup for one phase.

    Shared by the inline sequential path (``post_phase_git_github``) and the
    serial merge queue in the parallel wave coordinator. The merge is the one
    serialization point; everything before it can run per-worktree in parallel.
    """

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
    if bp_result.ok or bp_result.status == "DRY_RUN":
        record_stage_checkpoint(
            run_dir,
            state,
            phase,
            "branch_protection",
            details={"status": bp_result.status, "branch": base_branch},
        )

    critical = []
    verdict_path = phase_dir / "verdict.json"
    if verdict_path.exists():
        verdict_data = read_json(verdict_path)
        critical = critical_findings_for_gate(
            str(verdict_data.get("verdict", verdict)),
            list(verdict_data.get("findings", [])),
            str(verdict_data.get("severity", "none")),
        )
    merge_changed_files = [] if dry_git else changed
    gate = evaluate_merge_gate(
        campaign_id=state["campaign_id"],
        phase_id=phase["phase_id"],
        lane=lane,
        verdict=verdict,
        ci_status=ci_status,
        changed_files=merge_changed_files,
        artifact_policy={"ok": dry_git or not blocked, "blocked_files": blocked},
        config=config,
        env=os.environ,
        dry_run=merge_dry_run or pr_number is None,
        branch_protection=bp_result,
        critical_findings=critical,
        stop_requested=stop_requested(run_dir),
    )
    write_merge_gate_artifacts(phase_dir, gate)
    phase["merge_gate_status"] = gate.status
    if gate.status in PASSING_VERDICTS:
        record_stage_checkpoint(
            run_dir,
            state,
            phase,
            "merge_gate",
            details={"merge_allowed": gate.merge_allowed, "dry_run": gate.dry_run},
        )
    if gate.status not in PASSING_VERDICTS:
        reason = "MERGE_GATE_BLOCKED: " + "; ".join(gate.reasons)
        block_provider_gate(
            run_dir,
            state,
            phase,
            MERGE_GATE_BLOCKED,
            reason,
            event="MERGE_GATE_BLOCKED",
            source="merge_gate_blocked",
        )
        return False
    if pr_number is not None:
        if not presync_before_merge_or_block(run_dir, state, phase, Path(execution_root), pr_number):
            return False
        merge_result = perform_merge(pr_number=pr_number, gate=gate, root=execution_root)
        write_merge_result_artifacts(phase_dir, merge_result)
        if merge_result_auto_armed(merge_result):
            reason = (
                "AUTO_MERGE_ARMED: GitHub auto-merge is armed for "
                f"PR {pr_number}. Resume from merge after GitHub merges the PR."
            )
            mark_auto_merge_pending(
                run_dir,
                state,
                phase,
                reason,
                event=AUTO_MERGE_ARMED,
                pr_number=pr_number,
            )
            return False
        if merge_result_is_merged(merge_result) or (merge_result.ok and not merge_result.dry_run):
            if merge_result_direct_performed(merge_result) or (
                not merge_result_is_already_merged(merge_result) and not merge_result_metadata(merge_result)
            ):
                state["auto_merge_performed"] = True
            phase["merged"] = True
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "merge",
                details={
                    "pr_number": pr_number,
                    "status": merge_result_status(merge_result),
                    "classification": merge_result_classification(merge_result),
                    "already_merged": merge_result_is_already_merged(merge_result),
                },
            )
            append_event(
                run_dir,
                state,
                "MERGED",
                phase_id=phase["phase_id"],
                pr_number=pr_number,
                classification=merge_result_classification(merge_result),
            )
            append_event(run_dir, state, "PR_MERGED", phase_id=phase["phase_id"], pr_number=pr_number)
            cleanup_phase_worktree_after_merge(run_dir, state, phase)
        elif merge_result.blocked and gate.merge_allowed:
            reason = "MERGE_EXECUTION_BLOCKED: " + (merge_result.instructions or merge_result.stderr)
            block_provider_gate(
                run_dir,
                state,
                phase,
                MERGE_EXECUTION_BLOCKED,
                reason,
                event=MERGE_EXECUTION_BLOCKED,
                source="merge_execution_blocked",
            )
            return False
    return True


def find_state_phase(state: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in state.get("phases", []):
        if phase.get("phase_id") == phase_id:
            return phase
    raise ValueError(f"Run state is missing phase {phase_id}.")


def resume_artifact_policy(config: dict[str, Any], changed: list[str], *, artifact_source: str) -> dict[str, Any]:
    artifacts = config.get("artifacts") if isinstance(config.get("artifacts"), dict) else {}
    allow_patterns = list(artifacts.get("allow_commit", [])) if isinstance(artifacts, dict) else []
    forbid_patterns = list(artifacts.get("forbid_commit", [])) if isinstance(artifacts, dict) else []
    placeholder_exceptions = artifacts.get("placeholder_exceptions") if isinstance(artifacts, dict) else None
    placeholder_dirs = artifacts.get("placeholder_dirs") if isinstance(artifacts, dict) else None
    if not isinstance(placeholder_exceptions, list):
        placeholder_exceptions = None
    if not isinstance(placeholder_dirs, list):
        placeholder_dirs = None
    allowed, blocked = curate_commit_paths(
        changed,
        allow_patterns=allow_patterns,
        forbid_patterns=forbid_patterns,
        placeholder_exceptions=placeholder_exceptions,
        placeholder_dirs=placeholder_dirs,
    )
    return {
        "ok": not blocked,
        "artifact_source": artifact_source,
        "changed_files": changed,
        "allowed_files": allowed,
        "blocked_files": blocked,
    }


def recorded_phase_commit_sha(phase_dir: Path, phase: dict[str, Any], state: dict[str, Any]) -> str | None:
    git_phase = read_json_if_exists(phase_dir / "git_phase.json")
    candidates = [
        phase.get("commit_sha"),
        state.get("commit_sha"),
        read_stripped_if_exists(phase_dir / "commit_sha.txt"),
        git_phase.get("commit_sha"),
    ]
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return None


def resume_head_mismatch_allowed() -> bool:
    return os.environ.get("FRONTIER_ALLOW_RESUME_HEAD_MISMATCH") == "1"


def pr_metadata(result: GitHubResult) -> dict[str, Any]:
    metadata = result.metadata if isinstance(result.metadata, dict) else {}
    data = metadata.get("pr")
    return data if isinstance(data, dict) else {}


def pr_is_merged(data: dict[str, Any]) -> bool:
    return str(data.get("state") or "").upper() == "MERGED" or bool(data.get("mergedAt"))


def validate_resume_pr_head(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    phase_dir: Path,
    *,
    pr_data: dict[str, Any],
) -> bool:
    expected = recorded_phase_commit_sha(phase_dir, phase, state)
    actual = str(pr_data.get("headRefOid") or "").strip()
    match = True
    reason = ""
    if expected:
        match = bool(actual) and actual.lower() == expected.lower()
        if not match:
            reason = (
                "RESUME_PRECONDITION_FAILED: PR headRefOid does not match recorded phase commit_sha. "
                "Set FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1 only after manually verifying the PR head."
            )
    payload = {
        "status": "PASS" if match else "MISMATCH",
        "expected_commit_sha": expected,
        "headRefOid": actual,
        "override_allowed": resume_head_mismatch_allowed(),
        "recorded_at": utc_now(),
    }
    write_json(phase_dir / "resume_head_check.json", payload)
    if match:
        return True
    if resume_head_mismatch_allowed():
        append_event(
            run_dir,
            state,
            "RESUME_HEAD_MISMATCH_OVERRIDDEN",
            phase_id=phase["phase_id"],
            expected_commit_sha=expected,
            headRefOid=actual,
        )
        return True
    write_resume_precondition_failure(run_dir, state, phase, reason, precondition=payload)
    return False


def finish_targeted_resume(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    verdict: str,
    from_stage: str,
    reason: str | None = None,
) -> None:
    note = reason or f"Targeted resume from {from_stage} completed for {phase['phase_id']}; no later phases were started."
    finish_provider_phase(run_dir, state, phase, verdict, event="RESUME_PHASE_PASS", reason=f"Resumed from {from_stage}.")
    state["status"] = "STOPPED"
    state["stop_requested"] = True
    write_provider_stop(run_dir, state, note)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, note)


def write_resume_precondition_failure(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    reason: str,
    *,
    precondition: dict[str, Any] | None = None,
) -> None:
    phase_dir = provider_phase_dir(run_dir, phase)
    payload = {
        "status": RESUME_PRECONDITION_FAILED,
        "phase_id": phase["phase_id"],
        "reason": reason,
        "precondition": precondition or {},
        "recorded_at": utc_now(),
    }
    write_json(phase_dir / "resume_precondition_failed.json", payload)
    (phase_dir / "resume_precondition_failed.md").write_text(
        "# Resume Precondition Failed\n\n" + reason + "\n",
        encoding="utf-8",
    )
    set_provider_phase_status(phase, RESUME_PRECONDITION_FAILED)
    phase["status_reason"] = reason
    state["status"] = RESUME_PRECONDITION_FAILED
    state["stop_requested"] = True
    state["current_phase_id"] = phase["phase_id"]
    append_event(
        run_dir,
        state,
        RESUME_PRECONDITION_FAILED,
        phase_id=phase["phase_id"],
        reason=reason,
    )
    write_provider_stop(run_dir, state, reason)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, reason)
    progress(run_dir, f"{phase['phase_id']} resume precondition failed.")


def run_deterministic_resume_gates(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    from_stage: str,
    no_provider_replay: bool,
    execution_root: Path = ROOT,
) -> bool:
    del no_provider_replay
    phase_dir = provider_phase_dir(run_dir, phase)
    config = load_config(ROOT / "frontier.yaml")
    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    project_config = config.get("project") if isinstance(config.get("project"), dict) else {}
    lane = str(phase.get("lane") or "green").lower()
    verdict_data = read_json(phase_dir / "verdict.json")
    verdict = str(verdict_data.get("verdict", "BLOCKED"))
    required_checks = phase_required_checks(phase, config)
    mock_enabled = bool(state.get("mock_providers"))
    pr_number = recover_pr_number(phase_dir, phase, state)
    if pr_number is None:
        write_resume_precondition_failure(
            run_dir,
            state,
            phase,
            "RESUME_PRECONDITION_FAILED: pr_create.json or state must contain a valid PR number.",
        )
        return False

    if mock_enabled:
        changed = changed_files_from_artifacts(phase_dir)
        artifact_source = "run_artifacts_mock"
    else:
        state["github_operations_performed"] = True
        state["network_used"] = True
        pr_view_result = view_pr(pr_number, root=execution_root)
        write_github_result(phase_dir / "resume_pr_view.json", pr_view_result)
        if pr_view_result.blocked:
            write_resume_precondition_failure(
                run_dir,
                state,
                phase,
                "RESUME_PRECONDITION_FAILED: live PR metadata could not be read.",
                precondition=pr_view_result.to_dict(),
            )
            return False
        pr_data = pr_metadata(pr_view_result)
        if pr_is_merged(pr_data):
            phase["pr_number"] = pr_number
            phase["merged"] = True
            merge_method = str(github_config.get("merge_method") or "squash")
            merge_command = ["gh", "pr", "merge", str(pr_number), f"--{merge_method}", "--delete-branch"]
            already_merged_result = GitHubResult(
                "merge_pr",
                False,
                merge_command,
                0,
                pr_view_result.stdout,
                pr_view_result.stderr,
                metadata={
                    "status": ALREADY_MERGED,
                    "classification": "already_merged",
                    "merged": True,
                    "already_merged": True,
                    "auto_merge_armed": False,
                    "direct_merge_performed": False,
                    "command": merge_command,
                    "pre_view_command": pr_view_result.command,
                    "pre_view_return_code": pr_view_result.return_code,
                    "pre_view_stdout": pr_view_result.stdout,
                    "pre_view_stderr": pr_view_result.stderr,
                    "pre_pr": pr_data,
                },
            )
            write_merge_result_artifacts(phase_dir, already_merged_result)
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "merge",
                details={
                    "resume": True,
                    "pr_number": pr_number,
                    "already_merged": True,
                    "status": ALREADY_MERGED,
                    "classification": "already_merged",
                },
            )
            append_event(
                run_dir,
                state,
                "MERGED",
                phase_id=phase["phase_id"],
                pr_number=pr_number,
                classification="already_merged",
            )
            append_event(run_dir, state, "RESUME_PR_ALREADY_MERGED", phase_id=phase["phase_id"], pr_number=pr_number)
            cleanup_phase_worktree_after_merge(run_dir, state, phase)
            finish_targeted_resume(
                run_dir,
                state,
                phase,
                verdict=verdict,
                from_stage=from_stage,
                reason=f"PR {pr_number} is already merged; marked {phase['phase_id']} complete.",
            )
            return True
        if not validate_resume_pr_head(run_dir, state, phase, phase_dir, pr_data=pr_data):
            return False
        pr_diff_result = list_pr_diff_files(pr_number, root=execution_root)
        write_github_result(phase_dir / "resume_pr_diff.json", pr_diff_result)
        if pr_diff_result.blocked:
            changed = changed_files_from_artifacts(phase_dir)
            artifact_source = "run_artifacts_fallback"
            append_event(
                run_dir,
                state,
                "RESUME_PR_DIFF_FALLBACK",
                phase_id=phase["phase_id"],
                pr_number=pr_number,
                reason=pr_diff_result.instructions or pr_diff_result.stderr,
            )
        else:
            files = pr_diff_result.metadata.get("files") if isinstance(pr_diff_result.metadata, dict) else []
            changed = [str(item) for item in files] if isinstance(files, list) else []
            artifact_source = "pr_diff"

    artifact_result = resume_artifact_policy(config, changed, artifact_source=artifact_source)
    write_json(phase_dir / "resume_artifact_policy.json", artifact_result)
    append_event(
        run_dir,
        state,
        "RESUME_ARTIFACT_POLICY",
        phase_id=phase["phase_id"],
        artifact_source=artifact_source,
        changed_files=len(changed),
        blocked_files=artifact_result["blocked_files"],
    )

    if mock_enabled:
        ci_result = classify_ci_checks(
            [{"name": check or "mock-ci", "state": "SUCCESS", "bucket": "pass"} for check in (required_checks or ["mock-ci"])],
            required_checks=required_checks,
        )
    else:
        ci_result = wait_for_ci(
            pr_number,
            timeout_seconds=int(github_config.get("ci_timeout_seconds", 900)),
            poll_seconds=int(github_config.get("ci_poll_seconds", 15)),
            required_checks=required_checks,
            root=execution_root,
        )
    write_ci_status_artifacts(phase_dir, ci_result)
    phase["ci_status"] = ci_result.state
    append_event(run_dir, state, "RESUME_CI_RERUN", phase_id=phase["phase_id"], ci_status=ci_result.state)
    if ci_result.state == CI_SUCCESS:
        record_stage_checkpoint(run_dir, state, phase, "ci", details={"resume": True, "pr_number": pr_number})
    if github_config.get("require_ci", True) and ci_result.state != CI_SUCCESS:
        if phase.get("status") in MERGE_PENDING_STATUSES:
            reason = f"AUTO_MERGE_ARMED: PR {pr_number} is still waiting for CI status {ci_result.state}."
            mark_auto_merge_pending(
                run_dir,
                state,
                phase,
                reason,
                event="RESUME_AUTO_MERGE_PENDING",
                pr_number=pr_number,
            )
            return True
        block_provider_gate(
            run_dir,
            state,
            phase,
            CI_BLOCKED,
            f"CI_BLOCKED: CI status was {ci_result.state}.",
            event="CI_BLOCKED",
            source="resume_ci_blocked",
        )
        return False

    base_branch = str(project_config.get("default_branch") or "main") if mock_enabled else detect_default_branch(root=execution_root)
    bp_result = inspect_branch_protection(
        branch=base_branch,
        required_checks=required_checks,
        require_branch_protection=bool(github_config.get("require_branch_protection", True)),
        root=execution_root,
        dry_run=mock_enabled and bool(github_config.get("allow_unprotected_dry_run", True)),
    )
    write_branch_protection_artifacts(phase_dir, bp_result)
    append_event(
        run_dir,
        state,
        "RESUME_BRANCH_PROTECTION_RERUN",
        phase_id=phase["phase_id"],
        status=bp_result.status,
    )
    if bp_result.ok or bp_result.status == "DRY_RUN":
        record_stage_checkpoint(
            run_dir,
            state,
            phase,
            "branch_protection",
            details={"resume": True, "status": bp_result.status, "branch": base_branch},
        )
    elif phase.get("status") in MERGE_PENDING_STATUSES:
        reason = f"AUTO_MERGE_ARMED: PR {pr_number} is still waiting for branch protection status {bp_result.status}."
        mark_auto_merge_pending(
            run_dir,
            state,
            phase,
            reason,
            event="RESUME_AUTO_MERGE_PENDING",
            pr_number=pr_number,
        )
        return True

    critical = critical_findings_for_gate(
        str(verdict_data.get("verdict", verdict)),
        list(verdict_data.get("findings", [])),
        str(verdict_data.get("severity", "none")),
    )
    allow_automerge = os.environ.get("FRONTIER_ALLOW_AUTOMERGE", "").lower() in {"1", "true", "yes", "on"}
    merge_dry_run = mock_enabled or os.environ.get("FRONTIER_MERGE_DRY_RUN") == "1" or not allow_automerge
    gate = evaluate_merge_gate(
        campaign_id=state["campaign_id"],
        phase_id=phase["phase_id"],
        lane=lane,
        verdict=verdict,
        ci_status=ci_result.state,
        changed_files=changed,
        artifact_policy=artifact_result,
        config=config,
        env=os.environ,
        dry_run=merge_dry_run,
        branch_protection=bp_result,
        critical_findings=critical,
        stop_requested=stop_requested(run_dir),
    )
    write_merge_gate_artifacts(phase_dir, gate)
    phase["merge_gate_status"] = gate.status
    append_event(
        run_dir,
        state,
        "RESUME_MERGE_GATE_RERUN",
        phase_id=phase["phase_id"],
        status=gate.status,
        merge_allowed=gate.merge_allowed,
        from_stage=from_stage,
    )
    if gate.status in PASSING_VERDICTS:
        record_stage_checkpoint(
            run_dir,
            state,
            phase,
            "merge_gate",
            details={"resume": True, "merge_allowed": gate.merge_allowed, "dry_run": gate.dry_run},
        )
    if gate.status not in PASSING_VERDICTS:
        reason = "MERGE_GATE_BLOCKED: " + "; ".join(gate.reasons)
        block_provider_gate(
            run_dir,
            state,
            phase,
            MERGE_GATE_BLOCKED,
            reason,
            event="MERGE_GATE_BLOCKED",
            source="resume_merge_gate_blocked",
        )
        return False

    if gate.merge_allowed:
        if not presync_before_merge_or_block(run_dir, state, phase, Path(execution_root), pr_number):
            return False
        merge_result = perform_merge(pr_number=pr_number, gate=gate, root=execution_root)
        write_merge_result_artifacts(phase_dir, merge_result)
        append_event(
            run_dir,
            state,
            "RESUME_PERFORM_MERGE",
            phase_id=phase["phase_id"],
            pr_number=pr_number,
            dry_run=merge_result.dry_run,
            blocked=merge_result.blocked,
            status=merge_result_status(merge_result),
            classification=merge_result_classification(merge_result),
        )
        if merge_result_auto_armed(merge_result):
            reason = (
                "AUTO_MERGE_ARMED: GitHub auto-merge is armed for "
                f"PR {pr_number}. Resume from merge after GitHub merges the PR."
            )
            mark_auto_merge_pending(
                run_dir,
                state,
                phase,
                reason,
                event="RESUME_AUTO_MERGE_ARMED",
                pr_number=pr_number,
            )
            return True
        if merge_result_is_merged(merge_result) or (merge_result.ok and not merge_result.dry_run):
            if merge_result_direct_performed(merge_result) or (
                not merge_result_is_already_merged(merge_result) and not merge_result_metadata(merge_result)
            ):
                state["auto_merge_performed"] = True
            phase["merged"] = True
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "merge",
                details={
                    "resume": True,
                    "pr_number": pr_number,
                    "status": merge_result_status(merge_result),
                    "classification": merge_result_classification(merge_result),
                    "already_merged": merge_result_is_already_merged(merge_result),
                },
            )
            append_event(
                run_dir,
                state,
                "MERGED",
                phase_id=phase["phase_id"],
                pr_number=pr_number,
                classification=merge_result_classification(merge_result),
            )
            append_event(run_dir, state, "PR_MERGED", phase_id=phase["phase_id"], pr_number=pr_number)
            cleanup_phase_worktree_after_merge(run_dir, state, phase)
        elif merge_result.blocked:
            reason = "MERGE_EXECUTION_BLOCKED: " + (merge_result.instructions or merge_result.stderr)
            block_provider_gate(
                run_dir,
                state,
                phase,
                MERGE_EXECUTION_BLOCKED,
                reason,
                event=MERGE_EXECUTION_BLOCKED,
                source="resume_merge_execution_blocked",
            )
            return False

    finish_targeted_resume(run_dir, state, phase, verdict=verdict, from_stage=from_stage)
    return True


def _read_phase_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def execute_provider_phase(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
    *,
    defer_merge: bool = False,
) -> bool:
    mock_enabled = bool(state.get("mock_providers"))
    phase_id = phase["phase_id"]
    phase_dir = provider_phase_dir(run_dir, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)
    execution_root = ROOT

    if state.get("worktree_mode"):
        if phase.get("branch") and phase.get("worktree_path"):
            if not mock_enabled:
                execution_root = Path(str(phase["worktree_path"]))
            append_event(
                run_dir,
                state,
                "WORKTREE_RESUME",
                phase_id=phase_id,
                branch=phase["branch"],
                path=phase["worktree_path"],
            )
        else:
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

    if phase.get("status") in PROVIDER_WAITING_STATUSES:
        if provider_replay_disabled():
            block_provider_run(
                run_dir,
                state,
                phase,
                RESUME_PRECONDITION_FAILED,
                "FRONTIER_NO_PROVIDER_REPLAY=1 prevents resuming a provider-dependent stage.",
            )
            return False
        resume_stage = str(phase.get("resume_stage") or phase.get("provider_limit", {}).get("safe_resume_stage") or "")
        mapped_status = PROVIDER_RESUME_STATUS_BY_STAGE.get(resume_stage)
        if not mapped_status:
            block_provider_run(
                run_dir,
                state,
                phase,
                RESUME_PRECONDITION_FAILED,
                f"Cannot resume provider limit from unknown stage {resume_stage!r}.",
            )
            return False
        set_provider_phase_status(phase, mapped_status)
        phase.pop("status_reason", None)
        append_event(
            run_dir,
            state,
            "PROVIDER_LIMIT_RESUME",
            phase_id=phase_id,
            resume_stage=resume_stage,
            mapped_status=mapped_status,
        )
        write_state(run_dir, state)

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
                if handle_provider_nonzero(
                    run_dir,
                    state,
                    phase,
                    provider="claude",
                    stage="spec",
                    result=result,
                ):
                    return False
                write_provider_failure(phase_dir / "spec.md", "Claude Spec Generation Failed", result)
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="spec_generation_error")
                block_provider_run(run_dir, state, phase, "BLOCKED", "Claude spec generation failed.")
                return False
            spec_text = result.stdout
        (phase_dir / "spec.md").write_text(spec_text, encoding="utf-8")
        record_stage_checkpoint(run_dir, state, phase, "spec")
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
        if not prepare_phase_branch_for_execution(run_dir, state, phase, execution_root=execution_root):
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
                if handle_provider_nonzero(
                    run_dir,
                    state,
                    phase,
                    provider="codex",
                    stage="execute",
                    result=result,
                ):
                    return False
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="executor_error")
                block_provider_run(run_dir, state, phase, "BLOCKED", "Codex executor returned nonzero.")
                return False
        (phase_dir / "executor_output.md").write_text(executor_text, encoding="utf-8")
        quarantine_executor_review_artifacts(phase_dir, run_dir, state, phase)
        record_stage_checkpoint(run_dir, state, phase, "execute")
        set_provider_phase_status(phase, "EXECUTED")
        append_event(run_dir, state, "EXECUTED", phase_id=phase_id)
        write_state(run_dir, state)
        write_provider_summary(run_dir, state, f"{phase_id} executed.")
    else:
        executor_text = _read_phase_text(phase_dir / "executor_output.md")

    if phase.get("status") in {"EXECUTED", "REPAIRED"}:
        quarantine_executor_review_artifacts(phase_dir, run_dir, state, phase)
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
            if verdict in PROVIDER_WAITING_STATUSES:
                return False
            if verdict not in PASSING_VERDICTS:
                block_provider_run(run_dir, state, phase, "BLOCKED", "Repair attempts exhausted after validation failure.")
                return False
        else:
            record_stage_checkpoint(run_dir, state, phase, "validate")
            set_provider_phase_status(phase, "VALIDATED")
            append_event(run_dir, state, "VALIDATED", phase_id=phase_id)
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, f"{phase_id} validated.")
    validation_text = _read_phase_text(phase_dir / "validation.md")

    if phase.get("status") == "VALIDATED":
        quarantine_executor_review_artifacts(phase_dir, run_dir, state, phase)
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
                if handle_provider_nonzero(
                    run_dir,
                    state,
                    phase,
                    provider="claude",
                    stage="review",
                    result=result,
                ):
                    return False
                (phase_dir / "review.md").write_text(review_text, encoding="utf-8")
                write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="claude_review_error")
                block_provider_run(run_dir, state, phase, "BLOCKED", "Claude review returned nonzero.")
                return False
        review_path = phase_dir / "review.md"
        review_path.write_text(review_text, encoding="utf-8")
        parsed_verdict = parse_review_text(review_text, review_path)
        verdict = parsed_verdict.verdict
        write_provider_verdict(phase_dir, state, phase, verdict, source="review", parsed=parsed_verdict)
        record_stage_checkpoint(run_dir, state, phase, "review")
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
    if verdict in PROVIDER_WAITING_STATUSES:
        return False
    if verdict not in PASSING_VERDICTS:
        block_provider_run(run_dir, state, phase, "BLOCKED", f"Review verdict was {verdict}.")
        return False

    handoff_text = provider_handoff_text(phase, verdict, mock_enabled)
    (phase_dir / "handoff.md").write_text(handoff_text, encoding="utf-8")
    workflow2 = runtime_config().raw.get("workflow2", {})
    if not isinstance(workflow2, dict) or bool(workflow2.get("semantic_done_check_required", True)):
        existing_done = read_json_if_exists(phase_dir / "done_check.json")
        # Only reuse a prior done-check when it is at least as new as this
        # execution's executor output. A re-executed phase rewrites
        # executor_output.md, which makes any stale done_check.json (e.g. a
        # BLOCKED verdict from an earlier attempt under a since-fixed
        # environment fault) older — so it is re-run fresh instead of cached.
        _done_path = phase_dir / "done_check.json"
        _exec_path = phase_dir / "executor_output.md"
        _done_is_fresh = (
            bool(existing_done.get("verdict"))
            and _done_path.exists()
            and (not _exec_path.exists() or _done_path.stat().st_mtime >= _exec_path.stat().st_mtime)
        )
        if _done_is_fresh:
            done_text = _read_phase_text(phase_dir / "done_check.md")
            done_verdict = str(existing_done.get("verdict"))
            record_stage_checkpoint(
                run_dir,
                state,
                phase,
                "done_check",
                details={"reused": True, "verdict": done_verdict},
            )
            append_event(run_dir, state, "DONE_CHECK_REUSED", phase_id=phase_id, verdict=done_verdict)
        else:
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
                    if handle_provider_nonzero(
                        run_dir,
                        state,
                        phase,
                        provider="claude",
                        stage="done_check",
                        result=result,
                    ):
                        return False
                    (phase_dir / "done_check.md").write_text(done_text, encoding="utf-8")
                    write_provider_verdict(phase_dir, state, phase, "BLOCKED", source="done_check_error")
                    block_provider_run(run_dir, state, phase, "BLOCKED", "Claude done-check returned nonzero.")
                    return False
            done_verdict = write_done_check_result(phase_dir, state, phase, done_text)
            record_stage_checkpoint(run_dir, state, phase, "done_check")
            append_event(run_dir, state, "DONE_CHECK", phase_id=phase_id, verdict=done_verdict)
        if done_verdict == "REWORK":
            verdict = run_provider_repair_loop(
                run_dir, state, phase, spec_text, done_text, validation_text, execution_root=execution_root
            )
            if verdict in PROVIDER_WAITING_STATUSES:
                return False
            if verdict not in PASSING_VERDICTS:
                block_provider_run(run_dir, state, phase, "BLOCKED", "Repair attempts exhausted after done-check.")
                return False
        elif done_verdict == "BLOCKED":
            block_provider_run(run_dir, state, phase, "BLOCKED", "Done-check returned BLOCKED.")
            return False
        elif done_verdict == "PASS_WITH_WARNINGS" and verdict == "PASS":
            verdict = "PASS_WITH_WARNINGS"
            write_provider_verdict(phase_dir, state, phase, verdict, source="done_check_warning")

    if not post_phase_git_github(
        run_dir, state, phase, verdict, execution_root=execution_root, defer_merge=defer_merge
    ):
        return False
    if defer_merge:
        # Build + PR + CI complete; phase is MERGE_READY. The serial merge queue
        # in the wave coordinator finalizes the merge and marks the phase PASS.
        return True
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
                if handle_provider_nonzero(
                    run_dir,
                    state,
                    phase,
                    provider="codex",
                    stage="repair",
                    result=result,
                ):
                    return str(phase.get("status") or WAITING_PROVIDER_LIMIT)
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
                if handle_provider_nonzero(
                    run_dir,
                    state,
                    phase,
                    provider="claude",
                    stage="repair_review",
                    result=result,
                ):
                    return str(phase.get("status") or WAITING_PROVIDER_LIMIT)
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
            status = classify_provider_nonzero("claude", result.stdout, result.stderr, result.returncode)
            if status in PROVIDER_WAITING_STATUSES:
                wait_campaign_provider_limit(
                    run_dir,
                    state,
                    provider="claude",
                    stage="campaign_done_check",
                    result=result,
                    status=status,
                )
                return status
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


@contextlib.contextmanager
def _parallel_mode():
    """Make per-phase block helpers local for the duration of a wave coordinator."""
    global _PARALLEL_MODE_ACTIVE
    previous = _PARALLEL_MODE_ACTIVE
    _PARALLEL_MODE_ACTIVE = True
    try:
        yield
    finally:
        _PARALLEL_MODE_ACTIVE = previous


def prepare_wave_worktrees(run_dir: Path, state: dict[str, Any], wave: list[dict[str, Any]]) -> None:
    """Serially create one Frontier worktree per wave phase before parallel build.

    Worktree creation mutates the shared main-repo worktree registry, so it is
    done here (serially) rather than racing inside concurrent build threads. The
    build path then re-binds the pre-created worktree instead of creating one.
    """

    if not state.get("worktree_mode") or bool(state.get("mock_providers")):
        return
    manager = WorktreeManager(ROOT, runtime_config().worktree_root)
    for phase in wave:
        if phase.get("branch") and phase.get("worktree_path"):
            continue
        try:
            plan = manager.create(state["campaign_id"], phase["phase_id"], phase.get("name"), dry_run=False)
        except FileExistsError:
            plan = manager.plan(state["campaign_id"], phase["phase_id"], phase.get("name"))
        phase["branch"] = plan.branch
        phase["worktree_path"] = plan.path
        phase_dir = provider_phase_dir(run_dir, phase)
        phase_dir.mkdir(parents=True, exist_ok=True)
        (phase_dir / "worktree_plan.json").write_text(
            json.dumps(plan.__dict__, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        append_event(run_dir, state, "WORKTREE_PLAN", phase_id=phase["phase_id"], branch=plan.branch, path=plan.path)
    write_state(run_dir, state)


def _build_wave_phase(run_dir: Path, state: dict[str, Any], phase: dict[str, Any]) -> bool:
    try:
        return execute_provider_phase(run_dir, state, phase, defer_merge=True)
    except Exception as error:  # defensive: keep one phase's crash from killing the wave
        finish_provider_phase(
            run_dir,
            state,
            phase,
            "BLOCKED",
            event="PHASE_STOPPED",
            reason=f"unexpected error during parallel build: {error}",
        )
        return False


def run_wave_build(
    run_dir: Path,
    state: dict[str, Any],
    wave: list[dict[str, Any]],
    scheduler: SchedulerSettings,
) -> None:
    """Build every phase in the wave concurrently (merge deferred)."""

    for phase in wave:
        # Coordinator-only means phase branches NEVER write ACTIVE_CAMPAIGN.md,
        # regardless of wave width (a width-1 bootstrap wave in a parallel run is
        # still coordinator-owned). Gate on policy, not width.
        if scheduler.update_active_campaign == "coordinator_only":
            phase["suppress_active_pointer"] = True
        phase["wave_id"] = state.get("wave_counter", 0)
    workers = max(1, min(scheduler.max_parallel_phases, len(wave)))
    if workers == 1 or len(wave) == 1:
        for phase in wave:
            _build_wave_phase(run_dir, state, phase)
        return
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="wave") as pool:
        futures = {pool.submit(_build_wave_phase, run_dir, state, phase): phase for phase in wave}
        for future in futures:
            future.result()


def finalize_merge_for_phase(
    run_dir: Path,
    state: dict[str, Any],
    phase: dict[str, Any],
) -> bool:
    """Serial merge of one MERGE_READY phase, reconstructing context from artifacts."""

    phase_dir = provider_phase_dir(run_dir, phase)
    config = load_config(ROOT / "frontier.yaml")
    github_config = config.get("github") if isinstance(config.get("github"), dict) else {}
    project_config = config.get("project") if isinstance(config.get("project"), dict) else {}
    lane = str(phase.get("lane") or "green").lower()
    mock_enabled = bool(state.get("mock_providers"))
    dry_git = mock_enabled and os.environ.get("FRONTIER_MOCK_COMMIT") != "1"
    merge_ready = read_json_if_exists(phase_dir / "merge_ready.json")
    verdict = str(
        merge_ready.get("verdict")
        or read_json_if_exists(phase_dir / "verdict.json").get("verdict")
        or "PASS"
    )
    pr_number = merge_ready.get("pr_number") or recover_pr_number(phase_dir, phase, state)
    ci_status = str(merge_ready.get("ci_status") or phase.get("ci_status") or (CI_SUCCESS if mock_enabled else "NOT_FOUND"))
    changed = list(merge_ready.get("changed_files") or changed_files_from_artifacts(phase_dir))
    blocked = list(merge_ready.get("blocked_files") or [])
    required_checks = phase_required_checks(phase, config)
    execution_root = ROOT
    worktree_path = str(phase.get("worktree_path") or "").strip()
    if state.get("worktree_mode") and not mock_enabled and worktree_path and Path(worktree_path).exists():
        execution_root = Path(worktree_path)
    ok = finalize_phase_merge(
        run_dir,
        state,
        phase,
        verdict,
        phase_dir=phase_dir,
        config=config,
        lane=lane,
        mock_enabled=mock_enabled,
        dry_git=dry_git,
        pr_number=pr_number,
        ci_status=ci_status,
        changed=changed,
        blocked=blocked,
        required_checks=required_checks,
        github_config=github_config,
        project_config=project_config,
        execution_root=execution_root,
    )
    if not ok:
        return False
    finish_provider_phase(run_dir, state, phase, verdict, event="PHASE_PASS")
    return True


def run_wave_merge(
    run_dir: Path,
    state: dict[str, Any],
    wave: list[dict[str, Any]],
    scheduler: SchedulerSettings,
) -> None:
    """Merge build-complete (MERGE_READY) phases one at a time, in queue order."""

    merge_ready = [p for p in wave if p.get("status") == MERGE_READY]
    if not merge_ready:
        return
    order = serial_merge_order(merge_ready)
    by_id = {p["phase_id"]: p for p in merge_ready}
    append_event(run_dir, state, "MERGE_QUEUE_START", order=order)
    for phase_id in order:
        if (run_dir / "STOP").exists():
            append_event(run_dir, state, "MERGE_QUEUE_STOP", reason="STOP file present", remaining=phase_id)
            break
        phase = by_id[phase_id]
        merged_ok = finalize_merge_for_phase(run_dir, state, phase)
        if merged_ok and scheduler.update_active_campaign == "coordinator_only":
            coordinator_update_active_campaign(run_dir, state, completed_phase=phase)


def coordinator_update_active_campaign(
    run_dir: Path,
    state: dict[str, Any],
    *,
    completed_phase: dict[str, Any] | None = None,
) -> None:
    """Coordinator-owned ACTIVE_CAMPAIGN pointer write (local-only, never racy).

    In parallel waves the phase branches do not touch ACTIVE_CAMPAIGN.md (see
    ``suppress_active_pointer``); the coordinator instead records the projected
    pointer to a run-local artifact for visibility. The tracked ACTIVE_CAMPAIGN.md
    is refreshed by the next sequential phase / closeout, exactly as the harness
    already reconstructs the pointer from run state.
    """

    text = render_active_campaign_pointer(
        state,
        completed_phase_id=(completed_phase or {}).get("phase_id"),
        completed_status=(completed_phase or {}).get("status"),
        note="Projected by the parallel wave coordinator.",
    )
    (run_dir / "ACTIVE_CAMPAIGN.projected.md").write_text(text, encoding="utf-8")
    append_event(
        run_dir,
        state,
        "ACTIVE_CAMPAIGN_POINTER_COORDINATOR",
        phase_id=(completed_phase or {}).get("phase_id"),
    )


def wave_integration_verify(run_dir: Path, state: dict[str, Any], wave_index: int) -> bool:
    if bool(state.get("mock_providers")):
        append_event(run_dir, state, "WAVE_INTEGRATION_VERIFY", wave=wave_index, mode="mock_skip", ok=True)
        return True
    ok, text = run_validation_commands(root=ROOT)
    (run_dir / f"wave_{wave_index}_verify.md").write_text(text, encoding="utf-8")
    append_event(run_dir, state, "WAVE_INTEGRATION_VERIFY", wave=wave_index, ok=ok)
    return ok


def finalize_completed_campaign(run_dir: Path, state: dict[str, Any]) -> int:
    # Structural guard: never declare COMPLETE while any phase is built-but-unmerged
    # (MERGE_READY) or otherwise not passing. run_campaign_done_check is an LLM/mock
    # judge that does not structurally detect an unmerged built phase, so a silent
    # incorrect completion would otherwise be possible after a mid-merge STOP/crash.
    not_passing = [
        p["phase_id"] for p in state.get("phases", []) if p.get("status") not in PASSING_VERDICTS
    ]
    if not_passing:
        reason = (
            "Cannot complete: phases are not passing (e.g. built-but-unmerged): "
            f"{', '.join(not_passing)}. Resume to merge or resolve them."
        )
        state["status"] = "BLOCKED"
        state["stop_requested"] = True
        append_event(run_dir, state, "RUN_COMPLETE_BLOCKED", not_passing=not_passing)
        write_provider_stop(run_dir, state, reason)
        write_state(run_dir, state)
        write_provider_summary(run_dir, state, reason)
        print(f"Campaign completion blocked by non-passing phases at {run_dir.relative_to(ROOT)}")
        return 0
    done_verdict = run_campaign_done_check(run_dir, state)
    if done_verdict in PROVIDER_WAITING_STATUSES:
        print(f"Stopped provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
        return 0
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
    coordinator_update_active_campaign(run_dir, state)
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, "All parsed phases completed.")
    progress(run_dir, "Run completed.")
    print(f"Completed provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
    return 0


MAX_GATE_RETRIES = 2


def drain_gate_blocked_phases(run_dir: Path, state: dict[str, Any], max_rounds: int = MAX_GATE_RETRIES) -> list[str]:
    """Self-heal: retry phases left gate-blocked (CI/merge-gate/merge-execution)
    by routing each through the gate-retry path (which runs presync + CI re-wait
    + merge) using its own worktree. Bounded by ``max_rounds`` and by lack of
    progress so a persistent block stops cleanly instead of looping. This is what
    lets the parallel coordinator recover from a transient block (CI revalidation
    timing, a moved base) and lets a plain resume retry a gate-blocked phase
    instead of orphaning it and its dependents. Pre-PR blocks (e.g. PUSH_BLOCKED)
    have no PR yet and are skipped here. Returns phase_ids still gate-blocked.

    Runs only in the coordinator/main thread between waves, so no worker threads
    touch the run state concurrently while it mutates it.
    """

    for _round in range(max(1, max_rounds)):
        if (run_dir / "STOP").exists():
            break
        drainable_statuses = set(GATE_BLOCKED_STATUSES)
        if resume_head_mismatch_allowed():
            # An authorized head-mismatch (FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1)
            # otherwise strands the phase in RESUME_PRECONDITION_FAILED, which is
            # not a gate-blocked status, so the drain skips it and dag_wave
            # SCHEDULE_DEADLOCKs. With the override armed, treat it as drainable:
            # the gate re-run re-checks the PR head (now overridden) and merges.
            drainable_statuses.add(RESUME_PRECONDITION_FAILED)
        blocked = [p for p in state.get("phases", []) if p.get("status") in drainable_statuses]
        if not blocked:
            break
        progressed = False
        for phase in blocked:
            phase_dir = provider_phase_dir(run_dir, phase)
            if recover_pr_number(phase_dir, phase, state) is None:
                continue
            worktree_path = str(phase.get("worktree_path") or "").strip()
            execution_root = (
                Path(worktree_path)
                if state.get("worktree_mode") and worktree_path and Path(worktree_path).exists()
                else ROOT
            )
            append_event(
                run_dir, state, "GATE_RETRY_DRAIN", phase_id=phase["phase_id"], status=phase.get("status")
            )
            # Re-validate from CI so a phase blocked on a (now-fixed) CI failure
            # re-waits the checks; for merge-stage blocks CI is already green so
            # wait_for_ci returns quickly. Both then run presync + merge.
            try:
                run_deterministic_resume_gates(
                    run_dir,
                    state,
                    phase,
                    from_stage="ci",
                    no_provider_replay=True,
                    execution_root=execution_root,
                )
            except Exception as error:  # never crash the coordinator on a retry
                append_event(
                    run_dir, state, "GATE_RETRY_DRAIN_ERROR", phase_id=phase["phase_id"], error=str(error)[:300]
                )
            if phase.get("status") in PASSING_VERDICTS:
                progressed = True
        write_state(run_dir, state)
        if not progressed:
            break
    return [p["phase_id"] for p in state.get("phases", []) if p.get("status") in GATE_BLOCKED_STATUSES]


def redrive_git_phase_blocked_phases(
    run_dir: Path,
    state: dict[str, Any],
    scheduler: SchedulerSettings,
    blocked: list[dict[str, Any]],
) -> list[str]:
    """Self-heal: re-drive phases left at GIT_PHASE_BLOCKED.

    GIT_PHASE_BLOCKED is the artifact-policy block at the git *commit* stage,
    distinct from the post-commit GATE_BLOCKED_STATUSES (PUSH/PR/CI/MERGE) that
    ``drain_gate_blocked_phases`` retries from ``ci`` (those already have a PR).
    A commit-stage block has no commit/push/PR yet, so it needs a re-drive from
    the build instead.

    ``execute_provider_phase`` is stage-driven by ``phase['status']``: a
    GIT_PHASE_BLOCKED phase skips every already-completed stage (reusing the
    cached spec/executor/validation/review/done-check artifacts — no provider
    re-call) and re-runs only the git/commit + PR + CI step via
    ``post_phase_git_github``. This lets a resume retry the commit after the
    blocking condition is resolved (e.g. an artifact-policy config fix) instead
    of orphaning the phase and its dependents behind the PENDING-only wave
    selector (the commit-stage analogue of the "resume silent stall").

    Runs only in the coordinator/main thread between waves, so no worker threads
    touch the run state concurrently. Returns phase_ids still GIT_PHASE_BLOCKED.
    """

    for phase in blocked:
        if (run_dir / "STOP").exists():
            break
        # Re-assert coordinator-owned pointer policy (mirrors run_wave_build) so a
        # re-driven phase branch still never writes ACTIVE_CAMPAIGN.md.
        if scheduler.update_active_campaign == "coordinator_only":
            phase["suppress_active_pointer"] = True
        append_event(
            run_dir, state, "GIT_PHASE_REDRIVE", phase_id=phase["phase_id"], status=phase.get("status")
        )
        _build_wave_phase(run_dir, state, phase)
    write_state(run_dir, state)
    return [p["phase_id"] for p in state.get("phases", []) if p.get("status") == GIT_PHASE_BLOCKED]


def run_dag_wave_parallel(
    run_dir: Path,
    state: dict[str, Any],
    scheduler: SchedulerSettings,
    max_phases: int,
) -> int:
    """Coordinator: build conflict-free waves concurrently, merge serially.

    Per wave: pick the next dependency-satisfied, conflict-free, parallel-safe
    set of PENDING phases; build them concurrently in isolated worktrees (merge
    deferred); merge the build-complete phases one at a time through the serial
    merge queue; run a wave integration verify; then recompute the next wave.
    """

    if not bool(state.get("mock_providers")) and not state.get("worktree_mode"):
        state["worktree_mode"] = True
        append_event(
            run_dir, state, "WORKTREE_MODE_FORCED", reason="parallel execution requires per-phase worktrees"
        )
    ensure_union_merge_attributes()
    state.setdefault("wave_counter", 0)
    executed = 0
    append_event(
        run_dir,
        state,
        "DAG_WAVE_RUN_START",
        max_parallel=scheduler.max_parallel_phases,
        update_active_campaign=scheduler.update_active_campaign,
    )

    with _parallel_mode():
        while True:
            if (run_dir / "STOP").exists():
                return provider_stop_without_execution(run_dir, state, "STOP file exists before next wave.")
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

            # Drain any phase left built-but-unmerged by a prior interrupted run
            # (STOP/crash during the serial merge queue) before scheduling new work.
            # Without this, resume's PENDING-only selection would orphan the phase
            # and the run could finalize with an unmerged built phase.
            leftover = [p for p in state["phases"] if p.get("status") == MERGE_READY]
            if leftover:
                append_event(run_dir, state, "MERGE_READY_DRAIN", phase_ids=[p["phase_id"] for p in leftover])
                run_wave_merge(run_dir, state, leftover, scheduler)
                write_state(run_dir, state)
                still_ready = [p["phase_id"] for p in state["phases"] if p.get("status") == MERGE_READY]
                if still_ready:
                    # The drain was interrupted (e.g. STOP reappeared); stop cleanly
                    # so a later resume retries rather than looping forever.
                    return provider_stop_without_execution(
                        run_dir, state, f"Merge-queue drain interrupted; {', '.join(still_ready)} remain MERGE_READY."
                    )
                continue

            # Self-heal on resume: retry any phase left gate-blocked by a prior
            # interrupted run (or a transient CI/merge timing) before scheduling
            # new work, so it and its dependents are not orphaned by the
            # PENDING-only wave selector (the "resume silent stall").
            if any(p.get("status") in GATE_BLOCKED_STATUSES for p in state["phases"]):
                remaining_blocked = drain_gate_blocked_phases(run_dir, state)
                if not remaining_blocked:
                    continue
                reason = (
                    f"Gate-blocked phase(s) could not be auto-retried: {', '.join(remaining_blocked)}. "
                    "Resolve the blocking condition and resume."
                )
                state["status"] = "STOPPED"
                state["stop_requested"] = True
                write_provider_stop(run_dir, state, reason)
                write_state(run_dir, state)
                write_provider_summary(run_dir, state, reason)
                print(f"Stopped (persistent gate-block) at {run_dir.relative_to(ROOT)}")
                return 0

            # Self-heal on resume: re-drive any phase left at GIT_PHASE_BLOCKED
            # (artifact-policy block at the git-commit stage) before scheduling
            # new work. Unlike the post-commit GATE_BLOCKED_STATUSES above, a
            # commit-stage block has no PR yet, so it is re-driven from the build
            # (reusing cached artifacts, no provider re-call) rather than from CI.
            # Without this, a resolved commit-stage block (e.g. after an
            # artifact-policy config fix) would be orphaned by the PENDING-only
            # wave selector and dead-lock its dependents.
            if any(p.get("status") == GIT_PHASE_BLOCKED for p in state["phases"]):
                git_blocked = [p for p in state["phases"] if p.get("status") == GIT_PHASE_BLOCKED]
                remaining_git_blocked = redrive_git_phase_blocked_phases(
                    run_dir, state, scheduler, git_blocked
                )
                if not remaining_git_blocked:
                    continue
                reason = (
                    "GIT_PHASE_BLOCKED phase(s) could not be auto-retried: "
                    f"{', '.join(remaining_git_blocked)}. Resolve the artifact-policy "
                    "or commit condition and resume."
                )
                state["status"] = "STOPPED"
                state["stop_requested"] = True
                write_provider_stop(run_dir, state, reason)
                write_state(run_dir, state)
                write_provider_summary(run_dir, state, reason)
                print(f"Stopped (persistent commit-block) at {run_dir.relative_to(ROOT)}")
                return 0

            wave = ready_wave_phases(state, scheduler)
            if not wave:
                if pending_phase_ids(state):
                    blocked_ids = pending_phase_ids(state)
                    reason = (
                        "SCHEDULE_DEADLOCK: no dependency-ready phase remains while "
                        f"{len(blocked_ids)} phase(s) are still pending: {', '.join(blocked_ids)}."
                    )
                    state["status"] = "BLOCKED"
                    state["stop_requested"] = True
                    append_event(run_dir, state, "SCHEDULE_DEADLOCK", pending=blocked_ids)
                    write_provider_stop(run_dir, state, reason)
                    write_state(run_dir, state)
                    write_provider_summary(run_dir, state, reason)
                    print(f"Schedule deadlock stopped run at {run_dir.relative_to(ROOT)}")
                    return 0
                return finalize_completed_campaign(run_dir, state)

            if executed >= max_phases:
                state["status"] = "STOPPED"
                state["stop_requested"] = True
                write_provider_stop(run_dir, state, f"Requested max phases reached: {max_phases}.")
                write_state(run_dir, state)
                write_provider_summary(run_dir, state, f"Requested max phases reached: {max_phases}.")
                print(f"Stopped after {executed} provider-wired phase(s) at {run_dir.relative_to(ROOT)}")
                return 0
            wave = wave[: max_phases - executed]

            wave_index = state["wave_counter"]
            wave_ids = [p["phase_id"] for p in wave]
            append_event(run_dir, state, "WAVE_START", wave=wave_index, phase_ids=wave_ids, width=len(wave))
            progress(run_dir, f"Wave {wave_index}: building {len(wave)} phase(s): {', '.join(wave_ids)}.")

            prepare_wave_worktrees(run_dir, state, wave)
            run_wave_build(run_dir, state, wave, scheduler)
            run_wave_merge(run_dir, state, wave, scheduler)
            wave_integration_verify(run_dir, state, wave_index)

            merged = [p["phase_id"] for p in wave if p.get("status") in PASSING_VERDICTS]
            stalled = [p["phase_id"] for p in wave if p.get("status") not in PASSING_VERDICTS]
            append_event(
                run_dir, state, "WAVE_COMPLETE", wave=wave_index, merged=merged, stalled=stalled
            )
            executed += len(wave)
            state["wave_counter"] = wave_index + 1
            write_state(run_dir, state)

            if stalled:
                # Self-heal: retry gate-blocked phases (presync + CI re-wait +
                # merge) once before giving up, so a transient block (CI
                # revalidation timing, a moved base) does not require a manual
                # resume. Genuine blocks (no PR, exhausted retries) still stop.
                if any(p.get("status") in GATE_BLOCKED_STATUSES for p in wave):
                    drain_gate_blocked_phases(run_dir, state)
                    stalled = [p["phase_id"] for p in wave if p.get("status") not in PASSING_VERDICTS]
                if not stalled:
                    continue
                reason = (
                    f"Wave {wave_index} left {len(stalled)} phase(s) not passing: {', '.join(stalled)}. "
                    "Resume after the blocking conditions are resolved."
                )
                state["status"] = "STOPPED"
                state["stop_requested"] = True
                write_provider_stop(run_dir, state, reason)
                write_state(run_dir, state)
                write_provider_summary(run_dir, state, reason)
                print(f"Stopped wave run with stalled phases at {run_dir.relative_to(ROOT)}")
                return 0


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
    scheduler = scheduler_settings_for_state(state)
    write_state(run_dir, state)
    if scheduler.runs_parallel:
        return run_dag_wave_parallel(run_dir, state, scheduler, max_phases)
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

        phase = select_next_phase(state, scheduler)
        if phase is None and scheduler.is_dag_wave and pending_phase_ids(state):
            blocked_ids = pending_phase_ids(state)
            reason = (
                "SCHEDULE_DEADLOCK: dag_wave mode found no dependency-ready phase while "
                f"{len(blocked_ids)} phase(s) remain pending: {', '.join(blocked_ids)}. "
                "A dependency is blocked or unsatisfiable."
            )
            state["status"] = "BLOCKED"
            state["stop_requested"] = True
            state["current_phase_id"] = None
            state["current_micro_attempt"] = 0
            append_event(run_dir, state, "SCHEDULE_DEADLOCK", pending=blocked_ids)
            write_provider_stop(run_dir, state, reason)
            write_state(run_dir, state)
            write_provider_summary(run_dir, state, reason)
            print(f"Schedule deadlock stopped run at {run_dir.relative_to(ROOT)}")
            return 0
        if phase is None:
            done_verdict = run_campaign_done_check(run_dir, state)
            if done_verdict in PROVIDER_WAITING_STATUSES:
                print(f"Stopped provider-wired Workflow 2 run at {run_dir.relative_to(ROOT)}")
                return 0
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

        if (run_dir / "STOP").exists():
            return provider_stop_without_execution(
                run_dir,
                state,
                f"STOP file exists before starting {phase.get('phase_id', 'next phase')}.",
            )

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
        "Commit-Eligible Allowed Paths:\n"
        f"- create or update {phase.output_path}\n\n"
        "Local-Only Run Artifacts:\n"
        f"{run_artifact_spec_policy(phase.phase_id)}\n"
        f"- write run artifacts under `runs/<run_id>/phases/{phase.phase_id}/`\n\n"
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
    with _RUN_WRITE_LOCK:
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
            campaign_id = resolve_active_campaign_id()
        if not campaign_id:
            print("Provider-wired mode requires --campaign-id or an ACTIVE_CAMPAIGN.md pointer.")
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
    stop_path = run_dir / "STOP"
    if stop_path.exists():
        gate_phase = current_gate_blocked_phase(state)
        if gate_phase is None:
            limit_phase = current_provider_limit_phase(state)
            if limit_phase is None:
                if stop_file_is_max_phase_limit(stop_path, state):
                    stop_path.unlink()
                    append_event(
                        run_dir,
                        state,
                        "RUN_RESUME_MAX_PHASES_STOP_REMOVED",
                        reason="Requested max phases reached.",
                    )
                else:
                    return provider_stop_without_execution(run_dir, state, "STOP file exists on resume.")
            else:
                if provider_replay_disabled():
                    return provider_stop_without_execution(
                        run_dir,
                        state,
                        "STOP file exists on provider-limit resume and FRONTIER_NO_PROVIDER_REPLAY=1 is set.",
                    )
                stop_path.unlink()
                append_event(
                    run_dir,
                    state,
                    "RUN_RESUME_PROVIDER_LIMIT",
                    phase_id=limit_phase["phase_id"],
                    resume_stage=limit_phase.get("resume_stage"),
                )
        else:
            stop_path.unlink()
            append_event(
                run_dir,
                state,
                "RUN_RESUME_GATE_RETRY",
                phase_id=gate_phase["phase_id"],
                gate_status=gate_phase.get("status"),
            )
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


def resume_provider_wired_stage(
    run_dir: Path,
    state: dict[str, Any],
    *,
    campaign_id: str | None,
    phase_id: str,
    from_stage: str,
    no_provider_replay: bool,
    worktree_mode: bool | None = None,
) -> int:
    try:
        stage_index(from_stage)
    except ValueError as error:
        print(error)
        return 2
    if no_provider_replay and from_stage not in {"ci", "branch_protection", "merge_gate", "merge", "complete"}:
        print("RESUME_PRECONDITION_FAILED: --no-provider-replay requires a deterministic resume stage.")
        return 2
    if campaign_id and state.get("campaign_id") != campaign_id:
        print(
            "RESUME_PRECONDITION_FAILED: run campaign "
            f"{state.get('campaign_id')!r} does not match requested {campaign_id!r}."
        )
        return 2
    try:
        load_ledger_campaign(str(state["campaign_id"]))
        phase = find_state_phase(state, phase_id)
    except ValueError as error:
        print(error)
        return 2

    phase_dir = provider_phase_dir(run_dir, phase)
    precondition = validate_resume_preconditions(
        phase_dir=phase_dir,
        phase=phase,
        state=state,
        from_stage=from_stage,
        allow_deterministic_rerun=True,
    )
    if not precondition.ok:
        reason = f"{RESUME_PRECONDITION_FAILED}: {summarize_resume_failure(precondition)}"
        write_resume_precondition_failure(
            run_dir,
            state,
            phase,
            reason,
            precondition=precondition.to_dict(),
        )
        print(reason)
        return 1

    if worktree_mode is not None:
        state["worktree_mode"] = worktree_mode
    if no_provider_replay:
        state["no_provider_replay"] = True
    stop_path = run_dir / "STOP"
    if stop_path.exists():
        stop_path.unlink()
        append_event(run_dir, state, "RUN_RESUME_STOP_REMOVED", phase_id=phase_id, from_stage=from_stage)
    mapped_status = PROVIDER_RESUME_STATUS_BY_STAGE.get(from_stage)
    if mapped_status:
        set_provider_phase_status(phase, mapped_status)
        phase.pop("status_reason", None)
    state["status"] = "RUNNING"
    state["stop_requested"] = False
    state["current_phase_id"] = phase_id
    state["current_stage"] = from_stage
    state.setdefault("provider_wired", True)
    state.setdefault("mock_providers", mock_providers_enabled())
    state.setdefault("provider_mode", "mock" if state.get("mock_providers") else "external")
    append_event(
        run_dir,
        state,
        "RUN_RESUME_STAGE",
        mode="provider_wired",
        phase_id=phase_id,
        from_stage=from_stage,
        no_provider_replay=no_provider_replay,
    )
    write_state(run_dir, state)
    write_provider_summary(run_dir, state, f"Resuming {phase_id} from {from_stage}.")
    progress(run_dir, f"Resuming {phase_id} from {from_stage}.")
    try:
        with run_lock(run_dir):
            if from_stage == "complete":
                write_provider_summary(run_dir, state, f"Resume preconditions are valid for {phase_id} complete.")
                return 0
            if from_stage in {"ci", "branch_protection", "merge_gate", "merge"}:
                ok = run_deterministic_resume_gates(
                    run_dir,
                    state,
                    phase,
                    from_stage=from_stage,
                    no_provider_replay=no_provider_replay,
                    execution_root=ROOT,
                )
                return 0 if ok else 1
            return continue_provider_wired_run(run_dir, state, 1, "resume-stage")
    except RuntimeError as error:
        print(error)
        return 1


def resume(
    run_id: str | None = None,
    *,
    run_dir: Path | None = None,
    campaign_id: str | None = None,
    phase_id: str | None = None,
    from_stage: str | None = None,
    provider_wired: bool = False,
    no_provider_replay: bool = False,
    max_phases: int | None = None,
    worktree_mode: bool | None = None,
) -> int:
    env_run = os.environ.get("FRONTIER_RESUME_RUN") or None
    env_phase = os.environ.get("FRONTIER_RESUME_PHASE") or None
    env_stage = os.environ.get("FRONTIER_RESUME_STAGE") or None
    if os.environ.get("FRONTIER_NO_PROVIDER_REPLAY", "").lower() in {"1", "true", "yes", "on"}:
        no_provider_replay = True
    phase_id = phase_id or env_phase
    from_stage = from_stage or env_stage
    if no_provider_replay and not from_stage:
        print("RESUME_PRECONDITION_FAILED: --no-provider-replay requires --from-stage.")
        return 2
    if run_dir is not None:
        run_ref = run_dir
    elif env_run:
        env_path = Path(env_run)
        run_ref = env_path if env_path.is_absolute() or len(env_path.parts) > 1 else ROOT / "runs" / env_path
    else:
        run_ref = None
    if run_ref is None:
        if run_id:
            run_ref = ROOT / "runs" / run_id
        else:
            target_campaign = campaign_id or resolve_active_campaign_id()
            if not target_campaign:
                print(
                    "Missing --run-id, --run-dir, FRONTIER_RESUME_RUN, or --campaign-id, "
                    "and no ACTIVE_CAMPAIGN.md pointer to resume."
                )
                return 2
            campaign_id = target_campaign
            run_ref = latest_campaign_run_dir(target_campaign, provider_wired_only=provider_wired)
            if run_ref is None:
                print(
                    f"No active local run found for campaign {target_campaign}. "
                    "Start one with `run --campaign-id`."
                )
                return 2
    elif not run_ref.is_absolute():
        run_ref = ROOT / run_ref
    run_dir = run_ref
    run_id = run_dir.name
    state_path = run_dir / "state.json"
    if not state_path.exists():
        print(f"Unknown run directory: {run_dir}")
        return 1

    state = read_json(state_path)
    if state.get("driver") == PROVIDER_WIRED_DRIVER or (
        provider_wired and state.get("provider_wired") is True
    ):
        if from_stage:
            if not phase_id:
                print("RESUME_PRECONDITION_FAILED: --from-stage requires --phase-id or FRONTIER_RESUME_PHASE.")
                return 2
            return resume_provider_wired_stage(
                run_dir,
                state,
                campaign_id=campaign_id,
                phase_id=phase_id,
                from_stage=from_stage,
                no_provider_replay=no_provider_replay,
                worktree_mode=worktree_mode,
            )
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


def plan_dag(campaign_id: str | None, *, max_parallel: int | None = None, as_json: bool = False) -> int:
    """Read-only DAG wave plan for a campaign (no run, no provider/git calls)."""

    if not campaign_id:
        campaign_id = resolve_active_campaign_id()
    if not campaign_id:
        print("plan-dag requires --campaign-id or an ACTIVE_CAMPAIGN.md pointer.")
        return 2
    try:
        campaign = load_ledger_campaign(campaign_id)
    except (ValueError, RuntimeError, OSError) as error:
        print(error)
        return 2
    scheduler = resolve_scheduler_config(campaign.campaign_yaml)
    effective_max = max_parallel if max_parallel is not None else scheduler.max_parallel_phases
    phases = [dag_scheduler.phase_from_ledger(p) for p in campaign.phases]
    try:
        plan = dag_scheduler.plan_campaign(
            phases, max_parallel=effective_max, red_authorized=scheduler.red_authorized
        )
    except dag_scheduler.SchedulerError as error:
        print(f"DAG validation failed: {error}")
        return 1

    if as_json:
        print(json.dumps({"campaign_id": campaign_id, "plan": plan.to_dict()}, indent=2, sort_keys=True))
        return 0

    print(f"Campaign: {campaign_id}")
    print(f"Scheduler mode: {scheduler.mode}   max_parallel_phases: {effective_max}")
    print(
        f"Waves: {len(plan.waves)}   max width: {plan.max_width}   "
        f"parallelizable: {str(plan.has_parallel).lower()}"
    )
    for wave in plan.waves:
        tag = "parallel" if wave.parallel else "single "
        print(f"  Wave {wave.index} [{tag}]: {', '.join(wave.phase_ids)}")
    if plan.unsafe:
        print("Run-alone / not parallel-safe:")
        for pid, reason in plan.unsafe:
            print(f"  - {pid}: {reason}")
    if plan.conflicts:
        print("Conflicts (kept in separate waves):")
        for left, right, why in plan.conflicts:
            print(f"  - {left} vs {right}: {why}")
    if plan.blocked:
        print("Blocked (unsatisfiable dependencies):")
        for pid, reason in plan.blocked:
            print(f"  - {pid}: {reason}")
    return 0


def _apply_scheduler_cli_env(args: argparse.Namespace) -> None:
    """Translate --parallel / --max-parallel flags into scheduler env overrides."""

    if getattr(args, "parallel", False):
        os.environ["FRONTIER_PARALLEL"] = "1"
    if getattr(args, "max_parallel", None):
        os.environ["FRONTIER_MAX_PARALLEL_PHASES"] = str(args.max_parallel)


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
    run_parser.add_argument("--parallel", action="store_true", help="Arm dag_wave parallel execution.")
    run_parser.add_argument("--max-parallel", type=int, help="Max concurrent phases per wave.")
    worktree_group = run_parser.add_mutually_exclusive_group()
    worktree_group.add_argument("--worktree-mode", action="store_true")
    worktree_group.add_argument("--no-worktree", action="store_true")
    resume_parser = subparsers.add_parser("resume", help="Resume a stopped run or a Workflow 2 stage.")
    resume_parser.add_argument("--run-id")
    resume_parser.add_argument("--run-dir", type=Path)
    resume_parser.add_argument("--campaign-id")
    resume_parser.add_argument("--phase-id")
    resume_parser.add_argument("--from-stage")
    resume_parser.add_argument("--provider-wired", action="store_true")
    resume_parser.add_argument("--no-provider-replay", action="store_true")
    resume_parser.add_argument("--max-phases", type=int)
    resume_parser.add_argument("--parallel", action="store_true", help="Arm dag_wave parallel execution.")
    resume_parser.add_argument("--max-parallel", type=int, help="Max concurrent phases per wave.")
    resume_worktree_group = resume_parser.add_mutually_exclusive_group()
    resume_worktree_group.add_argument("--worktree-mode", action="store_true")
    resume_worktree_group.add_argument("--no-worktree", action="store_true")
    plan_parser = subparsers.add_parser("plan-dag", help="Print the DAG wave plan for a campaign (read-only).")
    plan_parser.add_argument("--campaign-id")
    plan_parser.add_argument("--max-parallel", type=int)
    plan_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "run":
        _apply_scheduler_cli_env(args)
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
        _apply_scheduler_cli_env(args)
        return resume(
            args.run_id,
            run_dir=args.run_dir,
            campaign_id=args.campaign_id,
            phase_id=args.phase_id,
            from_stage=args.from_stage,
            provider_wired=args.provider_wired,
            no_provider_replay=args.no_provider_replay,
            max_phases=args.max_phases,
            worktree_mode=True if args.worktree_mode else False if args.no_worktree else None,
        )
    if args.command == "plan-dag":
        return plan_dag(args.campaign_id, max_parallel=args.max_parallel, as_json=args.json)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
