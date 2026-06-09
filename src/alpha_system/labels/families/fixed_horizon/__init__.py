"""Fixed-horizon forward-return label family.

This package defines additive, label-only substrate for fixed-horizon
trade-close and midprice forward returns. It consumes canonical input views and
FLF-P16 label contracts; it does not materialize values, read providers, or
expose labels as live features.
"""

from alpha_system.labels.families.fixed_horizon.family import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelError,
    FixedHorizonLabelName,
    HorizonOverlapMetadata,
    MAINTENANCE_GUARD_VERSION,
    MAINTENANCE_POLICY_ID,
    OVERLAP_METADATA_VERSION,
    build_fixed_horizon_label_definition,
    build_fixed_horizon_label_definitions,
    compute_horizon_overlap_metadata,
    compute_fixed_horizon_label,
    compute_fixed_horizon_labels,
    supported_fixed_horizon_labels,
)

__all__ = [
    "FixedHorizonLabelDefinition",
    "FixedHorizonLabelError",
    "FixedHorizonLabelName",
    "HorizonOverlapMetadata",
    "MAINTENANCE_GUARD_VERSION",
    "MAINTENANCE_POLICY_ID",
    "OVERLAP_METADATA_VERSION",
    "build_fixed_horizon_label_definition",
    "build_fixed_horizon_label_definitions",
    "compute_horizon_overlap_metadata",
    "compute_fixed_horizon_label",
    "compute_fixed_horizon_labels",
    "supported_fixed_horizon_labels",
]
