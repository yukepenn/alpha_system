from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.experiments.management_outputs import (
    ManagementOutputError,
    resolve_management_output_dir,
    resolve_management_output_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_management_grid_outputs_may_use_temp_paths(tmp_path: Path) -> None:
    paths = resolve_management_output_paths(tmp_path / "management")

    assert Path(paths.output_dir).is_relative_to(tmp_path)
    assert Path(paths.manifest_path).suffix == ".json"


def test_management_grid_outputs_inside_repo_are_constrained() -> None:
    with pytest.raises(ManagementOutputError):
        resolve_management_output_dir(REPO_ROOT / "docs" / "management_grid_outputs")


def test_management_grid_rejects_db_like_output_path(tmp_path: Path) -> None:
    with pytest.raises(ManagementOutputError):
        resolve_management_output_dir(tmp_path / "management.sqlite3")
