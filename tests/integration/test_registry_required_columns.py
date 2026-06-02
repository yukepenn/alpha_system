from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from alpha_system.core.registry import (
    EXPERIMENT_RUN_TABLES,
    REQUIRED_RUN_RECORD_COLUMNS,
    connect_registry,
    init_registry,
    missing_required_run_columns,
    table_columns,
)
from alpha_system.experiments.registry import RunRecord, get_run_record, insert_run_record


def test_experiment_run_tables_have_required_reproducibility_columns(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path, read_only=True) as connection:
        assert missing_required_run_columns(connection) == {}
        for table in EXPERIMENT_RUN_TABLES:
            columns = set(table_columns(connection, table))
            assert set(REQUIRED_RUN_RECORD_COLUMNS).issubset(columns)


def test_experiment_run_json_columns_round_trip(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    timestamp = datetime(2026, 6, 2, 1, 20, 7, tzinfo=timezone.utc)

    with connect_registry(registry_path) as connection:
        for table in EXPERIMENT_RUN_TABLES:
            record = RunRecord(
                run_id=f"{table}-run-1",
                timestamp=timestamp,
                git_commit="abc123",
                git_dirty=True,
                code_hash="code-hash",
                config_hash="config-hash",
                data_version="dataset-v1",
                factor_versions={"factor_a": "1", "factor_b": "2"},
                label_versions={"label_a": "2026-06-02"},
                engine_version="engine-v1",
                parameters={"window": 20, "session_reset": True},
                artifact_paths={"summary": "artifacts/example/summary.json"},
                decision_status="review_required",
                warnings=("synthetic warning",),
                status_message="stored for registry round-trip test",
            )
            insert_run_record(connection, table, record)
            loaded = get_run_record(connection, table, record.run_id)

            assert loaded is not None
            assert loaded.factor_versions == record.factor_versions
            assert loaded.label_versions == record.label_versions
            assert loaded.parameters == record.parameters
            assert loaded.artifact_paths == record.artifact_paths
            assert loaded.warnings == record.warnings
            assert loaded.git_dirty is True
