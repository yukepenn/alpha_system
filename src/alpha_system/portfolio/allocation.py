"""Capital allocation state for portfolio target construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.portfolio.spec import CapitalAllocationSpec


class CapitalAllocationError(ValueError):
    """Raised when allocation state is invalid."""


@dataclass(frozen=True, slots=True)
class CapitalAllocationState:
    total_equity: Decimal
    cash_available: Decimal
    reserved_notional_by_instrument: Mapping[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "total_equity", _positive_decimal(self.total_equity, "total_equity"))
        object.__setattr__(self, "cash_available", _non_negative_decimal(self.cash_available, "cash_available"))
        reserved = {
            _text(instrument_id, "instrument_id"): _non_negative_decimal(value, "reserved_notional")
            for instrument_id, value in self.reserved_notional_by_instrument.items()
        }
        object.__setattr__(self, "reserved_notional_by_instrument", dict(sorted(reserved.items())))

    @classmethod
    def from_spec(cls, spec: CapitalAllocationSpec) -> "CapitalAllocationState":
        return cls(total_equity=spec.starting_equity, cash_available=spec.starting_equity)

    @property
    def reserved_notional(self) -> Decimal:
        return sum(self.reserved_notional_by_instrument.values(), Decimal("0"))

    def available_notional(self, spec: CapitalAllocationSpec) -> Decimal:
        buffered_cash = self.cash_available * (Decimal("1") - spec.cash_buffer)
        return max(buffered_cash - self.reserved_notional, Decimal("0"))

    def reserve(self, instrument_id: str, notional: Decimal) -> "CapitalAllocationState":
        active_instrument = _text(instrument_id, "instrument_id")
        active_notional = _non_negative_decimal(notional, "notional")
        updated = dict(self.reserved_notional_by_instrument)
        updated[active_instrument] = updated.get(active_instrument, Decimal("0")) + active_notional
        return replace(self, reserved_notional_by_instrument=updated)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CapitalAllocationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise CapitalAllocationError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CapitalAllocationError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise CapitalAllocationError(f"{field_name} must be positive")
    return active


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        raise CapitalAllocationError(f"{field_name} must be non-negative")
    return active
