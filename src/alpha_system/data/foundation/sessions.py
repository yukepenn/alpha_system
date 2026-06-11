"""Session templates and dated trading calendar records.

DATA-P12 owns local-only session/calendar contracts. This module performs no
provider calls, opens no broker/account surface, and does not claim exchange
holiday completeness or official calendar finality.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime, time, timedelta
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alpha_system.data.foundation.instruments import (
    InstrumentMasterRecord,
    load_futures_instrument_master_records,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

SESSION_CALENDAR_SCHEMA = "alpha_system.session_calendar.v1"

REQUIRED_SESSION_TEMPLATE_FIELDS: tuple[str, ...] = (
    "template_id",
    "timezone",
    "rth_start",
    "rth_end",
    "eth_start",
    "eth_end",
    "maintenance_breaks",
    "source",
)

REQUIRED_TRADING_CALENDAR_FIELDS: tuple[str, ...] = (
    "calendar_id",
    "instrument_root",
    "date",
    "session_type",
    "open_ts",
    "close_ts",
    "breaks",
    "is_holiday",
    "is_early_close",
    "source",
)

SESSION_TYPE_RTH = "RTH"
SESSION_TYPE_ETH = "ETH"
SESSION_TYPE_HOLIDAY = "HOLIDAY"
SESSION_TYPE_EARLY_CLOSE = "EARLY_CLOSE"
CME_INDEX_FUTURES_SESSION_TEMPLATE_ID = "session_cme_index_futures_eth"
SUPPORTED_SESSION_TYPES: frozenset[str] = frozenset(
    {
        SESSION_TYPE_RTH,
        SESSION_TYPE_ETH,
        SESSION_TYPE_HOLIDAY,
        SESSION_TYPE_EARLY_CLOSE,
    }
)

_SECONDS_PER_DAY = 24 * 60 * 60
_FORBIDDEN_IMPLICIT_TIMEZONES: frozenset[str] = frozenset(
    {
        "auto",
        "default",
        "implicit",
        "local",
        "system",
    }
)
_FORBIDDEN_SOURCE_FINALITY_MARKERS: frozenset[str] = frozenset(
    {
        "authoritative",
        "certified",
        "complete_holiday",
        "exchange_final",
        "official_final",
        "production",
    }
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve(strict=False).parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent.resolve(strict=False)
    return Path.cwd().resolve(strict=False)


DEFAULT_SESSION_CALENDAR_CONFIG = (
    _repo_root() / "configs" / "data" / "session_templates_and_calendar.json"
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


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_root_symbol(value: object) -> str:
    root_symbol = _require_text(value, "instrument_root").upper()
    if not root_symbol.isalnum():
        msg = "instrument_root must be alphanumeric"
        raise DataFoundationValidationError(msg)
    master_roots = {record.root_symbol for record in load_futures_instrument_master_records()}
    if root_symbol not in master_roots:
        msg = f"instrument_root {root_symbol!r} is not in the futures instrument master"
        raise DataFoundationValidationError(msg)
    return root_symbol


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _require_source(value: object, field_name: str = "source") -> str:
    source = _require_text(value, field_name)
    token = source.lower().replace("-", "_").replace(" ", "_")
    if any(marker in token for marker in _FORBIDDEN_SOURCE_FINALITY_MARKERS):
        msg = f"{field_name} must not claim holiday completeness or exchange-final authority"
        raise DataFoundationValidationError(msg)
    if "synthetic" not in token and "to_be_verified" not in token:
        msg = f"{field_name} must include a synthetic or to_be_verified provenance marker"
        raise DataFoundationValidationError(msg)
    return source


def _require_explicit_timezone(value: object) -> str:
    timezone_id = _require_text(value, "timezone")
    token = timezone_id.lower()
    if token in _FORBIDDEN_IMPLICIT_TIMEZONES:
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


def _parse_clock_time(value: object, field_name: str) -> time:
    if isinstance(value, datetime):
        msg = f"{field_name} must be a clock time, not a datetime"
        raise DataFoundationValidationError(msg)
    if isinstance(value, time):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = time.fromisoformat(raw)
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 clock time"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        msg = f"{field_name} must use the template timezone field, not per-time tzinfo"
        raise DataFoundationValidationError(msg)
    return parsed


def _clock_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _parse_date(value: object, field_name: str) -> Date:
    if isinstance(value, datetime):
        msg = f"{field_name} must be a calendar date, not a datetime"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Date):
        return value
    raw = _require_text(value, field_name)
    try:
        return Date.fromisoformat(raw)
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 date"
        raise DataFoundationValidationError(msg) from exc


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


def _parse_optional_aware_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _parse_aware_datetime(value, field_name)


def _normalize_session_type(value: object) -> str:
    token = _require_text(value, "session_type").upper().replace("-", "_").replace(" ", "_")
    if token not in SUPPORTED_SESSION_TYPES:
        msg = "session_type must be one of RTH, ETH, HOLIDAY, EARLY_CLOSE"
        raise DataFoundationValidationError(msg)
    return token


def _require_iterable(value: object, field_name: str) -> Iterable[object]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be a list of explicit window mappings"
        raise DataFoundationValidationError(msg)
    return value


@dataclass(frozen=True, slots=True)
class SessionTimeWindow:
    """A clock-time maintenance break window for a session template."""

    start: time
    end: time

    def __post_init__(self) -> None:
        start = _parse_clock_time(self.start, "maintenance_breaks.start")
        end = _parse_clock_time(self.end, "maintenance_breaks.end")
        if _clock_seconds(start) >= _clock_seconds(end):
            msg = "maintenance_breaks windows must have start < end"
            raise DataFoundationValidationError(msg)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "SessionTimeWindow":
        """Build a maintenance break window from declarative config."""

        if "start" not in values or "end" not in values:
            msg = "maintenance_breaks entries must include start and end"
            raise DataFoundationValidationError(msg)
        return cls(start=values["start"], end=values["end"])

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for docs and audits."""

        return MappingProxyType(
            {
                "start": self.start.isoformat(timespec="minutes"),
                "end": self.end.isoformat(timespec="minutes"),
            }
        )


@dataclass(frozen=True, slots=True)
class TradingCalendarBreak:
    """A concrete timestamp break window inside a dated open session."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        start = _parse_aware_datetime(self.start, "breaks.start")
        end = _parse_aware_datetime(self.end, "breaks.end")
        if end <= start:
            msg = "breaks windows must have start < end"
            raise DataFoundationValidationError(msg)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "TradingCalendarBreak":
        """Build a dated break window from declarative config."""

        if "start" not in values or "end" not in values:
            msg = "breaks entries must include start and end"
            raise DataFoundationValidationError(msg)
        return cls(start=_parse_aware_datetime(values["start"], "breaks.start"), end=values["end"])

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for docs and audits."""

        return MappingProxyType(
            {
                "start": self.start.isoformat(),
                "end": self.end.isoformat(),
            }
        )


def _coerce_session_time_window(value: object) -> SessionTimeWindow:
    if isinstance(value, SessionTimeWindow):
        return value
    if isinstance(value, Mapping):
        return SessionTimeWindow.from_mapping(value)
    msg = "maintenance_breaks entries must be mappings or SessionTimeWindow records"
    raise DataFoundationValidationError(msg)


def _coerce_trading_calendar_break(value: object) -> TradingCalendarBreak:
    if isinstance(value, TradingCalendarBreak):
        return value
    if isinstance(value, Mapping):
        return TradingCalendarBreak.from_mapping(value)
    msg = "breaks entries must be mappings or TradingCalendarBreak records"
    raise DataFoundationValidationError(msg)


def _normalize_session_time_windows(value: object) -> tuple[SessionTimeWindow, ...]:
    return tuple(
        _coerce_session_time_window(item)
        for item in _require_iterable(value, "maintenance_breaks")
    )


def _normalize_calendar_breaks(value: object) -> tuple[TradingCalendarBreak, ...]:
    return tuple(
        _coerce_trading_calendar_break(item)
        for item in _require_iterable(value, "breaks")
    )


def _validate_rth_within_eth(
    *,
    rth_start: time,
    rth_end: time,
    eth_start: time,
    eth_end: time,
) -> None:
    eth_start_seconds = _clock_seconds(eth_start)
    eth_end_seconds = _clock_seconds(eth_end)
    if eth_start_seconds == eth_end_seconds:
        msg = "eth_start and eth_end must not be equal"
        raise DataFoundationValidationError(msg)
    if eth_end_seconds <= eth_start_seconds:
        eth_end_seconds += _SECONDS_PER_DAY

    rth_start_seconds = _clock_seconds(rth_start)
    rth_end_seconds = _clock_seconds(rth_end)
    if rth_start_seconds >= rth_end_seconds:
        msg = "rth_start must be before rth_end"
        raise DataFoundationValidationError(msg)

    candidates = (
        (rth_start_seconds, rth_end_seconds),
        (rth_start_seconds + _SECONDS_PER_DAY, rth_end_seconds + _SECONDS_PER_DAY),
    )
    if not any(eth_start_seconds <= start and end <= eth_end_seconds for start, end in candidates):
        msg = "RTH window must fall within the ETH window"
        raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True)
class SessionTemplate:
    """Validated exchange-time session template referenced by an instrument root."""

    template_id: str
    timezone: str
    rth_start: time
    rth_end: time
    eth_start: time
    eth_end: time
    maintenance_breaks: tuple[SessionTimeWindow, ...]
    source: str

    def __post_init__(self) -> None:
        template_id = _normalize_id(self.template_id, "template_id")
        timezone_id = _require_explicit_timezone(self.timezone)
        rth_start = _parse_clock_time(self.rth_start, "rth_start")
        rth_end = _parse_clock_time(self.rth_end, "rth_end")
        eth_start = _parse_clock_time(self.eth_start, "eth_start")
        eth_end = _parse_clock_time(self.eth_end, "eth_end")
        maintenance_breaks = _normalize_session_time_windows(self.maintenance_breaks)
        source = _require_source(self.source)

        _validate_rth_within_eth(
            rth_start=rth_start,
            rth_end=rth_end,
            eth_start=eth_start,
            eth_end=eth_end,
        )

        object.__setattr__(self, "template_id", template_id)
        object.__setattr__(self, "timezone", timezone_id)
        object.__setattr__(self, "rth_start", rth_start)
        object.__setattr__(self, "rth_end", rth_end)
        object.__setattr__(self, "eth_start", eth_start)
        object.__setattr__(self, "eth_end", eth_end)
        object.__setattr__(self, "maintenance_breaks", maintenance_breaks)
        object.__setattr__(self, "source", source)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "SessionTemplate":
        """Build a session template from config data and fail closed."""

        missing = tuple(field for field in REQUIRED_SESSION_TEMPLATE_FIELDS if field not in values)
        if missing:
            msg = "SessionTemplate missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            template_id=_require_text(values["template_id"], "template_id"),
            timezone=_require_text(values["timezone"], "timezone"),
            rth_start=values["rth_start"],
            rth_end=values["rth_end"],
            eth_start=values["eth_start"],
            eth_end=values["eth_end"],
            maintenance_breaks=_normalize_session_time_windows(values["maintenance_breaks"]),
            source=_require_text(values["source"], "source"),
        )

    @property
    def zone(self) -> ZoneInfo:
        """Return the IANA timezone object for exchange-time conversions."""

        return ZoneInfo(self.timezone)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for audits and docs generation."""

        return MappingProxyType(
            {
                "template_id": self.template_id,
                "timezone": self.timezone,
                "rth_start": self.rth_start.isoformat(timespec="minutes"),
                "rth_end": self.rth_end.isoformat(timespec="minutes"),
                "eth_start": self.eth_start.isoformat(timespec="minutes"),
                "eth_end": self.eth_end.isoformat(timespec="minutes"),
                "maintenance_breaks": tuple(
                    window.to_mapping() for window in self.maintenance_breaks
                ),
                "source": self.source,
            }
        )


@dataclass(frozen=True, slots=True)
class SessionWindowState:
    """Timestamp-derived exchange-time session state for one bar."""

    template_id: str
    timezone: str
    local_ts: datetime
    trade_date: Date
    segment_label: str
    is_rth: bool
    is_eth: bool
    rth_open_ts: datetime
    rth_close_ts: datetime
    minutes_from_rth_open: int | None
    minutes_to_rth_close: int | None


@dataclass(frozen=True, slots=True)
class TradingCalendarRecord:
    """Concrete dated session record with explicit timezone-aware timestamps."""

    calendar_id: str
    instrument_root: str
    date: Date
    session_type: str
    open_ts: datetime | None
    close_ts: datetime | None
    breaks: tuple[TradingCalendarBreak, ...]
    is_holiday: bool
    is_early_close: bool
    source: str

    def __post_init__(self) -> None:
        calendar_id = _normalize_id(self.calendar_id, "calendar_id")
        instrument_root = _normalize_root_symbol(self.instrument_root)
        calendar_date = _parse_date(self.date, "date")
        session_type = _normalize_session_type(self.session_type)
        is_holiday = _require_bool(self.is_holiday, "is_holiday")
        is_early_close = _require_bool(self.is_early_close, "is_early_close")
        open_ts = _parse_optional_aware_datetime(self.open_ts, "open_ts")
        close_ts = _parse_optional_aware_datetime(self.close_ts, "close_ts")
        breaks = _normalize_calendar_breaks(self.breaks)
        source = _require_source(self.source)

        if is_holiday and is_early_close:
            msg = "holiday sessions cannot also be early-close sessions"
            raise DataFoundationValidationError(msg)
        if is_holiday and session_type != SESSION_TYPE_HOLIDAY:
            msg = "is_holiday records must use session_type HOLIDAY"
            raise DataFoundationValidationError(msg)
        if not is_holiday and session_type == SESSION_TYPE_HOLIDAY:
            msg = "session_type HOLIDAY requires is_holiday true"
            raise DataFoundationValidationError(msg)
        if is_early_close and session_type != SESSION_TYPE_EARLY_CLOSE:
            msg = "is_early_close records must use session_type EARLY_CLOSE"
            raise DataFoundationValidationError(msg)
        if session_type == SESSION_TYPE_EARLY_CLOSE and not is_early_close:
            msg = "session_type EARLY_CLOSE requires is_early_close true"
            raise DataFoundationValidationError(msg)

        if is_holiday:
            if (open_ts is None) != (close_ts is None):
                msg = "holiday records must omit both open_ts and close_ts or provide both"
                raise DataFoundationValidationError(msg)
            if open_ts is not None and close_ts is not None and close_ts != open_ts:
                msg = "holiday records with timestamps must be explicitly closed"
                raise DataFoundationValidationError(msg)
            if breaks:
                msg = "holiday records must not include tradable break windows"
                raise DataFoundationValidationError(msg)
        else:
            if open_ts is None or close_ts is None:
                msg = "non-holiday sessions require open_ts and close_ts"
                raise DataFoundationValidationError(msg)
            if close_ts <= open_ts:
                msg = "close_ts must be greater than open_ts for open sessions"
                raise DataFoundationValidationError(msg)
            for window in breaks:
                if not (open_ts <= window.start and window.end <= close_ts):
                    msg = "breaks windows must fall within the open session"
                    raise DataFoundationValidationError(msg)

        object.__setattr__(self, "calendar_id", calendar_id)
        object.__setattr__(self, "instrument_root", instrument_root)
        object.__setattr__(self, "date", calendar_date)
        object.__setattr__(self, "session_type", session_type)
        object.__setattr__(self, "open_ts", open_ts)
        object.__setattr__(self, "close_ts", close_ts)
        object.__setattr__(self, "breaks", breaks)
        object.__setattr__(self, "is_holiday", is_holiday)
        object.__setattr__(self, "is_early_close", is_early_close)
        object.__setattr__(self, "source", source)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "TradingCalendarRecord":
        """Build a dated calendar record from config data and fail closed."""

        missing = tuple(field for field in REQUIRED_TRADING_CALENDAR_FIELDS if field not in values)
        if missing:
            msg = "TradingCalendarRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            calendar_id=_require_text(values["calendar_id"], "calendar_id"),
            instrument_root=_require_text(values["instrument_root"], "instrument_root"),
            date=values["date"],
            session_type=values["session_type"],
            open_ts=_parse_optional_aware_datetime(values["open_ts"], "open_ts"),
            close_ts=_parse_optional_aware_datetime(values["close_ts"], "close_ts"),
            breaks=_normalize_calendar_breaks(values["breaks"]),
            is_holiday=values["is_holiday"],
            is_early_close=values["is_early_close"],
            source=_require_text(values["source"], "source"),
        )

    @property
    def is_open_session(self) -> bool:
        """Return whether this record describes a tradable open session."""

        return not self.is_holiday

    @property
    def duration(self) -> timedelta:
        """Return the concrete open-session duration, or zero for holidays."""

        if self.open_ts is None or self.close_ts is None:
            return timedelta(0)
        return self.close_ts - self.open_ts

    @property
    def has_offset_transition(self) -> bool:
        """Return whether open and close timestamps expose a timezone offset change."""

        if self.open_ts is None or self.close_ts is None:
            return False
        return self.open_ts.utcoffset() != self.close_ts.utcoffset()

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable mapping for audits and docs generation."""

        return MappingProxyType(
            {
                "calendar_id": self.calendar_id,
                "instrument_root": self.instrument_root,
                "date": self.date.isoformat(),
                "session_type": self.session_type,
                "open_ts": None if self.open_ts is None else self.open_ts.isoformat(),
                "close_ts": None if self.close_ts is None else self.close_ts.isoformat(),
                "breaks": tuple(window.to_mapping() for window in self.breaks),
                "is_holiday": self.is_holiday,
                "is_early_close": self.is_early_close,
                "source": self.source,
            }
        )


def _load_config_payload(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"session/calendar config cannot be loaded from {path}"
        raise DataFoundationValidationError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = "session/calendar config must be a JSON object"
        raise DataFoundationValidationError(msg)
    if payload.get("schema") != SESSION_CALENDAR_SCHEMA:
        msg = f"session/calendar config schema must be {SESSION_CALENDAR_SCHEMA!r}"
        raise DataFoundationValidationError(msg)
    return payload


def load_session_templates(path: str | Path | None = None) -> tuple[SessionTemplate, ...]:
    """Load DATA-P12 session templates from a declarative JSON config."""

    config_path = DEFAULT_SESSION_CALENDAR_CONFIG if path is None else Path(path)
    payload = _load_config_payload(config_path)
    raw_templates = payload.get("session_templates")
    if isinstance(raw_templates, str) or not isinstance(raw_templates, list) or not raw_templates:
        msg = "session_templates must be a non-empty list"
        raise DataFoundationValidationError(msg)

    templates = tuple(
        SessionTemplate.from_mapping(raw_template)
        for raw_template in raw_templates
        if isinstance(raw_template, Mapping)
    )
    if len(templates) != len(raw_templates):
        msg = "session_templates entries must be JSON objects"
        raise DataFoundationValidationError(msg)

    template_ids = [template.template_id for template in templates]
    duplicate_ids = sorted(
        {
            template_id
            for template_id in template_ids
            if template_ids.count(template_id) > 1
        }
    )
    if duplicate_ids:
        msg = "session_templates contains duplicate template_id values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_ids))
    return templates


def load_session_templates_by_id(
    path: str | Path | None = None,
) -> Mapping[str, SessionTemplate]:
    """Load DATA-P12 session templates keyed by ``template_id``."""

    templates = load_session_templates(path)
    return MappingProxyType({template.template_id: template for template in templates})


def load_session_template_by_id(
    template_id: str = CME_INDEX_FUTURES_SESSION_TEMPLATE_ID,
    path: str | Path | None = None,
) -> SessionTemplate:
    """Load one session template by id from the declarative config."""

    normalized = _normalize_id(template_id, "template_id")
    templates = load_session_templates_by_id(path)
    template = templates.get(normalized)
    if template is None:
        msg = f"session template does not resolve: {normalized}"
        raise DataFoundationValidationError(msg)
    return template


def classify_session_timestamp(
    timestamp: datetime,
    *,
    template: SessionTemplate | None = None,
    template_id: str = CME_INDEX_FUTURES_SESSION_TEMPLATE_ID,
    path: str | Path | None = None,
) -> SessionWindowState:
    """Classify a bar timestamp against the template's local session windows.

    The RTH interval is start-inclusive/end-exclusive for bar-start timestamps.
    For the CME index futures template this means a bar at 08:30 America/Chicago
    is RTH, a bar at 14:59 is RTH, and a bar at 15:00 belongs to ETH.
    """

    aware_ts = _require_aware_datetime(timestamp, "timestamp")
    session_template = (
        load_session_template_by_id(template_id=template_id, path=path)
        if template is None
        else template
    )
    local_ts = aware_ts.astimezone(session_template.zone)
    rth_open = datetime.combine(local_ts.date(), session_template.rth_start, session_template.zone)
    rth_close = datetime.combine(local_ts.date(), session_template.rth_end, session_template.zone)
    if rth_close <= rth_open:
        msg = "RTH close must be after RTH open for timestamp classification"
        raise DataFoundationValidationError(msg)
    is_rth = rth_open <= local_ts < rth_close
    minutes_from_open = None
    minutes_to_close = None
    if is_rth:
        minutes_from_open = _floor_minutes_between(rth_open, local_ts)
        minutes_to_close = _floor_minutes_between(local_ts, rth_close)
    segment_label = SESSION_TYPE_RTH if is_rth else SESSION_TYPE_ETH
    return SessionWindowState(
        template_id=session_template.template_id,
        timezone=session_template.timezone,
        local_ts=local_ts,
        trade_date=_template_trade_date(local_ts, session_template),
        segment_label=segment_label,
        is_rth=is_rth,
        is_eth=not is_rth,
        rth_open_ts=rth_open,
        rth_close_ts=rth_close,
        minutes_from_rth_open=minutes_from_open,
        minutes_to_rth_close=minutes_to_close,
    )


def session_segment_id(
    series_id: str,
    timestamp: datetime,
    *,
    template: SessionTemplate | None = None,
    template_id: str = CME_INDEX_FUTURES_SESSION_TEMPLATE_ID,
    path: str | Path | None = None,
) -> str:
    """Return the session feature id segment for a timestamp-derived session."""

    state = classify_session_timestamp(
        timestamp,
        template=template,
        template_id=template_id,
        path=path,
    )
    return (
        f"{_require_text(series_id, 'series_id')}:"
        f"{state.trade_date.isoformat()}:"
        f"{state.segment_label}"
    )


def _floor_minutes_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def _template_trade_date(local_ts: datetime, template: SessionTemplate) -> Date:
    if _clock_seconds(template.eth_end) <= _clock_seconds(template.eth_start):
        if _clock_seconds(local_ts.time()) >= _clock_seconds(template.eth_start):
            return local_ts.date() + timedelta(days=1)
    return local_ts.date()


def load_trading_calendar_records(
    path: str | Path | None = None,
) -> tuple[TradingCalendarRecord, ...]:
    """Load synthetic dated trading calendar records from a declarative JSON config."""

    config_path = DEFAULT_SESSION_CALENDAR_CONFIG if path is None else Path(path)
    payload = _load_config_payload(config_path)
    raw_records = payload.get("calendar_records", [])
    if isinstance(raw_records, str) or not isinstance(raw_records, list):
        msg = "calendar_records must be a list"
        raise DataFoundationValidationError(msg)

    records = tuple(
        TradingCalendarRecord.from_mapping(raw_record)
        for raw_record in raw_records
        if isinstance(raw_record, Mapping)
    )
    if len(records) != len(raw_records):
        msg = "calendar_records entries must be JSON objects"
        raise DataFoundationValidationError(msg)

    keys = [
        (
            record.calendar_id,
            record.instrument_root,
            record.date,
            record.session_type,
        )
        for record in records
    ]
    duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
    if duplicate_keys:
        msg = "calendar_records contains duplicate dated session records"
        raise DataFoundationValidationError(msg)
    return records


def resolve_session_template_for_instrument(
    instrument: InstrumentMasterRecord,
    templates_by_id: Mapping[str, SessionTemplate] | None = None,
) -> SessionTemplate:
    """Resolve an instrument-master ``session_template_id`` to a template."""

    templates = load_session_templates_by_id() if templates_by_id is None else templates_by_id
    template = templates.get(instrument.session_template_id)
    if template is None:
        msg = (
            "InstrumentMasterRecord.session_template_id does not resolve to a "
            f"SessionTemplate: {instrument.session_template_id}"
        )
        raise DataFoundationValidationError(msg)
    if template.timezone != instrument.timezone:
        msg = (
            "SessionTemplate timezone must match InstrumentMasterRecord timezone "
            f"for {instrument.root_symbol}"
        )
        raise DataFoundationValidationError(msg)
    return template


def resolve_session_templates_for_instrument_master(
    *,
    instrument_master_path: str | Path | None = None,
    session_calendar_path: str | Path | None = None,
) -> Mapping[str, SessionTemplate]:
    """Resolve all instrument-master roots to session templates."""

    templates_by_id = load_session_templates_by_id(session_calendar_path)
    records = load_futures_instrument_master_records(instrument_master_path)
    return MappingProxyType(
        {
            record.root_symbol: resolve_session_template_for_instrument(
                record,
                templates_by_id,
            )
            for record in records
        }
    )


__all__ = [
    "DEFAULT_SESSION_CALENDAR_CONFIG",
    "REQUIRED_SESSION_TEMPLATE_FIELDS",
    "REQUIRED_TRADING_CALENDAR_FIELDS",
    "SESSION_CALENDAR_SCHEMA",
    "SESSION_TYPE_EARLY_CLOSE",
    "SESSION_TYPE_ETH",
    "SESSION_TYPE_HOLIDAY",
    "SESSION_TYPE_RTH",
    "SUPPORTED_SESSION_TYPES",
    "CME_INDEX_FUTURES_SESSION_TEMPLATE_ID",
    "SessionTemplate",
    "SessionTimeWindow",
    "SessionWindowState",
    "TradingCalendarBreak",
    "TradingCalendarRecord",
    "classify_session_timestamp",
    "load_session_template_by_id",
    "load_session_templates",
    "load_session_templates_by_id",
    "load_trading_calendar_records",
    "resolve_session_template_for_instrument",
    "resolve_session_templates_for_instrument_master",
    "session_segment_id",
]
