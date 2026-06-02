"""Fixture-level canonical bar construction helpers."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.data.bar_schema import (
    DECIMAL_FIELDS,
    INT_FIELDS,
    OPTIONAL_DECIMAL_FIELDS,
    TIMESTAMP_FIELDS,
)
from alpha_system.data.validation import BarValidationConfig, require_valid_bars


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        parsed = datetime.fromisoformat(text)
    else:
        msg = f"{value!r} is not a timestamp"
        raise TypeError(msg)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_decimal(value: Any, *, nullable: bool) -> Decimal | None:
    if value is None:
        if nullable:
            return None
        msg = "required decimal value is missing"
        raise ValueError(msg)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text == "" and nullable:
            return None
        return Decimal(text)
    return Decimal(str(value))


def _parse_int(value: Any) -> int:
    if isinstance(value, bool):
        msg = f"{value!r} is not an int"
        raise TypeError(msg)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value.strip())
    return int(value)


def _parse_quality_flags(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()
        return tuple(part.strip() for part in text.split("|") if part.strip())
    return (str(value),)


def normalize_bar_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one fixture-like mapping into canonical Python scalar types."""
    normalized = dict(record)
    for field in TIMESTAMP_FIELDS:
        if field in normalized:
            normalized[field] = _parse_timestamp(normalized[field])
    for field in DECIMAL_FIELDS:
        if field in normalized:
            normalized[field] = _parse_decimal(
                normalized[field],
                nullable=field in OPTIONAL_DECIMAL_FIELDS,
            )
    for field in INT_FIELDS:
        if field in normalized:
            normalized[field] = _parse_int(normalized[field])
    if "quality_flags" in normalized:
        normalized["quality_flags"] = _parse_quality_flags(normalized["quality_flags"])
    return normalized


def normalize_bar_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    validation_config: BarValidationConfig | None = None,
    validate: bool = True,
) -> tuple[dict[str, Any], ...]:
    """Normalize fixture rows and optionally run canonical validation."""
    normalized = tuple(normalize_bar_record(row) for row in rows)
    if validate:
        require_valid_bars(
            normalized,
            config=validation_config or BarValidationConfig(),
        )
    return normalized


def load_csv_bar_fixture(
    path: str | Path,
    *,
    validation_config: BarValidationConfig | None = None,
    validate: bool = True,
) -> tuple[dict[str, Any], ...]:
    """Load a tiny documented CSV fixture into normalized canonical rows."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    return normalize_bar_rows(
        rows,
        validation_config=validation_config,
        validate=validate,
    )
