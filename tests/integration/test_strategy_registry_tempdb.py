from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from alpha_system.core.enums import Direction
from alpha_system.strategies.spec import (
    StrategyRegistryError,
    get_strategy_version,
    register_strategy_spec,
)
from alpha_system.strategies.templates import build_single_factor_threshold_spec


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_strategy_versions_registered_in_temporary_sqlite_db(tmp_path: Path) -> None:
    registry_path = tmp_path / "strategy_registry.sqlite3"
    spec = build_single_factor_threshold_spec(
        strategy_id="threshold_strategy",
        version="v1",
        owner="research",
        factor_id="fixture_close_delta",
        factor_version="v1",
        entry_threshold=0.5,
        exit_threshold=-0.1,
        direction=Direction.LONG,
    )

    register_strategy_spec(
        registry_path,
        spec,
        data_version="data:v1",
        code_hash="a" * 64,
        config_hash="b" * 64,
    )

    with sqlite3.connect(registry_path) as connection:
        strategy_count = connection.execute(
            "SELECT count(*) FROM strategy_registry"
        ).fetchone()[0]
        version_count = connection.execute(
            "SELECT count(*) FROM strategy_versions"
        ).fetchone()[0]
    record = get_strategy_version(registry_path, "threshold_strategy", "v1")

    assert strategy_count == 1
    assert version_count == 1
    assert record is not None
    assert record.data_version == "data:v1"
    assert record.factor_versions == {"fixture_close_delta": "v1"}
    assert registry_path.exists()
    assert not _is_relative_to(registry_path.resolve(), REPO_ROOT)


def test_duplicate_strategy_version_rejected_in_temp_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "strategy_registry.sqlite3"
    spec = build_single_factor_threshold_spec(
        strategy_id="threshold_strategy",
        version="v1",
        owner="research",
        factor_id="fixture_close_delta",
        factor_version="v1",
        entry_threshold=0.5,
        exit_threshold=-0.1,
        direction=Direction.LONG,
    )

    register_strategy_spec(registry_path, spec, data_version="data:v1")

    with pytest.raises(StrategyRegistryError, match="already exists"):
        register_strategy_spec(registry_path, spec, data_version="data:v1")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
