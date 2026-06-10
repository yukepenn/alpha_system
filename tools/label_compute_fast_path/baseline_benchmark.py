"""Bounded reference-label benchmark for LABEL_COMPUTE_FAST_PATH_V1.

The entrypoint times only the dependency-free reference label family compute
functions over already-canonical local rows. It does not materialize values,
open the label registry, or write benchmark payloads.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.canonical_loader import (
    load_canonical_bbo_rows,
    load_canonical_ohlcv_rows,
)
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.features.input_views import BBOInputRow, BBOInputView, OHLCVInputRow, OHLCVInputView
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_label,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_label,
)
from alpha_system.labels.families.path import (
    PathLabelName,
    build_path_label_definition,
    compute_path_label,
)
from alpha_system.labels.roll_guard import ROLL_GUARD_VERSION, ROLL_POLICY_ID

DEFAULT_ALPHA_DATA_ROOT = Path("~/alpha_data/alpha_system").expanduser()
DEFAULT_CANONICAL_RELATIVE_ROOT = Path("databento") / "canonical" / "glbx_mdp3"
DATASET_INVENTORY_PATH = Path("configs/labels/scaleout/dataset_version_inventory.json")
DEFAULT_SYMBOL = "ES"
DEFAULT_YEAR = 2024
DEFAULT_START_TS = "2024-06-01T00:00:00+00:00"
DEFAULT_END_TS = "2024-07-01T00:00:00+00:00"

BASE_FIXED_HORIZONS = (1, 3, 5, 10, 15, 30)
EXTENDED_FIXED_HORIZONS = (60, 120, 240)
COST_HORIZONS = (1, 3, 5, 10, 15, 30, 60, 120, 240)
PATH_HORIZONS = (5, 10, 15, 30, 60, 120, 240)
ACCEPTED_FUTSUB_YEARS = tuple(range(2019, 2027))
FUTSUB_SYMBOLS = ("ES", "NQ", "RTY")
ROW_BUDGET_PER_UNIT = 550_000
PATH_METRICS_PER_UNIT = 4
COST_LABELS_PER_HORIZON = 2

FAMILY_ORDER = (
    "fixed_base",
    "fixed_extended",
    "close_out",
    "cost_adjusted",
    "path",
)


class BaselineBenchmarkError(ValueError):
    """Raised when the bounded reference benchmark cannot proceed."""


@dataclass(frozen=True, slots=True)
class SliceDefinition:
    """Value-free identity of the bounded benchmark slice."""

    symbol: str
    year: int
    start_ts: str
    end_ts: str
    ohlcv_dataset_version_id: str
    bbo_dataset_version_id: str
    ohlcv_row_count: int
    bbo_row_count: int
    roll_event_count: int
    maintenance_gap_count: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "symbol": self.symbol,
            "year": self.year,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "ohlcv_dataset_version_id": self.ohlcv_dataset_version_id,
            "bbo_dataset_version_id": self.bbo_dataset_version_id,
            "ohlcv_row_count": self.ohlcv_row_count,
            "bbo_row_count": self.bbo_row_count,
            "roll_event_count": self.roll_event_count,
            "maintenance_gap_count": self.maintenance_gap_count,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Value-free timing result for one benchmark family."""

    family: str
    definitions: int
    elapsed_seconds: float
    rows_processed: int
    records_emitted: int
    full_window_rows_basis: int
    notes: str = ""

    @property
    def rows_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.rows_processed / self.elapsed_seconds

    @property
    def full_window_runtime_estimate_seconds(self) -> float:
        rate = self.rows_per_second
        if rate <= 0:
            return 0.0
        return self.full_window_rows_basis / rate

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "family": self.family,
            "definitions": self.definitions,
            "elapsed_seconds": self.elapsed_seconds,
            "rows_processed": self.rows_processed,
            "records_emitted": self.records_emitted,
            "rows_per_second": self.rows_per_second,
            "full_window_rows_basis": self.full_window_rows_basis,
            "full_window_runtime_estimate_seconds": (
                self.full_window_runtime_estimate_seconds
            ),
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    """Complete value-free benchmark summary."""

    slice_definition: SliceDefinition
    results: tuple[BenchmarkResult, ...]
    timing_mode: str = "compute_only"
    reference_engine: str = "alpha_system.labels.families.*.compute_*_label"
    production_registry_write: bool = False
    full_window_timed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "alpha_system.label_compute_fast_path.baseline_benchmark.v1",
            "timing_mode": self.timing_mode,
            "reference_engine": self.reference_engine,
            "production_registry_write": self.production_registry_write,
            "full_window_timed": self.full_window_timed,
            "slice": self.slice_definition.to_dict(),
            "results": [result.to_dict() for result in self.results],
        }

    def to_markdown(self) -> str:
        slice_dict = self.slice_definition.to_dict()
        lines = [
            "# LCFP-P01 Reference Label Baseline Benchmark",
            "",
            "This is a value-free, bounded compute-only timing summary. It records",
            "counts, elapsed time, rows per second, and extrapolated runtime only.",
            "No label values, market prices, Parquet payloads, SQLite rows, or JSONL",
            "payloads are included.",
            "",
            "## Timing Contract",
            "",
            f"- Reference engine: `{self.reference_engine}`",
            f"- Timing mode: `{self.timing_mode}`",
            f"- Production registry write occurred: `{str(self.production_registry_write).lower()}`",
            f"- Full-window reference timing occurred: `{str(self.full_window_timed).lower()}`",
            "- Full-window numbers below are extrapolations from bounded measured rows/sec.",
            "",
            "## Bounded Slice",
            "",
        ]
        for key, value in slice_dict.items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(
            [
                "",
                "The default slice is a single roll-containing symbol-month. Roll presence is",
                "counted from the analytic CME equity-index quarterly roll calendar; maintenance",
                "gaps are counted from one-minute OHLCV timestamp gaps in the bounded slice.",
                "",
                "## Results",
                "",
                "| Family | Definitions | Elapsed sec | Rows processed | Records emitted | Rows/sec | Full-window row basis | Estimated full-window sec | Notes |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for result in self.results:
            lines.append(
                "| "
                + " | ".join(
                    (
                        f"`{result.family}`",
                        str(result.definitions),
                        f"{result.elapsed_seconds:.6f}",
                        str(result.rows_processed),
                        str(result.records_emitted),
                        f"{result.rows_per_second:.2f}",
                        str(result.full_window_rows_basis),
                        f"{result.full_window_runtime_estimate_seconds:.2f}",
                        result.notes or "",
                    )
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "## Extrapolation Basis",
                "",
                "- Accepted FUTSUB years: `2019` through `2026`; blocked `2018` is excluded.",
                "- Symbols: `ES`, `NQ`, `RTY`.",
                f"- Per-unit row budget: `{ROW_BUDGET_PER_UNIT}` rows.",
                "- Fixed base basis: 3 symbols x 8 years x 6 horizons x row budget.",
                "- Extended basis: 3 symbols x 8 years x 3 horizons x row budget.",
                "- Close-out basis: 3 symbols x 8 years x 2 symbolic horizons x row budget.",
                "- Cost-adjusted basis: 3 symbols x 8 years x 9 horizons x 2 existing cost/spread labels x row budget.",
                "- Path basis: 3 symbols x 8 years x 7 horizons x 4 existing path metrics x row budget.",
                "",
                "## Safety",
                "",
                "This command does not instantiate `LabelRegistry`, does not call",
                "`materialize_labels`, does not write value stores, and does not mutate",
                "`$ALPHA_DATA_ROOT/registry/labels.sqlite`.",
                "",
            ]
        )
        return "\n".join(lines)


def run_benchmark(
    *,
    alpha_data_root: Path,
    canonical_root: Path,
    symbol: str,
    year: int,
    start_ts: str,
    end_ts: str,
    families: Sequence[str],
) -> BenchmarkSummary:
    """Load the bounded slice and time requested reference families."""

    inventory = _load_dataset_inventory(DATASET_INVENTORY_PATH)
    ohlcv_dataset_id = _dataset_id(inventory, schema="ohlcv_1m", year=year)
    bbo_dataset_id = _dataset_id(inventory, schema="bbo_1m", year=year)

    ohlcv_mappings = load_canonical_ohlcv_rows(
        canonical_root=canonical_root,
        dataset_version_id=ohlcv_dataset_id,
        symbol=symbol,
        start_ts=start_ts,
        end_ts=end_ts,
        partition_schema="ohlcv_1m",
    )
    bbo_mappings = load_canonical_bbo_rows(
        canonical_root=canonical_root,
        dataset_version_id=bbo_dataset_id,
        symbol=symbol,
        start_ts=start_ts,
        end_ts=end_ts,
        partition_schema="bbo_1m",
    )
    if not ohlcv_mappings:
        raise BaselineBenchmarkError("bounded slice loaded zero OHLCV rows")
    if not bbo_mappings:
        raise BaselineBenchmarkError("bounded slice loaded zero BBO rows")

    ohlcv_view = OHLCVInputView(tuple(_ohlcv_input_row(row) for row in ohlcv_mappings))
    bbo_view = BBOInputView(tuple(_bbo_input_row(row) for row in bbo_mappings))
    slice_definition = SliceDefinition(
        symbol=symbol.upper(),
        year=year,
        start_ts=start_ts,
        end_ts=end_ts,
        ohlcv_dataset_version_id=ohlcv_dataset_id,
        bbo_dataset_version_id=bbo_dataset_id,
        ohlcv_row_count=len(ohlcv_view.rows),
        bbo_row_count=len(bbo_view.rows),
        roll_event_count=_roll_event_count(symbol, start_ts, end_ts),
        maintenance_gap_count=_maintenance_gap_count(ohlcv_view.rows),
    )

    family_set = _normalize_families(families)
    results: list[BenchmarkResult] = []
    if "fixed_base" in family_set:
        results.append(_benchmark_fixed_base(ohlcv_view, start_ts, ohlcv_dataset_id))
    if "fixed_extended" in family_set:
        results.append(_benchmark_fixed_extended(ohlcv_view, start_ts, ohlcv_dataset_id))
    if "close_out" in family_set:
        results.append(_benchmark_close_out(ohlcv_view, start_ts, ohlcv_dataset_id))
    if "cost_adjusted" in family_set:
        results.append(_benchmark_cost_adjusted(bbo_view, ohlcv_view, start_ts, bbo_dataset_id))
    if "path" in family_set:
        results.append(_benchmark_path(ohlcv_view, start_ts, ohlcv_dataset_id))

    return BenchmarkSummary(slice_definition=slice_definition, results=tuple(results))


def _benchmark_fixed_base(
    view: OHLCVInputView,
    availability_time: str,
    dataset_version_id: str,
) -> BenchmarkResult:
    names = tuple(_fixed_name(horizon) for horizon in BASE_FIXED_HORIZONS)
    definitions = tuple(
        build_fixed_horizon_label_definition(
            name,
            _fixed_horizon_spec(name, availability_time=availability_time),
            dataset_version_ids=(dataset_version_id,),
        )
        for name in names
    )

    started = perf_counter()
    record_count = 0
    for definition in definitions:
        record_count += len(compute_fixed_horizon_label(definition, view))
    elapsed = perf_counter() - started
    return BenchmarkResult(
        family="fixed_base",
        definitions=len(definitions),
        elapsed_seconds=elapsed,
        rows_processed=len(view.rows) * len(definitions),
        records_emitted=record_count,
        full_window_rows_basis=_full_window_basis("fixed_base"),
        notes="FUTSUB-P16 horizons 1/3/5/10/15/30m",
    )


def _benchmark_fixed_extended(
    view: OHLCVInputView,
    availability_time: str,
    dataset_version_id: str,
) -> BenchmarkResult:
    names = tuple(_fixed_name(horizon) for horizon in EXTENDED_FIXED_HORIZONS)
    definitions = tuple(
        build_fixed_horizon_label_definition(
            name,
            _fixed_horizon_spec(name, availability_time=availability_time),
            dataset_version_ids=(dataset_version_id,),
        )
        for name in names
    )

    started = perf_counter()
    record_count = 0
    for definition in definitions:
        record_count += len(compute_fixed_horizon_label(definition, view))
    elapsed = perf_counter() - started
    return BenchmarkResult(
        family="fixed_extended",
        definitions=len(definitions),
        elapsed_seconds=elapsed,
        rows_processed=len(view.rows) * len(definitions),
        records_emitted=record_count,
        full_window_rows_basis=_full_window_basis("fixed_extended"),
        notes="FUTSUB-P17 horizons 60/120/240m",
    )


def _benchmark_close_out(
    view: OHLCVInputView,
    availability_time: str,
    dataset_version_id: str,
) -> BenchmarkResult:
    names = (FixedHorizonLabelName.SESSION_CLOSE, FixedHorizonLabelName.MAINTENANCE_FLAT)
    definitions = tuple(
        build_fixed_horizon_label_definition(
            name,
            _fixed_horizon_spec(name, availability_time=availability_time),
            dataset_version_ids=(dataset_version_id,),
        )
        for name in names
    )

    started = perf_counter()
    record_count = 0
    for definition in definitions:
        record_count += len(compute_fixed_horizon_label(definition, view))
    elapsed = perf_counter() - started
    return BenchmarkResult(
        family="close_out",
        definitions=len(definitions),
        elapsed_seconds=elapsed,
        rows_processed=len(view.rows) * len(definitions),
        records_emitted=record_count,
        full_window_rows_basis=_full_window_basis("close_out"),
        notes="FUTSUB-P18 session_close and maintenance_flat",
    )


def _benchmark_cost_adjusted(
    bbo_view: BBOInputView,
    ohlcv_view: OHLCVInputView,
    availability_time: str,
    dataset_version_id: str,
) -> BenchmarkResult:
    definitions = tuple(
        build_cost_adjusted_label_definition(
            label_name,
            _cost_adjusted_spec(
                label_name,
                horizon_minutes=horizon,
                availability_time=availability_time,
            ),
            dataset_version_ids=(dataset_version_id,),
        )
        for horizon in COST_HORIZONS
        for label_name in (
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        )
    )

    started = perf_counter()
    record_count = 0
    for definition in definitions:
        record_count += len(
            compute_cost_adjusted_label(
                definition,
                bbo_view,
                trade_rows=ohlcv_view.rows,
            )
        )
    elapsed = perf_counter() - started
    return BenchmarkResult(
        family="cost_adjusted",
        definitions=len(definitions),
        elapsed_seconds=elapsed,
        rows_processed=len(bbo_view.rows) * len(definitions),
        records_emitted=record_count,
        full_window_rows_basis=_full_window_basis("cost_adjusted"),
        notes="FUTSUB-P19 horizons 1..240m x cost/spread labels",
    )


def _benchmark_path(
    view: OHLCVInputView,
    availability_time: str,
    dataset_version_id: str,
) -> BenchmarkResult:
    definitions = tuple(
        build_path_label_definition(
            label_name,
            _path_spec(horizon_steps=horizon, availability_time=availability_time),
            dataset_version_ids=(dataset_version_id,),
        )
        for horizon in PATH_HORIZONS
        for label_name in PathLabelName
    )

    started = perf_counter()
    record_count = 0
    for definition in definitions:
        record_count += len(compute_path_label(definition, view))
    elapsed = perf_counter() - started
    return BenchmarkResult(
        family="path",
        definitions=len(definitions),
        elapsed_seconds=elapsed,
        rows_processed=len(view.rows) * len(definitions),
        records_emitted=record_count,
        full_window_rows_basis=_full_window_basis("path"),
        notes="FUTSUB-P20 horizons 5..240m x MFE/MAE/TBS/triple-barrier",
    )


def _fixed_horizon_spec(
    name: FixedHorizonLabelName,
    *,
    availability_time: str,
) -> LabelSpec:
    if name is FixedHorizonLabelName.SESSION_CLOSE:
        return _close_out_spec(name, availability_time=availability_time)
    if name is FixedHorizonLabelName.MAINTENANCE_FLAT:
        return _close_out_spec(name, availability_time=availability_time)
    horizon = _horizon_minutes(name)
    return create_label_spec(
        horizon=f"{horizon}m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": horizon,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
            "terminal_key": "series_id+contract_id+event_ts",
            "roll_policy_id": ROLL_POLICY_ID,
            "roll_guard_version": ROLL_GUARD_VERSION,
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_family",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [name.value.replace("_ret_", "_return_")],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _close_out_spec(
    name: FixedHorizonLabelName,
    *,
    availability_time: str,
) -> LabelSpec:
    return create_label_spec(
        horizon=name.value,
        path_rules={
            "path": "trade_price_close_out_return",
            "close_out_terminal": name.value,
            "terminal_rule": "exact session/maintenance close-out terminal",
            "terminal_key": "series_id+contract_id+event_ts",
            "terminal_scope": "series_id+contract_id+close_out_boundary",
            "roll_policy_id": ROLL_POLICY_ID,
            "roll_guard_version": ROLL_GUARD_VERSION,
        },
        cost_model={
            "model": "gross_unadjusted_close_out_return",
            "adjustment_scope": "not_applied_in_close_out_family",
        },
        target_stop_rules={
            "target_rule": "not_used_for_close_out_return",
            "stop_rule": "not_used_for_close_out_return",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [f"close_out_{name.value}"],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _cost_adjusted_spec(
    label_name: CostAdjustedLabelName,
    *,
    horizon_minutes: int,
    availability_time: str,
) -> LabelSpec:
    if label_name is CostAdjustedLabelName.COST_ADJUSTED_FWD_RET:
        cost_model: dict[str, object] = {
            "model": "spread_plus_bps",
            "spread_adjustment": "half_spread_round_trip",
            "fixed_cost_bps": 1.0,
        }
    else:
        cost_model = {
            "model": "spread_adjusted",
            "spread_adjustment": "half_spread_round_trip",
        }
    return create_label_spec(
        horizon=f"{horizon_minutes}m",
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "exact event_ts match with valid BBO only",
            "horizon_steps": horizon_minutes,
            "horizon_minutes": horizon_minutes,
        },
        cost_model=cost_model,
        target_stop_rules={
            "target_rule": "disabled_for_cost_adjusted_reference_benchmark",
            "stop_rule": "disabled_for_cost_adjusted_reference_benchmark",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"{label_name.value}_{horizon_minutes}m"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _path_spec(
    *,
    horizon_steps: int,
    availability_time: str,
) -> LabelSpec:
    path_ids = [f"path_{name.value}_{horizon_steps}m" for name in PathLabelName]
    return create_label_spec(
        horizon=f"{horizon_steps}_trade_bars",
        path_rules={
            "path": "ohlcv_trade_truth_forward_path",
            "horizon_steps": horizon_steps,
            "price_field": "close",
            "direction": "long",
            "trade_truth_predicate": "alpha_system.features.semantics.is_real_trade_bar",
        },
        cost_model={"model": "gross_path_labels_unadjusted", "reason": "no cost adjustment"},
        target_stop_rules={
            "target_return": 0.0025,
            "stop_return": -0.0025,
            "same_bar_policy": "ambiguous",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": path_ids,
            "aliases": [name.value for name in PathLabelName],
            "transforms": [f"label({label_id})" for label_id in path_ids],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _ohlcv_input_row(row: Mapping[str, object]) -> OHLCVInputRow:
    record = CanonicalBarRecord.from_mapping(row)
    return OHLCVInputRow(
        instrument_id=record.instrument_id,
        contract_id=record.contract_id,
        series_id=record.series_id,
        bar_start_ts=record.bar_start_ts,
        bar_end_ts=record.bar_end_ts,
        event_ts=record.event_ts,
        available_ts=record.available_ts,
        ingested_at=record.ingested_at,
        open=record.open,
        high=record.high,
        low=record.low,
        close=record.close,
        volume=record.volume,
        data_version=record.data_version,
        quality_flags=record.quality_flags,
        session_label=record.session_label,
    )


def _bbo_input_row(row: Mapping[str, object]) -> BBOInputRow:
    record = CanonicalBBORecord.from_mapping(row)
    return BBOInputRow(
        instrument_id=record.instrument_id,
        contract_id=record.contract_id,
        series_id=record.series_id,
        bar_start_ts=record.bar_start_ts,
        bar_end_ts=record.bar_end_ts,
        event_ts=record.event_ts,
        available_ts=record.available_ts,
        ingested_at=record.ingested_at,
        bid=record.bid,
        ask=record.ask,
        bid_size=record.bid_size,
        ask_size=record.ask_size,
        mid=record.mid,
        spread=record.spread,
        data_version=record.data_version,
        quality_flags=record.quality_flags,
        session_label=record.session_label,
        spread_ticks=record.spread_ticks,
        microprice=record.microprice,
        bid_order_count=record.bid_order_count,
        ask_order_count=record.ask_order_count,
    )


def _load_dataset_inventory(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BaselineBenchmarkError(f"dataset inventory could not be read: {path}") from exc
    if not isinstance(payload, Mapping):
        raise BaselineBenchmarkError("dataset inventory must be a mapping")
    return payload


def _dataset_id(inventory: Mapping[str, object], *, schema: str, year: int) -> str:
    schemas = inventory.get("schemas")
    if not isinstance(schemas, Mapping):
        raise BaselineBenchmarkError("dataset inventory missing schemas")
    schema_payload = schemas.get(schema)
    if not isinstance(schema_payload, Mapping):
        raise BaselineBenchmarkError(f"dataset inventory missing schema {schema}")
    year_payload = schema_payload.get(str(year))
    if not isinstance(year_payload, Mapping):
        raise BaselineBenchmarkError(f"dataset inventory missing year {year}")
    dataset_id = year_payload.get("dataset_version_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise BaselineBenchmarkError(f"dataset inventory missing DatasetVersion for {schema}/{year}")
    return dataset_id


def _full_window_basis(family: str) -> int:
    year_count = len(ACCEPTED_FUTSUB_YEARS)
    symbol_count = len(FUTSUB_SYMBOLS)
    if family == "fixed_base":
        return symbol_count * year_count * len(BASE_FIXED_HORIZONS) * ROW_BUDGET_PER_UNIT
    if family == "fixed_extended":
        return symbol_count * year_count * len(EXTENDED_FIXED_HORIZONS) * ROW_BUDGET_PER_UNIT
    if family == "close_out":
        return symbol_count * year_count * 2 * ROW_BUDGET_PER_UNIT
    if family == "cost_adjusted":
        return (
            symbol_count
            * year_count
            * len(COST_HORIZONS)
            * COST_LABELS_PER_HORIZON
            * ROW_BUDGET_PER_UNIT
        )
    if family == "path":
        return (
            symbol_count
            * year_count
            * len(PATH_HORIZONS)
            * PATH_METRICS_PER_UNIT
            * ROW_BUDGET_PER_UNIT
        )
    raise BaselineBenchmarkError(f"unsupported family: {family}")


def _normalize_families(families: Sequence[str]) -> frozenset[str]:
    if not families or tuple(families) == ("all",):
        return frozenset(FAMILY_ORDER)
    unknown = tuple(family for family in families if family not in FAMILY_ORDER)
    if unknown:
        raise BaselineBenchmarkError("unsupported benchmark family: " + ", ".join(unknown))
    return frozenset(families)


def _fixed_name(horizon_minutes: int) -> FixedHorizonLabelName:
    return FixedHorizonLabelName(f"fwd_ret_{horizon_minutes}m")


def _horizon_minutes(name: FixedHorizonLabelName) -> int:
    token = name.value.removeprefix("mid_fwd_ret_").removeprefix("fwd_ret_")
    return int(token.removesuffix("m"))


def _roll_event_count(symbol: str, start_ts: str, end_ts: str) -> int:
    from alpha_system.data.foundation.rolls import (
        build_analytic_cme_equity_index_quarterly_roll_calendar,
    )

    start = _parse_dt(start_ts)
    end = _parse_dt(end_ts)
    records = build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=(symbol.upper(),),
        start_year=start.year,
        end_year=end.year,
    )
    return sum(1 for record in records if start.date() <= record.roll_date < end.date())


def _maintenance_gap_count(rows: Sequence[OHLCVInputRow]) -> int:
    ordered = sorted(rows, key=lambda row: row.event_ts)
    gaps = 0
    for previous, current in zip(ordered, ordered[1:], strict=False):
        delta_seconds = (current.event_ts - previous.event_ts).total_seconds()
        if 60 < delta_seconds <= 7_200:
            gaps += 1
    return gaps


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alpha-data-root", default=os.environ.get("ALPHA_DATA_ROOT"))
    parser.add_argument("--canonical-root")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--start-ts", default=DEFAULT_START_TS)
    parser.add_argument("--end-ts", default=DEFAULT_END_TS)
    parser.add_argument(
        "--family",
        action="append",
        choices=("all", *FAMILY_ORDER),
        default=None,
        help="Benchmark family to run; repeatable. Defaults to all.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    alpha_data_root = Path(args.alpha_data_root).expanduser() if args.alpha_data_root else DEFAULT_ALPHA_DATA_ROOT
    canonical_root = (
        Path(args.canonical_root).expanduser()
        if args.canonical_root
        else alpha_data_root / DEFAULT_CANONICAL_RELATIVE_ROOT
    )
    summary = run_benchmark(
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        symbol=args.symbol,
        year=args.year,
        start_ts=args.start_ts,
        end_ts=args.end_ts,
        families=tuple(args.family or ("all",)),
    )
    if args.format == "json":
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        print(summary.to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

