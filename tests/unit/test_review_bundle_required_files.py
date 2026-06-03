from __future__ import annotations

from tests.unit.reports.review_bundle_fixtures import build_fixture_bundle


def test_review_bundle_required_files_are_present(tmp_path) -> None:
    bundle = build_fixture_bundle(tmp_path)

    assert "run_manifest" in bundle.validation.present_required_files
    assert "artifact_manifest" in bundle.validation.present_required_files
    assert bundle.run_manifest["exists"] is True
    assert bundle.artifact_manifest["entries"]
