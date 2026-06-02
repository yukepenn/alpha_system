from __future__ import annotations

import pytest

from alpha_system.factors.lifecycle import (
    FactorLifecycleError,
    TransitionContext,
    assert_transition_allowed,
    is_transition_allowed,
)


@pytest.mark.parametrize(
    ("source", "target"),
    (
        ("draft", "candidate"),
        ("draft", "deprecated"),
        ("candidate", "validated"),
        ("candidate", "deprecated"),
        ("validated", "approved"),
        ("validated", "deprecated"),
        ("approved", "deprecated"),
    ),
)
def test_legal_factor_lifecycle_transitions(source: str, target: str) -> None:
    context = TransitionContext(
        validation_artifact_path="local_only/factor_validation/summary.json",
        validation_reviewed=True,
        promotion_reviewed=True,
    )

    assert is_transition_allowed(source, target)
    assert_transition_allowed(source, target, context=context)


@pytest.mark.parametrize(
    ("source", "target"),
    (
        ("draft", "approved"),
        ("draft", "validated"),
        ("candidate", "approved"),
        ("deprecated", "candidate"),
    ),
)
def test_illegal_factor_lifecycle_transitions_are_rejected(
    source: str,
    target: str,
) -> None:
    with pytest.raises(FactorLifecycleError, match="illegal"):
        assert_transition_allowed(source, target)


def test_review_gates_are_enforced_for_transition_targets() -> None:
    with pytest.raises(FactorLifecycleError, match="validation artifact"):
        assert_transition_allowed("draft", "candidate")

    with pytest.raises(FactorLifecycleError, match="recorded review"):
        assert_transition_allowed(
            "candidate",
            "validated",
            context=TransitionContext(
                validation_artifact_path="local_only/factor_validation/summary.json"
            ),
        )

    with pytest.raises(FactorLifecycleError, match="promotion decision"):
        assert_transition_allowed(
            "validated",
            "approved",
            context=TransitionContext(
                validation_artifact_path="local_only/factor_validation/summary.json",
                validation_reviewed=True,
            ),
        )
