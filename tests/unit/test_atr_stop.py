from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.management.spec import AtrStopSpec
from alpha_system.management.stops import atr_stop_price


def test_atr_stop_uses_bar_atr_or_configured_value() -> None:
    spec = AtrStopSpec(enabled=True, atr_multiple=Decimal("2"))

    assert atr_stop_price(Direction.LONG, Decimal("100"), spec, {"atr": "1.5"}) == Decimal("97.0")
    assert atr_stop_price(Direction.SHORT, Decimal("100"), spec, {"atr": "1.5"}) == Decimal("103.0")


def test_atr_stop_can_use_fixed_config_value() -> None:
    spec = AtrStopSpec(enabled=True, atr_multiple=Decimal("3"), atr_value=Decimal("1"))

    assert atr_stop_price(Direction.LONG, Decimal("100"), spec, {}) == Decimal("97")
