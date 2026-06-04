"""Root-level futures instrument records and contract-economics anchors.

DATA-P05 owns the futures instrument master. This module is local-only: it
performs no provider calls, opens no broker/account surface, and selects no
current or front-month contract.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alpha_system.data.foundation.ibkr import IBKRClientIdPolicy
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

REQUIRED_FUTURES_CONTRACT_FIELDS: tuple[str, ...] = (
    "contract_id",
    "root_symbol",
    "contract_month",
    "ib_symbol",
    "trading_class",
    "con_id",
    "last_trade_date_or_contract_month",
    "expiration",
    "multiplier",
    "exchange",
    "currency",
    "include_expired_support_status",
)

REQUIRED_CONTRACT_DETAILS_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "snapshot_id",
    "contract_id",
    "raw_details_ref",
    "normalized_fields",
    "retrieved_at",
    "client_id",
    "source",
    "hash",
)

_FUTURES_MONTH_CODE_PATTERN = re.compile(r"^[FGHJKMNQUVXZ]\d{1,2}$")
_YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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


def _require_reference(value: object, field_name: str) -> str:
    reference = _require_text(value, field_name)
    if "\n" in reference or "\r" in reference:
        msg = f"{field_name} must be a single-line reference"
        raise DataFoundationValidationError(msg)
    if reference[0] in {"{", "["}:
        msg = f"{field_name} must reference a local-only object or synthetic fixture"
        raise DataFoundationValidationError(msg)
    return reference


def _require_optional_reference(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_reference(value, field_name)


def _parse_date(value: object, field_name: str) -> date:
    if isinstance(value, datetime):
        msg = f"{field_name} must be a calendar date, not a datetime"
        raise DataFoundationValidationError(msg)
    if isinstance(value, date):
        return value
    raw = _require_text(value, field_name)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 date"
        raise DataFoundationValidationError(msg) from exc


def _normalize_contract_month(value: object) -> str:
    contract_month = _require_text(value, "contract_month").upper()
    if _YEAR_MONTH_PATTERN.fullmatch(contract_month):
        year, month = contract_month.split("-")
        try:
            date(int(year), int(month), 1)
        except ValueError as exc:
            msg = "contract_month must contain a valid month"
            raise DataFoundationValidationError(msg) from exc
        return contract_month
    if _FUTURES_MONTH_CODE_PATTERN.fullmatch(contract_month):
        return contract_month
    msg = "contract_month must use YYYY-MM or futures month-code style such as H5"
    raise DataFoundationValidationError(msg)


def _normalize_optional_con_id(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        msg = "con_id must be a positive integer or None when not yet discovered"
        raise DataFoundationValidationError(msg)
    if isinstance(value, int):
        con_id = value
    elif isinstance(value, str) and value.strip().isdigit():
        con_id = int(value.strip())
    else:
        msg = "con_id must be a positive integer or None when not yet discovered"
        raise DataFoundationValidationError(msg)
    if con_id <= 0:
        msg = "con_id must be positive when discovered"
        raise DataFoundationValidationError(msg)
    return con_id


def _require_bool_or_none(value: object, field_name: str) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    msg = f"{field_name} must be true, false, or None"
    raise DataFoundationValidationError(msg)


def _freeze_contract_details_value(value: object, field_name: str) -> object:
    if isinstance(value, Mapping):
        if not value:
            msg = f"{field_name} must not be an empty mapping"
            raise DataFoundationValidationError(msg)
        return MappingProxyType(
            {
                _require_text(key, f"{field_name} key"): _freeze_contract_details_value(
                    nested_value,
                    f"{field_name}.{key}",
                )
                for key, nested_value in sorted(value.items(), key=lambda item: str(item[0]))
            }
        )
    if isinstance(value, tuple | list):
        return tuple(_freeze_contract_details_value(item, f"{field_name}[]") for item in value)
    if isinstance(value, Decimal):
        return str(value)
    if value is None or isinstance(value, bool | int | str):
        return value
    msg = f"{field_name} must contain only JSON-stable synthetic contract-detail values"
    raise DataFoundationValidationError(msg)


def _normalize_normalized_fields(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "normalized_fields must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    return _freeze_contract_details_value(value, "normalized_fields")


def _canonical_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _canonical_json_value(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_canonical_json_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, StrEnum):
        return str(value)
    if value is None or isinstance(value, bool | int | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _canonical_json_value(payload),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_sha256_hash(value: object) -> str | None:
    if value is None:
        return None
    raw = _require_text(value, "hash").lower()
    if not _SHA256_HEX_PATTERN.fullmatch(raw):
        msg = "hash must be a lowercase sha256 hex digest"
        raise DataFoundationValidationError(msg)
    return raw


def _validate_snapshot_client_id(value: object) -> int:
    return IBKRClientIdPolicy.default().validate_client_id(value)


class IncludeExpiredSupportStatus(StrEnum):
    """Discovered status for whether IBKR includeExpired worked for a request."""

    NOT_CHECKED = "not_checked"
    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


def _normalize_include_expired_status(value: object) -> IncludeExpiredSupportStatus:
    if isinstance(value, IncludeExpiredSupportStatus):
        return value
    raw = _require_text(value, "include_expired_support_status").lower()
    try:
        return IncludeExpiredSupportStatus(raw)
    except ValueError as exc:
        msg = (
            "include_expired_support_status must be one of "
            "not_checked, unknown, supported, unsupported"
        )
        raise DataFoundationValidationError(msg) from exc


def compute_contract_details_snapshot_hash(
    *,
    contract_id: object,
    raw_details_ref: object,
    normalized_fields: object,
    retrieved_at: object,
    client_id: object,
    source: object,
) -> str:
    """Compute the content hash for an immutable contract-details snapshot."""

    normalized_retrieved_at = _parse_aware_datetime(retrieved_at, "retrieved_at")
    return _stable_hash(
        {
            "schema": "alpha_system.contract_details_snapshot.v1",
            "contract_id": _normalize_id(contract_id, "contract_id"),
            "raw_details_ref": _require_reference(raw_details_ref, "raw_details_ref"),
            "normalized_fields": _normalize_normalized_fields(normalized_fields),
            "retrieved_at": normalized_retrieved_at,
            "client_id": _validate_snapshot_client_id(client_id),
            "source": _require_text(source, "source"),
        }
    )


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
    def from_mapping(cls, values: Mapping[str, object]) -> InstrumentMasterRecord:
        """Build a record from config data and fail closed on missing fields."""

        missing = tuple(field for field in REQUIRED_INSTRUMENT_MASTER_FIELDS if field not in values)
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


@dataclass(frozen=True, slots=True)
class FuturesContractRecord:
    """Validated dated futures contract identity.

    The record addresses one dated futures contract. It reconciles root-level
    economics against ``InstrumentMasterRecord`` and records includeExpired
    support only as a discovered status, never as assumed full availability.
    """

    contract_id: str
    root_symbol: str
    contract_month: str
    ib_symbol: str
    trading_class: str
    con_id: int | None
    last_trade_date_or_contract_month: str
    expiration: date
    multiplier: Decimal
    exchange: str
    currency: str
    include_expired_support_status: IncludeExpiredSupportStatus = (
        IncludeExpiredSupportStatus.NOT_CHECKED
    )

    def __post_init__(self) -> None:
        contract_id = _normalize_id(self.contract_id, "contract_id")
        root_symbol = _normalize_root_symbol(self.root_symbol)
        masters = load_futures_instrument_master_by_root()
        master = masters.get(root_symbol)
        if master is None:
            msg = f"root_symbol {root_symbol!r} is not in the futures instrument master"
            raise DataFoundationValidationError(msg)

        contract_month = _normalize_contract_month(self.contract_month)
        ib_symbol = _require_text(self.ib_symbol, "ib_symbol").upper()
        trading_class = _require_text(self.trading_class, "trading_class").upper()
        con_id = _normalize_optional_con_id(self.con_id)
        last_trade_date_or_contract_month = _require_text(
            self.last_trade_date_or_contract_month,
            "last_trade_date_or_contract_month",
        )
        expiration = _parse_date(self.expiration, "expiration")
        multiplier = _require_positive_decimal(self.multiplier, "multiplier")
        exchange = _require_text(self.exchange, "exchange").upper()
        currency = _require_text(self.currency, "currency").upper()
        include_expired_support_status = _normalize_include_expired_status(
            self.include_expired_support_status
        )

        if ib_symbol != master.ib_symbol:
            msg = f"ib_symbol {ib_symbol!r} does not reconcile with {root_symbol} instrument master"
            raise DataFoundationValidationError(msg)
        if multiplier != master.multiplier:
            msg = (
                f"multiplier {multiplier} does not reconcile with "
                f"{root_symbol} instrument master multiplier {master.multiplier}"
            )
            raise DataFoundationValidationError(msg)
        if exchange != master.exchange:
            msg = f"exchange {exchange!r} does not reconcile with {root_symbol} instrument master"
            raise DataFoundationValidationError(msg)
        if currency != master.currency:
            msg = f"currency {currency!r} does not reconcile with {root_symbol} instrument master"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "contract_month", contract_month)
        object.__setattr__(self, "ib_symbol", ib_symbol)
        object.__setattr__(self, "trading_class", trading_class)
        object.__setattr__(self, "con_id", con_id)
        object.__setattr__(
            self,
            "last_trade_date_or_contract_month",
            last_trade_date_or_contract_month,
        )
        object.__setattr__(self, "expiration", expiration)
        object.__setattr__(self, "multiplier", multiplier)
        object.__setattr__(self, "exchange", exchange)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(
            self,
            "include_expired_support_status",
            include_expired_support_status,
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> FuturesContractRecord:
        """Build a dated contract from declarative data and fail closed."""

        missing = tuple(field for field in REQUIRED_FUTURES_CONTRACT_FIELDS if field not in values)
        if missing:
            msg = "FuturesContractRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            contract_id=_require_text(values["contract_id"], "contract_id"),
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            contract_month=_require_text(values["contract_month"], "contract_month"),
            ib_symbol=_require_text(values["ib_symbol"], "ib_symbol"),
            trading_class=_require_text(values["trading_class"], "trading_class"),
            con_id=values["con_id"],
            last_trade_date_or_contract_month=_require_text(
                values["last_trade_date_or_contract_month"],
                "last_trade_date_or_contract_month",
            ),
            expiration=_parse_date(values["expiration"], "expiration"),
            multiplier=_require_decimal(values["multiplier"], "multiplier"),
            exchange=_require_text(values["exchange"], "exchange"),
            currency=_require_text(values["currency"], "currency"),
            include_expired_support_status=_normalize_include_expired_status(
                values["include_expired_support_status"]
            ),
        )

    def with_include_expired_support_status(
        self,
        status: IncludeExpiredSupportStatus | str,
    ) -> FuturesContractRecord:
        """Return a new record with a discovered includeExpired support status."""

        return FuturesContractRecord(
            contract_id=self.contract_id,
            root_symbol=self.root_symbol,
            contract_month=self.contract_month,
            ib_symbol=self.ib_symbol,
            trading_class=self.trading_class,
            con_id=self.con_id,
            last_trade_date_or_contract_month=self.last_trade_date_or_contract_month,
            expiration=self.expiration,
            multiplier=self.multiplier,
            exchange=self.exchange,
            currency=self.currency,
            include_expired_support_status=_normalize_include_expired_status(status),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for manifests and handoff audits."""

        return MappingProxyType(
            {
                "contract_id": self.contract_id,
                "root_symbol": self.root_symbol,
                "contract_month": self.contract_month,
                "ib_symbol": self.ib_symbol,
                "trading_class": self.trading_class,
                "con_id": self.con_id,
                "last_trade_date_or_contract_month": self.last_trade_date_or_contract_month,
                "expiration": self.expiration.isoformat(),
                "multiplier": str(self.multiplier),
                "exchange": self.exchange,
                "currency": self.currency,
                "include_expired_support_status": str(self.include_expired_support_status),
            }
        )


@dataclass(frozen=True, slots=True)
class ContractDetailsSnapshot:
    """Immutable, content-addressed snapshot of normalized contract details."""

    snapshot_id: str
    contract_id: str
    raw_details_ref: str
    normalized_fields: Mapping[str, object]
    retrieved_at: datetime
    client_id: int
    source: str
    hash: str | None = None

    def __post_init__(self) -> None:
        snapshot_id = _normalize_id(self.snapshot_id, "snapshot_id")
        contract_id = _normalize_id(self.contract_id, "contract_id")
        raw_details_ref = _require_reference(self.raw_details_ref, "raw_details_ref")
        normalized_fields = _normalize_normalized_fields(self.normalized_fields)
        retrieved_at = _parse_aware_datetime(self.retrieved_at, "retrieved_at")
        client_id = _validate_snapshot_client_id(self.client_id)
        source = _require_text(self.source, "source")
        computed_hash = compute_contract_details_snapshot_hash(
            contract_id=contract_id,
            raw_details_ref=raw_details_ref,
            normalized_fields=normalized_fields,
            retrieved_at=retrieved_at,
            client_id=client_id,
            source=source,
        )
        supplied_hash = _normalize_sha256_hash(self.hash)
        if supplied_hash is not None and supplied_hash != computed_hash:
            msg = "hash does not match the contract-details snapshot content"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "snapshot_id", snapshot_id)
        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "raw_details_ref", raw_details_ref)
        object.__setattr__(self, "normalized_fields", normalized_fields)
        object.__setattr__(self, "retrieved_at", retrieved_at)
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "hash", computed_hash)

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: str,
        contract_id: str,
        raw_details_ref: str,
        normalized_fields: Mapping[str, object],
        retrieved_at: datetime,
        client_id: int,
        source: str,
    ) -> ContractDetailsSnapshot:
        """Create a snapshot and compute its content hash."""

        return cls(
            snapshot_id=snapshot_id,
            contract_id=contract_id,
            raw_details_ref=raw_details_ref,
            normalized_fields=normalized_fields,
            retrieved_at=retrieved_at,
            client_id=client_id,
            source=source,
            hash=None,
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ContractDetailsSnapshot:
        """Build a snapshot from persisted data and validate its hash."""

        missing = tuple(
            field for field in REQUIRED_CONTRACT_DETAILS_SNAPSHOT_FIELDS if field not in values
        )
        if missing:
            msg = "ContractDetailsSnapshot missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            snapshot_id=_require_text(values["snapshot_id"], "snapshot_id"),
            contract_id=_require_text(values["contract_id"], "contract_id"),
            raw_details_ref=_require_text(values["raw_details_ref"], "raw_details_ref"),
            normalized_fields=_normalize_normalized_fields(values["normalized_fields"]),
            retrieved_at=_parse_aware_datetime(values["retrieved_at"], "retrieved_at"),
            client_id=_validate_snapshot_client_id(values["client_id"]),
            source=_require_text(values["source"], "source"),
            hash=_require_text(values["hash"], "hash"),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping with the validated content hash."""

        return MappingProxyType(
            {
                "snapshot_id": self.snapshot_id,
                "contract_id": self.contract_id,
                "raw_details_ref": self.raw_details_ref,
                "normalized_fields": self.normalized_fields,
                "retrieved_at": self.retrieved_at.isoformat(),
                "client_id": self.client_id,
                "source": self.source,
                "hash": self.hash,
            }
        )


@dataclass(frozen=True, slots=True)
class ContractDiscoveryRequest:
    """Declarative input for no-live-call contract discovery scaffolding."""

    root_symbol: str
    sec_type: str = "FUT"
    include_expired: bool | None = None
    client_id: int = 201
    source: str = "dsrc_synthetic_contract_discovery"

    def __post_init__(self) -> None:
        root_symbol = _normalize_root_symbol(self.root_symbol)
        masters = load_futures_instrument_master_by_root()
        if root_symbol not in masters:
            msg = f"root_symbol {root_symbol!r} is not in the futures instrument master"
            raise DataFoundationValidationError(msg)
        sec_type = _require_text(self.sec_type, "sec_type").upper()
        if sec_type != "FUT":
            msg = "contract discovery scaffold only accepts sec_type FUT"
            raise DataFoundationValidationError(msg)
        include_expired = _require_bool_or_none(self.include_expired, "include_expired")
        client_id = _validate_snapshot_client_id(self.client_id)
        source = _require_text(self.source, "source")

        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "sec_type", sec_type)
        object.__setattr__(self, "include_expired", include_expired)
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "source", source)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ContractDiscoveryRequest:
        """Build a discovery request from declarative synthetic inputs."""

        if "root_symbol" not in values:
            msg = "ContractDiscoveryRequest missing required field: root_symbol"
            raise DataFoundationValidationError(msg)
        return cls(
            root_symbol=_require_text(values["root_symbol"], "root_symbol"),
            sec_type=_require_text(values.get("sec_type", "FUT"), "sec_type"),
            include_expired=_require_bool_or_none(
                values.get("include_expired"),
                "include_expired",
            ),
            client_id=_validate_snapshot_client_id(values.get("client_id", 201)),
            source=_require_text(
                values.get("source", "dsrc_synthetic_contract_discovery"),
                "source",
            ),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return the request without adding provider or history-depth claims."""

        return MappingProxyType(
            {
                "root_symbol": self.root_symbol,
                "sec_type": self.sec_type,
                "include_expired": self.include_expired,
                "client_id": self.client_id,
                "source": self.source,
            }
        )


@dataclass(frozen=True, slots=True)
class ContractDiscoveryAvailabilityLogEntry:
    """Availability log entry emitted by the no-live-call discovery scaffold."""

    root_symbol: str
    sec_type: str
    include_expired_requested: bool | None
    include_expired_support_status: IncludeExpiredSupportStatus
    discovered_at: datetime
    source: str
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        root_symbol = _normalize_root_symbol(self.root_symbol)
        masters = load_futures_instrument_master_by_root()
        if root_symbol not in masters:
            msg = f"root_symbol {root_symbol!r} is not in the futures instrument master"
            raise DataFoundationValidationError(msg)
        sec_type = _require_text(self.sec_type, "sec_type").upper()
        if sec_type != "FUT":
            msg = "availability log entries only support sec_type FUT"
            raise DataFoundationValidationError(msg)
        include_expired_requested = _require_bool_or_none(
            self.include_expired_requested,
            "include_expired_requested",
        )
        include_expired_support_status = _normalize_include_expired_status(
            self.include_expired_support_status
        )
        discovered_at = _parse_aware_datetime(self.discovered_at, "discovered_at")
        source = _require_text(self.source, "source")
        evidence_ref = _require_optional_reference(self.evidence_ref, "evidence_ref")

        if include_expired_requested is not True and include_expired_support_status in {
            IncludeExpiredSupportStatus.SUPPORTED,
            IncludeExpiredSupportStatus.UNSUPPORTED,
        }:
            msg = "supported/unsupported includeExpired status requires include_expired=True"
            raise DataFoundationValidationError(msg)
        if (
            include_expired_support_status
            in {
                IncludeExpiredSupportStatus.SUPPORTED,
                IncludeExpiredSupportStatus.UNSUPPORTED,
            }
            and evidence_ref is None
        ):
            msg = "supported/unsupported includeExpired status requires evidence_ref"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "root_symbol", root_symbol)
        object.__setattr__(self, "sec_type", sec_type)
        object.__setattr__(self, "include_expired_requested", include_expired_requested)
        object.__setattr__(
            self,
            "include_expired_support_status",
            include_expired_support_status,
        )
        object.__setattr__(self, "discovered_at", discovered_at)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "evidence_ref", evidence_ref)

    def to_mapping(self) -> Mapping[str, object]:
        """Return an availability-only log entry with no history-depth field."""

        return MappingProxyType(
            {
                "root_symbol": self.root_symbol,
                "sec_type": self.sec_type,
                "include_expired_requested": self.include_expired_requested,
                "include_expired_support_status": str(self.include_expired_support_status),
                "discovered_at": self.discovered_at.isoformat(),
                "source": self.source,
                "evidence_ref": self.evidence_ref,
            }
        )


@dataclass(frozen=True, slots=True)
class ContractDiscoveryResult:
    """Pure discovery scaffold result tying records to an availability log."""

    request: ContractDiscoveryRequest
    availability_log_entry: ContractDiscoveryAvailabilityLogEntry
    contract_record: FuturesContractRecord | None = None
    snapshot: ContractDetailsSnapshot | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request, ContractDiscoveryRequest):
            msg = "request must be a ContractDiscoveryRequest"
            raise DataFoundationValidationError(msg)
        if not isinstance(
            self.availability_log_entry,
            ContractDiscoveryAvailabilityLogEntry,
        ):
            msg = "availability_log_entry must be a ContractDiscoveryAvailabilityLogEntry"
            raise DataFoundationValidationError(msg)
        if self.availability_log_entry.root_symbol != self.request.root_symbol:
            msg = "availability log root_symbol must match the discovery request"
            raise DataFoundationValidationError(msg)
        if self.availability_log_entry.sec_type != self.request.sec_type:
            msg = "availability log sec_type must match the discovery request"
            raise DataFoundationValidationError(msg)
        if self.contract_record is not None:
            if not isinstance(self.contract_record, FuturesContractRecord):
                msg = "contract_record must be a FuturesContractRecord"
                raise DataFoundationValidationError(msg)
            if self.contract_record.root_symbol != self.request.root_symbol:
                msg = "contract_record root_symbol must match the discovery request"
                raise DataFoundationValidationError(msg)
        if self.snapshot is not None:
            if not isinstance(self.snapshot, ContractDetailsSnapshot):
                msg = "snapshot must be a ContractDetailsSnapshot"
                raise DataFoundationValidationError(msg)
            if self.snapshot.client_id != self.request.client_id:
                msg = "snapshot client_id must match the discovery request"
                raise DataFoundationValidationError(msg)
            if (
                self.contract_record is not None
                and self.snapshot.contract_id != self.contract_record.contract_id
            ):
                msg = "snapshot contract_id must match the dated contract record"
                raise DataFoundationValidationError(msg)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable discovery result for manifests or handoffs."""

        return MappingProxyType(
            {
                "request": self.request.to_mapping(),
                "availability_log_entry": self.availability_log_entry.to_mapping(),
                "contract_record": None
                if self.contract_record is None
                else self.contract_record.to_mapping(),
                "snapshot": None if self.snapshot is None else self.snapshot.to_mapping(),
            }
        )


def _coerce_discovery_request(
    request: ContractDiscoveryRequest | Mapping[str, object],
) -> ContractDiscoveryRequest:
    if isinstance(request, ContractDiscoveryRequest):
        return request
    if isinstance(request, Mapping):
        return ContractDiscoveryRequest.from_mapping(request)
    msg = "request must be a ContractDiscoveryRequest or mapping"
    raise DataFoundationValidationError(msg)


def _coerce_futures_contract_record(
    record: FuturesContractRecord | Mapping[str, object] | None,
) -> FuturesContractRecord | None:
    if record is None:
        return None
    if isinstance(record, FuturesContractRecord):
        return record
    if isinstance(record, Mapping):
        return FuturesContractRecord.from_mapping(record)
    msg = "contract_record must be a FuturesContractRecord, mapping, or None"
    raise DataFoundationValidationError(msg)


def _coerce_contract_details_snapshot(
    snapshot: ContractDetailsSnapshot | Mapping[str, object] | None,
) -> ContractDetailsSnapshot | None:
    if snapshot is None:
        return None
    if isinstance(snapshot, ContractDetailsSnapshot):
        return snapshot
    if isinstance(snapshot, Mapping):
        return ContractDetailsSnapshot.from_mapping(snapshot)
    msg = "snapshot must be a ContractDetailsSnapshot, mapping, or None"
    raise DataFoundationValidationError(msg)


def record_contract_discovery(
    request: ContractDiscoveryRequest | Mapping[str, object],
    *,
    include_expired_support_status: IncludeExpiredSupportStatus | str | None = None,
    discovered_at: datetime | None = None,
    evidence_ref: str | None = None,
    contract_record: FuturesContractRecord | Mapping[str, object] | None = None,
    snapshot: ContractDetailsSnapshot | Mapping[str, object] | None = None,
) -> ContractDiscoveryResult:
    """Record synthetic contract discovery without network I/O or history claims."""

    normalized_request = _coerce_discovery_request(request)
    if include_expired_support_status is None:
        status = (
            IncludeExpiredSupportStatus.UNKNOWN
            if normalized_request.include_expired is True
            else IncludeExpiredSupportStatus.NOT_CHECKED
        )
    else:
        status = _normalize_include_expired_status(include_expired_support_status)

    log_entry = ContractDiscoveryAvailabilityLogEntry(
        root_symbol=normalized_request.root_symbol,
        sec_type=normalized_request.sec_type,
        include_expired_requested=normalized_request.include_expired,
        include_expired_support_status=status,
        discovered_at=datetime.now(UTC) if discovered_at is None else discovered_at,
        source=normalized_request.source,
        evidence_ref=evidence_ref,
    )

    normalized_contract_record = _coerce_futures_contract_record(contract_record)
    if normalized_contract_record is not None:
        normalized_contract_record = normalized_contract_record.with_include_expired_support_status(
            status
        )
    return ContractDiscoveryResult(
        request=normalized_request,
        availability_log_entry=log_entry,
        contract_record=normalized_contract_record,
        snapshot=_coerce_contract_details_snapshot(snapshot),
    )


__all__ = [
    "ContractDetailsSnapshot",
    "ContractDiscoveryAvailabilityLogEntry",
    "ContractDiscoveryRequest",
    "ContractDiscoveryResult",
    "DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG",
    "FuturesContractRecord",
    "IncludeExpiredSupportStatus",
    "INSTRUMENT_MASTER_ANCHOR_STATUS",
    "INSTRUMENT_MASTER_CERTIFICATION_STATUS",
    "INSTRUMENT_MASTER_SCHEMA",
    "INSTRUMENT_MASTER_SOURCE_ID",
    "InstrumentMasterRecord",
    "REQUIRED_CONTRACT_DETAILS_SNAPSHOT_FIELDS",
    "REQUIRED_FUTURES_CONTRACT_FIELDS",
    "REQUIRED_INSTRUMENT_MASTER_FIELDS",
    "compute_contract_details_snapshot_hash",
    "load_futures_instrument_master_by_root",
    "load_futures_instrument_master_records",
    "record_contract_discovery",
]
