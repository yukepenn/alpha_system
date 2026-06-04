"""Root-level futures instrument records and contract-economics anchors.

DATA-P05 owns the futures instrument master. This module is local-only: it
performs no provider calls, opens no broker/account surface, and selects no
current or front-month contract.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alpha_system.data.foundation.sources import DataFoundationValidationError

INSTRUMENT_MASTER_SCHEMA = "alpha_system.instrument_master.v1"
INSTRUMENT_MASTER_ANCHOR_STATUS = "to_be_verified_economic_anchor"
INSTRUMENT_MASTER_CERTIFICATION_STATUS = "not_production_certified"
INSTRUMENT_MASTER_SOURCE_ID = "dsrc_campaign_goal_contract_economics"

REQUIRED_INSTRUMENT_MASTER_FIELDS: tuple[str, ...] = (
    "root_symbol",
    "ib_symbol",
    "exchange",
    "currency",
    "asset_class",
    "sec_type",
    "point_value",
    "tick_size",
    "tick_value",
    "multiplier",
    "timezone",
    "session_template_id",
    "roll_policy_id",
    "source",
    "source_retrieved_at",
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve(strict=False).parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent.resolve(strict=False)
    return Path.cwd().resolve(strict=False)


DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG = (
    _repo_root() / "configs" / "data" / "futures_instrument_master.json"
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _require_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be an exact decimal value"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            msg = f"{field_name} must be an exact decimal value"
            raise DataFoundationValidationError(msg)
        try:
            decimal_value = Decimal(raw)
        except InvalidOperation as exc:
            msg = f"{field_name} must be an exact decimal value"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = f"{field_name} must be an exact decimal value"
        raise DataFoundationValidationError(msg)

    if not decimal_value.is_finite():
        msg = f"{field_name} must be a finite decimal value"
        raise DataFoundationValidationError(msg)
    return decimal_value


def _require_positive_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _require_decimal(value, field_name)
    if decimal_value <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return decimal_value


def _require_explicit_timezone(value: object) -> str:
    timezone_id = _require_text(value, "timezone")
    token = timezone_id.lower()
    if token in {"local", "system", "default", "auto", "implicit"}:
        msg = "timezone must be an explicit IANA timezone, never implicit local time"
        raise DataFoundationValidationError(msg)
    if "/" not in timezone_id and timezone_id != "UTC":
        msg = "timezone must be an explicit IANA timezone such as America/Chicago"
        raise DataFoundationValidationError(msg)
    try:
        ZoneInfo(timezone_id)
    except ZoneInfoNotFoundError as exc:
        msg = f"timezone {timezone_id!r} is not available as an IANA timezone"
        raise DataFoundationValidationError(msg) from exc
    return timezone_id


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        msg = f"{field_name} must be a timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return value


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _require_aware_datetime(value, field_name)
    raw = _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
        raise DataFoundationValidationError(msg) from exc
    return _require_aware_datetime(parsed, field_name)


def _normalize_root_symbol(value: object) -> str:
    root_symbol = _require_text(value, "root_symbol").upper()
    if not root_symbol.isalnum():
        msg = "root_symbol must be alphanumeric"
        raise DataFoundationValidationError(msg)
    return root_symbol


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


@dataclass(frozen=True, slots=True)
class InstrumentMasterRecord:
    """Validated root-level futures instrument definition.

    The record stores economics for a futures root only. It does not carry dated
    contract identity, ``trading_class``, ``con_id``, current-contract selection,
    or tradability state.
    """

    root_symbol: str
    ib_symbol: str
    exchange: str
    currency: str
    asset_class: str
    sec_type: str
    point_value: Decimal
    tick_size: Decimal
    tick_value: Decimal
    multiplier: Decimal
    timezone: str
    session_template_id: str
    roll_policy_id: str
    source: str
    source_retrieved_at: datetime

    def __post_init__(self) -> None:
        root_symbol = _normalize_root_symbol(self.root_symbol)
        ib_symbol = _require_text(self.ib_symbol, "ib_symbol").upper()
        exchange = _require_text(self.exchange, "exchange").upper()
        currency = _require_text(self.currency, "currency").upper()
        asset_class = _normalize_id(
            _require_text(self.asset_class, "asset_class").lower(),
            "asset_class",
        )
        sec_type = _require_text(self.sec_type, "sec_type").upper()
        point_value = _require_positive_decimal(self.point_value, "point_value")
        tick_size = _require_positive_decimal(self.tick_size, "tick_size")
        tick_value = _require_positive_decimal(self.tick_value, "tick_value")
        multiplier = _require_positive_decimal(self.multiplier, "multiplier")
        timezone_id = _require_explicit_timezone(self.timezone)
        session_template_id = _normalize_id(self.session_template_id, "session_template_id")
        roll_policy_id = _normalize_id(self.roll_policy_id, "roll_policy_id")
        source = _require_text(self.source, "source")
        source_retrieved_at = _require_aware_datetime(
            self.source_retrieved_at,
            "source_retrieved_at",
        )

        if not source.startswith("dsrc_"):
            msg = "source must be a DataSourceProfile-style source identifier with dsrc_ prefix"
            raise DataFoundationValidationError(msg)
        if sec_type != "FUT":
            msg = "sec_type must be FUT for futures instrument-master records"
            raise DataFoundationValidationError(msg)
        expected_tick_value = tick_size * point_value
        if tick_value != expected_tick_value:
            msg = (
                "tick_value must equal tick_size * point_value exactly; "
                f"{root_symbol} has {tick_value} vs {expected_tick_value}"
            )
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "ib_symbol", ib_symbol)
        object.__setattr__(self, "exchange", exchange)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "asset_class", asset_class)
        object.__setattr__(self, "sec_type", sec_type)
        object.__setattr__(self, "point_value", point_value)
        object.__setattr__(self, "tick_size", tick_size)
        object.__setattr__(self, "tick_value", tick_value)
        object.__setattr__(self, "multiplier", multiplier)
        object.__setattr__(self, "timezone", timezone_id)
        object.__setattr__(self, "session_template_id", session_template_id)
        object.__setattr__(self, "roll_policy_id", roll_policy_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "source_retrieved_at", source_retrieved_at)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "InstrumentMasterRecord":
        """Build a record from config data and fail closed on missing fields."""

        missing = tuple(
            field for field in REQUIRED_INSTRUMENT_MASTER_FIELDS if field not in values
        )
        if missing:
            msg = "InstrumentMasterRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            ib_symbol=_require_text(values["ib_symbol"], "ib_symbol"),
            exchange=_require_text(values["exchange"], "exchange"),
            currency=_require_text(values["currency"], "currency"),
            asset_class=_require_text(values["asset_class"], "asset_class"),
            sec_type=_require_text(values["sec_type"], "sec_type"),
            point_value=_require_decimal(values["point_value"], "point_value"),
            tick_size=_require_decimal(values["tick_size"], "tick_size"),
            tick_value=_require_decimal(values["tick_value"], "tick_value"),
            multiplier=_require_decimal(values["multiplier"], "multiplier"),
            timezone=_require_text(values["timezone"], "timezone"),
            session_template_id=_require_text(
                values["session_template_id"],
                "session_template_id",
            ),
            roll_policy_id=_require_text(values["roll_policy_id"], "roll_policy_id"),
            source=_require_text(values["source"], "source"),
            source_retrieved_at=_parse_aware_datetime(
                values["source_retrieved_at"],
                "source_retrieved_at",
            ),
        )

    @property
    def computed_tick_value(self) -> Decimal:
        """Return the exact ``tick_size * point_value`` economic invariant."""

        return self.tick_size * self.point_value

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for audits and docs generation."""

        return MappingProxyType(
            {
                "root_symbol": self.root_symbol,
                "ib_symbol": self.ib_symbol,
                "exchange": self.exchange,
                "currency": self.currency,
                "asset_class": self.asset_class,
                "sec_type": self.sec_type,
                "point_value": str(self.point_value),
                "tick_size": str(self.tick_size),
                "tick_value": str(self.tick_value),
                "multiplier": str(self.multiplier),
                "timezone": self.timezone,
                "session_template_id": self.session_template_id,
                "roll_policy_id": self.roll_policy_id,
                "source": self.source,
                "source_retrieved_at": self.source_retrieved_at.isoformat(),
            }
        )


def _load_config_payload(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_float=Decimal,
            parse_int=Decimal,
        )
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"instrument master config cannot be loaded from {path}"
        raise DataFoundationValidationError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = "instrument master config must be a JSON object"
        raise DataFoundationValidationError(msg)
    return payload


def load_futures_instrument_master_records(
    path: str | Path | None = None,
) -> tuple[InstrumentMasterRecord, ...]:
    """Load the DATA-P05 futures root anchors from declarative config."""

    config_path = DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG if path is None else Path(path)
    payload = _load_config_payload(config_path)

    if payload.get("schema") != INSTRUMENT_MASTER_SCHEMA:
        msg = f"instrument master config schema must be {INSTRUMENT_MASTER_SCHEMA!r}"
        raise DataFoundationValidationError(msg)
    if payload.get("anchor_status") != INSTRUMENT_MASTER_ANCHOR_STATUS:
        msg = "instrument master anchors must be marked to-be-verified"
        raise DataFoundationValidationError(msg)
    if payload.get("certification_status") != INSTRUMENT_MASTER_CERTIFICATION_STATUS:
        msg = "instrument master anchors must be marked not production-certified"
        raise DataFoundationValidationError(msg)

    raw_records = payload.get("records")
    if isinstance(raw_records, str) or not isinstance(raw_records, list) or not raw_records:
        msg = "instrument master config records must be a non-empty list"
        raise DataFoundationValidationError(msg)

    records = tuple(
        InstrumentMasterRecord.from_mapping(record)
        for record in raw_records
        if isinstance(record, Mapping)
    )
    if len(records) != len(raw_records):
        msg = "instrument master config records must be JSON objects"
        raise DataFoundationValidationError(msg)

    roots = [record.root_symbol for record in records]
    duplicate_roots = sorted({root for root in roots if roots.count(root) > 1})
    if duplicate_roots:
        msg = "instrument master config contains duplicate roots: " + ", ".join(duplicate_roots)
        raise DataFoundationValidationError(msg)

    return records


def load_futures_instrument_master_by_root(
    path: str | Path | None = None,
) -> Mapping[str, InstrumentMasterRecord]:
    """Load DATA-P05 futures root anchors keyed by root symbol."""

    records = load_futures_instrument_master_records(path)
    return MappingProxyType({record.root_symbol: record for record in records})


class FuturesContractRecord:
    """DATA-P05 placeholder for a dated futures contract record."""


class ContractDetailsSnapshot:
    """DATA-P06 placeholder for provider contract-detail metadata."""


__all__ = [
    "ContractDetailsSnapshot",
    "DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG",
    "FuturesContractRecord",
    "INSTRUMENT_MASTER_ANCHOR_STATUS",
    "INSTRUMENT_MASTER_CERTIFICATION_STATUS",
    "INSTRUMENT_MASTER_SCHEMA",
    "INSTRUMENT_MASTER_SOURCE_ID",
    "InstrumentMasterRecord",
    "REQUIRED_INSTRUMENT_MASTER_FIELDS",
    "load_futures_instrument_master_by_root",
    "load_futures_instrument_master_records",
]
