from __future__ import annotations

import json
from pathlib import Path

from alpha_system.backtest.reference import run_reference_backtest
from tests.fixtures.backtest_reference import signal_record, synthetic_bars, zero_cost_config


def test_reference_backtest_runs_fixture_and_writes_local_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "backtest_outputs"

    result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[signal_record(0, "entry"), signal_record(1, "exit")],
        config=zero_cost_config(),
        output_dir=output_dir,
        run_manifest_path=output_dir / "manifest.json",
        run_id="integration-fixture",
    )

    assert result.summary.total_trades == 1
    assert result.output_paths is not None
    assert Path(result.output_paths.trades_path).is_file()
    assert Path(result.output_paths.equity_path).is_file()
    assert Path(result.output_paths.summary_path).is_file()
    manifest = json.loads(Path(result.output_paths.manifest_path).read_text(encoding="utf-8"))
    assert manifest["engine_version"] == "reference_1min_v1"
    assert manifest["artifact_paths"]["trades"].startswith(output_dir.as_posix())
