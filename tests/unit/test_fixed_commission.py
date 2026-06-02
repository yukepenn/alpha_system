from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import CostInput, FixedCommissionCost


def test_fixed_commission_applies_once_per_fill() -> None:
    fill = CostInput(price=Decimal("100"), quantity=Decimal("3"), side="buy")

    breakdown = FixedCommissionCost(Decimal("2.50")).cost_for_fill(fill)

    assert breakdown.total == Decimal("2.50")
    assert breakdown.amount_for("fixed_commission") == Decimal("2.50")
