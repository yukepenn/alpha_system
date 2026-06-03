"""Failed-run recording and visible failed-run surfacing."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from alpha_system.core.registry import EXPERIMENT_RUN_TABLES
from alpha_system.experiments.run_records import (
    ExperimentRunRecord,
    FailedStep,
    insert_experiment_run_record,
    parse_status_payload,
)


FAILED_DECISION_STATUSES: frozenset[str] = frozenset(
    {"failed", "error", "blocked", "rejected", "validation_failed"}
)


@dataclass(frozen=True, slots=True)
class VisibleFailedRun:
    """A failed run surfaced from the registry."""

    table_name: str
    run_id: str
    decision_status: str
    failed_steps: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    status_message: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failed_steps"] = list(self.failed_steps)
        payload["warnings"] = list(self.warnings)
        return payload


def record_failed_run(
    connection: sqlite3.Connection,
    table_name: str,
    *,
    run_id: str,
    failed_step: str,
    error_message: str,
    timestamp: datetime | str | None = None,
    git_commit: str,
    git_dirty: bool | None,
    code_hash: str,
    config_hash: str,
    data_version: str,
    factor_versions: Mapping[str, str],
    label_versions: Mapping[str, str],
    engine_version: str,
    parameters: Mapping[str, Any] | None = None,
    artifact_paths: Mapping[str, str] | None = None,
    warnings: Sequence[str] = (),
) -> None:
    """Record a failed run in the normal run table with visible failure metadata."""
    active_timestamp = timestamp or datetime.now(timezone.utc)
    active_warnings = tuple(dict.fromkeys((*warnings, "failed run recorded visibly")))
    record = ExperimentRunRecord(
        run_id=run_id,
        timestamp=active_timestamp,
        git_commit=git_commit,
        git_dirty=git_dirty,
        code_hash=code_hash,
        config_hash=config_hash,
        data_version=data_version,
        factor_versions=factor_versions,
        label_versions=label_versions,
        engine_version=engine_version,
        parameters=dict(parameters or {}),
        artifact_paths=dict(artifact_paths or {"failure_record": "docs/REPRODUCIBILITY_AUDIT.md"}),
        decision_status="failed",
        warnings=active_warnings,
        failed_steps=(
            FailedStep(
                step=failed_step,
                status="failed",
                message=error_message,
                timestamp=active_timestamp,
            ),
        ),
        status_message=error_message,
    )
    insert_experiment_run_record(connection, table_name, record)


def list_failed_runs(
    connection: sqlite3.Connection,
    *,
    table_name: str | None = None,
) -> tuple[VisibleFailedRun, ...]:
    """Surface failed runs across experiment tables without hiding failed states."""
    tables = (table_name,) if table_name is not None else EXPERIMENT_RUN_TABLES
    failures: list[VisibleFailedRun] = []
    for table in tables:
        rows = connection.execute(
            f"""
            SELECT run_id, decision_status, warnings_json, status_message
            FROM {table}
            ORDER BY run_id
            """
        ).fetchall()
        for row in rows:
            status = str(row["decision_status"])
            status_payload = parse_status_payload(str(row["status_message"] or ""))
            warnings = _loads_list(row["warnings_json"])
            failed_steps = tuple(
                step for step in status_payload["failed_steps"] if isinstance(step, dict)
            )
            failure_visible = status.lower() in FAILED_DECISION_STATUSES or bool(failed_steps)
            if not failure_visible:
                continue
            failures.append(
                VisibleFailedRun(
                    table_name=table,
                    run_id=str(row["run_id"]),
                    decision_status=status,
                    failed_steps=failed_steps,
                    warnings=tuple(str(item) for item in warnings),
                    status_message=str(status_payload["message"]),
                )
            )
    return tuple(failures)


def hidden_failed_run_pattern(row: sqlite3.Row) -> bool:
    """Return whether a failed row lacks visible failure details."""
    status = str(row["decision_status"]).lower()
    if status not in FAILED_DECISION_STATUSES:
        return False
    payload = parse_status_payload(str(row["status_message"] or ""))
    warnings = _loads_list(row["warnings_json"])
    return not payload["failed_steps"] and not str(payload["message"]).strip() and not warnings


def _loads_list(value: str) -> list[Any]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []
