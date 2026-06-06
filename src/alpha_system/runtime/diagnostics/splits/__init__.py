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

# The symbols above are re-exported for convenience (callers and tests import
# them from this package path), but the package-level ``__all__`` is kept empty
# to match the runtime subpackage convention shared with the factor/label/etc.
# diagnostics packages and enforced by
# tests/unit/runtime/test_package_skeleton.py.
__all__: list[str] = []
