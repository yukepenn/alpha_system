"""Stable instrument identity helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.core.instrument_master import (
    InstrumentMasterCatalog,
    InstrumentMasterError,
    InstrumentMasterRecord,
)


STABLE_INSTRUMENT_IDENTITY_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "timezone",
    "multiplier",
    "corporate_action_policy",
)


def normalize_instrument_id(value: Any) -> str:
    """Return a non-empty stable internal instrument identity."""
    if not isinstance(value, str) or not value.strip():
        raise InstrumentMasterError("instrument_id must be a non-empty string")
    return value.strip()


def instrument_identity_payload(
    record: InstrumentMasterRecord | Mapping[str, Any],
) -> dict[str, Any]:
    """Return the stable identity fields used for deterministic hashes."""
    payload = _record_mapping(record)
    missing = tuple(field for field in STABLE_INSTRUMENT_IDENTITY_FIELDS if field not in payload)
    if missing:
        raise InstrumentMasterError(
            f"instrument identity payload missing fields: {', '.join(missing)}"
        )
    identity = {field: payload[field] for field in STABLE_INSTRUMENT_IDENTITY_FIELDS}
    identity["instrument_id"] = normalize_instrument_id(identity["instrument_id"])
    return identity


def instrument_identity_hash(record: InstrumentMasterRecord | Mapping[str, Any]) -> str:
    """Hash identity metadata without treating raw symbol as sufficient identity."""
    return hash_config(instrument_identity_payload(record))


def resolve_symbol_to_instrument_id(
    symbol: str,
    instruments: InstrumentMasterCatalog | Iterable[InstrumentMasterRecord | Mapping[str, Any]],
    *,
    active_date: Any = None,
    exchange: str | None = None,
    currency: str | None = None,
) -> str:
    """Resolve a raw symbol to a stable ``instrument_id`` only when unambiguous."""
    catalog = instruments if isinstance(instruments, InstrumentMasterCatalog) else InstrumentMasterCatalog(tuple(instruments))
    return catalog.resolve_symbol(
        symbol,
        active_date=active_date,
        exchange=exchange,
        currency=currency,
    )


def assert_instrument_ids(values: Iterable[Any]) -> tuple[str, ...]:
    """Validate a sequence of stable identities."""
    return tuple(normalize_instrument_id(value) for value in values)


def _record_mapping(record: InstrumentMasterRecord | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(record, InstrumentMasterRecord):
        return record.to_dict()
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    if isinstance(record, Mapping):
        return record
    raise InstrumentMasterError("instrument identity requires an instrument record mapping")
