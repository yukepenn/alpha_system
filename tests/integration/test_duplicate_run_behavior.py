from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.run_records import ExperimentRunRecord, insert_experiment_run_record


def test_duplicate_run_id_is_deterministically_rejected(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    record = ExperimentRunRecord(
        run_id="study-duplicate",
        timestamp="2026-06-02T01:20:07Z",
        git_commit="abc123",
        git_dirty=False,
        code_hash="code-hash",
        config_hash="config-hash",
        data_version="data:v1",
        factor_versions={"factor_a": "v1"},
        label_versions={"label_a": "v1"},
        engine_version="study_engine:v1",
        parameters={},
        artifact_paths={"summary": "docs/EXPERIMENT_REGISTRY.md"},
        decision_status="recorded",
    )

    with connect_registry(registry_path) as connection:
        insert_experiment_run_record(connection, "study_runs", record)
        with pytest.raises(sqlite3.IntegrityError):
            insert_experiment_run_record(connection, "study_runs", record)
        count = connection.execute(
            "SELECT count(*) FROM study_runs WHERE run_id = ?",
            (record.run_id,),
        ).fetchone()[0]

    assert count == 1
