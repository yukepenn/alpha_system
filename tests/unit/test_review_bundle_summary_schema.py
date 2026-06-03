from __future__ import annotations

from tests.unit.reports.review_bundle_fixtures import build_fixture_bundle


def test_review_bundle_summary_schema_is_small_and_deterministic(tmp_path) -> None:
    bundle = build_fixture_bundle(tmp_path)
    summary = bundle.summary_dict()

    assert set(summary) >= {
        "run_id",
        "bundle_type",
        "review_status",
        "promotion_decision_status",
        "no_lookahead_validation_status",
        "versions",
        "config_hashes",
        "code_hashes",
        "warning_count",
        "missing_artifact_count",
        "failed_run_count",
        "rejected_config_count",
        "validation",
    }
    assert "registry_records" not in summary
    assert summary == bundle.summary_dict()
