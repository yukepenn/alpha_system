from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from alpha_system.governance.canaries import (
    EXECUTABLE_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    NegativeControlResult,
    NegativeControlType,
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    expected_failure_for_canary_type,
    load_default_canary_fixture,
    run_future_shift_canary,
    run_governance_canary,
    run_label_leakage_canary,
    run_optimistic_fill_canary,
    run_random_target_canary,
    run_required_governance_canaries,
)


@pytest.mark.parametrize("canary_type", EXECUTABLE_NEGATIVE_CONTROL_TYPES)
def test_governance_canary_results_are_catalog_consistent(
    canary_type: NegativeControlType,
) -> None:
    result = run_governance_canary(canary_type)

    assert result.canary_type is canary_type
    assert result.expected_failure == expected_failure_for_canary_type(canary_type)
    assert result.observed_result == result.expected_failure
    assert result.pass_fail is NegativeControlPassFail.PASS
    assert result.guard_caught_injected_fault is True
    assert result.expected_failure_observed is True
    assert result.implies_alpha_validity is False
    assert NegativeControlResult.from_canonical_json(result.to_canonical_json()) == result


def test_required_governance_canaries_run_in_canonical_scope() -> None:
    results = run_required_governance_canaries()

    assert (
        tuple(result.canary_type for result in results)
        == EXECUTABLE_NEGATIVE_CONTROL_TYPES
    )
    assert tuple(result.canary_type.value for result in results) == (
        REQUIRED_NEGATIVE_CONTROL_TYPES
    )
    assert all(result.pass_fail is NegativeControlPassFail.PASS for result in results)


@pytest.mark.parametrize(
    ("canary_type", "runner"),
    [
        (NegativeControlType.RANDOM_TARGET, run_random_target_canary),
        (NegativeControlType.FUTURE_SHIFT, run_future_shift_canary),
        (NegativeControlType.PERMUTED_LABELS, run_label_leakage_canary),
        (NegativeControlType.OPTIMISTIC_FILL, run_optimistic_fill_canary),
    ],
)
def test_missed_guard_is_recorded_as_fail(
    canary_type: NegativeControlType,
    runner: Callable[..., NegativeControlResult],
) -> None:
    fixture = load_default_canary_fixture(canary_type)

    result = runner(fixture, guard=lambda _: False)

    assert result.canary_type is canary_type
    assert result.expected_failure == expected_failure_for_canary_type(canary_type)
    assert result.observed_result != result.expected_failure
    assert result.pass_fail is NegativeControlPassFail.FAIL
    assert result.guard_caught_injected_fault is False
    assert result.expected_failure_observed is False


def test_random_target_default_fixture_is_deterministic_and_executable() -> None:
    fixture = load_default_canary_fixture("random_target")

    first = run_governance_canary(NegativeControlType.RANDOM_TARGET, fixture)
    second = run_governance_canary("random_target", fixture)

    assert first == second
    assert first.pass_fail is NegativeControlPassFail.PASS
    assert first.observed_result == expected_failure_for_canary_type("random_target")


def test_guard_exception_is_not_silently_converted_to_pass() -> None:
    def broken_guard(_: dict[str, Any]) -> bool:
        raise RuntimeError("synthetic guard error")

    with pytest.raises(RuntimeError, match="synthetic guard error"):
        run_future_shift_canary(guard=broken_guard)
