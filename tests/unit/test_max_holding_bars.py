from __future__ import annotations

from alpha_system.management.rules import evaluate_management_bar
from alpha_system.management.spec import ManagementSpec
from tests.fixtures.backtest_reference import synthetic_bar
from tests.unit.test_management_rule_ordering import managed_state


def test_max_holding_bars_exits_on_limit_bar() -> None:
    state = managed_state(initial_stop=None, entry_bar_index=1)
    spec = ManagementSpec.from_mapping({"max_holding_bars": 2})

    decision = evaluate_management_bar(state, synthetic_bar(3), spec, is_last_session_bar=False)

    assert decision.full_exit is not None
    assert decision.full_exit.reason == "max_holding_bars"
