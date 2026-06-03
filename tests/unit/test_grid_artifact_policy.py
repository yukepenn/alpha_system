from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.experiments.grid_outputs import GridOutputError, resolve_grid_output_dir


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_grid_default_output_root_is_strategy_grid_artifact_root() -> None:
    output_dir = resolve_grid_output_dir(None)

    assert output_dir.is_relative_to(REPO_ROOT / "artifacts" / "strategy_grids")


def test_grid_output_policy_rejects_other_repo_dirs_and_db_suffix(tmp_path: Path) -> None:
    with pytest.raises(GridOutputError, match="artifacts/strategy_grids"):
        resolve_grid_output_dir(REPO_ROOT / "docs" / "bad_grid_output")

    with pytest.raises(GridOutputError, match="must not be a DB"):
        resolve_grid_output_dir(tmp_path / "grid.sqlite")
