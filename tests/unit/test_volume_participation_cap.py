from __future__ import annotations

from decimal import Decimal

from alpha_system.backtest.liquidity import LiquidityInput, VolumeParticipationCap


def test_volume_participation_cap_caps_requested_quantity() -> None:
    decision = VolumeParticipationCap(Decimal("0.10")).cap(
        LiquidityInput(
            requested_quantity=Decimal("200"),
            bar_volume=Decimal("1000"),
            price=Decimal("10"),
        )
    )

    assert decision.accepted is True
    assert decision.max_quantity == Decimal("100.00")
    assert decision.fill_quantity == Decimal("100.00")
    assert decision.rejected_quantity == Decimal("100.00")
    assert decision.participation_rate == Decimal("0.10")
