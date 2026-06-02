from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.paths import (
    DATA_SUBDIRS,
    DataLayerPaths,
    assert_local_wsl_path,
    assert_repo_relative_path,
    fixture_data_path,
    resolve_data_subpath,
)


def test_data_layer_paths_preserve_expected_subdirectories(tmp_path: Path) -> None:
    paths = DataLayerPaths.from_repo_root(tmp_path)

    assert tuple(paths.subdir(name).name for name in DATA_SUBDIRS) == DATA_SUBDIRS
    assert paths.raw == tmp_path / "data" / "raw"
    assert paths.canonical == tmp_path / "data" / "canonical"
    assert paths.factors == tmp_path / "data" / "factors"
    assert paths.labels == tmp_path / "data" / "labels"
    assert paths.cache == tmp_path / "data" / "cache"


def test_resolve_data_subpath_requires_known_subdir(tmp_path: Path) -> None:
    resolved = resolve_data_subpath(
        "canonical",
        "bars/instrument=SYNTH-1",
        repo_root=tmp_path,
    )

    assert resolved == tmp_path / "data" / "canonical" / "bars" / "instrument=SYNTH-1"

    with pytest.raises(ValueError, match="not a supported data subdirectory"):
        resolve_data_subpath("unknown", repo_root=tmp_path)


def test_paths_reject_absolute_traversal_windows_and_synced_paths() -> None:
    with pytest.raises(ValueError, match="repo-relative"):
        assert_repo_relative_path("/home/yuke_zhang/projects/alpha_system/data/raw")
    with pytest.raises(ValueError, match="must not traverse"):
        assert_repo_relative_path("../data/raw")
    with pytest.raises(ValueError, match="local WSL2"):
        assert_local_wsl_path("/mnt/c/Users/example/data")
    with pytest.raises(ValueError, match="local WSL2"):
        assert_local_wsl_path("/home/yuke_zhang/OneDrive/data")


def test_fixture_path_is_repo_local_and_under_fixture_data(tmp_path: Path) -> None:
    path = fixture_data_path("synthetic_1min_bars.csv", repo_root=tmp_path)

    assert path == tmp_path / "tests" / "fixtures" / "data" / "synthetic_1min_bars.csv"
