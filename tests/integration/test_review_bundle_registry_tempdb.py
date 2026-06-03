from __future__ import annotations

from datetime import datetime, timezone

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.artifact_manifest import (
    ArtifactManifestEntry,
    insert_artifact_manifest,
)
from alpha_system.experiments.registry import RunRecord, insert_run_record
from alpha_system.reports.review_bundle import build_review_bundle
from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


def test_review_bundle_reads_registry_records_from_tempdb(tmp_path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    run_id = "registry_bundle_fixture"
    with connect_registry(registry_path) as connection:
        insert_run_record(
            connection,
            "study_runs",
            RunRecord(
                run_id=run_id,
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                git_commit="git-sha",
                git_dirty=False,
                code_hash="code-hash-v1",
                config_hash="config-hash-v1",
                data_version="data:v1",
                factor_versions={"fixture_factor": "factor:v1"},
                label_versions={"fixture_label": "label:v1"},
                engine_version="fixture_engine_v1",
                parameters={"review_status": "review_pending"},
                artifact_paths={"summary": "docs/REVIEW_BUNDLES.md"},
                decision_status="research_evidence_only",
                warnings=(),
                status_message="",
            ),
        )
        insert_artifact_manifest(
            connection,
            ArtifactManifestEntry(
                artifact_id="registry-artifact",
                run_id=run_id,
                artifact_type="diagnostics_summary",
                relative_path="docs/REVIEW_BUNDLES.md",
                content_hash="",
                created_at="2026-01-01T00:00:00Z",
            ),
            run_table="study_runs",
        )

    bundle = build_review_bundle(
        run_id=run_id,
        registry_path=registry_path,
        artifact_manifest=write_artifact_manifest(tmp_path),
        run_manifest=write_run_manifest(tmp_path, run_manifest_payload(run_id)),
        source_root=REPO_ROOT,
    )

    assert bundle.registry_records
    assert bundle.registry_records[0]["table_name"] == "study_runs"
    assert bundle.artifact_manifest["entries"]
    assert registry_path.exists()
    assert not registry_path.is_relative_to(REPO_ROOT)
