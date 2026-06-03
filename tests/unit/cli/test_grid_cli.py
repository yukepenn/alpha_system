from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.cli.main import build_parser
from alpha_system.cli.grid import run_grid_cli


def test_grid_command_is_registered() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["grid", "run", "--help"])
    assert exc.value.code == 0


def test_grid_cli_run_writes_to_temp_output_and_json(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "grid.json"
    config_path.write_text(json.dumps(_payload(tmp_path), sort_keys=True), encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(["grid", "run", "--config", config_path.as_posix(), "--json"])

    status = run_grid_cli(args)
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert Path(payload["output_paths"]["leaderboard_path"]).is_relative_to(tmp_path / "grid")


def _payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "cli_grid",
        "run_id": "grid_cli",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 1,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }
