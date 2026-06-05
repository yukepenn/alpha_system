"""Diagnostic Databento-vs-IBKR canonical OHLCV comparison.

This module intentionally does not merge sources, pick canonical truth, or
create DatasetVersions. It reads local canonical refs only and writes a curated
report under ``ALPHA_DATA_ROOT``.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import sqlite3
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.core.registry import is_local_only_registry_path
from alpha_system.data.databento.canonicalize import BBO_PARTITION_SCHEMA, OHLCV_PARTITION_SCHEMA
from alpha_system.data.foundation.serialization import json_ready as _json_ready
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.ibkr.materialize import _repo_root, _validate_data_root

SUPPORTED_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY"})
MICRO_ROOTS: frozenset[str] = frozenset({"MES", "MNQ", "M2K"})
COMPARISON_REPORT_SCHEMA = "alpha_system.databento.cross_source_comparison.v1"
IBKR_SOURCE_ID = "dsrc_ibkr_historical"


@dataclass(frozen=True, slots=True)
class _ComparableBar:
    root: str
    bar_start_ts: datetime
    session_day: str
    session_label: str
    close: Decimal
    volume: Decimal


@dataclass(frozen=True, slots=True)
class CrossSourceComparison:
    """Redacted diagnostic comparison summary."""

    status: str
    output_path: str
    databento_row_count: int
    ibkr_row_count: int
    overlapping_session_count: int
    session_summaries: tuple[Mapping[str, object], ...]
    warnings: tuple[str, ...]
    bbo_availability_note: str
    ibkr_dataset_version_ids: tuple[str, ...]
    diagnostic_only: bool
    merged_dataset_version_created: bool
    generated_at: str

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": COMPARISON_REPORT_SCHEMA,
                "status": self.status,
                "output_path": self.output_path,
                "databento_row_count": self.databento_row_count,
                "ibkr_row_count": self.ibkr_row_count,
                "overlapping_session_count": self.overlapping_session_count,
                "session_summaries": self.session_summaries,
                "warnings": self.warnings,
                "bbo_availability_note": self.bbo_availability_note,
                "ibkr_dataset_version_ids": self.ibkr_dataset_version_ids,
                "diagnostic_only": self.diagnostic_only,
                "merged_dataset_version_created": self.merged_dataset_version_created,
                "generated_at": self.generated_at,
            }
        )


def run_compare_sources(
    *,
    databento_canonical_root: str | Path,
    ibkr_registry_path: str | Path,
    ibkr_symbol_root: str | Path,
    output_path: str | Path,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> CrossSourceComparison:
    """Compare local Databento and IBKR canonical bars over overlapping days."""

    data_root = _require_data_root(env)
    databento_root = _validate_data_path(
        Path(databento_canonical_root),
        data_root=data_root,
        field_name="databento_canonical_root",
    )
    ibkr_root = _validate_data_path(
        Path(ibkr_symbol_root),
        data_root=data_root,
        field_name="ibkr_symbol_root",
    )
    registry = _validate_registry_path(Path(ibkr_registry_path))
    report_path = _validate_output_path(Path(output_path), data_root=data_root)
    generated_at = _normalize_now(now)

    warnings: list[str] = []
    ibkr_dataset_versions, registry_warnings = _load_ibkr_dataset_versions(registry)
    warnings.extend(registry_warnings)
    databento_bars, databento_skipped = _read_canonical_bars(databento_root)
    ibkr_bars, ibkr_skipped = _read_canonical_bars(ibkr_root)
    if databento_skipped:
        warnings.append(f"WARNING: skipped {databento_skipped} malformed Databento rows")
    if ibkr_skipped:
        warnings.append(f"WARNING: skipped {ibkr_skipped} malformed IBKR rows")
    if not databento_bars:
        warnings.append("WARNING: no Databento OHLCV canonical rows found")
    if not ibkr_bars:
        warnings.append("WARNING: no IBKR OHLCV canonical rows found")

    bbo_note = _bbo_availability_note(databento_root)
    session_summaries, comparison_warnings = _compare_sessions(databento_bars, ibkr_bars)
    warnings.extend(comparison_warnings)
    if not session_summaries:
        status = "NO_OVERLAP"
        warnings.append("WARNING: no overlapping Databento/IBKR sessions or days found")
    else:
        status = "COMPARED_WITH_WARNINGS" if warnings else "COMPARED"

    summary = CrossSourceComparison(
        status=status,
        output_path=report_path.as_posix(),
        databento_row_count=len(databento_bars),
        ibkr_row_count=len(ibkr_bars),
        overlapping_session_count=len(session_summaries),
        session_summaries=session_summaries,
        warnings=tuple(warnings),
        bbo_availability_note=bbo_note,
        ibkr_dataset_version_ids=ibkr_dataset_versions,
        diagnostic_only=True,
        merged_dataset_version_created=False,
        generated_at=generated_at.isoformat(),
    )
    _write_report(report_path, summary)
    return summary


def _require_data_root(env: Mapping[str, str] | None) -> Path:
    source = os.environ if env is None else env
    value = source.get("ALPHA_DATA_ROOT")
    if value is None or not value.strip():
        msg = "ALPHA_DATA_ROOT is required for Databento cross-source comparison"
        raise DataFoundationValidationError(msg)
    return _validate_data_root(Path(value), _repo_root())


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_data_path(path: Path, *, data_root: Path, field_name: str) -> Path:
    resolved = _validate_data_root(path, _repo_root())
    if resolved != data_root and not _is_relative_to(resolved, data_root):
        msg = f"{field_name} must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    local_probe = (resolved if resolved.suffix == "" else resolved.parent) / "compare_probe.sqlite3"
    if not is_local_only_registry_path(local_probe):
        msg = f"{field_name} is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _validate_registry_path(path: Path) -> Path:
    resolved = _validate_data_root(path, _repo_root())
    if not is_local_only_registry_path(resolved):
        msg = f"ibkr_registry_path is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _validate_output_path(path: Path, *, data_root: Path) -> Path:
    resolved = _validate_data_root(path, _repo_root())
    if resolved.parent != data_root and not _is_relative_to(resolved.parent, data_root):
        msg = "output_path must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    local_probe = resolved.parent / "compare_report_probe.sqlite3"
    if not is_local_only_registry_path(local_probe):
        msg = f"output_path is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _normalize_now(now: datetime | None) -> datetime:
    active = now or datetime.now(UTC)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return active.astimezone(UTC).replace(microsecond=0)


def _load_ibkr_dataset_versions(registry_path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not registry_path.exists():
        return (), (f"WARNING: IBKR registry does not exist: {registry_path.as_posix()}",)
    try:
        connection = sqlite3.connect(f"file:{registry_path.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        return (), (f"WARNING: IBKR registry could not be opened read-only: {exc}",)
    with connection:
        connection.row_factory = sqlite3.Row
        table = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'dataset_versions'
            """
        ).fetchone()
        if table is None:
            return (), ("WARNING: IBKR registry has no dataset_versions table",)
        rows = connection.execute(
            """
            SELECT data_version, source_uri, metadata_json
            FROM dataset_versions
            ORDER BY data_version
            """
        ).fetchall()

    ids: list[str] = []
    for row in rows:
        source = str(row["source_uri"])
        if source == IBKR_SOURCE_ID:
            ids.append(str(row["data_version"]))
            continue
        try:
            payload = json.loads(str(row["metadata_json"]))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, Mapping):
            continue
        values = payload.get("dataset_version")
        if isinstance(values, Mapping) and values.get("source") == IBKR_SOURCE_ID:
            ids.append(str(row["data_version"]))
    warnings: tuple[str, ...] = ()
    if not ids:
        warnings = ("WARNING: no IBKR DatasetVersion rows found in registry",)
    return tuple(ids), warnings


def _read_canonical_bars(root: Path) -> tuple[tuple[_ComparableBar, ...], int]:
    if not root.exists():
        return (), 0
    bars: list[_ComparableBar] = []
    skipped = 0
    for path in _canonical_files(root):
        for row in _read_rows(path):
            try:
                bars.append(_bar_from_row(row))
            except DataFoundationValidationError:
                skipped += 1
    return tuple(sorted(bars, key=lambda bar: (bar.root, bar.bar_start_ts))), skipped


def _canonical_files(root: Path) -> tuple[Path, ...]:
    if root.is_file():
        return (root,) if _supported_data_file(root) else ()
    preferred = tuple(
        sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and _supported_data_file(path)
            and _path_has_schema(path, OHLCV_PARTITION_SCHEMA)
        )
    )
    if preferred:
        return preferred
    return tuple(
        sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and _supported_data_file(path)
            and not _path_has_schema(path, BBO_PARTITION_SCHEMA)
            and path.name != "manifest.json"
        )
    )


def _supported_data_file(path: Path) -> bool:
    return path.suffix.lower() in {".jsonl", ".json", ".csv", ".parquet"}


def _path_has_schema(path: Path, schema: str) -> bool:
    return any(part == f"schema={schema}" for part in path.parts)


def _read_rows(path: Path) -> tuple[Mapping[str, object], ...]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _read_jsonl(path)
    if suffix == ".json":
        return _read_json(path)
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".parquet":
        return _read_parquet(path)
    return ()


def _read_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, Mapping):
                rows.append(MappingProxyType(dict(payload)))
    return tuple(rows)


def _read_json(path: Path) -> tuple[Mapping[str, object], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return tuple(MappingProxyType(dict(row)) for row in payload if isinstance(row, Mapping))
    if isinstance(payload, Mapping):
        records = payload.get("records")
        if isinstance(records, list):
            return tuple(
                MappingProxyType(dict(row)) for row in records if isinstance(row, Mapping)
            )
        if "bar_start_ts" in payload and "close" in payload:
            return (MappingProxyType(dict(payload)),)
    return ()


def _read_csv(path: Path) -> tuple[Mapping[str, object], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(MappingProxyType(dict(row)) for row in csv.DictReader(handle))


def _read_parquet(path: Path) -> tuple[Mapping[str, object], ...]:
    pyarrow = _optional_module("pyarrow")
    if pyarrow is not None:
        parquet = importlib.import_module("pyarrow.parquet")
        return tuple(parquet.read_table(path).to_pylist())
    polars = _optional_module("polars")
    if polars is not None:
        return tuple(polars.read_parquet(path.as_posix()).to_dicts())
    msg = f"cannot read Parquet without pyarrow or polars: {path.as_posix()}"
    raise DataFoundationValidationError(msg)


def _optional_module(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise


def _bar_from_row(row: Mapping[str, object]) -> _ComparableBar:
    root = _row_root(row)
    if root is None:
        msg = "canonical row does not resolve to ES/NQ/RTY"
        raise DataFoundationValidationError(msg)
    bar_start = _parse_timestamp(_first(row, ("bar_start_ts", "provider_ts", "timestamp")))
    close = _decimal_value(row.get("close"), "close")
    volume = _decimal_value(row.get("volume", 0), "volume")
    return _ComparableBar(
        root=root,
        bar_start_ts=bar_start,
        session_day=_session_day(row, bar_start),
        session_label=_session_label(row),
        close=close,
        volume=volume,
    )


def _row_root(row: Mapping[str, object]) -> str | None:
    for field_name in (
        "symbol",
        "root",
        "instrument_id",
        "contract_id",
        "series_id",
        "raw_symbol",
    ):
        value = row.get(field_name)
        if value is None:
            continue
        root = _supported_root_from_text(str(value))
        if root is not None:
            return root
    return None


def _supported_root_from_text(value: str) -> str | None:
    normalized = value.strip().upper()
    if not normalized:
        return None
    first = normalized.replace(".", " ").replace("_", " ").replace("-", " ").split()[0]
    if first in MICRO_ROOTS:
        return None
    if first in SUPPORTED_ROOTS:
        return first
    compact = "".join(char for char in normalized if char.isalnum())
    if any(compact.startswith(root) for root in MICRO_ROOTS):
        return None
    for root in ("RTY", "NQ", "ES"):
        if compact.startswith(root):
            return root
    lowered = normalized.lower()
    for root in ("rty", "nq", "es"):
        if f"_{root}" in lowered or f"-{root}" in lowered:
            return root.upper()
    return None


def _first(row: Mapping[str, object], names: Sequence[str]) -> object | None:
    for name in names:
        value = row.get(name)
        if value is not None:
            return value
    return None


def _parse_timestamp(value: object) -> datetime:
    if value is None:
        msg = "canonical row missing timestamp"
        raise DataFoundationValidationError(msg)
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        value = to_pydatetime()
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, int) and not isinstance(value, bool):
        seconds, nanoseconds = divmod(value, 1_000_000_000)
        parsed = datetime.fromtimestamp(seconds, UTC).replace(microsecond=nanoseconds // 1000)
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            msg = "canonical timestamp must be ISO-8601 or UTC ns integer"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = "canonical timestamp must be ISO-8601 or UTC ns integer"
        raise DataFoundationValidationError(msg)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "canonical timestamp must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed.astimezone(UTC)


def _decimal_value(value: object, field_name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        msg = f"{field_name} must be a finite decimal"
        raise DataFoundationValidationError(msg)
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be a finite decimal"
        raise DataFoundationValidationError(msg) from exc
    if not parsed.is_finite():
        msg = f"{field_name} must be finite"
        raise DataFoundationValidationError(msg)
    return parsed


def _session_day(row: Mapping[str, object], bar_start: datetime) -> str:
    for field_name in ("session_date", "trading_date"):
        value = row.get(field_name)
        if value is not None and str(value).strip():
            return str(value).strip()[:10]
    return bar_start.date().isoformat()


def _session_label(row: Mapping[str, object]) -> str:
    value = row.get("session_label")
    if value is None or not str(value).strip():
        return "UNKNOWN"
    return str(value).strip().upper()


def _bbo_availability_note(databento_root: Path) -> str:
    has_bbo = databento_root.exists() and any(
        path.is_file() and _path_has_schema(path, BBO_PARTITION_SCHEMA)
        for path in databento_root.rglob("*")
    )
    if has_bbo:
        return (
            "Databento-only BBO-1m companion rows are present; this report compares "
            "OHLCV/TRADES bars and does not merge sources."
        )
    return (
        "Databento-only BBO-1m companion rows were not detected in the supplied root; "
        "this report compares OHLCV/TRADES bars and does not merge sources."
    )


def _compare_sessions(
    databento_bars: Sequence[_ComparableBar],
    ibkr_bars: Sequence[_ComparableBar],
) -> tuple[tuple[Mapping[str, object], ...], tuple[str, ...]]:
    databento_groups = _group_by_session(databento_bars)
    ibkr_groups = _group_by_session(ibkr_bars)
    summaries: list[Mapping[str, object]] = []
    warnings: list[str] = []
    for key in sorted(set(databento_groups) & set(ibkr_groups)):
        databento_map = databento_groups[key]
        ibkr_map = ibkr_groups[key]
        summary = _session_summary(key, databento_map, ibkr_map)
        summaries.append(summary)
        missing_total = int(summary["missing_in_databento_count"]) + int(
            summary["missing_in_ibkr_count"]
        )
        if missing_total:
            warnings.append(
                "WARNING: timestamp coverage differs for "
                f"{summary['root']} {summary['session_day']} {summary['session_label']}"
            )
        max_diff = summary["max_abs_close_diff"]
        if max_diff is not None and Decimal(str(max_diff)) != Decimal("0"):
            warnings.append(
                "WARNING: close prices differ for "
                f"{summary['root']} {summary['session_day']} {summary['session_label']}"
            )
        volume_diff = Decimal(str(summary["volume_difference"]))
        if volume_diff != Decimal("0"):
            warnings.append(
                "WARNING: volumes differ for "
                f"{summary['root']} {summary['session_day']} {summary['session_label']}"
            )
    return tuple(summaries), tuple(warnings)


def _group_by_session(
    bars: Sequence[_ComparableBar],
) -> Mapping[tuple[str, str, str], Mapping[datetime, _ComparableBar]]:
    grouped: dict[tuple[str, str, str], dict[datetime, _ComparableBar]] = defaultdict(dict)
    for bar in bars:
        grouped[(bar.root, bar.session_day, bar.session_label)][bar.bar_start_ts] = bar
    return MappingProxyType(
        {key: MappingProxyType(value) for key, value in sorted(grouped.items())}
    )


def _session_summary(
    key: tuple[str, str, str],
    databento_map: Mapping[datetime, _ComparableBar],
    ibkr_map: Mapping[datetime, _ComparableBar],
) -> Mapping[str, object]:
    root, session_day, session_label = key
    databento_times = set(databento_map)
    ibkr_times = set(ibkr_map)
    aligned_times = tuple(sorted(databento_times & ibkr_times))
    missing_in_databento = tuple(sorted(ibkr_times - databento_times))
    missing_in_ibkr = tuple(sorted(databento_times - ibkr_times))
    close_diffs = tuple(abs(databento_map[ts].close - ibkr_map[ts].close) for ts in aligned_times)
    databento_volume = sum((bar.volume for bar in databento_map.values()), Decimal("0"))
    ibkr_volume = sum((bar.volume for bar in ibkr_map.values()), Decimal("0"))
    volume_difference = databento_volume - ibkr_volume
    return MappingProxyType(
        {
            "root": root,
            "session_day": session_day,
            "session_label": session_label,
            "databento_interval_count": len(databento_times),
            "ibkr_interval_count": len(ibkr_times),
            "overlapping_interval_count": len(aligned_times),
            "mean_abs_close_diff": _decimal_or_none(_mean(close_diffs)),
            "max_abs_close_diff": _decimal_or_none(max(close_diffs) if close_diffs else None),
            "close_correlation": _correlation(
                [databento_map[ts].close for ts in aligned_times],
                [ibkr_map[ts].close for ts in aligned_times],
            ),
            "databento_volume": str(databento_volume),
            "ibkr_volume": str(ibkr_volume),
            "volume_difference": str(volume_difference),
            "missing_in_databento_count": len(missing_in_databento),
            "missing_in_ibkr_count": len(missing_in_ibkr),
            "missing_in_databento_sample": tuple(
                ts.isoformat() for ts in missing_in_databento[:25]
            ),
            "missing_in_ibkr_sample": tuple(ts.isoformat() for ts in missing_in_ibkr[:25]),
        }
    )


def _mean(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def _decimal_or_none(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _correlation(xs: Sequence[Decimal], ys: Sequence[Decimal]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_values = [float(value) for value in xs]
    y_values = [float(value) for value in ys]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_denominator = sum((x - x_mean) ** 2 for x in x_values)
    y_denominator = sum((y - y_mean) ** 2 for y in y_values)
    denominator = (x_denominator * y_denominator) ** 0.5
    if denominator == 0:
        return None
    return numerator / denominator


def _write_report(path: Path, summary: CrossSourceComparison) -> None:
    if path.suffix.lower() == ".md":
        _write_markdown_report(path, summary)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_json_ready(summary.to_mapping()), handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_markdown_report(path: Path, summary: CrossSourceComparison) -> None:
    lines = [
        "# Databento / IBKR Cross-Source Comparison",
        "",
        f"Status: {summary.status}",
        f"Generated at: {summary.generated_at}",
        "",
        "Diagnostic only: true",
        "Merged DatasetVersion created: false",
        "",
        f"Databento rows: {summary.databento_row_count}",
        f"IBKR rows: {summary.ibkr_row_count}",
        f"Overlapping sessions/days: {summary.overlapping_session_count}",
        "",
        f"BBO note: {summary.bbo_availability_note}",
        "",
        "## Warnings",
    ]
    lines.extend(f"- {warning}" for warning in summary.warnings)
    if not summary.warnings:
        lines.append("- None")
    lines.extend(["", "## Session Summaries"])
    for item in summary.session_summaries:
        lines.append(
            "- "
            f"{item['root']} {item['session_day']} {item['session_label']}: "
            f"overlap={item['overlapping_interval_count']}, "
            f"mean_abs_close_diff={item['mean_abs_close_diff']}, "
            f"max_abs_close_diff={item['max_abs_close_diff']}, "
            f"volume_difference={item['volume_difference']}"
        )
    if not summary.session_summaries:
        lines.append("- No overlap")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare local Databento and IBKR canonical OHLCV refs",
    )
    parser.add_argument("--databento-canonical-root", type=Path, required=True)
    parser.add_argument("--ibkr-registry-path", type=Path, required=True)
    parser.add_argument("--ibkr-symbol-root", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    return parser.parse_args(argv)


def _print_summary(summary: CrossSourceComparison) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.compare_sources``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_compare_sources(
            databento_canonical_root=args.databento_canonical_root,
            ibkr_registry_path=args.ibkr_registry_path,
            ibkr_symbol_root=args.ibkr_symbol_root,
            output_path=args.output,
        )
    except DataFoundationValidationError as exc:
        print(f"compare_sources blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0 if summary.status != "NO_OVERLAP" else 1


__all__ = ["CrossSourceComparison", "run_compare_sources"]


if __name__ == "__main__":
    raise SystemExit(main())
