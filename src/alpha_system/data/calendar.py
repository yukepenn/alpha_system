"""Synthetic trading calendar config loading and session lookup."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from alpha_system.core.enums import SessionType
from alpha_system.data.contracts import TradingSession
from alpha_system.data.sessions import build_session_id, session_contains_bar


HOLIDAY_QUALITY_FLAG = "holiday"
HALF_DAY_QUALITY_FLAG = "half_day"


@dataclass(frozen=True, slots=True)
class CalendarSessionDefinition:
    """One synthetic calendar entry before conversion to a contract session."""

    trading_date: date
    open_time: time | None
    close_time: time | None
    is_holiday: bool = False
    is_half_day: bool = False
    session_type: SessionType = SessionType.REGULAR
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TradingCalendar:
    """A small in-memory trading calendar with exchange timezone semantics."""

    calendar_id: str
    timezone: str
    regular_open: time
    regular_close: time
    sessions_by_date: Mapping[date, CalendarSessionDefinition] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "TradingCalendar":
        regular = _mapping(config, "regular_session")
        calendar_id = _required_str(config, "calendar_id")
        timezone = _required_str(config, "timezone")
        sessions = tuple(config.get("sessions", ()))
        regular_open = _parse_time(_required_str(regular, "open"))
        regular_close = _parse_time(_required_str(regular, "close"))

        parsed_sessions: dict[date, CalendarSessionDefinition] = {}
        for raw_session in sessions:
            entry = _parse_session_definition(
                raw_session,
                regular_open=regular_open,
                regular_close=regular_close,
            )
            parsed_sessions[entry.trading_date] = entry

        return cls(
            calendar_id=calendar_id,
            timezone=timezone,
            regular_open=regular_open,
            regular_close=regular_close,
            sessions_by_date=parsed_sessions,
            metadata=dict(config.get("metadata", {})),
        )

    def session_for_date(self, trading_date: date) -> TradingSession:
        """Return the contract session record for a date, including holidays."""
        definition = self.sessions_by_date.get(
            trading_date,
            CalendarSessionDefinition(
                trading_date=trading_date,
                open_time=self.regular_open,
                close_time=self.regular_close,
            ),
        )
        return self._to_contract(definition)

    def trading_session_for_date(self, trading_date: date) -> TradingSession | None:
        """Return the tradable session for a date, or None on a holiday."""
        session = self.session_for_date(trading_date)
        if session.is_holiday:
            return None
        return session

    def configured_sessions(self) -> tuple[TradingSession, ...]:
        """Return contract sessions explicitly present in the config."""
        return tuple(
            self.session_for_date(trading_date)
            for trading_date in sorted(self.sessions_by_date)
        )

    def configured_trading_sessions(self) -> tuple[TradingSession, ...]:
        """Return non-holiday configured sessions."""
        return tuple(
            session
            for session in self.configured_sessions()
            if not session.is_holiday
        )

    def session_by_id(self, session_id: str) -> TradingSession | None:
        """Look up a session id built by this calendar."""
        prefix = f"{self.calendar_id}:"
        if not session_id.startswith(prefix):
            return None
        parts = session_id.split(":")
        if len(parts) != 3:
            return None
        try:
            trading_date = date.fromisoformat(parts[1])
            session_type = SessionType(parts[2])
        except ValueError:
            return None
        session = self.session_for_date(trading_date)
        if session.session_type != session_type:
            return None
        return session

    def session_containing_bar(
        self,
        bar_start_ts: datetime,
        bar_end_ts: datetime,
    ) -> TradingSession | None:
        """Return the session containing a complete bar interval, if any."""
        _require_aware(bar_start_ts, "bar_start_ts")
        _require_aware(bar_end_ts, "bar_end_ts")
        local_date = bar_start_ts.astimezone(self.zone).date()
        session = self.trading_session_for_date(local_date)
        if session is None:
            return None
        if session_contains_bar(session, bar_start_ts, bar_end_ts):
            return session
        return None

    def _to_contract(
        self,
        definition: CalendarSessionDefinition,
    ) -> TradingSession:
        zone = self.zone
        if definition.is_holiday:
            open_ts = datetime.combine(definition.trading_date, time(0, 0), zone)
            close_ts = open_ts
        else:
            open_time = definition.open_time or self.regular_open
            close_time = definition.close_time or self.regular_close
            open_ts = datetime.combine(definition.trading_date, open_time, zone)
            close_ts = datetime.combine(definition.trading_date, close_time, zone)

        flags = list(definition.quality_flags)
        if definition.is_holiday and HOLIDAY_QUALITY_FLAG not in flags:
            flags.append(HOLIDAY_QUALITY_FLAG)
        if definition.is_half_day and HALF_DAY_QUALITY_FLAG not in flags:
            flags.append(HALF_DAY_QUALITY_FLAG)

        return TradingSession(
            calendar_id=self.calendar_id,
            trading_date=definition.trading_date,
            session_id=build_session_id(
                self.calendar_id,
                definition.trading_date,
                definition.session_type,
            ),
            open_ts=open_ts,
            close_ts=close_ts,
            is_holiday=definition.is_holiday,
            is_half_day=definition.is_half_day,
            session_type=definition.session_type,
            timezone=self.timezone,
            quality_flags=tuple(flags),
        )


def load_calendar_config(path: str | Path) -> TradingCalendar:
    """Load a tiny JSON calendar config into a TradingCalendar."""
    config_path = Path(path)
    if config_path.suffix.lower() != ".json":
        msg = f"calendar config must be JSON: {config_path}"
        raise ValueError(msg)
    with config_path.open("r", encoding="utf-8") as handle:
        raw_config = json.load(handle)
    if not isinstance(raw_config, Mapping):
        msg = "calendar config root must be a mapping"
        raise TypeError(msg)
    return TradingCalendar.from_config(raw_config)


def _parse_session_definition(
    value: Any,
    *,
    regular_open: time,
    regular_close: time,
) -> CalendarSessionDefinition:
    if not isinstance(value, Mapping):
        msg = "session config entries must be mappings"
        raise TypeError(msg)
    trading_date = date.fromisoformat(_required_str(value, "trading_date"))
    is_holiday = bool(value.get("is_holiday", False))
    is_half_day = bool(value.get("is_half_day", False))
    session_type = SessionType(
        str(value.get("session_type", SessionType.REGULAR.value))
    )

    open_time = (
        None
        if is_holiday
        else _parse_time(str(value.get("open", regular_open)))
    )
    close_time = (
        None
        if is_holiday
        else _parse_time(str(value.get("close", regular_close)))
    )
    quality_flags = tuple(str(flag) for flag in value.get("quality_flags", ()))

    return CalendarSessionDefinition(
        trading_date=trading_date,
        open_time=open_time,
        close_time=close_time,
        is_holiday=is_holiday,
        is_half_day=is_half_day,
        session_type=session_type,
        quality_flags=quality_flags,
    )


def _required_str(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or value.strip() == "":
        msg = f"{key} must be a non-empty string"
        raise ValueError(msg)
    return value


def _mapping(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        msg = f"{key} must be a mapping"
        raise TypeError(msg)
    return value


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise ValueError(msg)
