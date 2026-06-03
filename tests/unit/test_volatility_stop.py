from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.management.spec import VolatilityStopSpec
from alpha_system.management.stops import volatility_stop_price


def test_volatility_stop_uses_bar_field() -> None:
    spec = VolatilityStopSpec(enabled=True, volatility_multiple=Decimal("4"))

    assert volatility_stop_price(Direction.LONG, Decimal("100"), spec, {"volatility": "0.5"}) == Decimal("98.0")
    assert volatility_stop_price(Direction.SHORT, Decimal("100"), spec, {"volatility": "0.5"}) == Decimal("102.0")
