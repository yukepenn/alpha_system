"""Session helpers for synthetic, contract-aligned trading calendars."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from alpha_system.data.contracts import TradingSession
from alpha_system.core.enums import SessionType


ONE_MINUTE = timedelta(minutes=1)


def build_session_id(
    calendar_id: str,
    trading_date: date,
    session_type: SessionType = SessionType.REGULAR,
) -> str:
    """Build a stable session identifier from existing contract fields."""
    return f"{calendar_id}:{trading_date.isoformat()}:{session_type.value}"


def expected_bar_count(
    session: TradingSession,
    *,
    bar_size: timedelta = ONE_MINUTE,
) -> int:
    """Return the number of complete bars expected inside a session window."""
    if session.is_holiday:
        return 0
    if session.open_ts >= session.close_ts:
        return 0
    total_seconds = (session.close_ts - session.open_ts).total_seconds()
    return int(total_seconds // bar_size.total_seconds())


def expected_bar_starts(
    session: TradingSession,
    *,
    bar_size: timedelta = ONE_MINUTE,
) -> tuple[datetime, ...]:
    """Return the deterministic expected bar-start grid for one session."""
    starts: list[datetime] = []
    current = session.open_ts
    while current + bar_size <= session.close_ts:
        starts.append(current)
        current += bar_size
    return tuple(starts)


def session_contains_bar(
    session: TradingSession,
    bar_start_ts: datetime,
    bar_end_ts: datetime,
) -> bool:
    """Return whether a complete bar interval belongs to the session."""
    if session.is_holiday:
        return False
    if bar_start_ts >= bar_end_ts:
        return False
    return session.open_ts <= bar_start_ts and bar_end_ts <= session.close_ts


def bar_index_for_start(
    session: TradingSession,
    bar_start_ts: datetime,
    *,
    bar_size: timedelta = ONE_MINUTE,
) -> int | None:
    """Return the zero-based bar index for an aligned in-session bar start."""
    bar_end_ts = bar_start_ts + bar_size
    if not session_contains_bar(session, bar_start_ts, bar_end_ts):
        return None
    elapsed = bar_start_ts - session.open_ts
    remainder = elapsed % bar_size
    if remainder != timedelta(0):
        return None
    return int(elapsed.total_seconds() // bar_size.total_seconds())


def session_metadata_available_ts(
    *,
    bar_end_ts: datetime,
    bar_available_ts: datetime,
    latency: timedelta = timedelta(0),
) -> datetime:
    """Gate bar-attached session metadata behind bar completion and latency."""
    return max(bar_available_ts, bar_end_ts + latency)


def session_close_available_ts(
    session: TradingSession,
    *,
    latency: timedelta = timedelta(0),
) -> datetime:
    """Return when close-dependent session metadata may be used."""
    return session.close_ts + latency


def session_quality_available_ts(
    session: TradingSession,
    *,
    latency: timedelta = timedelta(0),
) -> datetime:
    """Return when full-session quality summaries may be used."""
    return session_close_available_ts(session, latency=latency)
