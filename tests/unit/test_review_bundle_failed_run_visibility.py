from __future__ import annotations

from alpha_system.reports.review_bundle import build_review_bundle
from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    registry_record,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


def test_review_bundle_surfaces_failed_steps(tmp_path) -> None:
    payload = run_manifest_payload()
    payload["failed_steps"] = (
        {"step": "artifact_manifest", "status": "failed", "message": "fixture failure"},
    )
    record = registry_record()
    record["decision_status"] = "failed"
    record["failed_steps"] = payload["failed_steps"]

    bundle = build_review_bundle(
        run_id="review_bundle_fixture",
        registry_records=(record,),
        artifact_manifest=write_artifact_manifest(tmp_path),
        run_manifest=write_run_manifest(tmp_path, payload),
        source_root=REPO_ROOT,
    )

    assert bundle.failed_steps
    assert bundle.validation.surfaced_failed_runs
    assert any(warning.code == "failed_run_visibility" for warning in bundle.warnings)
