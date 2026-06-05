from __future__ import annotations

from datetime import UTC, datetime

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.input_views import build_canonical_input_views

DATASET_ID = "dsv_input_view_no_lookahead_fixture_v1"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_as_of_uses_available_ts_not_event_ts_or_ingested_at() -> None:
    views = build_canonical_input_views(
        _accepted_version(),
        bar_rows=(_late_available_bar(), _early_available_bar()),
        bbo_rows=(_late_available_bbo(), _early_available_bbo()),
        partition_id="development_partition",
        purpose="feature_input",
    )

    usable = views.as_of(_dt("2024-01-02T14:33:00+00:00"))

    assert [row.bar_start_ts for row in usable.ohlcv.rows] == [
        _dt("2024-01-02T14:31:00+00:00")
    ]
    assert usable.ohlcv.rows[0].event_ts == _dt("2024-01-02T14:32:00+00:00")
    assert usable.ohlcv.rows[0].ingested_at == _dt("2024-01-02T15:00:00+00:00")
    assert usable.ohlcv.rows[0].available_ts == _dt("2024-01-02T14:32:05+00:00")

    assert [row.bar_start_ts for row in usable.bbo.rows] == [
        _dt("2024-01-02T14:31:00+00:00")
    ]
    assert usable.bbo.rows[0].event_ts == _dt("2024-01-02T14:32:00+00:00")
    assert usable.bbo.rows[0].ingested_at == _dt("2024-01-02T15:00:00+00:00")
    assert usable.bbo.rows[0].available_ts == _dt("2024-01-02T14:32:05+00:00")


def _accepted_version() -> AcceptedDatasetVersion:
    quality_report = _quality_report()
    return AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=_dataset_version(quality_report),
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=_coverage_report(),
    )


def _dataset_version(quality_report: DataQualityReport) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=DATASET_ID,
        source="dsrc_synthetic_feed",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=datetime(2024, 1, 2, 14, 30, tzinfo=UTC),
        end_ts=datetime(2024, 1, 2, 14, 33, tzinfo=UTC),
        contract_universe=("ESM4",),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=datetime(2024, 1, 2, 15, 0, tzinfo=UTC),
    )


def _quality_report() -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{DATASET_ID}",
        dataset_version_id=DATASET_ID,
        gap_summary=_quality_summary(),
        duplicate_summary=_quality_summary(),
        non_monotonic_summary=_quality_summary(),
        ohlc_errors=_quality_summary(),
        zero_negative_price_errors=_quality_summary(),
        zero_volume_anomalies=_quality_summary(),
        dst_anomalies=_quality_summary(),
        session_coverage=_quality_summary(),
        roll_discontinuities=_quality_summary(),
        provider_error_summary=_quality_summary(),
        bbo_missing_metric=_quality_summary(),
        abnormal_spread_summary=_quality_summary(),
        status=ReportStatus.PASSING,
    )


def _quality_summary() -> dict[str, object]:
    return {
        "count": 0,
        "status": ReportStatus.PASSING.value,
        "blocking": False,
    }


def _coverage_report() -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{DATASET_ID}",
        dataset_version_id=DATASET_ID,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(include_partition_counts=True),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    if include_partition_counts:
        summary["missing_interval_count"] = 0
        summary["incomplete_chunk_count"] = 0
    return summary


def _late_available_bar() -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:30:00+00:00",
        "bar_end_ts": "2024-01-02T14:31:00+00:00",
        "event_ts": "2024-01-02T14:31:00+00:00",
        "available_ts": "2024-01-02T14:40:00+00:00",
        "ingested_at": "2024-01-02T14:31:02+00:00",
        "open": "100.00",
        "high": "101.00",
        "low": "99.50",
        "close": "100.25",
        "volume": "10",
        "source": "dsrc_synthetic_feed",
        "source_request_id": "req_fixture_0",
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": "ETH",
    }


def _early_available_bar() -> dict[str, object]:
    return {
        **_late_available_bar(),
        "bar_start_ts": "2024-01-02T14:31:00+00:00",
        "bar_end_ts": "2024-01-02T14:32:00+00:00",
        "event_ts": "2024-01-02T14:32:00+00:00",
        "available_ts": "2024-01-02T14:32:05+00:00",
        "ingested_at": "2024-01-02T15:00:00+00:00",
        "open": "100.25",
        "low": "100.00",
        "close": "100.75",
        "source_request_id": "req_fixture_1",
    }


def _late_available_bbo() -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:30:00+00:00",
        "bar_end_ts": "2024-01-02T14:31:00+00:00",
        "event_ts": "2024-01-02T14:31:00+00:00",
        "available_ts": "2024-01-02T14:40:00+00:00",
        "ingested_at": "2024-01-02T14:31:02+00:00",
        "bid": "99.50",
        "ask": "100.50",
        "bid_size": "4",
        "ask_size": "6",
        "mid": "100.00",
        "spread": "1.00",
        "source": "dsrc_synthetic_feed",
        "source_request_id": "req_fixture_0",
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": "ETH",
        "spread_ticks": "4",
        "microprice": "100.10",
        "bid_order_count": 2,
        "ask_order_count": 3,
    }


def _early_available_bbo() -> dict[str, object]:
    return {
        **_late_available_bbo(),
        "bar_start_ts": "2024-01-02T14:31:00+00:00",
        "bar_end_ts": "2024-01-02T14:32:00+00:00",
        "event_ts": "2024-01-02T14:32:00+00:00",
        "available_ts": "2024-01-02T14:32:05+00:00",
        "ingested_at": "2024-01-02T15:00:00+00:00",
        "source_request_id": "req_fixture_1",
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
