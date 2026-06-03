"""In-memory validation for design-only L2 readiness schemas."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import BookSide, L2EventType
from alpha_system.l2.schemas import (
    L2_EVENT_DELTA_FIELDS,
    L2_SNAPSHOT_FIELDS,
    MAX_BOOK_LEVEL,
    MIN_BOOK_LEVEL,
    VALID_L2_SIDES,
    VALID_L2_UPDATE_ACTIONS,
    missing_l2_event_delta_fields,
    missing_l2_snapshot_fields,
)


@dataclass(frozen=True, slots=True)
class L2ValidationIssue:
    code: str
    message: str
    row_index: int | None = None
    field: str | None = None


@dataclass(frozen=True, slots=True)
class L2ValidationResult:
    issues: tuple[L2ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


class L2ValidationError(ValueError):
    """Raised when L2 schema validation is required to fail closed."""

    def __init__(self, issues: tuple[L2ValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _add(
    issues: list[L2ValidationIssue],
    code: str,
    message: str,
    *,
    row_index: int,
    field: str | None = None,
) -> None:
    issues.append(
        L2ValidationIssue(
            code=code,
            message=f"row {row_index}: {message}",
            row_index=row_index,
            field=field,
        )
    )


def _enum_value(value: Any, enum_type: type[BookSide] | type[L2EventType]) -> str | None:
    if isinstance(value, enum_type):
        return str(value.value)
    if isinstance(value, str):
        return value
    return None


def _timestamp(record: Mapping[str, Any], field: str) -> datetime | None:
    value = record.get(field)
    return value if isinstance(value, datetime) else None


def _validate_required(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
    delta: bool,
) -> None:
    missing_fields = (
        missing_l2_event_delta_fields(record)
        if delta
        else missing_l2_snapshot_fields(record)
    )
    for field in missing_fields:
        _add(
            issues,
            "missing_required_field",
            f"{field} is required",
            row_index=row_index,
            field=field,
        )

    fields = L2_EVENT_DELTA_FIELDS if delta else L2_SNAPSHOT_FIELDS
    for field in fields:
        if field.name in record and not field.nullable and record[field.name] is None:
            _add(
                issues,
                "missing_required_field",
                f"{field.name} is required",
                row_index=row_index,
                field=field.name,
            )

    for field in ("instrument_id", "session_id"):
        if field in record and _missing(record[field]):
            _add(
                issues,
                "missing_l2_key",
                f"{field} is required",
                row_index=row_index,
                field=field,
            )

    if "data_version" in record and _missing(record["data_version"]):
        _add(
            issues,
            "missing_data_version",
            "data_version is required",
            row_index=row_index,
            field="data_version",
        )

    if "quality_flags" in record and record["quality_flags"] is None:
        _add(
            issues,
            "missing_quality_flags",
            "quality_flags is required",
            row_index=row_index,
            field="quality_flags",
        )


def _validate_timestamps(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
) -> None:
    timestamps = {field: _timestamp(record, field) for field in ("event_ts", "receive_ts", "available_ts")}
    for field, value in timestamps.items():
        if field not in record:
            continue
        if value is None:
            _add(
                issues,
                "timestamp_type",
                f"{field} must be datetime",
                row_index=row_index,
                field=field,
            )
            continue
        if value.tzinfo is None or value.utcoffset() is None:
            _add(
                issues,
                "timestamp_timezone",
                f"{field} must be timezone-aware",
                row_index=row_index,
                field=field,
            )

    event_ts = timestamps["event_ts"]
    receive_ts = timestamps["receive_ts"]
    available_ts = timestamps["available_ts"]
    if event_ts is None or receive_ts is None or available_ts is None:
        return

    if receive_ts < event_ts:
        _add(
            issues,
            "receive_before_event",
            "receive_ts must be at or after event_ts",
            row_index=row_index,
            field="receive_ts",
        )
    if available_ts < event_ts:
        _add(
            issues,
            "available_before_event",
            "available_ts must be at or after event_ts",
            row_index=row_index,
            field="available_ts",
        )
    if available_ts < receive_ts:
        _add(
            issues,
            "available_before_receive",
            "available_ts must be at or after receive_ts",
            row_index=row_index,
            field="available_ts",
        )


def _validate_side(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
) -> None:
    if "side" not in record:
        return
    value = _enum_value(record["side"], BookSide)
    if value not in VALID_L2_SIDES:
        _add(
            issues,
            "invalid_side",
            f"side must be one of {', '.join(VALID_L2_SIDES)}",
            row_index=row_index,
            field="side",
        )


def _action_value(record: Mapping[str, Any]) -> str | None:
    if "action" not in record:
        return None
    return _enum_value(record["action"], L2EventType)


def _validate_action(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
) -> str | None:
    value = _action_value(record)
    if value not in VALID_L2_UPDATE_ACTIONS:
        _add(
            issues,
            "invalid_update_action",
            f"action must be one of {', '.join(VALID_L2_UPDATE_ACTIONS)}",
            row_index=row_index,
            field="action",
        )
    return value


def _validate_book_level(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
    required_for_record: bool,
) -> None:
    if "book_level" not in record:
        return
    value = record["book_level"]
    if value is None:
        if required_for_record:
            _add(
                issues,
                "missing_book_level",
                "book_level is required for this L2 record",
                row_index=row_index,
                field="book_level",
            )
        return
    if not isinstance(value, int) or isinstance(value, bool):
        _add(
            issues,
            "book_level_type",
            "book_level must be int",
            row_index=row_index,
            field="book_level",
        )
        return
    if value < MIN_BOOK_LEVEL or value > MAX_BOOK_LEVEL:
        _add(
            issues,
            "book_level_bounds",
            f"book_level must be between {MIN_BOOK_LEVEL} and {MAX_BOOK_LEVEL}",
            row_index=row_index,
            field="book_level",
        )


def _validate_optional_int(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
    field: str,
    minimum: int,
) -> None:
    if field not in record or record[field] is None:
        return
    value = record[field]
    if not isinstance(value, int) or isinstance(value, bool):
        _add(
            issues,
            f"{field}_type",
            f"{field} must be int when provided",
            row_index=row_index,
            field=field,
        )
        return
    if value < minimum:
        _add(
            issues,
            f"{field}_bounds",
            f"{field} must be at least {minimum} when provided",
            row_index=row_index,
            field=field,
        )


def _validate_decimal_fields(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
) -> None:
    for field in ("price", "size"):
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, Decimal):
            _add(
                issues,
                "decimal_type",
                f"{field} must be Decimal",
                row_index=row_index,
                field=field,
            )
            continue
        if field == "price" and value <= 0:
            _add(
                issues,
                "price_bounds",
                "price must be positive",
                row_index=row_index,
                field=field,
            )
        if field == "size" and value < 0:
            _add(
                issues,
                "size_bounds",
                "size must be nonnegative",
                row_index=row_index,
                field=field,
            )


def _validate_quality_flags(
    record: Mapping[str, Any],
    issues: list[L2ValidationIssue],
    *,
    row_index: int,
) -> None:
    if "quality_flags" not in record or record["quality_flags"] is None:
        return
    value = record["quality_flags"]
    if not isinstance(value, tuple) or not all(isinstance(flag, str) for flag in value):
        _add(
            issues,
            "quality_flags_type",
            "quality_flags must be tuple[str, ...]",
            row_index=row_index,
            field="quality_flags",
        )


def _validate_common(
    record: Mapping[str, Any],
    *,
    row_index: int,
    delta: bool,
) -> list[L2ValidationIssue]:
    issues: list[L2ValidationIssue] = []
    _validate_required(record, issues, row_index=row_index, delta=delta)
    _validate_timestamps(record, issues, row_index=row_index)
    _validate_side(record, issues, row_index=row_index)
    _validate_decimal_fields(record, issues, row_index=row_index)
    _validate_optional_int(
        record,
        issues,
        row_index=row_index,
        field="order_count",
        minimum=0,
    )
    _validate_quality_flags(record, issues, row_index=row_index)
    return issues


def validate_l2_snapshot(
    record: Mapping[str, Any],
    *,
    row_index: int = 0,
) -> L2ValidationResult:
    """Validate one in-memory synthetic L2 snapshot row."""
    issues = _validate_common(record, row_index=row_index, delta=False)
    _validate_book_level(
        record,
        issues,
        row_index=row_index,
        required_for_record=True,
    )
    return L2ValidationResult(tuple(issues))


def validate_l2_delta(
    record: Mapping[str, Any],
    *,
    row_index: int = 0,
) -> L2ValidationResult:
    """Validate one in-memory synthetic L2 event/delta row."""
    issues = _validate_common(record, row_index=row_index, delta=True)
    action = _validate_action(record, issues, row_index=row_index)
    _validate_optional_int(
        record,
        issues,
        row_index=row_index,
        field="sequence_id",
        minimum=1,
    )
    _validate_book_level(
        record,
        issues,
        row_index=row_index,
        required_for_record=action != L2EventType.CLEAR.value,
    )
    return L2ValidationResult(tuple(issues))


def validate_l2_snapshot_delta_consistency(
    snapshot: Mapping[str, Any],
    deltas: Iterable[Mapping[str, Any]],
) -> L2ValidationResult:
    """Validate the design-only contract between one snapshot and later deltas."""
    issues: list[L2ValidationIssue] = list(
        validate_l2_snapshot(snapshot, row_index=0).issues
    )
    materialized_deltas = tuple(deltas)
    previous_sequence_id: int | None = None

    for index, delta in enumerate(materialized_deltas, start=1):
        issues.extend(validate_l2_delta(delta, row_index=index).issues)

        for field in ("instrument_id", "session_id", "data_version"):
            if field in snapshot and field in delta and snapshot[field] != delta[field]:
                _add(
                    issues,
                    "snapshot_delta_mismatch",
                    f"delta {field} must match snapshot {field}",
                    row_index=index,
                    field=field,
                )

        snapshot_event_ts = _timestamp(snapshot, "event_ts")
        delta_event_ts = _timestamp(delta, "event_ts")
        if (
            snapshot_event_ts is not None
            and delta_event_ts is not None
            and delta_event_ts < snapshot_event_ts
        ):
            _add(
                issues,
                "delta_before_snapshot_event",
                "delta event_ts must not precede snapshot event_ts",
                row_index=index,
                field="event_ts",
            )

        snapshot_available_ts = _timestamp(snapshot, "available_ts")
        delta_available_ts = _timestamp(delta, "available_ts")
        if (
            snapshot_available_ts is not None
            and delta_available_ts is not None
            and delta_available_ts < snapshot_available_ts
        ):
            _add(
                issues,
                "delta_before_snapshot_available",
                "delta available_ts must not precede snapshot available_ts",
                row_index=index,
                field="available_ts",
            )

        sequence_id = delta.get("sequence_id")
        if isinstance(sequence_id, int) and not isinstance(sequence_id, bool):
            if previous_sequence_id is not None and sequence_id <= previous_sequence_id:
                _add(
                    issues,
                    "sequence_id_order",
                    "sequence_id must increase across provided deltas",
                    row_index=index,
                    field="sequence_id",
                )
            previous_sequence_id = sequence_id

    return L2ValidationResult(tuple(issues))


def require_valid_l2_snapshot(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a snapshot record when valid, otherwise raise."""
    result = validate_l2_snapshot(record)
    if not result.valid:
        raise L2ValidationError(result.issues)
    return record


def require_valid_l2_delta(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a delta record when valid, otherwise raise."""
    result = validate_l2_delta(record)
    if not result.valid:
        raise L2ValidationError(result.issues)
    return record
