from __future__ import annotations

from datetime import UTC, datetime

from alpha_system.features.reports import (
    CoverageBucket,
    FeatureCoverageReport,
    FeaturePartitionRole,
    FeatureQualityReport,
)
from alpha_system.reports.feature_card import FeatureCard, render_feature_card


def test_feature_card_renders_quality_coverage_and_no_claim_language() -> None:
    quality = FeatureQualityReport(
        feature_id="base_ohlcv_close_return_1m",
        feature_version_id="fver_" + "1" * 64,
        feature_request_id="freq_synthetic_feature_card",
        dataset_version_id="dsv_synthetic_feature_card",
        partition_id="development_partition",
        materialization_output_path="/tmp/alpha/features/values.jsonl",
        record_count=2,
        valid_value_record_count=2,
        nan_record_count=0,
        nan_rate=0.0,
        constant_feature=False,
        distinct_observed_values=2,
        missing_bbo_count=1,
        bbo_quarantined_count=0,
        available_ts_missing_count=0,
        available_ts_invalid_count=0,
        available_ts_before_event_count=0,
        duplicate_exposure_status="NO_FINDINGS",
    )
    coverage = FeatureCoverageReport(
        feature_id=quality.feature_id,
        feature_version_id=quality.feature_version_id,
        feature_request_id=quality.feature_request_id,
        dataset_version_id=quality.dataset_version_id,
        partition_id=quality.partition_id,
        partition_role=FeaturePartitionRole.DEVELOPMENT,
        materialization_output_path=quality.materialization_output_path,
        record_count=2,
        symbol_coverage=(
            CoverageBucket(
                "ES",
                2,
                _dt("2024-01-02T14:31:00+00:00"),
                _dt("2024-01-02T14:32:00+00:00"),
            ),
        ),
        session_coverage=(
            CoverageBucket(
                "RTH",
                2,
                _dt("2024-01-02T14:31:00+00:00"),
                _dt("2024-01-02T14:32:00+00:00"),
            ),
        ),
        partition_coverage=(
            CoverageBucket(
                "development_partition",
                2,
                _dt("2024-01-02T14:31:00+00:00"),
                _dt("2024-01-02T14:32:00+00:00"),
            ),
        ),
        expected_symbols=("ES",),
        expected_sessions=("RTH",),
        expected_partitions=("development_partition",),
        duplicate_exposure_status=quality.duplicate_exposure_status,
    )

    text = render_feature_card(quality, coverage)
    payload = FeatureCard(quality, coverage).to_dict()

    assert "Quality" in text
    assert "Coverage" in text
    assert "Duplicate Exposure" in text
    assert payload["status"] == "DESCRIPTIVE_ONLY"
    normalized = text.casefold()
    for phrase in (
        "alpha",
        "profitable",
        "profitability",
        "tradable",
        "tradability",
        "production-ready",
        "live-ready",
        "deployable",
        "market-beating",
    ):
        assert phrase not in normalized


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
