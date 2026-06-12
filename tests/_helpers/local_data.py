"""Sanctioned local-data skip helpers for tests that need private registries."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


PathResolver = str | Path | Callable[[], str | Path]
LOCAL_DATA_SKIP_PREFIX = "LOCAL DATA SKIP"


def _resolve_path(path_resolver: PathResolver) -> Path:
    raw = path_resolver() if callable(path_resolver) else path_resolver
    return Path(raw).expanduser()


def local_data_skip(path: str | Path, *, reason: str = "required local registry is absent") -> None:
    pytest.skip(f"{LOCAL_DATA_SKIP_PREFIX}: {reason}: {Path(path).expanduser()}")


def skip_unless_local_registry(
    path_resolver: PathResolver,
    *,
    reason: str = "required local registry is absent",
) -> Path:
    path = _resolve_path(path_resolver)
    if not path.exists():
        local_data_skip(path, reason=reason)
    return path
