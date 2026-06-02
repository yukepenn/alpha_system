"""Small helpers for inspecting dataclass-based schema contracts."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


def contract_field_names(contract_type: type[Any]) -> tuple[str, ...]:
    """Return declared dataclass field names in source order."""
    if not is_dataclass(contract_type):
        msg = f"{contract_type!r} is not a dataclass contract"
        raise TypeError(msg)
    return tuple(field.name for field in fields(contract_type))


def missing_contract_fields(
    contract_type: type[Any],
    required_fields: tuple[str, ...],
) -> tuple[str, ...]:
    """Return required field names absent from a dataclass contract."""
    present = set(contract_field_names(contract_type))
    return tuple(field for field in required_fields if field not in present)
