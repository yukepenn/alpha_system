"""Simple local liquidity controls for conservative research simulation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


ZERO = Decimal("0")


class LiquidityModelError(ValueError):
    """Raised when a liquidity input or policy is invalid."""


class LiquidityRejectedError(LiquidityModelError):
    """Raised when a fill is rejected by the conservative liquidity policy."""


@dataclass(frozen=True, slots=True)
class LiquidityInput:
    """Inputs for a simple participation cap and liquidity penalty."""

    requested_quantity: Decimal
    bar_volume: Decimal | None
    price: Decimal
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_quantity",
            _positive_decimal(self.requested_quantity, "requested_quantity"),
        )
        object.__setattr__(
            self,
            "bar_volume",
            None if self.bar_volume is None else _non_negative_decimal(self.bar_volume, "bar_volume"),
        )
        object.__setattr__(self, "price", _non_negative_decimal(self.price, "price"))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True, slots=True)
class LiquidityDecision:
    """Deterministic outcome of applying local liquidity controls."""

    accepted: bool
    requested_quantity: Decimal
    fill_quantity: Decimal
    rejected_quantity: Decimal
    max_quantity: Decimal
    participation_rate: Decimal
    penalty_cost: Decimal = ZERO
    reason: str = "accepted"

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_quantity", _positive_decimal(self.requested_quantity, "requested_quantity"))
        object.__setattr__(self, "fill_quantity", _non_negative_decimal(self.fill_quantity, "fill_quantity"))
        object.__setattr__(self, "rejected_quantity", _non_negative_decimal(self.rejected_quantity, "rejected_quantity"))
        object.__setattr__(self, "max_quantity", _non_negative_decimal(self.max_quantity, "max_quantity"))
        object.__setattr__(self, "participation_rate", _non_negative_decimal(self.participation_rate, "participation_rate"))
        object.__setattr__(self, "penalty_cost", _non_negative_decimal(self.penalty_cost, "penalty_cost"))

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "accepted": self.accepted,
            "requested_quantity": _decimal_text(self.requested_quantity),
            "fill_quantity": _decimal_text(self.fill_quantity),
            "rejected_quantity": _decimal_text(self.rejected_quantity),
            "max_quantity": _decimal_text(self.max_quantity),
            "participation_rate": _decimal_text(self.participation_rate),
            "penalty_cost": _decimal_text(self.penalty_cost),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VolumeParticipationCap:
    """Cap requested quantity to a configured fraction of bar volume."""

    max_participation: Decimal

    def __post_init__(self) -> None:
        active = _positive_decimal(self.max_participation, "max_participation")
        if active > Decimal("1"):
            msg = "max_participation must be <= 1"
            raise LiquidityModelError(msg)
        object.__setattr__(self, "max_participation", active)

    def max_quantity_for(self, bar_volume: Decimal | None) -> Decimal:
        if bar_volume is None:
            return ZERO
        return _non_negative_decimal(bar_volume, "bar_volume") * self.max_participation

    def cap(self, request: LiquidityInput) -> LiquidityDecision:
        max_quantity = self.max_quantity_for(request.bar_volume)
        fill_quantity = min(request.requested_quantity, max_quantity)
        rejected_quantity = request.requested_quantity - fill_quantity
        participation_rate = ZERO if request.bar_volume in (None, ZERO) else fill_quantity / request.bar_volume
        return LiquidityDecision(
            accepted=fill_quantity > ZERO,
            requested_quantity=request.requested_quantity,
            fill_quantity=fill_quantity,
            rejected_quantity=rejected_quantity,
            max_quantity=max_quantity,
            participation_rate=participation_rate,
            reason="accepted" if rejected_quantity == ZERO and fill_quantity > ZERO else "capped",
        )


@dataclass(frozen=True, slots=True)
class LiquidityPolicy:
    """Apply participation caps, optional rejection, and optional penalty."""

    max_participation: Decimal = Decimal("0.10")
    reject_when_exceeds: bool = False
    penalty_bps_when_capped: Decimal = ZERO

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_participation", _positive_decimal(self.max_participation, "max_participation"))
        if self.max_participation > Decimal("1"):
            msg = "max_participation must be <= 1"
            raise LiquidityModelError(msg)
        object.__setattr__(
            self,
            "penalty_bps_when_capped",
            _non_negative_decimal(self.penalty_bps_when_capped, "penalty_bps_when_capped"),
        )

    def evaluate(self, request: LiquidityInput) -> LiquidityDecision:
        base = VolumeParticipationCap(self.max_participation).cap(request)
        if request.bar_volume in (None, ZERO) or base.fill_quantity == ZERO:
            if self.reject_when_exceeds:
                raise LiquidityRejectedError("fill rejected because bar volume is unavailable or zero")
            return LiquidityDecision(
                accepted=False,
                requested_quantity=request.requested_quantity,
                fill_quantity=ZERO,
                rejected_quantity=request.requested_quantity,
                max_quantity=ZERO,
                participation_rate=ZERO,
                reason="no_liquidity",
            )
        if base.rejected_quantity > ZERO and self.reject_when_exceeds:
            raise LiquidityRejectedError("fill rejected because requested quantity exceeds participation cap")
        penalty = ZERO
        if base.rejected_quantity > ZERO and self.penalty_bps_when_capped > ZERO:
            penalty = request.price * base.fill_quantity * self.penalty_bps_when_capped / Decimal("10000")
        return LiquidityDecision(
            accepted=base.accepted,
            requested_quantity=base.requested_quantity,
            fill_quantity=base.fill_quantity,
            rejected_quantity=base.rejected_quantity,
            max_quantity=base.max_quantity,
            participation_rate=base.participation_rate,
            penalty_cost=penalty,
            reason=base.reason,
        )

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "model": "volume_participation",
            "max_participation": _decimal_text(self.max_participation),
            "reject_when_exceeds": self.reject_when_exceeds,
            "penalty_bps_when_capped": _decimal_text(self.penalty_bps_when_capped),
        }


def liquidity_policy_from_mapping(payload: Mapping[str, Any] | None) -> LiquidityPolicy:
    """Parse a small deterministic liquidity policy mapping."""

    if payload is None:
        return LiquidityPolicy()
    return LiquidityPolicy(
        max_participation=_decimal(payload.get("max_participation", "0.10"), "max_participation"),
        reject_when_exceeds=bool(payload.get("reject_when_exceeds", False)),
        penalty_bps_when_capped=_decimal(payload.get("penalty_bps_when_capped", "0"), "penalty_bps_when_capped"),
    )


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise LiquidityModelError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise LiquidityModelError(msg) from exc


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < ZERO:
        msg = f"{field_name} must be non-negative"
        raise LiquidityModelError(msg)
    return active


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= ZERO:
        msg = f"{field_name} must be positive"
        raise LiquidityModelError(msg)
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
