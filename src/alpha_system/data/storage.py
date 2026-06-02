"""Local fixture and Parquet storage helpers."""

from __future__ import annotations

import importlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from alpha_system.data.build_bars import load_csv_bar_fixture, normalize_bar_rows
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.data.validation import BarValidationConfig


class DataDependencyError(RuntimeError):
    """Raised when an optional local analytical dependency is unavailable."""


def require_dependency(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        msg = (
            f"{module_name} is required for this local data-layer operation; "
            "install the project data dependencies in the execution environment"
        )
        raise DataDependencyError(msg) from exc


def dependency_available(module_name: str) -> bool:
    try:
        require_dependency(module_name)
    except DataDependencyError:
        return False
    return True


def read_csv_fixture_bars(
    path: str | Path,
    *,
    validation_config: BarValidationConfig | None = None,
) -> tuple[dict[str, Any], ...]:
    """Read a tiny synthetic CSV fixture into normalized canonical rows."""
    return load_csv_bar_fixture(
        assert_local_wsl_path(path),
        validation_config=validation_config,
    )


def read_parquet_bars(path: str | Path) -> Any:
    """Read local Parquet bars with Polars when that dependency is installed."""
    polars = require_dependency("polars")
    return polars.read_parquet(assert_local_wsl_path(path).as_posix())


def write_parquet_bars(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    *,
    validation_config: BarValidationConfig | None = None,
) -> Path:
    """Write normalized bars to a local Parquet file with Polars."""
    polars = require_dependency("polars")
    output_path = assert_local_wsl_path(path)
    normalized = normalize_bar_rows(
        rows,
        validation_config=validation_config,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    polars.DataFrame(list(normalized)).write_parquet(output_path.as_posix())
    return output_path
