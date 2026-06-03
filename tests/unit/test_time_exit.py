from __future__ import annotations

from decimal import Decimal

from alpha_system.management.rules import evaluate_management_bar
from alpha_system.management.spec import ManagementSpec
from tests.fixtures.backtest_reference import synthetic_bar
from tests.unit.test_management_rule_ordering import managed_state


def test_time_exit_closes_after_configured_minutes() -> None:
    state = managed_state(initial_stop=None)
    spec = ManagementSpec.from_mapping({"time_exit": {"enabled": True, "max_minutes": 30}})

    decision = evaluate_management_bar(
        state,
        synthetic_bar(31, open_price="100", close="100"),
        spec,
        is_last_session_bar=False,
    )

    assert decision.full_exit is not None
    assert decision.full_exit.reason == "time_exit"
    assert decision.full_exit.price == Decimal("99.99")
