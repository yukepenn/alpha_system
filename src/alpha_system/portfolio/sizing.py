"""Deterministic portfolio sizing helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.portfolio.spec import PositionSizingSpec, SizingMethod


class PortfolioSizingError(ValueError):
    """Raised when a sizing request cannot be evaluated."""


@dataclass(frozen=True, slots=True)
class SizeRequest:
    instrument_id: str
    direction: Direction
    price: Decimal
    equity: Decimal
    source_signal_id: str
    desired_exposure: Decimal | None = None
    confidence: Decimal | None = None
    stop_distance: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument_id", _text(self.instrument_id, "instrument_id"))
        object.__setattr__(self, "direction", _direction(self.direction))
        object.__setattr__(self, "price", _positive_decimal(self.price, "price"))
        object.__setattr__(self, "equity", _positive_decimal(self.equity, "equity"))
        object.__setattr__(self, "source_signal_id", _text(self.source_signal_id, "source_signal_id"))
        object.__setattr__(self, "desired_exposure", _optional_fraction(self.desired_exposure, "desired_exposure"))
        object.__setattr__(self, "confidence", _optional_fraction(self.confidence, "confidence"))
        object.__setattr__(self, "stop_distance", _optional_positive_decimal(self.stop_distance, "stop_distance"))


@dataclass(frozen=True, slots=True)
class SizeDecision:
    instrument_id: str
    direction: Direction
    target_notional: Decimal
    target_quantity: Decimal
    target_weight: Decimal
    source_signal_id: str
    rejected: bool = False
    capped: bool = False
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument_id", _text(self.instrument_id, "instrument_id"))
        object.__setattr__(self, "direction", _direction(self.direction))
        object.__setattr__(self, "target_notional", _non_negative_decimal(self.target_notional, "target_notional"))
        object.__setattr__(self, "target_quantity", _non_negative_decimal(self.target_quantity, "target_quantity"))
        object.__setattr__(self, "target_weight", _decimal(self.target_weight, "target_weight"))
        object.__setattr__(self, "source_signal_id", _text(self.source_signal_id, "source_signal_id"))
        object.__setattr__(self, "rejected", bool(self.rejected))
        object.__setattr__(self, "capped", bool(self.capped))
        object.__setattr__(self, "reasons", tuple(str(reason) for reason in self.reasons))

    @property
    def signed_notional(self) -> Decimal:
        if self.direction is Direction.SHORT:
            return -self.target_notional
        if self.direction is Direction.FLAT:
            return Decimal("0")
        return self.target_notional

    def with_notional(self, notional: Decimal, equity: Decimal, reason: str, *, rejected: bool = False) -> "SizeDecision":
        active_notional = _non_negative_decimal(notional, "notional")
        quantity = Decimal("0") if self.target_notional == 0 else self.target_quantity * active_notional / self.target_notional
        if rejected:
            active_notional = Decimal("0")
            quantity = Decimal("0")
        signed_weight = _signed_weight(active_notional, equity, self.direction)
        return replace(
            self,
            target_notional=active_notional,
            target_quantity=quantity,
            target_weight=signed_weight,
            rejected=self.rejected or rejected,
            capped=self.capped or (active_notional != self.target_notional and not rejected),
            reasons=_append_reason(self.reasons, reason),
        )


def size_position(request: SizeRequest, spec: PositionSizingSpec) -> SizeDecision:
    """Return the unconstrained target size for one signal request."""
    exposure_multiplier = request.desired_exposure if request.desired_exposure is not None else Decimal("1")
    if spec.method is SizingMethod.FIXED_NOTIONAL:
        base_notional = spec.fixed_notional or Decimal("0")
        target_notional = base_notional * exposure_multiplier
    elif spec.method is SizingMethod.RISK_PER_TRADE:
        risk_fraction = spec.risk_per_trade or Decimal("0")
        stop_distance = request.stop_distance or spec.stop_distance
        if stop_distance is None:
            raise PortfolioSizingError("risk_per_trade sizing requires stop_distance")
        risk_budget = request.equity * risk_fraction
        target_notional = risk_budget * request.price / stop_distance * exposure_multiplier
    else:
        raise PortfolioSizingError(f"unsupported sizing method: {spec.method}")

    if target_notional < spec.min_notional:
        target_notional = Decimal("0")
    quantity = target_notional / request.price if request.price else Decimal("0")
    if not spec.allow_fractional:
        quantity = quantity.to_integral_value(rounding=ROUND_FLOOR)
        target_notional = quantity * request.price
    return SizeDecision(
        instrument_id=request.instrument_id,
        direction=request.direction,
        target_notional=target_notional,
        target_quantity=quantity,
        target_weight=_signed_weight(target_notional, request.equity, request.direction),
        source_signal_id=request.source_signal_id,
    )


def zero_size_decision(
    *,
    instrument_id: str,
    direction: Direction,
    equity: Decimal,
    source_signal_id: str,
    reason: str,
) -> SizeDecision:
    return SizeDecision(
        instrument_id=instrument_id,
        direction=direction,
        target_notional=Decimal("0"),
        target_quantity=Decimal("0"),
        target_weight=Decimal("0"),
        source_signal_id=source_signal_id,
        reasons=(reason,),
    )


def _signed_weight(notional: Decimal, equity: Decimal, direction: Direction) -> Decimal:
    if direction is Direction.SHORT:
        return -notional / equity
    if direction is Direction.FLAT:
        return Decimal("0")
    return notional / equity


def _append_reason(reasons: tuple[str, ...], reason: str) -> tuple[str, ...]:
    if reason in reasons:
        return reasons
    return (*reasons, reason)


def _direction(value: Any) -> Direction:
    if isinstance(value, Direction):
        return value
    try:
        return Direction(str(value))
    except ValueError as exc:
        raise PortfolioSizingError(f"unsupported direction: {value}") from exc


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioSizingError(f"{field_name} must be a non-empty string")
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise PortfolioSizingError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioSizingError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise PortfolioSizingError(f"{field_name} must be positive")
    return active


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        raise PortfolioSizingError(f"{field_name} must be non-negative")
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _positive_decimal(value, field_name)


def _optional_fraction(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    active = _non_negative_decimal(value, field_name)
    if active > Decimal("1"):
        raise PortfolioSizingError(f"{field_name} must be no greater than 1")
    return active
