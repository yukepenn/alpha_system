from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.cli.main import build_parser
from alpha_system.cli.management import run_management_grid


def test_management_grid_command_is_registered() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["management", "grid", "--help"])

    assert exc.value.code == 0


def test_management_grid_cli_executes_tiny_config_and_json(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "management_grid.json"
    config_path.write_text(json.dumps(_payload(tmp_path), sort_keys=True), encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(["management", "grid", "--config", config_path.as_posix(), "--json"])

    status = run_management_grid(args)
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["completed_count"] == 1
    assert Path(payload["output_paths"]["leaderboard_path"]).is_relative_to(tmp_path / "management")


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "cli_management",
        "run_id": "management_cli",
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
        "candidate_id": "candidate:cli",
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
        "source_grid_config_hash": "hash-cli",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "review_status": "PASS",
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "execution_parameters": ["execution.fixed_bps"],
            "max_combinations": 1,
        },
    }
