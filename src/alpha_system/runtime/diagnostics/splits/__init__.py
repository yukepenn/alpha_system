"""Session and regime split diagnostics runtime surface."""

from alpha_system.runtime.diagnostics.splits.core import (  # noqa: F401
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
from alpha_system.runtime.diagnostics.splits.n_eff import (  # noqa: F401
    ESTIMATOR_FORMULA,
    ROWS_NOT_INDEPENDENT_MARKER,
    HorizonOverlapMetadata,
    NEffEstimate,
    NEffSampleReportingError,
    SessionDayAggregation,
    attach_n_eff_to_walk_forward_metadata,
    build_n_eff_sample_report,
    build_session_day_aggregation,
    coerce_horizon_overlap_metadata,
    estimate_n_eff,
)
from alpha_system.runtime.diagnostics.splits.walk_forward import (  # noqa: F401
    WalkForwardSplitConfig,
    WalkForwardSplitError,
    WalkForwardSplitPlan,
    build_walk_forward_split_plan,
    build_walk_forward_split_plan_for_observations,
    coerce_half_life_protocol,
    coerce_walk_forward_split_config,
    default_walk_forward_split_config,
)

# The symbols above are re-exported for convenience (callers and tests import
# them from this package path), but the package-level ``__all__`` is kept empty
# to match the runtime subpackage convention shared with the factor/label/etc.
# diagnostics packages and enforced by
# tests/unit/runtime/test_package_skeleton.py.
__all__: list[str] = []
