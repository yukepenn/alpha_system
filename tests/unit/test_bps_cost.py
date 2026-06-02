from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.costs import BpsCost, CostInput


def test_bps_cost_uses_absolute_notional() -> None:
    fill = CostInput(price=Decimal("100"), quantity=Decimal("5"), side="buy")

    breakdown = BpsCost(Decimal("10")).cost_for_fill(fill)

    assert breakdown.total == Decimal("0.5")


def test_bps_cost_respects_minimum_cost() -> None:
    fill = CostInput(price=Decimal("10"), quantity=Decimal("1"), side="sell")

    breakdown = BpsCost(Decimal("1"), minimum_cost=Decimal("0.25")).cost_for_fill(fill)

    assert breakdown.total == Decimal("0.25")
