"""BBO tradability feature family.

This package is additive feature-family substrate. It consumes canonical BBO
input views, FLF-P06 contracts, FLF-P07 causal primitives, and the FLF-P05
FeatureRequest gate. It does not read providers, materialize values, or persist
feature registry state.
"""

from alpha_system.features.families.bbo.family import (
    BBOFeatureDefinition,
    BBOFeatureError,
    BBOFeatureName,
    BBOFeatureSpec,
    LiquidityQualityFeatureSpec,
    MicropriceFeatureSpec,
    SpreadFeatureSpec,
    TopBookImbalanceFeatureSpec,
    build_bbo_feature_definition,
    build_bbo_feature_definitions,
    compute_bbo_feature,
    compute_bbo_features,
    supported_bbo_features,
)

__all__ = [
    "BBOFeatureDefinition",
    "BBOFeatureError",
    "BBOFeatureName",
    "BBOFeatureSpec",
    "LiquidityQualityFeatureSpec",
    "MicropriceFeatureSpec",
    "SpreadFeatureSpec",
    "TopBookImbalanceFeatureSpec",
    "build_bbo_feature_definition",
    "build_bbo_feature_definitions",
    "compute_bbo_feature",
    "compute_bbo_features",
    "supported_bbo_features",
]
