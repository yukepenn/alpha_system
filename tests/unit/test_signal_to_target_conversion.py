from __future__ import annotations

from decimal import Decimal

from alpha_system.portfolio.integration import signals_to_portfolio_targets
from alpha_system.portfolio.spec import PortfolioSpec
from tests.fixtures.backtest_reference import INSTRUMENT_ID, signal_record


def test_signal_to_target_conversion_uses_desired_exposure_multiplier() -> None:
    signal = signal_record(0, "entry", signal_id="entry")
    signal["desired_exposure"] = Decimal("0.5")
    spec = PortfolioSpec.from_mapping(
        {
            "position_sizing": {"method": "fixed_notional", "fixed_notional": "10000"},
            "capital_allocation": {"starting_equity": "100000"},
            "signal_to_target_conversion": {"use_desired_exposure": True},
        }
    )

    targets = signals_to_portfolio_targets(
        signals=[signal],
        prices={INSTRUMENT_ID: Decimal("100")},
        portfolio_spec=spec,
    )

    assert len(targets) == 1
    assert targets[0].instrument_id == INSTRUMENT_ID
    assert targets[0].source_signal_id == "entry"
    assert targets[0].target_notional == Decimal("5000.0")
    assert targets[0].target_quantity == Decimal("50.0")
