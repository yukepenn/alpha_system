from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars, zero_cost_config


def test_backtest_run_records_existing_registry_table_in_tempdb(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    output_dir = tmp_path / "outputs"

    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=zero_cost_config(),
        output_dir=output_dir,
        registry_path=registry_path,
        run_id="registry-fixture",
        repo_root=Path.cwd(),
    )

    assert result.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        row = connection.execute(
            """
            SELECT
                run_id,
                engine_version,
                data_version,
                factor_versions_json,
                parameters_json,
                artifact_paths_json,
                decision_status
            FROM backtest_runs
            """
        ).fetchone()

    assert row[0] == "registry-fixture"
    assert row[1] == "reference_1min_v1"
    assert row[2] == "data:v1"
    assert json.loads(row[3]) == {"fixture_factor": "v1"}
    assert json.loads(row[4])["execution_timing"] == "next_bar_conservative"
    assert "trades_path" in json.loads(row[5])
    assert row[6] == "reference_recorded"
