"""Cross-Market ES/NQ/RTY feature family.

This package is additive feature-family substrate. It consumes canonical input
views, FLF-P06 contracts, FLF-P07 causal primitives, and the FLF-P05
FeatureRequest gate. It does not read providers, materialize values, or persist
feature registry state.
"""

from alpha_system.features.families.cross_market.family import (
    CrossMarketAlignedSnapshot,
    CrossMarketFeatureDefinition,
    CrossMarketFeatureError,
    CrossMarketFeatureName,
    CrossMarketFeatureSpec,
    CrossMarketFlagFeatureSpec,
    CrossMarketInputBundle,
    CrossMarketReturnFeatureSpec,
    CrossMarketRollingFeatureSpec,
    CrossMarketRotationFeatureSpec,
    align_cross_market_rows,
    build_cross_market_feature_definition,
    build_cross_market_feature_definitions,
    compute_cross_market_feature,
    compute_cross_market_features,
    supported_cross_market_features,
)

__all__ = [
    "CrossMarketAlignedSnapshot",
    "CrossMarketFeatureDefinition",
    "CrossMarketFeatureError",
    "CrossMarketFeatureName",
    "CrossMarketFeatureSpec",
    "CrossMarketFlagFeatureSpec",
    "CrossMarketInputBundle",
    "CrossMarketReturnFeatureSpec",
    "CrossMarketRollingFeatureSpec",
    "CrossMarketRotationFeatureSpec",
    "align_cross_market_rows",
    "build_cross_market_feature_definition",
    "build_cross_market_feature_definitions",
    "compute_cross_market_feature",
    "compute_cross_market_features",
    "supported_cross_market_features",
]
