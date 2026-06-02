from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import CostInput, SpreadCost


def test_half_spread_cost_uses_observed_spread() -> None:
    fill = CostInput(
        price=Decimal("100"),
        quantity=Decimal("10"),
        side="buy",
        bid=Decimal("99.90"),
        ask=Decimal("100.10"),
        spread=Decimal("0.20"),
    )

    breakdown = SpreadCost("half_spread").cost_for_fill(fill)

    assert breakdown.total == Decimal("1.000")


def test_full_spread_cost_uses_observed_spread() -> None:
    fill = CostInput(
        price=Decimal("100"),
        quantity=Decimal("10"),
        side="sell",
        bid=Decimal("99.90"),
        ask=Decimal("100.10"),
        spread=Decimal("0.20"),
    )

    breakdown = SpreadCost("full_spread").cost_for_fill(fill)

    assert breakdown.total == Decimal("2.00")
