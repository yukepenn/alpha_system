from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import load_universe_config
from alpha_system.experiments.universe_runner import UniverseRunnerSpec, run_universe_fixture


CONFIG_PATH = Path("configs/universes/examples/tiny_multi_symbol.json")


def test_universe_runner_fixture_writes_temp_json_manifest(tmp_path: Path) -> None:
    result = run_universe_fixture(
        UniverseRunnerSpec(
            run_id="universe_runner_fixture",
            universe=load_universe_config(CONFIG_PATH),
            calendars=_calendars(),
            trading_dates=(date(2026, 1, 2),),
            bars=_complete_bars(),
            output_dir=(tmp_path / "universe").as_posix(),
        )
    )

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert result.registry_written is False
    assert result.missing_data_flags == {}
    assert manifest["universe_hash"] == result.universe_hash
    assert len(result.aligned_sessions) == 2
    assert sorted(path.suffix for path in Path(result.output_dir).iterdir()) == [".json", ".json"]


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
