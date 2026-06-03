from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import MISSING_DATA_FLAG, UniverseSpec
from alpha_system.experiments.universe_runner import align_universe_sessions, per_symbol_missing_data_flags


def test_per_symbol_missing_data_flags_are_recorded() -> None:
    universe = UniverseSpec.from_mapping(_universe_payload())
    sessions = align_universe_sessions(
        universe,
        {
            "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "America/New_York"),
            "EQ_US_SYNTH_B": _calendar("XCME_SYNTH", "America/Chicago"),
        },
        (date(2026, 1, 2),),
    )
    bars = (
        _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York"))),
        _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 31, tzinfo=ZoneInfo("America/New_York"))),
        _bar("EQ_US_SYNTH_B", datetime(2026, 1, 2, 8, 30, tzinfo=ZoneInfo("America/Chicago"))),
    )

    flags = per_symbol_missing_data_flags(bars, sessions)

    assert flags == {"EQ_US_SYNTH_B": (MISSING_DATA_FLAG,)}


def _calendar(calendar_id: str, zone: str) -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": calendar_id,
            "timezone": zone,
            "regular_session": {"open": "09:30" if zone == "America/New_York" else "08:30", "close": "09:32" if zone == "America/New_York" else "08:32"},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _bar(instrument_id: str, start: datetime) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "bar_start_ts": start,
        "bar_end_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1),
    }


def _universe_payload() -> dict[str, object]:
    return {
        "universe_id": "missing_flags",
        "name": "Missing Flags",
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
                "asset_class": "equity",
                "exchange": "XCME",
                "currency": "USD",
                "timezone": "America/Chicago",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
        ],
    }
