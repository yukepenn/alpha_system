from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.portfolio.sizing import SizeRequest, size_position
from alpha_system.portfolio.spec import PositionSizingSpec


def test_fixed_notional_sizing_is_deterministic() -> None:
    decision = size_position(
        SizeRequest(
            instrument_id="SYNTH_A",
            direction=Direction.LONG,
            price=Decimal("50"),
            equity=Decimal("100000"),
            source_signal_id="sig-1",
        ),
        PositionSizingSpec(method="fixed_notional", fixed_notional="10000"),
    )

    assert decision.target_notional == Decimal("10000")
    assert decision.target_quantity == Decimal("200")
    assert decision.target_weight == Decimal("0.1")


def test_risk_per_trade_sizing_uses_equity_and_stop_distance() -> None:
    decision = size_position(
        SizeRequest(
            instrument_id="SYNTH_A",
            direction=Direction.LONG,
            price=Decimal("100"),
            equity=Decimal("100000"),
            source_signal_id="sig-1",
        ),
        PositionSizingSpec(
            method="risk_per_trade",
            risk_per_trade="0.01",
            stop_distance="2",
            fixed_notional=None,
        ),
    )

    assert decision.target_quantity == Decimal("500")
    assert decision.target_notional == Decimal("50000")
