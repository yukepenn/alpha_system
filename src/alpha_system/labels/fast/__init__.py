"""Vectorized label producer core for the fast-path campaign."""

from alpha_system.labels.fast.fixed_horizon import (
    FIXED_HORIZON_LABEL_IDS,
    FixedHorizonPackCoverage,
    build_fixed_horizon_label_pack,
    fixed_horizon_pack_coverage,
    supports_fixed_horizon_label_pack,
)
from alpha_system.labels.fast.materializer import (
    FAST_LABEL_PRODUCER_ENGINE_ID,
    FAST_LABEL_VALUE_SCHEMA_VERSION,
    FastFixedHorizonLabelMetadata,
    FastLabelComputation,
    FastLabelComputationMetadata,
    FastLabelDeclaration,
    FastLabelMaterializer,
    FastLabelPack,
    FastLabelPackError,
    LabelPanelFrameRequest,
)

__all__ = [
    "FAST_LABEL_PRODUCER_ENGINE_ID",
    "FAST_LABEL_VALUE_SCHEMA_VERSION",
    "FIXED_HORIZON_LABEL_IDS",
    "FastFixedHorizonLabelMetadata",
    "FastLabelComputation",
    "FastLabelComputationMetadata",
    "FastLabelDeclaration",
    "FastLabelMaterializer",
    "FastLabelPack",
    "FastLabelPackError",
    "FixedHorizonPackCoverage",
    "LabelPanelFrameRequest",
    "build_fixed_horizon_label_pack",
    "fixed_horizon_pack_coverage",
    "supports_fixed_horizon_label_pack",
]
