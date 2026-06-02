"""Local DuckDB and Polars query helpers over tiny fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.data.storage import require_dependency


def _quote_identifier(identifier: str) -> str:
    if not identifier.replace("_", "").isalnum() or identifier[0].isdigit():
        msg = f"{identifier!r} is not a simple SQL identifier"
        raise ValueError(msg)
    return f'"{identifier}"'


def _quote_sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def query_csv_with_duckdb(
    csv_path: str | Path,
    sql: str,
    *,
    table_name: str = "bars",
) -> tuple[dict[str, Any], ...]:
    """Run local DuckDB SQL over a tiny CSV fixture."""
    duckdb = require_dependency("duckdb")
    fixture_path = assert_local_wsl_path(csv_path)
    quoted_table = _quote_identifier(table_name)
    quoted_path = _quote_sql_path(fixture_path)
    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            f"""
            CREATE VIEW {quoted_table} AS
            SELECT * FROM read_csv_auto('{quoted_path}', header = true)
            """
        )
        cursor = connection.execute(sql)
        columns = tuple(column[0] for column in cursor.description)
        return tuple(dict(zip(columns, row, strict=True)) for row in cursor.fetchall())
    finally:
        connection.close()


def query_parquet_with_duckdb(
    parquet_path: str | Path,
    sql: str,
    *,
    table_name: str = "bars",
) -> tuple[dict[str, Any], ...]:
    """Run local DuckDB SQL over a local Parquet file."""
    duckdb = require_dependency("duckdb")
    fixture_path = assert_local_wsl_path(parquet_path)
    quoted_table = _quote_identifier(table_name)
    quoted_path = _quote_sql_path(fixture_path)
    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            f"""
            CREATE VIEW {quoted_table} AS
            SELECT * FROM read_parquet('{quoted_path}')
            """
        )
        cursor = connection.execute(sql)
        columns = tuple(column[0] for column in cursor.description)
        return tuple(dict(zip(columns, row, strict=True)) for row in cursor.fetchall())
    finally:
        connection.close()


def scan_csv_lazy_with_polars(csv_path: str | Path) -> Any:
    """Return a Polars lazy scan over a tiny CSV fixture."""
    polars = require_dependency("polars")
    return polars.scan_csv(assert_local_wsl_path(csv_path).as_posix())


def polars_fixture_close_summary(csv_path: str | Path) -> tuple[dict[str, Any], ...]:
    """Build a tiny lazy Polars summary over deterministic fixture rows."""
    polars = require_dependency("polars")
    lazy_frame = scan_csv_lazy_with_polars(csv_path)
    result = (
        lazy_frame.with_columns(polars.col("close").cast(polars.Float64))
        .group_by("instrument_id")
        .agg(
            polars.len().alias("bar_count"),
            polars.col("close").mean().alias("mean_close"),
        )
        .collect()
    )
    return tuple(result.to_dicts())
