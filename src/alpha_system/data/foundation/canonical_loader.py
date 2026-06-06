"""Dependency-guarded loader for already-canonical local OHLCV Parquet.

This loader reads ONLY already-canonical local Parquet partitions produced by the
data layer. It never reads raw provider files, never calls providers, and never
writes inside the repository tree. Parquet reads use the optional ``polars``
dependency through ``require_dependency`` so that stdlib-only imports stay clean
and environments without ``polars`` fail closed with a clear message.

The returned rows are canonical OHLCV mapping dicts (string-typed price/volume
fields, ISO timestamp strings) that downstream feature/label engines consume as
``CanonicalBarRecord``-compatible mappings.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.data.storage import require_dependency

DEFAULT_PARTITION_SCHEMA = "ohlcv_1m"

# Canonical OHLCV mapping keys expected by the feature/label engines. Mirrors
# CanonicalBarRecord.from_mapping field set (see data/foundation/bars.py).
CANONICAL_OHLCV_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "contract_id",
    "series_id",
    "bar_start_ts",
    "bar_end_ts",
    "event_ts",
    "available_ts",
    "ingested_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "source",
    "source_request_id",
    "data_version",
    "quality_flags",
    "session_label",
)


class CanonicalLoaderError(ValueError):
    """Raised when canonical Parquet loading fails closed."""


def canonical_partition_path(
    canonical_root: str | Path,
    *,
    dataset_version_id: str,
    symbol: str,
    partition_schema: str = DEFAULT_PARTITION_SCHEMA,
    part_name: str = "part-00000.parquet",
) -> Path:
    """Resolve the canonical Parquet partition path for one symbol.

    Layout: ``<canonical_root>/<dataset_version_id>/schema=<partition_schema>/
    root=<SYMBOL>/<part_name>``.
    """

    root = assert_local_wsl_path(canonical_root)
    dsv = _require_token(dataset_version_id, "dataset_version_id")
    sym = _require_token(symbol, "symbol").upper()
    schema = _require_token(partition_schema, "partition_schema")
    return (
        root
        / dsv
        / f"schema={schema}"
        / f"root={sym}"
        / _require_token(part_name, "part_name")
    )


def load_canonical_ohlcv_rows(
    *,
    canonical_root: str | Path,
    dataset_version_id: str,
    symbol: str,
    start_ts: str | None = None,
    end_ts: str | None = None,
    partition_schema: str = DEFAULT_PARTITION_SCHEMA,
) -> tuple[dict[str, Any], ...]:
    """Load canonical OHLCV bar rows from one local Parquet partition.

    Filters rows whose ``bar_start_ts`` falls in ``[start_ts, end_ts)`` when a
    bound is supplied, normalizes ``quality_flags`` to a tuple of strings, and
    returns rows sorted by ``event_ts``. Requires the optional ``polars``
    dependency; raises ``DataDependencyError`` when it is unavailable.
    """

    polars = require_dependency("polars")
    partition_path = canonical_partition_path(
        canonical_root,
        dataset_version_id=dataset_version_id,
        symbol=symbol,
        partition_schema=partition_schema,
    )
    if not partition_path.exists():
        raise CanonicalLoaderError(
            f"canonical OHLCV partition does not exist: {partition_path.as_posix()}"
        )

    frame = polars.scan_parquet(partition_path.as_posix())
    if start_ts is not None:
        frame = frame.filter(polars.col("bar_start_ts") >= _require_token(start_ts, "start_ts"))
    if end_ts is not None:
        frame = frame.filter(polars.col("bar_start_ts") < _require_token(end_ts, "end_ts"))
    collected = frame.collect()

    rows = [_normalize_row(row) for row in collected.to_dicts()]
    rows.sort(key=lambda row: str(row.get("event_ts", "")))
    return tuple(rows)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["quality_flags"] = _normalize_quality_flags(normalized.get("quality_flags"))
    return normalized


def _normalize_quality_flags(value: object) -> tuple[str, ...]:
    """Normalize a Parquet quality_flags cell to a tuple of non-empty strings.

    Parquet stores this column as a list that may be ``None`` or ``[None]``;
    drop ``None`` entries and coerce the remainder to stripped strings.
    """

    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence):
        flags: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                flags.append(text)
        return tuple(flags)
    return ()


def _require_token(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise CanonicalLoaderError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise CanonicalLoaderError(f"{field_name} must be a non-empty string")
    return text


__all__ = [
    "CANONICAL_OHLCV_FIELDS",
    "DEFAULT_PARTITION_SCHEMA",
    "CanonicalLoaderError",
    "canonical_partition_path",
    "load_canonical_ohlcv_rows",
]
