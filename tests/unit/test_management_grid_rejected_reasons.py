from __future__ import annotations

import csv
from pathlib import Path

from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid


def test_management_grid_rejected_reason_is_visible(tmp_path: Path) -> None:
    result = run_management_grid(ManagementGridSpec.from_mapping(_payload(tmp_path)))
    rows = list(csv.DictReader(Path(result.output_paths.rejected_configs_path).open()))

    assert result.completed_count == 0
    assert result.rejected_count == 1
    assert rows[0]["reason"] == "fixture rule rejects tight fixed stop"
    assert rows[0]["status"] == "rejected"


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "rejected_reasons",
        "run_id": "management_rejected_reasons",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "max_combinations": 1,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01"]},
            "execution": {"fixed_bps": ["1"]},
        },
        "rejection_rules": [
            {
                "when": {"management.fixed_stop.stop_pct": "0.01"},
                "reason": "fixture rule rejects tight fixed stop",
            }
        ],
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:rejected",
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
        "source_grid_config_hash": "hash-rejected",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
