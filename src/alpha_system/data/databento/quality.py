"""Databento canonical quality gates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import timedelta
from decimal import Decimal

from alpha_system.data.databento.coverage import (
    DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
    classify_dense_grid_coverage,
    classify_sparse_ohlcv_coverage,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import DataQualityReport, ReportStatus
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError

_NO_TRADE_QUALITY_PROXY_FLAG = "no_trade_quality_proxy"


def ohlcv_quality_report(
    *,
    quality_report_id: str,
    dataset_version_id: str,
    bars: Iterable[CanonicalBarRecord | Mapping[str, object]],
    expected_sessions: Iterable[str],
    expected_gap_intervals: Iterable[Mapping[str, object]],
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> DataQualityReport:
    """Build the OHLCV quality report for sparse trade-based Databento bars.

    Acceptable sparse no-trade minutes are filled only inside the quality audit
    as non-output proxy rows so the generic gap checker does not treat
    trade-based absence as a data defect. The proxy rows are never returned,
    persisted, or treated as executable/tradable prices.
    """

    real_bars = tuple(_canonical_bar(bar) for bar in bars)
    intervals = tuple(expected_gap_intervals)
    classification = classify_sparse_ohlcv_coverage(
        bars=real_bars,
        expected_intervals=intervals,
        max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
    )
    proxy_bars = _sparse_quality_proxy_bars(
        real_bars,
        expected_intervals=intervals,
        max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
    )
    report = DataQualityReport.from_canonical_bars(
        quality_report_id=quality_report_id,
        dataset_version_id=dataset_version_id,
        bars=proxy_bars,
        expected_sessions=expected_sessions,
        expected_gap_intervals=intervals,
    )
    return _with_no_trade_metrics(
        report,
        classification.metrics_by_symbol,
        suspected_non_trading_sessions=classification.suspected_non_trading_sessions,
    )


def dense_grid_quality_report(
    *,
    quality_report_id: str,
    dataset_version_id: str,
    dense_bars: Sequence[DenseGridBarRecord | Mapping[str, object]],
    expected_sessions: Iterable[str],
    expected_gap_intervals: Iterable[Mapping[str, object]],
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> DataQualityReport:
    """Build dense-grid quality metrics without treating synthetic rows as trades."""

    dense_records = tuple(
        row if isinstance(row, DenseGridBarRecord) else DenseGridBarRecord.from_mapping(row)
        for row in dense_bars
    )
    if not dense_records:
        msg = "dense grid quality requires at least one dense row"
        raise DataFoundationValidationError(msg)
    intervals = tuple(expected_gap_intervals)
    classification = classify_dense_grid_coverage(
        dense_bars=dense_records,
        expected_intervals=intervals,
        max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
    )
    report = DataQualityReport.from_canonical_bars(
        quality_report_id=quality_report_id,
        dataset_version_id=dataset_version_id,
        bars=tuple(_dense_quality_proxy_bar(row) for row in dense_records),
        expected_sessions=expected_sessions,
        expected_gap_intervals=intervals,
    )
    return _with_no_trade_metrics(
        report,
        classification.metrics_by_symbol,
        suspected_non_trading_sessions=classification.suspected_non_trading_sessions,
    )


def bbo_quality_report(
    *,
    quality_report_id: str,
    dataset_version_id: str,
    bbos: Iterable[CanonicalBBORecord | Mapping[str, object]],
    expected_ohlcv_bars: Iterable[CanonicalBarRecord | Mapping[str, object]],
    expected_sessions: Iterable[str],
    abnormal_spread_threshold: object | None,
) -> DataQualityReport:
    """Build the fail-closed BBO quality report for Databento quotes."""

    return DataQualityReport.from_canonical_bbos(
        quality_report_id=quality_report_id,
        dataset_version_id=dataset_version_id,
        bbos=bbos,
        expected_ohlcv_bars=expected_ohlcv_bars,
        expected_sessions=expected_sessions,
        abnormal_spread_threshold=abnormal_spread_threshold,
    )


def _sparse_quality_proxy_bars(
    bars: Sequence[CanonicalBarRecord],
    *,
    expected_intervals: Sequence[Mapping[str, object]],
    max_contiguous_no_trade_minutes: int,
) -> tuple[CanonicalBarRecord, ...]:
    by_key: dict[tuple[str, str, str], dict[object, CanonicalBarRecord]] = {}
    for bar in bars:
        by_key.setdefault(_group_key(bar), {})[bar.bar_start_ts] = bar

    output: list[CanonicalBarRecord] = []
    for interval in expected_intervals:
        normalized = _normalize_interval_for_quality(interval)
        key = (
            str(normalized["instrument_id"]),
            str(normalized["contract_id"]),
            str(normalized["session_label"]),
        )
        real_by_start = by_key.get(key, {})
        expected_starts = _minute_starts(normalized["start_ts"], normalized["end_ts"])
        observed = {start for start in expected_starts if start in real_by_start}
        if not observed:
            continue
        prior_close: Decimal | None = None
        prior_real: CanonicalBarRecord | None = None
        for start in expected_starts:
            real = real_by_start.get(start)
            if real is not None:
                output.append(real)
                prior_close = real.close
                prior_real = real
                continue
            if prior_close is None or prior_real is None:
                continue
            output.append(
                _proxy_bar_from_previous_close(
                    template=prior_real,
                    bar_start_ts=start,
                    previous_close=prior_close,
                )
            )
    return tuple(sorted(output, key=lambda bar: (_group_key(bar), bar.bar_start_ts)))


def _dense_quality_proxy_bar(row: DenseGridBarRecord) -> CanonicalBarRecord:
    volume = Decimal("1") if row.synthetic else row.volume
    return CanonicalBarRecord.from_mapping(
        {
            "instrument_id": row.instrument_id,
            "contract_id": row.contract_id,
            "series_id": row.series_id,
            "bar_start_ts": row.bar_start_ts,
            "bar_end_ts": row.bar_end_ts,
            "event_ts": row.event_ts,
            "available_ts": row.available_ts,
            "ingested_at": row.ingested_at,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": volume,
            "source": row.source,
            "source_request_id": row.source_request_id,
            "data_version": row.data_version,
            "quality_flags": row.quality_flags,
            "session_label": row.session_label,
        }
    )


def _proxy_bar_from_previous_close(
    *,
    template: CanonicalBarRecord,
    bar_start_ts: object,
    previous_close: Decimal,
) -> CanonicalBarRecord:
    start = bar_start_ts
    end = start + timedelta(minutes=1)
    return CanonicalBarRecord.from_mapping(
        {
            "instrument_id": template.instrument_id,
            "contract_id": template.contract_id,
            "series_id": template.series_id,
            "bar_start_ts": start,
            "bar_end_ts": end,
            "event_ts": end,
            "available_ts": end,
            "ingested_at": template.ingested_at,
            "open": previous_close,
            "high": previous_close,
            "low": previous_close,
            "close": previous_close,
            "volume": Decimal("1"),
            "source": template.source,
            "source_request_id": template.source_request_id,
            "data_version": template.data_version,
            "quality_flags": (_NO_TRADE_QUALITY_PROXY_FLAG,),
            "session_label": template.session_label,
        }
    )


def _with_no_trade_metrics(
    report: DataQualityReport,
    metrics_by_symbol: Mapping[str, Mapping[str, object]],
    *,
    suspected_non_trading_sessions: Sequence[Mapping[str, object]] = (),
) -> DataQualityReport:
    values = dict(report.to_mapping())
    gap_summary = dict(values["gap_summary"])
    gap_summary["no_trade_metrics_by_symbol"] = metrics_by_symbol
    if suspected_non_trading_sessions:
        gap_summary.update(_quality_quarantine_summary(suspected_non_trading_sessions))
        if gap_summary["status"] == ReportStatus.PASSING.value:
            gap_summary["status"] = ReportStatus.WARNING.value
            gap_summary["blocking"] = False
        if values["status"] == ReportStatus.PASSING.value:
            values["status"] = ReportStatus.WARNING.value
    values["gap_summary"] = gap_summary
    return DataQualityReport.from_mapping(values)


def _quality_quarantine_summary(
    sessions: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    all_absent_dates = tuple(
        sorted(
            {
                str(session["session_date"])
                for session in sessions
                if bool(session["all_symbols_absent"])
            }
        )
    )
    return {
        "suspected_non_trading_session_count": len(sessions),
        "suspected_non_trading_session_minute_count": sum(
            int(session["minute_count"]) for session in sessions
        ),
        "suspected_non_trading_sessions": tuple(sessions[:25]),
        "suspected_non_trading_sessions_truncated": len(sessions) > 25,
        "all_symbols_absent_dates": all_absent_dates[:25],
        "all_symbols_absent_date_count": len(all_absent_dates),
    }


def _canonical_bar(bar: CanonicalBarRecord | Mapping[str, object]) -> CanonicalBarRecord:
    return bar if isinstance(bar, CanonicalBarRecord) else CanonicalBarRecord.from_mapping(bar)


def _group_key(bar: CanonicalBarRecord) -> tuple[str, str, str]:
    return (bar.instrument_id, bar.contract_id, bar.session_label)


def _normalize_interval_for_quality(value: Mapping[str, object]) -> Mapping[str, object]:
    start = value["start_ts"]
    end = value["end_ts"]
    return {
        "instrument_id": value["instrument_id"],
        "contract_id": value["contract_id"],
        "session_label": value["session_label"],
        "start_ts": start if hasattr(start, "tzinfo") else _parse_datetime_text(start),
        "end_ts": end if hasattr(end, "tzinfo") else _parse_datetime_text(end),
    }


def _parse_datetime_text(value: object) -> object:
    from datetime import datetime

    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _minute_starts(start: object, end: object) -> tuple[object, ...]:
    current = start
    starts = []
    while current < end:
        starts.append(current)
        current += timedelta(minutes=1)
    return tuple(starts)


__all__ = ["bbo_quality_report", "dense_grid_quality_report", "ohlcv_quality_report"]
