"""Canonical 1-minute bar schema primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from alpha_system.core.schema import contract_field_names, missing_contract_fields
from alpha_system.data.contracts import OneMinuteBar


REQUIRED_BAR_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "session_id",
    "bar_index",
    "bar_start_ts",
    "bar_end_ts",
    "event_ts",
    "available_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "vwap",
    "trade_count",
    "bid",
    "ask",
    "spread",
    "source_version",
    "data_version",
    "quality_flags",
)

TIMESTAMP_FIELDS: tuple[str, ...] = (
    "bar_start_ts",
    "bar_end_ts",
    "event_ts",
    "available_ts",
)

DECIMAL_FIELDS: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "vwap",
    "bid",
    "ask",
    "spread",
)

OPTIONAL_DECIMAL_FIELDS: tuple[str, ...] = ("bid", "ask", "spread")
STRING_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "session_id",
    "source_version",
    "data_version",
)
INT_FIELDS: tuple[str, ...] = ("bar_index", "trade_count")
VERSION_FIELDS: tuple[str, ...] = ("source_version", "data_version")
BAR_KEY_FIELDS: tuple[str, ...] = ("instrument_id", "session_id", "bar_index")


@dataclass(frozen=True, slots=True)
class BarField:
    """One canonical bar field and its Python representation."""

    name: str
    python_type: type[Any]
    nullable: bool = False


CANONICAL_1MIN_BAR_FIELDS: tuple[BarField, ...] = (
    BarField("instrument_id", str),
    BarField("session_id", str),
    BarField("bar_index", int),
    BarField("bar_start_ts", datetime),
    BarField("bar_end_ts", datetime),
    BarField("event_ts", datetime),
    BarField("available_ts", datetime),
    BarField("open", Decimal),
    BarField("high", Decimal),
    BarField("low", Decimal),
    BarField("close", Decimal),
    BarField("volume", Decimal),
    BarField("vwap", Decimal),
    BarField("trade_count", int),
    BarField("bid", Decimal, nullable=True),
    BarField("ask", Decimal, nullable=True),
    BarField("spread", Decimal, nullable=True),
    BarField("source_version", str),
    BarField("data_version", str),
    BarField("quality_flags", tuple),
)

CANONICAL_1MIN_BAR_SCHEMA: Mapping[str, BarField] = {
    field.name: field for field in CANONICAL_1MIN_BAR_FIELDS
}


def canonical_bar_columns() -> tuple[str, ...]:
    """Return canonical columns in stable contract order."""
    return REQUIRED_BAR_FIELDS


def contract_alignment_errors() -> tuple[str, ...]:
    """Return schema/contract alignment problems, if any."""
    errors: list[str] = []
    missing = missing_contract_fields(OneMinuteBar, REQUIRED_BAR_FIELDS)
    if missing:
        errors.append(f"OneMinuteBar missing required fields: {', '.join(missing)}")

    contract_order = contract_field_names(OneMinuteBar)
    if contract_order != REQUIRED_BAR_FIELDS:
        errors.append(
            "OneMinuteBar field order differs from canonical schema: "
            f"{contract_order!r}"
        )
    return tuple(errors)


def missing_required_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Return canonical fields absent from a record mapping."""
    return tuple(field for field in REQUIRED_BAR_FIELDS if field not in record)


def _type_name(value_type: type[Any]) -> str:
    if value_type is Decimal:
        return "Decimal"
    if value_type is datetime:
        return "datetime"
    return value_type.__name__


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def field_type_errors(
    record: Mapping[str, Any],
    *,
    require_all: bool = True,
) -> tuple[str, ...]:
    """Return type-enforcement errors for a normalized canonical bar record."""
    errors: list[str] = []
    if require_all:
        errors.extend(f"{field} is missing" for field in missing_required_fields(record))

    for field in CANONICAL_1MIN_BAR_FIELDS:
        if field.name not in record:
            continue
        value = record[field.name]
        if value is None and field.nullable:
            continue
        if field.python_type is int:
            if not isinstance(value, int) or _is_bool(value):
                errors.append(f"{field.name} must be int")
            continue
        if field.python_type is tuple:
            if not isinstance(value, tuple) or not all(
                isinstance(item, str) for item in value
            ):
                errors.append(f"{field.name} must be tuple[str, ...]")
            continue
        if not isinstance(value, field.python_type):
            errors.append(
                f"{field.name} must be {_type_name(field.python_type)}"
            )
    return tuple(errors)
