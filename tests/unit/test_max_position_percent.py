from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.portfolio.risk import enforce_position_percent
from alpha_system.portfolio.sizing import SizeDecision
from alpha_system.portfolio.spec import RiskLimitsSpec


def test_max_position_percent_caps_single_target() -> None:
    decision = SizeDecision(
        instrument_id="SYNTH_A",
        direction=Direction.LONG,
        target_notional=Decimal("50000"),
        target_quantity=Decimal("500"),
        target_weight=Decimal("0.5"),
        source_signal_id="sig-1",
    )

    capped = enforce_position_percent(
        (decision,),
        Decimal("100000"),
        RiskLimitsSpec(max_position_percent="0.2"),
    )[0]

    assert capped.target_notional == Decimal("20000.0")
    assert capped.target_quantity == Decimal("200.0")
    assert capped.capped is True
    assert "max_position_percent" in capped.reasons
