from __future__ import annotations

from pathlib import Path

from alpha_system.core.migrations import apply_migrations
from alpha_system.core.registry import connect_registry, inspect_registry_status


def test_registry_migrations_are_idempotent(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"

    with connect_registry(registry_path) as connection:
        first_apply = apply_migrations(connection)
        second_apply = apply_migrations(connection)
        migration_count = connection.execute(
            "SELECT count(*) FROM schema_migrations"
        ).fetchone()[0]

    assert len(first_apply) == 1
    assert second_apply == ()
    assert migration_count == 1
    assert inspect_registry_status(registry_path).valid
