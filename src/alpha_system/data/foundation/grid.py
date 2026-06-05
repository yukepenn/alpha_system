"""Dense research-grid OHLCV records.

DenseGridBarRecord is a derived research view over sparse provider OHLCV truth.
Synthetic no-trade rows are explicitly flagged and are not executable prices,
tradability evidence, broker readiness evidence, or live-data readiness.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from types import MappingProxyType

from alpha_system.data.foundation.bars import CANONICAL_BAR_RECORD_FIELDS
from alpha_system.data.foundation.sessions import SUPPORTED_SESSION_TYPES
from alpha_system.data.foundation.sources import DataFoundationValidationError

DENSE_GRID_BAR_EXTRA_FIELDS: tuple[str, ...] = (
    "has_trade",
    "synthetic",
    "fill_method",
    "provider_bar_ref",
)

DENSE_GRID_BAR_RECORD_FIELDS: tuple[str, ...] = (
    CANONICAL_BAR_RECORD_FIELDS + DENSE_GRID_BAR_EXTRA_FIELDS
)

NO_TRADE_QUALITY_FLAG = "no_trade"
PREVIOUS_CLOSE_FILL_METHOD = "previous_close"

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


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _require_text(value, field_name)


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


def _parse_utc_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware UTC datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC)


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


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


def _require_positive_decimal(value: object, field_name: str) -> Decimal:
    parsed = _require_finite_decimal(value, field_name)
    if parsed <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return parsed


def _normalize_text_collection(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be an explicit collection of strings"
        raise DataFoundationValidationError(msg)
    items = tuple(_require_text(item, field_name) for item in value)
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


@dataclass(frozen=True, slots=True, kw_only=True)
class DenseGridBarRecord:
    """Validated dense OHLCV research-grid row.

    Rows with ``synthetic=True`` are previous-close no-trade placeholders. They
    preserve a one-minute research grid but are not provider bars and must not be
    treated as executable prices or proof of tradability.
    """

    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str
    source_request_id: str
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str
    has_trade: bool
    synthetic: bool
    fill_method: str | None
    provider_bar_ref: str | None

    def __post_init__(self) -> None:
        instrument_id = _normalize_id(self.instrument_id, "instrument_id")
        contract_id = _normalize_id(self.contract_id, "contract_id")
        series_id = _normalize_id(self.series_id, "series_id")
        bar_start_ts = _parse_utc_datetime(self.bar_start_ts, "bar_start_ts")
        bar_end_ts = _parse_utc_datetime(self.bar_end_ts, "bar_end_ts")
        event_ts = _parse_utc_datetime(self.event_ts, "event_ts")
        available_ts = _parse_utc_datetime(self.available_ts, "available_ts")
        ingested_at = _parse_utc_datetime(self.ingested_at, "ingested_at")
        open_price = _require_positive_decimal(self.open, "open")
        high_price = _require_positive_decimal(self.high, "high")
        low_price = _require_positive_decimal(self.low, "low")
        close_price = _require_positive_decimal(self.close, "close")
        volume = _require_non_negative_decimal(self.volume, "volume")
        source = _normalize_source(self.source)
        source_request_id = _normalize_id(self.source_request_id, "source_request_id")
        data_version = _require_text(self.data_version, "data_version")
        quality_flags = _normalize_text_collection(self.quality_flags, "quality_flags")
        session_label = _normalize_session_label(self.session_label)
        has_trade = _require_bool(self.has_trade, "has_trade")
        synthetic = _require_bool(self.synthetic, "synthetic")
        fill_method = _optional_text(self.fill_method, "fill_method")
        provider_bar_ref = _optional_text(self.provider_bar_ref, "provider_bar_ref")

        if bar_end_ts <= bar_start_ts:
            msg = "bar_end_ts must be greater than bar_start_ts"
            raise DataFoundationValidationError(msg)
        if available_ts < bar_end_ts:
            msg = "available_ts must be greater than or equal to bar_end_ts"
            raise DataFoundationValidationError(msg)
        if high_price < low_price:
            msg = "high must be greater than or equal to low"
            raise DataFoundationValidationError(msg)
        if not (low_price <= open_price <= high_price):
            msg = "open must satisfy low <= open <= high"
            raise DataFoundationValidationError(msg)
        if not (low_price <= close_price <= high_price):
            msg = "close must satisfy low <= close <= high"
            raise DataFoundationValidationError(msg)

        flag_tokens = frozenset(flag.lower() for flag in quality_flags)
        if has_trade:
            if synthetic:
                msg = "real dense-grid rows must not be synthetic"
                raise DataFoundationValidationError(msg)
            if fill_method is not None:
                msg = "real dense-grid rows must not carry fill_method"
                raise DataFoundationValidationError(msg)
            if provider_bar_ref is None:
                msg = "real dense-grid rows must reference the sparse provider data_version"
                raise DataFoundationValidationError(msg)
        else:
            if not synthetic:
                msg = "no-trade dense-grid rows must be synthetic"
                raise DataFoundationValidationError(msg)
            if fill_method != PREVIOUS_CLOSE_FILL_METHOD:
                msg = 'synthetic no-trade rows must use fill_method "previous_close"'
                raise DataFoundationValidationError(msg)
            if provider_bar_ref is not None:
                msg = "synthetic no-trade rows must not reference a provider bar"
                raise DataFoundationValidationError(msg)
            if volume != Decimal("0"):
                msg = "synthetic no-trade rows must have zero volume"
                raise DataFoundationValidationError(msg)
            if NO_TRADE_QUALITY_FLAG not in flag_tokens:
                msg = 'synthetic no-trade rows require the "no_trade" quality flag'
                raise DataFoundationValidationError(msg)
            if not (
                open_price == high_price == low_price == close_price
                and close_price > Decimal("0")
            ):
                msg = "synthetic no-trade rows must carry one positive previous-close price"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "instrument_id", instrument_id)
        object.__setattr__(self, "contract_id", contract_id)
        object.__setattr__(self, "series_id", series_id)
        object.__setattr__(self, "bar_start_ts", bar_start_ts)
        object.__setattr__(self, "bar_end_ts", bar_end_ts)
        object.__setattr__(self, "event_ts", event_ts)
        object.__setattr__(self, "available_ts", available_ts)
        object.__setattr__(self, "ingested_at", ingested_at)
        object.__setattr__(self, "open", open_price)
        object.__setattr__(self, "high", high_price)
        object.__setattr__(self, "low", low_price)
        object.__setattr__(self, "close", close_price)
        object.__setattr__(self, "volume", volume)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "source_request_id", source_request_id)
        object.__setattr__(self, "data_version", data_version)
        object.__setattr__(self, "quality_flags", quality_flags)
        object.__setattr__(self, "session_label", session_label)
        object.__setattr__(self, "has_trade", has_trade)
        object.__setattr__(self, "synthetic", synthetic)
        object.__setattr__(self, "fill_method", fill_method)
        object.__setattr__(self, "provider_bar_ref", provider_bar_ref)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DenseGridBarRecord:
        """Build a dense grid row from a mapping and reject unsupported fields."""

        extra = tuple(field for field in values if field not in DENSE_GRID_BAR_RECORD_FIELDS)
        if extra:
            msg = "DenseGridBarRecord includes unsupported fields: "
            raise DataFoundationValidationError(msg + ", ".join(extra))

        missing = tuple(field for field in DENSE_GRID_BAR_RECORD_FIELDS if field not in values)
        if missing:
            msg = "DenseGridBarRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            instrument_id=_require_text(values["instrument_id"], "instrument_id"),
            contract_id=_require_text(values["contract_id"], "contract_id"),
            series_id=_require_text(values["series_id"], "series_id"),
            bar_start_ts=_parse_utc_datetime(values["bar_start_ts"], "bar_start_ts"),
            bar_end_ts=_parse_utc_datetime(values["bar_end_ts"], "bar_end_ts"),
            event_ts=_parse_utc_datetime(values["event_ts"], "event_ts"),
            available_ts=_parse_utc_datetime(values["available_ts"], "available_ts"),
            ingested_at=_parse_utc_datetime(values["ingested_at"], "ingested_at"),
            open=_require_positive_decimal(values["open"], "open"),
            high=_require_positive_decimal(values["high"], "high"),
            low=_require_positive_decimal(values["low"], "low"),
            close=_require_positive_decimal(values["close"], "close"),
            volume=_require_non_negative_decimal(values["volume"], "volume"),
            source=_require_text(values["source"], "source"),
            source_request_id=_require_text(values["source_request_id"], "source_request_id"),
            data_version=_require_text(values["data_version"], "data_version"),
            quality_flags=_normalize_text_collection(values["quality_flags"], "quality_flags"),
            session_label=_require_text(values["session_label"], "session_label"),
            has_trade=_require_bool(values["has_trade"], "has_trade"),
            synthetic=_require_bool(values["synthetic"], "synthetic"),
            fill_method=_optional_text(values["fill_method"], "fill_method"),
            provider_bar_ref=_optional_text(values["provider_bar_ref"], "provider_bar_ref"),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable dense grid mapping."""

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
                "open": str(self.open),
                "high": str(self.high),
                "low": str(self.low),
                "close": str(self.close),
                "volume": str(self.volume),
                "source": self.source,
                "source_request_id": self.source_request_id,
                "data_version": self.data_version,
                "quality_flags": self.quality_flags,
                "session_label": self.session_label,
                "has_trade": self.has_trade,
                "synthetic": self.synthetic,
                "fill_method": self.fill_method,
                "provider_bar_ref": self.provider_bar_ref,
            }
        )


__all__ = [
    "DENSE_GRID_BAR_RECORD_FIELDS",
    "DenseGridBarRecord",
    "NO_TRADE_QUALITY_FLAG",
    "PREVIOUS_CLOSE_FILL_METHOD",
]
