from __future__ import annotations

from pathlib import Path

from alpha_system.core.registry import SCHEMA_VERSION, init_registry


def test_registry_initializes_in_temp_database(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"

    status = init_registry(registry_path)

    assert registry_path.exists()
    assert status.valid
    assert status.schema_version == SCHEMA_VERSION
    assert status.migrations_current
    assert status.missing_tables == ()
