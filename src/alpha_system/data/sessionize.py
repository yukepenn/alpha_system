"""Pure in-memory session assignment for canonical 1-minute bar rows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from typing import Any

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.quality import OUT_OF_SESSION_FLAG, add_quality_flags
from alpha_system.data.sessions import (
    bar_index_for_start,
    expected_bar_count,
    session_close_available_ts,
    session_metadata_available_ts,
)


def sessionize_bars(
    rows: Iterable[Mapping[str, Any]],
    calendar: TradingCalendar,
    *,
    available_latency: timedelta = timedelta(0),
    validate_existing_keys: bool = True,
) -> tuple[dict[str, Any], ...]:
    """Assign rows to sessions and compute per-session bar_index values.

    The transform is deterministic, in-memory, and returns copied records. Bars
    outside a tradable session remain present with an out-of-session flag.
    """
    return tuple(
        _sessionize_row(
            row,
            calendar,
            available_latency=available_latency,
            validate_existing_keys=validate_existing_keys,
        )
        for row in rows
    )


def _sessionize_row(
    row: Mapping[str, Any],
    calendar: TradingCalendar,
    *,
    available_latency: timedelta,
    validate_existing_keys: bool,
) -> dict[str, Any]:
    start = row.get("bar_start_ts")
    end = row.get("bar_end_ts")
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return _out_of_session_row(row, calendar=calendar, start=start, end=end)

    session = calendar.session_containing_bar(start, end)
    if session is None:
        return _out_of_session_row(row, calendar=calendar, start=start, end=end)

    bar_index = bar_index_for_start(session, start)
    if bar_index is None:
        return _out_of_session_row(row, calendar=calendar, start=start, end=end)

    if validate_existing_keys:
        _validate_existing_session_key(row, session.session_id, bar_index)

    out = dict(row)
    out["session_id"] = session.session_id
    out["bar_index"] = bar_index
    out["calendar_id"] = session.calendar_id
    out["trading_date"] = session.trading_date
    out["session_open_ts"] = session.open_ts
    out["session_close_ts"] = session.close_ts
    out["is_holiday"] = session.is_holiday
    out["is_half_day"] = session.is_half_day
    out["session_type"] = session.session_type.value
    out["timezone"] = session.timezone
    out["expected_bar_count"] = expected_bar_count(session)

    available = row.get("available_ts")
    if isinstance(available, datetime):
        out["session_metadata_available_ts"] = session_metadata_available_ts(
            bar_end_ts=end,
            bar_available_ts=available,
            latency=available_latency,
        )
    else:
        out["session_metadata_available_ts"] = end + available_latency
    out["session_close_available_ts"] = session_close_available_ts(
        session,
        latency=available_latency,
    )
    return out


def _out_of_session_row(
    row: Mapping[str, Any],
    *,
    calendar: TradingCalendar,
    start: Any,
    end: Any,
) -> dict[str, Any]:
    out = add_quality_flags(row, OUT_OF_SESSION_FLAG)
    out["session_id"] = ""
    out["bar_index"] = -1
    out["calendar_id"] = calendar.calendar_id
    if isinstance(start, datetime):
        out["trading_date"] = start.astimezone(calendar.zone).date()
    out["session_open_ts"] = None
    out["session_close_ts"] = None
    out["is_holiday"] = False
    out["is_half_day"] = False
    out["session_type"] = None
    out["timezone"] = calendar.timezone
    out["expected_bar_count"] = 0
    if isinstance(end, datetime):
        out["session_metadata_available_ts"] = end
    return out


def _validate_existing_session_key(
    row: Mapping[str, Any],
    derived_session_id: str,
    derived_bar_index: int,
) -> None:
    existing_session_id = row.get("session_id")
    if existing_session_id not in (None, "", derived_session_id):
        msg = (
            f"existing session_id {existing_session_id!r} does not match "
            f"derived session_id {derived_session_id!r}"
        )
        raise ValueError(msg)

    existing_bar_index = row.get("bar_index")
    if existing_bar_index not in (None, -1, derived_bar_index):
        msg = (
            f"existing bar_index {existing_bar_index!r} does not match "
            f"derived bar_index {derived_bar_index!r}"
        )
        raise ValueError(msg)
