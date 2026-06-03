from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.audit import audit_registry


def test_registry_audit_detects_missing_hashes_and_git_commit(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        _insert_run(
            connection,
            run_id="study-missing-hashes",
            git_commit="",
            code_hash="",
            config_hash="",
        )
        result = audit_registry(connection)

    codes = result.by_code()
    assert "missing_git_commit" in codes
    assert "missing_code_hash" in codes
    assert "missing_config_hash" in codes


def test_registry_audit_detects_missing_artifacts_hidden_failures_and_reviewless_promotion(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        _insert_run(
            connection,
            run_id="study-hidden-failure",
            artifact_paths_json="{}",
            decision_status="failed",
            warnings_json="[]",
            status_message="",
        )
        connection.execute(
            """
            INSERT INTO promotion_decisions (
                decision_id, subject_type, subject_id, subject_version, run_id,
                decision_status, decided_at, reviewer, rationale,
                artifact_paths_json, metadata_json, status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "promotion-without-review",
                "candidate",
                "candidate-1",
                "",
                "study-hidden-failure",
                "approved",
                "2026-06-02T01:20:07Z",
                "",
                "",
                "{}",
                "{}",
                "",
            ),
        )
        result = audit_registry(connection)

    codes = result.by_code()
    assert "missing_artifact_references" in codes
    assert "hidden_failed_run" in codes
    assert "promotion_without_review" in codes


def _insert_run(connection, **overrides: object) -> None:
    values: dict[str, object] = {
        "run_id": "study-complete",
        "timestamp": "2026-06-02T01:20:07Z",
        "git_commit": "abc123",
        "git_dirty": 0,
        "code_hash": "code-hash",
        "config_hash": "config-hash",
        "data_version": "data:v1",
        "factor_versions_json": canonical_json({"factor_a": "v1"}),
        "label_versions_json": canonical_json({"label_a": "v1"}),
        "engine_version": "study_engine:v1",
        "parameters_json": "{}",
        "artifact_paths_json": canonical_json({"summary": "docs/EXPERIMENT_REGISTRY.md"}),
        "decision_status": "recorded",
        "warnings_json": "[]",
        "status_message": "recorded",
    }
    values.update(overrides)
    connection.execute(
        """
        INSERT INTO study_runs (
            run_id, timestamp, git_commit, git_dirty, code_hash, config_hash,
            data_version, factor_versions_json, label_versions_json, engine_version,
            parameters_json, artifact_paths_json, decision_status, warnings_json,
            status_message
        )
        VALUES (
            :run_id, :timestamp, :git_commit, :git_dirty, :code_hash, :config_hash,
            :data_version, :factor_versions_json, :label_versions_json, :engine_version,
            :parameters_json, :artifact_paths_json, :decision_status, :warnings_json,
            :status_message
        )
        """,
        values,
    )
