"""Signal schemas produced from reviewed factor information."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from alpha_system.core.enums import Direction


class SignalSpecError(ValueError):
    """Raised when signal specifications or records violate the schema."""


class SignalType(str, Enum):
    """Strategy-intent signal types."""

    ENTRY = "entry"
    EXIT = "exit"
    HOLD = "hold"


SIGNAL_RECORD_SCHEMA_FIELDS: tuple[str, ...] = (
    "signal_id",
    "instrument_id",
    "event_ts",
    "available_ts",
    "session_id",
    "bar_index",
    "signal_type",
    "direction",
    "score",
    "confidence",
    "desired_exposure",
    "strategy_id",
    "strategy_version",
    "factor_versions",
    "quality_flags",
    "data_version",
)

REQUIRED_SIGNAL_RECORD_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "event_ts",
    "available_ts",
    "session_id",
    "bar_index",
    "signal_type",
    "direction",
    "strategy_id",
    "strategy_version",
    "factor_versions",
    "quality_flags",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SignalRecord:
    """One point-in-time strategy-intent signal with provenance metadata."""

    signal_id: str
    instrument_id: str
    event_ts: datetime
    available_ts: datetime
    session_id: str
    bar_index: int
    signal_type: SignalType
    direction: Direction
    score: float | Decimal | None
    confidence: float | Decimal | None
    desired_exposure: float | Decimal | None
    strategy_id: str
    strategy_version: str
    factor_versions: Mapping[str, str]
    quality_flags: tuple[str, ...]
    data_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", _required_string(self.signal_id, "signal_id"))
        object.__setattr__(
            self,
            "instrument_id",
            _required_string(self.instrument_id, "instrument_id"),
        )
        object.__setattr__(
            self,
            "event_ts",
            _datetime_value(self.event_ts, "event_ts"),
        )
        object.__setattr__(
            self,
            "available_ts",
            _datetime_value(self.available_ts, "available_ts"),
        )
        if self.available_ts < self.event_ts:
            msg = "signal available_ts must be at or after event_ts"
            raise SignalSpecError(msg)
        object.__setattr__(self, "session_id", _required_string(self.session_id, "session_id"))
        object.__setattr__(self, "bar_index", _non_negative_int(self.bar_index, "bar_index"))
        object.__setattr__(
            self,
            "signal_type",
            _parse_signal_type(self.signal_type, "signal_type"),
        )
        object.__setattr__(
            self,
            "direction",
            _parse_direction(self.direction, "direction"),
        )
        object.__setattr__(self, "score", _optional_number(self.score, "score"))
        object.__setattr__(
            self,
            "confidence",
            _optional_number(self.confidence, "confidence"),
        )
        object.__setattr__(
            self,
            "desired_exposure",
            _optional_number(self.desired_exposure, "desired_exposure"),
        )
        object.__setattr__(
            self,
            "strategy_id",
            _required_string(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(
            self,
            "strategy_version",
            _required_string(self.strategy_version, "strategy_version"),
        )
        object.__setattr__(
            self,
            "factor_versions",
            _version_map(self.factor_versions, "factor_versions"),
        )
        object.__setattr__(
            self,
            "quality_flags",
            _string_tuple(self.quality_flags, "quality_flags"),
        )
        object.__setattr__(self, "data_version", str(self.data_version))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SignalRecord":
        """Build a signal record from a JSON-like mapping."""
        missing = tuple(field for field in REQUIRED_SIGNAL_RECORD_FIELDS if field not in payload)
        if missing:
            msg = f"signal record missing required fields: {', '.join(missing)}"
            raise SignalSpecError(msg)
        return cls(
            signal_id=str(payload.get("signal_id") or _derived_signal_id(payload)),
            instrument_id=payload["instrument_id"],
            event_ts=_datetime_value(payload["event_ts"], "event_ts"),
            available_ts=_datetime_value(payload["available_ts"], "available_ts"),
            session_id=payload["session_id"],
            bar_index=payload["bar_index"],
            signal_type=payload["signal_type"],
            direction=payload["direction"],
            score=payload.get("score"),
            confidence=payload.get("confidence"),
            desired_exposure=payload.get("desired_exposure"),
            strategy_id=payload["strategy_id"],
            strategy_version=payload["strategy_version"],
            factor_versions=payload["factor_versions"],
            quality_flags=_quality_flags(payload["quality_flags"]),
            data_version=str(payload.get("data_version", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize in stable signal-record schema order."""
        return {
            "signal_id": self.signal_id,
            "instrument_id": self.instrument_id,
            "event_ts": _datetime_to_text(self.event_ts),
            "available_ts": _datetime_to_text(self.available_ts),
            "session_id": self.session_id,
            "bar_index": self.bar_index,
            "signal_type": self.signal_type.value,
            "direction": self.direction.value,
            "score": _number_to_json(self.score),
            "confidence": _number_to_json(self.confidence),
            "desired_exposure": _number_to_json(self.desired_exposure),
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "factor_versions": dict(sorted(self.factor_versions.items())),
            "quality_flags": list(self.quality_flags),
            "data_version": self.data_version,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class SignalSpec:
    """Versioned declaration for a signal stream produced by a strategy spec."""

    signal_id: str
    name: str
    strategy_id: str
    strategy_version: str
    signal_type: SignalType
    direction: Direction
    required_factor_ids: tuple[str, ...]
    factor_versions: Mapping[str, str]
    parameters: Mapping[str, Any]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", _required_string(self.signal_id, "signal_id"))
        object.__setattr__(self, "name", _required_string(self.name, "name"))
        object.__setattr__(
            self,
            "strategy_id",
            _required_string(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(
            self,
            "strategy_version",
            _required_string(self.strategy_version, "strategy_version"),
        )
        object.__setattr__(
            self,
            "signal_type",
            _parse_signal_type(self.signal_type, "signal_type"),
        )
        object.__setattr__(
            self,
            "direction",
            _parse_direction(self.direction, "direction"),
        )
        object.__setattr__(
            self,
            "required_factor_ids",
            _string_tuple(self.required_factor_ids, "required_factor_ids"),
        )
        object.__setattr__(
            self,
            "factor_versions",
            _version_map(self.factor_versions, "factor_versions"),
        )
        undeclared = tuple(
            sorted(set(self.factor_versions).difference(self.required_factor_ids))
        )
        if undeclared:
            msg = f"factor_versions contains undeclared factors: {', '.join(undeclared)}"
            raise SignalSpecError(msg)
        object.__setattr__(self, "parameters", _mapping(self.parameters, "parameters"))
        object.__setattr__(self, "metadata", _mapping(self.metadata, "metadata"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SignalSpec":
        """Build a signal specification from a JSON-like mapping."""
        required = (
            "signal_id",
            "name",
            "strategy_id",
            "strategy_version",
            "signal_type",
            "direction",
            "required_factor_ids",
            "factor_versions",
            "parameters",
            "metadata",
        )
        missing = tuple(field for field in required if field not in payload)
        if missing:
            msg = f"SignalSpec missing required fields: {', '.join(missing)}"
            raise SignalSpecError(msg)
        return cls(
            signal_id=payload["signal_id"],
            name=payload["name"],
            strategy_id=payload["strategy_id"],
            strategy_version=payload["strategy_version"],
            signal_type=payload["signal_type"],
            direction=payload["direction"],
            required_factor_ids=_string_tuple(
                payload["required_factor_ids"],
                "required_factor_ids",
            ),
            factor_versions=payload["factor_versions"],
            parameters=payload["parameters"],
            metadata=payload["metadata"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible values."""
        return {
            "signal_id": self.signal_id,
            "name": self.name,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "signal_type": self.signal_type.value,
            "direction": self.direction.value,
            "required_factor_ids": list(self.required_factor_ids),
            "factor_versions": dict(sorted(self.factor_versions.items())),
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


def assert_signal_record_schema(value: SignalRecord | Mapping[str, Any]) -> None:
    """Raise when a signal record does not expose the required schema order."""
    payload = value.to_dict() if isinstance(value, SignalRecord) else dict(value)
    fields = tuple(payload)
    if fields != SIGNAL_RECORD_SCHEMA_FIELDS:
        msg = f"signal record fields differ from schema: {fields!r}"
        raise SignalSpecError(msg)


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise SignalSpecError(msg)
    return value.strip()


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise SignalSpecError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise SignalSpecError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _datetime_to_text(value: datetime) -> str:
    active = value
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer"
        raise SignalSpecError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise SignalSpecError(msg)
    return value


def _optional_number(value: Any, field_name: str) -> float | Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        msg = f"{field_name} must be numeric when present"
        raise SignalSpecError(msg)
    if isinstance(value, int):
        return float(value)
    return value


def _number_to_json(value: float | Decimal | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _parse_signal_type(value: Any, field_name: str) -> SignalType:
    if isinstance(value, SignalType):
        return value
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise SignalSpecError(msg)
    try:
        return SignalType(value.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in SignalType)
        msg = f"{field_name} must be one of: {allowed}"
        raise SignalSpecError(msg) from exc


def _parse_direction(value: Any, field_name: str) -> Direction:
    if isinstance(value, Direction):
        return value
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise SignalSpecError(msg)
    try:
        return Direction(value.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Direction)
        msg = f"{field_name} must be one of: {allowed}"
        raise SignalSpecError(msg) from exc


def _version_map(value: Any, field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or not value:
        msg = f"{field_name} must be a non-empty mapping"
        raise SignalSpecError(msg)
    normalized: dict[str, str] = {}
    for key, item in value.items():
        factor_id = _required_string(key, f"{field_name}.key")
        factor_version = _required_string(item, f"{field_name}.{factor_id}")
        normalized[factor_id] = factor_version
    return normalized


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        msg = f"{field_name} must be a sequence of strings"
        raise SignalSpecError(msg)
    normalized = tuple(_required_string(item, field_name) for item in value)
    if not normalized:
        msg = f"{field_name} must contain at least one value"
        raise SignalSpecError(msg)
    if len(set(normalized)) != len(normalized):
        msg = f"{field_name} must not contain duplicates"
        raise SignalSpecError(msg)
    return normalized


def _quality_flags(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item for item in value.split("|") if item)
    return _string_tuple(value, "quality_flags")


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be a mapping"
        raise SignalSpecError(msg)
    return dict(value)


def _derived_signal_id(payload: Mapping[str, Any]) -> str:
    parts = (
        str(payload.get("strategy_id", "strategy")),
        str(payload.get("strategy_version", "version")),
        str(payload.get("instrument_id", "instrument")),
        str(payload.get("event_ts", "event")),
        str(payload.get("signal_type", "signal")),
    )
    return ":".join(part.strip().replace(":", "_") for part in parts if part)
