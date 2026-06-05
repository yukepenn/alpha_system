"""Databento canonical coverage gates.

Databento OHLCV-1m is trade-based: a missing sparse bar can be a legitimate
no-trade minute. This module keeps that provider truth separate from blocking
    provider-data gaps and from the derived dense research grid.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from types import MappingProxyType

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import CoverageReport, ReportStatus
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr.materialize import _expected_intervals

DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES = 240
NO_TRADE_INTERVAL = "no_trade_interval"
MISSING_PREVIOUS_PRICE = "missing_previous_price"
PROVIDER_DATA_GAP = "provider_data_gap"
SUSPECTED_NON_TRADING_SESSION = "suspected_non_trading_session"
DENSE_GRID_MISSING_ROW = "dense_grid_missing_row"
LONG_NO_TRADE_RUN = "long_no_trade_run"

BAR_SIZE_SECONDS_1M = 60
MAX_COVERAGE_INTERVALS = 25


@dataclass(frozen=True, slots=True)
class DatabentoCoverageClassification:
    """Aggregate no-trade/provider-gap classification for Databento OHLCV."""

    metrics_by_symbol: Mapping[str, Mapping[str, object]]
    provider_gap_intervals: tuple[Mapping[str, object], ...]
    provider_gap_sessions: tuple[Mapping[str, object], ...]
    suspected_non_trading_sessions: tuple[Mapping[str, object], ...]
    long_no_trade_runs: tuple[Mapping[str, object], ...]
    interval_metrics: tuple[Mapping[str, object], ...]

    @property
    def provider_gap_minute_count(self) -> int:
        return sum(
            int(interval["missing_bar_count"]) for interval in self.provider_gap_intervals
        )

    @property
    def suspected_non_trading_session_count(self) -> int:
        return len(self.suspected_non_trading_sessions)

    @property
    def suspected_non_trading_minute_count(self) -> int:
        return sum(
            int(session["minute_count"]) for session in self.suspected_non_trading_sessions
        )

    @property
    def long_no_trade_run_count(self) -> int:
        return len(self.long_no_trade_runs)

    @property
    def long_no_trade_minute_count(self) -> int:
        return sum(int(run["minute_count"]) for run in self.long_no_trade_runs)


def expected_intervals_for_bars(
    *,
    bars: Sequence[CanonicalBarRecord],
    symbols: Sequence[str],
    partition_id: str,
    settings_by_symbol: Mapping[str, object],
    calendar: object,
    start_ts: object,
    end_ts: object,
) -> tuple[Mapping[str, object], ...]:
    """Return session-aware expected intervals using the shared materializer logic."""

    return _expected_intervals(
        bars,
        symbols=symbols,
        partition_id=partition_id,
        settings_by_symbol=settings_by_symbol,
        calendar=calendar,
        start_ts=_parse_aware_datetime(start_ts, "start_ts"),
        end_ts=_parse_aware_datetime(end_ts, "end_ts"),
    )


def expected_intervals_for_symbols(
    *,
    symbols: Sequence[str],
    partition_id: str,
    settings_by_symbol: Mapping[str, object],
    calendar: object,
    start_ts: object,
    end_ts: object,
) -> tuple[Mapping[str, object], ...]:
    """Return clipped session intervals for all requested symbols.

    This variant does not require observed bars, so an entirely missing expected
    session can still be classified as a suspected non-trading session.
    """

    start = _parse_aware_datetime(start_ts, "start_ts")
    end = _parse_aware_datetime(end_ts, "end_ts")
    if end <= start:
        msg = "end_ts must be greater than start_ts"
        raise DataFoundationValidationError(msg)

    sessions = _trading_sessions_for_window(calendar, start_ts=start, end_ts=end)
    intervals: list[Mapping[str, object]] = []
    for symbol in symbols:
        root = str(symbol).upper()
        settings = settings_by_symbol[root]
        for session in sessions:
            interval_start = _ceil_to_minute(max(session.open_ts, start))
            interval_end = _floor_to_minute(min(session.close_ts, end))
            if interval_end <= interval_start:
                continue
            intervals.append(
                MappingProxyType(
                    {
                        "symbol": root,
                        "instrument_id": str(settings.instrument_id),
                        "contract_id": _contract_id_for_symbol(root, settings),
                        "session_label": str(settings.session_label).upper(),
                        "start_ts": interval_start.isoformat(),
                        "end_ts": interval_end.isoformat(),
                        "partition_id": partition_id,
                        "session_id": session.session_id,
                        "trading_date": session.trading_date.isoformat(),
                    }
                )
            )
    if not intervals:
        msg = "no expected Databento intervals overlap the requested window"
        raise DataFoundationValidationError(msg)
    return tuple(intervals)


def ohlcv_coverage_report(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    bars: Sequence[CanonicalBarRecord],
    expected_intervals: Sequence[Mapping[str, object]],
    incomplete_chunks: Iterable[object] = (),
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> CoverageReport:
    """Build OHLCV coverage with sparse no-trade minutes treated as acceptable.

    Coverage blocks only on incomplete raw chunks. Mid-session missing runs
    bounded by real trades, including runs longer than
    ``max_contiguous_no_trade_minutes``, are non-blocking no-trade metrics.
    """

    classification = classify_sparse_ohlcv_coverage(
        bars=bars,
        expected_intervals=expected_intervals,
        max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
    )
    return _coverage_report_from_classification(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        classification=classification,
        incomplete_chunks=incomplete_chunks,
    )


def dense_grid_coverage_report(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    dense_bars: Sequence[DenseGridBarRecord | Mapping[str, object]],
    expected_intervals: Sequence[Mapping[str, object]],
    incomplete_chunks: Iterable[object] = (),
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> CoverageReport:
    """Build dense-grid coverage without treating synthetic rows as trades."""

    classification = classify_dense_grid_coverage(
        dense_bars=dense_bars,
        expected_intervals=expected_intervals,
        max_contiguous_no_trade_minutes=max_contiguous_no_trade_minutes,
    )
    return _coverage_report_from_classification(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        classification=classification,
        incomplete_chunks=incomplete_chunks,
    )


def bbo_coverage_report(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    bbos: Sequence[CanonicalBBORecord],
    expected_intervals: Sequence[Mapping[str, object]],
) -> CoverageReport:
    """Build the existing fail-closed BBO coverage report."""

    return CoverageReport.from_canonical_bbos(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        bbos=bbos,
        expected_intervals=expected_intervals,
    )


def classify_sparse_ohlcv_coverage(
    *,
    bars: Sequence[CanonicalBarRecord | Mapping[str, object]],
    expected_intervals: Sequence[Mapping[str, object]],
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> DatabentoCoverageClassification:
    """Classify sparse OHLCV no-bar minutes under the Databento trade policy."""

    threshold = _positive_threshold(max_contiguous_no_trade_minutes)
    bar_views = tuple(_canonical_bar(bar) for bar in bars)
    starts_by_key: dict[tuple[str, str, str], set[datetime]] = defaultdict(set)
    for bar in bar_views:
        starts_by_key[_group_key(bar)].add(bar.bar_start_ts)
    return _classify_intervals(
        expected_intervals=expected_intervals,
        observed_starts_by_key=starts_by_key,
        trade_starts_by_key=starts_by_key,
        synthetic_starts_by_key={},
        max_contiguous_no_trade_minutes=threshold,
        dense_grid=False,
    )


def classify_dense_grid_coverage(
    *,
    dense_bars: Sequence[DenseGridBarRecord | Mapping[str, object]],
    expected_intervals: Sequence[Mapping[str, object]],
    max_contiguous_no_trade_minutes: int = DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES,
) -> DatabentoCoverageClassification:
    """Classify dense-grid rows while keeping synthetic rows non-executable."""

    threshold = _positive_threshold(max_contiguous_no_trade_minutes)
    observed_by_key: dict[tuple[str, str, str], set[datetime]] = defaultdict(set)
    trade_by_key: dict[tuple[str, str, str], set[datetime]] = defaultdict(set)
    synthetic_by_key: dict[tuple[str, str, str], set[datetime]] = defaultdict(set)
    for raw in dense_bars:
        row = raw if isinstance(raw, DenseGridBarRecord) else DenseGridBarRecord.from_mapping(raw)
        key = (row.instrument_id, row.contract_id, row.session_label)
        observed_by_key[key].add(row.bar_start_ts)
        if row.has_trade:
            trade_by_key[key].add(row.bar_start_ts)
        if row.synthetic:
            synthetic_by_key[key].add(row.bar_start_ts)
    return _classify_intervals(
        expected_intervals=expected_intervals,
        observed_starts_by_key=observed_by_key,
        trade_starts_by_key=trade_by_key,
        synthetic_starts_by_key=synthetic_by_key,
        max_contiguous_no_trade_minutes=threshold,
        dense_grid=True,
    )


def _classify_intervals(
    *,
    expected_intervals: Sequence[Mapping[str, object]],
    observed_starts_by_key: Mapping[tuple[str, str, str], set[datetime]],
    trade_starts_by_key: Mapping[tuple[str, str, str], set[datetime]],
    synthetic_starts_by_key: Mapping[tuple[str, str, str], set[datetime]],
    max_contiguous_no_trade_minutes: int,
    dense_grid: bool,
) -> DatabentoCoverageClassification:
    intervals = tuple(_normalize_expected_interval(interval) for interval in expected_intervals)
    if not intervals:
        msg = "Databento coverage requires explicit expected_intervals"
        raise DataFoundationValidationError(msg)

    symbol_metrics: dict[str, dict[str, int | float]] = defaultdict(_metric_counts)
    provider_gap_intervals: list[Mapping[str, object]] = []
    provider_gap_sessions: list[Mapping[str, object]] = []
    suspected_non_trading_sessions: list[Mapping[str, object]] = []
    long_no_trade_runs: list[Mapping[str, object]] = []
    interval_metrics: list[Mapping[str, object]] = []
    session_presence = _session_presence_by_key(
        intervals,
        trade_starts_by_key=trade_starts_by_key,
    )
    all_symbols_absent_by_date = _all_symbols_absent_by_date(session_presence)
    recorded_suspected_sessions: set[tuple[str, str, str, str, str]] = set()

    for interval in intervals:
        expected_starts = _minute_starts(interval["start_ts"], interval["end_ts"])
        expected_count = len(expected_starts)
        key = (
            str(interval["instrument_id"]),
            str(interval["contract_id"]),
            str(interval["session_label"]),
        )
        # Iterate the small per-session expected_starts and test membership in the
        # per-key sets (O(1) each). The by-key sets aggregate the whole window per
        # (instrument, contract, session_label), so iterating them per session was
        # O(sessions * total_minutes); this is O(session_minutes) per session.
        observed_set = observed_starts_by_key.get(key, frozenset())
        trade_set = trade_starts_by_key.get(key, frozenset())
        synthetic_set = synthetic_starts_by_key.get(key, frozenset())
        observed = {start for start in expected_starts if start in observed_set}
        trades = {start for start in expected_starts if start in trade_set}
        synthetic = {start for start in expected_starts if start in synthetic_set}
        session_key = _session_key(interval)
        session = session_presence[session_key]
        metrics = symbol_metrics[str(interval["symbol"])]
        if not bool(session["has_trade"]):
            metrics["suspected_non_trading_session_minutes"] += expected_count
            metrics["suspected_non_trading_session_count"] += 1
            if session_key not in recorded_suspected_sessions:
                suspected_non_trading_sessions.append(
                    _suspected_non_trading_session(
                        interval=interval,
                        session=session,
                        all_symbols_absent=all_symbols_absent_by_date[
                            str(interval["trading_date"])
                        ],
                    )
                )
                recorded_suspected_sessions.add(session_key)
            interval_metrics.append(
                _interval_metric(
                    interval=interval,
                    expected_count=0,
                    covered_count=0,
                    provider_gap_count=0,
                    expected_absent_count=expected_count,
                )
            )
            continue

        metrics["expected_minutes"] += expected_count
        metrics["trade_minutes"] += len(trades)
        metrics["synthetic_minutes"] += len(synthetic)
        metrics["dense_row_minutes"] += len(observed)
        if dense_grid:
            metrics["no_trade_interval_minutes"] += len(synthetic)
            metrics["no_trade_filled_minutes"] += len(synthetic)

        provider_gap_count = 0
        if not observed:
            metrics["no_trade_unfilled_minutes"] += expected_count
            metrics["missing_previous_price_minutes"] += expected_count
        else:
            session_trades = set(session["trade_starts"])
            first_trade = min(trades or session_trades)
            trade_first = min(trades) if trades else None
            trade_last = max(trades) if trades else None
            if first_trade > interval["start_ts"]:
                leading = _minute_starts(interval["start_ts"], first_trade)
                metrics["no_trade_unfilled_minutes"] += len(leading)
                metrics["missing_previous_price_minutes"] += len(leading)

            for run_start, run_end, run_count in _missing_runs(
                expected_starts,
                observed,
            ):
                if run_end <= first_trade:
                    continue
                bounded_by_trades = _run_bounded_by_trades(
                    trade_first,
                    trade_last,
                    run_start=run_start,
                    run_end=run_end,
                )
                if bounded_by_trades and run_count > max_contiguous_no_trade_minutes:
                    metrics["no_trade_interval_minutes"] += run_count
                    metrics["no_trade_filled_minutes"] += run_count
                    metrics["long_no_trade_run_count"] += 1
                    metrics["long_no_trade_run_minutes"] += run_count
                    long_no_trade_runs.append(
                        _long_no_trade_run(
                            interval=interval,
                            start=run_start,
                            end=run_end,
                            minute_count=run_count,
                            threshold_minutes=max_contiguous_no_trade_minutes,
                        )
                    )
                elif dense_grid:
                    provider_gap_count += run_count
                    _add_provider_gap(
                        provider_gap_intervals,
                        provider_gap_sessions,
                        interval=interval,
                        start=run_start,
                        end=run_end,
                        minute_count=run_count,
                        reason=DENSE_GRID_MISSING_ROW,
                    )
                else:
                    metrics["no_trade_interval_minutes"] += run_count
                    metrics["no_trade_filled_minutes"] += run_count

        metrics["provider_gap_minutes"] += provider_gap_count
        interval_metrics.append(
            _interval_metric(
                interval=interval,
                expected_count=expected_count,
                covered_count=max(0, expected_count - provider_gap_count),
                provider_gap_count=provider_gap_count,
                expected_absent_count=0,
            )
        )

    frozen_metrics = {}
    for symbol, metrics in sorted(symbol_metrics.items()):
        expected = int(metrics["expected_minutes"])
        no_trade_minutes = int(metrics["no_trade_filled_minutes"])
        ratio = float(no_trade_minutes / expected) if expected else 0.0
        frozen_metrics[symbol] = MappingProxyType(
            {
                key: int(value) if isinstance(value, int | float) else value
                for key, value in metrics.items()
            }
            | {"no_trade_ratio": ratio}
        )

    return DatabentoCoverageClassification(
        metrics_by_symbol=MappingProxyType(frozen_metrics),
        provider_gap_intervals=tuple(provider_gap_intervals),
        provider_gap_sessions=_dedupe_provider_gap_sessions(provider_gap_sessions),
        suspected_non_trading_sessions=_dedupe_suspected_non_trading_sessions(
            suspected_non_trading_sessions,
        ),
        long_no_trade_runs=_dedupe_long_no_trade_runs(long_no_trade_runs),
        interval_metrics=tuple(interval_metrics),
    )


def _coverage_report_from_classification(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    classification: DatabentoCoverageClassification,
    incomplete_chunks: Iterable[object],
) -> CoverageReport:
    chunk_summaries, suppressed_chunks = _blocking_incomplete_chunks(
        incomplete_chunks,
        classification=classification,
    )
    symbol_entries: dict[str, dict[str, int]] = defaultdict(_coverage_counts)
    contract_entries: dict[str, dict[str, int]] = defaultdict(_coverage_counts)
    session_entries: dict[str, dict[str, int]] = defaultdict(_coverage_counts)
    partition_entries: dict[str, dict[str, int]] = defaultdict(_coverage_counts)

    for interval in classification.interval_metrics:
        expected = int(interval["expected_count"])
        covered = int(interval["covered_count"])
        missing = int(interval["provider_gap_count"])
        for entries, key in (
            (symbol_entries, str(interval["symbol"])),
            (contract_entries, str(interval["contract_id"])),
            (session_entries, str(interval["session_label"])),
            (partition_entries, str(interval["partition_id"])),
        ):
            entries[key]["expected"] += expected
            entries[key]["observed"] += covered
            entries[key]["missing"] += missing

    missing_intervals = classification.provider_gap_intervals[:MAX_COVERAGE_INTERVALS]
    return CoverageReport(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        symbol_coverage=_coverage_summary(
            bucket_name="symbol",
            entries=symbol_entries,
            extra={
                "no_trade_metrics_by_symbol": classification.metrics_by_symbol,
                "long_no_trade_runs_by_symbol": _long_no_trade_runs_by_symbol(
                    classification.long_no_trade_runs
                ),
                **_quarantine_summary(classification.suspected_non_trading_sessions),
            },
        ),
        contract_coverage=_coverage_summary(
            bucket_name="contract",
            entries=contract_entries,
        ),
        session_coverage=_coverage_summary(
            bucket_name="session",
            entries=session_entries,
            extra={
                "provider_gap_sessions": classification.provider_gap_sessions[
                    :MAX_COVERAGE_INTERVALS
                ],
                **_quarantine_summary(classification.suspected_non_trading_sessions),
            },
        ),
        partition_coverage=_coverage_summary(
            bucket_name="partition",
            entries=partition_entries,
            missing_interval_count=len(missing_intervals),
            incomplete_chunk_count=len(chunk_summaries),
            extra={
                "provider_gap_interval_count": len(classification.provider_gap_intervals),
                "provider_gap_minute_count": classification.provider_gap_minute_count,
                **_quarantine_summary(classification.suspected_non_trading_sessions),
                "suppressed_incomplete_chunk_count": len(suppressed_chunks),
                "suppressed_incomplete_chunks": suppressed_chunks[:MAX_COVERAGE_INTERVALS],
                "long_no_trade_run_count": classification.long_no_trade_run_count,
                "long_no_trade_run_minute_count": classification.long_no_trade_minute_count,
            },
        ),
        missing_intervals=missing_intervals,
        incomplete_chunks=chunk_summaries,
    )


def _interval_metric(
    *,
    interval: Mapping[str, object],
    expected_count: int,
    covered_count: int,
    provider_gap_count: int,
    expected_absent_count: int,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "instrument_id": interval["instrument_id"],
            "contract_id": interval["contract_id"],
            "session_label": interval["session_label"],
            "partition_id": interval["partition_id"],
            "trading_date": interval["trading_date"],
            "start_ts": interval["start_ts"],
            "end_ts": interval["end_ts"],
            "expected_count": expected_count,
            "covered_count": covered_count,
            "provider_gap_count": provider_gap_count,
            "expected_absent_count": expected_absent_count,
        }
    )


def _quarantine_summary(
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
    partial_absent_dates = tuple(
        sorted(
            {
                str(session["session_date"])
                for session in sessions
                if not bool(session["all_symbols_absent"])
            }
        )
    )
    return MappingProxyType(
        {
            "suspected_non_trading_session_count": len(sessions),
            "suspected_non_trading_session_minute_count": sum(
                int(session["minute_count"]) for session in sessions
            ),
            "suspected_non_trading_sessions": tuple(sessions[:MAX_COVERAGE_INTERVALS]),
            "suspected_non_trading_sessions_truncated": (
                len(sessions) > MAX_COVERAGE_INTERVALS
            ),
            "all_symbols_absent_dates": all_absent_dates[:MAX_COVERAGE_INTERVALS],
            "all_symbols_absent_date_count": len(all_absent_dates),
            "partial_symbols_absent_dates": partial_absent_dates[:MAX_COVERAGE_INTERVALS],
            "partial_symbols_absent_date_count": len(partial_absent_dates),
        }
    )


def _long_no_trade_runs_by_symbol(
    runs: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    by_symbol: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for run in runs:
        by_symbol[str(run["symbol"])].append(run)

    summary: dict[str, Mapping[str, object]] = {}
    for symbol, symbol_runs in sorted(by_symbol.items()):
        summary[symbol] = MappingProxyType(
            {
                "count": len(symbol_runs),
                "minute_count": sum(int(run["minute_count"]) for run in symbol_runs),
                "sample_runs": tuple(symbol_runs[:MAX_COVERAGE_INTERVALS]),
                "truncated": len(symbol_runs) > MAX_COVERAGE_INTERVALS,
                "status": ReportStatus.WARNING.value,
                "blocking": False,
            }
        )
    return MappingProxyType(summary)


def _blocking_incomplete_chunks(
    incomplete_chunks: Iterable[object],
    *,
    classification: DatabentoCoverageClassification,
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    all_absent_dates = {
        str(session["session_date"])
        for session in classification.suspected_non_trading_sessions
        if bool(session["all_symbols_absent"])
    }
    blocking: list[Mapping[str, object]] = []
    suppressed: list[Mapping[str, object]] = []
    for raw_chunk in incomplete_chunks:
        chunk_dates = _incomplete_chunk_dates(
            raw_chunk,
            interval_metrics=classification.interval_metrics,
        )
        if chunk_dates and all(date_text in all_absent_dates for date_text in chunk_dates):
            suppressed.append(_suppressed_incomplete_chunk(raw_chunk, chunk_dates))
            continue
        blocking.append(
            _incomplete_chunk_mapping(
                raw_chunk,
                interval_metrics=classification.interval_metrics,
            )
        )
    return tuple(blocking), tuple(suppressed)


def _incomplete_chunk_mapping(
    raw_chunk: object,
    *,
    interval_metrics: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    if isinstance(raw_chunk, Mapping):
        if {"chunk_id", "status", "start_ts", "end_ts"}.issubset(raw_chunk):
            return raw_chunk
        date_text = _date_text(raw_chunk.get("trading_date", raw_chunk.get("date")))
    else:
        date_text = _date_text(raw_chunk)
    start, end = _date_interval_bounds(date_text, interval_metrics=interval_metrics)
    return MappingProxyType(
        {
            "chunk_id": f"hchunk_databento_incomplete_{date_text.replace('-', '_')}",
            "status": "INCOMPLETE",
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "reason": "incomplete_chunk",
            "trading_date": date_text,
        }
    )


def _incomplete_chunk_dates(
    raw_chunk: object,
    *,
    interval_metrics: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    if isinstance(raw_chunk, Mapping):
        raw_date = raw_chunk.get("trading_date", raw_chunk.get("date"))
        if raw_date is not None:
            return (_date_text(raw_date),)
        if "start_ts" in raw_chunk and "end_ts" in raw_chunk:
            start = _parse_aware_datetime(raw_chunk["start_ts"], "incomplete_chunk.start_ts")
            end = _parse_aware_datetime(raw_chunk["end_ts"], "incomplete_chunk.end_ts")
            dates = _trading_dates_overlapping(
                start,
                end,
                interval_metrics=interval_metrics,
            )
            return dates or (start.date().isoformat(),)
        return ()
    return (_date_text(raw_chunk),)


def _suppressed_incomplete_chunk(
    raw_chunk: object,
    dates: Sequence[str],
) -> Mapping[str, object]:
    if isinstance(raw_chunk, Mapping):
        chunk_id = str(raw_chunk.get("chunk_id", "hchunk_databento_incomplete"))
    else:
        chunk_id = f"hchunk_databento_incomplete_{'_'.join(dates).replace('-', '_')}"
    return MappingProxyType(
        {
            "chunk_id": chunk_id,
            "trading_dates": tuple(dates[:MAX_COVERAGE_INTERVALS]),
            "reason": "suppressed_all_symbols_suspected_non_trading_session",
        }
    )


def _date_interval_bounds(
    date_text: str,
    *,
    interval_metrics: Sequence[Mapping[str, object]],
) -> tuple[datetime, datetime]:
    starts = []
    ends = []
    for metric in interval_metrics:
        if str(metric["trading_date"]) != date_text:
            continue
        starts.append(_parse_aware_datetime(metric["start_ts"], "interval_metric.start_ts"))
        ends.append(_parse_aware_datetime(metric["end_ts"], "interval_metric.end_ts"))
    if not starts or not ends:
        msg = "incomplete chunk date does not overlap expected Databento intervals: "
        raise DataFoundationValidationError(msg + date_text)
    return min(starts), max(ends)


def _trading_dates_overlapping(
    start: datetime,
    end: datetime,
    *,
    interval_metrics: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    dates = []
    for metric in interval_metrics:
        interval_start = _parse_aware_datetime(metric["start_ts"], "interval_metric.start_ts")
        interval_end = _parse_aware_datetime(metric["end_ts"], "interval_metric.end_ts")
        if interval_start < end and start < interval_end:
            dates.append(str(metric["trading_date"]))
    return tuple(sorted(set(dates)))


def _date_text(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value).strip()
    if not raw:
        msg = "incomplete chunk date must be a non-empty YYYY-MM-DD value"
        raise DataFoundationValidationError(msg)
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        msg = "incomplete chunk date must be a YYYY-MM-DD value"
        raise DataFoundationValidationError(msg) from exc


def _metric_counts() -> dict[str, int]:
    return {
        "expected_minutes": 0,
        "trade_minutes": 0,
        "synthetic_minutes": 0,
        "dense_row_minutes": 0,
        "no_trade_interval_minutes": 0,
        "no_trade_filled_minutes": 0,
        "no_trade_unfilled_minutes": 0,
        "missing_previous_price_minutes": 0,
        "suspected_non_trading_session_minutes": 0,
        "suspected_non_trading_session_count": 0,
        "provider_gap_minutes": 0,
        "long_no_trade_run_count": 0,
        "long_no_trade_run_minutes": 0,
    }


def _coverage_counts() -> dict[str, int]:
    return {"expected": 0, "observed": 0, "missing": 0}


def _session_presence_by_key(
    intervals: Sequence[Mapping[str, object]],
    *,
    trade_starts_by_key: Mapping[tuple[str, str, str], set[datetime]],
) -> Mapping[tuple[str, str, str, str, str], Mapping[str, object]]:
    sessions: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for interval in intervals:
        group_key = (
            str(interval["instrument_id"]),
            str(interval["contract_id"]),
            str(interval["session_label"]),
        )
        expected_starts = _minute_starts(interval["start_ts"], interval["end_ts"])
        trade_set = trade_starts_by_key.get(group_key, frozenset())
        trades = {start for start in expected_starts if start in trade_set}
        session_key = _session_key(interval)
        current = sessions.setdefault(
            session_key,
            {
                "symbol": interval["symbol"],
                "instrument_id": interval["instrument_id"],
                "contract_id": interval["contract_id"],
                "session_label": interval["session_label"],
                "trading_date": interval["trading_date"],
                "start_ts": interval["start_ts"],
                "end_ts": interval["end_ts"],
                "minute_count": 0,
                "has_trade": False,
                "trade_starts": set(),
            },
        )
        current["start_ts"] = min(
            _parse_aware_datetime(current["start_ts"], "session.start_ts"),
            interval["start_ts"],
        )
        current["end_ts"] = max(
            _parse_aware_datetime(current["end_ts"], "session.end_ts"),
            interval["end_ts"],
        )
        current["minute_count"] = int(current["minute_count"]) + len(expected_starts)
        current["has_trade"] = bool(current["has_trade"]) or bool(trades)
        current["trade_starts"] = set(current["trade_starts"]) | trades
    return MappingProxyType(
        {key: MappingProxyType(value) for key, value in sessions.items()}
    )


def _session_key(interval: Mapping[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(interval["symbol"]),
        str(interval["instrument_id"]),
        str(interval["contract_id"]),
        str(interval["session_label"]),
        str(interval["trading_date"]),
    )


def _all_symbols_absent_by_date(
    session_presence: Mapping[tuple[str, str, str, str, str], Mapping[str, object]],
) -> Mapping[str, bool]:
    by_date: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for session in session_presence.values():
        by_date[str(session["trading_date"])].append(session)
    return MappingProxyType(
        {
            trading_date: all(not bool(session["has_trade"]) for session in sessions)
            for trading_date, sessions in by_date.items()
        }
    )


def _suspected_non_trading_session(
    *,
    interval: Mapping[str, object],
    session: Mapping[str, object],
    all_symbols_absent: bool,
) -> Mapping[str, object]:
    start = _parse_aware_datetime(session["start_ts"], "session.start_ts")
    end = _parse_aware_datetime(session["end_ts"], "session.end_ts")
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "session_date": str(session["trading_date"]),
            "trading_date": str(session["trading_date"]),
            "session_label": interval["session_label"],
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "minute_count": int(session["minute_count"]),
            "classification": SUSPECTED_NON_TRADING_SESSION,
            "reason": "whole_expected_session_absent",
            "all_symbols_absent": all_symbols_absent,
            "status": ReportStatus.WARNING.value,
        }
    )


def _run_bounded_by_trades(
    trade_first: datetime | None,
    trade_last: datetime | None,
    *,
    run_start: datetime,
    run_end: datetime,
) -> bool:
    # Equivalent to "a trade exists before run_start AND a trade exists at/after
    # run_end", but computed from the precomputed session min/max trade so this
    # is O(1) per run instead of O(trades) (avoids O(runs*trades) on dense data).
    if trade_first is None or trade_last is None:
        return False
    return trade_first < run_start and trade_last >= run_end


def _coverage_summary(
    *,
    bucket_name: str,
    entries: Mapping[str, Mapping[str, int]],
    missing_interval_count: int | None = None,
    incomplete_chunk_count: int | None = None,
    extra: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    expected_total = 0
    observed_total = 0
    missing_total = 0
    samples = []
    for key, counts in sorted(entries.items()):
        expected = int(counts["expected"])
        observed = int(counts["observed"])
        missing = int(counts["missing"])
        expected_total += expected
        observed_total += observed
        missing_total += missing
        samples.append(
            {
                bucket_name: key,
                "expected_bar_count": expected,
                "observed_bar_count": observed,
                "missing_bar_count": missing,
            }
        )
    status = (
        ReportStatus.BLOCKING
        if missing_total or (incomplete_chunk_count is not None and incomplete_chunk_count)
        else ReportStatus.PASSING
    )
    summary: dict[str, object] = {
        "status": status.value,
        "blocking": status is ReportStatus.BLOCKING,
        "expected_count": expected_total,
        "observed_count": observed_total,
        "missing_count": missing_total,
        "sample_buckets": tuple(samples[:MAX_COVERAGE_INTERVALS]),
        "truncated": len(samples) > MAX_COVERAGE_INTERVALS,
    }
    if missing_interval_count is not None:
        summary["missing_interval_count"] = missing_interval_count
    if incomplete_chunk_count is not None:
        summary["incomplete_chunk_count"] = incomplete_chunk_count
    if extra is not None:
        summary.update(dict(extra))
    return MappingProxyType(summary)


def _missing_runs(
    expected_starts: tuple[datetime, ...],
    observed: set[datetime],
) -> tuple[tuple[datetime, datetime, int], ...]:
    runs: list[tuple[datetime, datetime, int]] = []
    active_start: datetime | None = None
    active_count = 0
    previous_missing: datetime | None = None
    for start in expected_starts:
        if start in observed:
            if active_start is not None and previous_missing is not None:
                runs.append(
                    (
                        active_start,
                        previous_missing + timedelta(minutes=1),
                        active_count,
                    )
                )
            active_start = None
            active_count = 0
            previous_missing = None
            continue
        if active_start is None:
            active_start = start
            active_count = 1
        else:
            active_count += 1
        previous_missing = start
    if active_start is not None and previous_missing is not None:
        runs.append((active_start, previous_missing + timedelta(minutes=1), active_count))
    return tuple(runs)


def _add_provider_gap(
    provider_gap_intervals: list[Mapping[str, object]],
    provider_gap_sessions: list[Mapping[str, object]],
    *,
    interval: Mapping[str, object],
    start: datetime,
    end: datetime,
    minute_count: int,
    reason: str,
) -> None:
    row = MappingProxyType(
        {
            "symbol": interval["symbol"],
            "instrument_id": interval["instrument_id"],
            "contract_id": interval["contract_id"],
            "session_label": interval["session_label"],
            "partition_id": interval["partition_id"],
            "trading_date": interval["trading_date"],
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "expected_bar_count": minute_count,
            "observed_bar_count": 0,
            "missing_bar_count": minute_count,
            "classification": PROVIDER_DATA_GAP,
            "reason": reason,
            "status": ReportStatus.BLOCKING.value,
        }
    )
    provider_gap_intervals.append(row)
    provider_gap_sessions.append(
        MappingProxyType(
            {
                "symbol": interval["symbol"],
                "session_date": interval["trading_date"],
                "trading_date": interval["trading_date"],
                "session_label": interval["session_label"],
                "session_start_ts": interval["start_ts"].isoformat(),
                "session_end_ts": interval["end_ts"].isoformat(),
                "reason": reason,
            }
        )
    )


def _long_no_trade_run(
    *,
    interval: Mapping[str, object],
    start: datetime,
    end: datetime,
    minute_count: int,
    threshold_minutes: int,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "symbol": interval["symbol"],
            "instrument_id": interval["instrument_id"],
            "contract_id": interval["contract_id"],
            "session_date": interval["trading_date"],
            "trading_date": interval["trading_date"],
            "session_label": interval["session_label"],
            "partition_id": interval["partition_id"],
            "start_ts": start.isoformat(),
            "end_ts": end.isoformat(),
            "minute_count": minute_count,
            "threshold_minutes": threshold_minutes,
            "classification": LONG_NO_TRADE_RUN,
            "reason": "max_contiguous_no_trade_exceeded",
            "status": ReportStatus.WARNING.value,
            "blocking": False,
        }
    )


def _dedupe_provider_gap_sessions(
    sessions: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[object, ...], Mapping[str, object]] = {}
    for session in sessions:
        key = (
            session["symbol"],
            session["session_label"],
            session["session_start_ts"],
            session["session_end_ts"],
            session["reason"],
        )
        deduped[key] = session
    return tuple(deduped[key] for key in sorted(deduped))


def _dedupe_long_no_trade_runs(
    runs: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[object, ...], Mapping[str, object]] = {}
    for run in runs:
        key = (
            run["symbol"],
            run["session_date"],
            run["session_label"],
            run["start_ts"],
            run["end_ts"],
        )
        deduped[key] = run
    return tuple(deduped[key] for key in sorted(deduped))


def _dedupe_suspected_non_trading_sessions(
    sessions: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    deduped: dict[tuple[object, ...], Mapping[str, object]] = {}
    for session in sessions:
        key = (
            session["symbol"],
            session["session_date"],
            session["session_label"],
            session["start_ts"],
            session["end_ts"],
        )
        deduped[key] = session
    return tuple(deduped[key] for key in sorted(deduped))


def _trading_sessions_for_window(
    calendar: object,
    *,
    start_ts: datetime,
    end_ts: datetime,
) -> tuple[object, ...]:
    zone = getattr(calendar, "zone", None)
    if zone is None:
        msg = "calendar does not expose a timezone for Databento coverage"
        raise DataFoundationValidationError(msg)
    start_date = start_ts.astimezone(zone).date()
    end_date = end_ts.astimezone(zone).date() + timedelta(days=1)
    sessions = []
    current = start_date
    while current <= end_date:
        session = _calendar_session_for_date(calendar, current)
        if session is not None and session.close_ts > start_ts and session.open_ts < end_ts:
            sessions.append(session)
        current += timedelta(days=1)
    if not sessions:
        msg = "no tradable calendar sessions overlap the Databento coverage window"
        raise DataFoundationValidationError(msg)
    return tuple(sessions)


def _calendar_session_for_date(calendar: object, trading_date: object) -> object | None:
    trading_session_for_date = getattr(calendar, "trading_session_for_date", None)
    if callable(trading_session_for_date):
        session = trading_session_for_date(trading_date)
    else:
        session_for_date = getattr(calendar, "session_for_date", None)
        if not callable(session_for_date):
            msg = "calendar does not expose session lookup for Databento coverage"
            raise DataFoundationValidationError(msg)
        session = session_for_date(trading_date)
    if session is None or session.is_holiday:
        return None
    return session


def _canonical_bar(bar: CanonicalBarRecord | Mapping[str, object]) -> CanonicalBarRecord:
    return bar if isinstance(bar, CanonicalBarRecord) else CanonicalBarRecord.from_mapping(bar)


def _group_key(bar: CanonicalBarRecord) -> tuple[str, str, str]:
    return (bar.instrument_id, bar.contract_id, bar.session_label)


def _normalize_expected_interval(value: Mapping[str, object]) -> Mapping[str, object]:
    required = (
        "symbol",
        "instrument_id",
        "contract_id",
        "session_label",
        "start_ts",
        "end_ts",
        "partition_id",
    )
    missing = tuple(field for field in required if field not in value)
    if missing:
        msg = "Databento expected interval missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    start = _parse_aware_datetime(value["start_ts"], "expected_interval.start_ts")
    end = _parse_aware_datetime(value["end_ts"], "expected_interval.end_ts")
    if end <= start:
        msg = "Databento expected interval end_ts must be greater than start_ts"
        raise DataFoundationValidationError(msg)
    seconds = int((end - start).total_seconds())
    if seconds <= 0 or seconds % BAR_SIZE_SECONDS_1M:
        msg = "Databento expected intervals must align to complete 1-minute bars"
        raise DataFoundationValidationError(msg)
    trading_date = _normalize_trading_date(value, start)
    return MappingProxyType(
        {
            "symbol": str(value["symbol"]).upper(),
            "instrument_id": str(value["instrument_id"]),
            "contract_id": str(value["contract_id"]),
            "session_label": str(value["session_label"]).upper(),
            "start_ts": start,
            "end_ts": end,
            "partition_id": str(value["partition_id"]),
            "trading_date": trading_date,
        }
    )


def _normalize_trading_date(value: Mapping[str, object], start: datetime) -> str:
    raw = value.get("trading_date", value.get("session_date"))
    if raw is None:
        return start.date().isoformat()
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    try:
        return date.fromisoformat(str(raw)).isoformat()
    except ValueError as exc:
        msg = "Databento expected interval trading_date must be YYYY-MM-DD"
        raise DataFoundationValidationError(msg) from exc


def _minute_starts(start: datetime, end: datetime) -> tuple[datetime, ...]:
    current = start.astimezone(UTC)
    stop = end.astimezone(UTC)
    starts = []
    while current < stop:
        starts.append(current)
        current += timedelta(minutes=1)
    return tuple(starts)


def _ceil_to_minute(value: datetime) -> datetime:
    active = value.astimezone(UTC)
    floored = active.replace(second=0, microsecond=0)
    if floored == active:
        return floored
    return floored + timedelta(minutes=1)


def _floor_to_minute(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(second=0, microsecond=0)


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        if not raw:
            msg = f"{field_name} must be a timezone-aware datetime"
            raise DataFoundationValidationError(msg)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be a timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC)


def _positive_threshold(value: object) -> int:
    if isinstance(value, bool):
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg) from exc
    if parsed <= 0:
        msg = "max_contiguous_no_trade_minutes must be a positive integer"
        raise DataFoundationValidationError(msg)
    return parsed


def _contract_id_for_symbol(symbol: str, settings: object) -> str:
    value = getattr(settings, "contract_id", None)
    if value is not None:
        return str(value)
    return f"contract_databento_{symbol.lower()}_v_0_front"


__all__ = [
    "DEFAULT_MAX_CONTIGUOUS_NO_TRADE_MINUTES",
    "DENSE_GRID_MISSING_ROW",
    "LONG_NO_TRADE_RUN",
    "MISSING_PREVIOUS_PRICE",
    "NO_TRADE_INTERVAL",
    "PROVIDER_DATA_GAP",
    "SUSPECTED_NON_TRADING_SESSION",
    "DatabentoCoverageClassification",
    "bbo_coverage_report",
    "classify_dense_grid_coverage",
    "classify_sparse_ohlcv_coverage",
    "dense_grid_coverage_report",
    "expected_intervals_for_bars",
    "expected_intervals_for_symbols",
    "ohlcv_coverage_report",
]
