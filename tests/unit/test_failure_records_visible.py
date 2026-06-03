from __future__ import annotations

from pathlib import Path

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.failure_records import list_failed_runs, record_failed_run


def test_failed_runs_are_listed_across_experiment_tables(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        record_failed_run(
            connection,
            "grid_runs",
            run_id="grid-failure-1",
            failed_step="grid_config",
            error_message="configuration rejected visibly",
            timestamp="2026-06-02T01:20:07Z",
            git_commit="abc123",
            git_dirty=False,
            code_hash="code-hash",
            config_hash="config-hash",
            data_version="data:v1",
            factor_versions={"factor_a": "v1"},
            label_versions={"label_a": "v1"},
            engine_version="grid_engine:v1",
            artifact_paths={"failure": "docs/REPRODUCIBILITY_AUDIT.md"},
        )
        failures = list_failed_runs(connection)

    assert [failure.run_id for failure in failures] == ["grid-failure-1"]
    assert failures[0].table_name == "grid_runs"
    assert failures[0].decision_status == "failed"
