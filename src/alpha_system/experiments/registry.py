"""Experiment-style run record access over the SQLite metadata registry."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import EXPERIMENT_RUN_TABLES


@dataclass(frozen=True, slots=True, kw_only=True)
class RunRecord:
    run_id: str
    timestamp: datetime | str
    git_commit: str | None
    git_dirty: bool | None
    code_hash: str
    config_hash: str
    data_version: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    engine_version: str
    parameters: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    decision_status: str
    warnings: Sequence[str] = ()
    status_message: str = ""


def _normalize_timestamp(value: datetime | str) -> str:
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_loads(value: str) -> Any:
    return json.loads(value)


def _validate_run_table(table_name: str) -> None:
    if table_name not in EXPERIMENT_RUN_TABLES:
        msg = f"{table_name!r} is not an experiment-style run table"
        raise ValueError(msg)


def insert_run_record(
    connection: sqlite3.Connection,
    table_name: str,
    record: RunRecord,
) -> None:
    """Insert one run record into an experiment-style run table."""
    _validate_run_table(table_name)
    connection.execute(
        f"""
        INSERT INTO {table_name} (
            run_id,
            timestamp,
            git_commit,
            git_dirty,
            code_hash,
            config_hash,
            data_version,
            factor_versions_json,
            label_versions_json,
            engine_version,
            parameters_json,
            artifact_paths_json,
            decision_status,
            warnings_json,
            status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.run_id,
            _normalize_timestamp(record.timestamp),
            record.git_commit,
            None if record.git_dirty is None else int(record.git_dirty),
            record.code_hash,
            record.config_hash,
            record.data_version,
            canonical_json(record.factor_versions),
            canonical_json(record.label_versions),
            record.engine_version,
            canonical_json(record.parameters),
            canonical_json(record.artifact_paths),
            record.decision_status,
            canonical_json(list(record.warnings)),
            record.status_message,
        ),
    )


def get_run_record(
    connection: sqlite3.Connection,
    table_name: str,
    run_id: str,
) -> RunRecord | None:
    """Read one run record from an experiment-style run table."""
    _validate_run_table(table_name)
    row = connection.execute(
        f"""
        SELECT
            run_id,
            timestamp,
            git_commit,
            git_dirty,
            code_hash,
            config_hash,
            data_version,
            factor_versions_json,
            label_versions_json,
            engine_version,
            parameters_json,
            artifact_paths_json,
            decision_status,
            warnings_json,
            status_message
        FROM {table_name}
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    if row is None:
        return None

    return RunRecord(
        run_id=str(row["run_id"]),
        timestamp=str(row["timestamp"]),
        git_commit=row["git_commit"],
        git_dirty=None if row["git_dirty"] is None else bool(row["git_dirty"]),
        code_hash=str(row["code_hash"]),
        config_hash=str(row["config_hash"]),
        data_version=str(row["data_version"]),
        factor_versions=_json_loads(row["factor_versions_json"]),
        label_versions=_json_loads(row["label_versions_json"]),
        engine_version=str(row["engine_version"]),
        parameters=_json_loads(row["parameters_json"]),
        artifact_paths=_json_loads(row["artifact_paths_json"]),
        decision_status=str(row["decision_status"]),
        warnings=tuple(_json_loads(row["warnings_json"])),
        status_message=str(row["status_message"]),
    )
