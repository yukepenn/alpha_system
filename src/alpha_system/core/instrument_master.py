"""Instrument master records and active-date lookup utilities."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alpha_system.core.enums import AssetClass, CorporateActionPolicy
from alpha_system.data.contracts import InstrumentMaster


REQUIRED_INSTRUMENT_MASTER_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "symbol",
    "asset_class",
    "exchange",
    "currency",
    "timezone",
    "tick_size",
    "lot_size",
    "multiplier",
    "start_date",
    "end_date",
    "corporate_action_policy",
    "metadata",
)


class InstrumentMasterError(ValueError):
    """Raised when instrument metadata is incomplete or ambiguous."""


@dataclass(frozen=True, slots=True, kw_only=True)
class InstrumentMasterRecord:
    """Validated instrument metadata with ``instrument_id`` as stable identity."""

    instrument_id: str
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str
    timezone: str
    tick_size: Decimal
    lot_size: Decimal
    multiplier: Decimal
    start_date: date
    end_date: date | None
    corporate_action_policy: CorporateActionPolicy
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument_id", _text(self.instrument_id, "instrument_id"))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol"))
        object.__setattr__(self, "asset_class", _asset_class(self.asset_class))
        object.__setattr__(self, "exchange", _text(self.exchange, "exchange"))
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        timezone = _text(self.timezone, "timezone")
        _validate_timezone(timezone)
        object.__setattr__(self, "timezone", timezone)
        object.__setattr__(self, "tick_size", _positive_decimal(self.tick_size, "tick_size"))
        object.__setattr__(self, "lot_size", _positive_decimal(self.lot_size, "lot_size"))
        object.__setattr__(self, "multiplier", _positive_decimal(self.multiplier, "multiplier"))
        start_date = _date_value(self.start_date, "start_date")
        end_date = _optional_date(self.end_date, "end_date")
        if end_date is not None and end_date < start_date:
            raise InstrumentMasterError("end_date must be on or after start_date")
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "end_date", end_date)
        object.__setattr__(
            self,
            "corporate_action_policy",
            _corporate_action_policy(self.corporate_action_policy),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "InstrumentMasterRecord":
        if not isinstance(payload, Mapping):
            raise InstrumentMasterError("instrument master record must be a mapping")
        missing = missing_instrument_fields(payload)
        if missing:
            raise InstrumentMasterError(
                f"instrument master record missing required fields: {', '.join(missing)}"
            )
        return cls(
            instrument_id=payload["instrument_id"],
            symbol=payload["symbol"],
            asset_class=payload["asset_class"],
            exchange=payload["exchange"],
            currency=payload["currency"],
            timezone=payload["timezone"],
            tick_size=payload["tick_size"],
            lot_size=payload["lot_size"],
            multiplier=payload["multiplier"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            corporate_action_policy=payload["corporate_action_policy"],
            metadata=_mapping(payload["metadata"], "metadata"),
        )

    def active_on(self, active_date: date | str) -> bool:
        query_date = _date_value(active_date, "active_date")
        return self.start_date <= query_date and (
            self.end_date is None or query_date <= self.end_date
        )

    def to_contract(self) -> InstrumentMaster:
        return InstrumentMaster(
            instrument_id=self.instrument_id,
            symbol=self.symbol,
            asset_class=self.asset_class,
            exchange=self.exchange,
            currency=self.currency,
            timezone=self.timezone,
            tick_size=self.tick_size,
            lot_size=self.lot_size,
            multiplier=self.multiplier,
            start_date=self.start_date,
            end_date=self.end_date,
            corporate_action_policy=self.corporate_action_policy,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            field: _json_ready(getattr(self, field))
            for field in REQUIRED_INSTRUMENT_MASTER_FIELDS
        }


@dataclass(frozen=True, slots=True)
class InstrumentMasterCatalog:
    """In-memory instrument master keyed by stable ``instrument_id``."""

    records: tuple[InstrumentMasterRecord, ...]

    def __post_init__(self) -> None:
        records = tuple(_record(record) for record in self.records)
        seen: set[str] = set()
        for record in records:
            if record.instrument_id in seen:
                raise InstrumentMasterError(f"duplicate instrument_id: {record.instrument_id}")
            seen.add(record.instrument_id)
        object.__setattr__(self, "records", tuple(sorted(records, key=lambda item: item.instrument_id)))

    @classmethod
    def from_mappings(cls, payloads: Iterable[Mapping[str, Any]]) -> "InstrumentMasterCatalog":
        return cls(tuple(InstrumentMasterRecord.from_mapping(payload) for payload in payloads))

    def by_instrument_id(self) -> dict[str, InstrumentMasterRecord]:
        return {record.instrument_id: record for record in self.records}

    def get(self, instrument_id: str) -> InstrumentMasterRecord:
        normalized = _text(instrument_id, "instrument_id")
        try:
            return self.by_instrument_id()[normalized]
        except KeyError as exc:
            raise InstrumentMasterError(f"unknown instrument_id: {normalized}") from exc

    def active_records(self, active_date: date | str) -> tuple[InstrumentMasterRecord, ...]:
        return tuple(record for record in self.records if record.active_on(active_date))

    def resolve_symbol(
        self,
        symbol: str,
        *,
        active_date: date | str | None = None,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> str:
        """Resolve a symbol to ``instrument_id`` when metadata makes it unique."""
        normalized_symbol = _text(symbol, "symbol")
        candidates = [record for record in self.records if record.symbol == normalized_symbol]
        if active_date is not None:
            candidates = [record for record in candidates if record.active_on(active_date)]
        if exchange is not None:
            normalized_exchange = _text(exchange, "exchange")
            candidates = [record for record in candidates if record.exchange == normalized_exchange]
        if currency is not None:
            normalized_currency = _text(currency, "currency").upper()
            candidates = [record for record in candidates if record.currency == normalized_currency]
        if not candidates:
            raise InstrumentMasterError(f"symbol {normalized_symbol!r} did not resolve to an instrument_id")
        if len(candidates) > 1:
            ids = ", ".join(record.instrument_id for record in candidates)
            raise InstrumentMasterError(
                f"symbol {normalized_symbol!r} is ambiguous; matching instrument_ids: {ids}"
            )
        return candidates[0].instrument_id


def missing_instrument_fields(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(field for field in REQUIRED_INSTRUMENT_MASTER_FIELDS if field not in payload)


def instrument_master_field_coverage(
    record: InstrumentMasterRecord | Mapping[str, Any],
) -> dict[str, bool]:
    payload = record.to_dict() if isinstance(record, InstrumentMasterRecord) else record
    return {field: field in payload for field in REQUIRED_INSTRUMENT_MASTER_FIELDS}


def load_instrument_master(path: str | Path) -> InstrumentMasterCatalog:
    """Load a small JSON instrument master config."""
    config_path = Path(path).expanduser().resolve(strict=False)
    if config_path.suffix.lower() != ".json":
        raise InstrumentMasterError(f"instrument master config must be JSON: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    records = payload.get("instruments", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(records, list | tuple):
        raise InstrumentMasterError("instrument master config must contain an instruments list")
    return InstrumentMasterCatalog.from_mappings(records)


def _record(value: InstrumentMasterRecord | Mapping[str, Any]) -> InstrumentMasterRecord:
    if isinstance(value, InstrumentMasterRecord):
        return value
    return InstrumentMasterRecord.from_mapping(value)


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InstrumentMasterError(f"{field_name} must be a mapping")
    return value


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InstrumentMasterError(f"{field_name} must be a non-empty string")
    return value.strip()


def _asset_class(value: Any) -> AssetClass:
    if isinstance(value, AssetClass):
        return value
    try:
        return AssetClass(str(value))
    except ValueError as exc:
        raise InstrumentMasterError(f"unsupported asset_class: {value}") from exc


def _corporate_action_policy(value: Any) -> CorporateActionPolicy:
    if isinstance(value, CorporateActionPolicy):
        return value
    try:
        return CorporateActionPolicy(str(value))
    except ValueError as exc:
        raise InstrumentMasterError(f"unsupported corporate_action_policy: {value}") from exc


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InstrumentMasterError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InstrumentMasterError(f"{field_name} must be numeric") from exc


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise InstrumentMasterError(f"{field_name} must be positive")
    return active


def _date_value(value: date | str, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise InstrumentMasterError(f"{field_name} must be an ISO date") from exc
    raise InstrumentMasterError(f"{field_name} must be a date or ISO date string")


def _optional_date(value: date | str | None, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    return _date_value(value, field_name)


def _validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise InstrumentMasterError(f"timezone is not recognized: {value}") from exc


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, AssetClass | CorporateActionPolicy):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value
