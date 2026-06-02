"""Canonical 1-minute bar validation primitives."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.data.bar_schema import (
    BAR_KEY_FIELDS,
    REQUIRED_BAR_FIELDS,
    TIMESTAMP_FIELDS,
    VERSION_FIELDS,
    field_type_errors,
    missing_required_fields,
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    row_index: int | None = None
    field: str | None = None


@dataclass(frozen=True, slots=True)
class BarValidationConfig:
    available_latency: timedelta = timedelta(0)
    spread_tolerance: Decimal = Decimal("0.000001")
    require_event_within_bar: bool = True


@dataclass(frozen=True, slots=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def messages(self) -> tuple[str, ...]:
        return tuple(issue.message for issue in self.issues)


class BarValidationError(ValueError):
    """Raised when canonical bar validation fails."""

    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        self.issues = issues
        messages = "; ".join(issue.message for issue in issues)
        super().__init__(messages)


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _add(
    issues: list[ValidationIssue],
    code: str,
    message: str,
    *,
    row_index: int,
    field: str | None = None,
) -> None:
    issues.append(
        ValidationIssue(
            code=code,
            message=f"row {row_index}: {message}",
            row_index=row_index,
            field=field,
        )
    )


def _decimal(record: Mapping[str, Any], field: str) -> Decimal | None:
    value = record.get(field)
    return value if isinstance(value, Decimal) else None


def _timestamp(record: Mapping[str, Any], field: str) -> datetime | None:
    value = record.get(field)
    return value if isinstance(value, datetime) else None


def _validate_required(
    record: Mapping[str, Any],
    issues: list[ValidationIssue],
    *,
    row_index: int,
) -> None:
    for field in missing_required_fields(record):
        _add(
            issues,
            "missing_required_field",
            f"{field} is required",
            row_index=row_index,
            field=field,
        )
    for field in BAR_KEY_FIELDS:
        if field in record and _missing(record[field]):
            _add(
                issues,
                "missing_bar_key",
                f"{field} is required",
                row_index=row_index,
                field=field,
            )
    for field in VERSION_FIELDS:
        if field in record and _missing(record[field]):
            _add(
                issues,
                "missing_version",
                f"{field} is required",
                row_index=row_index,
                field=field,
            )


def _validate_types(
    record: Mapping[str, Any],
    issues: list[ValidationIssue],
    *,
    row_index: int,
) -> None:
    for message in field_type_errors(record):
        field = message.split(" ", maxsplit=1)[0]
        _add(issues, "field_type", message, row_index=row_index, field=field)


def _validate_timestamps(
    record: Mapping[str, Any],
    issues: list[ValidationIssue],
    *,
    row_index: int,
    config: BarValidationConfig,
) -> None:
    timestamps = {field: _timestamp(record, field) for field in TIMESTAMP_FIELDS}
    if any(value is None for value in timestamps.values()):
        return

    start = timestamps["bar_start_ts"]
    end = timestamps["bar_end_ts"]
    event = timestamps["event_ts"]
    available = timestamps["available_ts"]
    assert start is not None
    assert end is not None
    assert event is not None
    assert available is not None

    if start >= end:
        _add(
            issues,
            "bar_interval_order",
            "bar_start_ts must be before bar_end_ts",
            row_index=row_index,
            field="bar_start_ts",
        )
    if config.require_event_within_bar and not (start <= event <= end):
        _add(
            issues,
            "event_ts_order",
            "event_ts must fall inside the bar interval",
            row_index=row_index,
            field="event_ts",
        )
    if available < event:
        _add(
            issues,
            "available_before_event",
            "available_ts must not precede event_ts",
            row_index=row_index,
            field="available_ts",
        )
    earliest_available = end + config.available_latency
    if available < earliest_available:
        _add(
            issues,
            "available_before_bar_latency",
            "available_ts must be at or after bar_end_ts plus latency",
            row_index=row_index,
            field="available_ts",
        )


def _validate_ohlc(
    record: Mapping[str, Any],
    issues: list[ValidationIssue],
    *,
    row_index: int,
) -> None:
    open_ = _decimal(record, "open")
    high = _decimal(record, "high")
    low = _decimal(record, "low")
    close = _decimal(record, "close")
    volume = _decimal(record, "volume")
    if high is not None and low is not None and high < low:
        _add(
            issues,
            "ohlc_high_low",
            "high must be greater than or equal to low",
            row_index=row_index,
            field="high",
        )
    if (
        low is not None
        and high is not None
        and open_ is not None
        and not (low <= open_ <= high)
    ):
        _add(
            issues,
            "ohlc_open_range",
            "open must be between low and high",
            row_index=row_index,
            field="open",
        )
    if (
        low is not None
        and high is not None
        and close is not None
        and not (low <= close <= high)
    ):
        _add(
            issues,
            "ohlc_close_range",
            "close must be between low and high",
            row_index=row_index,
            field="close",
        )
    if volume is not None and volume < 0:
        _add(
            issues,
            "negative_volume",
            "volume must be nonnegative",
            row_index=row_index,
            field="volume",
        )

    trade_count = record.get("trade_count")
    if isinstance(trade_count, int) and trade_count < 0:
        _add(
            issues,
            "negative_trade_count",
            "trade_count must be nonnegative",
            row_index=row_index,
            field="trade_count",
        )


def _validate_spread(
    record: Mapping[str, Any],
    issues: list[ValidationIssue],
    *,
    row_index: int,
    config: BarValidationConfig,
) -> None:
    bid = _decimal(record, "bid")
    ask = _decimal(record, "ask")
    spread = _decimal(record, "spread")
    if spread is not None and spread < 0:
        _add(
            issues,
            "negative_spread",
            "spread must be nonnegative",
            row_index=row_index,
            field="spread",
        )
    if bid is None or ask is None:
        return
    if bid < 0:
        _add(issues, "negative_bid", "bid must be nonnegative", row_index=row_index, field="bid")
    if ask < 0:
        _add(issues, "negative_ask", "ask must be nonnegative", row_index=row_index, field="ask")
    if bid > ask:
        _add(
            issues,
            "bid_above_ask",
            "bid must be less than or equal to ask",
            row_index=row_index,
            field="bid",
        )
    if spread is not None and abs((ask - bid) - spread) > config.spread_tolerance:
        _add(
            issues,
            "spread_mismatch",
            "spread must equal ask minus bid within tolerance",
            row_index=row_index,
            field="spread",
        )


def validate_bar(
    record: Mapping[str, Any],
    *,
    row_index: int = 0,
    config: BarValidationConfig | None = None,
) -> ValidationResult:
    """Validate one normalized canonical bar record."""
    active_config = config or BarValidationConfig()
    issues: list[ValidationIssue] = []
    _validate_required(record, issues, row_index=row_index)
    _validate_types(record, issues, row_index=row_index)
    _validate_timestamps(record, issues, row_index=row_index, config=active_config)
    _validate_ohlc(record, issues, row_index=row_index)
    _validate_spread(record, issues, row_index=row_index, config=active_config)
    return ValidationResult(tuple(issues))


def _duplicate_issues(rows: tuple[Mapping[str, Any], ...]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    seen_bar_keys: dict[tuple[Any, Any, Any], int] = {}
    seen_ts_keys: dict[tuple[Any, Any, Any], int] = {}
    for index, row in enumerate(rows):
        bar_key = (row.get("instrument_id"), row.get("session_id"), row.get("bar_index"))
        if not any(_missing(value) for value in bar_key):
            previous = seen_bar_keys.get(bar_key)
            if previous is None:
                seen_bar_keys[bar_key] = index
            else:
                _add(
                    issues,
                    "duplicate_bar_index_key",
                    f"duplicates row {previous} by instrument/session/bar_index",
                    row_index=index,
                )

        ts_key = (
            row.get("instrument_id"),
            row.get("session_id"),
            row.get("bar_start_ts"),
        )
        if not any(_missing(value) for value in ts_key):
            previous = seen_ts_keys.get(ts_key)
            if previous is None:
                seen_ts_keys[ts_key] = index
            else:
                _add(
                    issues,
                    "duplicate_bar_timestamp_key",
                    f"duplicates row {previous} by instrument/session/bar_start_ts",
                    row_index=index,
                )
    return tuple(issues)


def validate_bars(
    rows: Iterable[Mapping[str, Any]],
    *,
    config: BarValidationConfig | None = None,
) -> ValidationResult:
    """Validate canonical bars including duplicate identity checks."""
    materialized = tuple(rows)
    issues: list[ValidationIssue] = []
    for index, row in enumerate(materialized):
        issues.extend(validate_bar(row, row_index=index, config=config).issues)
    issues.extend(_duplicate_issues(materialized))
    return ValidationResult(tuple(issues))


def require_valid_bars(
    rows: Iterable[Mapping[str, Any]],
    *,
    config: BarValidationConfig | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Return rows when valid, otherwise raise BarValidationError."""
    materialized = tuple(rows)
    result = validate_bars(materialized, config=config)
    if not result.valid:
        raise BarValidationError(result.issues)
    return materialized
