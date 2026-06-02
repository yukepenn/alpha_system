"""Factor lifecycle states, transitions, and gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from alpha_system.core.enums import FactorStatus


class FactorLifecycleError(ValueError):
    """Raised when a lifecycle state or transition violates policy."""


FACTOR_LIFECYCLE_STATES: tuple[FactorStatus, ...] = (
    FactorStatus.DRAFT,
    FactorStatus.CANDIDATE,
    FactorStatus.VALIDATED,
    FactorStatus.APPROVED,
    FactorStatus.DEPRECATED,
)

LEGAL_TRANSITIONS: dict[FactorStatus, tuple[FactorStatus, ...]] = {
    FactorStatus.DRAFT: (FactorStatus.CANDIDATE, FactorStatus.DEPRECATED),
    FactorStatus.CANDIDATE: (FactorStatus.VALIDATED, FactorStatus.DEPRECATED),
    FactorStatus.VALIDATED: (FactorStatus.APPROVED, FactorStatus.DEPRECATED),
    FactorStatus.APPROVED: (FactorStatus.DEPRECATED,),
    FactorStatus.DEPRECATED: (),
}

DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT = False


@dataclass(frozen=True, slots=True, kw_only=True)
class TransitionContext:
    """Evidence available when evaluating a lifecycle transition."""

    validation_artifact_path: str | None = None
    validation_reviewed: bool = False
    promotion_reviewed: bool = False


def parse_factor_status(value: Any) -> FactorStatus:
    """Parse a serialized lifecycle state."""
    if isinstance(value, FactorStatus):
        return value
    if not isinstance(value, str) or not value.strip():
        msg = "factor status must be a non-empty string"
        raise FactorLifecycleError(msg)
    try:
        return FactorStatus(value.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(state.value for state in FACTOR_LIFECYCLE_STATES)
        msg = f"unsupported factor status {value!r}; allowed: {allowed}"
        raise FactorLifecycleError(msg) from exc


def is_transition_allowed(from_status: Any, to_status: Any) -> bool:
    """Return whether a lifecycle transition is structurally legal."""
    source = parse_factor_status(from_status)
    target = parse_factor_status(to_status)
    return target in LEGAL_TRANSITIONS[source]


def assert_transition_allowed(
    from_status: Any,
    to_status: Any,
    *,
    context: TransitionContext | None = None,
) -> None:
    """Reject illegal transitions and missing lifecycle gates."""
    source = parse_factor_status(from_status)
    target = parse_factor_status(to_status)
    if target not in LEGAL_TRANSITIONS[source]:
        msg = f"illegal factor lifecycle transition: {source.value} -> {target.value}"
        raise FactorLifecycleError(msg)

    active_context = context or TransitionContext()
    if target in {FactorStatus.CANDIDATE, FactorStatus.VALIDATED, FactorStatus.APPROVED}:
        if not active_context.validation_artifact_path:
            msg = f"{target.value} factors require a validation artifact reference"
            raise FactorLifecycleError(msg)
    if target is FactorStatus.VALIDATED and not active_context.validation_reviewed:
        msg = "validated factors require a recorded review status"
        raise FactorLifecycleError(msg)
    if target is FactorStatus.APPROVED and not active_context.promotion_reviewed:
        msg = "approved factors require a review-backed promotion decision"
        raise FactorLifecycleError(msg)


def can_materialize_long_term(
    status: Any,
    *,
    explicit_override: bool = False,
) -> bool:
    """Return whether long-term factor-value materialization is policy-eligible."""
    parsed = parse_factor_status(status)
    if parsed is FactorStatus.DRAFT:
        return explicit_override and DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT
    return parsed in {
        FactorStatus.VALIDATED,
        FactorStatus.APPROVED,
        FactorStatus.DEPRECATED,
    }


def requires_validation_artifact(status: Any) -> bool:
    parsed = parse_factor_status(status)
    return parsed in {
        FactorStatus.CANDIDATE,
        FactorStatus.VALIDATED,
        FactorStatus.APPROVED,
    }


def requires_recorded_validation_review(status: Any) -> bool:
    parsed = parse_factor_status(status)
    return parsed in {FactorStatus.VALIDATED, FactorStatus.APPROVED}


def requires_review_backed_promotion(status: Any) -> bool:
    parsed = parse_factor_status(status)
    return parsed is FactorStatus.APPROVED
