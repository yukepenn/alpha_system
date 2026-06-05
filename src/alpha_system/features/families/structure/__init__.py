"""Liquidity sweep and structure primitive feature family.

This package is additive feature-family substrate. It consumes canonical OHLCV
and BBO input views, FLF-P06 contracts, FLF-P07 causal primitives, and the
FLF-P05 FeatureRequest gate. It does not read providers, materialize values, or
persist feature registry state.
"""

from alpha_system.features.families.structure.family import (
    CompressionFeatureSpec,
    OpeningRangeFeatureSpec,
    PriorExtremeFeatureSpec,
    StructureFeatureDefinition,
    StructureFeatureError,
    StructureFeatureName,
    StructureFeatureSpec,
    StructureInputBundle,
    SweepFeatureSpec,
    WickFeatureSpec,
    build_structure_feature_definition,
    build_structure_feature_definitions,
    compute_structure_feature,
    compute_structure_features,
    supported_structure_features,
)

__all__ = [
    "CompressionFeatureSpec",
    "OpeningRangeFeatureSpec",
    "PriorExtremeFeatureSpec",
    "StructureFeatureDefinition",
    "StructureFeatureError",
    "StructureFeatureName",
    "StructureFeatureSpec",
    "StructureInputBundle",
    "SweepFeatureSpec",
    "WickFeatureSpec",
    "build_structure_feature_definition",
    "build_structure_feature_definitions",
    "compute_structure_feature",
    "compute_structure_features",
    "supported_structure_features",
]
