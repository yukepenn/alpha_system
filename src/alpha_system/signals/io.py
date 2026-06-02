"""Local-only signal serialization helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.signals.spec import SignalRecord
from alpha_system.signals.validation import validate_signal_records


DEFAULT_SIGNAL_STORE_ROOT = Path("/tmp/alpha_system/signals")

FORBIDDEN_SIGNAL_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".log",
)


class SignalIOError(ValueError):
    """Raised when signal I/O would violate local-only artifact policy."""


@dataclass(frozen=True, slots=True)
class SignalStoreWrite:
    output_dir: Path
    signals_path: Path
    manifest_path: Path
    record_count: int


def default_signal_store_root() -> Path:
    """Return the ignored local-only default signal store root."""
    return assert_local_wsl_path(DEFAULT_SIGNAL_STORE_ROOT)


def resolve_signal_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve and validate a local-only signal output directory."""
    candidate = assert_local_wsl_path(output_dir or default_signal_store_root())
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        msg = "signal output directories must be temp/local paths outside the repo"
        raise SignalIOError(msg)
    if candidate.suffix.lower() in FORBIDDEN_SIGNAL_SUFFIXES:
        msg = "signal output directory must not be a DB, log, or columnar artifact path"
        raise SignalIOError(msg)
    return candidate


def write_signal_records(
    records: Iterable[SignalRecord | Mapping[str, Any]],
    *,
    output_dir: str | Path | None = None,
    file_name: str = "signals.jsonl",
    manifest: Mapping[str, Any] | None = None,
    manifest_name: str = "run_manifest.json",
) -> SignalStoreWrite:
    """Write signal records and a small manifest to a temp/local JSONL store."""
    root = resolve_signal_output_dir(output_dir)
    safe_file_name = _safe_jsonl_name(file_name)
    safe_manifest_name = _safe_json_name(manifest_name)
    normalized = validate_signal_records(records)
    root.mkdir(parents=True, exist_ok=True)

    signals_path = root / safe_file_name
    _assert_signal_file_path_allowed(signals_path)
    with signals_path.open("w", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(json.dumps(record.to_dict(), sort_keys=True))
            handle.write("\n")

    manifest_path = root / safe_manifest_name
    _assert_signal_file_path_allowed(manifest_path)
    payload = {
        **dict(manifest or {}),
        "record_count": len(normalized),
        "signals_path": signals_path.as_posix(),
    }
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    manifest_path.write_text(
        json.dumps(payload, sort_keys=True, indent=2),
        encoding="utf-8",
    )

    return SignalStoreWrite(
        output_dir=root,
        signals_path=signals_path,
        manifest_path=manifest_path,
        record_count=len(normalized),
    )


def read_signal_records(path: str | Path) -> tuple[SignalRecord, ...]:
    """Read signal records from a local JSONL file."""
    input_path = assert_local_wsl_path(path)
    if input_path.suffix.lower() != ".jsonl":
        msg = "signal record files must be JSONL"
        raise SignalIOError(msg)
    records = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(SignalRecord.from_mapping(json.loads(line)))
    return tuple(records)


def _assert_signal_file_path_allowed(path: Path) -> None:
    resolved = assert_local_wsl_path(path)
    if resolved.suffix.lower() in FORBIDDEN_SIGNAL_SUFFIXES:
        msg = "signal stores must not write DB, log, Parquet, Arrow, or Feather files"
        raise SignalIOError(msg)
    repo_root = repository_root_from_module()
    if _is_relative_to(resolved, repo_root):
        msg = "signal stores must not write under committed repository paths"
        raise SignalIOError(msg)


def _safe_jsonl_name(name: str) -> str:
    safe = _safe_name(name)
    if not safe.endswith(".jsonl"):
        msg = "signal file names must end with .jsonl"
        raise SignalIOError(msg)
    return safe


def _safe_json_name(name: str) -> str:
    safe = _safe_name(name)
    if not safe.endswith(".json"):
        msg = "signal manifest file names must end with .json"
        raise SignalIOError(msg)
    return safe


def _safe_name(name: str) -> str:
    if "/" in name or "\\" in name:
        msg = "signal file names must not contain path separators"
        raise SignalIOError(msg)
    normalized = "".join(char if char.isalnum() or char in "._-" else "_" for char in name)
    normalized = normalized.strip("._-")
    if not normalized:
        msg = "signal file name must contain at least one safe character"
        raise SignalIOError(msg)
    return normalized


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
