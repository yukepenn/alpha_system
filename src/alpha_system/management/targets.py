"""Target helpers for R-multiple management rules."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.management.spec import ManagementSpecError, TargetRMultipleSpec


def target_r_price(
    direction: Direction,
    entry_price: Decimal,
    risk_per_unit: Decimal | None,
    spec: TargetRMultipleSpec,
) -> Decimal | None:
    """Return the full-exit target price for an R-multiple target."""
    if not spec.enabled:
        return None
    if risk_per_unit is None or spec.r_multiple is None:
        return None
    distance = risk_per_unit * spec.r_multiple
    if direction is Direction.LONG:
        return entry_price + distance
    if direction is Direction.SHORT:
        return entry_price - distance
    raise ManagementSpecError("target price requires long or short direction")


def threshold_r_price(
    direction: Direction,
    entry_price: Decimal,
    risk_per_unit: Decimal,
    threshold_r: Decimal,
) -> Decimal:
    """Return the price corresponding to an arbitrary R threshold."""
    if direction is Direction.LONG:
        return entry_price + risk_per_unit * threshold_r
    if direction is Direction.SHORT:
        return entry_price - risk_per_unit * threshold_r
    raise ManagementSpecError("threshold price requires long or short direction")


def favorable_price_hit(direction: Direction, price: Decimal | None, bar: Mapping[str, Any]) -> bool:
    """Return whether a target-like favorable price was touched."""
    if price is None:
        return False
    if direction is Direction.LONG:
        return _decimal(bar["high"]) >= price
    if direction is Direction.SHORT:
        return _decimal(bar["low"]) <= price
    return False


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
