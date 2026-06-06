"""Session and regime split diagnostics runtime surface."""

from alpha_system.runtime.diagnostics.splits.core import (
    DEFAULT_MIN_SAMPLE_COUNT,
    RegimeSplitReport,
    SessionSplitReport,
    SplitBucketSummary,
    SplitDefinition,
    SplitDiagnosticsError,
    build_regime_split_report,
    build_session_split_report,
    build_split_diagnostics_reports,
    default_regime_split_definitions,
    default_session_split_definitions,
)

__all__ = [
    "DEFAULT_MIN_SAMPLE_COUNT",
    "RegimeSplitReport",
    "SessionSplitReport",
    "SplitBucketSummary",
    "SplitDefinition",
    "SplitDiagnosticsError",
    "build_regime_split_report",
    "build_session_split_report",
    "build_split_diagnostics_reports",
    "default_regime_split_definitions",
    "default_session_split_definitions",
]
