"""Eligibility policy for survivor-only management grids."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from alpha_system.experiments.survivors import SurvivorRecord, VALID_REVIEW_STATUSES


class CandidateEligibilityError(ValueError):
    """Raised when a candidate may not enter a management grid."""

    def __init__(self, decision: "CandidateEligibilityDecision") -> None:
        self.decision = decision
        super().__init__("; ".join(decision.reasons) or "candidate is not eligible")


@dataclass(frozen=True, slots=True)
class CandidateEligibilityDecision:
    """Result of applying the survivor eligibility gate."""

    candidate_id: str
    eligible: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    allowed_scope: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        payload["warnings"] = list(self.warnings)
        payload["allowed_scope"] = dict(self.allowed_scope)
        return payload


def evaluate_candidate_eligibility(
    survivor: SurvivorRecord,
    *,
    parameter_paths: Iterable[str] = (),
    max_combinations: int | None = None,
) -> CandidateEligibilityDecision:
    """Return whether ``survivor`` is eligible for the requested management grid."""
    requested_paths = tuple(str(path) for path in parameter_paths)
    reasons: list[str] = []
    warnings: list[str] = list(survivor.warnings)

    if survivor.review_status not in VALID_REVIEW_STATUSES:
        reasons.append("survivor review_status is not eligible for management-grid entry")
    if not survivor.survivor_eligibility_reason:
        reasons.append("survivor eligibility reason is required")
    if not survivor.source_grid_config_hash:
        reasons.append("source grid config hash is required")

    allowed_paths = _allowed_parameter_paths(survivor.allowed_management_grid_scope)
    if requested_paths and not allowed_paths:
        reasons.append("allowed_management_grid_scope must list finite parameter paths")
    else:
        missing = tuple(sorted(set(requested_paths).difference(allowed_paths)))
        if missing:
            reasons.append(f"requested parameters exceed survivor scope: {', '.join(missing)}")

    scope_max, scope_max_error = _scope_maximum(survivor.allowed_management_grid_scope)
    if scope_max_error is not None:
        reasons.append(scope_max_error)
    if max_combinations is not None and scope_max is not None and max_combinations > scope_max:
        reasons.append(
            "requested max_combinations exceeds survivor allowed scope "
            f"({max_combinations} > {scope_max})"
        )

    if warnings:
        warnings.append("survivor warnings were carried into management-grid review evidence")

    return CandidateEligibilityDecision(
        candidate_id=survivor.candidate_id,
        eligible=not reasons,
        reasons=tuple(reasons),
        warnings=tuple(dict.fromkeys(warnings)),
        allowed_scope=dict(survivor.allowed_management_grid_scope),
    )


def assert_candidate_eligible(
    survivor: SurvivorRecord,
    *,
    parameter_paths: Iterable[str] = (),
    max_combinations: int | None = None,
) -> CandidateEligibilityDecision:
    """Return the eligibility decision or raise with visible reasons."""
    decision = evaluate_candidate_eligibility(
        survivor,
        parameter_paths=parameter_paths,
        max_combinations=max_combinations,
    )
    if not decision.eligible:
        raise CandidateEligibilityError(decision)
    return decision


def _allowed_parameter_paths(scope: Mapping[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for key in ("parameters", "management_parameters", "execution_parameters"):
        value = scope.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            paths.append(value)
            continue
        if isinstance(value, Iterable):
            paths.extend(str(item) for item in value)
    normalized = []
    for path in paths:
        active = str(path).strip()
        if active and active != "*":
            normalized.append(active)
    return tuple(dict.fromkeys(normalized))


def _scope_maximum(scope: Mapping[str, Any]) -> tuple[int | None, str | None]:
    return _optional_positive_int(
        scope.get("max_combinations"),
        "allowed_management_grid_scope.max_combinations",
    )


def _optional_positive_int(value: Any, field_name: str) -> tuple[int | None, str | None]:
    if value in (None, ""):
        return None, None
    if isinstance(value, bool):
        return None, f"{field_name} must be a positive integer"
    try:
        active = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a positive integer"
    if active <= 0:
        return None, f"{field_name} must be positive"
    return active, None
