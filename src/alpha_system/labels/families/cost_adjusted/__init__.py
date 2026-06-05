"""Cost-adjusted / spread-adjusted label family.

This package is additive label-family substrate. It consumes governed
``LabelSpec`` records through FLF-P16 label contracts and canonical BBO input
views. It does not read providers, materialize values, persist labels, or expose
labels as live features.
"""

from alpha_system.labels.families.cost_adjusted.family import (
    CostAdjustedForwardReturnSpec,
    CostAdjustedLabelDefinition,
    CostAdjustedLabelError,
    CostAdjustedLabelName,
    CostAdjustedLabelSpec,
    SpreadAdjustedForwardReturnSpec,
    build_cost_adjusted_label_definition,
    build_cost_adjusted_label_definitions,
    compute_cost_adjusted_label,
    compute_cost_adjusted_labels,
    supported_cost_adjusted_labels,
)

__all__ = [
    "CostAdjustedForwardReturnSpec",
    "CostAdjustedLabelDefinition",
    "CostAdjustedLabelError",
    "CostAdjustedLabelName",
    "CostAdjustedLabelSpec",
    "SpreadAdjustedForwardReturnSpec",
    "build_cost_adjusted_label_definition",
    "build_cost_adjusted_label_definitions",
    "compute_cost_adjusted_label",
    "compute_cost_adjusted_labels",
    "supported_cost_adjusted_labels",
]
