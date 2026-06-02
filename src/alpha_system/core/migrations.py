"""SQLite migration loading and application for the metadata registry."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from alpha_system.core.hashing import hash_text


MIGRATION_TABLE = "schema_migrations"
MIGRATION_DIR = Path(__file__).with_name("migrations")


class MigrationError(RuntimeError):
    """Raised when registry migrations cannot be applied safely."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    path: Path
    sql: str
    checksum: str


def load_migrations(directory: str | Path | None = None) -> tuple[Migration, ...]:
    """Load versioned ``*.sql`` files sorted by integer prefix."""
    migration_dir = Path(directory) if directory is not None else MIGRATION_DIR
    migrations: list[Migration] = []
    if not migration_dir.exists():
        return ()

    for path in sorted(migration_dir.glob("*.sql")):
        prefix = path.name.split("_", 1)[0]
        try:
            version = int(prefix)
        except ValueError as exc:
            msg = f"migration file {path.name!r} must start with an integer prefix"
            raise MigrationError(msg) from exc
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=version,
                name=path.name,
                path=path,
                sql=sql,
                checksum=hash_text(sql),
            )
        )

    versions = [migration.version for migration in migrations]
    if len(versions) != len(set(versions)):
        msg = f"duplicate migration versions found: {versions}"
        raise MigrationError(msg)
    return tuple(migrations)


def latest_migration_version(migrations: tuple[Migration, ...] | None = None) -> int:
    loaded = load_migrations() if migrations is None else migrations
    return max((migration.version for migration in loaded), default=0)


def ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """
    )


def applied_migrations(connection: sqlite3.Connection) -> dict[int, str]:
    ensure_migration_table(connection)
    rows = connection.execute(
        f"SELECT version, checksum FROM {MIGRATION_TABLE} ORDER BY version"
    ).fetchall()
    return {int(row[0]): str(row[1]) for row in rows}


def current_schema_version(connection: sqlite3.Connection) -> int:
    ensure_migration_table(connection)
    row = connection.execute(f"SELECT max(version) FROM {MIGRATION_TABLE}").fetchone()
    return int(row[0]) if row is not None and row[0] is not None else 0


def apply_migrations(
    connection: sqlite3.Connection,
    migrations: tuple[Migration, ...] | None = None,
) -> tuple[Migration, ...]:
    """Apply pending migrations once and verify previously applied checksums."""
    loaded = load_migrations() if migrations is None else migrations
    ensure_migration_table(connection)
    applied = applied_migrations(connection)
    applied_now: list[Migration] = []

    for migration in loaded:
        existing_checksum = applied.get(migration.version)
        if existing_checksum is not None:
            if existing_checksum != migration.checksum:
                msg = (
                    f"applied migration {migration.version} checksum mismatch: "
                    f"{existing_checksum} != {migration.checksum}"
                )
                raise MigrationError(msg)
            continue

        connection.executescript(migration.sql)
        connection.execute(
            f"""
            INSERT INTO {MIGRATION_TABLE} (version, name, checksum)
            VALUES (?, ?, ?)
            """,
            (migration.version, migration.name, migration.checksum),
        )
        applied_now.append(migration)

    connection.commit()
    return tuple(applied_now)
