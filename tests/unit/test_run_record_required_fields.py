from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.run_records import (
    ExperimentRunRecord,
    FailedStep,
    RunRecordError,
    get_experiment_run_record,
    insert_experiment_run_record,
)


def test_hardened_run_record_round_trips_required_fields(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    record = _record()

    with connect_registry(registry_path) as connection:
        insert_experiment_run_record(connection, "study_runs", record)
        loaded = get_experiment_run_record(connection, "study_runs", record.run_id)

    assert loaded is not None
    assert loaded.git_commit == "abc123"
    assert loaded.git_dirty is False
    assert loaded.factor_versions == {"factor_a": "v1"}
    assert loaded.label_versions == {"label_a": "v1"}
    assert loaded.artifact_paths == {"summary": "docs/EXPERIMENT_REGISTRY.md"}


def test_missing_git_commit_is_rejected(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    record = _record(git_commit=None)

    with connect_registry(registry_path) as connection:
        with pytest.raises(RunRecordError, match="git_commit"):
            insert_experiment_run_record(connection, "study_runs", record)


def test_missing_required_label_version_is_rejected_for_study_runs(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    record = _record(label_versions={})

    with connect_registry(registry_path) as connection:
        with pytest.raises(RunRecordError, match="label_versions"):
            insert_experiment_run_record(connection, "study_runs", record)


def test_failed_run_requires_failed_step_visibility(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    hidden_failure = _record(decision_status="failed", failed_steps=())
    visible_failure = _record(
        run_id="study-visible-failure",
        decision_status="failed",
        failed_steps=(FailedStep(step="registry_write", status="failed", message="boom"),),
    )

    with connect_registry(registry_path) as connection:
        with pytest.raises(RunRecordError, match="failed-step"):
            insert_experiment_run_record(connection, "study_runs", hidden_failure)
        insert_experiment_run_record(connection, "study_runs", visible_failure)

        with pytest.raises(sqlite3.IntegrityError):
            insert_experiment_run_record(connection, "study_runs", visible_failure)


def _record(**overrides: object) -> ExperimentRunRecord:
    payload: dict[str, object] = {
        "run_id": "study-run-1",
        "timestamp": "2026-06-02T01:20:07Z",
        "git_commit": "abc123",
        "git_dirty": False,
        "code_hash": "code-hash",
        "config_hash": "config-hash",
        "data_version": "data:v1",
        "factor_versions": {"factor_a": "v1"},
        "label_versions": {"label_a": "v1"},
        "engine_version": "study_engine:v1",
        "parameters": {"window": 5},
        "artifact_paths": {"summary": "docs/EXPERIMENT_REGISTRY.md"},
        "decision_status": "recorded",
        "warnings": (),
        "failed_steps": (),
        "status_message": "recorded",
    }
    payload.update(overrides)
    return ExperimentRunRecord(**payload)  # type: ignore[arg-type]
