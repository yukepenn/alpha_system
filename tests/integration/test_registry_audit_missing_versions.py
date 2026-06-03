from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.audit import audit_registry


def test_registry_audit_detects_missing_versions_where_required(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        connection.execute(
            """
            INSERT INTO study_runs (
                run_id, timestamp, git_commit, git_dirty, code_hash, config_hash,
                data_version, factor_versions_json, label_versions_json, engine_version,
                parameters_json, artifact_paths_json, decision_status, warnings_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "study-missing-versions",
                "2026-06-02T01:20:07Z",
                "abc123",
                0,
                "code-hash",
                "config-hash",
                "",
                "{}",
                "{}",
                "study_engine:v1",
                "{}",
                canonical_json({"summary": "docs/EXPERIMENT_REGISTRY.md"}),
                "recorded",
                "[]",
                "recorded",
            ),
        )
        result = audit_registry(connection)

    codes = result.by_code()
    assert "missing_data_version" in codes
    assert "missing_factor_versions" in codes
    assert "missing_label_versions" in codes
