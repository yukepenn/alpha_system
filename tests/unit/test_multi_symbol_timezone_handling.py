from __future__ import annotations

from datetime import date, timezone

import pytest

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import UniverseSpec
from alpha_system.experiments.universe_runner import UniverseRunnerError, align_universe_sessions


def test_multi_symbol_timezone_handling_does_not_assume_one_zone() -> None:
    universe = UniverseSpec.from_mapping(_universe_payload())
    sessions = align_universe_sessions(
        universe,
        {
            "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "America/New_York", "09:30", "09:31"),
            "EQ_JP_SYNTH_A": _calendar("XTKS_SYNTH", "Asia/Tokyo", "09:00", "09:01"),
        },
        (date(2026, 1, 2),),
    )

    utc_opens = {session.instrument_id: session.open_ts.astimezone(timezone.utc) for session in sessions}
    assert utc_opens["EQ_US_SYNTH_A"].hour == 14
    assert utc_opens["EQ_JP_SYNTH_A"].hour == 0
    assert {session.timezone for session in sessions} == {"America/New_York", "Asia/Tokyo"}


def test_calendar_timezone_mismatch_is_rejected() -> None:
    universe = UniverseSpec.from_mapping(_universe_payload())

    with pytest.raises(UniverseRunnerError, match="timezone"):
        align_universe_sessions(
            universe,
            {
                "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "UTC", "09:30", "09:31"),
                "EQ_JP_SYNTH_A": _calendar("XTKS_SYNTH", "Asia/Tokyo", "09:00", "09:01"),
            },
            (date(2026, 1, 2),),
        )


def _calendar(calendar_id: str, zone: str, open_time: str, close_time: str) -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": calendar_id,
            "timezone": zone,
            "regular_session": {"open": open_time, "close": close_time},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _universe_payload() -> dict[str, object]:
    return {
        "universe_id": "timezone_handling",
        "name": "Timezone Handling",
        "data_version": "synthetic:universe:v1",
        "instruments": [
            {
                "instrument_id": "EQ_US_SYNTH_A",
                "symbol": "SYN-A",
                "asset_class": "equity",
                "exchange": "XNYS",
                "currency": "USD",
                "timezone": "America/New_York",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
            {
                "instrument_id": "EQ_JP_SYNTH_A",
                "symbol": "SYN-J",
                "asset_class": "equity",
                "exchange": "XTKS",
                "currency": "JPY",
                "timezone": "Asia/Tokyo",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
        ],
    }
