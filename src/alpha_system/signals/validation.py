"""Signal schema and no-lookahead validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from alpha_system.signals.spec import (
    SignalRecord,
    SignalSpecError,
    assert_signal_record_schema,
)


class SignalValidationError(ValueError):
    """Raised when signal records violate schema or timing rules."""


def validate_signal_record(value: SignalRecord | Mapping[str, Any]) -> SignalRecord:
    """Return a normalized signal record after schema and timing validation."""
    try:
        record = value if isinstance(value, SignalRecord) else SignalRecord.from_mapping(value)
        assert_signal_record_schema(record)
    except SignalSpecError as exc:
        raise SignalValidationError(str(exc)) from exc
    if record.available_ts < record.event_ts:
        msg = "signal available_ts must be at or after event_ts"
        raise SignalValidationError(msg)
    return record


def validate_signal_records(
    values: Iterable[SignalRecord | Mapping[str, Any]],
) -> tuple[SignalRecord, ...]:
    """Validate a sequence of signal records."""
    return tuple(validate_signal_record(value) for value in values)


def validate_signal_available_ts(
    signal: SignalRecord | Mapping[str, Any],
    factor_values: Iterable[Mapping[str, Any] | Any],
) -> SignalRecord:
    """Raise if a signal is available before any declared input factor value."""
    record = validate_signal_record(signal)
    normalized = tuple(_factor_mapping(value) for value in factor_values)
    if not normalized:
        msg = "at least one factor value is required for signal timing validation"
        raise SignalValidationError(msg)

    declared = dict(record.factor_versions)
    seen: set[str] = set()
    latest_available: datetime | None = None
    for factor in normalized:
        factor_id = _required_string(factor.get("factor_id"), "factor_id")
        factor_version = _required_string(factor.get("factor_version"), "factor_version")
        if factor_id not in declared:
            msg = f"signal used undeclared factor value: {factor_id}"
            raise SignalValidationError(msg)
        if declared[factor_id] != factor_version:
            msg = (
                "signal factor version mismatch: "
                f"{factor_id} expected {declared[factor_id]}, got {factor_version}"
            )
            raise SignalValidationError(msg)
        available_ts = _datetime_value(factor.get("available_ts"), "factor.available_ts")
        latest_available = (
            available_ts
            if latest_available is None
            else max(latest_available, available_ts)
        )
        seen.add(factor_id)

    missing = tuple(sorted(set(declared).difference(seen)))
    if missing:
        msg = f"signal missing factor values for: {', '.join(missing)}"
        raise SignalValidationError(msg)
    if latest_available is not None and record.available_ts < latest_available:
        msg = (
            "signal available_ts must not be earlier than input factor available_ts "
            f"({record.available_ts.isoformat()} < {latest_available.isoformat()})"
        )
        raise SignalValidationError(msg)
    return record


def _factor_mapping(value: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload
    msg = "factor values must be mappings or expose to_dict()"
    raise SignalValidationError(msg)


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise SignalValidationError(msg)
    return value.strip()


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise SignalValidationError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise SignalValidationError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)
