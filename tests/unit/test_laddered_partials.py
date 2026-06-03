from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.management.partials import account_partial_exit, eligible_partial_exits
from alpha_system.management.spec import LadderedPartialsSpec, PartialTakeProfitStep


def test_laddered_partial_exits_are_ordered_and_accounted() -> None:
    spec = LadderedPartialsSpec(
        enabled=True,
        steps=(
            PartialTakeProfitStep(label="two_r", threshold_r=Decimal("2"), exit_fraction=Decimal("0.25")),
            PartialTakeProfitStep(label="one_r", threshold_r=Decimal("1"), exit_fraction=Decimal("0.5")),
        ),
    )

    decisions = eligible_partial_exits(
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        risk_per_unit=Decimal("2"),
        remaining_quantity=Decimal("10"),
        filled_labels=(),
        spec=spec,
        bar={"high": "104.5", "low": "99"},
    )

    assert [decision.step.label for decision in decisions] == ["one_r", "two_r"]
    assert [decision.quantity for decision in decisions] == [Decimal("5.0"), Decimal("2.50")]

    accounting = account_partial_exit(
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        exit_price=Decimal("102"),
        exit_quantity=Decimal("5"),
        current_quantity=Decimal("10"),
        current_entry_cost=Decimal("1"),
        exit_cost=Decimal("0.2"),
    )

    assert accounting.gross_pnl == Decimal("10")
    assert accounting.allocated_entry_cost == Decimal("0.5")
    assert accounting.net_pnl == Decimal("9.3")
    assert accounting.remaining_quantity == Decimal("5")
