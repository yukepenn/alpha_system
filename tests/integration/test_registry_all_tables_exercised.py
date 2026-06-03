from __future__ import annotations

from pathlib import Path

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import REQUIRED_TABLES, connect_registry, init_registry
from alpha_system.experiments.artifact_manifest import (
    ArtifactManifestEntry,
    insert_artifact_manifest,
)
from alpha_system.experiments.promotion import PromotionDecision, insert_promotion_decision
from alpha_system.experiments.run_records import ExperimentRunRecord, insert_experiment_run_record


def test_all_required_registry_tables_are_exercised_against_temp_database(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path) as connection:
        _insert_dataset_version(connection)
        _insert_factor_registry(connection)
        _insert_factor_version(connection)
        _insert_label_version(connection)
        _insert_strategy_registry(connection)
        _insert_strategy_version(connection)
        for table in (
            "factor_validation_runs",
            "study_runs",
            "grid_runs",
            "ml_runs",
            "backtest_runs",
        ):
            insert_experiment_run_record(connection, table, _run_record(table))
        insert_artifact_manifest(
            connection,
            ArtifactManifestEntry(
                artifact_id="artifact-1",
                run_id="study_runs-run",
                artifact_type="summary",
                relative_path="docs/EXPERIMENT_REGISTRY.md",
                content_hash="artifact-hash",
                created_at="2026-06-02T01:20:07Z",
            ),
            run_table="study_runs",
        )
        insert_promotion_decision(
            connection,
            PromotionDecision(
                candidate_id="candidate-1",
                source_run_id="grid_runs-run",
                review_status="pass",
                decision_status="approved",
                reviewer_identity="reviewer-1",
                rationale="reviewed registry evidence",
                artifact_references={"review": "reviews/ALPHA_SYSTEM_V1/ASV1-P22.md"},
                timestamp="2026-06-02T01:20:07Z",
            ),
        )

        counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in REQUIRED_TABLES
        }

    assert set(counts) == set(REQUIRED_TABLES)
    assert all(count >= 1 for count in counts.values())


def _insert_dataset_version(connection) -> None:
    connection.execute(
        """
        INSERT INTO dataset_versions (
            data_version, dataset_name, created_at, source_uri, content_hash,
            config_hash, metadata_json, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "data:v1",
            "synthetic",
            "2026-06-02T01:20:07Z",
            "local-fixture",
            "content-hash",
            "config-hash",
            "{}",
            "recorded",
        ),
    )


def _insert_factor_registry(connection) -> None:
    connection.execute(
        """
        INSERT INTO factor_registry (
            factor_id, name, owner, description, status, created_at, updated_at,
            metadata_json, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "factor_a",
            "Factor A",
            "research",
            "Synthetic factor registry fixture.",
            "draft",
            "2026-06-02T01:20:07Z",
            "2026-06-02T01:20:07Z",
            "{}",
            "recorded",
        ),
    )


def _insert_factor_version(connection) -> None:
    connection.execute(
        """
        INSERT INTO factor_versions (
            factor_id, factor_version, created_at, git_commit, git_dirty, code_hash,
            config_hash, data_version, parameters_json, artifact_paths_json,
            decision_status, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "factor_a",
            "v1",
            "2026-06-02T01:20:07Z",
            "abc123",
            0,
            "code-hash",
            "config-hash",
            "data:v1",
            "{}",
            canonical_json({"summary": "docs/EXPERIMENT_REGISTRY.md"}),
            "draft",
            "recorded",
        ),
    )


def _insert_label_version(connection) -> None:
    connection.execute(
        """
        INSERT INTO label_versions (
            label_id, label_version, label_type, created_at, git_commit, git_dirty,
            code_hash, config_hash, data_version, parameters_json,
            artifact_paths_json, decision_status, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "label_a",
            "v1",
            "forward_return",
            "2026-06-02T01:20:07Z",
            "abc123",
            0,
            "code-hash",
            "config-hash",
            "data:v1",
            "{}",
            canonical_json({"summary": "docs/EXPERIMENT_REGISTRY.md"}),
            "draft",
            "recorded",
        ),
    )


def _insert_strategy_registry(connection) -> None:
    connection.execute(
        """
        INSERT INTO strategy_registry (
            strategy_id, name, owner, description, status, created_at, updated_at,
            metadata_json, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "strategy_a",
            "Strategy A",
            "research",
            "Synthetic strategy registry fixture.",
            "draft",
            "2026-06-02T01:20:07Z",
            "2026-06-02T01:20:07Z",
            "{}",
            "recorded",
        ),
    )


def _insert_strategy_version(connection) -> None:
    connection.execute(
        """
        INSERT INTO strategy_versions (
            strategy_id, strategy_version, created_at, git_commit, git_dirty,
            code_hash, config_hash, data_version, factor_versions_json,
            parameters_json, artifact_paths_json, decision_status, status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "strategy_a",
            "v1",
            "2026-06-02T01:20:07Z",
            "abc123",
            0,
            "code-hash",
            "config-hash",
            "data:v1",
            canonical_json({"factor_a": "v1"}),
            "{}",
            canonical_json({"summary": "docs/EXPERIMENT_REGISTRY.md"}),
            "draft",
            "recorded",
        ),
    )


def _run_record(table: str) -> ExperimentRunRecord:
    require_labels = table not in {"factor_validation_runs", "backtest_runs"}
    return ExperimentRunRecord(
        run_id=f"{table}-run",
        timestamp="2026-06-02T01:20:07Z",
        git_commit="abc123",
        git_dirty=False,
        code_hash="code-hash",
        config_hash="config-hash",
        data_version="data:v1",
        factor_versions={"factor_a": "v1"},
        label_versions={"label_a": "v1"} if require_labels else {},
        engine_version="engine:v1",
        parameters={"table": table},
        artifact_paths={"summary": "docs/EXPERIMENT_REGISTRY.md"},
        decision_status="recorded",
    )
