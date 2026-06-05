"""Session / Calendar / Roll feature family.

This package is additive feature-family substrate. It consumes canonical OHLCV
input views, FLF-P06 contracts, FLF-P07 causal contracts, FLF-P04 no-trade
semantics, and the FLF-P05 FeatureRequest gate. It does not read providers,
materialize values, or persist feature registry state.
"""

from alpha_system.features.families.session.family import (
    CalendarFeatureSpec,
    ExpirationFeatureSpec,
    RollFeatureSpec,
    SessionCalendarRollMetadata,
    SessionFeatureDefinition,
    SessionFeatureError,
    SessionFeatureName,
    SessionFeatureSpec,
    SessionPositionFeatureSpec,
    StatusFeatureSpec,
    build_session_feature_definition,
    build_session_feature_definitions,
    compute_session_feature,
    compute_session_features,
    row_key,
    supported_session_features,
)

__all__ = [
    "CalendarFeatureSpec",
    "ExpirationFeatureSpec",
    "RollFeatureSpec",
    "SessionCalendarRollMetadata",
    "SessionFeatureDefinition",
    "SessionFeatureError",
    "SessionFeatureName",
    "SessionFeatureSpec",
    "SessionPositionFeatureSpec",
    "StatusFeatureSpec",
    "build_session_feature_definition",
    "build_session_feature_definitions",
    "compute_session_feature",
    "compute_session_features",
    "row_key",
    "supported_session_features",
]
