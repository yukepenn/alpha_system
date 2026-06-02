from __future__ import annotations

from alpha_system.core.enums import FactorStatus
from alpha_system.factors.lifecycle import (
    FACTOR_LIFECYCLE_STATES,
    DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT,
    can_materialize_long_term,
    parse_factor_status,
    requires_recorded_validation_review,
    requires_review_backed_promotion,
    requires_validation_artifact,
)


def test_all_factor_lifecycle_states_are_represented() -> None:
    assert FACTOR_LIFECYCLE_STATES == (
        FactorStatus.DRAFT,
        FactorStatus.CANDIDATE,
        FactorStatus.VALIDATED,
        FactorStatus.APPROVED,
        FactorStatus.DEPRECATED,
    )
    assert [parse_factor_status(state.value) for state in FACTOR_LIFECYCLE_STATES]


def test_draft_materialization_is_blocked_by_default() -> None:
    assert DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT is False
    assert can_materialize_long_term("draft") is False
    assert can_materialize_long_term("draft", explicit_override=True) is False
    assert can_materialize_long_term("validated") is True
    assert can_materialize_long_term("approved") is True


def test_lifecycle_gate_requirements_are_explicit() -> None:
    assert requires_validation_artifact("draft") is False
    assert requires_validation_artifact("candidate") is True
    assert requires_recorded_validation_review("validated") is True
    assert requires_review_backed_promotion("approved") is True
    assert requires_review_backed_promotion("candidate") is False
