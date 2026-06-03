from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import MISSING_DATA_FLAG, load_universe_config
from alpha_system.experiments.universe_runner import UniverseRunnerSpec, run_universe_fixture


CONFIG_PATH = Path("configs/universes/examples/tiny_multi_symbol.json")


def test_multi_symbol_tiny_fixture_records_per_instrument_missing_flag(tmp_path: Path) -> None:
    result = run_universe_fixture(
        UniverseRunnerSpec(
            run_id="multi_symbol_tiny_fixture",
            universe=load_universe_config(CONFIG_PATH),
            calendars=_calendars(),
            trading_dates=(date(2026, 1, 2),),
            bars=(
                _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York"))),
                _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 31, tzinfo=ZoneInfo("America/New_York"))),
                _bar("EQ_US_SYNTH_B", datetime(2026, 1, 2, 8, 30, tzinfo=ZoneInfo("America/Chicago"))),
            ),
            output_dir=(tmp_path / "universe").as_posix(),
        )
    )

    assert result.missing_data_flags == {"EQ_US_SYNTH_B": (MISSING_DATA_FLAG,)}


def _calendars() -> dict[str, TradingCalendar]:
    return {
        "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "America/New_York", "09:30", "09:32"),
        "EQ_US_SYNTH_B": _calendar("XCME_SYNTH", "America/Chicago", "08:30", "08:32"),
    }


def _calendar(calendar_id: str, zone: str, open_time: str, close_time: str) -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": calendar_id,
            "timezone": zone,
            "regular_session": {"open": open_time, "close": close_time},
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
