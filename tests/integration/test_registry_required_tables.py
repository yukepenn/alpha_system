from __future__ import annotations

from pathlib import Path

from alpha_system.core.registry import REQUIRED_TABLES, connect_registry, init_registry, table_names


def test_registry_required_tables_exist(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    with connect_registry(registry_path, read_only=True) as connection:
        present = set(table_names(connection))

    assert set(REQUIRED_TABLES).issubset(present)
    assert len(REQUIRED_TABLES) == 13
