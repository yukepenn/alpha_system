from __future__ import annotations

from decimal import Decimal

from alpha_system.portfolio.integration import signals_to_portfolio_targets
from alpha_system.portfolio.spec import PortfolioSpec
from tests.fixtures.backtest_reference import INSTRUMENT_ID, signal_record


def test_insufficient_capital_rejects_target_by_default() -> None:
    spec = PortfolioSpec.from_mapping(
        {
            "position_sizing": {"method": "fixed_notional", "fixed_notional": "10000"},
            "capital_allocation": {
                "starting_equity": "5000",
                "insufficient_capital_policy": "reject",
            },
        }
    )

    targets = signals_to_portfolio_targets(
        signals=[signal_record(0, "entry", signal_id="entry")],
        prices={INSTRUMENT_ID: Decimal("100")},
        portfolio_spec=spec,
    )

    assert targets[0].rejected is True
    assert targets[0].target_notional == Decimal("0")
    assert targets[0].target_quantity == Decimal("0")
    assert "insufficient_capital" in targets[0].reasons
