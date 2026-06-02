"""SQLite metadata registry connection, initialization, and status inspection."""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core import migrations


SCHEMA_VERSION = 1

REQUIRED_TABLES: tuple[str, ...] = (
    "dataset_versions",
    "factor_registry",
    "factor_versions",
    "factor_validation_runs",
    "label_versions",
    "study_runs",
    "strategy_registry",
    "strategy_versions",
    "grid_runs",
    "ml_runs",
    "backtest_runs",
    "artifact_manifest",
    "promotion_decisions",
)

EXPERIMENT_RUN_TABLES: tuple[str, ...] = (
    "factor_validation_runs",
    "study_runs",
    "grid_runs",
    "ml_runs",
    "backtest_runs",
)

REQUIRED_RUN_RECORD_COLUMNS: tuple[str, ...] = (
    "run_id",
    "timestamp",
    "git_commit",
    "git_dirty",
    "code_hash",
    "config_hash",
    "data_version",
    "factor_versions_json",
    "label_versions_json",
    "engine_version",
    "parameters_json",
    "artifact_paths_json",
    "decision_status",
    "warnings_json",
    "status_message",
)

LOCAL_SYNC_MARKERS: tuple[str, ...] = (
    "onedrive",
    "dropbox",
    "google drive",
    "googledrive",
)


@dataclass(frozen=True, slots=True)
class RegistryStatus:
    registry_path: str
    exists: bool
    local_only: bool
    schema_version: int | None
    latest_migration_version: int
    migrations_current: bool
    required_tables: dict[str, bool]
    missing_tables: tuple[str, ...]
    valid: bool
    status_message: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["missing_tables"] = list(self.missing_tables)
        return payload


def resolve_registry_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def is_local_only_registry_path(path: str | Path) -> bool:
    """Return whether a registry path avoids known synced/nonlocal locations."""
    resolved = resolve_registry_path(path)
    normalized = resolved.as_posix()
    lowered = normalized.lower()
    if normalized.startswith(("/mnt/c/", "/mnt/d/", "/mnt/e/")):
        return False
    if any(marker in lowered for marker in LOCAL_SYNC_MARKERS):
        return False
    return resolved.suffix in {".sqlite", ".sqlite3", ".db"}


def connect_registry(path: str | Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a SQLite registry connection."""
    resolved = resolve_registry_path(path)
    if read_only:
        connection = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    else:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(resolved)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_registry(path: str | Path) -> RegistryStatus:
    """Create or open a registry database and apply pending migrations."""
    resolved = resolve_registry_path(path)
    with connect_registry(resolved) as connection:
        migrations.apply_migrations(connection)
    return inspect_registry_status(resolved)


def table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return tuple(str(row["name"]) for row in rows)


def table_columns(connection: sqlite3.Connection, table_name: str) -> tuple[str, ...]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return tuple(str(row["name"]) for row in rows)


def required_table_presence(connection: sqlite3.Connection) -> dict[str, bool]:
    present = set(table_names(connection))
    return {table: table in present for table in REQUIRED_TABLES}


def missing_required_run_columns(connection: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
    missing: dict[str, tuple[str, ...]] = {}
    for table in EXPERIMENT_RUN_TABLES:
        columns = set(table_columns(connection, table))
        absent = tuple(column for column in REQUIRED_RUN_RECORD_COLUMNS if column not in columns)
        if absent:
            missing[table] = absent
    return missing


def _schema_migration_table_exists(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (migrations.MIGRATION_TABLE,),
    ).fetchone()
    return row is not None


def _read_schema_version(connection: sqlite3.Connection) -> int | None:
    if not _schema_migration_table_exists(connection):
        return None
    row = connection.execute(
        f"SELECT max(version) AS version FROM {migrations.MIGRATION_TABLE}"
    ).fetchone()
    if row is None or row["version"] is None:
        return 0
    return int(row["version"])


def inspect_registry_status(path: str | Path) -> RegistryStatus:
    """Inspect registry state without creating or migrating the database."""
    resolved = resolve_registry_path(path)
    local_only = is_local_only_registry_path(resolved)
    latest_version = migrations.latest_migration_version()
    empty_presence = {table: False for table in REQUIRED_TABLES}

    if not resolved.exists():
        return RegistryStatus(
            registry_path=resolved.as_posix(),
            exists=False,
            local_only=local_only,
            schema_version=None,
            latest_migration_version=latest_version,
            migrations_current=False,
            required_tables=empty_presence,
            missing_tables=REQUIRED_TABLES,
            valid=False,
            status_message="registry database does not exist",
            error="missing registry database",
        )

    try:
        with connect_registry(resolved, read_only=True) as connection:
            presence = required_table_presence(connection)
            missing_tables = tuple(table for table, present in presence.items() if not present)
            schema_version = _read_schema_version(connection)
    except sqlite3.Error as exc:
        return RegistryStatus(
            registry_path=resolved.as_posix(),
            exists=True,
            local_only=local_only,
            schema_version=None,
            latest_migration_version=latest_version,
            migrations_current=False,
            required_tables=empty_presence,
            missing_tables=REQUIRED_TABLES,
            valid=False,
            status_message="registry database could not be inspected",
            error=str(exc),
        )

    migrations_current = schema_version == latest_version
    problems: list[str] = []
    if not local_only:
        problems.append("registry path is not local-only")
    if not migrations_current:
        problems.append("registry migrations are not current")
    if missing_tables:
        problems.append(f"missing required tables: {', '.join(missing_tables)}")

    return RegistryStatus(
        registry_path=resolved.as_posix(),
        exists=True,
        local_only=local_only,
        schema_version=schema_version,
        latest_migration_version=latest_version,
        migrations_current=migrations_current,
        required_tables=presence,
        missing_tables=missing_tables,
        valid=not problems,
        status_message="ok" if not problems else "; ".join(problems),
        error=None if not problems else "; ".join(problems),
    )
