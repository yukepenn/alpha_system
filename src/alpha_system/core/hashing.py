"""Deterministic hashing helpers for registry metadata."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


def _normalize_for_json(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize_for_json(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_for_json(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, set | frozenset):
        return sorted((_normalize_for_json(item) for item in value), key=repr)
    if isinstance(value, tuple | list):
        return [_normalize_for_json(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    """Serialize a Python value into stable JSON for hashing and storage."""
    normalized = _normalize_for_json(value)
    return json.dumps(
        normalized,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_hex(payload: bytes) -> str:
    """Return a SHA-256 hex digest for raw bytes."""
    return hashlib.sha256(payload).hexdigest()


def hash_text(text: str) -> str:
    """Return a SHA-256 hash for UTF-8 text."""
    return sha256_hex(text.encode("utf-8"))


def hash_config(config: Any) -> str:
    """Return a deterministic hash for JSON-like configuration data."""
    return hash_text(canonical_json(config))


def hash_file(path: str | Path) -> str:
    """Return a SHA-256 hash for a single file."""
    file_path = Path(path)
    return sha256_hex(file_path.read_bytes())


def hash_code_paths(paths: Iterable[str | Path], *, root: str | Path | None = None) -> str:
    """Hash a stable manifest of file paths and file contents."""
    root_path = Path(root).resolve() if root is not None else None
    entries: list[tuple[str, str]] = []
    for path in paths:
        file_path = Path(path)
        resolved = file_path.resolve()
        if root_path is None:
            display_path = file_path.as_posix()
        else:
            display_path = resolved.relative_to(root_path).as_posix()
        entries.append((display_path, hash_file(resolved)))
    return hash_config(entries)
