from __future__ import annotations

from alpha_system.reports.review_bundle import build_review_bundle
from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    registry_record,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


def test_review_bundle_surfaces_missing_artifact_warning(tmp_path) -> None:
    run_manifest = write_run_manifest(tmp_path, run_manifest_payload())
    artifact_manifest = write_artifact_manifest(
        tmp_path,
        [
            {
                "artifact_key": "missing_summary",
                "artifact_path": "artifacts/review_bundles/missing_summary.json",
            }
        ],
    )

    bundle = build_review_bundle(
        run_id="review_bundle_fixture",
        registry_records=(registry_record(),),
        artifact_manifest=artifact_manifest,
        run_manifest=run_manifest,
        source_root=REPO_ROOT,
    )

    assert bundle.missing_artifacts
    assert any(warning.code == "missing_artifact" for warning in bundle.warnings)
    assert bundle.validation.missing_artifacts
