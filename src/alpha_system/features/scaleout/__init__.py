"""Scaleout materialization orchestration for governed feature families."""

from alpha_system.features.scaleout.driver import (
    DEFAULT_SCALEOUT_CONFIG,
    MaterializedUnitEvidence,
    ScaleoutConfig,
    ScaleoutError,
    ScaleoutRunSummary,
    ScaleoutUnit,
    ScaleoutUnitRecord,
    build_scaleout_units,
    load_scaleout_config,
    materialize_base_ohlcv_unit,
    render_scaleout_summary_markdown,
    run_scaleout,
)

__all__ = [
    "MaterializedUnitEvidence",
    "DEFAULT_SCALEOUT_CONFIG",
    "ScaleoutConfig",
    "ScaleoutError",
    "ScaleoutRunSummary",
    "ScaleoutUnit",
    "ScaleoutUnitRecord",
    "build_scaleout_units",
    "load_scaleout_config",
    "materialize_base_ohlcv_unit",
    "render_scaleout_summary_markdown",
    "run_scaleout",
]
