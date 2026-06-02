"""Local-only signal store abstraction."""

from __future__ import annotations

import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.signals.io import (
    SignalIOError,
    SignalStoreWrite,
    read_signal_records,
    resolve_signal_output_dir,
    write_signal_records,
)
from alpha_system.signals.spec import SignalRecord


class SignalStoreError(ValueError):
    """Raised when signal store operations violate local-only policy."""


def is_local_only_signal_store_path(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> bool:
    """Return whether a signal output root avoids committed/synced paths."""
    try:
        resolved = assert_local_wsl_path(path)
    except ValueError:
        return False
    repo = Path(repo_root or Path.cwd()).expanduser().resolve(strict=False)
    if resolved == repo or repo in resolved.parents:
        return False
    return True


class LocalSignalStore:
    """Small JSONL signal store rooted outside committed repository paths."""

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        repo_root: str | Path | None = None,
    ):
        active_root = (
            Path(tempfile.mkdtemp(prefix="alpha_system_signals_"))
            if root is None
            else Path(root)
        )
        self.repo_root = Path(repo_root or Path.cwd()).expanduser().resolve(strict=False)
        self.root = active_root.expanduser().resolve(strict=False)
        if not is_local_only_signal_store_path(self.root, repo_root=self.repo_root):
            msg = f"signal store path is not local-only: {self.root.as_posix()}"
            raise SignalStoreError(msg)
        try:
            self.root = resolve_signal_output_dir(self.root)
        except SignalIOError as exc:
            raise SignalStoreError(str(exc)) from exc
        self.root.mkdir(parents=True, exist_ok=True)

    def write_signals(
        self,
        name: str,
        signals: Iterable[SignalRecord | Mapping[str, Any]],
        *,
        manifest: Mapping[str, Any] | None = None,
    ) -> SignalStoreWrite:
        """Write validated signals below this local-only store root."""
        try:
            return write_signal_records(
                signals,
                output_dir=self.root,
                file_name=f"{_safe_name(name)}.jsonl",
                manifest=manifest,
                manifest_name=f"{_safe_name(name)}.manifest.json",
            )
        except SignalIOError as exc:
            raise SignalStoreError(str(exc)) from exc

    def read_signals(self, name_or_path: str | Path) -> tuple[SignalRecord, ...]:
        """Read signal records from this store root."""
        candidate = Path(name_or_path)
        path = candidate if candidate.suffix else self.root / f"{_safe_name(str(name_or_path))}.jsonl"
        resolved = path.expanduser().resolve(strict=False)
        if self.root not in (resolved, *resolved.parents):
            msg = "signal store reads are restricted to the configured local root"
            raise SignalStoreError(msg)
        try:
            return read_signal_records(resolved)
        except SignalIOError as exc:
            raise SignalStoreError(str(exc)) from exc


def _safe_name(name: str) -> str:
    normalized = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)
    normalized = normalized.strip("._-")
    if not normalized:
        msg = "signal store name must contain at least one safe character"
        raise SignalStoreError(msg)
    return normalized
