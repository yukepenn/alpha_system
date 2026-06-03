from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.management.spec import TargetRMultipleSpec
from alpha_system.management.targets import favorable_price_hit, target_r_price


def test_target_r_multiple_price_and_hit_detection() -> None:
    spec = TargetRMultipleSpec(enabled=True, r_multiple=Decimal("1.5"))
    target = target_r_price(Direction.LONG, Decimal("100"), Decimal("2"), spec)

    assert target == Decimal("103.0")
    assert favorable_price_hit(Direction.LONG, target, {"high": "103", "low": "99"})
    assert not favorable_price_hit(Direction.LONG, target, {"high": "102.99", "low": "99"})
