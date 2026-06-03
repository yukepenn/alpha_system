from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid


def test_management_grid_writes_baseline_comparison_output(tmp_path: Path) -> None:
    result = run_management_grid(ManagementGridSpec.from_mapping(_payload(tmp_path)))

    rows = list(csv.DictReader(Path(result.output_paths.baseline_comparison_path).open()))

    assert rows
    assert {row["metric"] for row in rows} >= {"net_pnl", "final_equity", "total_trades", "costs"}
    assert all(row["baseline_config_id"] == "baseline_management" for row in rows)


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "baseline_comparison",
        "run_id": "management_baseline_comparison",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "max_combinations": 1,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {
                "fixed_stop.stop_pct": ["0.01"],
                "laddered_partial_take_profit.steps": [
                    [{"label": "half_at_1r", "threshold_r": "1", "exit_fraction": "0.5"}]
                ],
            },
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:baseline",
        "source_run_id": "grid_source",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "strategy_version": "strategy:v1",
        "baseline_management_config": {
            "management_id": "management:baseline",
            "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
            "eod_exit": True,
        },
        "baseline_portfolio_config": {"portfolio_id": "portfolio:baseline"},
        "source_grid_config_hash": "hash-baseline",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS_WITH_WARNINGS",
        "allowed_management_grid_scope": {
            "management_parameters": [
                "management.fixed_stop.stop_pct",
                "management.laddered_partial_take_profit.steps",
            ],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
