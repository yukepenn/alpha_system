from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.core.enums import Direction
from alpha_system.management.spec import FixedStopSpec, ManagementSpecError
from alpha_system.management.stops import fixed_stop_price


def test_fixed_stop_long_and_short_percent_prices() -> None:
    spec = FixedStopSpec(enabled=True, stop_pct=Decimal("0.02"))

    assert fixed_stop_price(Direction.LONG, Decimal("100"), spec) == Decimal("98.00")
    assert fixed_stop_price(Direction.SHORT, Decimal("100"), spec) == Decimal("102.00")


def test_fixed_stop_requires_distance_or_price_when_enabled() -> None:
    with pytest.raises(ManagementSpecError):
        FixedStopSpec(enabled=True)
