"""Persistent, queryable research-memory store for idea-to-verdict routes.

The ``memory_router`` is value-free and deliberately does not perform I/O: it
returns a ``MemoryRouteResult`` but never writes it. This module is the thin,
local-first persistence layer that turns those returned routes into a durable,
append-only, queryable research memory -- the fleet brain. It records WHAT the
machine concluded (verdict + reason + provenance + diagnostic numbers), never
raw market data or values, and it never marks anything promotion-eligible.

Layout (one append-only JSONL ledger per route action), under
``<ALPHA_DATA_ROOT>/research_memory/`` by default (local-only, like the feature
and label registries; never committed):

    graveyard.jsonl        REJECT routes
    requeue.jsonl          DATA_GAP / INCONCLUSIVE (incl. REVIEW_NEEDED) routes
    signal_shelf.jsonl     SIGNAL_PENDING_REVIEWER routes (non-promoting)
    promotion.jsonl        reviewer-gated WATCH / CANDIDATE routes

Each line is a value-free envelope: the routed verdict + reason_code, the full
machine record, and the provenance a future researcher needs to ask "tested
before? signal? rejected? data gap?" without re-running anything.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

RESEARCH_MEMORY_SCHEMA = "alpha_system.agent_factory.memory.research_memory_row.v1"
DEFAULT_ALPHA_DATA_ROOT = "~/alpha_data/alpha_system"
RESEARCH_MEMORY_SUBDIR = "research_memory"

# route action -> append-only ledger file
ACTION_LEDGERS: dict[str, str] = {
    "graveyard": "graveyard.jsonl",
    "requeue": "requeue.jsonl",
    "reviewer_pending_shelf": "signal_shelf.jsonl",
    "reviewer_gated_promotion": "promotion.jsonl",
}
# independent-reviewer adjudications layered over the signal shelf (append-only)
REVIEWER_ADJUDICATION_LEDGER = "reviewer_adjudications.jsonl"
# cross-idea family-wise multiplicity (FDR) accumulator (append-only; local-only).
# CROSS_IDEA_FDR_BUDGET_V1 Stage B records each setup-lane idea's per-test surrogate
# p here, keyed by its co-mined batch, so the family correction can refine across runs.
FAMILY_FDR_LEDGER = "family_fdr_ledger.jsonl"


class ResearchMemoryStoreError(ValueError):
    """Raised when a research-memory route cannot be persisted or read."""


def resolve_research_memory_dir(
    override: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the local research-memory directory.

    Precedence: explicit override, then ``$ALPHA_DATA_ROOT/research_memory``,
    then ``~/alpha_data/alpha_system/research_memory``. Mirrors the data-root
    convention used by the slice/feature/label resolvers.
    """

    if override is not None:
        return Path(override).expanduser()
    active_env = os.environ if env is None else env
    root = active_env.get("ALPHA_DATA_ROOT") or DEFAULT_ALPHA_DATA_ROOT
    return Path(root).expanduser() / RESEARCH_MEMORY_SUBDIR


def ensure_family_fdr_ledger_path(
    override: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve and ensure the local family-FDR ledger file exists (append-only).

    The ``FamilyFdrLedger`` is fail-closed: it requires an existing writable file.
    This creates the research-memory directory and an empty ledger file when needed
    so the Stage-B family-wise multiplicity accumulator can record/correct across
    ``alpha idea run`` invocations. Local-only, never committed.
    """

    directory = resolve_research_memory_dir(override, env=env)
    directory.mkdir(parents=True, exist_ok=True)
    ledger_path = directory / FAMILY_FDR_LEDGER
    if not ledger_path.exists():
        ledger_path.touch()
    return ledger_path


def build_research_memory_row(
    *,
    route_result: Mapping[str, Any],
    idea: Mapping[str, Any],
    readout: Mapping[str, Any],
    verdict: Mapping[str, Any] | str,
    created_at: str,
) -> dict[str, Any]:
    """Build the value-free, queryable envelope persisted for one route.

    Pulls provenance from the idea draft, the fast readout, and the route
    result so a future researcher can query by idea / factor / label / slice
    without re-running anything. No raw data or values are stored.
    """

    verdict_map = verdict if isinstance(verdict, Mapping) else {"verdict": verdict}
    slice_spec = _mapping(readout.get("slice_spec"))
    factor = _first_input(slice_spec, "feature_inputs", role="factor")
    label = _first_input(slice_spec, "label_inputs", role="label")
    quality = _main_effect_quality(readout)
    action = str(route_result.get("action") or "")
    return {
        "schema": RESEARCH_MEMORY_SCHEMA,
        "created_at": created_at,
        "verdict": route_result.get("verdict") or verdict_map.get("verdict"),
        "reason_code": verdict_map.get("reason_code"),
        "action": action,
        "record_type": route_result.get("record_type"),
        "promotion_eligible": route_result.get("promotion_eligible", False),
        "reviewer_required": action == "reviewer_pending_shelf",
        # provenance
        "alpha_spec_id": route_result.get("alpha_spec_id") or idea.get("alpha_spec_id"),
        "mechanism_id": idea.get("mechanism_id"),
        "hypothesis_id": idea.get("hypothesis_id"),
        "source": idea.get("source"),
        "study_kind": readout.get("study_kind") or slice_spec.get("study_kind"),
        "slice_id": slice_spec.get("slice_id"),
        "factor_id": factor.get("factor_id"),
        "feature_version_id": factor.get("pack_ref"),
        "feature_request_id": factor.get("feature_request_id"),
        "label_id": label.get("label_id"),
        "label_version_id": label.get("pack_ref"),
        "label_spec_id": label.get("label_spec_id"),
        # diagnostic numbers (value-free), when present
        "pearson_ic": quality.get("pearson_ic"),
        "rank_ic": quality.get("rank_ic"),
        "n_eff": quality.get("ic_power_n_eff"),
        "detectable_abs_ic": quality.get("ic_power_mde_abs_ic"),
        # full machine record as routed
        "memory_record": dict(_mapping(route_result.get("memory_record"))),
    }


def persist_route(
    *,
    route_result: Mapping[str, Any],
    idea: Mapping[str, Any],
    readout: Mapping[str, Any],
    verdict: Mapping[str, Any] | str,
    created_at: str,
    memory_dir: str | os.PathLike[str] | None = None,
) -> Path:
    """Append one route to its action ledger and return the ledger path."""

    if route_result.get("promotion_eligible") is True:
        raise ResearchMemoryStoreError(
            "research memory never persists a promotion-eligible route"
        )
    action = str(route_result.get("action") or "")
    ledger_name = ACTION_LEDGERS.get(action)
    if ledger_name is None:
        raise ResearchMemoryStoreError(f"unknown route action for persistence: {action!r}")
    row = build_research_memory_row(
        route_result=route_result,
        idea=idea,
        readout=readout,
        verdict=verdict,
        created_at=created_at,
    )
    directory = resolve_research_memory_dir(memory_dir)
    directory.mkdir(parents=True, exist_ok=True)
    ledger_path = directory / ledger_name
    line = json.dumps(row, ensure_ascii=True, sort_keys=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return ledger_path


def _signal_ref(row: Mapping[str, Any]) -> str | None:
    ref = row.get("signal_ref") or row.get("original_verdict_ref")
    if ref is None:
        record = row.get("memory_record")
        if isinstance(record, Mapping):
            ref = record.get("original_verdict_ref")
    return None if ref is None else str(ref)


def persist_reviewer_adjudication(
    adjudication: Mapping[str, Any],
    *,
    memory_dir: str | os.PathLike[str] | None = None,
) -> Path:
    """Append one independent-reviewer adjudication to its append-only ledger."""

    if adjudication.get("promotion_eligible") is True:
        raise ResearchMemoryStoreError(
            "reviewer adjudications are never promotion-eligible"
        )
    directory = resolve_research_memory_dir(memory_dir)
    directory.mkdir(parents=True, exist_ok=True)
    ledger_path = directory / REVIEWER_ADJUDICATION_LEDGER
    line = json.dumps(dict(adjudication), ensure_ascii=True, sort_keys=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return ledger_path


def pending_signals(
    *,
    memory_dir: str | os.PathLike[str] | None = None,
) -> list[dict[str, Any]]:
    """Return signal-shelf rows that have no reviewer adjudication yet."""

    adjudicated = {
        ref
        for row in read_ledger(REVIEWER_ADJUDICATION_LEDGER, memory_dir=memory_dir)
        if (ref := _signal_ref(row)) is not None
    }
    pending: list[dict[str, Any]] = []
    for row in read_ledger("reviewer_pending_shelf", memory_dir=memory_dir):
        if _signal_ref(row) not in adjudicated:
            pending.append(row)
    return pending


def read_ledger(
    action_or_filename: str,
    *,
    memory_dir: str | os.PathLike[str] | None = None,
) -> list[dict[str, Any]]:
    """Read one append-only ledger as a list of rows (empty if absent)."""

    ledger_name = ACTION_LEDGERS.get(action_or_filename, action_or_filename)
    path = resolve_research_memory_dir(memory_dir) / ledger_name
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def scan_research_memory(
    *,
    memory_dir: str | os.PathLike[str] | None = None,
    factor_id: str | None = None,
    label_version_id: str | None = None,
    slice_id: str | None = None,
    alpha_spec_id: str | None = None,
    verdict: str | None = None,
    actions: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Query the whole research memory with optional value-free filters.

    Lets a future researcher (or the reviewer workflow) ask "has this idea /
    factor / label / slice been tested, and with what verdict?" without
    re-running a probe.
    """

    selected = list(actions) if actions is not None else list(ACTION_LEDGERS)
    rows: list[dict[str, Any]] = []
    for action in selected:
        for row in read_ledger(action, memory_dir=memory_dir):
            if factor_id is not None and row.get("factor_id") != factor_id:
                continue
            if label_version_id is not None and row.get("label_version_id") != label_version_id:
                continue
            if slice_id is not None and row.get("slice_id") != slice_id:
                continue
            if alpha_spec_id is not None and row.get("alpha_spec_id") != alpha_spec_id:
                continue
            if verdict is not None and row.get("verdict") != verdict:
                continue
            rows.append(row)
    return rows


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_input(slice_spec: Mapping[str, Any], key: str, *, role: str) -> dict[str, Any]:
    for entry in slice_spec.get(key) or ():
        if isinstance(entry, Mapping) and str(entry.get("role")) == role:
            return dict(entry)
    # fall back to the first input of that kind if no role match
    for entry in slice_spec.get(key) or ():
        if isinstance(entry, Mapping):
            return dict(entry)
    return {}


def _main_effect_quality(readout: Mapping[str, Any]) -> dict[str, Any]:
    inner = readout.get("readout")
    if isinstance(inner, Mapping):
        report = inner.get("factor_diagnostics_report")
        if isinstance(report, Mapping):
            quality = report.get("quality_summary")
            if isinstance(quality, Mapping):
                return dict(quality)
    return {}


__all__ = [
    "ACTION_LEDGERS",
    "FAMILY_FDR_LEDGER",
    "RESEARCH_MEMORY_SCHEMA",
    "REVIEWER_ADJUDICATION_LEDGER",
    "ResearchMemoryStoreError",
    "build_research_memory_row",
    "ensure_family_fdr_ledger_path",
    "pending_signals",
    "persist_reviewer_adjudication",
    "persist_route",
    "read_ledger",
    "resolve_research_memory_dir",
    "scan_research_memory",
]
