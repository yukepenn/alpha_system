"""Base abstractions for deterministic factor computation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from alpha_system.factors.quality import normalize_quality_flags
from alpha_system.factors.spec import FactorSpec


FACTOR_VALUE_SCHEMA_FIELDS: tuple[str, ...] = (
    "factor_id",
    "factor_version",
    "instrument_id",
    "event_ts",
    "available_ts",
    "session_id",
    "bar_index",
    "value",
    "normalized_value",
    "quality_flags",
    "data_version",
    "compute_version",
)


class FactorComputeError(ValueError):
    """Raised when a factor implementation cannot compute deterministically."""


@dataclass(frozen=True, slots=True)
class FactorComputeContext:
    """Point-in-time compute context supplied to factor implementations."""

    spec: FactorSpec
    bar: Mapping[str, Any]
    input_history: tuple[Mapping[str, Any], ...]

    @property
    def parameters(self) -> Mapping[str, Any]:
        return self.spec.parameters


@dataclass(frozen=True, slots=True)
class FactorValue:
    """One computed factor value with the required ASV1-P11 schema."""

    factor_id: str
    factor_version: str
    instrument_id: str
    event_ts: datetime
    available_ts: datetime
    session_id: str
    bar_index: int
    value: float | str | None
    normalized_value: float | None
    quality_flags: tuple[str, ...]
    data_version: str
    compute_version: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize in stable factor-value schema order."""
        return {
            "factor_id": self.factor_id,
            "factor_version": self.factor_version,
            "instrument_id": self.instrument_id,
            "event_ts": _datetime_to_text(self.event_ts),
            "available_ts": _datetime_to_text(self.available_ts),
            "session_id": self.session_id,
            "bar_index": self.bar_index,
            "value": self.value,
            "normalized_value": self.normalized_value,
            "quality_flags": list(self.quality_flags),
            "data_version": self.data_version,
            "compute_version": self.compute_version,
        }


class BaseFactor(ABC):
    """Pure point-in-time factor implementation interface."""

    @property
    @abstractmethod
    def used_fields(self) -> tuple[str, ...]:
        """Return declared input names or source fields used by this factor."""

    @abstractmethod
    def compute(
        self,
        inputs: Mapping[str, Any],
        context: FactorComputeContext,
    ) -> Any:
        """Compute from declared inputs and prior point-in-time input history."""


@dataclass(frozen=True, slots=True)
class CorrectnessFixtureFactor(BaseFactor):
    """Tiny deterministic fixture factor used only by correctness tests."""

    input_name: str
    lag_bars: int = 1

    @property
    def used_fields(self) -> tuple[str, ...]:
        return (self.input_name,)

    def compute(
        self,
        inputs: Mapping[str, Any],
        context: FactorComputeContext,
    ) -> Any:
        if self.lag_bars <= 0:
            msg = "lag_bars must be positive"
            raise FactorComputeError(msg)
        if len(context.input_history) <= self.lag_bars:
            return None
        current = inputs[self.input_name]
        previous = context.input_history[-self.lag_bars - 1][self.input_name]
        if current is None or previous is None:
            return None
        return _numeric_delta(current, previous)


def build_factor_from_spec(spec: FactorSpec) -> BaseFactor:
    """Build the scoped MVP correctness fixture factor from spec parameters."""
    payload = spec.parameters.get("fixture_compute", {})
    if not isinstance(payload, Mapping):
        msg = "fixture_compute parameters must be a mapping"
        raise FactorComputeError(msg)

    name = str(payload.get("name", "close_delta")).strip().lower()
    if name != "close_delta":
        msg = f"unsupported fixture_compute name: {name}"
        raise FactorComputeError(msg)

    if not spec.input_fields:
        msg = "at least one declared input field is required"
        raise FactorComputeError(msg)
    input_name = str(payload.get("input_name", spec.input_fields[0].name))
    lag_bars = _positive_int(payload.get("lag_bars", 1), "lag_bars")
    return CorrectnessFixtureFactor(input_name=input_name, lag_bars=lag_bars)


def assert_factor_value_schema(value: FactorValue | Mapping[str, Any]) -> None:
    """Raise when a factor value does not expose the exact required fields."""
    payload = value.to_dict() if isinstance(value, FactorValue) else dict(value)
    fields = tuple(payload)
    if fields != FACTOR_VALUE_SCHEMA_FIELDS:
        msg = f"factor value fields differ from schema: {fields!r}"
        raise FactorComputeError(msg)


def coerce_factor_value(value: Any) -> float | str | None:
    """Coerce factor outputs to a deterministic JSON-compatible scalar."""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return value
    msg = f"unsupported factor value type: {type(value).__name__}"
    raise FactorComputeError(msg)


def factor_value_from_parts(
    *,
    spec: FactorSpec,
    bar: Mapping[str, Any],
    available_ts: datetime,
    value: Any,
    normalized_value: float | None,
    quality_flags: Sequence[Any],
    data_version: str,
    compute_version: str,
) -> FactorValue:
    """Construct and schema-check a factor value from compute pieces."""
    result = FactorValue(
        factor_id=spec.factor_id,
        factor_version=spec.version,
        instrument_id=str(bar["instrument_id"]),
        event_ts=_datetime_value(bar["event_ts"], "event_ts"),
        available_ts=available_ts,
        session_id=str(bar["session_id"]),
        bar_index=_int_value(bar["bar_index"], "bar_index"),
        value=coerce_factor_value(value),
        normalized_value=normalized_value,
        quality_flags=normalize_quality_flags(quality_flags),
        data_version=data_version,
        compute_version=compute_version,
    )
    assert_factor_value_schema(result)
    return result


def _numeric_delta(current: Any, previous: Any) -> Any:
    if isinstance(current, Decimal) or isinstance(previous, Decimal):
        return Decimal(str(current)) - Decimal(str(previous))
    if isinstance(current, int | float) and isinstance(previous, int | float):
        return float(current) - float(previous)
    msg = "correctness fixture inputs must be numeric"
    raise FactorComputeError(msg)


def _datetime_to_text(value: datetime) -> str:
    active = value
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise FactorComputeError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise FactorComputeError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _int_value(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be int"
        raise FactorComputeError(msg)
    return value


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a positive integer"
        raise FactorComputeError(msg)
    if value <= 0:
        msg = f"{field_name} must be positive"
        raise FactorComputeError(msg)
    return value
