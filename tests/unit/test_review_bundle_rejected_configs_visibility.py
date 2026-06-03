from __future__ import annotations

from alpha_system.reports.review_bundle import build_review_bundle
from tests.unit.reports.review_bundle_fixtures import (
    REPO_ROOT,
    registry_record,
    run_manifest_payload,
    write_artifact_manifest,
    write_run_manifest,
)


def test_review_bundle_surfaces_rejected_configs(tmp_path) -> None:
    payload = run_manifest_payload()
    payload["rejected_configs"] = (
        {"config_id": "too_many", "reason": "combination limit exceeded"},
    )

    bundle = build_review_bundle(
        run_id="review_bundle_fixture",
        registry_records=(registry_record(),),
        artifact_manifest=write_artifact_manifest(tmp_path),
        run_manifest=write_run_manifest(tmp_path, payload),
        source_root=REPO_ROOT,
    )

    assert bundle.rejected_configs
    assert bundle.validation.surfaced_rejected_configs
    assert any(warning.code == "rejected_config_visibility" for warning in bundle.warnings)
