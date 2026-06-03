from __future__ import annotations

from alpha_system.management.rules import evaluate_management_bar
from alpha_system.management.spec import ManagementSpec
from tests.fixtures.backtest_reference import synthetic_bar
from tests.unit.test_management_rule_ordering import managed_state


def test_eod_exit_uses_last_session_bar_only() -> None:
    state = managed_state(initial_stop=None)
    spec = ManagementSpec.from_mapping({"eod_exit": True})

    no_exit = evaluate_management_bar(state, synthetic_bar(1), spec, is_last_session_bar=False)
    eod_exit = evaluate_management_bar(state, synthetic_bar(2), spec, is_last_session_bar=True)

    assert no_exit.full_exit is None
    assert eod_exit.full_exit is not None
    assert eod_exit.full_exit.reason == "eod_exit"
