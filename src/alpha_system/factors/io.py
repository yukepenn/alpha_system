"""Local-only factor-value I/O helpers."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.data.bar_schema import DECIMAL_FIELDS, INT_FIELDS, REQUIRED_BAR_FIELDS
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.factors.base import FactorValue


DEFAULT_FACTOR_STORE_ROOT = Path("/tmp/alpha_system/factors")


class FactorIOError(ValueError):
    """Raised when factor I/O would violate local-only policy."""


@dataclass(frozen=True, slots=True)
class FactorStoreWrite:
    output_dir: Path
    values_path: Path
    manifest_path: Path
    record_count: int


def default_factor_store_root() -> Path:
    """Return the ignored local-only default factor store root."""
    return assert_local_wsl_path(DEFAULT_FACTOR_STORE_ROOT)


def resolve_factor_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve and validate a local-only factor output directory."""
    candidate = assert_local_wsl_path(output_dir or default_factor_store_root())
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        msg = "factor output directories must be temp/local paths outside the repo"
        raise FactorIOError(msg)
    return candidate


def read_canonical_bars(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Read tiny local canonical bars from JSONL or CSV for SDK materialization."""
    input_path = assert_local_wsl_path(path)
    if not input_path.exists():
        msg = f"canonical data path does not exist: {input_path.as_posix()}"
        raise FactorIOError(msg)
    suffix = input_path.suffix.lower()
    if suffix == ".jsonl":
        return tuple(_normalize_bar(json.loads(line)) for line in _jsonl_lines(input_path))
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            return tuple(_normalize_bar(row) for row in csv.DictReader(handle))
    msg = "canonical data path must be .jsonl or .csv for this MVP"
    raise FactorIOError(msg)


def filter_bars(
    bars: Iterable[Mapping[str, Any]],
    *,
    instrument_id: str | None = None,
    session_id: str | None = None,
    start_ts: str | datetime | None = None,
    end_ts: str | datetime | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """Filter local bars by instrument, session, and event timestamp."""
    start = None if start_ts is None else _datetime_value(start_ts, "start_ts")
    end = None if end_ts is None else _datetime_value(end_ts, "end_ts")
    selected: list[Mapping[str, Any]] = []
    for bar in bars:
        event_ts = _datetime_value(bar["event_ts"], "event_ts")
        if instrument_id is not None and str(bar["instrument_id"]) != instrument_id:
            continue
        if session_id is not None and str(bar["session_id"]) != session_id:
            continue
        if start is not None and event_ts < start:
            continue
        if end is not None and event_ts > end:
            continue
        selected.append(bar)
    return tuple(selected)


def write_factor_values(
    values: Sequence[FactorValue],
    *,
    output_dir: str | Path | None = None,
    manifest: Mapping[str, Any] | None = None,
    manifest_path: str | Path | None = None,
) -> FactorStoreWrite:
    """Write factor values and a small manifest to a temp/local JSONL store."""
    root = resolve_factor_output_dir(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    values_path = root / "factor_values.jsonl"
    values_path.write_text(
        "".join(json.dumps(value.to_dict(), sort_keys=True) + "\n" for value in values),
        encoding="utf-8",
    )

    active_manifest_path = (
        assert_local_wsl_path(manifest_path) if manifest_path is not None else root / "run_manifest.json"
    )
    write_run_manifest(
        {
            **dict(manifest or {}),
            "record_count": len(values),
            "values_path": values_path.as_posix(),
        },
        active_manifest_path,
    )
    return FactorStoreWrite(
        output_dir=root,
        values_path=values_path,
        manifest_path=active_manifest_path,
        record_count=len(values),
    )


def write_run_manifest(
    manifest: Mapping[str, Any],
    manifest_path: str | Path,
) -> Path:
    """Write a small temp/local run manifest without writing factor values."""
    output = assert_local_wsl_path(manifest_path)
    if _is_relative_to(output, repository_root_from_module()):
        msg = "factor run manifests must be temp/local paths outside the repo"
        raise FactorIOError(msg)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(manifest)
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    output.write_text(
        json.dumps(payload, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return output


def read_factor_value_dicts(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Read factor-value JSONL records as dictionaries."""
    input_path = assert_local_wsl_path(path)
    return tuple(json.loads(line) for line in _jsonl_lines(input_path))


def _jsonl_lines(path: Path) -> tuple[str, ...]:
    return tuple(line for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _normalize_bar(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = tuple(field for field in REQUIRED_BAR_FIELDS if field not in payload)
    if missing:
        msg = f"canonical bar missing required fields: {', '.join(missing)}"
        raise FactorIOError(msg)
    return {field: _normalize_bar_value(field, payload[field]) for field in REQUIRED_BAR_FIELDS}


def _normalize_bar_value(field: str, value: Any) -> Any:
    if field in DECIMAL_FIELDS:
        if value in ("", None):
            return None
        return Decimal(str(value))
    if field in INT_FIELDS:
        return int(value)
    if field in {"bar_start_ts", "bar_end_ts", "event_ts", "available_ts"}:
        return _datetime_value(value, field)
    if field == "quality_flags":
        if isinstance(value, str):
            return tuple(item for item in value.split("|") if item)
        if isinstance(value, list | tuple):
            return tuple(str(item) for item in value)
        return (str(value),)
    return str(value)


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise FactorIOError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise FactorIOError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
