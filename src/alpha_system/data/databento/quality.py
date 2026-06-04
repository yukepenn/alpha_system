"""Databento canonical quality gates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import DataQualityReport
from alpha_system.data.foundation.quotes import CanonicalBBORecord


def ohlcv_quality_report(
    *,
    quality_report_id: str,
    dataset_version_id: str,
    bars: Iterable[CanonicalBarRecord | Mapping[str, object]],
    expected_sessions: Iterable[str],
    expected_gap_intervals: Iterable[Mapping[str, object]],
) -> DataQualityReport:
    """Build the fail-closed OHLCV quality report for Databento bars."""

    return DataQualityReport.from_canonical_bars(
        quality_report_id=quality_report_id,
        dataset_version_id=dataset_version_id,
        bars=bars,
        expected_sessions=expected_sessions,
        expected_gap_intervals=expected_gap_intervals,
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


__all__ = ["bbo_quality_report", "ohlcv_quality_report"]
