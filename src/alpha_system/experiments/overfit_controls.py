"""Management-grid overfit controls and warning assembly."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


SURVIVOR_WORKFLOW_STEPS: tuple[str, ...] = (
    "factor_diagnostics",
    "simple_signal_grid",
    "simple_management_baseline",
    "survivor_only_management_grid",
    "finalist_execution_validation_future_scope",
)

PATH_DEPENDENT_MANAGEMENT_PREFIXES: tuple[str, ...] = (
    "management.laddered_partial_take_profit",
    "management.trailing_stop",
    "management.breakeven_stop",
    "management.max_holding_bars",
    "management.cooldown",
)


@dataclass(frozen=True, slots=True)
class ManagementOverfitAssessment:
    """Warnings and controls retained with management-grid outputs."""

    warnings: tuple[str, ...]
    controls: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "warnings": list(self.warnings),
            "controls": dict(self.controls),
        }


def assess_management_overfit_controls(
    *,
    combination_count: int,
    max_combinations: int,
    parameter_paths: Iterable[str],
    survivor_warning_count: int,
    rejected_count: int = 0,
) -> ManagementOverfitAssessment:
    """Return management overfit controls and review warnings for a run."""
    paths = tuple(str(path) for path in parameter_paths)
    warnings = [
        "management-grid results are review-only research evidence",
        "survivor-only eligibility gate was applied before management expansion",
        f"bounded expansion evaluated {combination_count} of at most {max_combinations} declared combinations",
    ]
    if any(path.startswith(PATH_DEPENDENT_MANAGEMENT_PREFIXES) for path in paths):
        warnings.append("path-dependent management rules require conservative review")
    if len(paths) >= 4:
        warnings.append("multiple management dimensions increase review burden")
    if survivor_warning_count:
        warnings.append("survivor record warnings were retained for review")
    if rejected_count:
        warnings.append("one or more management-grid configs were rejected with visible reasons")

    return ManagementOverfitAssessment(
        warnings=tuple(dict.fromkeys(warnings)),
        controls={
            "workflow_steps": list(SURVIVOR_WORKFLOW_STEPS),
            "survivor_only": True,
            "finite_parameter_lists": True,
            "max_combinations": max_combinations,
            "combination_count": combination_count,
            "parameter_paths": list(paths),
            "rejected_config_count": rejected_count,
            "auto_promotion": False,
            "candidate_decision": "not_made_by_management_grid",
        },
    )
