from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import CostInput, PerUnitCommissionCost


def test_per_unit_commission_scales_with_quantity() -> None:
    fill = CostInput(price=Decimal("25"), quantity=Decimal("200"), side="sell")

    breakdown = PerUnitCommissionCost(Decimal("0.005")).cost_for_fill(fill)

    assert breakdown.total == Decimal("1.000")
    assert breakdown.amount_for("per_unit_commission") == Decimal("1.000")
