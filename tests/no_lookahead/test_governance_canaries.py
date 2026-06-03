from __future__ import annotations

import pytest

from alpha_system.backtest.conservative_semantics import signal_fill_bar_is_allowed
from alpha_system.backtest.execution_config import ExecutionConfig
from alpha_system.governance.canaries import (
    NegativeControlPassFail,
    NegativeControlType,
    load_default_canary_fixture,
    run_future_shift_canary,
    run_label_leakage_canary,
    run_optimistic_fill_canary,
)
from alpha_system.governance.label_leakage_guard import (
    LabelLeakageFindingKind,
    check_label_leakage,
)


def test_future_shift_canary_fails_closed_on_availability_time_lookahead() -> None:
    fixture = load_default_canary_fixture(NegativeControlType.FUTURE_SHIFT)

    guard_result = check_label_leakage(fixture["label_spec"], fixture["features"])
    canary_result = run_future_shift_canary(fixture)

    assert guard_result.blocked is True
    assert any(
        finding.kind is LabelLeakageFindingKind.LOOKAHEAD
        for finding in guard_result.findings
    )
    assert canary_result.pass_fail is NegativeControlPassFail.PASS
    assert canary_result.guard_caught_injected_fault is True


def test_label_leakage_canary_fails_closed_on_forbidden_label_overlap() -> None:
    fixture = load_default_canary_fixture(NegativeControlType.PERMUTED_LABELS)

    guard_result = check_label_leakage(fixture["label_spec"], fixture["features"])
    canary_result = run_label_leakage_canary(fixture)

    assert guard_result.blocked is True
    assert any(
        finding.kind is LabelLeakageFindingKind.LABEL_AS_FEATURE
        for finding in guard_result.findings
    )
    assert canary_result.pass_fail is NegativeControlPassFail.PASS
    assert canary_result.guard_caught_injected_fault is True


def test_optimistic_fill_canary_fails_closed_on_same_bar_assumption() -> None:
    fixture = load_default_canary_fixture(NegativeControlType.OPTIMISTIC_FILL)
    same_bar_fill = fixture["same_bar_fill"]

    with pytest.raises(ValueError, match="next_bar_conservative"):
        ExecutionConfig.from_mapping(fixture["execution_config"])

    assert (
        signal_fill_bar_is_allowed(
            signal_bar_index=int(same_bar_fill["signal_bar_index"]),
            fill_bar_index=int(same_bar_fill["fill_bar_index"]),
        )
        is False
    )

    canary_result = run_optimistic_fill_canary(fixture)

    assert canary_result.pass_fail is NegativeControlPassFail.PASS
    assert canary_result.guard_caught_injected_fault is True
