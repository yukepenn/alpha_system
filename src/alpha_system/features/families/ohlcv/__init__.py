"""Base OHLCV feature family.

This package is additive feature-family substrate. It consumes canonical OHLCV
input views, FLF-P06 contracts, FLF-P07 causal primitives, and the FLF-P05
FeatureRequest gate. It does not read providers, materialize values, or persist
feature registry state.
"""

from alpha_system.features.families.ohlcv.family import (
    OHLCVFeatureDefinition,
    OHLCVFeatureError,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    build_ohlcv_feature_definitions,
    compute_ohlcv_feature,
    compute_ohlcv_features,
    supported_ohlcv_features,
)

__all__ = [
    "OHLCVFeatureDefinition",
    "OHLCVFeatureError",
    "OHLCVFeatureName",
    "build_ohlcv_feature_definition",
    "build_ohlcv_feature_definitions",
    "compute_ohlcv_feature",
    "compute_ohlcv_features",
    "supported_ohlcv_features",
]
