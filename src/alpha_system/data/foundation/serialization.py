"""JSON-stable value helpers for data-foundation summary and manifest emitters."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.sources import DataFoundationValidationError


def json_ready_base(value: object) -> object:
    """Return the minimal JSON-stable form for summary and manifest emitters."""

    if isinstance(value, Mapping | MappingProxyType):
        return {str(key): json_ready_base(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [json_ready_base(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def json_ready(value: object) -> object:
    """Return the fuller JSON-stable form for manifests and materialization."""

    if isinstance(value, Mapping | MappingProxyType):
        return {str(key): json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [json_ready(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


__all__ = ["json_ready", "json_ready_base"]
