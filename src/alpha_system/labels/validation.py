"""Label validation and no-lookahead guards."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from alpha_system.labels.spec import LabelSpec, LabelSpecError


class LabelValidationError(ValueError):
    """Raised when a label record violates no-lookahead or schema rules."""


def validate_label_record(label: LabelSpec | Mapping[str, Any]) -> LabelSpec:
    """Validate one label record and return its normalized representation."""
    try:
        spec = label if isinstance(label, LabelSpec) else LabelSpec.from_mapping(label)
    except LabelSpecError as exc:
        raise LabelValidationError(str(exc)) from exc

    metadata = dict(spec.path_metadata)
    for required in ("session_id", "label_version", "horizon_end_ts"):
        if required not in metadata or str(metadata[required]).strip() == "":
            msg = f"path_metadata.{required} is required for label alignment"
            raise LabelValidationError(msg)

    horizon_end_ts = _datetime(metadata["horizon_end_ts"], "path_metadata.horizon_end_ts")
    if spec.label_available_ts < horizon_end_ts:
        msg = "label_available_ts must be at or after horizon_end_ts"
        raise LabelValidationError(msg)
    if spec.label_available_ts < spec.event_ts:
        msg = "label_available_ts must be at or after event_ts"
        raise LabelValidationError(msg)

    required_bars = int(metadata.get("required_future_bars", 0))
    observed_bars = int(metadata.get("observed_future_bars", 0))
    insufficient = bool(metadata.get("insufficient_future", False))
    if required_bars < 1:
        msg = "path_metadata.required_future_bars must be positive"
        raise LabelValidationError(msg)
    if observed_bars < required_bars and not insufficient:
        msg = "insufficient future bars must be represented explicitly"
        raise LabelValidationError(msg)
    if insufficient and spec.value is not None:
        msg = "insufficient future labels must use a null value"
        raise LabelValidationError(msg)
    return spec


def validate_label_collection(labels: Iterable[LabelSpec | Mapping[str, Any]]) -> tuple[LabelSpec, ...]:
    """Validate a collection of labels and reject duplicate label ids per key."""
    normalized = tuple(validate_label_record(label) for label in labels)
    seen: set[tuple[str, str, datetime, str, str, str]] = set()
    for label in normalized:
        metadata = dict(label.path_metadata)
        key = (
            label.instrument_id,
            metadata["session_id"],
            label.event_ts,
            label.label_id,
            label.data_version,
            metadata["label_version"],
        )
        if key in seen:
            msg = f"duplicate label alignment key: {key}"
            raise LabelValidationError(msg)
        seen.add(key)
    return normalized


def assert_label_not_available_before(
    label: LabelSpec | Mapping[str, Any],
    *,
    as_of_ts: datetime,
) -> None:
    """Reject attempts to read a label before its availability timestamp."""
    spec = validate_label_record(label)
    as_of = _datetime(as_of_ts, "as_of_ts")
    if as_of < spec.label_available_ts:
        msg = "label is not available at the requested as_of_ts"
        raise LabelValidationError(msg)


def validate_no_lookahead(labels: Iterable[LabelSpec | Mapping[str, Any]]) -> None:
    """Validate that every label is gated at or after its future horizon."""
    for label in labels:
        validate_label_record(label)


def _datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        msg = f"{field_name} must be a datetime or ISO-8601 string"
        raise LabelValidationError(msg)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise LabelValidationError(msg)
    return parsed.astimezone(timezone.utc)
