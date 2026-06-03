from __future__ import annotations

from pathlib import Path

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.failure_records import list_failed_runs, record_failed_run


def test_failed_run_recording_keeps_failure_visible(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        record_failed_run(
            connection,
            "study_runs",
            run_id="failed-study-1",
            failed_step="artifact_manifest",
            error_message="manifest hash capture failed",
            timestamp="2026-06-02T01:20:07Z",
            git_commit="abc123",
            git_dirty=True,
            code_hash="code-hash",
            config_hash="config-hash",
            data_version="data:v1",
            factor_versions={"factor_a": "v1"},
            label_versions={"label_a": "v1"},
            engine_version="study_engine:v1",
            artifact_paths={"failure": "docs/REPRODUCIBILITY_AUDIT.md"},
        )
        failures = list_failed_runs(connection, table_name="study_runs")

    assert len(failures) == 1
    assert failures[0].run_id == "failed-study-1"
    assert failures[0].failed_steps[0]["step"] == "artifact_manifest"
    assert "failed run recorded visibly" in failures[0].warnings
