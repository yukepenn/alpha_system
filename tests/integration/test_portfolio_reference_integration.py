from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.reference import run_reference_backtest
from alpha_system.portfolio.integration import (
    reference_default_quantity_from_targets,
    signals_to_portfolio_targets,
)
from alpha_system.portfolio.spec import PortfolioSpec
from tests.fixtures.backtest_reference import INSTRUMENT_ID, signal_record, synthetic_bar, zero_cost_config


def test_portfolio_targets_can_parameterize_reference_quantity_without_accounting() -> None:
    bars = [
        synthetic_bar(0, open_price="100", close="100"),
        synthetic_bar(1, open_price="100", close="100"),
        synthetic_bar(2, open_price="100", close="100"),
    ]
    signal = signal_record(0, "entry", signal_id="entry")
    spec = PortfolioSpec.from_mapping(
        {
            "position_sizing": {"method": "fixed_notional", "fixed_notional": "100"},
            "capital_allocation": {"starting_equity": "100000"},
            "risk_limits": {"max_position_percent": "0.1", "max_gross_exposure": "1.0"},
        }
    )
    targets = signals_to_portfolio_targets(
        signals=[signal],
        prices={INSTRUMENT_ID: Decimal("100")},
        portfolio_spec=spec,
    )

    quantity = reference_default_quantity_from_targets(targets, instrument_id=INSTRUMENT_ID)
    result = run_reference_backtest(
        bars=bars,
        signals=[signal],
        config=zero_cost_config(default_quantity=quantity, eod_flat=True),
        run_id="portfolio-reference-integration",
    )

    assert quantity == Decimal("1")
    assert targets[0].target_notional == Decimal("100")
    assert result.summary.total_trades == 1
    assert result.trades[0].quantity == Decimal("1")
    assert result.output_paths is None
    assert result.manifest["artifact_paths"] == {}
