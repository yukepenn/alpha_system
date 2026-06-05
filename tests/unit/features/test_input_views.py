from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features import input_views
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.input_views import (
    BBO_QUALITY_FLAG_TOKENS,
    build_canonical_input_views,
)

DATASET_ID = "dsv_input_view_fixture_v1"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_builders_route_through_consumption_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    accepted = _accepted_version()
    bar_record = CanonicalBarRecord.from_mapping(_bar_mapping(1))
    bbo_record = CanonicalBBORecord.from_mapping(_bbo_mapping(1))
    calls: list[tuple[str, object, object, object]] = []

    def fake_bars(
        observed: object,
        rows: object,
        *,
        partition_id: object,
        purpose: object,
        **_: object,
    ) -> tuple[CanonicalBarRecord, ...]:
        calls.append(("bars", observed, partition_id, purpose))
        assert tuple(rows) == ({"canonical": "bar"},)
        return (bar_record,)

    def fake_bbos(
        observed: object,
        rows: object,
        *,
        partition_id: object,
        purpose: object,
        **_: object,
    ) -> tuple[CanonicalBBORecord, ...]:
        calls.append(("bbos", observed, partition_id, purpose))
        assert tuple(rows) == ({"canonical": "bbo"},)
        return (bbo_record,)

    monkeypatch.setattr(input_views.consumption, "canonical_bars_from_mappings", fake_bars)
    monkeypatch.setattr(input_views.consumption, "canonical_bbos_from_mappings", fake_bbos)

    views = build_canonical_input_views(
        accepted,
        bar_rows=({"canonical": "bar"},),
        bbo_rows=({"canonical": "bbo"},),
        partition_id="development_partition",
        purpose="feature_input",
    )

    assert views.ohlcv.rows[0].data_version == DATASET_ID
    assert views.bbo.rows[0].data_version == DATASET_ID
    assert calls == [
        ("bars", accepted, "development_partition", "feature_input"),
        ("bbos", accepted, "development_partition", "feature_input"),
    ]


def test_views_are_read_only_and_ordered_by_available_ts_only() -> None:
    views = build_canonical_input_views(
        _accepted_version(),
        bar_rows=(_bar_mapping(0), _bar_mapping(1)),
        bbo_rows=(_bbo_mapping(0), _bbo_mapping(1)),
        partition_id="development_partition",
        purpose="feature_input",
    )

    assert [row.available_ts for row in views.ohlcv.rows] == [
        _dt("2024-01-02T14:32:05+00:00"),
        _dt("2024-01-02T14:33:00+00:00"),
    ]
    assert [row.event_ts for row in views.ohlcv.rows] == [
        _dt("2024-01-02T14:32:00+00:00"),
        _dt("2024-01-02T14:31:00+00:00"),
    ]
    assert [row.ingested_at for row in views.bbo.rows] == [
        _dt("2024-01-02T15:00:00+00:00"),
        _dt("2024-01-02T14:31:02+00:00"),
    ]

    with pytest.raises(FrozenInstanceError):
        views.ohlcv.rows[0].close = Decimal("1")
    with pytest.raises(AttributeError):
        views.bbo.rows.append(views.bbo.rows[0])  # type: ignore[attr-defined]


def test_bbo_fields_and_quality_flags_are_exposed_without_imputation() -> None:
    views = build_canonical_input_views(
        _accepted_version(),
        bar_rows=(_bar_mapping(1),),
        bbo_rows=(_missing_bbo_mapping(), _bbo_mapping(1)),
        partition_id="development_partition",
        purpose="feature_input",
    )

    missing_row = views.bbo.rows[0]
    quoted_row = views.bbo.rows[1]

    assert BBO_QUALITY_FLAG_TOKENS == frozenset({"missing_bbo", "bbo_quarantined"})
    assert missing_row.quality_flags == ("missing_bbo", "bbo_quarantined")
    assert missing_row.bid == Decimal("0")
    assert missing_row.ask == Decimal("0")
    assert missing_row.microprice == Decimal("0")
    assert quoted_row.bid == Decimal("99.50")
    assert quoted_row.ask == Decimal("100.50")
    assert quoted_row.bid_size == Decimal("4")
    assert quoted_row.ask_size == Decimal("6")
    assert quoted_row.mid == Decimal("100.00")
    assert quoted_row.spread == Decimal("1.00")
    assert quoted_row.spread_ticks == Decimal("4")
    assert quoted_row.microprice == Decimal("100.10")
    assert quoted_row.bid_order_count == 2
    assert quoted_row.ask_order_count == 3


def test_raw_provider_shaped_fields_are_rejected_before_view_rows_are_exposed() -> None:
    row = {**_bar_mapping(1), "provider_ts": "2024-01-02T14:31:00+00:00"}

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        build_canonical_input_views(
            _accepted_version(),
            bar_rows=(row,),
            bbo_rows=(_bbo_mapping(1),),
            partition_id="development_partition",
            purpose="feature_input",
        )


def test_combined_as_of_returns_rows_usable_by_available_ts() -> None:
    views = build_canonical_input_views(
        _accepted_version(),
        bar_rows=(_bar_mapping(0), _bar_mapping(1)),
        bbo_rows=(_bbo_mapping(0), _bbo_mapping(1)),
        partition_id="development_partition",
        purpose="feature_input",
    )

    usable = views.as_of(_dt("2024-01-02T14:32:30+00:00"))

    assert [row.bar_start_ts for row in usable.ohlcv.rows] == [
        _dt("2024-01-02T14:31:00+00:00")
    ]
    assert [row.bar_start_ts for row in usable.bbo.rows] == [
        _dt("2024-01-02T14:31:00+00:00")
    ]
    assert views.available_timestamps == (
        _dt("2024-01-02T14:32:05+00:00"),
        _dt("2024-01-02T14:33:00+00:00"),
    )


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


def _bar_mapping(index: int) -> dict[str, object]:
    if index == 0:
        return {
            **_bar_mapping(1),
            "bar_start_ts": "2024-01-02T14:30:00+00:00",
            "bar_end_ts": "2024-01-02T14:31:00+00:00",
            "event_ts": "2024-01-02T14:31:00+00:00",
            "available_ts": "2024-01-02T14:33:00+00:00",
            "ingested_at": "2024-01-02T14:31:02+00:00",
            "close": "100.25",
        }
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:31:00+00:00",
        "bar_end_ts": "2024-01-02T14:32:00+00:00",
        "event_ts": "2024-01-02T14:32:00+00:00",
        "available_ts": "2024-01-02T14:32:05+00:00",
        "ingested_at": "2024-01-02T15:00:00+00:00",
        "open": "100.25",
        "high": "101.00",
        "low": "100.00",
        "close": "100.75",
        "volume": "10",
        "source": "dsrc_synthetic_feed",
        "source_request_id": "req_fixture_1",
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": "ETH",
    }


def _bbo_mapping(index: int) -> dict[str, object]:
    row = {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": "2024-01-02T14:31:00+00:00",
        "bar_end_ts": "2024-01-02T14:32:00+00:00",
        "event_ts": "2024-01-02T14:32:00+00:00",
        "available_ts": "2024-01-02T14:32:05+00:00",
        "ingested_at": "2024-01-02T15:00:00+00:00",
        "bid": "99.50",
        "ask": "100.50",
        "bid_size": "4",
        "ask_size": "6",
        "mid": "100.00",
        "spread": "1.00",
        "source": "dsrc_synthetic_feed",
        "source_request_id": "req_fixture_1",
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": "ETH",
        "spread_ticks": "4",
        "microprice": "100.10",
        "bid_order_count": 2,
        "ask_order_count": 3,
    }
    if index == 0:
        row.update(
            {
                "bar_start_ts": "2024-01-02T14:30:00+00:00",
                "bar_end_ts": "2024-01-02T14:31:00+00:00",
                "event_ts": "2024-01-02T14:31:00+00:00",
                "available_ts": "2024-01-02T14:33:00+00:00",
                "ingested_at": "2024-01-02T14:31:02+00:00",
                "source_request_id": "req_fixture_0",
            }
        )
    return row


def _missing_bbo_mapping() -> dict[str, object]:
    return {
        **_bbo_mapping(1),
        "available_ts": "2024-01-02T14:32:00+00:00",
        "bid": "0",
        "ask": "0",
        "bid_size": "0",
        "ask_size": "0",
        "mid": "0",
        "spread": "0",
        "quality_flags": ("missing_bbo", "bbo_quarantined"),
        "spread_ticks": "0",
        "microprice": "0",
        "bid_order_count": 0,
        "ask_order_count": 0,
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
