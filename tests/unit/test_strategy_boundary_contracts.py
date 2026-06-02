from __future__ import annotations

from alpha_system.core.schema import contract_field_names
from alpha_system.strategies.contracts import StrategySpec


def test_strategy_spec_allowed_outputs_and_dependencies_present() -> None:
    fields = set(contract_field_names(StrategySpec))

    assert {
        "entry_signal",
        "exit_signal",
        "direction",
        "confidence_score",
        "desired_exposure",
        "required_factor_ids",
    }.issubset(fields)


def test_strategy_spec_forbidden_responsibilities_are_absent() -> None:
    fields = set(contract_field_names(StrategySpec))

    forbidden = {
        "account_equity",
        "position_sizing",
        "fills",
        "fill_model",
        "order_lifecycle",
        "slippage",
        "commission",
        "partial_take_profit",
        "partial_take_profit_accounting",
        "portfolio_aggregation",
    }

    assert fields.isdisjoint(forbidden)
