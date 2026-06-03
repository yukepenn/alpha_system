"""Canonical hardened run-record model for experiment registry rows."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from alpha_system.core.registry import EXPERIMENT_RUN_TABLES
from alpha_system.experiments.registry import (
    RunRecord as RegistryRunRecord,
    get_run_record as get_registry_run_record,
    insert_run_record as insert_registry_run_record,
)
from alpha_system.experiments.version_refs import VersionReferences, VersionRefError


RUN_CATEGORY_TABLES: dict[str, str] = {
    "factor_validation": "factor_validation_runs",
    "study": "study_runs",
    "grid": "grid_runs",
    "management_grid": "grid_runs",
    "ml": "ml_runs",
    "backtest": "backtest_runs",
}

RUN_TABLE_REQUIREMENTS: dict[str, dict[str, bool]] = {
    "factor_validation_runs": {
        "require_factor_versions": True,
        "require_label_versions": False,
    },
    "study_runs": {
        "require_factor_versions": True,
        "require_label_versions": True,
    },
    "grid_runs": {
        "require_factor_versions": True,
        "require_label_versions": True,
    },
    "ml_runs": {
        "require_factor_versions": True,
        "require_label_versions": True,
    },
    "backtest_runs": {
        "require_factor_versions": True,
        "require_label_versions": False,
    },
}


class RunRecordError(ValueError):
    """Raised when a run record is incomplete or structurally invalid."""


@dataclass(frozen=True, slots=True)
class FailedStep:
    """Visible failed-step metadata kept with failed run records."""

    step: str
    status: str
    message: str = ""
    timestamp: datetime | str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "step", _require_text(self.step, "failed step"))
        object.__setattr__(self, "status", _require_text(self.status, "failed step status"))
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", _timestamp_text(self.timestamp))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRunRecord:
    """Full reproducibility run record shared across experiment run tables."""

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
    failed_steps: Sequence[FailedStep | Mapping[str, Any]] = ()
    status_message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_id", _require_text(self.run_id, "run_id"))
        object.__setattr__(self, "timestamp", _timestamp_text(self.timestamp))
        if self.git_commit is not None:
            object.__setattr__(
                self,
                "git_commit",
                _require_text(self.git_commit, "git_commit"),
            )
        object.__setattr__(self, "code_hash", _require_text(self.code_hash, "code_hash"))
        object.__setattr__(self, "config_hash", _require_text(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "decision_status",
            _require_text(self.decision_status, "decision_status"),
        )
        try:
            refs = VersionReferences(
                data_version=self.data_version,
                factor_versions=self.factor_versions,
                label_versions=self.label_versions,
                engine_version=self.engine_version,
            )
        except VersionRefError as exc:
            raise RunRecordError(str(exc)) from exc
        object.__setattr__(self, "data_version", refs.data_version)
        object.__setattr__(self, "factor_versions", refs.factor_versions)
        object.__setattr__(self, "label_versions", refs.label_versions)
        object.__setattr__(self, "engine_version", refs.engine_version)
        object.__setattr__(self, "parameters", dict(self.parameters))
        object.__setattr__(self, "artifact_paths", _validate_artifact_path_map(self.artifact_paths))
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(
            self,
            "failed_steps",
            tuple(_coerce_failed_step(item) for item in self.failed_steps),
        )

    def validate_for_table(self, table_name: str) -> None:
        """Reject missing required fields for the target run table."""
        if table_name not in EXPERIMENT_RUN_TABLES:
            raise RunRecordError(f"{table_name!r} is not an experiment run table")
        if not self.git_commit:
            raise RunRecordError("git_commit is required for hardened run records")
        requirements = RUN_TABLE_REQUIREMENTS[table_name]
        try:
            refs = VersionReferences(
                data_version=self.data_version,
                factor_versions=self.factor_versions,
                label_versions=self.label_versions,
                engine_version=self.engine_version,
            )
            refs.validate_requirements(
                require_factor_versions=requirements["require_factor_versions"],
                require_label_versions=requirements["require_label_versions"],
            )
        except VersionRefError as exc:
            raise RunRecordError(str(exc)) from exc
        if not self.artifact_paths:
            raise RunRecordError("artifact_paths must contain at least one artifact reference")
        if self.decision_status.lower() in {"failed", "error"} and not self.failed_steps:
            raise RunRecordError("failed runs must include failed-step visibility")

    def to_registry_record(self) -> RegistryRunRecord:
        return RegistryRunRecord(
            run_id=self.run_id,
            timestamp=str(self.timestamp),
            git_commit=self.git_commit,
            git_dirty=self.git_dirty,
            code_hash=self.code_hash,
            config_hash=self.config_hash,
            data_version=self.data_version,
            factor_versions=dict(self.factor_versions),
            label_versions=dict(self.label_versions),
            engine_version=self.engine_version,
            parameters=dict(self.parameters),
            artifact_paths=dict(self.artifact_paths),
            decision_status=self.decision_status,
            warnings=tuple(self.warnings),
            status_message=_status_payload_text(
                message=self.status_message,
                failed_steps=self.failed_steps,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failed_steps"] = [step.to_dict() for step in self.failed_steps]
        return payload


def _require_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise RunRecordError(f"{field_name} must be non-empty")
    return text


def _timestamp_text(value: datetime | str) -> str:
    if isinstance(value, str):
        return _require_text(value, "timestamp")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_artifact_path_map(values: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise RunRecordError("artifact_paths must be a mapping")
    normalized: dict[str, str] = {}
    for key, value in values.items():
        normalized[_require_text(str(key), "artifact path key")] = _require_text(
            str(value),
            f"artifact_paths[{key!r}]",
        )
    return dict(sorted(normalized.items()))


def _coerce_failed_step(value: FailedStep | Mapping[str, Any]) -> FailedStep:
    if isinstance(value, FailedStep):
        return value
    if not isinstance(value, Mapping):
        raise RunRecordError("failed_steps must contain FailedStep objects or mappings")
    return FailedStep(
        step=str(value.get("step", "")),
        status=str(value.get("status", "")),
        message=str(value.get("message", "")),
        timestamp=value.get("timestamp"),
    )


def _status_payload_text(*, message: str, failed_steps: Sequence[FailedStep]) -> str:
    if not failed_steps:
        return message
    return json.dumps(
        {
            "message": message,
            "failed_steps": [step.to_dict() for step in failed_steps],
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_status_payload(status_message: str) -> dict[str, Any]:
    """Parse hardened status payloads while tolerating legacy plain text."""
    if not status_message:
        return {"message": "", "failed_steps": []}
    try:
        payload = json.loads(status_message)
    except json.JSONDecodeError:
        return {"message": status_message, "failed_steps": []}
    if not isinstance(payload, Mapping):
        return {"message": status_message, "failed_steps": []}
    failed_steps = payload.get("failed_steps")
    if not isinstance(failed_steps, list):
        failed_steps = []
    return {
        "message": str(payload.get("message", "")),
        "failed_steps": failed_steps,
    }


def insert_experiment_run_record(
    connection: sqlite3.Connection,
    table_name: str,
    record: ExperimentRunRecord,
) -> None:
    """Validate and insert one hardened run record."""
    record.validate_for_table(table_name)
    insert_registry_run_record(connection, table_name, record.to_registry_record())


def get_experiment_run_record(
    connection: sqlite3.Connection,
    table_name: str,
    run_id: str,
) -> ExperimentRunRecord | None:
    """Read a hardened run record from an existing experiment table."""
    record = get_registry_run_record(connection, table_name, run_id)
    if record is None:
        return None
    payload = parse_status_payload(record.status_message)
    return ExperimentRunRecord(
        run_id=record.run_id,
        timestamp=record.timestamp,
        git_commit=record.git_commit,
        git_dirty=record.git_dirty,
        code_hash=record.code_hash,
        config_hash=record.config_hash,
        data_version=record.data_version,
        factor_versions=record.factor_versions,
        label_versions=record.label_versions,
        engine_version=record.engine_version,
        parameters=record.parameters,
        artifact_paths=record.artifact_paths,
        decision_status=record.decision_status,
        warnings=record.warnings,
        failed_steps=payload["failed_steps"],
        status_message=payload["message"],
    )
