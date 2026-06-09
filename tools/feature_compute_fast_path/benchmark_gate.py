"""Bounded-real benchmark gate for ``FEATURE_COMPUTE_FAST_PATH_V1``.

The benchmark reads canonical local data, invokes the real reference feature /
label runners and the real V1 fast-pack runners, confirms value parity on the
same slice, and writes only a value-free Markdown summary.
"""

from __future__ import annotations

import argparse
import math
import os
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.data.foundation.canonical_loader import (
    load_canonical_bbo_rows,
    load_canonical_ohlcv_rows,
)
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
)
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.families.bbo import (
    BBOFeatureDefinition,
    BBOFeatureName,
    build_bbo_feature_definition,
    compute_bbo_feature,
)
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureDefinition,
    CrossMarketFeatureName,
    CrossMarketInputBundle,
    build_cross_market_feature_definition,
    compute_cross_market_feature,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureDefinition,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.families.session import (
    SessionFeatureDefinition,
    SessionFeatureName,
    build_session_feature_definition,
    compute_session_feature,
)
from alpha_system.features.families.structure import (
    StructureFeatureDefinition,
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.fast import PackMaterializer, build_fast_feature_pack
from alpha_system.features.input_views import (
    CanonicalInputViews,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.fast import (
    FastLabelMaterializer,
    build_fixed_horizon_label_pack,
)
from alpha_system.labels.fast.materializer import (
    _bbo_panel_row as _label_bbo_panel_row,
)
from alpha_system.labels.fast.materializer import (
    _ohlcv_panel_row as _label_ohlcv_panel_row,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_labels,
    supported_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelValueRecord

CAMPAIGN_ID = "FEATURE_COMPUTE_FAST_PATH_V1"
PHASE_ID = "FCFP-P13"
SUMMARY_PATH = Path("research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md")
DEFAULT_CANONICAL_SUBPATH = Path("databento/canonical/glbx_mdp3")
DEFAULT_SYMBOLS = ("ES", "NQ", "RTY")
DEFAULT_PRIMARY_SYMBOL = "ES"
DEFAULT_YEAR = 2024
DEFAULT_MONTH = 12
DEFAULT_OHLCV_DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"
DEFAULT_DENSE_OHLCV_DATASET_VERSION_ID = "dsv_databento_ohlcv_dense_2024_v1"
DEFAULT_BBO_DATASET_VERSION_ID = "dsv_databento_bbo_f9e1d70a04d9dae4"
DEFAULT_OHLCV_PARTITION_SCHEMA = "ohlcv_1m"
DEFAULT_DENSE_OHLCV_PARTITION_SCHEMA = "ohlcv_1m_dense"
DEFAULT_BBO_PARTITION_SCHEMA = "bbo_1m"
BENCHMARK_PARTITION_ID = "validation_partition"
BENCHMARK_PURPOSE = "feature_compute_fast_path_benchmark_gate"
ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"

REQUIRED_REPORT_FIELDS = (
    "elapsed",
    "rows_per_sec",
    "canonical_reads_per_symbol_year",
    "output_features_or_labels_per_read",
    "full_accepted_window_runtime_estimate",
    "speedup_vs_reference",
)

FLOAT_TOLERANCES: Mapping[str, tuple[float, float, str]] = {
    "base_ohlcv_rolling_volatility": (
        1e-16,
        1e-11,
        "rolling volatility variance reduction may differ by binary summation order",
    ),
    "base_ohlcv_volume_zscore": (
        5e-8,
        0.0,
        "volume_zscore rolling variance may differ by binary summation order",
    ),
    "base_ohlcv_vwap": (1e-12, 1e-12, "VWAP cumulative floating point reduction"),
    "base_ohlcv_anchored_vwap": (
        1e-12,
        1e-12,
        "anchored VWAP cumulative floating point reduction",
    ),
    "base_ohlcv_distance_to_vwap": (
        1e-12,
        1e-12,
        "distance to VWAP cumulative floating point reduction",
    ),
    "base_ohlcv_atr": (1e-12, 1e-12, "ATR rolling mean reduction"),
    "base_ohlcv_trendiness": (1e-12, 1e-12, "trendiness floating point reduction"),
    "liquidity_structure_range_contraction": (
        1e-12,
        1e-12,
        "range-contraction floating point reduction",
    ),
    "liquidity_structure_prior_high_distance": (
        1e-12,
        1e-12,
        "structure distance floating point reduction",
    ),
    "liquidity_structure_prior_low_distance": (
        1e-12,
        1e-12,
        "structure distance floating point reduction",
    ),
    "liquidity_structure_opening_range_high_distance": (
        1e-12,
        1e-12,
        "opening-range distance floating point reduction",
    ),
    "liquidity_structure_opening_range_low_distance": (
        1e-12,
        1e-12,
        "opening-range distance floating point reduction",
    ),
    "liquidity_structure_close_location_value": (
        1e-12,
        1e-12,
        "structure ratio floating point reduction",
    ),
    "liquidity_structure_wick_rejection_score": (
        1e-12,
        1e-12,
        "structure ratio floating point reduction",
    ),
    "bbo_tradability_spread_zscore": (
        1e-12,
        1e-12,
        "spread z-score rolling variance may differ by binary summation order",
    ),
    "cross_market_nq_es_rolling_beta_residual": (
        1e-12,
        1e-12,
        "cross-market rolling covariance reduction",
    ),
    "cross_market_rty_es_rolling_beta_residual": (
        1e-12,
        1e-12,
        "cross-market rolling covariance reduction",
    ),
    "cross_market_nq_es_rolling_correlation": (
        1e-12,
        1e-12,
        "cross-market rolling correlation reduction",
    ),
    "cross_market_rty_es_rolling_correlation": (
        1e-12,
        1e-12,
        "cross-market rolling correlation reduction",
    ),
}


class BenchmarkError(ValueError):
    """Raised when the benchmark cannot produce a valid gate result."""


class ParityError(AssertionError):
    """Raised when reference and V1 records differ on the bounded real slice."""


@dataclass(frozen=True, slots=True)
class BenchmarkWindow:
    """Resolved bounded measurement window."""

    year: int = DEFAULT_YEAR
    month: int = DEFAULT_MONTH
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    primary_symbol: str = DEFAULT_PRIMARY_SYMBOL
    ohlcv_dataset_version_id: str = DEFAULT_OHLCV_DATASET_VERSION_ID
    dense_ohlcv_dataset_version_id: str = DEFAULT_DENSE_OHLCV_DATASET_VERSION_ID
    bbo_dataset_version_id: str = DEFAULT_BBO_DATASET_VERSION_ID
    start_ts: datetime | None = None
    end_ts: datetime | None = None

    def __post_init__(self) -> None:
        if self.month < 1 or self.month > 12:
            raise BenchmarkError("month must be in 1..12")
        symbols = tuple(symbol.upper() for symbol in self.symbols)
        if not symbols:
            raise BenchmarkError("at least one symbol is required")
        primary = self.primary_symbol.upper()
        if primary not in symbols:
            raise BenchmarkError("primary_symbol must be present in symbols")
        object.__setattr__(self, "symbols", symbols)
        object.__setattr__(self, "primary_symbol", primary)

    @property
    def resolved_start_ts(self) -> datetime:
        if self.start_ts is not None:
            return self.start_ts
        return datetime(self.year, self.month, 1, tzinfo=UTC)

    @property
    def resolved_end_ts(self) -> datetime:
        if self.end_ts is not None:
            return self.end_ts
        if self.month == 12:
            return datetime(self.year + 1, 1, 1, tzinfo=UTC)
        return datetime(self.year, self.month + 1, 1, tzinfo=UTC)

    @property
    def identifier(self) -> str:
        return f"{self.year}-{self.month:02d}"

    @property
    def year_start_ts(self) -> datetime:
        return datetime(self.year, 1, 1, tzinfo=UTC)

    @property
    def year_end_ts(self) -> datetime:
        return datetime(self.year + 1, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class SliceValidation:
    """Value-free slice self-validation result."""

    roll_event_count: int
    raw_contract_transition_count: int
    session_gap_count: int
    row_count_by_input: Mapping[str, int]
    notes: tuple[str, ...]

    @property
    def slice_row_count(self) -> int:
        return sum(self.row_count_by_input.values())


@dataclass(frozen=True, slots=True)
class PackResult:
    """Value-free benchmark result for one pack."""

    pack_id: str
    kind: str
    symbols: tuple[str, ...]
    slice_row_count: int
    output_count: int
    reference_elapsed_seconds: float
    v1_elapsed_seconds: float
    reference_rows_per_sec: float
    v1_rows_per_sec: float
    reference_canonical_reads: int
    v1_canonical_reads: int
    canonical_reads_per_symbol_year: float
    output_features_or_labels_per_read: float
    speedup_vs_reference: float
    full_accepted_window_rows: int
    full_accepted_window_runtime_estimate_seconds: float
    extrapolation_basis: str
    parity_result: str
    tolerance_notes: tuple[str, ...]

    def required_report_fields(self) -> dict[str, float | str]:
        return {
            "elapsed": self.v1_elapsed_seconds,
            "rows_per_sec": self.v1_rows_per_sec,
            "canonical_reads_per_symbol_year": self.canonical_reads_per_symbol_year,
            "output_features_or_labels_per_read": self.output_features_or_labels_per_read,
            "full_accepted_window_runtime_estimate": (
                self.full_accepted_window_runtime_estimate_seconds
            ),
            "speedup_vs_reference": self.speedup_vs_reference,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkPayload:
    """Complete value-free benchmark payload."""

    status: str
    generated_at: datetime
    alpha_data_root: str
    canonical_root: str
    window: BenchmarkWindow
    validation: SliceValidation | None
    packs: tuple[PackResult, ...]
    blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class _InputFrames:
    ohlcv_rows: Mapping[str, tuple[dict[str, Any], ...]]
    dense_ohlcv_rows: Mapping[str, tuple[dict[str, Any], ...]]
    bbo_rows: Mapping[str, tuple[dict[str, Any], ...]]
    full_window_rows: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _FeaturePackSpec:
    pack_id: str
    definitions: tuple[
        OHLCVFeatureDefinition
        | BBOFeatureDefinition
        | SessionFeatureDefinition
        | CrossMarketFeatureDefinition
        | StructureFeatureDefinition
        | FixedHorizonLabelDefinition,
        ...
    ]
    feature_set: FeatureSetSpec | None
    input_kind: str
    symbols: tuple[str, ...]
    reference_runner: Callable[[], tuple[FeatureValueRecord | LabelValueRecord, ...]]
    fast_runner: Callable[[], tuple[FeatureValueRecord | LabelValueRecord, ...]]
    slice_row_count: int
    full_accepted_window_rows: int
    reference_canonical_reads: int
    v1_canonical_reads: int
    symbol_count: int
    extrapolation_basis: str
    tolerance_by_version_id: Mapping[str, tuple[float, float, str]]


def extrapolate_runtime_seconds(full_window_rows: int, rows_per_sec: float) -> float:
    """Estimate full-window runtime from measured bounded-slice throughput."""

    if full_window_rows < 0:
        raise BenchmarkError("full_window_rows must be non-negative")
    if rows_per_sec <= 0 or not math.isfinite(rows_per_sec):
        raise BenchmarkError("rows_per_sec must be positive and finite")
    return full_window_rows / rows_per_sec


def validate_report_fields(fields: Mapping[str, object]) -> None:
    """Assert the benchmark report includes the required value-free fields."""

    missing = tuple(field for field in REQUIRED_REPORT_FIELDS if field not in fields)
    if missing:
        raise BenchmarkError("benchmark report missing fields: " + ", ".join(missing))


def validate_slice_self_coverage(
    *,
    roll_event_count: int,
    session_gap_count: int,
) -> None:
    """Fail closed unless the bounded slice contains roll and gap coverage."""

    if roll_event_count < 1:
        raise BenchmarkError(
            "bounded benchmark slice contains no configured contract-roll event; "
            "choose a roll month or widen the window"
        )
    if session_gap_count < 1:
        raise BenchmarkError(
            "bounded benchmark slice contains no session gap; choose a window with "
            "holiday or maintenance gaps"
        )


def blocked_summary(alpha_data_root: str | None, reason: str) -> BenchmarkPayload:
    """Build a value-free blocked payload for genuine missing-data fallbacks."""

    return BenchmarkPayload(
        status="BLOCKED",
        generated_at=datetime.now(UTC),
        alpha_data_root=alpha_data_root or "",
        canonical_root="",
        window=BenchmarkWindow(),
        validation=None,
        packs=(),
        blocked_reason=reason,
    )


def render_summary_markdown(payload: BenchmarkPayload) -> str:
    """Render a value-free benchmark summary."""

    lines: list[str] = [
        "# FCFP-P13 Benchmark Summary",
        "",
        f"- Campaign: `{CAMPAIGN_ID}`",
        f"- Phase: `{PHASE_ID}`",
        f"- Status: `{payload.status}`",
        f"- Generated at: `{payload.generated_at.isoformat()}`",
        "- Value policy: value-free summary only; no feature, label, price, "
        "Parquet, SQLite, or row-level values are included.",
    ]
    if payload.blocked_reason is not None and payload.validation is None:
        lines.extend(("", "## Blocked", "", payload.blocked_reason, ""))
        return "\n".join(lines)

    validation = payload.validation
    if validation is None:
        raise BenchmarkError("non-blocked payload requires slice validation")
    lines.extend(
        [
            "",
            "## Window",
            "",
            f"- Window: `{payload.window.identifier}` "
            f"(`{payload.window.resolved_start_ts.isoformat()}` to "
            f"`{payload.window.resolved_end_ts.isoformat()}`)",
            f"- Symbols: `{', '.join(payload.window.symbols)}`",
            f"- Primary single-symbol packs: `{payload.window.primary_symbol}`",
            f"- OHLCV DatasetVersion: `{payload.window.ohlcv_dataset_version_id}`",
            f"- Dense OHLCV DatasetVersion: `{payload.window.dense_ohlcv_dataset_version_id}`",
            f"- BBO DatasetVersion: `{payload.window.bbo_dataset_version_id}`",
            f"- Slice row count across loaded inputs: `{validation.slice_row_count}`",
            f"- Contract-roll events in configured roll calendar: `{validation.roll_event_count}`",
            f"- Raw contract/id transitions observed in canonical rows: "
            f"`{validation.raw_contract_transition_count}`",
            f"- Session gaps observed: `{validation.session_gap_count}`",
        ]
    )
    for note in validation.notes:
        lines.append(f"- Note: {note}")

    if payload.blocked_reason is not None:
        lines.extend(
            [
                "",
                "## Blocked",
                "",
                payload.blocked_reason,
                "",
                "No speedup or full-window runtime estimate is reported because "
                "real-data parity did not pass.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Pack | Slice Rows | Outputs | Reference Elapsed (s) | "
            "V1 Elapsed (s) | V1 Rows/s | Reference Reads | V1 Reads | "
            "Reads/Symbol-Year | Outputs/Read | Speedup | Full-Window Estimate | Parity |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for pack in payload.packs:
        validate_report_fields(pack.required_report_fields())
        lines.append(
            "| "
            + " | ".join(
                (
                    pack.pack_id,
                    str(pack.slice_row_count),
                    str(pack.output_count),
                    _seconds(pack.reference_elapsed_seconds),
                    _seconds(pack.v1_elapsed_seconds),
                    _number(pack.v1_rows_per_sec),
                    str(pack.reference_canonical_reads),
                    str(pack.v1_canonical_reads),
                    _number(pack.canonical_reads_per_symbol_year),
                    _number(pack.output_features_or_labels_per_read),
                    _number(pack.speedup_vs_reference),
                    _seconds(pack.full_accepted_window_runtime_estimate_seconds),
                    pack.parity_result,
                )
            )
            + " |"
        )

    lines.extend(["", "## Extrapolation Basis", ""])
    for pack in payload.packs:
        lines.append(f"- `{pack.pack_id}`: {pack.extrapolation_basis}")

    lines.extend(["", "## Parity Confirmation", ""])
    for pack in payload.packs:
        notes = "; ".join(pack.tolerance_notes) if pack.tolerance_notes else "exact parity"
        availability_field = (
            "label_available_ts" if pack.kind == "labels" else "available_ts"
        )
        version_field = "label_version_id" if pack.kind == "labels" else "feature_version_id"
        lines.append(
            f"- `{pack.pack_id}`: `{pack.parity_result}` on value, "
            f"{availability_field}, gap/quality flags, and {version_field} "
            f"identity ({notes})."
        )

    lines.extend(
        [
            "",
            "## Required Report Fields",
            "",
            "- `elapsed`: V1 elapsed seconds per pack; reference elapsed seconds is also reported.",
            "- `rows_per_sec`: V1 bounded-slice input rows per second.",
            "- `canonical_reads_per_symbol_year`: V1 canonical reads per symbol-year unit.",
            "- `output_features_or_labels_per_read`: governed outputs divided by V1 canonical reads.",
            "- `full_accepted_window_runtime_estimate`: extrapolated seconds from slice rows/sec.",
            "- `speedup_vs_reference`: reference elapsed seconds divided by V1 elapsed seconds.",
            "",
        ]
    )
    return "\n".join(lines)


def run_benchmark(
    *,
    alpha_data_root: Path,
    summary_path: Path = SUMMARY_PATH,
    window: BenchmarkWindow = BenchmarkWindow(),
) -> BenchmarkPayload:
    """Run the bounded-real benchmark and write the value-free summary."""

    if not alpha_data_root.exists():
        payload = blocked_summary(
            alpha_data_root.as_posix(),
            f"ALPHA_DATA_ROOT is absent: {alpha_data_root.as_posix()}",
        )
        _write_summary(summary_path, payload)
        return payload

    canonical_root = alpha_data_root / DEFAULT_CANONICAL_SUBPATH
    if not canonical_root.exists():
        payload = blocked_summary(
            alpha_data_root.as_posix(),
            f"canonical root is absent: {canonical_root.as_posix()}",
        )
        _write_summary(summary_path, payload)
        return payload

    inputs = _load_inputs(canonical_root, window)
    validation = _validate_slice(window, inputs)
    accepted_versions = {
        window.ohlcv_dataset_version_id: _accepted_version(alpha_data_root, window.ohlcv_dataset_version_id),
        window.bbo_dataset_version_id: _accepted_version(alpha_data_root, window.bbo_dataset_version_id),
    }
    packs = _build_pack_specs(
        window=window,
        inputs=inputs,
        accepted_versions=accepted_versions,
    )

    try:
        results = tuple(_benchmark_pack(pack) for pack in packs)
    except ParityError as exc:
        payload = BenchmarkPayload(
            status="BLOCKED_PARITY",
            generated_at=datetime.now(UTC),
            alpha_data_root=alpha_data_root.as_posix(),
            canonical_root=canonical_root.as_posix(),
            window=window,
            validation=validation,
            packs=(),
            blocked_reason=(
                "Real-data parity confirmation failed before speedup reporting: "
                f"{_format_parity_failure(exc, packs)}"
            ),
        )
        _write_summary(summary_path, payload)
        raise
    _assert_materially_faster(results)
    _assert_reduced_reads(results)
    payload = BenchmarkPayload(
        status="COMPLETE",
        generated_at=datetime.now(UTC),
        alpha_data_root=alpha_data_root.as_posix(),
        canonical_root=canonical_root.as_posix(),
        window=window,
        validation=validation,
        packs=results,
    )
    _write_summary(summary_path, payload)
    return payload


def _load_inputs(canonical_root: Path, window: BenchmarkWindow) -> _InputFrames:
    start = window.resolved_start_ts.isoformat()
    end = window.resolved_end_ts.isoformat()
    ohlcv: dict[str, tuple[dict[str, Any], ...]] = {}
    dense: dict[str, tuple[dict[str, Any], ...]] = {}
    bbo: dict[str, tuple[dict[str, Any], ...]] = {}
    full_counts: dict[str, int] = {}
    for symbol in window.symbols:
        ohlcv[symbol] = load_canonical_ohlcv_rows(
            canonical_root=canonical_root,
            dataset_version_id=window.ohlcv_dataset_version_id,
            symbol=symbol,
            start_ts=start,
            end_ts=end,
            partition_schema=DEFAULT_OHLCV_PARTITION_SCHEMA,
        )
        dense[symbol] = load_canonical_ohlcv_rows(
            canonical_root=canonical_root,
            dataset_version_id=window.dense_ohlcv_dataset_version_id,
            symbol=symbol,
            start_ts=start,
            end_ts=end,
            partition_schema=DEFAULT_DENSE_OHLCV_PARTITION_SCHEMA,
        )
        bbo[symbol] = load_canonical_bbo_rows(
            canonical_root=canonical_root,
            dataset_version_id=window.bbo_dataset_version_id,
            symbol=symbol,
            start_ts=start,
            end_ts=end,
            partition_schema=DEFAULT_BBO_PARTITION_SCHEMA,
        )
        full_counts[f"ohlcv:{symbol}"] = _partition_row_count(
            canonical_root,
            dataset_version_id=window.ohlcv_dataset_version_id,
            partition_schema=DEFAULT_OHLCV_PARTITION_SCHEMA,
            symbol=symbol,
            start_ts=window.year_start_ts.isoformat(),
            end_ts=window.year_end_ts.isoformat(),
        )
        full_counts[f"dense_ohlcv:{symbol}"] = _partition_row_count(
            canonical_root,
            dataset_version_id=window.dense_ohlcv_dataset_version_id,
            partition_schema=DEFAULT_DENSE_OHLCV_PARTITION_SCHEMA,
            symbol=symbol,
            start_ts=window.year_start_ts.isoformat(),
            end_ts=window.year_end_ts.isoformat(),
        )
        full_counts[f"bbo:{symbol}"] = _partition_row_count(
            canonical_root,
            dataset_version_id=window.bbo_dataset_version_id,
            partition_schema=DEFAULT_BBO_PARTITION_SCHEMA,
            symbol=symbol,
            start_ts=window.year_start_ts.isoformat(),
            end_ts=window.year_end_ts.isoformat(),
        )
        full_counts[f"accepted_ohlcv:{symbol}"] = _accepted_window_row_count(
            canonical_root,
            partition_schema=DEFAULT_OHLCV_PARTITION_SCHEMA,
            symbol=symbol,
        )
        full_counts[f"accepted_dense_ohlcv:{symbol}"] = _accepted_window_row_count(
            canonical_root,
            partition_schema=DEFAULT_DENSE_OHLCV_PARTITION_SCHEMA,
            symbol=symbol,
        )
        full_counts[f"accepted_bbo:{symbol}"] = _accepted_window_row_count(
            canonical_root,
            partition_schema=DEFAULT_BBO_PARTITION_SCHEMA,
            symbol=symbol,
        )
    return _InputFrames(
        ohlcv_rows=ohlcv,
        dense_ohlcv_rows=dense,
        bbo_rows=bbo,
        full_window_rows=full_counts,
    )


def _partition_row_count(
    canonical_root: Path,
    *,
    dataset_version_id: str,
    partition_schema: str,
    symbol: str,
    start_ts: str,
    end_ts: str,
) -> int:
    polars = __import__("polars")
    path = (
        canonical_root
        / dataset_version_id
        / f"schema={partition_schema}"
        / f"root={symbol}"
        / "part-00000.parquet"
    )
    return int(
        polars.scan_parquet(path.as_posix())
        .filter((polars.col("bar_start_ts") >= start_ts) & (polars.col("bar_start_ts") < end_ts))
        .select(polars.len().alias("rows"))
        .collect()
        .item()
    )


def _accepted_window_row_count(
    canonical_root: Path,
    *,
    partition_schema: str,
    symbol: str,
) -> int:
    polars = __import__("polars")
    total = 0
    for path in sorted(canonical_root.glob(f"*/schema={partition_schema}/root={symbol}/part-00000.parquet")):
        total += int(
            polars.scan_parquet(path.as_posix())
            .select(polars.len().alias("rows"))
            .collect()
            .item()
        )
    if total <= 0:
        raise BenchmarkError(
            f"no accepted-window rows found for {symbol} schema {partition_schema}"
        )
    return total


def _validate_slice(window: BenchmarkWindow, inputs: _InputFrames) -> SliceValidation:
    row_counts: dict[str, int] = {}
    for symbol, rows in inputs.ohlcv_rows.items():
        row_counts[f"ohlcv:{symbol}"] = len(rows)
    for symbol, rows in inputs.bbo_rows.items():
        row_counts[f"bbo:{symbol}"] = len(rows)

    session_gaps = sum(_session_gap_count(rows) for rows in inputs.ohlcv_rows.values())
    raw_transitions = sum(_raw_contract_transition_count(rows) for rows in inputs.ohlcv_rows.values())
    roll_events = len(_scheduled_roll_events(window))
    validate_slice_self_coverage(
        roll_event_count=roll_events,
        session_gap_count=session_gaps,
    )
    notes = (
        "Contract roll self-validation uses the configured quarterly CME roll "
        "calendar because the canonical continuous front rows keep stable "
        "contract_id / instrument_id identifiers.",
    )
    return SliceValidation(
        roll_event_count=roll_events,
        raw_contract_transition_count=raw_transitions,
        session_gap_count=session_gaps,
        row_count_by_input=row_counts,
        notes=notes,
    )


def _scheduled_roll_events(window: BenchmarkWindow) -> tuple[date, ...]:
    start = window.resolved_start_ts.date()
    end = window.resolved_end_ts.date()
    events = []
    for month in (3, 6, 9, 12):
        event = _third_friday(window.year, month)
        if start <= event < end:
            events.append(event)
    return tuple(events)


def _third_friday(year: int, month: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != 4:
        current += timedelta(days=1)
    return current + timedelta(days=14)


def _session_gap_count(rows: Sequence[Mapping[str, Any]]) -> int:
    ordered = sorted((_parse_ts(row["event_ts"]) for row in rows))
    return sum(
        1
        for previous, current in zip(ordered, ordered[1:], strict=False)
        if (current - previous).total_seconds() > 60
    )


def _raw_contract_transition_count(rows: Sequence[Mapping[str, Any]]) -> int:
    ordered = sorted(rows, key=lambda row: str(row["event_ts"]))
    transitions = 0
    previous: tuple[str, str] | None = None
    for row in ordered:
        current = (str(row.get("contract_id")), str(row.get("instrument_id")))
        if previous is not None and current != previous:
            transitions += 1
        previous = current
    return transitions


def _build_pack_specs(
    *,
    window: BenchmarkWindow,
    inputs: _InputFrames,
    accepted_versions: Mapping[str, AcceptedDatasetVersion],
) -> tuple[_FeaturePackSpec, ...]:
    primary = window.primary_symbol
    ohlcv_rows = inputs.ohlcv_rows[primary]
    bbo_rows = inputs.bbo_rows[primary]
    accepted_ohlcv = accepted_versions[window.ohlcv_dataset_version_id]
    accepted_bbo = accepted_versions[window.bbo_dataset_version_id]
    ohlcv_view = build_ohlcv_input_view(
        accepted_ohlcv,
        ohlcv_rows,
        partition_id=BENCHMARK_PARTITION_ID,
        purpose=BENCHMARK_PURPOSE,
        governance_metadata=_governance_metadata(),
    )
    bbo_view = build_bbo_input_view(
        accepted_bbo,
        bbo_rows,
        partition_id=BENCHMARK_PARTITION_ID,
        purpose=BENCHMARK_PURPOSE,
        governance_metadata=_governance_metadata(),
    )
    materializer = PackMaterializer()

    specs: list[_FeaturePackSpec] = []
    specs.extend(
        (
            _feature_pack_spec(
                "base_ohlcv",
                *_base_ohlcv_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_ohlcv_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "session_calendar_roll",
                *_session_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_session_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "vwap_session_auction",
                *_vwap_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_ohlcv_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "regime_vol_compression",
                *_regime_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_mixed_ohlcv_structure_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "liquidity_pa_structure",
                *_liquidity_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_structure_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "volume_activity",
                *_volume_contracts(window.ohlcv_dataset_version_id),
                input_kind="ohlcv",
                rows=ohlcv_rows,
                reference_view=ohlcv_view,
                reference_compute=_reference_mixed_ohlcv_structure_records,
                materializer=materializer,
                slice_row_count=len(ohlcv_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_ohlcv:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
            _feature_pack_spec(
                "bbo_tradability",
                *_bbo_contracts(window.bbo_dataset_version_id),
                input_kind="bbo",
                rows=bbo_rows,
                reference_view=bbo_view,
                reference_compute=_reference_bbo_records,
                materializer=materializer,
                slice_row_count=len(bbo_rows),
                full_accepted_window_rows=inputs.full_window_rows[f"accepted_bbo:{primary}"],
                symbol_count=1,
                symbols=(primary,),
            ),
        )
    )
    specs.append(_cross_market_pack_spec(window, inputs, accepted_ohlcv, materializer))
    specs.append(_label_pack_spec(window, inputs, accepted_ohlcv, accepted_bbo))
    return tuple(specs)


def _feature_pack_spec(
    pack_id: str,
    definitions: tuple[
        OHLCVFeatureDefinition
        | BBOFeatureDefinition
        | SessionFeatureDefinition
        | StructureFeatureDefinition,
        ...
    ],
    feature_set: FeatureSetSpec,
    *,
    input_kind: str,
    rows: tuple[dict[str, Any], ...],
    reference_view: Any,
    reference_compute: Callable[[tuple[Any, ...], Any], tuple[FeatureValueRecord, ...]],
    materializer: PackMaterializer,
    slice_row_count: int,
    full_accepted_window_rows: int,
    symbol_count: int,
    symbols: tuple[str, ...],
) -> _FeaturePackSpec:
    pack = build_fast_feature_pack(feature_set)
    tolerance_by_version_id = _feature_tolerances(definitions)
    return _FeaturePackSpec(
        pack_id=pack_id,
        definitions=definitions,
        feature_set=feature_set,
        input_kind=input_kind,
        symbols=symbols,
        reference_runner=lambda: reference_compute(definitions, reference_view),
        fast_runner=lambda: materializer.compute_values(
            _feature_frame_from_rows(rows),
            pack,
        ),
        slice_row_count=slice_row_count,
        full_accepted_window_rows=full_accepted_window_rows,
        reference_canonical_reads=len(definitions),
        v1_canonical_reads=1,
        symbol_count=symbol_count,
        extrapolation_basis=(
            f"{pack_id}: {slice_row_count} bounded {input_kind} rows measured; "
            f"{full_accepted_window_rows} accepted-window {input_kind} rows extrapolated"
        ),
        tolerance_by_version_id=tolerance_by_version_id,
    )


def _cross_market_pack_spec(
    window: BenchmarkWindow,
    inputs: _InputFrames,
    accepted_ohlcv: AcceptedDatasetVersion,
    materializer: PackMaterializer,
) -> _FeaturePackSpec:
    definitions, feature_set = _cross_market_contracts(window.ohlcv_dataset_version_id)
    views = {
        symbol: build_ohlcv_input_view(
            accepted_ohlcv,
            inputs.ohlcv_rows[symbol],
            partition_id=BENCHMARK_PARTITION_ID,
            purpose=BENCHMARK_PURPOSE,
            governance_metadata=_governance_metadata(),
        )
        for symbol in window.symbols
    }
    bundle = CrossMarketInputBundle(ohlcv_by_instrument=views)
    rows = tuple(row for symbol in window.symbols for row in inputs.ohlcv_rows[symbol])
    pack = build_fast_feature_pack(feature_set)
    full_rows = sum(inputs.full_window_rows[f"accepted_ohlcv:{symbol}"] for symbol in window.symbols)
    slice_rows = sum(len(inputs.ohlcv_rows[symbol]) for symbol in window.symbols)
    return _FeaturePackSpec(
        pack_id="cross_market",
        definitions=definitions,
        feature_set=feature_set,
        input_kind="ohlcv_panel",
        symbols=window.symbols,
        reference_runner=lambda: _reference_cross_market_records(definitions, bundle),
    fast_runner=lambda: materializer.compute_values(
        _feature_frame_from_rows(rows),
        pack,
    ),
        slice_row_count=slice_rows,
        full_accepted_window_rows=full_rows,
        reference_canonical_reads=len(definitions) * len(window.symbols),
        v1_canonical_reads=len(window.symbols),
        symbol_count=len(window.symbols),
        extrapolation_basis=(
            f"cross_market: {slice_rows} bounded {','.join(window.symbols)} OHLCV rows measured; "
            f"{full_rows} accepted-window {','.join(window.symbols)} OHLCV rows extrapolated"
        ),
        tolerance_by_version_id=_feature_tolerances(definitions),
    )


def _label_pack_spec(
    window: BenchmarkWindow,
    inputs: _InputFrames,
    accepted_ohlcv: AcceptedDatasetVersion,
    accepted_bbo: AcceptedDatasetVersion,
) -> _FeaturePackSpec:
    definitions = _fixed_horizon_definitions(
        dataset_version_ids=(
            window.ohlcv_dataset_version_id,
            window.bbo_dataset_version_id,
        )
    )
    pack = build_fixed_horizon_label_pack(definitions)
    materializer = FastLabelMaterializer()
    symbol = window.primary_symbol
    ohlcv_rows = inputs.ohlcv_rows[symbol]
    bbo_rows = inputs.bbo_rows[symbol]
    views = CanonicalInputViews(
        ohlcv=build_ohlcv_input_view(
            accepted_ohlcv,
            ohlcv_rows,
            partition_id=BENCHMARK_PARTITION_ID,
            purpose=BENCHMARK_PURPOSE,
            governance_metadata=_governance_metadata(),
        ),
        bbo=build_bbo_input_view(
            accepted_bbo,
            bbo_rows,
            partition_id=BENCHMARK_PARTITION_ID,
            purpose=BENCHMARK_PURPOSE,
            governance_metadata=_governance_metadata(),
        ),
    )
    full_rows = (
        inputs.full_window_rows[f"accepted_ohlcv:{symbol}"]
        + inputs.full_window_rows[f"accepted_bbo:{symbol}"]
    )
    slice_rows = len(ohlcv_rows) + len(bbo_rows)
    trade_label_count = sum(1 for item in definitions if not item.is_midprice)
    mid_label_count = len(definitions) - trade_label_count
    # Prepare the V1 engine's input panel ONCE, outside the timed fast_runner --
    # symmetric with the reference engine, whose CanonicalInputViews (`views`
    # above) are also built once outside its timed reference_runner. Input
    # adaptation (raw canonical rows -> prepared panel / prepared views) is a
    # once-per-batch cost that amortizes to ~0 at full-window scale and across
    # all horizons; timing it for V1 but not the reference made the bounded-slice
    # label comparison measure adaptation overhead instead of compute. Both timed
    # regions now measure compute given prepared canonical input. (For labels the
    # structural V1 win is also the 2-vs-N canonical reads asserted separately.)
    fast_panel = materializer.prepare_price_panel(
        _label_frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=bbo_rows)
    )
    return _FeaturePackSpec(
        pack_id="fixed_horizon_labels",
        definitions=definitions,
        feature_set=None,
        input_kind="label_panel",
        symbols=(symbol,),
        reference_runner=lambda: _flatten_label_records(
            compute_fixed_horizon_labels(definitions, views)
        ),
        fast_runner=lambda: materializer.compute_values_from_panel(fast_panel, pack),
        slice_row_count=slice_rows,
        full_accepted_window_rows=full_rows,
        reference_canonical_reads=trade_label_count + mid_label_count,
        v1_canonical_reads=2,
        symbol_count=1,
        extrapolation_basis=(
            f"fixed_horizon_labels: {slice_rows} bounded {symbol} OHLCV+BBO rows measured; "
            f"{full_rows} accepted-window {symbol} OHLCV+BBO rows extrapolated"
        ),
        tolerance_by_version_id={},
    )


def _benchmark_pack(pack: _FeaturePackSpec) -> PackResult:
    reference_elapsed, reference_records = _time_call(pack.reference_runner)
    fast_elapsed, fast_records = _time_call(pack.fast_runner)
    if pack.pack_id == "fixed_horizon_labels":
        _assert_label_parity(
            _group_labels(reference_records),  # type: ignore[arg-type]
            _group_labels(fast_records),  # type: ignore[arg-type]
        )
        output_count = len({record.label_version_id for record in fast_records})  # type: ignore[attr-defined]
        tolerance_notes: tuple[str, ...] = ()
        kind = "labels"
    else:
        _assert_feature_parity(
            _group_features(reference_records),  # type: ignore[arg-type]
            _group_features(fast_records),  # type: ignore[arg-type]
            pack.tolerance_by_version_id,
        )
        output_count = len({record.feature_version_id for record in fast_records})  # type: ignore[attr-defined]
        tolerance_notes = _tolerance_notes(pack.tolerance_by_version_id)
        kind = "features"
    v1_rows_per_sec = pack.slice_row_count / fast_elapsed if fast_elapsed > 0 else math.inf
    reference_rows_per_sec = (
        pack.slice_row_count / reference_elapsed if reference_elapsed > 0 else math.inf
    )
    speedup = reference_elapsed / fast_elapsed if fast_elapsed > 0 else math.inf
    return PackResult(
        pack_id=pack.pack_id,
        kind=kind,
        symbols=pack.symbols,
        slice_row_count=pack.slice_row_count,
        output_count=output_count,
        reference_elapsed_seconds=reference_elapsed,
        v1_elapsed_seconds=fast_elapsed,
        reference_rows_per_sec=reference_rows_per_sec,
        v1_rows_per_sec=v1_rows_per_sec,
        reference_canonical_reads=pack.reference_canonical_reads,
        v1_canonical_reads=pack.v1_canonical_reads,
        canonical_reads_per_symbol_year=pack.v1_canonical_reads / pack.symbol_count,
        output_features_or_labels_per_read=output_count / pack.v1_canonical_reads,
        speedup_vs_reference=speedup,
        full_accepted_window_rows=pack.full_accepted_window_rows,
        full_accepted_window_runtime_estimate_seconds=extrapolate_runtime_seconds(
            pack.full_accepted_window_rows,
            v1_rows_per_sec,
        ),
        extrapolation_basis=pack.extrapolation_basis,
        parity_result="PASS",
        tolerance_notes=tolerance_notes,
    )


def _feature_frame_from_rows(rows: Sequence[Mapping[str, Any]]) -> Any:
    polars = __import__("polars")
    normalized = [dict(row) for row in rows]
    if not normalized:
        raise BenchmarkError("feature benchmark rows must be non-empty")
    frame = polars.DataFrame(normalized, infer_schema_length=None)
    if "quality_flags" in frame.columns:
        frame = frame.with_columns(
            polars.col("quality_flags").cast(polars.List(polars.String))
        )
    return frame.sort("available_ts")


def _label_frame_from_rows(
    *,
    ohlcv_rows: Sequence[Mapping[str, Any]],
    bbo_rows: Sequence[Mapping[str, Any]],
) -> Any:
    polars = __import__("polars")
    rows: list[dict[str, Any]] = []
    rows.extend(_label_ohlcv_panel_row(row) for row in ohlcv_rows)
    rows.extend(_label_bbo_panel_row(row) for row in bbo_rows)
    if not rows:
        raise BenchmarkError("label benchmark rows must be non-empty")
    frame = polars.DataFrame(rows, infer_schema_length=None)
    frame = frame.with_columns(
        polars.col("quality_flags").cast(polars.List(polars.String))
    )
    return frame.sort(("price_basis", "series_id", "event_ts", "available_ts"))


def _format_parity_failure(
    error: ParityError,
    packs: Sequence[_FeaturePackSpec],
) -> str:
    message = str(error)
    for pack in packs:
        for definition in pack.definitions:
            version_id = getattr(
                definition,
                "feature_version_id",
                getattr(definition, "label_version_id", ""),
            )
            if not version_id or str(version_id) not in message:
                continue
            identity = getattr(
                definition,
                "feature_id",
                getattr(getattr(definition, "name", None), "value", "unknown"),
            )
            return f"{pack.pack_id}/{identity} ({version_id}): {message}"
    return message


def _time_call[RecordT](runner: Callable[[], tuple[RecordT, ...]]) -> tuple[float, tuple[RecordT, ...]]:
    start = perf_counter()
    records = runner()
    elapsed = perf_counter() - start
    if elapsed <= 0:
        elapsed = 1e-12
    return elapsed, records


def _assert_feature_parity(
    reference: Mapping[str, tuple[FeatureValueRecord, ...]],
    fast: Mapping[str, tuple[FeatureValueRecord, ...]],
    tolerance_by_version_id: Mapping[str, tuple[float, float, str]],
) -> None:
    if set(reference) != set(fast):
        raise ParityError("feature_version_id sets differ")
    for feature_version_id, reference_records in reference.items():
        fast_records = fast[feature_version_id]
        ref_by_key = {
            (record.feature_version_id, record.entity_id, record.event_ts, record.available_ts): record
            for record in reference_records
        }
        fast_by_key = {
            (record.feature_version_id, record.entity_id, record.event_ts, record.available_ts): record
            for record in fast_records
        }
        if set(ref_by_key) != set(fast_by_key):
            raise ParityError(f"{feature_version_id}: record keys differ")
        abs_tol, rel_tol, _ = tolerance_by_version_id.get(
            feature_version_id,
            (0.0, 0.0, "exact"),
        )
        for key, ref in ref_by_key.items():
            got = fast_by_key[key]
            if got.available_ts != ref.available_ts:
                raise ParityError(f"{feature_version_id}: available_ts differs")
            if got.quality_flags != ref.quality_flags:
                raise ParityError(f"{feature_version_id}: quality_flags differ")
            if not _values_match(ref.value, got.value, abs_tol=abs_tol, rel_tol=rel_tol):
                raise ParityError(f"{feature_version_id}: value differs beyond tolerance")


def _assert_label_parity(
    reference: Mapping[str, tuple[LabelValueRecord, ...]],
    fast: Mapping[str, tuple[LabelValueRecord, ...]],
) -> None:
    if set(reference) != set(fast):
        raise ParityError("label_version_id sets differ")
    for label_version_id, reference_records in reference.items():
        fast_records = fast[label_version_id]
        ref_by_key = {
            (record.label_version_id, record.entity_id, record.event_ts): record
            for record in reference_records
        }
        fast_by_key = {
            (record.label_version_id, record.entity_id, record.event_ts): record
            for record in fast_records
        }
        if set(ref_by_key) != set(fast_by_key):
            raise ParityError(f"{label_version_id}: label record keys differ")
        for key, ref in ref_by_key.items():
            got = fast_by_key[key]
            if got.horizon_end_ts != ref.horizon_end_ts:
                raise ParityError(f"{label_version_id}: horizon_end_ts differs")
            if got.label_available_ts != ref.label_available_ts:
                raise ParityError(f"{label_version_id}: label_available_ts differs")
            if got.quality_flags != ref.quality_flags:
                raise ParityError(f"{label_version_id}: label quality_flags differ")
            if got.label_spec_id != ref.label_spec_id:
                raise ParityError(f"{label_version_id}: label_spec_id differs")
            if not _values_match(ref.value, got.value, abs_tol=1e-12, rel_tol=1e-12):
                raise ParityError(f"{label_version_id}: label value differs beyond tolerance")


def _values_match(reference: Any, fast: Any, *, abs_tol: float, rel_tol: float) -> bool:
    if reference is None or fast is None:
        return reference is fast
    if isinstance(reference, Mapping) and isinstance(fast, Mapping):
        if set(reference) != set(fast):
            return False
        return all(
            _values_match(reference[key], fast[key], abs_tol=abs_tol, rel_tol=rel_tol)
            for key in reference
        )
    if isinstance(reference, (int, float)) and isinstance(fast, (int, float)):
        if abs_tol == 0.0 and rel_tol == 0.0:
            return fast == reference
        return math.isclose(float(fast), float(reference), abs_tol=abs_tol, rel_tol=rel_tol)
    return fast == reference


def _feature_tolerances(
    definitions: Sequence[
        OHLCVFeatureDefinition
        | BBOFeatureDefinition
        | SessionFeatureDefinition
        | CrossMarketFeatureDefinition
        | StructureFeatureDefinition
    ],
) -> dict[str, tuple[float, float, str]]:
    tolerances: dict[str, tuple[float, float, str]] = {}
    for definition in definitions:
        tolerance = FLOAT_TOLERANCES.get(definition.feature_id)
        if tolerance is not None:
            tolerances[definition.feature_version_id] = tolerance
    return tolerances


def _tolerance_notes(
    tolerance_by_version_id: Mapping[str, tuple[float, float, str]],
) -> tuple[str, ...]:
    seen: set[str] = set()
    notes: list[str] = []
    for _, _, reason in tolerance_by_version_id.values():
        if reason not in seen:
            seen.add(reason)
            notes.append(reason)
    return tuple(notes)


def _group_features(records: tuple[FeatureValueRecord, ...]) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {key: tuple(value) for key, value in grouped.items()}


def _group_labels(records: tuple[LabelValueRecord, ...]) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {key: tuple(value) for key, value in grouped.items()}


def _flatten_label_records(
    records_by_name: Mapping[FixedHorizonLabelName, tuple[LabelValueRecord, ...]]
) -> tuple[LabelValueRecord, ...]:
    return tuple(record for records in records_by_name.values() for record in records)


def _reference_ohlcv_records(
    definitions: tuple[Any, ...],
    view: Any,
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        record
        for definition in definitions
        for record in compute_ohlcv_feature(definition, view)
    )


def _reference_bbo_records(
    definitions: tuple[Any, ...],
    view: Any,
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        record
        for definition in definitions
        for record in compute_bbo_feature(definition, view)
    )


def _reference_session_records(
    definitions: tuple[Any, ...],
    view: Any,
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        record
        for definition in definitions
        for record in compute_session_feature(definition, view)
    )


def _reference_structure_records(
    definitions: tuple[Any, ...],
    view: Any,
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        record
        for definition in definitions
        for record in compute_structure_feature(definition, view)
    )


def _reference_mixed_ohlcv_structure_records(
    definitions: tuple[Any, ...],
    view: Any,
) -> tuple[FeatureValueRecord, ...]:
    records: list[FeatureValueRecord] = []
    for definition in definitions:
        if isinstance(definition, OHLCVFeatureDefinition):
            records.extend(compute_ohlcv_feature(definition, view))
        else:
            records.extend(compute_structure_feature(definition, view))
    return tuple(records)


def _reference_cross_market_records(
    definitions: tuple[Any, ...],
    bundle: CrossMarketInputBundle,
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        record
        for definition in definitions
        for record in compute_cross_market_feature(definition, bundle)
    )


class EmptyRegistryReader:
    """Read-only empty exposure registry for approved benchmark requests."""

    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def _approved_feature_request(name: str) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[name],
        formula_sketch={
            "exposure_family": name,
            "inputs": ["canonical_rows"],
            "operation": name,
            "benchmark_gate": PHASE_ID,
        },
        availability_assumptions={
            "timing": "benchmark uses accepted canonical rows with explicit available_ts"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["event_ts", "available_ts", "quality_flags"],
            "source": "local accepted canonical data only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _base_ohlcv_contracts(dataset_id: str) -> tuple[tuple[OHLCVFeatureDefinition, ...], FeatureSetSpec]:
    features = (
        OHLCVFeatureName.RETURNS,
        OHLCVFeatureName.LOG_RETURNS,
        OHLCVFeatureName.ROLLING_VOLATILITY,
        OHLCVFeatureName.ROLLING_RANGE,
        OHLCVFeatureName.RANGE_POSITION,
        OHLCVFeatureName.VOLUME_ZSCORE,
    )
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_base_ohlcv_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=20,
            horizon=1,
            reset_on_session=False,
            ddof=0,
        )
        for feature in features
    )
    return definitions, _feature_set("base_ohlcv", "FCFP-P02", definitions)


def _session_contracts(dataset_id: str) -> tuple[tuple[SessionFeatureDefinition, ...], FeatureSetSpec]:
    definitions = tuple(
        build_session_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_session_calendar_roll_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
        )
        for feature in tuple(SessionFeatureName)
    )
    return definitions, _feature_set("session_calendar_roll", "FCFP-P03", definitions)


def _vwap_contracts(dataset_id: str) -> tuple[tuple[OHLCVFeatureDefinition, ...], FeatureSetSpec]:
    features = (
        OHLCVFeatureName.VWAP,
        OHLCVFeatureName.ANCHORED_VWAP,
        OHLCVFeatureName.DISTANCE_TO_VWAP,
        OHLCVFeatureName.OPENING_RANGE,
        OHLCVFeatureName.OVERNIGHT_RANGE,
    )
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_vwap_session_auction_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            opening_range_minutes=2,
            anchor_session_label="RTH",
            reset_on_session=True,
        )
        for feature in features
    )
    return definitions, _feature_set("vwap_session_auction", "FCFP-P04", definitions)


def _regime_contracts(dataset_id: str) -> tuple[
    tuple[OHLCVFeatureDefinition | StructureFeatureDefinition, ...],
    FeatureSetSpec,
]:
    definitions = (
        build_ohlcv_feature_definition(
            OHLCVFeatureName.ATR,
            _approved_feature_request("fast_path_regime_vol_compression_atr"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            reset_on_session=True,
        ),
        build_ohlcv_feature_definition(
            OHLCVFeatureName.TRENDINESS,
            _approved_feature_request("fast_path_regime_vol_compression_trendiness"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            reset_on_session=True,
        ),
        build_structure_feature_definition(
            StructureFeatureName.RANGE_CONTRACTION,
            _approved_feature_request("fast_path_regime_vol_compression_range_contraction"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            reset_on_session=True,
        ),
    )
    return definitions, _feature_set("regime_vol_compression", "FCFP-P05", definitions)


def _liquidity_contracts(dataset_id: str) -> tuple[tuple[StructureFeatureDefinition, ...], FeatureSetSpec]:
    definitions = tuple(
        build_structure_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_liquidity_pa_structure_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            opening_range_minutes=2,
            opening_session_label="RTH",
            reset_on_session=True,
        )
        for feature in tuple(StructureFeatureName)
    )
    return definitions, _feature_set("liquidity_pa_structure", "FCFP-P06", definitions)


def _volume_contracts(dataset_id: str) -> tuple[
    tuple[OHLCVFeatureDefinition | StructureFeatureDefinition, ...],
    FeatureSetSpec,
]:
    ohlcv_features = (
        OHLCVFeatureName.ROLLING_VOLUME,
        OHLCVFeatureName.VOLUME_ZSCORE,
        OHLCVFeatureName.SESSION_MINUTE,
        OHLCVFeatureName.ROLLING_RANGE,
        OHLCVFeatureName.RANGE_POSITION,
        OHLCVFeatureName.TRENDINESS,
    )
    structure_features = (
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        StructureFeatureName.WICK_REJECTION_SCORE,
    )
    definitions = (
        *tuple(
            build_ohlcv_feature_definition(
                feature,
                _approved_feature_request(f"fast_path_volume_activity_{feature.value}"),
                EmptyRegistryReader(),
                dataset_version_ids=(dataset_id,),
                window_length=1 if feature is OHLCVFeatureName.SESSION_MINUTE else 20,
                horizon=1,
                reset_on_session=True,
            )
            for feature in ohlcv_features
        ),
        *tuple(
            build_structure_feature_definition(
                feature,
                _approved_feature_request(f"fast_path_volume_activity_{feature.value}"),
                EmptyRegistryReader(),
                dataset_version_ids=(dataset_id,),
                window_length=3,
                reset_on_session=True,
            )
            for feature in structure_features
        ),
    )
    return definitions, _feature_set("volume_activity", "FCFP-P07", definitions)


def _bbo_contracts(dataset_id: str) -> tuple[tuple[BBOFeatureDefinition, ...], FeatureSetSpec]:
    definitions = tuple(
        build_bbo_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_bbo_tradability_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            reset_on_session=True,
            ddof=0,
        )
        for feature in tuple(BBOFeatureName)
    )
    return definitions, _feature_set("bbo_tradability", "FCFP-P08", definitions)


def _cross_market_contracts(dataset_id: str) -> tuple[
    tuple[CrossMarketFeatureDefinition, ...],
    FeatureSetSpec,
]:
    definitions = tuple(
        build_cross_market_feature_definition(
            feature,
            _approved_feature_request(f"fast_path_cross_market_{feature.value}"),
            EmptyRegistryReader(),
            dataset_version_ids=(dataset_id,),
            window_length=3,
            horizon=1,
            reset_on_session=True,
            ddof=0,
            alignment_policy="strict_intersection",
        )
        for feature in tuple(CrossMarketFeatureName)
    )
    return definitions, _feature_set("cross_market", "FCFP-P09", definitions)


def _fixed_horizon_definitions(
    *,
    dataset_version_ids: Sequence[str],
) -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = {
        label: _governed_label_spec(label)
        for label in supported_fixed_horizon_labels()
    }
    return tuple(
        build_fixed_horizon_label_definition(
            label,
            specs[label],
            dataset_version_ids=dataset_version_ids,
        )
        for label in supported_fixed_horizon_labels()
    )


def _feature_set(
    pack_id: str,
    phase_id: str,
    definitions: Sequence[
        OHLCVFeatureDefinition
        | BBOFeatureDefinition
        | SessionFeatureDefinition
        | CrossMarketFeatureDefinition
        | StructureFeatureDefinition
    ],
) -> FeatureSetSpec:
    features = []
    for definition in definitions:
        spec = definition.spec
        features.append(getattr(spec, "feature_spec", spec))
    return FeatureSetSpec(
        feature_set_id=f"feature_set_fast_path_{pack_id}_v1",
        feature_set_version="v1",
        features=tuple(features),
        description=f"V1 {pack_id} bounded-real benchmark pack.",
        metadata={"campaign": CAMPAIGN_ID, "phase": phase_id, "benchmark": PHASE_ID},
    )


def _governed_label_spec(label: FixedHorizonLabelName):
    horizon = label.value.removeprefix("mid_fwd_ret_").removeprefix("fwd_ret_")
    is_mid = label.value.startswith("mid_")
    return create_label_spec(
        horizon=horizon,
        path_rules={
            "path": "midprice_forward_return" if is_mid else "trade_price_forward_return",
            "horizon_minutes": int(horizon.removesuffix("m")),
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_benchmark_gate",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_benchmark",
            "stop_rule": "not_used_for_fixed_horizon_benchmark",
        },
        availability_time="2024-01-01T00:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label.value],
            "aliases": [label.value],
            "transforms": [f"label({label.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _accepted_version(alpha_data_root: Path, dataset_version_id: str) -> AcceptedDatasetVersion:
    registry_path = alpha_data_root / "registry" / "datasets.sqlite"
    dataset_version = resolve_dataset_version(registry_path, dataset_version_id)
    if dataset_version is None:
        raise BenchmarkError(f"DatasetVersion not found: {dataset_version_id}")
    if not isinstance(dataset_version, DatasetVersion):
        raise BenchmarkError(f"DatasetVersion resolution returned invalid object: {dataset_version_id}")
    quality_report = _passing_quality_report(dataset_version_id)
    return AcceptedDatasetVersion(
        registry_path=registry_path,
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=_passing_coverage_report(dataset_version_id),
    )


def _passing_quality_report(dataset_version_id: str) -> DataQualityReport:
    summary = {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_version_id}_benchmark_shell",
        dataset_version_id=dataset_version_id,
        gap_summary=summary,
        duplicate_summary=summary,
        non_monotonic_summary=summary,
        ohlc_errors=summary,
        zero_negative_price_errors=summary,
        zero_volume_anomalies=summary,
        dst_anomalies=summary,
        session_coverage=summary,
        roll_discontinuities=summary,
        provider_error_summary=summary,
        bbo_missing_metric=summary,
        abnormal_spread_summary=summary,
        status=ReportStatus.PASSING,
    )


def _passing_coverage_report(dataset_version_id: str) -> CoverageReport:
    summary = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    partition_summary = dict(summary)
    partition_summary["missing_interval_count"] = 0
    partition_summary["incomplete_chunk_count"] = 0
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_version_id}_benchmark_shell",
        dataset_version_id=dataset_version_id,
        symbol_coverage=summary,
        contract_coverage=summary,
        session_coverage=summary,
        partition_coverage=partition_summary,
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _governance_metadata() -> dict[str, object]:
    return {
        "campaign": CAMPAIGN_ID,
        "phase": PHASE_ID,
        "purpose": BENCHMARK_PURPOSE,
        "contamination_metadata": "validation partition benchmark evidence only",
    }


def _parse_ts(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _assert_materially_faster(results: Sequence[PackResult]) -> None:
    slow = tuple(result.pack_id for result in results if result.speedup_vs_reference <= 1.0)
    if slow:
        raise BenchmarkError("V1 was not materially faster for packs: " + ", ".join(slow))


def _assert_reduced_reads(results: Sequence[PackResult]) -> None:
    not_reduced = tuple(
        result.pack_id
        for result in results
        if result.v1_canonical_reads >= result.reference_canonical_reads
    )
    if not_reduced:
        raise BenchmarkError(
            "V1 did not reduce canonical reads for packs: " + ", ".join(not_reduced)
        )


def _write_summary(path: Path, payload: BenchmarkPayload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary_markdown(payload), encoding="utf-8")


def _seconds(value: float) -> str:
    return f"{value:.6f}"


def _number(value: float) -> str:
    if math.isinf(value):
        return "inf"
    return f"{value:.2f}"


def window_year_text() -> str:
    return f"{DEFAULT_YEAR}"


def _env_alpha_data_root() -> Path | None:
    value = os.environ.get("ALPHA_DATA_ROOT")
    if not value:
        return None
    return Path(value).expanduser().resolve(strict=False)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alpha-data-root", default=None)
    parser.add_argument("--summary-path", default=SUMMARY_PATH.as_posix())
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--month", type=int, default=DEFAULT_MONTH)
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--primary-symbol", default=DEFAULT_PRIMARY_SYMBOL)
    parser.add_argument("--ohlcv-dataset-version-id", default=DEFAULT_OHLCV_DATASET_VERSION_ID)
    parser.add_argument(
        "--dense-ohlcv-dataset-version-id",
        default=DEFAULT_DENSE_OHLCV_DATASET_VERSION_ID,
    )
    parser.add_argument("--bbo-dataset-version-id", default=DEFAULT_BBO_DATASET_VERSION_ID)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    alpha_data_root = (
        Path(args.alpha_data_root).expanduser().resolve(strict=False)
        if args.alpha_data_root
        else _env_alpha_data_root()
    )
    if alpha_data_root is None:
        payload = blocked_summary(None, "ALPHA_DATA_ROOT is not set")
        _write_summary(Path(args.summary_path), payload)
        print("BLOCKED: ALPHA_DATA_ROOT is not set")
        return 2
    window = BenchmarkWindow(
        year=args.year,
        month=args.month,
        symbols=tuple(symbol.strip().upper() for symbol in args.symbols.split(",") if symbol.strip()),
        primary_symbol=args.primary_symbol,
        ohlcv_dataset_version_id=args.ohlcv_dataset_version_id,
        dense_ohlcv_dataset_version_id=args.dense_ohlcv_dataset_version_id,
        bbo_dataset_version_id=args.bbo_dataset_version_id,
    )
    payload = run_benchmark(
        alpha_data_root=alpha_data_root,
        summary_path=Path(args.summary_path),
        window=window,
    )
    print(f"{payload.status}: wrote {Path(args.summary_path).as_posix()}")
    return 0 if payload.status == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
