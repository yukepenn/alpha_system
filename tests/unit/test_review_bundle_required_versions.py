from __future__ import annotations

from tests.unit.reports.review_bundle_fixtures import build_fixture_bundle


def test_review_bundle_required_versions_are_present(tmp_path) -> None:
    bundle = build_fixture_bundle(tmp_path)

    assert bundle.validation.missing_required_versions == ()
    assert bundle.versions["data_version"] == "data:v1"
    assert bundle.versions["factor_versions"] == {"fixture_factor": "factor:v1"}
    assert bundle.versions["label_versions"] == {"fixture_label": "label:v1"}
    assert bundle.versions["engine_version"] == "fixture_engine_v1"
