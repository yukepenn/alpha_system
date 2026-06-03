"""Stop-price helpers for deterministic position management."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.management.spec import (
    AtrStopSpec,
    FixedStopSpec,
    ManagementSpec,
    ManagementSpecError,
    VolatilityStopSpec,
)


def fixed_stop_price(direction: Direction, entry_price: Decimal, spec: FixedStopSpec) -> Decimal | None:
    """Return the fixed stop price for a direction."""
    if not spec.enabled:
        return None
    if spec.stop_price is not None:
        return spec.stop_price
    if spec.stop_pct is None:
        return None
    if direction is Direction.LONG:
        return entry_price * (Decimal("1") - spec.stop_pct)
    if direction is Direction.SHORT:
        return entry_price * (Decimal("1") + spec.stop_pct)
    return None


def atr_stop_price(
    direction: Direction,
    entry_price: Decimal,
    spec: AtrStopSpec,
    bar: Mapping[str, Any],
) -> Decimal | None:
    """Return an ATR stop price using the configured ATR value source."""
    if not spec.enabled:
        return None
    atr = spec.atr_value if spec.atr_value is not None else _optional_bar_decimal(bar, spec.bar_field)
    if atr is None or spec.atr_multiple is None:
        return None
    distance = atr * spec.atr_multiple
    return _stop_from_distance(direction, entry_price, distance)


def volatility_stop_price(
    direction: Direction,
    entry_price: Decimal,
    spec: VolatilityStopSpec,
    bar: Mapping[str, Any],
) -> Decimal | None:
    """Return a volatility stop price using the configured volatility source."""
    if not spec.enabled:
        return None
    volatility = spec.volatility_value
    if volatility is None:
        volatility = _optional_bar_decimal(bar, spec.bar_field)
    if volatility is None or spec.volatility_multiple is None:
        return None
    distance = volatility * spec.volatility_multiple
    return _stop_from_distance(direction, entry_price, distance)


def initial_stop_price(
    direction: Direction,
    entry_price: Decimal,
    spec: ManagementSpec,
    bar: Mapping[str, Any],
) -> Decimal | None:
    """Return the most conservative configured initial stop for a position."""
    prices = tuple(
        price
        for price in (
            fixed_stop_price(direction, entry_price, spec.fixed_stop),
            atr_stop_price(direction, entry_price, spec.atr_stop, bar),
            volatility_stop_price(direction, entry_price, spec.volatility_stop, bar),
        )
        if price is not None
    )
    if not prices:
        return None
    return most_conservative_stop(direction, prices)


def risk_per_unit(entry_price: Decimal, stop_price: Decimal | None) -> Decimal | None:
    """Return absolute per-unit initial risk."""
    if stop_price is None:
        return None
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        raise ManagementSpecError("initial stop must be away from entry price")
    return risk


def stop_hit(direction: Direction, stop_price: Decimal | None, bar: Mapping[str, Any]) -> bool:
    """Return whether the current bar touches the active stop."""
    if stop_price is None:
        return False
    if direction is Direction.LONG:
        return _decimal(bar["low"]) <= stop_price
    if direction is Direction.SHORT:
        return _decimal(bar["high"]) >= stop_price
    return False


def most_conservative_stop(direction: Direction, prices: tuple[Decimal, ...]) -> Decimal:
    """Pick the stop closest to entry-side adverse movement."""
    if direction is Direction.LONG:
        return max(prices)
    if direction is Direction.SHORT:
        return min(prices)
    raise ManagementSpecError("stop selection requires long or short direction")


def _stop_from_distance(direction: Direction, entry_price: Decimal, distance: Decimal) -> Decimal:
    if direction is Direction.LONG:
        return entry_price - distance
    if direction is Direction.SHORT:
        return entry_price + distance
    raise ManagementSpecError("stop price requires long or short direction")


def _optional_bar_decimal(bar: Mapping[str, Any], field_name: str) -> Decimal | None:
    value = bar.get(field_name)
    if value in (None, ""):
        return None
    return _decimal(value)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
