"""Canonical quote-layer records.

This module defines provider-agnostic BBO records for offline canonicalization
contracts. It performs no provider calls, authorizes no pulls, and makes no
tradability or liquidity truth claims.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

from alpha_system.data.foundation.sessions import SUPPORTED_SESSION_TYPES
from alpha_system.data.foundation.sources import DataFoundationValidationError

CANONICAL_BBO_REQUIRED_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "contract_id",
    "series_id",
    "bar_start_ts",
    "bar_end_ts",
    "event_ts",
    "available_ts",
    "ingested_at",
    "bid",
    "ask",
    "bid_size",
    "ask_size",
    "mid",
    "spread",
    "source",
    "source_request_id",
    "data_version",
    "quality_flags",
    "session_label",
)

CANONICAL_BBO_OPTIONAL_FIELDS: tuple[str, ...] = (
    "spread_ticks",
    "microprice",
    "bid_order_count",
    "ask_order_count",
)

CANONICAL_BBO_RECORD_FIELDS: tuple[str, ...] = (
    CANONICAL_BBO_REQUIRED_FIELDS + CANONICAL_BBO_OPTIONAL_FIELDS
)

MISSING_BBO_QUALITY_FLAG = "missing_bbo"

_SAFE_PATH_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if "\n" in normalized or "\r" in normalized:
        msg = f"{field_name} must be a single-line string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not _SAFE_PATH_TOKEN_PATTERN.fullmatch(token):
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_source(value: object) -> str:
    source = _normalize_id(value, "source")
    if not source.startswith("dsrc_"):
        msg = "source must link to a DataSourceProfile source_id with dsrc_ prefix"
        raise DataFoundationValidationError(msg)
    return source


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_finite_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be an exact finite decimal value"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            msg = f"{field_name} must be an exact finite decimal value"
            raise DataFoundationValidationError(msg)
        try:
            parsed = Decimal(raw)
        except InvalidOperation as exc:
            msg = f"{field_name} must be an exact finite decimal value"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = f"{field_name} must be an exact finite decimal value"
        raise DataFoundationValidationError(msg)

    if not parsed.is_finite():
        msg = f"{field_name} must be finite"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_non_negative_decimal(value: object, field_name: str) -> Decimal:
    parsed = _require_finite_decimal(value, field_name)
    if parsed < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return parsed


def _optional_non_negative_decimal(value: object, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _require_non_negative_decimal(value, field_name)


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return value


def _parse_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            msg = f"{field_name} must be a non-negative integer"
            raise DataFoundationValidationError(msg)
        try:
            parsed = int(raw, 10)
        except ValueError as exc:
            msg = f"{field_name} must be a non-negative integer"
            raise DataFoundationValidationError(msg) from exc
        return _require_non_negative_int(parsed, field_name)
    return _require_non_negative_int(value, field_name)


def _optional_non_negative_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _parse_non_negative_int(value, field_name)


def _normalize_text_collection(
    value: object,
    field_name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be an explicit collection of strings"
        raise DataFoundationValidationError(msg)
    items = tuple(_require_text(item, field_name) for item in value)
    if not items and not allow_empty:
        msg = f"{field_name} must not be empty"
        raise DataFoundationValidationError(msg)
    duplicate_items = sorted({item for item in items if items.count(item) > 1})
    if duplicate_items:
        msg = f"{field_name} must not contain duplicate values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_items))
    return items


def _normalize_session_label(value: object) -> str:
    session_label = (
        _require_text(value, "session_label").upper().replace("-", "_").replace(" ", "_")
    )
    if session_label not in SUPPORTED_SESSION_TYPES:
        msg = "session_label must be drawn from the session model"
        raise DataFoundationValidationError(msg)
    return session_label


def _decimal_or_none(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalBBORecord:
    """Validated canonical best-bid-offer record.

    This record carries timestamp, price, size, and quality semantics only. It
    does not imply alpha value, tradability, broker readiness, or production
    readiness.
    """

    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    mid: Decimal
    spread: Decimal
    source: str
    source_request_id: str
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str
    spread_ticks: Decimal | None = None
    microprice: Decimal | None = None
    bid_order_count: int | None = None
    ask_order_count: int | None = None

    def __post_init__(self) -> None:
        instrument_id = _normalize_id(self.instrument_id, "instrument_id")
        contract_id = _normalize_id(self.contract_id, "contract_id")
        series_id = _normalize_id(self.series_id, "series_id")
        bar_start_ts = _parse_aware_datetime(self.bar_start_ts, "bar_start_ts")
        bar_end_ts = _parse_aware_datetime(self.bar_end_ts, "bar_end_ts")
        event_ts = _parse_aware_datetime(self.event_ts, "event_ts")
        available_ts = _parse_aware_datetime(self.available_ts, "available_ts")
        ingested_at = _parse_aware_datetime(self.ingested_at, "ingested_at")
        bid = _require_non_negative_decimal(self.bid, "bid")
        ask = _require_non_negative_decimal(self.ask, "ask")
        bid_size = _require_non_negative_decimal(self.bid_size, "bid_size")
        ask_size = _require_non_negative_decimal(self.ask_size, "ask_size")
        mid = _require_non_negative_decimal(self.mid, "mid")
        spread = _require_non_negative_decimal(self.spread, "spread")
        source = _normalize_source(self.source)
        source_request_id = _normalize_id(self.source_request_id, "source_request_id")
        data_version = _require_text(self.data_version, "data_version")
        quality_flags = _normalize_text_collection(
            self.quality_flags,
            "quality_flags",
            allow_empty=True,
        )
        session_label = _normalize_session_label(self.session_label)
        spread_ticks = _optional_non_negative_decimal(self.spread_ticks, "spread_ticks")
        microprice = _optional_non_negative_decimal(self.microprice, "microprice")
        bid_order_count = _optional_non_negative_int(self.bid_order_count, "bid_order_count")
        ask_order_count = _optional_non_negative_int(self.ask_order_count, "ask_order_count")

        if bar_end_ts <= bar_start_ts:
            msg = "bar_end_ts must be greater than bar_start_ts"
            raise DataFoundationValidationError(msg)
        if event_ts < bar_end_ts:
            msg = "event_ts must be greater than or equal to bar_end_ts"
            raise DataFoundationValidationError(msg)
        if available_ts < event_ts:
            msg = "available_ts must be greater than or equal to event_ts"
            raise DataFoundationValidationError(msg)
        if ingested_at == available_ts:
            msg = "ingested_at must be distinct from available_ts"
            raise DataFoundationValidationError(msg)
        if ask < bid:
            msg = "ask must be greater than or equal to bid"
            raise DataFoundationValidationError(msg)

        expected_mid = (bid + ask) / Decimal("2")
        expected_spread = ask - bid
        if mid != expected_mid:
            msg = "mid must equal (bid + ask) / 2"
            raise DataFoundationValidationError(msg)
        if spread != expected_spread:
            msg = "spread must equal ask - bid"
            raise DataFoundationValidationError(msg)

        flag_tokens = frozenset(flag.lower() for flag in quality_flags)
        missing_bbo = MISSING_BBO_QUALITY_FLAG in flag_tokens
        zero_quote = (
            bid == 0
            and ask == 0
            and bid_size == 0
            and ask_size == 0
            and mid == 0
            and spread == 0
        )
        if zero_quote and not missing_bbo:
            msg = "zero or missing BBO values require the missing_bbo quality flag"
            raise DataFoundationValidationError(msg)
        if missing_bbo and not zero_quote:
            msg = "missing_bbo quality flag requires explicit zero bid, ask, size, mid, and spread"
            raise DataFoundationValidationError(msg)
        if microprice is not None and not missing_bbo and not (bid <= microprice <= ask):
            msg = "microprice must lie between bid and ask"
            raise DataFoundationValidationError(msg)
        if missing_bbo and microprice not in {None, Decimal("0")}:
            msg = "missing_bbo quality flag cannot carry a non-zero microprice"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "instrument_id", instrument_id)
        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "series_id", series_id)
        object.__setattr__(self, "bar_start_ts", bar_start_ts)
        object.__setattr__(self, "bar_end_ts", bar_end_ts)
        object.__setattr__(self, "event_ts", event_ts)
        object.__setattr__(self, "available_ts", available_ts)
        object.__setattr__(self, "ingested_at", ingested_at)
        object.__setattr__(self, "bid", bid)
        object.__setattr__(self, "ask", ask)
        object.__setattr__(self, "bid_size", bid_size)
        object.__setattr__(self, "ask_size", ask_size)
        object.__setattr__(self, "mid", mid)
        object.__setattr__(self, "spread", spread)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "source_request_id", source_request_id)
        object.__setattr__(self, "data_version", data_version)
        object.__setattr__(self, "quality_flags", quality_flags)
        object.__setattr__(self, "session_label", session_label)
        object.__setattr__(self, "spread_ticks", spread_ticks)
        object.__setattr__(self, "microprice", microprice)
        object.__setattr__(self, "bid_order_count", bid_order_count)
        object.__setattr__(self, "ask_order_count", ask_order_count)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> CanonicalBBORecord:
        """Build a canonical BBO record and reject unsupported fields."""

        extra = tuple(field for field in values if field not in CANONICAL_BBO_RECORD_FIELDS)
        if extra:
            msg = "CanonicalBBORecord includes unsupported fields: "
            raise DataFoundationValidationError(msg + ", ".join(extra))

        missing = tuple(field for field in CANONICAL_BBO_REQUIRED_FIELDS if field not in values)
        if missing:
            msg = "CanonicalBBORecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            instrument_id=_require_text(values["instrument_id"], "instrument_id"),
            contract_id=_require_text(values["contract_id"], "contract_id"),
            series_id=_require_text(values["series_id"], "series_id"),
            bar_start_ts=_parse_aware_datetime(values["bar_start_ts"], "bar_start_ts"),
            bar_end_ts=_parse_aware_datetime(values["bar_end_ts"], "bar_end_ts"),
            event_ts=_parse_aware_datetime(values["event_ts"], "event_ts"),
            available_ts=_parse_aware_datetime(values["available_ts"], "available_ts"),
            ingested_at=_parse_aware_datetime(values["ingested_at"], "ingested_at"),
            bid=_require_non_negative_decimal(values["bid"], "bid"),
            ask=_require_non_negative_decimal(values["ask"], "ask"),
            bid_size=_require_non_negative_decimal(values["bid_size"], "bid_size"),
            ask_size=_require_non_negative_decimal(values["ask_size"], "ask_size"),
            mid=_require_non_negative_decimal(values["mid"], "mid"),
            spread=_require_non_negative_decimal(values["spread"], "spread"),
            source=_require_text(values["source"], "source"),
            source_request_id=_require_text(values["source_request_id"], "source_request_id"),
            data_version=_require_text(values["data_version"], "data_version"),
            quality_flags=_normalize_text_collection(
                values["quality_flags"],
                "quality_flags",
                allow_empty=True,
            ),
            session_label=_require_text(values["session_label"], "session_label"),
            spread_ticks=_optional_non_negative_decimal(
                values.get("spread_ticks"),
                "spread_ticks",
            ),
            microprice=_optional_non_negative_decimal(
                values.get("microprice"),
                "microprice",
            ),
            bid_order_count=_optional_non_negative_int(
                values.get("bid_order_count"),
                "bid_order_count",
            ),
            ask_order_count=_optional_non_negative_int(
                values.get("ask_order_count"),
                "ask_order_count",
            ),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable canonical BBO mapping."""

        return MappingProxyType(
            {
                "instrument_id": self.instrument_id,
                "contract_id": self.contract_id,
                "series_id": self.series_id,
                "bar_start_ts": self.bar_start_ts.isoformat(),
                "bar_end_ts": self.bar_end_ts.isoformat(),
                "event_ts": self.event_ts.isoformat(),
                "available_ts": self.available_ts.isoformat(),
                "ingested_at": self.ingested_at.isoformat(),
                "bid": str(self.bid),
                "ask": str(self.ask),
                "bid_size": str(self.bid_size),
                "ask_size": str(self.ask_size),
                "mid": str(self.mid),
                "spread": str(self.spread),
                "source": self.source,
                "source_request_id": self.source_request_id,
                "data_version": self.data_version,
                "quality_flags": self.quality_flags,
                "session_label": self.session_label,
                "spread_ticks": _decimal_or_none(self.spread_ticks),
                "microprice": _decimal_or_none(self.microprice),
                "bid_order_count": self.bid_order_count,
                "ask_order_count": self.ask_order_count,
            }
        )


__all__ = [
    "CANONICAL_BBO_OPTIONAL_FIELDS",
    "CANONICAL_BBO_RECORD_FIELDS",
    "CANONICAL_BBO_REQUIRED_FIELDS",
    "CanonicalBBORecord",
    "MISSING_BBO_QUALITY_FLAG",
]
