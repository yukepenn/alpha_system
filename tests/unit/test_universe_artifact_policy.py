from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import UniverseSpec
from alpha_system.experiments.universe_runner import (
    UniverseRunnerError,
    UniverseRunnerSpec,
    resolve_universe_output_dir,
    run_universe_fixture,
)


def test_universe_runner_outputs_default_to_temp_root() -> None:
    output_dir = resolve_universe_output_dir(None, run_id="artifact_policy")

    assert Path("artifacts").resolve() not in output_dir.parents
    assert "alpha_system_universe_runs" in output_dir.as_posix()


def test_universe_runner_rejects_repository_output_roots() -> None:
    with pytest.raises(UniverseRunnerError, match="outside the repo"):
        resolve_universe_output_dir("artifacts/universe/example", run_id="blocked")


def test_universe_runner_rejects_repository_registry_path() -> None:
    with pytest.raises(UniverseRunnerError, match="temp/local path outside the repo"):
        run_universe_fixture(
            UniverseRunnerSpec(
                run_id="blocked_registry",
                universe=UniverseSpec.from_mapping(_universe_payload()),
                calendars={"EQ_US_SYNTH_A": _calendar()},
                trading_dates=(date(2026, 1, 2),),
                output_dir=None,
                registry_path="metadata/blocked.sqlite3",
            )
        )


def _calendar() -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": "XNYS_SYNTH",
            "timezone": "America/New_York",
            "regular_session": {"open": "09:30", "close": "09:31"},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _universe_payload() -> dict[str, object]:
    return {
        "universe_id": "artifact_policy",
        "name": "Artifact Policy",
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
            }
        ],
    }
