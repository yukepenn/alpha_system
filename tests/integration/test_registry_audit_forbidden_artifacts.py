from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.audit import audit_registry


def test_registry_audit_detects_forbidden_artifact_paths(tmp_path: Path) -> None:
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
                "study-forbidden-artifact",
                "2026-06-02T01:20:07Z",
                "abc123",
                0,
                "code-hash",
                "config-hash",
                "data:v1",
                canonical_json({"factor_a": "v1"}),
                canonical_json({"label_a": "v1"}),
                "study_engine:v1",
                "{}",
                canonical_json({"db": "/mnt/c/Users/example/registry.sqlite3"}),
                "recorded",
                "[]",
                "recorded",
            ),
        )
        connection.execute(
            """
            INSERT INTO artifact_manifest (
                artifact_id, run_id, run_table, artifact_key, artifact_path,
                content_hash, artifact_role, created_at, metadata_json, status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "artifact-forbidden",
                "study-forbidden-artifact",
                "study_runs",
                "db",
                "../metadata/registry.sqlite3",
                "",
                "registry",
                "2026-06-02T01:20:07Z",
                "{}",
                "",
            ),
        )
        result = audit_registry(connection)

    forbidden = result.by_code()["forbidden_artifact_path"]
    assert len(forbidden) >= 2
    assert {finding.table_name for finding in forbidden} >= {"study_runs", "artifact_manifest"}
