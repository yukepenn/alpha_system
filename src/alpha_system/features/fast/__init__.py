"""Vectorized feature producer core for the fast-path campaign."""

from alpha_system.features.fast.materializer import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializer,
    PackMaterializerError,
    SymbolYearFrameRequest,
)

__all__ = [
    "FAST_PRODUCER_ENGINE_ID",
    "FAST_VALUE_SCHEMA_VERSION",
    "FastFeatureDeclaration",
    "FastFeaturePack",
    "PackMaterializer",
    "PackMaterializerError",
    "SymbolYearFrameRequest",
]
