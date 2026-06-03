from __future__ import annotations

from tests.unit.reports.review_bundle_fixtures import build_fixture_bundle


def test_review_bundle_records_promotion_status_without_state_change(tmp_path) -> None:
    bundle = build_fixture_bundle(tmp_path)

    assert bundle.promotion_decision_status == "not_recorded"
    assert bundle.summary_dict()["promotion_decision_status"] == "not_recorded"
    assert bundle.validation.promotion_decision_status == "not_recorded"
