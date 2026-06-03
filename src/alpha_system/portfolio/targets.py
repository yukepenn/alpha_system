"""Portfolio target schema and stable serialization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.portfolio.sizing import SizeDecision


class PortfolioTargetError(ValueError):
    """Raised when a portfolio target violates the schema."""


PORTFOLIO_TARGET_SCHEMA_FIELDS: tuple[str, ...] = (
    "target_id",
    "instrument_id",
    "event_ts",
    "available_ts",
    "session_id",
    "bar_index",
    "direction",
    "target_notional",
    "target_quantity",
    "target_weight",
    "source_signal_id",
    "strategy_id",
    "strategy_version",
    "data_version",
    "quality_flags",
    "rejected",
    "reasons",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioTarget:
    target_id: str
    instrument_id: str
    event_ts: datetime
    available_ts: datetime
    session_id: str
    bar_index: int
    direction: Direction
    target_notional: Decimal
    target_quantity: Decimal
    target_weight: Decimal
    source_signal_id: str
    strategy_id: str
    strategy_version: str
    data_version: str
    quality_flags: tuple[str, ...]
    rejected: bool = False
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_id", _text(self.target_id, "target_id"))
        object.__setattr__(self, "instrument_id", _text(self.instrument_id, "instrument_id"))
        object.__setattr__(self, "event_ts", _datetime_value(self.event_ts, "event_ts"))
        object.__setattr__(self, "available_ts", _datetime_value(self.available_ts, "available_ts"))
        if self.available_ts < self.event_ts:
            raise PortfolioTargetError("portfolio target available_ts must be at or after event_ts")
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id"))
        object.__setattr__(self, "bar_index", _non_negative_int(self.bar_index, "bar_index"))
        object.__setattr__(self, "direction", _direction(self.direction))
        object.__setattr__(self, "target_notional", _non_negative_decimal(self.target_notional, "target_notional"))
        object.__setattr__(self, "target_quantity", _non_negative_decimal(self.target_quantity, "target_quantity"))
        object.__setattr__(self, "target_weight", _decimal(self.target_weight, "target_weight"))
        object.__setattr__(self, "source_signal_id", _text(self.source_signal_id, "source_signal_id"))
        object.__setattr__(self, "strategy_id", _text(self.strategy_id, "strategy_id"))
        object.__setattr__(self, "strategy_version", _text(self.strategy_version, "strategy_version"))
        object.__setattr__(self, "data_version", _text(self.data_version, "data_version"))
        object.__setattr__(self, "quality_flags", _string_tuple(self.quality_flags, "quality_flags"))
        object.__setattr__(self, "rejected", bool(self.rejected))
        object.__setattr__(self, "reasons", _string_tuple(self.reasons, "reasons") if self.reasons else ())
        if self.direction is Direction.FLAT and (self.target_notional != 0 or self.target_quantity != 0):
            raise PortfolioTargetError("flat portfolio targets must have zero notional and quantity")

    @classmethod
    def from_decision(
        cls,
        *,
        decision: SizeDecision,
        target_id: str,
        event_ts: datetime,
        available_ts: datetime,
        session_id: str,
        bar_index: int,
        strategy_id: str,
        strategy_version: str,
        data_version: str,
        quality_flags: Sequence[str],
    ) -> "PortfolioTarget":
        return cls(
            target_id=target_id,
            instrument_id=decision.instrument_id,
            event_ts=event_ts,
            available_ts=available_ts,
            session_id=session_id,
            bar_index=bar_index,
            direction=decision.direction,
            target_notional=decision.target_notional,
            target_quantity=decision.target_quantity,
            target_weight=decision.target_weight,
            source_signal_id=decision.source_signal_id,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            data_version=data_version,
            quality_flags=tuple(quality_flags),
            rejected=decision.rejected,
            reasons=decision.reasons,
        )

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    @property
    def signed_notional(self) -> Decimal:
        if self.direction is Direction.SHORT:
            return -self.target_notional
        if self.direction is Direction.FLAT:
            return Decimal("0")
        return self.target_notional

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "instrument_id": self.instrument_id,
            "event_ts": _datetime_to_text(self.event_ts),
            "available_ts": _datetime_to_text(self.available_ts),
            "session_id": self.session_id,
            "bar_index": self.bar_index,
            "direction": self.direction.value,
            "target_notional": _decimal_text(self.target_notional),
            "target_quantity": _decimal_text(self.target_quantity),
            "target_weight": _decimal_text(self.target_weight),
            "source_signal_id": self.source_signal_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "data_version": self.data_version,
            "quality_flags": list(self.quality_flags),
            "rejected": self.rejected,
            "reasons": list(self.reasons),
        }


def target_id_for(prefix: str, signal_id: str, instrument_id: str, bar_index: int) -> str:
    return f"{_slug(prefix)}:{_slug(instrument_id)}:{bar_index}:{_slug(signal_id)}"


def validate_target_schema(target: PortfolioTarget | Mapping[str, Any]) -> bool:
    payload = target.to_dict() if isinstance(target, PortfolioTarget) else dict(target)
    missing = tuple(field for field in PORTFOLIO_TARGET_SCHEMA_FIELDS if field not in payload)
    if missing:
        raise PortfolioTargetError(f"portfolio target missing fields: {', '.join(missing)}")
    PortfolioTarget(
        target_id=payload["target_id"],
        instrument_id=payload["instrument_id"],
        event_ts=payload["event_ts"],
        available_ts=payload["available_ts"],
        session_id=payload["session_id"],
        bar_index=payload["bar_index"],
        direction=payload["direction"],
        target_notional=payload["target_notional"],
        target_quantity=payload["target_quantity"],
        target_weight=payload["target_weight"],
        source_signal_id=payload["source_signal_id"],
        strategy_id=payload["strategy_id"],
        strategy_version=payload["strategy_version"],
        data_version=payload["data_version"],
        quality_flags=payload["quality_flags"],
        rejected=payload["rejected"],
        reasons=payload["reasons"],
    )
    return True


def targets_to_records(targets: Sequence[PortfolioTarget]) -> tuple[dict[str, Any], ...]:
    ordered = sorted(targets, key=lambda target: (target.instrument_id, target.source_signal_id, target.target_id))
    return tuple(target.to_dict() for target in ordered)


def _slug(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in value.strip())


def _direction(value: Any) -> Direction:
    if isinstance(value, Direction):
        return value
    try:
        return Direction(str(value))
    except ValueError as exc:
        raise PortfolioTargetError(f"unsupported direction: {value}") from exc


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            active = datetime.fromisoformat(text)
        except ValueError as exc:
            raise PortfolioTargetError(f"{field_name} must be an ISO datetime") from exc
    else:
        raise PortfolioTargetError(f"{field_name} must be a datetime")
    if active.tzinfo is None:
        raise PortfolioTargetError(f"{field_name} must be timezone-aware")
    return active.astimezone(timezone.utc)


def _datetime_to_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioTargetError(f"{field_name} must be a non-empty string")
    return value.strip()


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise PortfolioTargetError(f"{field_name} must be a non-negative integer")
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        raise PortfolioTargetError(f"{field_name} must be a non-negative integer") from exc
    if active < 0:
        raise PortfolioTargetError(f"{field_name} must be non-negative")
    return active


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise PortfolioTargetError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioTargetError(f"{field_name} must be numeric") from exc


def _non_negative_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active < 0:
        raise PortfolioTargetError(f"{field_name} must be non-negative")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, bytes):
        values = tuple(str(item) for item in value)
    else:
        raise PortfolioTargetError(f"{field_name} must be a string sequence")
    if any(not item.strip() for item in values):
        raise PortfolioTargetError(f"{field_name} contains an empty value")
    return tuple(item.strip() for item in values)
