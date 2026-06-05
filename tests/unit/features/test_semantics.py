from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.input_views import (
    BBOInputRow,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.features.semantics import (
    BBO_MISSINGNESS_QUALITY_FLAGS,
    bbo_invariants_hold,
    bbo_quote_semantics,
    dense_grid_bar_semantics,
    has_missing_bbo,
    has_missing_or_abnormal_bbo,
    is_bbo_quarantined,
    is_real_trade_bar,
    is_synthetic_no_trade_bar,
    is_valid_bbo_quote,
    select_missing_or_abnormal_bbo_rows,
    select_real_trade_bars,
    select_synthetic_no_trade_bars,
    select_valid_bbo_quotes,
)

DATASET_ID = "dsv_semantics_fixture_v1"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


def test_synthetic_no_trade_rows_are_flagged_and_excluded_from_trade_bars() -> None:
    real_row, no_trade_row = _accepted_version().dense_grid_bars_from_mappings(
        (_dense_trade_mapping(), _dense_no_trade_mapping()),
        partition_id="development_partition",
        purpose="feature_input",
    )

    no_trade = dense_grid_bar_semantics(no_trade_row)

    assert no_trade.has_trade is False
    assert no_trade.synthetic is True
    assert no_trade.fill_method == "previous_close"
    assert no_trade.provider_bar_ref is None
    assert no_trade.no_trade is True
    assert is_synthetic_no_trade_bar(no_trade_row) is True
    assert is_real_trade_bar(no_trade_row) is False
    assert select_real_trade_bars((real_row, no_trade_row)) == (real_row,)
    assert select_synthetic_no_trade_bars((real_row, no_trade_row)) == (no_trade_row,)


def test_sparse_ohlcv_input_rows_remain_provider_trade_truth() -> None:
    view = build_ohlcv_input_view(
        _accepted_version(),
        (_bar_mapping(),),
        partition_id="development_partition",
        purpose="feature_input",
    )
    row = view.rows[0]

    assert is_real_trade_bar(row) is True
    assert is_synthetic_no_trade_bar(row) is False
    assert select_real_trade_bars(view.rows) == (row,)
    assert select_synthetic_no_trade_bars(view.rows) == ()


def test_missing_and_quarantined_bbo_rows_are_flagged_not_filled() -> None:
    view = build_bbo_input_view(
        _accepted_version(),
        (_missing_bbo_mapping(), _bbo_mapping(), _quarantined_bbo_mapping()),
        partition_id="development_partition",
        purpose="feature_input",
    )
    missing_row, valid_row, quarantined_row = view.rows

    assert BBO_MISSINGNESS_QUALITY_FLAGS == frozenset({"missing_bbo", "bbo_quarantined"})
    assert has_missing_bbo(missing_row) is True
    assert is_bbo_quarantined(quarantined_row) is True
    assert has_missing_or_abnormal_bbo(valid_row) is False
    assert select_missing_or_abnormal_bbo_rows(view.rows) == (missing_row, quarantined_row)
    assert select_valid_bbo_quotes(view.rows) == (valid_row,)

    assert missing_row.bid == Decimal("0")
    assert missing_row.ask == Decimal("0")
    assert missing_row.mid == Decimal("0")
    assert missing_row.microprice == Decimal("0")
    assert valid_row.bid == Decimal("99.50")
    assert valid_row.ask == Decimal("100.50")


def test_valid_bbo_rows_preserve_canonical_invariants() -> None:
    row = build_bbo_input_view(
        _accepted_version(),
        (_bbo_mapping(),),
        partition_id="development_partition",
        purpose="feature_input",
    ).rows[0]

    semantics = bbo_quote_semantics(row)

    assert semantics.missing_bbo is False
    assert semantics.bbo_quarantined is False
    assert semantics.missing_or_abnormal is False
    assert semantics.invariants_hold is True
    assert bbo_invariants_hold(row) is True
    assert is_valid_bbo_quote(row) is True


def test_bbo_microprice_without_valid_sizes_fails_closed() -> None:
    row = BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_CONTINUOUS",
        bar_start_ts=_dt("2024-01-02T14:31:00+00:00"),
        bar_end_ts=_dt("2024-01-02T14:32:00+00:00"),
        event_ts=_dt("2024-01-02T14:32:00+00:00"),
        available_ts=_dt("2024-01-02T14:32:05+00:00"),
        ingested_at=_dt("2024-01-02T15:00:00+00:00"),
        bid=Decimal("99.50"),
        ask=Decimal("100.50"),
        bid_size=Decimal("0"),
        ask_size=Decimal("6"),
        mid=Decimal("100.00"),
        spread=Decimal("1.00"),
        data_version=DATASET_ID,
        quality_flags=(),
        session_label="ETH",
        microprice=Decimal("100.10"),
    )

    assert bbo_invariants_hold(row) is False
    assert is_valid_bbo_quote(row) is False


def test_predicates_are_deterministic_and_unsupported_rows_fail_closed() -> None:
    row = _accepted_version().dense_grid_bars_from_mappings(
        (_dense_no_trade_mapping(),),
        partition_id="development_partition",
        purpose="feature_input",
    )[0]

    assert is_synthetic_no_trade_bar(row) is is_synthetic_no_trade_bar(row)
    assert dense_grid_bar_semantics(row) == dense_grid_bar_semantics(row)
    with pytest.raises(DataFoundationValidationError, match="trade-bar semantics"):
        is_real_trade_bar({"has_trade": True})
    with pytest.raises(DataFoundationValidationError, match="BBO semantics"):
        is_valid_bbo_quote({"bid": "99.50"})


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


def _bar_mapping() -> dict[str, object]:
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


def _dense_trade_mapping() -> dict[str, object]:
    return {
        **_bar_mapping(),
        "has_trade": True,
        "synthetic": False,
        "fill_method": None,
        "provider_bar_ref": "dsv_semantics_sparse_bar_1",
    }


def _dense_no_trade_mapping() -> dict[str, object]:
    return {
        **_bar_mapping(),
        "bar_start_ts": "2024-01-02T14:32:00+00:00",
        "bar_end_ts": "2024-01-02T14:33:00+00:00",
        "event_ts": "2024-01-02T14:33:00+00:00",
        "available_ts": "2024-01-02T14:33:05+00:00",
        "ingested_at": "2024-01-02T15:00:01+00:00",
        "open": "100.75",
        "high": "100.75",
        "low": "100.75",
        "close": "100.75",
        "volume": "0",
        "quality_flags": ("no_trade",),
        "has_trade": False,
        "synthetic": True,
        "fill_method": "previous_close",
        "provider_bar_ref": None,
    }


def _bbo_mapping() -> dict[str, object]:
    return {
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


def _missing_bbo_mapping() -> dict[str, object]:
    return {
        **_bbo_mapping(),
        "available_ts": "2024-01-02T14:32:00+00:00",
        "bid": "0",
        "ask": "0",
        "bid_size": "0",
        "ask_size": "0",
        "mid": "0",
        "spread": "0",
        "quality_flags": ("missing_bbo",),
        "spread_ticks": "0",
        "microprice": "0",
        "bid_order_count": 0,
        "ask_order_count": 0,
    }


def _quarantined_bbo_mapping() -> dict[str, object]:
    return {
        **_bbo_mapping(),
        "available_ts": "2024-01-02T14:32:10+00:00",
        "quality_flags": ("bbo_quarantined",),
        "source_request_id": "req_fixture_2",
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
