from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import load_universe_config
from alpha_system.experiments.universe_runner import UniverseRunnerSpec, run_universe_fixture


CONFIG_PATH = Path("configs/universes/examples/tiny_multi_symbol.json")


def test_universe_runner_records_universe_hash_in_temp_registry(tmp_path: Path) -> None:
    universe = load_universe_config(CONFIG_PATH)
    result = run_universe_fixture(
        UniverseRunnerSpec(
            run_id="universe_registry_hash",
            universe=universe,
            calendars=_calendars(),
            trading_dates=(date(2026, 1, 2),),
            bars=_complete_bars(),
            output_dir=(tmp_path / "universe").as_posix(),
            registry_path=(tmp_path / "registry.sqlite3").as_posix(),
        )
    )

    assert result.registry_written is True
    with sqlite3.connect(tmp_path / "registry.sqlite3") as connection:
        row = connection.execute(
            """
            SELECT config_hash, parameters_json, artifact_paths_json, decision_status
            FROM study_runs
            WHERE run_id = ?
            """,
            ("universe_registry_hash",),
        ).fetchone()

    parameters = json.loads(row[1])
    assert row[0] == result.config_hash
    assert parameters["universe_hash"] == result.universe_hash
    assert parameters["universe_id"] == "tiny_multi_symbol_synthetic"
    assert "manifest_path" in json.loads(row[2])
    assert row[3] == "universe_fixture_recorded"


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


def _complete_bars() -> tuple[dict[str, object], ...]:
    return (
        _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York"))),
        _bar("EQ_US_SYNTH_A", datetime(2026, 1, 2, 9, 31, tzinfo=ZoneInfo("America/New_York"))),
        _bar("EQ_US_SYNTH_B", datetime(2026, 1, 2, 8, 30, tzinfo=ZoneInfo("America/Chicago"))),
        _bar("EQ_US_SYNTH_B", datetime(2026, 1, 2, 8, 31, tzinfo=ZoneInfo("America/Chicago"))),
    )


def _bar(instrument_id: str, start: datetime) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "bar_start_ts": start,
        "bar_end_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1),
    }
