from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from alpha_system.data.cli_validation import load_cli_config
from alpha_system.data.databento import canonicalize as canonicalize_module
from alpha_system.data.databento.coverage import (
    LONG_NO_TRADE_RUN,
    SUSPECTED_NON_TRADING_SESSION,
    bbo_coverage_report,
    expected_intervals_for_symbols,
    ohlcv_coverage_report,
)
from alpha_system.data.databento.dense_grid import (
    DENSE_OHLCV_PARTITION_SCHEMA,
    run_dense_grid,
)
from alpha_system.data.databento.register_dataset import run_register_dataset
from alpha_system.data.databento.request_spec import DatabentoRequestSpec
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import ReportStatus
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.ibkr.materialize import _load_calendar, _settings_for_symbols

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
INSTRUMENT_CONFIG = Path("configs/data/databento_es_nq_rty_instruments.json")
CALENDAR_CONFIG = Path("configs/data/session_templates_and_calendar.json")
VALIDATION_CONFIG = Path("configs/data/databento_materialize_validation.json")
SPARSE_VERSION = "dsv_databento_ohlcv_sparse_test"
BBO_VERSION = "dsv_databento_bbo_test"
DENSE_VERSION = "dsv_databento_ohlcv_dense_test"
SOURCE_REQUEST_ID = "dbnmanifest_test"


def _spec(
    start: datetime,
    end: datetime,
    *,
    symbols: tuple[str, ...] = ("ES.v.0",),
) -> DatabentoRequestSpec:
    return DatabentoRequestSpec(
        symbols=symbols,
        stype_in="continuous",
        schemas=("ohlcv-1m",),
        start=start,
        end=end,
    )


def _env(data_root: Path) -> dict[str, str]:
    return {"CI": "true", "ALPHA_DATA_ROOT": data_root.as_posix()}


_SYMBOL_META = {
    "ES": {
        "instrument_id": "inst_databento_es",
        "contract_id": "contract_databento_es_v_0_front",
        "series_id": "series_databento_es_front_unadjusted",
    },
    "NQ": {
        "instrument_id": "inst_databento_nq",
        "contract_id": "contract_databento_nq_v_0_front",
        "series_id": "series_databento_nq_front_unadjusted",
    },
    "RTY": {
        "instrument_id": "inst_databento_rty",
        "contract_id": "contract_databento_rty_v_0_front",
        "series_id": "series_databento_rty_front_unadjusted",
    },
}


def _bar(start: datetime, close: Decimal) -> CanonicalBarRecord:
    return _bar_for("ES", start, close)


def _bar_for(symbol: str, start: datetime, close: Decimal) -> CanonicalBarRecord:
    end = start + timedelta(minutes=1)
    meta = _SYMBOL_META[symbol]
    return CanonicalBarRecord.from_mapping(
        {
            "instrument_id": meta["instrument_id"],
            "contract_id": meta["contract_id"],
            "series_id": meta["series_id"],
            "bar_start_ts": start,
            "bar_end_ts": end,
            "event_ts": end,
            "available_ts": end + timedelta(seconds=5),
            "ingested_at": NOW,
            "open": close - Decimal("0.25"),
            "high": close + Decimal("0.25"),
            "low": close - Decimal("0.50"),
            "close": close,
            "volume": Decimal("10"),
            "source": "dsrc_databento_historical",
            "source_request_id": SOURCE_REQUEST_ID,
            "data_version": SPARSE_VERSION,
            "quality_flags": (),
            "session_label": "ETH",
        }
    )


def _bbo(start: datetime, close: Decimal) -> CanonicalBBORecord:
    return _bbo_for("ES", start, close)


def _bbo_for(symbol: str, start: datetime, close: Decimal) -> CanonicalBBORecord:
    end = start + timedelta(minutes=1)
    meta = _SYMBOL_META[symbol]
    bid = close - Decimal("0.25")
    ask = close
    return CanonicalBBORecord.from_mapping(
        {
            "instrument_id": meta["instrument_id"],
            "contract_id": meta["contract_id"],
            "series_id": meta["series_id"],
            "bar_start_ts": start,
            "bar_end_ts": end,
            "event_ts": end,
            "available_ts": end + timedelta(seconds=5),
            "ingested_at": NOW,
            "bid": bid,
            "ask": ask,
            "bid_size": Decimal("1"),
            "ask_size": Decimal("1"),
            "mid": (bid + ask) / Decimal("2"),
            "spread": ask - bid,
            "source": "dsrc_databento_historical",
            "source_request_id": SOURCE_REQUEST_ID,
            "data_version": BBO_VERSION,
            "quality_flags": (),
            "session_label": "ETH",
        }
    )


def _canonical_root(data_root: Path) -> Path:
    return data_root / "databento" / "canonical" / "glbx_mdp3"


def _write_schema(
    data_root: Path,
    *,
    data_version: str,
    partition_schema: str,
    records: tuple[CanonicalBarRecord | CanonicalBBORecord, ...],
) -> Path:
    canonical_root = _canonical_root(data_root)
    canonicalize_module._write_schema_records(
        canonical_root=canonical_root,
        data_version=data_version,
        partition_schema=partition_schema,
        records=records,
    )
    return canonical_root


def _dense_rows(canonical_root: Path, data_version: str) -> tuple[DenseGridBarRecord, ...]:
    rows = []
    schema_root = canonical_root / data_version / f"schema={DENSE_OHLCV_PARTITION_SCHEMA}"
    for path in sorted(schema_root.glob("root=*/part-*")):
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle if line.strip())
        elif path.suffix == ".parquet":
            import pyarrow.parquet as parquet

            rows.extend(parquet.ParquetFile(path).read().to_pylist())
    return tuple(DenseGridBarRecord.from_mapping(row) for row in rows)


def _expected_intervals(
    start: datetime,
    end: datetime,
    *,
    symbols: tuple[str, ...] = ("ES",),
):
    instrument_config = load_cli_config(INSTRUMENT_CONFIG)
    calendar = _load_calendar(CALENDAR_CONFIG, instrument_config)
    settings = _settings_for_symbols(symbols=symbols, instrument_config=instrument_config)
    return expected_intervals_for_symbols(
        symbols=symbols,
        partition_id="development_partition",
        settings_by_symbol=settings,
        calendar=calendar,
        start_ts=start,
        end_ts=end,
    )


def _validation_config_with_threshold(tmp_path: Path, threshold: int) -> Path:
    path = tmp_path / "databento_validation.json"
    path.write_text(
        json.dumps(
            {
                "schema": "alpha_system.databento_materialize_validation_config.v1",
                "allow_non_fixture_input": True,
                "available_latency_seconds": 5,
                "spread_tolerance": "0.000001",
                "require_event_within_bar": True,
                "max_bbo_spread": "10",
                "max_contiguous_no_trade_minutes": threshold,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_dense_grid_emits_synthetic_no_trade_row_and_registers(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "registry.sqlite"
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 3, tzinfo=UTC)
    sparse_bars = (
        _bar(start, Decimal("5000.00")),
        _bar(start + timedelta(minutes=2), Decimal("5001.00")),
    )
    bbo_records = (
        _bbo(start, Decimal("5000.00")),
        _bbo(start + timedelta(minutes=2), Decimal("5001.00")),
    )
    canonical_root = _write_schema(
        data_root,
        data_version=SPARSE_VERSION,
        partition_schema="ohlcv_1m",
        records=sparse_bars,
    )
    _write_schema(
        data_root,
        data_version=BBO_VERSION,
        partition_schema="bbo_1m",
        records=bbo_records,
    )

    summary = run_dense_grid(
        sparse_canonical_root=canonical_root,
        ohlcv_data_version=SPARSE_VERSION,
        request_spec=_spec(start, end),
        output_root=data_root,
        dense_data_version=DENSE_VERSION,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )
    rows = _dense_rows(Path(summary.canonical_root), DENSE_VERSION)
    synthetic = next(row for row in rows if row.bar_start_ts == start + timedelta(minutes=1))

    assert summary.row_count == 3
    assert summary.counts_by_symbol["ES"]["trade_minutes"] == 2
    assert summary.counts_by_symbol["ES"]["no_trade_filled_minutes"] == 1
    assert synthetic.open == synthetic.high == synthetic.low == synthetic.close
    assert synthetic.close == Decimal("5000.00")
    assert synthetic.volume == Decimal("0")
    assert synthetic.has_trade is False
    assert synthetic.synthetic is True
    assert synthetic.fill_method == "previous_close"
    assert "no_trade" in synthetic.quality_flags
    assert synthetic.available_ts == synthetic.bar_end_ts + timedelta(seconds=5)

    registered = run_register_dataset(
        canonical_root=summary.canonical_root,
        request_spec=_spec(start, end),
        registry_path=registry_path,
        ohlcv_data_version=SPARSE_VERSION,
        bbo_data_version=BBO_VERSION,
        dense_data_version=DENSE_VERSION,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    assert registered.registered is True
    assert registered.ohlcv_coverage_status == "PASSING"
    assert registered.dense_coverage_status == "PASSING"
    assert registered.dense_row_count == 3
    with sqlite3.connect(registry_path) as connection:
        versions = {
            row[0]
            for row in connection.execute("SELECT data_version FROM dataset_versions")
        }
    assert versions == {SPARSE_VERSION, BBO_VERSION, DENSE_VERSION}


def test_dense_grid_does_not_forward_fill_across_closed_break(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    start = datetime(2024, 1, 3, 21, 58, tzinfo=UTC)
    end = datetime(2024, 1, 3, 23, 3, tzinfo=UTC)
    sparse_bars = (
        _bar(start, Decimal("5000.00")),
        _bar(datetime(2024, 1, 3, 23, 2, tzinfo=UTC), Decimal("5001.00")),
    )
    canonical_root = _write_schema(
        data_root,
        data_version=SPARSE_VERSION,
        partition_schema="ohlcv_1m",
        records=sparse_bars,
    )

    summary = run_dense_grid(
        sparse_canonical_root=canonical_root,
        ohlcv_data_version=SPARSE_VERSION,
        request_spec=_spec(start, end),
        output_root=data_root,
        dense_data_version=DENSE_VERSION,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )
    starts = {
        row.bar_start_ts: row
        for row in _dense_rows(Path(summary.canonical_root), DENSE_VERSION)
    }

    assert datetime(2024, 1, 3, 21, 59, tzinfo=UTC) in starts
    assert starts[datetime(2024, 1, 3, 21, 59, tzinfo=UTC)].synthetic is True
    assert datetime(2024, 1, 3, 22, 0, tzinfo=UTC) not in starts
    assert datetime(2024, 1, 3, 23, 0, tzinfo=UTC) not in starts
    assert datetime(2024, 1, 3, 23, 1, tzinfo=UTC) not in starts
    assert summary.counts_by_symbol["ES"]["missing_previous_price_minutes"] == 2


def test_whole_missing_expected_session_is_quarantined_without_dense_rows(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    observed_start = datetime(2024, 1, 3, 23, 0, tzinfo=UTC)
    end = observed_start + timedelta(minutes=2)
    sparse_bars = (
        _bar(observed_start, Decimal("5000.00")),
        _bar(observed_start + timedelta(minutes=1), Decimal("5000.25")),
    )
    canonical_root = _write_schema(
        data_root,
        data_version=SPARSE_VERSION,
        partition_schema="ohlcv_1m",
        records=sparse_bars,
    )

    summary = run_dense_grid(
        sparse_canonical_root=canonical_root,
        ohlcv_data_version=SPARSE_VERSION,
        request_spec=_spec(start, end),
        output_root=data_root,
        dense_data_version=DENSE_VERSION,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )
    rows = _dense_rows(Path(summary.canonical_root), DENSE_VERSION)
    coverage = ohlcv_coverage_report(
        coverage_report_id="covr_sparse_suspected_non_trading",
        dataset_version_id=SPARSE_VERSION,
        bars=sparse_bars,
        expected_intervals=_expected_intervals(start, end),
    )

    assert summary.row_count == 2
    assert all(row.bar_start_ts >= observed_start for row in rows)
    assert summary.counts_by_symbol["ES"]["suspected_non_trading_session_count"] == 1
    assert summary.suspected_non_trading_sessions[0]["classification"] == (
        SUSPECTED_NON_TRADING_SESSION
    )
    assert coverage.coverage_status is ReportStatus.PASSING
    assert coverage.missing_intervals == ()
    assert coverage.partition_coverage["suspected_non_trading_session_count"] == 1
    assert coverage.partition_coverage["suspected_non_trading_sessions"][0][
        "classification"
    ] == SUSPECTED_NON_TRADING_SESSION


def test_all_symbols_absent_date_is_recorded() -> None:
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    observed_start = datetime(2024, 1, 3, 23, 0, tzinfo=UTC)
    end = observed_start + timedelta(minutes=1)
    intervals = _expected_intervals(start, end, symbols=("ES", "NQ"))
    report = ohlcv_coverage_report(
        coverage_report_id="covr_sparse_all_symbols_absent",
        dataset_version_id=SPARSE_VERSION,
        bars=(
            _bar_for("ES", observed_start, Decimal("5000.00")),
            _bar_for("NQ", observed_start, Decimal("17000.00")),
        ),
        expected_intervals=intervals,
    )

    assert report.coverage_status is ReportStatus.PASSING
    assert report.partition_coverage["suspected_non_trading_session_count"] == 2
    assert report.partition_coverage["all_symbols_absent_date_count"] == 1
    assert all(
        session["all_symbols_absent"]
        for session in report.partition_coverage["suspected_non_trading_sessions"]
    )


def test_leading_minutes_are_missing_previous_price_not_provider_gap() -> None:
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 3, tzinfo=UTC)
    report = ohlcv_coverage_report(
        coverage_report_id="covr_sparse_leading",
        dataset_version_id=SPARSE_VERSION,
        bars=(_bar(start + timedelta(minutes=2), Decimal("5000.00")),),
        expected_intervals=_expected_intervals(start, end),
    )

    assert report.coverage_status is ReportStatus.PASSING
    metrics = report.symbol_coverage["no_trade_metrics_by_symbol"]["ES"]
    assert metrics["missing_previous_price_minutes"] == 2
    assert metrics["no_trade_filled_minutes"] == 0
    assert metrics["no_trade_ratio"] == 0.0
    assert metrics["provider_gap_minutes"] == 0
    assert report.missing_intervals == ()


def test_long_no_trade_run_passes_and_records_metric() -> None:
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 6, tzinfo=UTC)
    bars = (
        _bar(start, Decimal("5000.00")),
        _bar(start + timedelta(minutes=5), Decimal("5001.00")),
    )
    passing = ohlcv_coverage_report(
        coverage_report_id="covr_sparse_high_notrade",
        dataset_version_id=SPARSE_VERSION,
        bars=bars,
        expected_intervals=_expected_intervals(start, end),
        max_contiguous_no_trade_minutes=10,
    )
    long_run = ohlcv_coverage_report(
        coverage_report_id="covr_sparse_long_no_trade",
        dataset_version_id=SPARSE_VERSION,
        bars=bars,
        expected_intervals=_expected_intervals(start, end),
        max_contiguous_no_trade_minutes=2,
    )

    assert passing.coverage_status is ReportStatus.PASSING
    assert passing.symbol_coverage["no_trade_metrics_by_symbol"]["ES"]["no_trade_ratio"] > 0.5
    assert long_run.coverage_status is ReportStatus.PASSING
    assert long_run.missing_intervals == ()
    metrics = long_run.symbol_coverage["no_trade_metrics_by_symbol"]["ES"]
    assert metrics["provider_gap_minutes"] == 0
    assert metrics["long_no_trade_run_count"] == 1
    assert metrics["long_no_trade_run_minutes"] == 4
    long_run_summary = long_run.symbol_coverage["long_no_trade_runs_by_symbol"]["ES"]
    assert long_run_summary["count"] == 1
    assert long_run_summary["minute_count"] == 4
    assert long_run_summary["blocking"] is False
    assert long_run_summary["sample_runs"][0]["classification"] == LONG_NO_TRADE_RUN
    assert long_run.partition_coverage["long_no_trade_run_count"] == 1
    assert long_run.partition_coverage["long_no_trade_run_minute_count"] == 4


def test_incomplete_chunk_blocks_unless_all_symbols_absent() -> None:
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 3, tzinfo=UTC)
    intervals = _expected_intervals(start, end)
    trading_date = str(intervals[0]["trading_date"])
    blocking = ohlcv_coverage_report(
        coverage_report_id="covr_incomplete_chunk",
        dataset_version_id=SPARSE_VERSION,
        bars=(_bar(start, Decimal("5000.00")),),
        expected_intervals=intervals,
        incomplete_chunks=(trading_date,),
    )
    suppressed = ohlcv_coverage_report(
        coverage_report_id="covr_incomplete_all_absent",
        dataset_version_id=SPARSE_VERSION,
        bars=(),
        expected_intervals=intervals,
        incomplete_chunks=(trading_date,),
    )

    assert blocking.coverage_status is ReportStatus.BLOCKING
    assert blocking.partition_coverage["incomplete_chunk_count"] == 1
    assert blocking.incomplete_chunks[0]["trading_date"] == trading_date
    assert suppressed.coverage_status is ReportStatus.PASSING
    assert suppressed.partition_coverage["incomplete_chunk_count"] == 0
    assert suppressed.partition_coverage["suppressed_incomplete_chunk_count"] == 1
    assert suppressed.partition_coverage["suspected_non_trading_session_count"] == 1


def test_register_succeeds_with_quarantined_whole_session_absence(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "registry.sqlite"
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    observed_start = datetime(2024, 1, 3, 23, 0, tzinfo=UTC)
    end = observed_start + timedelta(minutes=2)
    sparse_bars = (
        _bar(observed_start, Decimal("5000.00")),
        _bar(observed_start + timedelta(minutes=1), Decimal("5000.25")),
    )
    bbo_records = (
        _bbo(observed_start, Decimal("5000.00")),
        _bbo(observed_start + timedelta(minutes=1), Decimal("5000.25")),
    )
    canonical_root = _write_schema(
        data_root,
        data_version=SPARSE_VERSION,
        partition_schema="ohlcv_1m",
        records=sparse_bars,
    )
    _write_schema(
        data_root,
        data_version=BBO_VERSION,
        partition_schema="bbo_1m",
        records=bbo_records,
    )
    dense_summary = run_dense_grid(
        sparse_canonical_root=canonical_root,
        ohlcv_data_version=SPARSE_VERSION,
        request_spec=_spec(start, end),
        output_root=data_root,
        dense_data_version=DENSE_VERSION,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    registered = run_register_dataset(
        canonical_root=dense_summary.canonical_root,
        request_spec=_spec(start, end),
        registry_path=registry_path,
        ohlcv_data_version=SPARSE_VERSION,
        bbo_data_version=BBO_VERSION,
        dense_data_version=DENSE_VERSION,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    assert registered.registered is True
    assert registered.ohlcv_coverage_status == "PASSING"
    assert registered.dense_coverage_status == "PASSING"
    assert registered.blocking_summary["ohlcv_quality_status"] == "WARNING"
    assert registered.blocking_summary["dense_quality_status"] == "WARNING"
    assert registered.blocking_summary["ohlcv_quarantine_summary"][
        "suspected_non_trading_session_count"
    ] == 1
    assert registered.blocking_summary["dense_quarantine_summary"][
        "suspected_non_trading_session_count"
    ] == 1


def test_register_succeeds_for_bounded_long_no_trade_run(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "registry.sqlite"
    validation_config = _validation_config_with_threshold(tmp_path, 2)
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = start + timedelta(minutes=6)
    sparse_bars = (
        _bar(start, Decimal("5000.00")),
        _bar(start + timedelta(minutes=5), Decimal("5001.00")),
    )
    bbo_records = (
        _bbo(start, Decimal("5000.00")),
        _bbo(start + timedelta(minutes=5), Decimal("5001.00")),
    )
    canonical_root = _write_schema(
        data_root,
        data_version=SPARSE_VERSION,
        partition_schema="ohlcv_1m",
        records=sparse_bars,
    )
    _write_schema(
        data_root,
        data_version=BBO_VERSION,
        partition_schema="bbo_1m",
        records=bbo_records,
    )
    dense_summary = run_dense_grid(
        sparse_canonical_root=canonical_root,
        ohlcv_data_version=SPARSE_VERSION,
        request_spec=_spec(start, end),
        output_root=data_root,
        dense_data_version=DENSE_VERSION,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=validation_config,
        env=_env(data_root),
        now=NOW,
    )
    rows = _dense_rows(Path(dense_summary.canonical_root), DENSE_VERSION)
    synthetic_rows = [
        row for row in rows if start < row.bar_start_ts < start + timedelta(minutes=5)
    ]

    registered = run_register_dataset(
        canonical_root=dense_summary.canonical_root,
        request_spec=_spec(start, end),
        registry_path=registry_path,
        ohlcv_data_version=SPARSE_VERSION,
        bbo_data_version=BBO_VERSION,
        dense_data_version=DENSE_VERSION,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=validation_config,
        env=_env(data_root),
        now=NOW,
    )

    assert dense_summary.row_count == 6
    assert dense_summary.provider_gap_sessions == ()
    assert dense_summary.counts_by_symbol["ES"]["no_trade_filled_minutes"] == 4
    assert dense_summary.counts_by_symbol["ES"]["long_no_trade_run_count"] == 1
    assert synthetic_rows
    assert len(synthetic_rows) == 4
    assert all(row.synthetic and not row.has_trade for row in synthetic_rows)
    assert all(row.fill_method == "previous_close" for row in synthetic_rows)
    assert all("no_trade" in row.quality_flags for row in synthetic_rows)
    assert registered.registered is True
    assert registered.registry_path == registry_path.as_posix()
    assert registered.ohlcv_coverage_status == "PASSING"
    assert registered.dense_coverage_status == "PASSING"
    assert registered.blocking_summary["ohlcv_coverage_blocks"] is False
    assert registered.blocking_summary["dense_coverage_blocks"] is False
    assert registered.blocking_summary["ohlcv_no_trade_metrics_by_symbol"]["ES"][
        "provider_gap_minutes"
    ] == 0
    assert registered.blocking_summary["ohlcv_no_trade_metrics_by_symbol"]["ES"][
        "long_no_trade_run_minutes"
    ] == 4
    assert registered.blocking_summary["ohlcv_long_no_trade_runs_by_symbol"]["ES"][
        "count"
    ] == 1
    assert registered.blocking_summary["dense_no_trade_metrics_by_symbol"]["ES"][
        "long_no_trade_run_minutes"
    ] == 0


def test_bbo_coverage_remains_separate_from_ohlcv_no_trade_policy() -> None:
    start = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
    end = datetime(2024, 1, 2, 23, 3, tzinfo=UTC)
    intervals = _expected_intervals(start, end)
    ohlcv = ohlcv_coverage_report(
        coverage_report_id="covr_ohlcv_notrade",
        dataset_version_id=SPARSE_VERSION,
        bars=(
            _bar(start, Decimal("5000.00")),
            _bar(start + timedelta(minutes=2), Decimal("5001.00")),
        ),
        expected_intervals=intervals,
    )
    bbo = bbo_coverage_report(
        coverage_report_id="covr_bbo_still_strict",
        dataset_version_id=BBO_VERSION,
        bbos=(),
        expected_intervals=intervals,
    )

    assert ohlcv.coverage_status is ReportStatus.PASSING
    assert bbo.coverage_status is ReportStatus.BLOCKING
