from __future__ import annotations

import json
from pathlib import Path

from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid


def test_management_grid_surfaces_warnings(tmp_path: Path) -> None:
    result = run_management_grid(ManagementGridSpec.from_mapping(_payload(tmp_path)))

    warnings = json.loads(Path(result.output_paths.warnings_path).read_text(encoding="utf-8"))

    assert "small survivor sample" in warnings
    assert any("review-only research evidence" in warning for warning in warnings)


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "warnings",
        "run_id": "management_warnings",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management").as_posix(),
        "max_combinations": 1,
        "survivors": [_survivor()],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01"]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _survivor() -> dict[str, object]:
    return {
        "candidate_id": "candidate:warnings",
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
        "source_grid_config_hash": "hash-warnings",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": ["small survivor sample"],
        "review_status": "PASS_WITH_WARNINGS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
