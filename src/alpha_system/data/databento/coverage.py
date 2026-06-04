"""Databento canonical coverage gates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import CoverageReport
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.ibkr.materialize import _expected_intervals


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
        start_ts=start_ts,
        end_ts=end_ts,
    )


def ohlcv_coverage_report(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    bars: Sequence[CanonicalBarRecord],
    expected_intervals: Sequence[Mapping[str, object]],
) -> CoverageReport:
    """Build the fail-closed OHLCV coverage report."""

    return CoverageReport.from_canonical_bars(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        bars=bars,
        expected_intervals=expected_intervals,
    )


def bbo_coverage_report(
    *,
    coverage_report_id: str,
    dataset_version_id: str,
    bbos: Sequence[CanonicalBBORecord],
    expected_intervals: Sequence[Mapping[str, object]],
) -> CoverageReport:
    """Build the fail-closed BBO coverage report."""

    return CoverageReport.from_canonical_bbos(
        coverage_report_id=coverage_report_id,
        dataset_version_id=dataset_version_id,
        bbos=bbos,
        expected_intervals=expected_intervals,
    )


__all__ = [
    "bbo_coverage_report",
    "expected_intervals_for_bars",
    "ohlcv_coverage_report",
]
