from __future__ import annotations

from datetime import date, timezone

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import UniverseSpec
from alpha_system.experiments.universe_runner import align_universe_sessions


def test_multi_symbol_sessions_align_by_instrument_calendar() -> None:
    universe = UniverseSpec.from_mapping(_universe_payload())
    sessions = align_universe_sessions(
        universe,
        {
            "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "America/New_York", "09:30", "09:32"),
            "EQ_US_SYNTH_B": _calendar("XCME_SYNTH", "America/Chicago", "08:30", "08:32"),
        },
        (date(2026, 1, 2),),
    )

    assert [session.instrument_id for session in sessions] == ["EQ_US_SYNTH_A", "EQ_US_SYNTH_B"]
    assert [session.session_id for session in sessions] == [
        "XNYS_SYNTH:2026-01-02:regular",
        "XCME_SYNTH:2026-01-02:regular",
    ]
    assert [session.expected_bar_count for session in sessions] == [2, 2]
    assert sessions[0].open_ts.astimezone(timezone.utc).hour == 14
    assert sessions[1].open_ts.astimezone(timezone.utc).hour == 14


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
        "universe_id": "session_alignment",
        "name": "Session Alignment",
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
                "instrument_id": "EQ_US_SYNTH_B",
                "symbol": "SYN-B",
                "asset_class": "future",
                "exchange": "XCME",
                "currency": "USD",
                "timezone": "America/Chicago",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
        ],
    }
