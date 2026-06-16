"""Restart-safe scaleout driver for governed FeaturePack materialization.

The driver is deliberately thin. Family formulas stay in the approved feature
family modules, canonical rows are loaded through the sanctioned loader used by
the seed operator, and registry writes go through ``FeatureStore`` via
``run_seed_feature_pack``.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.foundation.datasets import (
    DatasetAcceptanceState,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.features.pack_integrity import reconcile_registered_feature_pack_path
from alpha_system.features.store import FeatureStore
from alpha_system.governance.serialization import canonical_serialize

SCALEOUT_CONFIG_SCHEMA = "alpha_system.futures_substrate_scaleout.feature_scaleout_config.v1"
LABEL_SCALEOUT_CONFIG_SCHEMA = "alpha_system.futures_substrate_scaleout.label_scaleout_config.v1"
DEFAULT_SCALEOUT_CONFIG = "configs/features/scaleout/base_ohlcv.json"
DEFAULT_LABEL_SCALEOUT_CONFIG = "configs/labels/scaleout/fixed_horizon.json"
DEFAULT_POLICY_CONFIG = "configs/data/dataset_acceptance/futsub_p02_policy.json"
DEFAULT_ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
DEFAULT_BOUNDED_YEAR = 2024
SCALEOUT_ENGINE_V1 = "v1"
SCALEOUT_ENGINE_REFERENCE = "reference"
DEFAULT_SCALEOUT_ENGINE = SCALEOUT_ENGINE_V1
SCALEOUT_ENGINES = frozenset({SCALEOUT_ENGINE_V1, SCALEOUT_ENGINE_REFERENCE})
DEFAULT_CPU_WORKERS = 1
LABEL_CPU_WORKERS_ENV = "ALPHA_LABEL_CPU_WORKERS"
FORCE_RECOMPUTE_ENV = "ALPHA_SCALEOUT_FORCE_RECOMPUTE"
REFERENCE_LABEL_PRODUCER_ENGINE_ID = "alpha_system.labels.reference_engine.v1"
REFERENCE_LABEL_WORKER_MANIFEST_SCHEMA = "alpha_system.labels.reference.worker_manifest.v1"
REFERENCE_LABEL_THREADS_PER_WORKER = 2
SESSION_METADATA_ROLE_MARKER = "SESSION_METADATA_POINT_IN_TIME"
SESSION_METADATA_ROLE_FAMILIES = frozenset(
    {
        "session_calendar_maintenance",
        "liquidity_sweep_pa_structure",
        "cross_market_alignment",
    }
)
ELIGIBLE_ACCEPTANCE_STATES = frozenset(
    {
        DatasetAcceptanceState.ACCEPTED.value,
        DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS.value,
    }
)

_ACCEPTANCE_ROW_RE = re.compile(
    r"^\|\s*`(?P<schema>[^`]+)`\s*\|\s*(?P<year>\d{4})\s*\|\s*"
    r"`(?P<dataset>[^`]+)`\s*\|\s*`(?P<state>[^`]+)`\s*\|"
)


class ScaleoutError(ValueError):
    """Raised when scaleout planning or execution fails closed."""


@dataclass(frozen=True, slots=True)
class ScaleoutTarget:
    """Optional targeted/incremental selectors for a scaleout run."""

    family: str | None = None
    feature_ids: tuple[str, ...] = ()
    feature_groups: tuple[str, ...] = ()
    label_ids: tuple[str, ...] = ()
    label_groups: tuple[str, ...] = ()
    horizon_groups: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()
    years: tuple[int, ...] = ()
    dataset_version_ids: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        """Return true when at least one selector is present."""

        return bool(
            self.family
            or self.feature_ids
            or self.feature_groups
            or self.label_ids
            or self.label_groups
            or self.horizon_groups
            or self.symbols
            or self.years
            or self.dataset_version_ids
        )

    @property
    def label_targeted(self) -> bool:
        """Return true when label selectors are present."""

        return bool(self.label_ids or self.label_groups)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible target summary."""

        return {
            "family": self.family,
            "feature_ids": list(self.feature_ids),
            "feature_groups": list(self.feature_groups),
            "label_ids": list(self.label_ids),
            "label_groups": list(self.label_groups),
            "horizon_groups": list(self.horizon_groups),
            "symbols": list(self.symbols),
            "years": list(self.years),
            "dataset_version_ids": list(self.dataset_version_ids),
            "active": self.active,
        }


@dataclass(frozen=True, slots=True)
class ScaleoutDryRunEstimate:
    """Value-free dry-run estimate for selected scaleout units."""

    selected_unit_count: int
    planned_step_count: int
    symbol_count: int
    symbols: tuple[str, ...]
    year_count: int
    years: tuple[int, ...]
    dataset_version_ids: tuple[str, ...]
    estimated_rows_per_unit: int
    estimated_total_rows: int
    estimated_seconds_per_unit: float
    estimated_total_seconds: float
    unit_estimates: tuple[Mapping[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible estimate summary."""

        return {
            "selected_unit_count": self.selected_unit_count,
            "planned_step_count": self.planned_step_count,
            "symbol_count": self.symbol_count,
            "symbols": list(self.symbols),
            "year_count": self.year_count,
            "years": list(self.years),
            "dataset_version_ids": list(self.dataset_version_ids),
            "estimated_rows_per_unit": self.estimated_rows_per_unit,
            "estimated_total_rows": self.estimated_total_rows,
            "estimated_seconds_per_unit": self.estimated_seconds_per_unit,
            "estimated_total_seconds": self.estimated_total_seconds,
            "units": [dict(unit) for unit in self.unit_estimates],
        }


@dataclass(frozen=True, slots=True)
class ScaleoutWorkerPlan:
    """Effective CPU worker plan for one scaleout run or stage."""

    requested_workers: int
    effective_workers: int
    threads_per_worker: int
    available_cores: int
    reductions: tuple[str, ...] = ()

    @property
    def parallel_enabled(self) -> bool:
        return self.effective_workers > 1

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_workers": self.requested_workers,
            "effective_workers": self.effective_workers,
            "threads_per_worker": self.threads_per_worker,
            "available_cores": self.available_cores,
            "parallel_enabled": self.parallel_enabled,
            "reductions": list(self.reductions),
        }


@dataclass(frozen=True, slots=True)
class ScaleoutConfig:
    """Parsed feature scaleout configuration."""

    config_path: Path
    campaign_id: str
    phase_id: str
    family: str
    feature_names: tuple[str, ...]
    feature_groups: Mapping[str, tuple[str, ...]]
    label_names: tuple[str, ...]
    label_groups: Mapping[str, tuple[str, ...]]
    horizon_groups: Mapping[str, tuple[str, ...]]
    symbols: tuple[str, ...]
    years: tuple[int, ...]
    input_schemas: tuple[str, ...]
    horizons: tuple[str, ...]
    dense_grid_required: bool
    row_budget_per_unit: int
    estimated_seconds_per_unit: float
    inventory_path: Path
    eligible_states: tuple[str, ...]
    value_store_format: ValueStoreFormat
    value_namespace: str
    checkpoint_root: Path
    completed_manifest: Path
    completion_marker_template: str
    partition_template: str
    bounded_year: int = DEFAULT_BOUNDED_YEAR
    alpha_spec_id: str = DEFAULT_ALPHA_SPEC_ID
    policy_path: Path = Path(DEFAULT_POLICY_CONFIG)


@dataclass(frozen=True, slots=True)
class ScaleoutInputDataset:
    """One accepted input DatasetVersion required by a scaleout unit."""

    schema_id: str
    dataset_version_id: str
    acceptance_state: str
    acceptance_state_source: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible input DatasetVersion summary."""

        return {
            "schema": self.schema_id,
            "dataset_version_id": self.dataset_version_id,
            "acceptance_state": self.acceptance_state,
            "acceptance_state_source": self.acceptance_state_source,
        }


@dataclass(frozen=True, slots=True)
class ScaleoutUnit:
    """One family x schema x symbol x accepted-year materialization unit."""

    unit_id: str
    family: str
    schema_id: str
    symbol: str
    year: int
    dataset_version_id: str
    acceptance_state: str
    acceptance_state_source: str
    partition_id: str
    window_start_ts: str
    window_end_ts: str
    feature_set_id: str
    feature_set_version: str
    feature_names: tuple[str, ...]
    horizon: str = ""
    input_datasets: tuple[ScaleoutInputDataset, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible unit summary."""

        payload: dict[str, object] = {
            "unit_id": self.unit_id,
            "family": self.family,
            "schema": self.schema_id,
            "symbol": self.symbol,
            "year": self.year,
            "dataset_version_id": self.dataset_version_id,
            "acceptance_state": self.acceptance_state,
            "acceptance_state_source": self.acceptance_state_source,
            "partition_id": self.partition_id,
            "window_start_ts": self.window_start_ts,
            "window_end_ts": self.window_end_ts,
            "input_datasets": [dataset.to_dict() for dataset in self.input_datasets],
            "feature_set": {
                "feature_set_id": self.feature_set_id,
                "feature_set_version": self.feature_set_version,
                "features": list(self.feature_names),
            },
        }
        if self.horizon:
            payload["horizon"] = self.horizon
        return payload


@dataclass(frozen=True, slots=True)
class MaterializedUnitEvidence:
    """Value-free evidence returned by one completed unit materialization."""

    parquet_path: str
    content_hash: str
    row_count: int
    feature_version_ids: tuple[str, ...] = ()
    label_version_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScaleoutUnitRecord:
    """Ledger/result record for one scaleout unit."""

    unit: ScaleoutUnit
    status: str
    stage: str
    parquet_path: str | None = None
    content_hash: str | None = None
    row_count: int = 0
    feature_version_ids: tuple[str, ...] = ()
    label_version_ids: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible result record."""

        return {
            **self.unit.to_dict(),
            "status": self.status,
            "stage": self.stage,
            "parquet_path": self.parquet_path,
            "content_hash": self.content_hash,
            "row_count": self.row_count,
            "feature_version_ids": list(self.feature_version_ids),
            "label_version_ids": list(self.label_version_ids),
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class _VWAPSessionAuctionBinding:
    """One config-facing P08 feature label bound to an approved OHLCV feature."""

    config_name: str
    ohlcv_name: str
    exposure_name: str
    anchor_session_label: str | None = None
    opening_range_minutes: int = 30


@dataclass(frozen=True, slots=True)
class _RegimeVolatilityCompressionBinding:
    """One config-facing P09 label bound to an approved governed primitive."""

    config_name: str
    primitive_family: str
    primitive_name: str
    exposure_name: str
    window_length: int = 20
    horizon: int = 1


@dataclass(frozen=True, slots=True)
class _LiquidityPAStructureBinding:
    """One approved structure primitive bound to one or more P10 config labels."""

    config_names: tuple[str, ...]
    primitive_name: str
    exposure_name: str
    window_length: int = 3


@dataclass(frozen=True, slots=True)
class _VolumeActivityBinding:
    """One governed primitive bound to one or more P11 config labels."""

    config_names: tuple[str, ...]
    primitive_family: str
    primitive_name: str
    exposure_name: str
    window_length: int = 20
    horizon: int = 1


@dataclass(frozen=True, slots=True)
class _BBOTradabilityTopBookBinding:
    """One existing BBO primitive bound to one P12 config label."""

    config_name: str
    bbo_name: str
    exposure_name: str
    window_length: int = 3


@dataclass(frozen=True, slots=True)
class _CrossMarketAlignmentBinding:
    """One existing Cross-Market primitive bound to one P13 config label."""

    config_name: str
    cross_market_name: str
    exposure_name: str
    window_length: int = 3


@dataclass(frozen=True, slots=True)
class _BBOAcceptedContext:
    """BBO-specific accepted context for one scaleout unit."""

    accepted: Any
    bbo_rows: tuple[Mapping[str, Any], ...]
    quality_status: str
    coverage_status: str


@dataclass(frozen=True, slots=True)
class _BBOPrimaryLabelAcceptedContext:
    """Label accepted-context adapter for a BBO-primary scaleout unit.

    The generic reference-label preflight (``_label_accepted_context``) returns
    an object exposing ``.accepted`` (an AcceptedDatasetVersion used to build the
    materialization plan) and ``.bar_rows`` (canonical OHLCV rows used to build
    the OHLCV trade-row view). A BBO-primary unit has NO OHLCV canonical surface
    on its DatasetVersion, so the BBO-aware preflight
    (``_build_bbo_accepted_context``) supplies the accepted version plus
    BBO-specific quality/coverage reports, and ``bar_rows`` is empty: the
    reference cost_adjusted value math is BBO-resident and consumes the BBO
    view, using OHLCV trade rows only as an optional synthetic-no-trade overlay
    that is absent (and must remain absent) when no OHLCV input dataset is wired.
    """

    accepted: Any
    bar_rows: tuple[Mapping[str, Any], ...]
    quality_status: str
    coverage_status: str


@dataclass(frozen=True, slots=True)
class _CrossMarketAcceptedContext:
    """Cross-market accepted context for one multi-instrument scaleout unit."""

    accepted: Any
    bar_rows: tuple[Mapping[str, Any], ...]
    row_counts_by_symbol: Mapping[str, int]
    quality_status: str
    coverage_status: str


@dataclass(frozen=True, slots=True)
class _V1PreparedWorkerJob:
    unit: ScaleoutUnit
    feature_set: Any
    feature_request_payloads: Mapping[str, Mapping[str, Any]]
    registry_metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class _ReferenceLabelWorkerManifest:
    """Deterministic, value-free manifest for one reference-label worker unit."""

    unit_key: Mapping[str, Any]
    parquet_path: str
    content_hash: str
    row_count: int
    label_version_ids: tuple[str, ...]
    producer_engine_id: str
    value_schema_version: str
    manifest_path: str

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": REFERENCE_LABEL_WORKER_MANIFEST_SCHEMA,
            "unit_key": dict(self.unit_key),
            "parquet_path": self.parquet_path,
            "content_hash": self.content_hash,
            "row_count": self.row_count,
            "label_version_ids": list(self.label_version_ids),
            "producer_engine_id": self.producer_engine_id,
            "value_schema_version": self.value_schema_version,
            "manifest_path": self.manifest_path,
        }
        payload["manifest_hash"] = "sha256:" + hash_config(payload)
        return payload


@dataclass(frozen=True, slots=True)
class _ReferenceLabelWorkerUnitOutput:
    """Reference-label worker output queued for the single serial registry writer."""

    materialization_result: Any
    label_definitions: tuple[Any, ...]
    registry_metadata: Mapping[str, Any]
    manifest: _ReferenceLabelWorkerManifest | None = None


@dataclass(frozen=True, slots=True)
class ScaleoutRunSummary:
    """Summary for a scaleout plan or execution run."""

    campaign_id: str
    phase_id: str
    family: str
    engine: str
    target: ScaleoutTarget
    rollout: str
    dry_run: bool
    bounded_year: int
    accepted_unit_count: int
    bounded_unit_count: int
    worker_plan: ScaleoutWorkerPlan
    force_recompute: bool = False
    dry_run_estimate: ScaleoutDryRunEstimate | None = None
    records: tuple[ScaleoutUnitRecord, ...] = field(default_factory=tuple)

    @property
    def completed_count(self) -> int:
        return sum(1 for record in self.records if record.status == "completed")

    @property
    def skipped_count(self) -> int:
        return sum(1 for record in self.records if record.status == "skipped")

    @property
    def planned_count(self) -> int:
        return sum(1 for record in self.records if record.status == "planned")

    @property
    def failed_count(self) -> int:
        return sum(1 for record in self.records if record.status == "failed")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible run summary."""

        return {
            "campaign_id": self.campaign_id,
            "phase_id": self.phase_id,
            "family": self.family,
            "engine": self.engine,
            "target": self.target.to_dict(),
            "rollout": self.rollout,
            "dry_run": self.dry_run,
            "bounded_year": self.bounded_year,
            "accepted_unit_count": self.accepted_unit_count,
            "bounded_unit_count": self.bounded_unit_count,
            "worker_plan": self.worker_plan.to_dict(),
            "force_recompute": self.force_recompute,
            "dry_run_estimate": (
                self.dry_run_estimate.to_dict() if self.dry_run_estimate is not None else None
            ),
            "planned_count": self.planned_count,
            "completed_count": self.completed_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "records": [record.to_dict() for record in self.records],
        }


UnitExecutor = Callable[
    [ScaleoutConfig, ScaleoutUnit, Path, Path, Path],
    MaterializedUnitEvidence,
]


def load_scaleout_config(path: str | Path = DEFAULT_SCALEOUT_CONFIG) -> ScaleoutConfig:
    """Load and validate a feature scaleout config."""

    config_path = Path(path).expanduser().resolve(strict=False)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScaleoutError(f"scaleout config could not be read: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ScaleoutError(f"scaleout config is not valid JSON: {config_path}") from exc
    if not isinstance(payload, Mapping):
        raise ScaleoutError("scaleout config root must be a mapping")
    schema = payload.get("schema")
    if schema not in {SCALEOUT_CONFIG_SCHEMA, LABEL_SCALEOUT_CONFIG_SCHEMA}:
        raise ScaleoutError(
            "scaleout config schema must be one of: "
            f"{SCALEOUT_CONFIG_SCHEMA}, {LABEL_SCALEOUT_CONFIG_SCHEMA}"
        )
    is_label_config = schema == LABEL_SCALEOUT_CONFIG_SCHEMA

    grid = _require_mapping(payload.get("batch_unit_grid"), "batch_unit_grid")
    budgets = _optional_mapping(payload.get("budgets"), "budgets")
    dataset_selection = _require_mapping(payload.get("dataset_selection"), "dataset_selection")
    targeting = _optional_mapping(payload.get("targeting"), "targeting")
    value_store = _require_mapping(payload.get("value_store"), "value_store")
    checkpoint = _require_mapping(payload.get("checkpoint"), "checkpoint")
    identity = _require_mapping(payload.get("identity"), "identity")

    repo_root = Path.cwd().resolve(strict=False)
    value_store_format = ValueStoreFormat(_require_text(value_store.get("format"), "value_store.format"))
    if value_store_format is not ValueStoreFormat.PARQUET:
        raise ScaleoutError("scaleout research-scale value_store.format must be parquet")

    checkpoint_root = Path(_require_text(checkpoint.get("checkpoint_root"), "checkpoint_root"))
    if is_label_config:
        feature_names = ()
        label_names = _scaleout_label_names(
            _require_text(payload.get("family"), "family"),
            _text_tuple(payload.get("governed_scope"), "governed_scope"),
        )
    else:
        feature_names = _text_tuple(payload.get("governed_scope"), "governed_scope")
        label_names = _optional_text_tuple(
            payload.get("governed_label_scope"),
            "governed_label_scope",
        )
    row_budget_per_unit = _optional_positive_int(
        budgets.get("row_budget_per_unit"),
        "budgets.row_budget_per_unit",
        default=0,
    )
    return ScaleoutConfig(
        config_path=config_path,
        campaign_id=_require_text(payload.get("campaign_id"), "campaign_id"),
        phase_id=_require_text(payload.get("phase_id"), "phase_id"),
        family=_require_text(payload.get("family"), "family"),
        feature_names=feature_names,
        feature_groups=_group_mapping(
            targeting.get("feature_groups"),
            "targeting.feature_groups",
            allowed_names=feature_names,
        ),
        label_names=label_names,
        label_groups=_group_mapping(
            targeting.get("label_groups"),
            "targeting.label_groups",
            allowed_names=label_names,
        ),
        horizon_groups=_label_horizon_groups(
            label_names,
            targeting.get("horizon_groups"),
        )
        if is_label_config
        else {},
        symbols=_text_tuple(grid.get("symbols"), "batch_unit_grid.symbols"),
        years=_int_tuple(grid.get("years"), "batch_unit_grid.years"),
        input_schemas=_text_tuple(grid.get("input_schemas"), "batch_unit_grid.input_schemas"),
        horizons=_optional_text_tuple(grid.get("horizons"), "batch_unit_grid.horizons"),
        dense_grid_required=_optional_bool(
            grid.get("dense_grid_required"),
            "batch_unit_grid.dense_grid_required",
            default=False,
        ),
        row_budget_per_unit=row_budget_per_unit,
        estimated_seconds_per_unit=_optional_float(
            targeting.get("estimated_seconds_per_unit"),
            "targeting.estimated_seconds_per_unit",
            default=_default_seconds_per_unit(row_budget_per_unit),
        ),
        inventory_path=_repo_path(
            dataset_selection.get("inventory_ref"),
            "dataset_selection.inventory_ref",
            repo_root=repo_root,
        ),
        eligible_states=_text_tuple(
            dataset_selection.get("eligible_states"),
            "dataset_selection.eligible_states",
        ),
        value_store_format=value_store_format,
        value_namespace=_require_text(value_store.get("value_namespace"), "value_namespace"),
        checkpoint_root=checkpoint_root,
        completed_manifest=Path(
            _require_text(checkpoint.get("completed_manifest"), "completed_manifest")
        ),
        completion_marker_template=_require_text(
            checkpoint.get("completion_marker_template"),
            "completion_marker_template",
        ),
        partition_template=_require_text(
            identity.get("partition_template"),
            "identity.partition_template",
        ),
        policy_path=Path(DEFAULT_POLICY_CONFIG),
    )


def build_scaleout_units(
    config: ScaleoutConfig,
    *,
    target: ScaleoutTarget | None = None,
) -> tuple[ScaleoutUnit, ...]:
    """Build the selected family/name x symbol x year grid from value-free locks."""

    target = target or ScaleoutTarget()
    if target.family is not None and target.family != config.family:
        return ()
    if target.label_targeted and not config.label_names:
        return ()
    selected_names = _selected_names_for_config(config, target)
    if not selected_names:
        return ()
    selected_symbols = _unit_symbols_for_config(config, target)
    selected_years = _selected_years(config, target)
    selected_dataset_version_ids = set(target.dataset_version_ids)
    inventory = _load_json_mapping(config.inventory_path, "dataset inventory")
    schemas = _require_mapping(inventory.get("schemas"), "dataset inventory schemas")
    summary_path = _optional_repo_path(inventory.get("source_summary"))
    summary_states = (
        _acceptance_states_from_summary(summary_path)
        if summary_path is not None and summary_path.exists()
        else {}
    )
    partial_year_end_ts = _partial_year_end_ts(config.policy_path)
    units: list[ScaleoutUnit] = []
    for year in selected_years:
        input_datasets: list[ScaleoutInputDataset] = []
        for schema_id in config.input_schemas:
            schema_inventory = _require_mapping(schemas.get(schema_id), f"schemas.{schema_id}")
            year_inventory = _require_mapping(
                schema_inventory.get(str(year)),
                f"schemas.{schema_id}.{year}",
            )
            dataset_version_id = _require_text(
                year_inventory.get("dataset_version_id"),
                f"schemas.{schema_id}.{year}.dataset_version_id",
            )
            state, state_source = _state_for_unit(
                schema_id,
                year,
                dataset_version_id,
                summary_states=summary_states,
                inventory_state=year_inventory.get("committed_summary_state"),
            )
            if state not in config.eligible_states:
                input_datasets = []
                break
            input_datasets.append(
                ScaleoutInputDataset(
                    schema_id=schema_id,
                    dataset_version_id=dataset_version_id,
                    acceptance_state=state,
                    acceptance_state_source=state_source,
                )
            )
        if not input_datasets:
            continue
        if selected_dataset_version_ids and selected_dataset_version_ids.isdisjoint(
            dataset.dataset_version_id for dataset in input_datasets
        ):
            continue
        primary = _primary_input_dataset(config, tuple(input_datasets))
        for symbol in selected_symbols:
            if _is_label_scaleout_config(config):
                if _label_config_needs_horizon_grid(config):
                    # The configured horizon grid is orthogonal to the label
                    # names (cost_adjusted, path): one unit per horizon carries
                    # every governed label name so the full name x horizon
                    # surface is wired (LCFP-P08 coverage repair).
                    unit_axes = tuple(
                        (selected_names, horizon, horizon) for horizon in config.horizons
                    )
                else:
                    # Label names embed their horizon (fixed/extended/close-out):
                    # keep the established one-name-per-unit grain and identity.
                    unit_axes = tuple(((name,), name, "") for name in selected_names)
            else:
                unit_axes = ((selected_names, "", ""),)
            for names, horizon_token, grid_horizon in unit_axes:
                partition_id = _render_partition(
                    config.partition_template,
                    symbol=symbol,
                    year=year,
                    horizon=horizon_token,
                )
                set_kind = "label_set" if _is_label_scaleout_config(config) else "feature_set"
                set_id = f"{set_kind}_futures_scaleout_{config.family}"
                if _is_label_scaleout_config(config):
                    set_id = f"{set_id}_{horizon_token}"
                set_version = f"v1_{symbol.lower()}_{year}"
                if _is_label_scaleout_config(config):
                    set_version = f"{set_version}_{horizon_token}"
                unit_payload = _unit_identity_payload(
                    config,
                    symbol=symbol,
                    year=year,
                    primary=primary,
                    input_datasets=tuple(input_datasets),
                    feature_set_id=set_id,
                    feature_set_version=set_version,
                    feature_names=names,
                    horizon=grid_horizon,
                )
                units.append(
                    ScaleoutUnit(
                        unit_id=f"mbu_{hash_config(unit_payload)[:24]}",
                        family=config.family,
                        schema_id=primary.schema_id,
                        symbol=symbol,
                        year=year,
                        dataset_version_id=primary.dataset_version_id,
                        acceptance_state=primary.acceptance_state,
                        acceptance_state_source=primary.acceptance_state_source,
                        partition_id=partition_id,
                        window_start_ts=f"{year:04d}-01-01T00:00:00+00:00",
                        window_end_ts=partial_year_end_ts.get(
                            year,
                            f"{year + 1:04d}-01-01T00:00:00+00:00",
                        ),
                        feature_set_id=set_id,
                        feature_set_version=set_version,
                        feature_names=names,
                        horizon=grid_horizon,
                        input_datasets=tuple(input_datasets),
                    )
                )
    return tuple(sorted(units, key=lambda item: (item.year, item.symbol, item.schema_id)))


def _label_config_needs_horizon_grid(config: ScaleoutConfig) -> bool:
    """True when the configured horizon grid is orthogonal to the label names."""

    if not config.horizons:
        return False
    return all(
        _label_horizon_token(name) not in config.horizons for name in config.label_names
    )


def _primary_input_dataset(
    config: ScaleoutConfig,
    input_datasets: tuple[ScaleoutInputDataset, ...],
) -> ScaleoutInputDataset:
    if config.dense_grid_required:
        for dataset in input_datasets:
            if dataset.schema_id == "ohlcv_dense_research_grid":
                return dataset
    return input_datasets[0]


def _unit_identity_payload(
    config: ScaleoutConfig,
    *,
    symbol: str,
    year: int,
    primary: ScaleoutInputDataset,
    input_datasets: tuple[ScaleoutInputDataset, ...],
    feature_set_id: str,
    feature_set_version: str,
    feature_names: tuple[str, ...],
    horizon: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": SCALEOUT_CONFIG_SCHEMA,
        "campaign_id": config.campaign_id,
        "family": config.family,
        "schema_id": primary.schema_id,
        "symbol": symbol,
        "year": year,
        "dataset_version_id": primary.dataset_version_id,
        "value_store_format": config.value_store_format.value,
        "feature_set_id": feature_set_id,
        "feature_set_version": feature_set_version,
    }
    if horizon:
        # Horizon-grid label units (cost_adjusted, path) key identity on the
        # grid horizon per the config unit_id_formula. Name-grain units keep
        # the established payload so previously materialized unit ids hold.
        payload["horizon"] = horizon
    configured_names = config.label_names if _is_label_scaleout_config(config) else config.feature_names
    if feature_names != configured_names:
        key = "selected_label_names" if _is_label_scaleout_config(config) else "selected_feature_names"
        payload[key] = list(feature_names)
    if len(input_datasets) > 1:
        payload["input_dataset_versions"] = [dataset.to_dict() for dataset in input_datasets]
    return payload


def _resolve_engine_token(engine: str | None, config: ScaleoutConfig) -> str:
    """Resolve the effective engine for one scaleout run.

    An explicit ``engine`` request is honored for every config type. When the
    caller does not request an engine, label scaleout configs default to the
    reference engine — the only production label path until the LCFP-P07 parity
    and LCFP-P08 benchmark gates accept the fast label path — while feature
    configs keep the V1 default.
    """

    if engine is None:
        if _is_label_scaleout_config(config):
            return SCALEOUT_ENGINE_REFERENCE
        return DEFAULT_SCALEOUT_ENGINE
    return _normalize_engine(engine)


def _parallel_worker_compute_allowed(
    config: ScaleoutConfig,
    engine: str,
    *,
    use_default_executor: bool,
) -> bool:
    if not use_default_executor:
        return False
    engine_token = _normalize_engine(engine)
    if engine_token == SCALEOUT_ENGINE_V1:
        return True
    return engine_token == SCALEOUT_ENGINE_REFERENCE and _is_label_scaleout_config(config)


def run_scaleout(
    config: ScaleoutConfig,
    *,
    alpha_data_root: str | Path | None = None,
    dataset_registry_path: str | Path | None = None,
    canonical_root: str | Path | None = None,
    rollout: str = "bounded-then-full",
    execute: bool = False,
    bounded_year: int | None = None,
    engine: str | None = None,
    unit_executor: UnitExecutor | None = None,
    target: ScaleoutTarget | None = None,
    workers: int | None = DEFAULT_CPU_WORKERS,
    force_recompute: bool | str | None = None,
    log: Callable[[str], None] | None = None,
) -> ScaleoutRunSummary:
    """Plan or execute scaleout units.

    ``workers=1`` preserves the serial path. For V1 execute-mode runs with more
    than one effective worker, canonical loading and value computation happen in
    worker processes and registry registration is replayed by this process in
    deterministic unit order.

    ``engine=None`` means "default per config type": label scaleout configs
    default to the reference engine until LCFP acceptance, feature configs
    default to V1. An explicit ``engine="v1"`` opt-in on a label config is
    honored.
    """

    rollout_token = _normalize_rollout(rollout)
    engine_token = _resolve_engine_token(engine, config)
    requested_workers = _normalize_workers(workers)
    force_recompute_token = _normalize_force_recompute(force_recompute)
    target = target or ScaleoutTarget()
    units = build_scaleout_units(config, target=target)
    bounded = _bounded_units(units, bounded_year or config.bounded_year)
    records: list[ScaleoutUnitRecord] = []

    if not execute:
        planned = _planned_units_for_rollout(units, bounded, rollout_token)
        worker_plan = _resolve_worker_plan(
            requested_workers,
            unit_count=len(planned),
            parallel_allowed=False,
        )
        records.extend(
            _preview_record(config, unit, stage=stage)
            for stage, unit in planned
        )
        return ScaleoutRunSummary(
            campaign_id=config.campaign_id,
            phase_id=config.phase_id,
            family=config.family,
            engine=engine_token,
            target=target,
            rollout=rollout_token,
            dry_run=True,
            bounded_year=bounded_year or config.bounded_year,
            accepted_unit_count=len(units),
            bounded_unit_count=len(bounded),
            worker_plan=worker_plan,
            force_recompute=force_recompute_token,
            dry_run_estimate=_dry_run_estimate(
                config,
                units=units,
                planned_step_count=len(planned),
            ),
            records=tuple(records),
        )

    alpha_root = _alpha_data_root(alpha_data_root)
    dataset_registry = _required_path(dataset_registry_path, "dataset_registry_path")
    canonical = _canonical_root(canonical_root)
    ledger = _ScaleoutLedger(alpha_root, config)
    use_default_executor = unit_executor is None
    executor = unit_executor or _unit_executor_for_family(config.family, engine=engine_token)
    planned = _planned_units_for_rollout(units, bounded, rollout_token)
    worker_plan = _resolve_worker_plan(
        requested_workers,
        unit_count=len(planned),
        parallel_allowed=_parallel_worker_compute_allowed(
            config,
            engine_token,
            use_default_executor=use_default_executor,
        ),
    )

    for stage, stage_units in _execution_stages(units, bounded, rollout_token):
        stage_records = _execute_stage(
            config,
            stage_units,
            stage=stage,
            alpha_data_root=alpha_root,
            dataset_registry_path=dataset_registry,
            canonical_root=canonical,
            ledger=ledger,
            executor=executor,
            engine=engine_token,
            requested_workers=requested_workers,
            parallel_worker_compute=_parallel_worker_compute_allowed(
                config,
                engine_token,
                use_default_executor=use_default_executor,
            ),
            force_recompute=force_recompute_token,
            log=log,
        )
        records.extend(stage_records)
        if stage == "bounded_real" and any(record.status == "failed" for record in stage_records):
            break

    return ScaleoutRunSummary(
        campaign_id=config.campaign_id,
        phase_id=config.phase_id,
        family=config.family,
        engine=engine_token,
        target=target,
        rollout=rollout_token,
        dry_run=False,
        bounded_year=bounded_year or config.bounded_year,
        accepted_unit_count=len(units),
        bounded_unit_count=len(bounded),
        worker_plan=worker_plan,
        force_recompute=force_recompute_token,
        records=tuple(records),
    )


def _materialize_unit_per_feature(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    accepted: Any,
    feature_definition_builders: Sequence[Callable[[object], Any]],
    inputs_factory: Callable[[Mapping[str, Any]], Any],
    feature_set_metadata: Mapping[str, Any],
    governance_metadata: Mapping[str, Any],
    description: str,
    feature_set_version_suffix: Callable[[Any], str],
    empty_values_message: str,
) -> MaterializedUnitEvidence:
    """Materialize and register every governed feature of one unit, per feature.

    The FLF-P05 duplicate-exposure request gate is re-evaluated against the live
    feature registry at registration time, and the request id is a function of the
    registry state observed when the request is checked. A single combined
    ``materialize_features`` call would freeze every FeatureSpec (and its request id)
    against one registry snapshot, but each registration mutates the registry, so the
    later siblings' frozen request ids no longer match the registration-time gate
    (``checked FeatureRequest id must match FeatureSpec.feature_request_id``).

    Mirroring the sanctioned ``run_seed_feature_pack`` seam, each feature is therefore
    built against the current live registry and materialized + registered on its own
    (one Parquet path per feature) so build-time and registration-time gate state
    agree. Feature identity (``feature_version_id``) is content-addressed and
    registry-state-independent, so the registered ids still equal the write-free
    dry-run preview and keystone identity is preserved. The per-feature Parquet path
    and content hash are verified through ``register_materialized_feature`` for each
    registered FeatureVersion.
    """

    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.contracts import FeatureSetSpec
    from alpha_system.features.engine.materialization import (
        build_feature_materialization_plan,
        materialize_features,
    )
    from alpha_system.features.store import FeatureStore

    if not feature_definition_builders:
        raise ScaleoutError(f"unit {unit.unit_id} did not select any governed features")

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    feature_version_ids: list[str] = []
    parquet_paths: list[str] = []
    content_hashes: list[str] = []
    schema_versions: list[str | None] = []
    total_rows = 0
    for builder in feature_definition_builders:
        # Build this one feature against the LIVE registry so its request gate
        # decision (and request id) matches what register_materialized_feature
        # re-checks immediately afterward.
        definition = builder(store.registry)
        feature_spec = _definition_feature_spec(definition)
        checked_request = definition.request_gate_decision.checked_feature_request
        if checked_request is None:
            raise ScaleoutError("FeatureRequest gate did not return a checked request")
        # Feature-level idempotency. ``feature_version_id`` is content-addressed over
        # the computational contract (FeatureSpec.to_identity_dict), so an already
        # registered fver whose Parquet file still exists is the byte-identical
        # feature this unit would otherwise recompute. Reuse it and skip
        # re-materialization. This makes the driver restart-safe at feature
        # granularity: a unit that was only partially registered by an earlier run
        # (or that shares an already-registered feature) completes without
        # recomputing finished features or tripping the FeatureStore identity guard
        # on records that legitimately predate this run.
        existing_fvid = definition.feature_version_id
        existing_record = store.resolve_feature(existing_fvid)
        existing_parquet = getattr(existing_record, "parquet_path", None)
        if (
            existing_record is not None
            and existing_parquet
            and Path(existing_parquet).exists()
            and not _normalize_force_recompute(None)
        ):
            feature_version_ids.append(existing_fvid)
            parquet_paths.append(str(existing_parquet))
            content_hashes.append(str(getattr(existing_record, "value_content_hash", "") or ""))
            schema_versions.append(getattr(existing_record, "value_schema_version", None))
            total_rows += int(getattr(existing_record, "value_record_count", 0) or 0)
            continue
        feature_set = FeatureSetSpec(
            feature_set_id=unit.feature_set_id,
            feature_set_version=f"{unit.feature_set_version}_{feature_set_version_suffix(definition)}",
            features=(feature_spec,),
            description=description,
            metadata=dict(feature_set_metadata),
        )
        plan = build_feature_materialization_plan(
            feature_set,
            accepted,
            partition_id=unit.partition_id,
            alpha_data_root=alpha_data_root,
            governance_metadata=governance_metadata,
            output_namespace=config.value_namespace,
        )
        result = materialize_features(
            plan,
            inputs_factory(governance_metadata),
            (definition,),
            value_store_format=ValueStoreFormat.PARQUET,
        )
        if result.record_count == 0:
            raise ScaleoutError(empty_values_message.format(unit_id=unit.unit_id))
        handle = result.value_store_handle
        if not isinstance(handle, ValueStoreHandle):
            raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
        parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
        content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
        record = store.register_materialized_feature(
            result,
            feature_spec=feature_spec,
            feature_version=definition.version,
            feature_request=checked_request,
            registry_metadata=governance_metadata,
        )
        _verify_feature_registry_roundtrip(
            unit,
            alpha_data_root=alpha_data_root,
            feature_version_ids=(record.feature_version_id,),
            parquet_path=parquet_path,
            content_hash=content_hash,
            value_schema_version=handle.schema_version,
        )
        reconcile_registered_feature_pack_path(
            alpha_data_root=alpha_data_root,
            parquet_path=parquet_path,
        )
        feature_version_ids.append(record.feature_version_id)
        parquet_paths.append(parquet_path)
        content_hashes.append(content_hash)
        schema_versions.append(handle.schema_version)
        total_rows += handle.value_count
    return MaterializedUnitEvidence(
        parquet_path=parquet_paths[0],
        content_hash=content_hashes[0],
        row_count=total_rows,
        feature_version_ids=tuple(feature_version_ids),
    )


def materialize_base_ohlcv_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one Base OHLCV unit through the sanctioned seam.

    Each governed Base OHLCV FeatureSpec is built through the SAME path as
    ``run_seed_feature_pack`` (``_build_feature_request`` + ``_feature_input_scope`` +
    ``build_ohlcv_feature_definition``) and materialized + registered per feature via
    ``_materialize_unit_per_feature``, so the registered ``feature_version_id``s are
    identical to the write-free dry-run preview and keystone identity is preserved.
    """

    from alpha_system.cli.seed_pack import (
        _build_accepted_context,
        _build_feature_request,
        _coerce_feature_name,
        _feature_input_scope,
    )
    from alpha_system.features.families.ohlcv import build_ohlcv_feature_definition

    if config.family != "base_ohlcv" or unit.family != "base_ohlcv":
        raise ScaleoutError("FUTSUB-P06 executor supports only the base_ohlcv family")

    seed_config = _seed_config(config, unit)
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    def _make_builder(entry: Any) -> Callable[[object], Any]:
        def _build(registry_reader: object) -> Any:
            request = _build_feature_request(
                seed_config.feature_set, entry.name, exposure_scope=unit.partition_id
            )
            return build_ohlcv_feature_definition(
                _coerce_feature_name(entry.name),
                request,
                registry_reader,
                dataset_version_ids=(unit.dataset_version_id,),
                window_length=entry.window_length,
                horizon=entry.horizon,
                reset_on_session=False,
                input_scope=_feature_input_scope(seed_config),
            )

        return _build

    governance_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    feature_set_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=[
            _make_builder(entry) for entry in seed_config.feature_set.features
        ],
        inputs_factory=lambda gm: _ohlcv_inputs(context, gm),
        feature_set_metadata=feature_set_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P06 Base OHLCV FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no base OHLCV feature values",
    )


def _ohlcv_inputs(context: Any, governance_metadata: Mapping[str, Any]) -> Any:
    from alpha_system.features.engine.materialization import FeatureMaterializationInputs

    return FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
        governance_metadata=governance_metadata,
    )


def materialize_fixed_horizon_label_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one fixed-horizon LabelPack unit through ``run_seed_label_pack``."""

    from alpha_system.cli.seed_pack import run_seed_label_pack

    if config.family not in {"fixed_horizon", "session_close_maintenance_flat"} or unit.family != config.family:
        raise ScaleoutError(
            "label executor supports only fixed_horizon and "
            "session_close_maintenance_flat label families"
        )

    metadata = _label_scaleout_metadata(config, unit)
    summary = run_seed_label_pack(
        _label_seed_config(config, unit),
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
        value_store_format=ValueStoreFormat.PARQUET,
        output_namespace=config.value_namespace,
        governance_metadata=metadata,
        registry_metadata=metadata,
    )
    handle = _require_mapping(summary.get("value_store_handle"), "value_store_handle")
    parquet_path = _require_text(handle.get("parquet_path"), "value_store_handle.parquet_path")
    content_hash = _require_text(handle.get("content_hash"), "value_store_handle.content_hash")
    label_version_ids = tuple(
        _require_text(value, "label_version_id")
        for value in _sequence(summary.get("label_version_ids"), "label_version_ids")
    )
    row_count = int(summary.get("value_record_count") or handle.get("value_count") or 0)
    if row_count <= 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no fixed-horizon label values")
    _verify_label_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        label_version_ids=label_version_ids,
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=str(handle.get("schema_version") or ""),
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=row_count,
        label_version_ids=label_version_ids,
    )


def materialize_fast_label_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one label unit through the V1 fast label producer path."""

    output = _compute_fast_label_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=False,
        include_records=True,
    )
    return _register_fast_label_worker_output(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        output=output,
    )


def materialize_reference_label_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one label unit through the reference engine, then register serially."""

    output = _compute_reference_label_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=False,
        include_records=True,
    )
    return _register_reference_label_worker_output(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        output=output,
    )


def _compute_reference_label_unit_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    *,
    write_manifest: bool,
    include_records: bool,
) -> _ReferenceLabelWorkerUnitOutput:
    """Compute and persist one reference-label unit without mutating the registry."""

    from alpha_system.features.input_views import build_ohlcv_input_view
    from alpha_system.labels.engine import (
        LABEL_MATERIALIZATION_PURPOSE,
        LABEL_MATERIALIZATION_SCHEMA,
        LabelMaterializationResult,
        _LabelInputViews,
        _compute_records,
        _definitions_by_version_id,
        _materialization_output_path_for_format,
        _validate_materialized_records,
        _write_records_idempotently,
        build_label_materialization_plan,
    )

    if not _is_label_scaleout_config(config) or unit.family != config.family:
        raise ScaleoutError("reference label executor requires a label scaleout unit")
    definitions = _reference_label_definitions_for_unit(config, unit)
    registry_metadata = _label_scaleout_metadata(config, unit)
    context = _label_accepted_context(
        config,
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    plan = build_label_materialization_plan(
        definitions,
        context.accepted,
        partition_id=unit.partition_id,
        instrument_ids=(),
        alpha_data_root=alpha_data_root,
        governance_metadata=registry_metadata,
        output_namespace=config.value_namespace,
    )
    ohlcv_view = build_ohlcv_input_view(
        context.accepted,
        context.bar_rows,
        partition_id=unit.partition_id,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=registry_metadata,
    )
    bbo_view = _reference_label_bbo_view(
        definitions,
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
        partition_id=unit.partition_id,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=registry_metadata,
    )
    started = perf_counter()
    records = _compute_records(
        plan,
        _definitions_by_version_id(definitions, plan),
        _LabelInputViews(ohlcv=ohlcv_view, bbo=bbo_view),
    )
    _validate_materialized_records(plan, records)
    write_result = _write_records_idempotently(
        plan,
        records,
        value_store_format=config.value_store_format,
    )
    result = LabelMaterializationResult(
        plan=plan,
        records=records,
        dry_run=False,
        wrote_output=write_result.wrote_output,
        output_path=_materialization_output_path_for_format(plan, config.value_store_format),
        value_store_handle=write_result.handle,
        planned_input_rows=len(context.bar_rows) + len(getattr(bbo_view, "rows", ())),
        planned_label_count=len(definitions),
        runtime_seconds=perf_counter() - started,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no reference label values")
    manifest = _reference_label_worker_manifest_from_result(
        alpha_data_root=alpha_data_root,
        config=config,
        unit=unit,
        result=result,
        label_version_ids=_reference_label_version_ids(definitions),
        value_schema_version=LABEL_MATERIALIZATION_SCHEMA,
    )
    if write_manifest:
        _write_reference_label_worker_manifest(manifest)
    if not include_records:
        result = LabelMaterializationResult(
            plan=result.plan,
            records=(),
            dry_run=result.dry_run,
            wrote_output=result.wrote_output,
            output_path=result.output_path,
            value_store_handle=result.value_store_handle,
            planned_input_rows=result.planned_input_rows,
            planned_label_count=result.planned_label_count,
            runtime_seconds=result.runtime_seconds,
        )
    return _ReferenceLabelWorkerUnitOutput(
        materialization_result=result,
        label_definitions=definitions,
        registry_metadata=registry_metadata,
        manifest=manifest,
    )


def _register_reference_label_worker_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    output: Any,
) -> MaterializedUnitEvidence:
    """Serially register one worker-computed reference-label unit."""

    from alpha_system.labels.engine import (
        LABEL_MATERIALIZATION_SCHEMA,
        _definition_contract,
        _definition_version,
    )
    from alpha_system.labels.registry import LabelRegistry

    result = _reference_label_result_with_records(output.materialization_result)
    handle = result.value_store_handle
    if handle is None:
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    records = []
    registry_metadata = dict(output.registry_metadata)
    if output.manifest is not None:
        registry_metadata["worker_manifest_path"] = output.manifest.manifest_path
    for definition in output.label_definitions:
        records.append(
            registry.register_materialized_label(
                result,
                label_contract=_definition_contract(definition),
                label_version=_definition_version(definition),
                registry_metadata=registry_metadata,
            )
        )
    label_version_ids = tuple(record.label_version_id for record in records)
    expected_label_version_ids = _reference_label_version_ids(output.label_definitions)
    if label_version_ids != expected_label_version_ids:
        raise ScaleoutError("registered reference label_version_id order changed")
    _verify_label_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        label_version_ids=label_version_ids,
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=LABEL_MATERIALIZATION_SCHEMA,
    )
    for label_version_id in label_version_ids:
        record = registry.resolve_label(label_version_id)
        if record is None or record.producer_engine_id != REFERENCE_LABEL_PRODUCER_ENGINE_ID:
            raise ScaleoutError("registered label is missing reference producer provenance")
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        label_version_ids=label_version_ids,
    )


def _reference_label_bbo_view(
    definitions: tuple[Any, ...],
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
    partition_id: str,
    purpose: str,
    governance_metadata: Mapping[str, Any],
) -> Any:
    from alpha_system.features.input_views import BBOInputView, build_bbo_input_view

    if not _reference_label_definitions_require_bbo(definitions):
        return BBOInputView(())
    bbo_dataset = _label_bbo_input_dataset(unit)
    if bbo_dataset is None:
        raise ScaleoutError(
            f"unit {unit.unit_id} requires a BBO input DatasetVersion but none "
            "is wired in unit.input_datasets"
        )
    bbo_unit = replace(
        unit,
        schema_id=bbo_dataset.schema_id,
        dataset_version_id=bbo_dataset.dataset_version_id,
        acceptance_state=bbo_dataset.acceptance_state,
        acceptance_state_source=bbo_dataset.acceptance_state_source,
    )
    context = _build_bbo_accepted_context(
        bbo_unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    return build_bbo_input_view(
        context.accepted,
        context.bbo_rows,
        partition_id=partition_id,
        purpose=purpose,
        governance_metadata=governance_metadata,
    )


def _reference_label_definitions_require_bbo(definitions: tuple[Any, ...]) -> bool:
    from alpha_system.labels.families.cost_adjusted import CostAdjustedLabelDefinition
    from alpha_system.labels.families.fixed_horizon import FixedHorizonLabelDefinition

    for definition in definitions:
        if isinstance(definition, CostAdjustedLabelDefinition):
            return True
        if isinstance(definition, FixedHorizonLabelDefinition) and getattr(
            definition,
            "is_midprice",
            False,
        ):
            return True
    return False


def _reference_label_definitions_for_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Any, ...]:
    return _fast_label_definitions_for_unit(config, unit)


def _reference_label_version_ids(definitions: Sequence[Any]) -> tuple[str, ...]:
    from alpha_system.labels.engine import _definition_version

    return tuple(_definition_version(definition).label_version_id for definition in definitions)


def _reference_label_result_with_records(result: Any) -> Any:
    if not hasattr(result, "records") or getattr(result, "records", ()):
        return result
    from alpha_system.labels.engine import LabelMaterializationResult

    handle = result.value_store_handle
    if handle is None or not handle.parquet_path:
        raise ScaleoutError("reference label worker output is missing a Parquet handle")
    return LabelMaterializationResult(
        plan=result.plan,
        records=_label_value_records_from_parquet(handle.parquet_path, result.plan),
        dry_run=result.dry_run,
        wrote_output=result.wrote_output,
        output_path=result.output_path,
        value_store_handle=handle,
        planned_input_rows=result.planned_input_rows,
        planned_label_count=result.planned_label_count,
        runtime_seconds=result.runtime_seconds,
    )


def _reference_label_worker_manifest_path(
    alpha_data_root: str | Path,
    *,
    checkpoint_root: str | Path,
    unit_id: str,
) -> Path:
    return (
        Path(alpha_data_root)
        / Path(checkpoint_root)
        / "reference_worker_manifests"
        / f"{unit_id}.json"
    )


def _reference_label_worker_manifest_from_result(
    *,
    alpha_data_root: Path,
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    result: Any,
    label_version_ids: Sequence[str],
    value_schema_version: str,
) -> _ReferenceLabelWorkerManifest:
    handle = result.value_store_handle
    if handle is None or not handle.parquet_path or not handle.content_hash:
        raise ScaleoutError("reference label worker result requires a Parquet handle")
    manifest_path = _reference_label_worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    return _ReferenceLabelWorkerManifest(
        unit_key=_worker_unit_key(unit),
        parquet_path=str(handle.parquet_path),
        content_hash=str(handle.content_hash),
        row_count=int(handle.value_count),
        label_version_ids=tuple(str(value) for value in label_version_ids),
        producer_engine_id=REFERENCE_LABEL_PRODUCER_ENGINE_ID,
        value_schema_version=value_schema_version,
        manifest_path=manifest_path.as_posix(),
    )


def _write_reference_label_worker_manifest(
    manifest: _ReferenceLabelWorkerManifest,
) -> None:
    manifest_path = Path(manifest.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        canonical_serialize(manifest.to_dict()) + "\n",
        encoding="utf-8",
    )


def _compute_fast_label_unit_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    *,
    write_manifest: bool,
    include_records: bool,
) -> Any:
    """Compute and persist one fast label unit without mutating the registry."""

    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.data.foundation.canonical_loader import DEFAULT_BBO_PARTITION_SCHEMA
    from alpha_system.labels.fast import (
        FAST_LABEL_PRODUCER_ENGINE_ID,
        FAST_LABEL_VALUE_SCHEMA_VERSION,
        FastLabelWorkerUnitOutput,
        LabelPanelFrameRequest,
        label_worker_manifest_from_result,
        label_worker_manifest_path,
        write_label_worker_manifest,
    )

    pack = _fast_label_pack_for_unit(config, unit)
    registry_metadata = _fast_label_registry_metadata(config, unit)
    context = _label_accepted_context(
        config,
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    requires_bbo = _fast_label_pack_requires_bbo(pack)
    materializer = _shared_fast_label_materializer(requires_bbo=requires_bbo)
    bbo_dataset = _label_bbo_input_dataset(unit) if requires_bbo else None
    if requires_bbo and bbo_dataset is None:
        raise ScaleoutError(
            f"unit {unit.unit_id} requires a BBO input DatasetVersion but none "
            "is wired in unit.input_datasets"
        )
    request = LabelPanelFrameRequest(
        canonical_root=canonical_root,
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        year=unit.year,
        start_ts=unit.window_start_ts,
        end_ts=unit.window_end_ts,
        ohlcv_partition_schema=_on_disk_partition_schema(
            canonical_root,
            unit.dataset_version_id,
            unit.schema_id,
        ),
        bbo_partition_schema=(
            _on_disk_partition_schema(
                canonical_root,
                bbo_dataset.dataset_version_id,
                bbo_dataset.schema_id,
            )
            if bbo_dataset is not None
            else DEFAULT_BBO_PARTITION_SCHEMA
        ),
        bbo_dataset_version_id=(
            bbo_dataset.dataset_version_id if bbo_dataset is not None else None
        ),
    )
    result = materializer.materialize_pack(
        pack,
        context.accepted,
        partition_id=unit.partition_id,
        load_request=request,
        instrument_ids=(unit.symbol,),
        alpha_data_root=alpha_data_root,
        governance_metadata=registry_metadata,
        output_namespace=config.value_namespace,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no fast label values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    _require_text(handle.content_hash, "value_store_handle.content_hash")
    manifest_path = label_worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    manifest = label_worker_manifest_from_result(
        unit_key=_worker_unit_key(unit),
        result=result,
        label_version_ids=pack.label_version_ids,
        producer_engine_id=FAST_LABEL_PRODUCER_ENGINE_ID,
        value_schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
        manifest_path=manifest_path,
    )
    if write_manifest:
        write_label_worker_manifest(manifest_path, manifest)
    if not include_records:
        from alpha_system.labels.engine import LabelMaterializationResult

        result = LabelMaterializationResult(
            plan=result.plan,
            records=(),
            dry_run=result.dry_run,
            wrote_output=result.wrote_output,
            output_path=result.output_path,
            value_store_handle=result.value_store_handle,
            planned_input_rows=result.planned_input_rows,
            planned_label_count=result.planned_label_count,
            runtime_seconds=result.runtime_seconds,
        )
    return FastLabelWorkerUnitOutput(
        materialization_result=result,
        pack=pack,
        registry_metadata={**registry_metadata, "worker_manifest_path": manifest_path.as_posix()},
        manifest=manifest,
    )


def _register_fast_label_worker_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    output: Any,
) -> MaterializedUnitEvidence:
    """Serially register one worker-computed fast label unit via LabelRegistry."""

    from alpha_system.labels.fast import (
        FAST_LABEL_PRODUCER_ENGINE_ID,
        FAST_LABEL_VALUE_SCHEMA_VERSION,
        FastLabelMaterializer,
    )
    from alpha_system.labels.registry import LabelRegistry

    result = _fast_label_result_with_records(output.materialization_result)
    handle = result.value_store_handle
    if handle is None:
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    materializer = FastLabelMaterializer()
    records = materializer.register_pack(
        result,
        output.pack,
        store=registry,
        registry_metadata=output.registry_metadata,
    )
    label_version_ids = tuple(record.label_version_id for record in records)
    if label_version_ids != tuple(output.pack.label_version_ids):
        raise ScaleoutError("registered label_version_id order changed")
    _verify_label_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        label_version_ids=label_version_ids,
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    for label_version_id in label_version_ids:
        record = registry.resolve_label(label_version_id)
        if record is None or record.producer_engine_id != FAST_LABEL_PRODUCER_ENGINE_ID:
            raise ScaleoutError("registered label is missing fast producer provenance")
        if record.value_schema_version != FAST_LABEL_VALUE_SCHEMA_VERSION:
            raise ScaleoutError("registered label fast value schema version mismatch")
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        label_version_ids=label_version_ids,
    )


def _label_scaleout_metadata(config: ScaleoutConfig, unit: ScaleoutUnit) -> dict[str, Any]:
    from alpha_system.labels.families.fixed_horizon import (
        MAINTENANCE_GUARD_VERSION,
        MAINTENANCE_POLICY_ID,
    )
    from alpha_system.labels.roll_guard import ROLL_GUARD_VERSION, ROLL_POLICY_ID

    terminal_key = "series_id+contract_id+event_ts"
    terminal_resolution = "exact_event_ts"
    if config.family == "cost_adjusted":
        terminal_key = "series_id+contract_id+bar_end_ts"
        terminal_resolution = "bar_end_aligned_bbo_proxy"
    return {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "label_set_id": unit.feature_set_id,
        "label_names": list(unit.feature_names),
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        "value_store_format": ValueStoreFormat.PARQUET.value,
        "roll_policy_id": ROLL_POLICY_ID,
        "roll_guard_version": ROLL_GUARD_VERSION,
        "roll_cross_policy": "drop",
        "maintenance_policy_id": MAINTENANCE_POLICY_ID,
        "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
        "maintenance_crossing_policy": "drop",
        "terminal_key": terminal_key,
        "terminal_resolution": terminal_resolution,
        "producer_engine_id": "alpha_system.labels.reference_engine.v1",
    }


def _fast_label_registry_metadata(config: ScaleoutConfig, unit: ScaleoutUnit) -> dict[str, Any]:
    from alpha_system.labels.families.fixed_horizon import (
        MAINTENANCE_GUARD_VERSION,
        MAINTENANCE_POLICY_ID,
    )
    from alpha_system.labels.fast import (
        FAST_LABEL_PRODUCER_ENGINE_ID,
        FAST_LABEL_VALUE_SCHEMA_VERSION,
    )
    from alpha_system.labels.roll_guard import ROLL_GUARD_VERSION, ROLL_POLICY_ID

    return {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "label_set_id": unit.feature_set_id,
        "label_names": list(unit.feature_names),
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        "value_store_format": ValueStoreFormat.PARQUET.value,
        "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
        "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
        "engine_selection": SCALEOUT_ENGINE_V1,
        "roll_policy_id": ROLL_POLICY_ID,
        "roll_guard_version": ROLL_GUARD_VERSION,
        "roll_cross_policy": "drop",
        "maintenance_policy_id": MAINTENANCE_POLICY_ID,
        "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
        "maintenance_crossing_policy": "drop",
        "terminal_key": "series_id+contract_id+event_ts",
        "terminal_resolution": (
            "full_path_window_guarded_before_scan"
            if config.family == "path"
            else "exact_event_ts"
        ),
    }


def _fast_label_pack_for_unit(config: ScaleoutConfig, unit: ScaleoutUnit) -> Any:
    definitions = _fast_label_definitions_for_unit(config, unit)
    if config.family in {"fixed_horizon", "extended_horizon"}:
        from alpha_system.labels.fast import build_fixed_horizon_label_pack

        return build_fixed_horizon_label_pack(definitions)
    if config.family == "session_close_maintenance_flat":
        from alpha_system.labels.fast import build_session_maintenance_label_pack

        return build_session_maintenance_label_pack(definitions)
    if config.family == "cost_adjusted":
        from alpha_system.labels.fast import build_cost_adjusted_label_pack

        return build_cost_adjusted_label_pack(definitions)
    if config.family == "path":
        from alpha_system.labels.fast import build_path_label_pack

        return build_path_label_pack(definitions)
    raise ScaleoutError(f"unsupported fast label scaleout family: {config.family}")


def _fast_label_definitions_for_unit(config: ScaleoutConfig, unit: ScaleoutUnit) -> tuple[Any, ...]:
    dataset_version_ids = _label_input_dataset_version_ids(unit)
    if config.family in {"fixed_horizon", "extended_horizon", "session_close_maintenance_flat"}:
        from alpha_system.cli.seed_pack import _build_label_spec, _label_materialization_scope
        from alpha_system.labels.families.fixed_horizon import (
            build_fixed_horizon_label_definition,
        )

        seed_config = _generic_label_seed_config(config, unit)
        label_set = seed_config.label_set
        if label_set is None:
            raise ScaleoutError("label unit seed config did not build a label_set")
        return tuple(
            build_fixed_horizon_label_definition(
                entry.name,
                _build_label_spec(seed_config, entry),
                dataset_version_ids=dataset_version_ids,
                materialization_scope=_label_materialization_scope(seed_config),
            )
            for entry in label_set.labels
        )
    if config.family == "cost_adjusted":
        from alpha_system.labels.families.cost_adjusted import (
            build_cost_adjusted_label_definition,
        )

        return tuple(
            build_cost_adjusted_label_definition(
                name,
                _cost_adjusted_label_spec(name, unit),
                dataset_version_ids=dataset_version_ids,
                materialization_scope=_label_unit_materialization_scope(unit),
            )
            for name in unit.feature_names
        )
    if config.family == "path":
        from alpha_system.labels.families.path import build_path_label_definition

        return tuple(
            build_path_label_definition(
                name,
                _path_label_spec(name, unit),
                dataset_version_ids=dataset_version_ids,
                materialization_scope=_label_unit_materialization_scope(unit),
            )
            for name in unit.feature_names
        )
    raise ScaleoutError(f"unsupported fast label scaleout family: {config.family}")


def _generic_label_seed_config(config: ScaleoutConfig, unit: ScaleoutUnit) -> Any:
    from alpha_system.cli.seed_pack import LabelSetConfig, LabelSpecConfig, SeedPackConfig

    return SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        label_set=LabelSetConfig(
            label_set_id=unit.feature_set_id,
            labels=tuple(
                LabelSpecConfig(name=name, horizon=_scaleout_label_horizon(name))
                for name in unit.feature_names
            ),
        ),
    )


# Process-local accepted-context cache. The accepted context (canonical bar
# load + quality/coverage reports + DatasetVersion handle) depends only on the
# dataset/window identity, never on the unit's label set, so consecutive
# per-horizon units of one symbol-year reuse one validation instead of
# re-parsing the canonical slice per unit. Bounded; cleared with the
# materializer caches for benchmark cold starts.
_LABEL_ACCEPTED_CONTEXT_CACHE: dict[tuple[str, ...], Any] = {}
_LABEL_ACCEPTED_CONTEXT_CACHE_MAX = 2


def _unit_primary_schema_is_bbo(unit: ScaleoutUnit) -> bool:
    """Return whether the unit's RESOLVED primary input schema is a BBO schema.

    Dispatch is on the unit's resolved ``schema_id`` (the on-disk primary
    surface), never on a config flag. OHLCV-primary units
    (``schema_id == "ohlcv_1m"``) return False and take the unchanged
    OHLCV-bound preflight; BBO-primary units (``schema_id`` startswith ``bbo``)
    return True and route the BBO canonical loader + BBO quality/coverage. The
    ``startswith("bbo")`` test mirrors ``_label_bbo_input_dataset``.
    """

    return unit.schema_id.startswith("bbo")


def _label_accepted_context(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> Any:
    from alpha_system.cli.seed_pack import _build_accepted_context

    if _unit_primary_schema_is_bbo(unit):
        return _bbo_primary_label_accepted_context(
            unit,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
        )

    cache_key = (
        unit.dataset_version_id,
        unit.symbol,
        unit.schema_id,
        unit.window_start_ts,
        unit.window_end_ts,
        str(canonical_root),
        str(dataset_registry_path),
    )
    cached = _LABEL_ACCEPTED_CONTEXT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    context = _build_accepted_context(
        _generic_label_seed_config(config, unit),
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )
    while len(_LABEL_ACCEPTED_CONTEXT_CACHE) >= _LABEL_ACCEPTED_CONTEXT_CACHE_MAX:
        _LABEL_ACCEPTED_CONTEXT_CACHE.pop(next(iter(_LABEL_ACCEPTED_CONTEXT_CACHE)), None)
    _LABEL_ACCEPTED_CONTEXT_CACHE[cache_key] = context
    return context


def _bbo_primary_label_accepted_context(
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> _BBOPrimaryLabelAcceptedContext:
    """Build the accepted-context preflight for a BBO-primary label unit.

    Reuses the existing BBO-aware preflight (``_build_bbo_accepted_context``),
    which loads the BBO canonical surface and builds BBO-appropriate
    quality/coverage reports (bad-quote / wide-spread / missing-bbo semantics
    via ``DataQualityReport.from_canonical_bbos`` and
    ``CoverageReport.from_canonical_bbos``). No OHLCV bars are loaded or
    projected: ``bar_rows`` is empty so the reference cost_adjusted compute sees
    an empty OHLCV trade-row overlay, which is the design intent for a unit that
    wires exactly one (BBO) input dataset (no second value truth, no
    single-dsv-wall relaxation). The accepted DatasetVersion carries the same
    ``dataset_version_id`` as the unit, so registered lvers stay on the BBO dsv.
    """

    cache_key = (
        "bbo_primary",
        unit.dataset_version_id,
        unit.symbol,
        unit.schema_id,
        unit.window_start_ts,
        unit.window_end_ts,
        str(canonical_root),
        str(dataset_registry_path),
    )
    cached = _LABEL_ACCEPTED_CONTEXT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    bbo_context = _build_bbo_accepted_context(
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    context = _BBOPrimaryLabelAcceptedContext(
        accepted=bbo_context.accepted,
        bar_rows=(),
        quality_status=bbo_context.quality_status,
        coverage_status=bbo_context.coverage_status,
    )
    while len(_LABEL_ACCEPTED_CONTEXT_CACHE) >= _LABEL_ACCEPTED_CONTEXT_CACHE_MAX:
        _LABEL_ACCEPTED_CONTEXT_CACHE.pop(next(iter(_LABEL_ACCEPTED_CONTEXT_CACHE)), None)
    _LABEL_ACCEPTED_CONTEXT_CACHE[cache_key] = context
    return context


def _label_input_dataset_version_ids(unit: ScaleoutUnit) -> tuple[str, ...]:
    values = tuple(dataset.dataset_version_id for dataset in unit.input_datasets)
    return values or (unit.dataset_version_id,)


def _label_unit_materialization_scope(unit: ScaleoutUnit) -> dict[str, str]:
    scope = {
        "dataset_version_id": unit.dataset_version_id,
        "partition_id": unit.partition_id,
        "partition_schema": unit.schema_id,
        "symbol": unit.symbol.upper(),
        "window_end_ts": unit.window_end_ts,
        "window_start_ts": unit.window_start_ts,
    }
    if unit.horizon:
        scope["horizon"] = unit.horizon
    return scope


def _scaleout_label_horizon(name: str, unit: ScaleoutUnit | None = None) -> str:
    if unit is not None and unit.horizon:
        return unit.horizon
    if name in {"session_close", "maintenance_flat"}:
        return name
    token = _label_horizon_token(name)
    if token.endswith("m") and token[:-1].isdigit():
        return token
    return "5m"


def _cost_adjusted_label_spec(name: str, unit: ScaleoutUnit) -> Any:
    from alpha_system.governance.label_spec import create_label_spec

    horizon = _scaleout_label_horizon(name, unit)
    model = "spread_plus_bps" if name == "cost_adjusted_fwd_ret" else "spread_adjusted"
    cost_model: dict[str, Any] = {
        "model": model,
        "spread_adjustment": "half_spread_round_trip",
    }
    if model == "spread_plus_bps":
        cost_model["fixed_cost_bps"] = 0.25
    return create_label_spec(
        horizon=horizon,
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "bar_end_aligned_bbo_proxy",
            "horizon_steps": int(horizon.removesuffix("m")),
        },
        cost_model=cost_model,
        target_stop_rules={
            "target_rule": "not_used_for_cost_adjusted_forward_return",
            "stop_rule": "not_used_for_cost_adjusted_forward_return",
        },
        availability_time=unit.window_start_ts,
        forbidden_feature_overlap={
            "label_ids": [name],
            "aliases": [f"scaleout_{name}"],
            "transforms": [f"label({name})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _path_label_spec(name: str, unit: ScaleoutUnit) -> Any:
    from alpha_system.governance.label_spec import create_label_spec

    horizon_steps = int(_scaleout_label_horizon(name, unit).removesuffix("m"))
    path_label_ids = [f"path_{label_name}" for label_name in unit.feature_names]
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
            "target_return": 0.02,
            "stop_return": -0.02,
            "same_bar_policy": "ambiguous",
        },
        availability_time=unit.window_start_ts,
        forbidden_feature_overlap={
            "label_ids": path_label_ids,
            "aliases": list(unit.feature_names),
            "transforms": [f"label({label_id})" for label_id in path_label_ids],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _fast_label_pack_requires_bbo(pack: Any) -> bool:
    from alpha_system.labels.families.cost_adjusted import CostAdjustedLabelDefinition
    from alpha_system.labels.families.fixed_horizon import FixedHorizonLabelDefinition

    for definition in pack.definitions:
        if isinstance(definition, CostAdjustedLabelDefinition):
            return True
        if isinstance(definition, FixedHorizonLabelDefinition) and definition.is_midprice:
            return True
    return False


def _empty_bbo_loader(**_kwargs: Any) -> tuple[Mapping[str, Any], ...]:
    return ()


def _label_bbo_input_dataset(unit: ScaleoutUnit) -> ScaleoutInputDataset | None:
    """Return the unit's BBO input DatasetVersion, if one is wired.

    The BBO panel must load from the BBO DatasetVersion, never from a
    ``schema=bbo_1m`` path under the OHLCV DatasetVersion (LCFP-P08 repair).
    """

    for dataset in unit.input_datasets:
        if dataset.schema_id.startswith("bbo"):
            return dataset
    return None


# Process-local fast-label materializers. Sharing one materializer per BBO
# flavor lets consecutive units of the same symbol-year reuse the loaded frame,
# prepared shared panel, and terminal-index models (the once-per-batch input
# adaptation), instead of re-running them per horizon unit. The materializer
# bounds its own caches, and registry writes stay on the serial keystone path.
_FAST_LABEL_MATERIALIZERS: dict[bool, Any] = {}


def _shared_fast_label_materializer(*, requires_bbo: bool) -> Any:
    from alpha_system.labels.fast import FastLabelMaterializer

    materializer = _FAST_LABEL_MATERIALIZERS.get(requires_bbo)
    if materializer is None:
        materializer = (
            FastLabelMaterializer()
            if requires_bbo
            else FastLabelMaterializer(canonical_bbo_loader=_empty_bbo_loader)
        )
        _FAST_LABEL_MATERIALIZERS[requires_bbo] = materializer
    return materializer


def reset_fast_label_materializer_caches() -> None:
    """Drop process-local fast-label caches (benchmark cold starts)."""

    _FAST_LABEL_MATERIALIZERS.clear()
    _LABEL_ACCEPTED_CONTEXT_CACHE.clear()


def _bar_or_dense_inputs(
    config: ScaleoutConfig,
    context: Any,
    governance_metadata: Mapping[str, Any],
) -> Any:
    from alpha_system.features.engine.materialization import FeatureMaterializationInputs

    return FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=() if config.dense_grid_required else context.bar_rows,
        dense_grid_bar_rows=context.bar_rows if config.dense_grid_required else (),
        governance_metadata=governance_metadata,
    )


def materialize_session_calendar_maintenance_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one Session / Calendar / Maintenance unit through the seam."""

    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    if (
        config.family != "session_calendar_maintenance"
        or unit.family != "session_calendar_maintenance"
    ):
        raise ScaleoutError(
            "FUTSUB-P07 executor supports only the session_calendar_maintenance family"
        )

    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(name=name, window_length=1, horizon=1)
                for name in unit.feature_names
            ),
        ),
    )
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "point_in_time_session_metadata_guard": "enforced",
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_session_definition_builders(config, unit),
        inputs_factory=lambda gm: _bar_or_dense_inputs(config, context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P07 session/calendar/maintenance FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no session feature values",
    )


def materialize_vwap_session_auction_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one VWAP / session-auction unit through the sanctioned seam."""

    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    if config.family != "vwap_session_auction" or unit.family != "vwap_session_auction":
        raise ScaleoutError("FUTSUB-P08 executor supports only the vwap_session_auction family")

    bindings = _vwap_session_auction_bindings(unit.feature_names)
    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(name=binding.ohlcv_name, window_length=1, horizon=1)
                for binding in bindings
            ),
        ),
    )
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "running_vwap_point_in_time_guard": "enforced",
        "final_session_aggregate_intraday_use": "forbidden",
        "feature_bindings": [_vwap_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_vwap_session_auction_definition_builders(config, unit),
        inputs_factory=lambda gm: _ohlcv_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P08 VWAP / session-auction FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no VWAP/session feature values",
    )


def materialize_regime_volatility_compression_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one regime / volatility / compression unit through the seam."""

    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    if (
        config.family != "regime_volatility_compression"
        or unit.family != "regime_volatility_compression"
    ):
        raise ScaleoutError(
            "FUTSUB-P09 executor supports only the regime_volatility_compression family"
        )

    bindings = _regime_volatility_compression_bindings(unit.feature_names)
    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(
                    name=binding.primitive_name,
                    window_length=binding.window_length,
                    horizon=binding.horizon,
                )
                for binding in bindings
            ),
        ),
    )
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "available_ts_regime_guard": "enforced",
        "feature_bindings": [_regime_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_regime_volatility_compression_definition_builders(
            config, unit
        ),
        inputs_factory=lambda gm: _ohlcv_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P09 regime / volatility / compression FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no regime feature values",
    )


def materialize_liquidity_sweep_pa_structure_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one liquidity-sweep / PA-structure unit through the seam."""

    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    if (
        config.family != "liquidity_sweep_pa_structure"
        or unit.family != "liquidity_sweep_pa_structure"
    ):
        raise ScaleoutError(
            "FUTSUB-P10 executor supports only the liquidity_sweep_pa_structure family"
        )

    bindings = _liquidity_pa_structure_bindings(unit.feature_names)
    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(
                    name=binding.primitive_name,
                    window_length=binding.window_length,
                    horizon=1,
                )
                for binding in bindings
            ),
        ),
    )
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "objective_pa_guard": "enforced",
        "subjective_pa_encoding": "forbidden",
        "feature_bindings": [_liquidity_pa_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_liquidity_pa_structure_definition_builders(config, unit),
        inputs_factory=lambda gm: _ohlcv_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P10 liquidity-sweep / PA-structure FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no liquidity/PA feature values",
    )


def materialize_volume_activity_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one volume / activity unit through the sanctioned seam."""

    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    if config.family != "volume_activity" or unit.family != "volume_activity":
        raise ScaleoutError("FUTSUB-P11 executor supports only the volume_activity family")

    bindings = _volume_activity_bindings(unit.feature_names)
    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(
                    name=binding.primitive_name,
                    window_length=binding.window_length,
                    horizon=binding.horizon,
                )
                for binding in bindings
            ),
        ),
    )
    context = _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "activity_primitives_only_guard": "enforced",
        "feature_bindings": [_volume_activity_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_volume_activity_definition_builders(config, unit),
        inputs_factory=lambda gm: _ohlcv_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P11 volume / activity FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no volume/activity feature values",
    )


def materialize_bbo_tradability_top_book_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one BBO tradability / top-book unit through the sanctioned seam."""

    if (
        config.family != "bbo_tradability_top_book"
        or unit.family != "bbo_tradability_top_book"
    ):
        raise ScaleoutError(
            "FUTSUB-P12 executor supports only the bbo_tradability_top_book family"
        )

    bindings = _bbo_tradability_top_book_bindings(unit.feature_names)
    context = _build_bbo_accepted_context(
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "bbo_proxy_semantics": "time_sampled_forward_filled_tradability_proxy",
        "execution_truth_claims": "forbidden",
        "passive_fill_claims": "forbidden",
        "queue_priority_claims": "forbidden",
        "impact_claims": "forbidden",
        "available_ts_forward_fill_guard": "preserve_canonical_bbo_available_ts",
        "missingness_policy": "surface_flags_no_silent_imputation",
        "feature_bindings": [_bbo_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_bbo_tradability_top_book_definition_builders(config, unit),
        inputs_factory=lambda gm: _bbo_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P12 BBO tradability / top-book FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no BBO feature values",
    )


def _bbo_inputs(context: Any, governance_metadata: Mapping[str, Any]) -> Any:
    from alpha_system.features.engine.materialization import FeatureMaterializationInputs

    return FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bbo_rows=context.bbo_rows,
        governance_metadata=governance_metadata,
    )


def materialize_cross_market_alignment_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one cross-market alignment unit through the sanctioned seam."""

    if (
        config.family != "cross_market_alignment"
        or unit.family != "cross_market_alignment"
    ):
        raise ScaleoutError("FUTSUB-P13 executor supports only the cross_market_alignment family")

    bindings = _cross_market_alignment_bindings(unit.feature_names)
    context = _build_cross_market_accepted_context(
        config,
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )

    base_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "family": config.family,
        "target_symbol": unit.symbol.upper(),
        "alignment_policy": "strict_intersection",
        "per_instrument_available_ts": "preserved",
        "cross_instrument_forward_fill": "forbidden",
        "missing_instrument_imputation": "forbidden",
        "feature_bindings": [_cross_market_binding_metadata(binding) for binding in bindings],
        "row_counts_by_symbol": dict(context.row_counts_by_symbol),
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    governance_metadata = {**base_metadata, "unit_id": unit.unit_id}
    return _materialize_unit_per_feature(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        accepted=context.accepted,
        feature_definition_builders=_cross_market_alignment_definition_builders(config, unit),
        inputs_factory=lambda gm: _cross_market_inputs(context, gm),
        feature_set_metadata=base_metadata,
        governance_metadata=governance_metadata,
        description="FUTSUB-P13 cross-market alignment FeaturePack scaleout unit",
        feature_set_version_suffix=lambda definition: _definition_feature_spec(
            definition
        ).feature_id,
        empty_values_message="unit {unit_id} produced no cross-market feature values",
    )


def _cross_market_inputs(context: Any, governance_metadata: Mapping[str, Any]) -> Any:
    from alpha_system.features.engine.materialization import FeatureMaterializationInputs

    return FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
        governance_metadata=governance_metadata,
    )


def materialize_v1_feature_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one scaleout unit through the V1 fast-pack producer path."""

    output = _compute_v1_feature_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=False,
        include_records=True,
    )
    return _register_v1_worker_output(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        output=output,
    )


def materialize_v1_feature_unit_force_recompute(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one V1 feature unit while honoring serial force-recompute."""

    output = _compute_v1_feature_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=False,
        include_records=True,
        force_recompute=True,
    )
    return _register_v1_worker_output(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        output=output,
    )


def _compute_v1_feature_unit_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    *,
    write_manifest: bool,
    include_records: bool,
    prepared_feature_set: Any | None = None,
    prepared_feature_request_payloads: Mapping[str, Mapping[str, Any]] | None = None,
    prepared_registry_metadata: Mapping[str, Any] | None = None,
    force_recompute: bool = False,
) -> Any:
    """Compute and persist one V1 unit without mutating the feature registry."""

    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.fast import (
        FAST_PRODUCER_ENGINE_ID,
        FAST_VALUE_SCHEMA_VERSION,
        FastWorkerUnitOutput,
        PackMaterializer,
        build_fast_feature_pack,
        worker_manifest_from_result,
        worker_manifest_path,
        write_worker_manifest,
    )

    if prepared_feature_set is None:
        prepared = _prepare_v1_worker_job(
            config,
            unit,
            alpha_data_root=alpha_data_root,
            force_recompute=force_recompute,
        )
        feature_set = prepared.feature_set
        request_payloads = prepared.feature_request_payloads
        governance_metadata = prepared.registry_metadata
    else:
        feature_set = prepared_feature_set
        if prepared_feature_request_payloads is None or prepared_registry_metadata is None:
            raise ScaleoutError("prepared V1 worker job is incomplete")
        request_payloads = prepared_feature_request_payloads
        governance_metadata = prepared_registry_metadata
    pack = build_fast_feature_pack(feature_set)
    materializer = PackMaterializer()
    accepted, canonical_frame = _v1_context_and_frame(
        config,
        unit,
        materializer=materializer,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=unit.partition_id,
        canonical_frame=canonical_frame,
        alpha_data_root=alpha_data_root,
        governance_metadata=governance_metadata,
        output_namespace=config.value_namespace,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no V1 feature values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    _require_text(handle.content_hash, "value_store_handle.content_hash")
    feature_version_ids = tuple(declaration.feature_version_id for declaration in pack.declarations)
    manifest_path = worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    manifest = worker_manifest_from_result(
        unit_key=_worker_unit_key(unit),
        result=result,
        feature_version_ids=feature_version_ids,
        producer_engine_id=FAST_PRODUCER_ENGINE_ID,
        value_schema_version=FAST_VALUE_SCHEMA_VERSION,
        manifest_path=manifest_path,
    )
    if write_manifest:
        write_worker_manifest(manifest_path, manifest)
    if not include_records:
        from alpha_system.features.engine import FeatureMaterializationResult

        result = FeatureMaterializationResult(
            plan=result.plan,
            records=(),
            dry_run=result.dry_run,
            wrote_output=result.wrote_output,
            output_path=result.output_path,
            value_store_handle=result.value_store_handle,
        )
    return FastWorkerUnitOutput(
        materialization_result=result,
        feature_set=feature_set,
        feature_request_payloads=request_payloads,
        registry_metadata=governance_metadata,
        manifest=manifest,
    )


def _register_v1_worker_output(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    output: Any,
    rebuild_request_against_live_registry: bool = False,
) -> MaterializedUnitEvidence:
    """Serially register one worker-computed V1 unit through FeatureStore.

    ``rebuild_request_against_live_registry`` is set only by the PARALLEL worker
    stage. The serial executor computes each unit's request immediately before it
    registers that same unit, so the request still matches the live registry and
    no rebuild is needed. The parallel stage instead prepares every unit's request
    up front (against the initial registry) and registers them one-by-one through
    this single writer, which mutates the registry per unit -- so a later unit's
    pre-computed request id no longer matches its spec
    ("checked FeatureRequest id must match FeatureSpec.feature_request_id"). When
    the flag is set, re-run the FLF-P05 duplicate-exposure request gate against the
    LIVE registry here and rebuild this unit's plan with the resulting fresh
    feature_set, mirroring how _materialize_unit_per_feature builds each feature
    against the live registry. feature_version_id is content-addressed independent
    of registry state, so the worker's already-computed values still register under
    the same identity and at the same Parquet output path (the path does not depend
    on the request id); only the registry-state-dependent request provenance and the
    plan content hash change, rebuilt from the worker plan's own dataset/partition/
    output_path with no second canonical read or accepted-version handle.
    """

    from alpha_system.features.engine.materialization import (
        _feature_version_ids,
        _plan_content_hash,
    )
    from alpha_system.features.fast import PackMaterializer, build_fast_feature_pack

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    materializer = PackMaterializer()
    result = _v1_result_with_records(output.materialization_result)
    handle = result.value_store_handle
    if handle is None:
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    pack = build_fast_feature_pack(output.feature_set)
    records: list[Any] = []
    if not hasattr(result, "plan"):
        records.extend(
            materializer.register_pack(
                result,
                pack,
                feature_requests=output.feature_request_payloads,
                store=store,
                registry_metadata=output.registry_metadata,
            )
        )
    else:
        current_features = list(result.plan.feature_set.features)
        for ordinal, declaration in enumerate(pack.declarations):
            existing = store.resolve_feature(declaration.feature_version_id)
            if existing is not None:
                _require_existing_v1_materialization(existing, declaration.feature_version_id)
                if _registered_content_hash(existing) == content_hash:
                    records.append(existing)
                    continue
                current_features[ordinal] = existing.feature_spec
                updated_result = _v1_result_with_feature_set(
                    result,
                    features=tuple(current_features),
                )
                records.append(
                    _register_existing_v1_feature_update(
                        store,
                        updated_result,
                        existing,
                        registry_metadata=output.registry_metadata,
                    )
                )
                continue

            fresh, fresh_pack, fresh_declaration = _fresh_v1_declaration_for_version(
                config,
                unit,
                expected_version_id=declaration.feature_version_id,
                alpha_data_root=alpha_data_root,
            )
            current_features[ordinal] = fresh_declaration.feature_spec
            fresh_feature_set = replace(
                result.plan.feature_set,
                features=tuple(current_features),
            )
            worker_plan = result.plan
            fresh_idempotency_key = _plan_content_hash(
                fresh_feature_set,
                dataset_version_id=worker_plan.dataset_version_id,
                partition_id=worker_plan.partition_id,
                output_path=worker_plan.output_path,
                governance_metadata=worker_plan.governance_metadata,
            )
            fresh_result = replace(
                result,
                plan=replace(
                    worker_plan,
                    feature_set=fresh_feature_set,
                    plan_id=f"fmat_{fresh_idempotency_key}",
                    idempotency_key=fresh_idempotency_key,
                    feature_version_ids=_feature_version_ids(fresh_feature_set),
                ),
            )
            records.extend(
                materializer.register_pack(
                    fresh_result,
                    fresh_pack,
                    feature_requests=fresh.feature_request_payloads,
                    store=store,
                    registry_metadata=fresh.registry_metadata,
                    reconcile_after_register=False,
                )
            )
    feature_version_ids = tuple(record.feature_version_id for record in records)
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=feature_version_ids,
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    reconcile_registered_feature_pack_path(
        alpha_data_root=alpha_data_root,
        parquet_path=parquet_path,
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        feature_version_ids=feature_version_ids,
    )


def _require_existing_v1_materialization(record: Any, feature_version_id: str) -> None:
    if not _registry_record_matches_engine(record, SCALEOUT_ENGINE_V1):
        raise ScaleoutError(
            "existing V1 feature version has non-V1 producer provenance: "
            f"{feature_version_id}"
        )
    parquet_path = getattr(record, "parquet_path", None)
    if not parquet_path or not Path(parquet_path).exists():
        raise ScaleoutError(
            "existing V1 feature version is missing Parquet materialization: "
            f"{feature_version_id}"
        )


def _registered_content_hash(record: Any) -> str:
    return str(getattr(record, "value_content_hash", "") or "")


def _v1_result_with_feature_set(result: Any, *, features: tuple[Any, ...]) -> Any:
    from alpha_system.features.engine.materialization import (
        _feature_version_ids,
        _plan_content_hash,
    )

    worker_plan = result.plan
    feature_set = replace(worker_plan.feature_set, features=features)
    idempotency_key = _plan_content_hash(
        feature_set,
        dataset_version_id=worker_plan.dataset_version_id,
        partition_id=worker_plan.partition_id,
        output_path=worker_plan.output_path,
        governance_metadata=worker_plan.governance_metadata,
    )
    return replace(
        result,
        plan=replace(
            worker_plan,
            feature_set=feature_set,
            plan_id=f"fmat_{idempotency_key}",
            idempotency_key=idempotency_key,
            feature_version_ids=_feature_version_ids(feature_set),
        ),
    )


def _register_existing_v1_feature_update(
    store: Any,
    result: Any,
    existing: Any,
    *,
    registry_metadata: Mapping[str, Any],
) -> Any:
    from alpha_system.features.fast import FAST_PRODUCER_ENGINE_ID

    return store.register_materialized_feature(
        result,
        feature_spec=existing.feature_spec,
        feature_version=existing.feature_version,
        feature_request=_feature_request_payload_mapping(existing.feature_request_payload),
        lineage=existing.lineage,
        producer_engine_id=FAST_PRODUCER_ENGINE_ID,
        registry_metadata=registry_metadata,
    )


def _feature_request_payload_mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise ScaleoutError("existing feature request payload is not a mapping")
    return value


def _fresh_v1_declaration_for_version(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    expected_version_id: str,
    alpha_data_root: Path,
) -> tuple[_V1PreparedWorkerJob, Any, Any]:
    """Rebuild one live-registry V1 declaration selected by stable identity."""

    from alpha_system.features.contracts import FeatureSetSpec
    from alpha_system.features.fast import (
        FAST_PRODUCER_ENGINE_ID,
        FastFeaturePack,
        build_fast_feature_pack,
        feature_request_payloads,
    )

    builders = _feature_definition_builders_for_unit(config, unit)
    preview_definitions = tuple(builder(lambda: ()) for builder in builders)
    matching_ordinals = tuple(
        ordinal
        for ordinal, definition in enumerate(preview_definitions)
        if definition.feature_version_id == expected_version_id
    )
    if len(matching_ordinals) != 1:
        raise ScaleoutError(
            "fresh V1 declaration rebuild could not select the expected feature_version_id"
        )
    definition = builders[matching_ordinals[0]](
        FeatureStore.from_alpha_data_root(alpha_data_root).registry
    )
    if definition.feature_version_id != expected_version_id:
        raise ScaleoutError("fresh V1 declaration changed feature_version_id")
    feature_spec = _definition_feature_spec(definition)
    checked_request = definition.request_gate_decision.checked_feature_request
    if checked_request is None:
        raise ScaleoutError("FeatureRequest gate did not return a checked request")
    fresh = _V1PreparedWorkerJob(
        unit=unit,
        feature_set=FeatureSetSpec(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            features=(feature_spec,),
            description=f"FCFP-P15 V1 {config.family} scaleout unit",
            metadata={
                "campaign_id": config.campaign_id,
                "phase_id": config.phase_id,
                "family": config.family,
                "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                "input_dataset_versions": [
                    dataset.to_dict() for dataset in unit.input_datasets
                ],
            },
        ),
        feature_request_payloads=feature_request_payloads(
            {feature_spec.feature_id: checked_request}
        ),
        registry_metadata=_v1_registry_metadata(config, unit),
    )
    fresh_pack = build_fast_feature_pack(fresh.feature_set)
    matches = tuple(
        declaration
        for declaration in fresh_pack.declarations
        if declaration.feature_version_id == expected_version_id
    )
    if len(matches) != 1:
        raise ScaleoutError(
            "fresh V1 declaration rebuild did not select the expected feature_version_id"
        )
    fresh_declaration = matches[0]
    single_pack = FastFeaturePack(
        feature_set=replace(fresh.feature_set, features=(fresh_declaration.feature_spec,)),
        declarations=(fresh_declaration,),
        prepare_frame=fresh_pack.prepare_frame,
    )
    return fresh, single_pack, fresh_declaration


def _prepare_v1_worker_job(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    force_recompute: bool = False,
) -> _V1PreparedWorkerJob:
    """Build V1 identity/request context in the serial parent process."""

    from alpha_system.features.contracts import FeatureSetSpec
    from alpha_system.features.fast import (
        FAST_PRODUCER_ENGINE_ID,
        FAST_VALUE_SCHEMA_VERSION,
        feature_request_payloads,
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    existing_context = (
        _existing_v1_feature_context_for_force_recompute(
            config,
            unit,
            store,
            alpha_data_root=alpha_data_root,
        )
        if force_recompute
        else None
    )
    if existing_context is None:
        definitions = _feature_definitions_for_unit(config, unit, store.registry)
        if not definitions:
            raise ScaleoutError(f"unit {unit.unit_id} did not select any governed features")
        feature_specs = tuple(_definition_feature_spec(definition) for definition in definitions)
        feature_requests: dict[str, Any] = {}
        for definition, feature_spec in zip(definitions, feature_specs, strict=True):
            checked_request = definition.request_gate_decision.checked_feature_request
            if checked_request is None:
                raise ScaleoutError("FeatureRequest gate did not return a checked request")
            if feature_spec.feature_id in feature_requests:
                raise ScaleoutError(
                    f"duplicate V1 feature selection for {feature_spec.feature_id}"
                )
            feature_requests[feature_spec.feature_id] = checked_request
    else:
        feature_specs, feature_requests = existing_context
    _require_trusted_scaleout_feature_specs(config, feature_specs)
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=feature_specs,
        description=f"FCFP-P15 V1 {config.family} scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    return _V1PreparedWorkerJob(
        unit=unit,
        feature_set=feature_set,
        feature_request_payloads=feature_request_payloads(feature_requests),
        registry_metadata=_v1_registry_metadata(config, unit),
    )


def _require_trusted_scaleout_feature_specs(
    config: ScaleoutConfig,
    feature_specs: Sequence[Any],
) -> None:
    if config.family == "session_calendar_maintenance":
        rejected = sorted(
            _require_text(getattr(feature, "feature_id", ""), "feature_spec.feature_id")
            for feature in feature_specs
            if (
                not getattr(feature, "live", False)
                or not getattr(feature, "implementation_eligible", False)
                or not getattr(feature, "window").is_live_compatible
            )
        )
        if rejected:
            raise ScaleoutError(
                "session_calendar_maintenance scaleout excludes offline/non-causal "
                "features: " + ", ".join(rejected)
            )
    if config.family == "cross_market_alignment":
        rejected = []
        for feature in feature_specs:
            parameters = getattr(feature, "transform").parameters.to_dict()
            if parameters.get("alignment_policy") != "strict_intersection":
                rejected.append(
                    _require_text(getattr(feature, "feature_id", ""), "feature_spec.feature_id")
                )
        if rejected:
            raise ScaleoutError(
                "cross_market_alignment scaleout requires "
                "alignment_policy=strict_intersection: " + ", ".join(sorted(rejected))
            )


def _existing_v1_feature_context_for_force_recompute(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    store: Any,
    *,
    alpha_data_root: Path,
) -> tuple[tuple[Any, ...], dict[str, Mapping[str, Any]]] | None:
    """Return V1 specs/request payloads for force-recompute preview ids.

    Force-recompute needs to write the complete pack at the established value
    path. Some repair packs intentionally contain a mix of already-registered
    fvids and newly-previewed replacement fvids. Reuse existing request
    provenance for registered fvids so they do not re-enter the duplicate gate,
    and build only missing fvids against the live registry.
    """

    feature_version_ids = _preview_feature_version_ids(config, unit)
    if not feature_version_ids:
        return None
    feature_specs: list[Any] = []
    feature_requests: dict[str, Mapping[str, Any]] = {}
    for feature_version_id in feature_version_ids:
        existing = store.resolve_feature(feature_version_id)
        if existing is not None:
            _require_existing_v1_materialization(existing, feature_version_id)
            feature_spec = existing.feature_spec
            request_payload = existing.feature_request_payload
        else:
            fresh, _, fresh_declaration = _fresh_v1_declaration_for_version(
                config,
                unit,
                expected_version_id=feature_version_id,
                alpha_data_root=alpha_data_root,
            )
            feature_spec = fresh_declaration.feature_spec
            request_payload = fresh.feature_request_payloads.get(feature_spec.feature_id)
            if request_payload is None:
                raise ScaleoutError(
                    "fresh V1 declaration rebuild did not return a FeatureRequest "
                    f"payload for {feature_spec.feature_id}"
                )
        feature_id = _require_text(feature_spec.feature_id, "feature_spec.feature_id")
        if feature_id in feature_requests:
            raise ScaleoutError(f"duplicate V1 feature selection for {feature_id}")
        feature_specs.append(feature_spec)
        feature_requests[feature_id] = request_payload
    return tuple(feature_specs), feature_requests


def _worker_unit_key(unit: ScaleoutUnit) -> dict[str, object]:
    return {
        "unit_id": unit.unit_id,
        "family": unit.family,
        "symbol": unit.symbol,
        "year": unit.year,
        "dataset_version_id": unit.dataset_version_id,
        "partition_id": unit.partition_id,
        "input_datasets": [dataset.to_dict() for dataset in unit.input_datasets],
    }


def _v1_result_with_records(result: Any) -> Any:
    if not hasattr(result, "records") or getattr(result, "records", ()):
        return result
    from alpha_system.features.engine import FeatureMaterializationResult

    handle = result.value_store_handle
    if handle is None or not handle.parquet_path:
        raise ScaleoutError("worker output is missing a Parquet value-store handle")
    return FeatureMaterializationResult(
        plan=result.plan,
        records=_feature_value_records_from_parquet(handle.parquet_path),
        dry_run=result.dry_run,
        wrote_output=result.wrote_output,
        output_path=result.output_path,
        value_store_handle=handle,
    )


def _fast_label_result_with_records(result: Any) -> Any:
    if not hasattr(result, "records") or getattr(result, "records", ()):
        return result
    from alpha_system.labels.engine import LabelMaterializationResult

    handle = result.value_store_handle
    if handle is None or not handle.parquet_path:
        raise ScaleoutError("fast label worker output is missing a Parquet handle")
    return LabelMaterializationResult(
        plan=result.plan,
        records=_label_value_records_from_parquet(handle.parquet_path, result.plan),
        dry_run=result.dry_run,
        wrote_output=result.wrote_output,
        output_path=result.output_path,
        value_store_handle=handle,
        planned_input_rows=result.planned_input_rows,
        planned_label_count=result.planned_label_count,
        runtime_seconds=result.runtime_seconds,
    )


def _fast_label_plan_from_manifest(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    pack: Any,
) -> Any:
    from alpha_system.features.consumption import AcceptedDatasetVersion
    from alpha_system.data.foundation.datasets import DatasetVersion
    from alpha_system.labels.engine import build_label_materialization_plan

    dataset_version = DatasetVersion(
        dataset_version_id=unit.dataset_version_id,
        source="dsrc_manifest_resume",
        symbol_universe=(unit.symbol,),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=_datetime_from_iso(unit.window_start_ts),
        end_ts=_datetime_from_iso(unit.window_end_ts),
        contract_universe=(unit.symbol,),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash="0" * 64,
        code_hash="0" * 64,
        config_hash="0" * 64,
        quality_report_hash="0" * 64,
        created_at=_datetime_from_iso(unit.window_end_ts),
    )
    accepted = AcceptedDatasetVersion(
        registry_path="manifest_resume",
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=None,
        coverage_report=None,
    )
    return build_label_materialization_plan(
        pack.definitions,
        accepted,
        partition_id=unit.partition_id,
        instrument_ids=(unit.symbol,),
        alpha_data_root=alpha_data_root,
        governance_metadata=_fast_label_registry_metadata(config, unit),
        output_namespace=config.value_namespace,
    )


def _label_value_records_from_parquet(parquet_path: str | Path, plan: Any) -> tuple[Any, ...]:
    from alpha_system.core.value_store import load_parquet_values
    from alpha_system.labels.version import LabelValueRecord

    contracts = {
        contract.derive_label_version().label_version_id: contract
        for contract in plan.label_contracts
    }
    records: list[LabelValueRecord] = []
    for payload in load_parquet_values(parquet_path):
        version_id = _require_text(payload.get("label_version_id"), "label_version_id")
        contract = contracts.get(version_id)
        if contract is None:
            raise ScaleoutError(f"Parquet label row is not in plan: {version_id}")
        records.append(
            LabelValueRecord(
                label_version_id=version_id,
                entity_id=_require_text(payload.get("entity_id"), "entity_id"),
                event_ts=_datetime_from_iso(payload.get("event_ts")),
                horizon_end_ts=_datetime_from_iso(payload.get("horizon_end_ts")),
                label_available_ts=_datetime_from_iso(payload.get("label_available_ts")),
                value=payload.get("value"),
                label_contract=contract,
                quality_flags=tuple(
                    _require_text(value, "quality_flag")
                    for value in (
                        payload.get("quality_flags")
                        if isinstance(payload.get("quality_flags"), Sequence)
                        and not isinstance(payload.get("quality_flags"), str)
                        else ()
                    )
                ),
            )
        )
    return tuple(records)


def _datetime_from_iso(value: object) -> datetime:
    text = _require_text(value, "datetime")
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _feature_value_records_from_parquet(parquet_path: str | Path) -> tuple[Any, ...]:
    from alpha_system.core.value_store import load_parquet_values
    from alpha_system.features.contracts import FeatureValueRecord

    return tuple(
        FeatureValueRecord(
            feature_version_id=_require_text(row.get("feature_version_id"), "feature_version_id"),
            entity_id=_require_text(row.get("entity_id"), "entity_id"),
            event_ts=_datetime_from_value(row.get("event_ts"), "event_ts"),
            available_ts=_datetime_from_value(row.get("available_ts"), "available_ts"),
            value=row.get("value"),
            quality_flags=tuple(row.get("quality_flags") or ()),
        )
        for row in load_parquet_values(parquet_path)
    )


def _datetime_from_value(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    text = _require_text(value, field_name)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _v1_context_and_frame(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    materializer: Any,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> tuple[Any, Any]:
    if config.family == "bbo_tradability_top_book":
        context = _build_bbo_accepted_context(
            unit,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
        )
        return context.accepted, materializer.frame_from_rows(context.bbo_rows)
    if config.family == "cross_market_alignment":
        context = _build_cross_market_accepted_context(
            config,
            unit,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
        )
        return context.accepted, materializer.frame_from_rows(context.bar_rows)
    context = _build_ohlcv_accepted_context(
        config,
        unit,
        dataset_registry_path=dataset_registry_path,
        canonical_root=canonical_root,
    )
    return context.accepted, materializer.frame_from_rows(context.bar_rows)


def _build_ohlcv_accepted_context(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> Any:
    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
        _build_accepted_context,
    )

    seed_config = SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=tuple(
                FeatureSpecConfig(name=name, window_length=_feature_window(name), horizon=1)
                for name in unit.feature_names
            ),
        ),
    )
    return _build_accepted_context(
        seed_config,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        bar_rows=None,
        bar_row_loader=_session_bar_row_loader,
        quality_coverage_builder=_scaleout_quality_coverage_builder,
        repo_root=Path.cwd(),
    )


def _feature_definition_builders_for_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    if config.family == "base_ohlcv":
        from alpha_system.cli.seed_pack import (
            _build_feature_request,
            _coerce_feature_name,
            _feature_input_scope,
        )
        from alpha_system.features.families.ohlcv import build_ohlcv_feature_definition

        seed_config = _seed_config(config, unit)

        def _make(entry: Any) -> Callable[[object], Any]:
            def _build(registry_reader: object) -> Any:
                return build_ohlcv_feature_definition(
                    _coerce_feature_name(entry.name),
                    _build_feature_request(
                        seed_config.feature_set,
                        entry.name,
                        exposure_scope=unit.partition_id,
                    ),
                    registry_reader,
                    dataset_version_ids=(unit.dataset_version_id,),
                    window_length=entry.window_length,
                    horizon=entry.horizon,
                    reset_on_session=False,
                    input_scope=_feature_input_scope(seed_config),
                )

            return _build

        return tuple(_make(entry) for entry in seed_config.feature_set.features)
    if config.family == "session_calendar_maintenance":
        return _session_definition_builders(config, unit)
    if config.family == "vwap_session_auction":
        return _vwap_session_auction_definition_builders(config, unit)
    if config.family == "regime_volatility_compression":
        return _regime_volatility_compression_definition_builders(config, unit)
    if config.family == "liquidity_sweep_pa_structure":
        return _liquidity_pa_structure_definition_builders(config, unit)
    if config.family == "volume_activity":
        return _volume_activity_definition_builders(config, unit)
    if config.family == "bbo_tradability_top_book":
        return _bbo_tradability_top_book_definition_builders(config, unit)
    if config.family == "cross_market_alignment":
        return _cross_market_alignment_definition_builders(config, unit)
    raise ScaleoutError(f"unsupported scaleout family: {config.family}")


def _feature_definitions_for_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _feature_definition_builders_for_unit(config, unit)
    )


def _unit_executor_for_family(
    family: str,
    *,
    engine: str = DEFAULT_SCALEOUT_ENGINE,
) -> UnitExecutor:
    engine_token = _normalize_engine(engine)
    if family in {"fixed_horizon", "session_close_maintenance_flat"}:
        if engine_token == SCALEOUT_ENGINE_V1:
            return materialize_fast_label_unit
        return materialize_reference_label_unit
    if family in {"cost_adjusted", "path"}:
        if engine_token == SCALEOUT_ENGINE_V1:
            return materialize_fast_label_unit
        return materialize_reference_label_unit
    if engine_token == SCALEOUT_ENGINE_V1:
        return materialize_v1_feature_unit
    if family == "base_ohlcv":
        return materialize_base_ohlcv_unit
    if family == "session_calendar_maintenance":
        return materialize_session_calendar_maintenance_unit
    if family == "vwap_session_auction":
        return materialize_vwap_session_auction_unit
    if family == "regime_volatility_compression":
        return materialize_regime_volatility_compression_unit
    if family == "liquidity_sweep_pa_structure":
        return materialize_liquidity_sweep_pa_structure_unit
    if family == "volume_activity":
        return materialize_volume_activity_unit
    if family == "bbo_tradability_top_book":
        return materialize_bbo_tradability_top_book_unit
    if family == "cross_market_alignment":
        return materialize_cross_market_alignment_unit
    raise ScaleoutError(f"unsupported scaleout family: {family}")


def render_scaleout_summary_markdown(summary: ScaleoutRunSummary) -> str:
    """Render a compact value-free Markdown summary."""

    states: dict[str, int] = {}
    for record in summary.records:
        states[record.unit.acceptance_state] = states.get(record.unit.acceptance_state, 0) + 1
    blocked_2018_schema = "bbo_1m" if summary.family == "bbo_tradability_top_book" else "ohlcv_1m"
    lines = [
        f"# {summary.family} Scaleout Summary",
        "",
        "Value-free scaleout summary. It contains no raw rows, canonical values,",
        "feature values, label values, provider responses, SQLite content, or Parquet payloads.",
        "",
        f"- Campaign: `{summary.campaign_id}`",
        f"- Phase: `{summary.phase_id}`",
        f"- Engine: `{summary.engine}`",
        f"- Rollout: `{summary.rollout}`",
        f"- Dry run: `{'yes' if summary.dry_run else 'no'}`",
        f"- Targeting active: `{'yes' if summary.target.active else 'no'}`",
        f"- Accepted unit count: `{summary.accepted_unit_count}`",
        f"- Bounded-real year: `{summary.bounded_year}`",
        f"- Bounded-real unit count: `{summary.bounded_unit_count}`",
        f"- Planned: `{summary.planned_count}`",
        f"- Completed: `{summary.completed_count}`",
        f"- Skipped: `{summary.skipped_count}`",
        f"- Failed: `{summary.failed_count}`",
        f"- Requested workers: `{summary.worker_plan.requested_workers}`",
        f"- Effective workers: `{summary.worker_plan.effective_workers}`",
        f"- Threads per worker: `{summary.worker_plan.threads_per_worker}`",
    ]
    if summary.worker_plan.reductions:
        lines.append(
            "- Worker reductions: `"
            + "; ".join(summary.worker_plan.reductions)
            + "`"
        )
    if summary.dry_run_estimate is not None:
        estimate = summary.dry_run_estimate
        lines.extend(
            [
                f"- Estimated rows per unit: `{estimate.estimated_rows_per_unit}`",
                f"- Estimated total rows: `{estimate.estimated_total_rows}`",
                f"- Estimated seconds per unit: `{estimate.estimated_seconds_per_unit}`",
                f"- Estimated total seconds: `{estimate.estimated_total_seconds}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Target",
            "",
            f"- Family: `{summary.target.family or summary.family}`",
            f"- Feature ids: `{', '.join(summary.target.feature_ids) or 'config default'}`",
            f"- Feature groups: `{', '.join(summary.target.feature_groups) or 'none'}`",
            f"- Label ids: `{', '.join(summary.target.label_ids) or 'none'}`",
            f"- Label groups: `{', '.join(summary.target.label_groups) or 'none'}`",
            f"- Symbols: `{', '.join(summary.target.symbols) or 'config default'}`",
            f"- Years: `{', '.join(str(year) for year in summary.target.years) or 'config default'}`",
            "- DatasetVersion ids: "
            f"`{', '.join(summary.target.dataset_version_ids) or 'accepted grid default'}`",
            "",
            "## Acceptance States",
            "",
            "| State | Unit count |",
            "| --- | ---: |",
        ]
    )
    for state in sorted(states):
        lines.append(f"| `{state}` | {states[state]} |")
    lines.extend(
        [
            "",
            "## Window Policy",
            "",
            "- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.",
            f"- Dataset-level fallback is used for 2018: the blocked 2018 `{blocked_2018_schema}`",
            "  DatasetVersion is excluded rather than fabricating per-symbol acceptance.",
            "- 2019 warning metadata and 2026 partial-year warning metadata are preserved",
            "  through the accepted/warned DatasetVersion state.",
            "- Multi-input units require every configured input schema/year to carry an",
            "  accepted or accepted-with-warnings DatasetVersion before execution.",
            "",
            "## Point-In-Time Guard",
            "",
            "- Feature values are emitted at the current source row `available_ts`;",
            "  label values carry `label_available_ts` at or after the forward terminal.",
            "- Rolling, expanding, prior-boundary, and derived-state inputs may use only",
            "  source rows whose `available_ts` is less than or equal to the output",
            "  `available_ts`.",
            "- Accepted DatasetVersion gates fail closed before canonical rows are",
            "  loaded or values are written.",
        ]
    )
    if summary.family == "vwap_session_auction":
        lines.extend(
            [
                "",
                "## Running-Vs-Final VWAP Discipline",
                "",
                "- Running VWAP and distance-to-VWAP are computed as expanding",
                "  point-in-time state keyed to each row `available_ts`.",
                "- Anchored ETH VWAP starts from the ETH anchor and carries forward only",
                "  rows already available at the output `available_ts`.",
                "- Final-session VWAP, full-session value area, and closing-auction",
                "  aggregates are not bound into intraday feature values.",
                "- Opening and overnight ranges update or freeze only after the source",
                "  rows needed for that point-in-time range are available.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "regime_volatility_compression":
        lines.extend(
            [
                "",
                "## Regime Primitive Bindings",
                "",
                "- `trendiness` binds to the existing `base_ohlcv_trendiness` primitive.",
                "- `atr_volatility_regime` binds to the existing `base_ohlcv_atr` primitive.",
                "- `range_compression` binds to the existing",
                "  `liquidity_structure_range_contraction` primitive.",
                "- `range_expansion` binds to the existing `base_ohlcv_rolling_range` primitive.",
                "- `momentum_reversion_state` binds to the existing `base_ohlcv_returns`",
                "  primitive.",
                "- All bindings use causal windows and emit values at the current row",
                "  `available_ts`; no final-session state or future labels are used.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "liquidity_sweep_pa_structure":
        lines.extend(
            [
                "",
                "## Liquidity / PA Primitive Bindings",
                "",
                "- `prior_high_low_sweep` binds to prior-boundary distance plus",
                "  sweep-high and sweep-low flags.",
                "- `close_back_inside` and `failed_breakout` bind to failed-high and",
                "  failed-low breakout flags.",
                "- `wick_rejection` binds to close-location and wick-rejection scores.",
                "- `displacement` is represented by the existing causal prior-boundary",
                "  distance and close-location primitives; no new displacement feature",
                "  is introduced.",
                "- `compression_breakout` is represented by existing range-contraction",
                "  plus sweep flags; no new compression-breakout feature is introduced.",
                "- All bindings are deterministic OHLCV-derived primitives emitted at",
                "  the current row `available_ts`; subjective/discretionary PA encodings",
                "  are forbidden.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "volume_activity":
        lines.extend(
            [
                "",
                "## Volume / Activity Primitive Bindings",
                "",
                "- `participation` is represented by existing rolling-volume and",
                "  volume-zscore primitives; no new participation formula is introduced.",
                "- `time_of_day_relative_volume` binds to existing volume-zscore plus",
                "  session-minute context.",
                "- `volume_regime` binds to existing rolling-volume and volume-zscore",
                "  primitives.",
                "- `activity_bursts` binds to existing volume-zscore plus rolling-range",
                "  activity context.",
                "- `effort_result_proxies` binds to existing rolling-volume, range-position,",
                "  trendiness, close-location, and wick-rejection primitives.",
                "- All bindings are deterministic OHLCV-derived primitives emitted at",
                "  the current row `available_ts`; no volume feature zoo is introduced.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "bbo_tradability_top_book":
        lines.extend(
            [
                "",
                "## BBO Proxy Guardrails",
                "",
                "- BBO-1m is treated strictly as a time-sampled and forward-filled",
                "  tradability proxy, not execution truth.",
                "- Passive-fill, queue-priority, market-impact, intra-minute path, and",
                "  execution-quality claims are forbidden.",
                "- Canonical BBO `available_ts` is preserved; no feature is emitted",
                "  before the source quote row is available.",
                "- Missing, quarantined, wide-spread, and low-depth conditions are",
                "  surfaced as flags or value gaps; they are not silently imputed.",
                "",
                "## BBO Top-Book Bindings",
                "",
                "- `mid`, `spread`, `spread_ticks`, and `spread_zscore` bind to existing",
                "  BBO spread primitives.",
                "- `top_book_depth` and `top_book_imbalance` bind to existing top-book",
                "  depth/imbalance primitives.",
                "- `missing_bbo_flag`, `bad_quote_flag`, `wide_spread_flag`, and",
                "  `low_depth_flag` bind to existing quote-quality flag primitives.",
                "- `microprice_proxy` binds to the existing BBO `microprice` primitive",
                "  and remains a proxy feature, not a fill or execution model.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "cross_market_alignment":
        lines.extend(
            [
                "",
                "## Cross-Market Alignment Guardrails",
                "",
                "- Cross-market materialization uses exact event-timestamp intersection",
                "  across ES, NQ, and RTY.",
                "- Output `available_ts` is the latest contributing per-instrument",
                "  availability timestamp for the same event timestamp.",
                "- Cross-instrument forward-fill and missing-instrument imputation are",
                "  forbidden; missing instruments or no-trade rows are surfaced as",
                "  gaps or excluded intersections.",
                "- The config labels bind to existing governed Cross-Market primitives;",
                "  no new cross-market feature formulas are introduced in this phase.",
                "",
                "## Cross-Market Primitive Bindings",
                "",
                "- `aligned_returns` binds to `synchronized_returns`.",
                "- `beta_residual` binds to NQ/ES and RTY/ES rolling beta residuals.",
                "- `basket_residual` binds to NQ-minus-ES and RTY-minus-ES return spreads.",
                "- `relative_strength_rank` and `catch_up_rotation` bind to existing",
                "  risk-on/risk-off rotation proxies.",
                "- `divergence_agreement` binds to confirmation and divergence flags.",
                "- `lead_lag` binds to existing NQ/ES and RTY/ES rolling correlations as",
                "  governed pair-state proxies; it does not introduce a new lead-lag",
                "  formula.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row feature values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `feature_version_id` through `FeatureStore.register_materialized_feature`.",
            ]
        )
    if summary.family == "fixed_horizon":
        lines.extend(
            [
                "",
                "## Fixed-Horizon Label Guards",
                "",
                "- Label compute uses the reference label engine via `run_seed_label_pack`.",
                "- Forward terminals are keyed by `series_id+contract_id+event_ts`.",
                "- Roll-splice windows use the wired roll guard with policy `drop`.",
                "- Daily maintenance-break crossings use policy `drop`.",
                "- Label materialization is Parquet-first; JSONL is not used for",
                "  research-scale values in this phase.",
                "",
                "## Materialized Value Evidence",
                "",
                "- This summary is value-free and does not include per-row label values.",
                "- In dry-run mode, Parquet paths, value content hashes, registry row",
                "  fields, materialized row counts, checkpoint markers, and observed",
                "  `label_available_ts` min/max are unavailable.",
                "- When `--execute` succeeds, the driver verifies Parquet-backed registry",
                "  rows for `value_store_format`, `parquet_path`, `value_content_hash`,",
                "  `value_schema_version`, `dataset_version_id`, and",
                "  `label_version_id` through `LabelRegistry.register_materialized_label`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Unit Outcomes",
            "",
            "| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |",
            "| --- | ---: | --- | --- | --- | --- | ---: |",
        ]
    )
    for record in summary.records:
        input_dataset_ids = ", ".join(
            f"{dataset.schema_id}:{dataset.dataset_version_id}"
            for dataset in _unit_input_datasets(record.unit)
        )
        lines.append(
            "| `{stage}` | {year} | `{symbol}` | `{dataset}` | `{inputs}` | `{status}` | {rows} |".format(
                stage=record.stage,
                year=record.unit.year,
                symbol=record.unit.symbol,
                dataset=record.unit.dataset_version_id,
                inputs=input_dataset_ids,
                status=record.status,
                rows=record.row_count,
            )
        )
    if summary.family in {
        "vwap_session_auction",
        "regime_volatility_compression",
        "liquidity_sweep_pa_structure",
        "volume_activity",
        "bbo_tradability_top_book",
        "cross_market_alignment",
    }:
        lines.extend(
            [
                "",
                "## Bounded-Real FeatureVersion Preview",
                "",
                "The bounded-real dry-run preview is write-free. It records deterministic",
                "FeatureVersion ids that execution is expected to register for the same",
                "unit identities; content hashes are unavailable until Parquet values are",
                "written.",
                "",
                "| Symbol | FeatureVersion ids |",
                "| --- | --- |",
            ]
        )
        for record in summary.records:
            if record.unit.year != summary.bounded_year:
                continue
            version_ids = ", ".join(f"`{version_id}`" for version_id in record.feature_version_ids)
            lines.append(f"| `{record.unit.symbol}` | {version_ids} |")
    if summary.family == "fixed_horizon":
        lines.extend(
            [
                "",
                "## Bounded-Real LabelVersion Preview",
                "",
                "The bounded-real dry-run preview is write-free. It records deterministic",
                "LabelVersion ids that execution is expected to register for the same",
                "unit identities; content hashes are unavailable until Parquet values are",
                "written.",
                "",
                "| Symbol | Label | LabelVersion ids |",
                "| --- | --- | --- |",
            ]
        )
        for record in summary.records:
            if record.unit.year != summary.bounded_year:
                continue
            version_ids = ", ".join(f"`{version_id}`" for version_id in record.label_version_ids)
            labels = ", ".join(f"`{name}`" for name in record.unit.feature_names)
            lines.append(f"| `{record.unit.symbol}` | {labels} | {version_ids} |")
    lines.append("")
    return "\n".join(lines)


class _ScaleoutLedger:
    def __init__(self, alpha_data_root: Path, config: ScaleoutConfig) -> None:
        self.alpha_data_root = alpha_data_root
        self.config = config
        self.completed_manifest_path = alpha_data_root / config.completed_manifest

    def latest_completed(self, unit: ScaleoutUnit) -> ScaleoutUnitRecord | None:
        latest: ScaleoutUnitRecord | None = None
        for record in self._read_records():
            if record.unit.unit_id == unit.unit_id and record.status == "completed":
                latest = record
        if latest is None:
            return None
        if not _completed_record_is_valid(latest):
            return ScaleoutUnitRecord(
                unit=unit,
                status="failed",
                stage="resume_check",
                message="completed ledger record is missing parquet/hash/row-count evidence",
            )
        parquet_path = Path(latest.parquet_path or "")
        if not parquet_path.exists():
            return ScaleoutUnitRecord(
                unit=unit,
                status="failed",
                stage="resume_check",
                parquet_path=latest.parquet_path,
                content_hash=latest.content_hash,
                row_count=latest.row_count,
                feature_version_ids=latest.feature_version_ids,
                message="completed ledger record points to a missing Parquet file",
            )
        return latest

    def append(self, record: ScaleoutUnitRecord) -> None:
        self.completed_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.completed_manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_serialize(record.to_dict()) + "\n")
        if record.status == "completed":
            marker_path = self._marker_path(record.unit)
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(
                canonical_serialize(record.to_dict()) + "\n",
                encoding="utf-8",
            )

    def _read_records(self) -> tuple[ScaleoutUnitRecord, ...]:
        if not self.completed_manifest_path.exists():
            return ()
        records: list[ScaleoutUnitRecord] = []
        for line in self.completed_manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                records.append(_record_from_payload(payload))
            except (json.JSONDecodeError, ScaleoutError):
                continue
        return tuple(records)

    def _marker_path(self, unit: ScaleoutUnit) -> Path:
        relative = self.config.completion_marker_template.format(unit_id=unit.unit_id)
        return self.alpha_data_root / relative


def _registry_completed_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    *,
    engine: str,
) -> ScaleoutUnitRecord | None:
    """Detect a unit already fully materialized in the live feature registry.

    The scaleout feature identity (``feature_version_id``) is content-addressed and
    registry-state independent, so the write-free identity preview yields exactly the
    ids a successful ``--execute`` would register. When every previewed id already
    resolves to a registered FeatureVersion whose Parquet file exists, the unit is
    already materialized: re-running it would (correctly) trip the FLF-P05
    duplicate-exposure guard at registration time. Treating it as completed makes the
    driver idempotent across runs even when the local checkpoint ledger was lost,
    without bypassing the guard or hand-writing any registry records. A partially
    registered unit (some ids missing or Parquet absent) returns ``None`` so the
    executor runs normally and the guard remains the authority on duplicates.
    """

    if _is_label_scaleout_config(config):
        return _registry_completed_label_unit(config, unit, alpha_data_root, engine=engine)
    try:
        feature_version_ids = _preview_feature_version_ids(config, unit)
    except (ValueError, ScaleoutError, KeyError, OSError):
        return None
    if not feature_version_ids:
        return None
    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    parquet_paths: list[str] = []
    content_hashes: list[str] = []
    total_rows = 0
    for feature_version_id in feature_version_ids:
        try:
            record = store.resolve_feature(feature_version_id)
        except Exception:  # noqa: BLE001 - any resolve failure => not completed
            return None
        if record is None:
            return None
        if not _registry_record_matches_engine(record, engine):
            return None
        parquet_path = getattr(record, "parquet_path", None)
        if not parquet_path or not Path(parquet_path).exists():
            return None
        parquet_paths.append(str(parquet_path))
        content_hashes.append(str(getattr(record, "value_content_hash", "") or ""))
        total_rows += int(getattr(record, "value_record_count", 0) or 0)
    return ScaleoutUnitRecord(
        unit=unit,
        status="completed",
        stage="registry_resume",
        parquet_path=parquet_paths[0],
        content_hash=content_hashes[0],
        row_count=total_rows,
        feature_version_ids=tuple(feature_version_ids),
    )


def _completed_record_has_registry_truth(
    config: ScaleoutConfig,
    record: ScaleoutUnitRecord,
    alpha_data_root: Path,
    *,
    engine: str,
) -> bool:
    if _is_label_scaleout_config(config):
        try:
            current_label_version_ids = _preview_label_version_ids(config, record.unit)
        except (ValueError, ScaleoutError, KeyError, OSError):
            return False
        if record.label_version_ids != current_label_version_ids:
            return False
        return _completed_label_record_has_registry_truth(record, alpha_data_root, engine=engine)
    if record.status != "completed" or not record.feature_version_ids:
        return False
    try:
        store = FeatureStore.from_alpha_data_root(alpha_data_root)
    except Exception:  # noqa: BLE001 - registry truth unavailable => not completed
        return False
    for feature_version_id in record.feature_version_ids:
        try:
            registry_record = store.resolve_feature(feature_version_id)
        except Exception:  # noqa: BLE001 - registry truth unavailable => not completed
            return False
        if registry_record is None:
            return False
        if not _registry_record_matches_engine(registry_record, engine):
            return False
        parquet_path = getattr(registry_record, "parquet_path", None)
        if not parquet_path or not Path(parquet_path).exists():
            return False
    return True


def _registry_completed_label_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    *,
    engine: str,
) -> ScaleoutUnitRecord | None:
    try:
        label_version_ids = _preview_label_version_ids(config, unit)
    except (ValueError, ScaleoutError, KeyError, OSError):
        return None
    if not label_version_ids:
        return None
    try:
        from alpha_system.labels.registry import LabelRegistry

        registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    except Exception:  # noqa: BLE001 - registry truth unavailable => not completed
        return None
    parquet_paths: list[str] = []
    content_hashes: list[str] = []
    total_rows = 0
    for label_version_id in label_version_ids:
        try:
            record = registry.resolve_label(label_version_id)
        except Exception:  # noqa: BLE001 - any resolve failure => not completed
            return None
        if record is None:
            return None
        if not _label_registry_record_matches_engine(record, engine):
            return None
        if record.dataset_version_id != unit.dataset_version_id:
            return None
        if record.partition_id != unit.partition_id:
            return None
        if record.value_store_format != ValueStoreFormat.PARQUET.value:
            return None
        parquet_path = getattr(record, "parquet_path", None)
        if not parquet_path or not Path(parquet_path).exists():
            return None
        parquet_paths.append(str(parquet_path))
        content_hashes.append(str(getattr(record, "value_content_hash", "") or ""))
        total_rows += int(getattr(record, "value_record_count", 0) or 0)
    return ScaleoutUnitRecord(
        unit=unit,
        status="completed",
        stage="registry_resume",
        parquet_path=parquet_paths[0],
        content_hash=content_hashes[0],
        row_count=total_rows,
        label_version_ids=tuple(label_version_ids),
    )


def _completed_label_record_has_registry_truth(
    record: ScaleoutUnitRecord,
    alpha_data_root: Path,
    *,
    engine: str,
) -> bool:
    if record.status != "completed" or not record.label_version_ids:
        return False
    try:
        from alpha_system.labels.registry import LabelRegistry

        registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    except Exception:  # noqa: BLE001 - registry truth unavailable => not completed
        return False
    for label_version_id in record.label_version_ids:
        try:
            registry_record = registry.resolve_label(label_version_id)
        except Exception:  # noqa: BLE001 - registry truth unavailable => not completed
            return False
        if registry_record is None:
            return False
        if not _label_registry_record_matches_engine(registry_record, engine):
            return False
        if registry_record.dataset_version_id != record.unit.dataset_version_id:
            return False
        if registry_record.partition_id != record.unit.partition_id:
            return False
        if registry_record.value_store_format != ValueStoreFormat.PARQUET.value:
            return False
        parquet_path = getattr(registry_record, "parquet_path", None)
        if not parquet_path or not Path(parquet_path).exists():
            return False
    return True


def _registry_record_matches_engine(record: Any, engine: str) -> bool:
    expected = _producer_engine_id_for_engine(engine)
    return getattr(record, "producer_engine_id", None) == expected


def _label_registry_record_matches_engine(record: Any, engine: str) -> bool:
    expected = _label_producer_engine_id_for_engine(engine)
    return getattr(record, "producer_engine_id", None) == expected


def _producer_engine_id_for_engine(engine: str) -> str:
    engine_token = _normalize_engine(engine)
    if engine_token == SCALEOUT_ENGINE_V1:
        from alpha_system.features.fast import FAST_PRODUCER_ENGINE_ID

        return FAST_PRODUCER_ENGINE_ID
    from alpha_system.features.registry import REFERENCE_FEATURE_PRODUCER_ENGINE_ID

    return REFERENCE_FEATURE_PRODUCER_ENGINE_ID


def _label_producer_engine_id_for_engine(engine: str) -> str:
    engine_token = _normalize_engine(engine)
    if engine_token == SCALEOUT_ENGINE_V1:
        from alpha_system.labels.fast import FAST_LABEL_PRODUCER_ENGINE_ID

        return FAST_LABEL_PRODUCER_ENGINE_ID
    return "alpha_system.labels.reference_engine.v1"


def _execute_stage(
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    *,
    stage: str,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    ledger: _ScaleoutLedger,
    executor: UnitExecutor,
    engine: str,
    requested_workers: int,
    parallel_worker_compute: bool,
    force_recompute: bool,
    log: Callable[[str], None] | None,
) -> tuple[ScaleoutUnitRecord, ...]:
    records_by_unit: dict[str, ScaleoutUnitRecord] = {}
    runnable_units: list[ScaleoutUnit] = []
    for unit in units:
        completed = None
        if not force_recompute:
            completed = ledger.latest_completed(unit)
            if (
                completed is not None
                and completed.status == "completed"
                and not _completed_record_has_registry_truth(
                    config,
                    completed,
                    alpha_data_root,
                    engine=engine,
                )
            ):
                completed = None
            if completed is None:
                registry_completed = _registry_completed_unit(
                    config,
                    unit,
                    alpha_data_root,
                    engine=engine,
                )
                if registry_completed is not None:
                    # Persist a checkpoint marker so subsequent runs short-circuit via
                    # the ledger without re-querying the registry, then fall through to
                    # the shared skip path below.
                    ledger.append(registry_completed)
                    completed = registry_completed
        if completed is not None:
            status = "skipped" if completed.status == "completed" else "failed"
            record = ScaleoutUnitRecord(
                unit=unit,
                status=status,
                stage=stage,
                parquet_path=completed.parquet_path,
                content_hash=completed.content_hash,
                row_count=completed.row_count,
                feature_version_ids=completed.feature_version_ids,
                label_version_ids=completed.label_version_ids,
                message=(
                    "completed unit skipped from checkpoint + registry truth"
                    if status == "skipped"
                    else completed.message
                ),
            )
            records_by_unit[unit.unit_id] = record
            continue
        try:
            _require_persisted_acceptance_lock(unit, dataset_registry_path)
        except (
            DataFoundationValidationError,
            OSError,
            ValueError,
        ) as exc:
            record = ScaleoutUnitRecord(
                unit=unit,
                status="failed",
                stage=stage,
                message=str(exc),
            )
            ledger.append(record)
            records_by_unit[unit.unit_id] = record
            continue
        runnable_units.append(unit)

    if runnable_units:
        worker_plan = _resolve_worker_plan(
            requested_workers,
            unit_count=len(runnable_units),
            parallel_allowed=parallel_worker_compute,
        )
        _log_worker_reductions(worker_plan, log)
        if worker_plan.parallel_enabled:
            if _is_label_scaleout_config(config) and engine == SCALEOUT_ENGINE_REFERENCE:
                computed = _compute_reference_label_stage_outputs_in_workers(
                    config,
                    tuple(runnable_units),
                    alpha_data_root=alpha_data_root,
                    dataset_registry_path=dataset_registry_path,
                    canonical_root=canonical_root,
                    worker_plan=worker_plan,
                    force_recompute=force_recompute,
                )
            else:
                computed = _compute_v1_stage_outputs_in_workers(
                    config,
                    tuple(runnable_units),
                    alpha_data_root=alpha_data_root,
                    dataset_registry_path=dataset_registry_path,
                    canonical_root=canonical_root,
                    worker_plan=worker_plan,
                    force_recompute=force_recompute,
                )
            for unit in runnable_units:
                outcome = computed[unit.unit_id]
                if isinstance(outcome, BaseException):
                    record = ScaleoutUnitRecord(
                        unit=unit,
                        status="failed",
                        stage=stage,
                        message=str(outcome),
                    )
                    ledger.append(record)
                    records_by_unit[unit.unit_id] = record
                    continue
                start_wait = perf_counter()
                try:
                    if _is_label_scaleout_config(config) and engine == SCALEOUT_ENGINE_V1:
                        evidence = _register_fast_label_worker_output(
                            config,
                            unit,
                            alpha_data_root=alpha_data_root,
                            output=outcome,
                        )
                    elif _is_label_scaleout_config(config):
                        evidence = _register_reference_label_worker_output(
                            config,
                            unit,
                            alpha_data_root=alpha_data_root,
                            output=outcome,
                        )
                    else:
                        evidence = _register_v1_worker_output(
                            config,
                            unit,
                            alpha_data_root=alpha_data_root,
                            output=outcome,
                            rebuild_request_against_live_registry=True,
                        )
                    queue_wait = perf_counter() - start_wait
                    record = ScaleoutUnitRecord(
                        unit=unit,
                        status="completed",
                        stage=stage,
                        parquet_path=evidence.parquet_path,
                        content_hash=evidence.content_hash,
                        row_count=evidence.row_count,
                        feature_version_ids=evidence.feature_version_ids,
                        label_version_ids=evidence.label_version_ids,
                        message=(
                            "worker compute registered by serial writer; "
                            f"registry_queue_wait_seconds={queue_wait:.6f}"
                        ),
                    )
                except (OSError, ValueError) as exc:
                    record = ScaleoutUnitRecord(
                        unit=unit,
                        status="failed",
                        stage=stage,
                        message=str(exc),
                    )
                ledger.append(record)
                records_by_unit[unit.unit_id] = record
        else:
            for unit in runnable_units:
                try:
                    if (
                        force_recompute
                        and engine == SCALEOUT_ENGINE_V1
                        and executor is materialize_v1_feature_unit
                    ):
                        evidence = materialize_v1_feature_unit_force_recompute(
                            config,
                            unit,
                            alpha_data_root,
                            dataset_registry_path,
                            canonical_root,
                        )
                    else:
                        evidence = executor(
                            config,
                            unit,
                            alpha_data_root,
                            dataset_registry_path,
                            canonical_root,
                        )
                    record = ScaleoutUnitRecord(
                        unit=unit,
                        status="completed",
                        stage=stage,
                        parquet_path=evidence.parquet_path,
                        content_hash=evidence.content_hash,
                        row_count=evidence.row_count,
                        feature_version_ids=evidence.feature_version_ids,
                        label_version_ids=evidence.label_version_ids,
                    )
                except (
                    DataFoundationValidationError,
                    OSError,
                    ValueError,
                ) as exc:
                    record = ScaleoutUnitRecord(
                        unit=unit,
                        status="failed",
                        stage=stage,
                        message=str(exc),
                    )
                ledger.append(record)
                records_by_unit[unit.unit_id] = record
    return tuple(
        records_by_unit[unit.unit_id]
        for unit in units
        if unit.unit_id in records_by_unit
    )


def _compute_v1_stage_outputs_in_workers(
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    *,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    worker_plan: ScaleoutWorkerPlan,
    force_recompute: bool,
) -> dict[str, Any | BaseException]:
    if _is_label_scaleout_config(config):
        return _compute_fast_label_stage_outputs_in_workers(
            config,
            units,
            alpha_data_root=alpha_data_root,
            dataset_registry_path=dataset_registry_path,
            canonical_root=canonical_root,
            worker_plan=worker_plan,
            force_recompute=force_recompute,
        )
    outputs: dict[str, Any | BaseException] = {}
    jobs: list[_V1PreparedWorkerJob] = []
    for unit in units:
        try:
            if not force_recompute:
                resumed = _v1_worker_output_from_manifest(
                    config,
                    unit,
                    alpha_data_root=alpha_data_root,
                )
                if resumed is not None:
                    outputs[unit.unit_id] = resumed
                    continue
            jobs.append(
                _prepare_v1_worker_job(
                    config,
                    unit,
                    alpha_data_root=alpha_data_root,
                    force_recompute=force_recompute,
                )
            )
        except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
            outputs[unit.unit_id] = exc
    if not jobs:
        return outputs
    # Use the "spawn" start method, NOT the Linux default "fork". The parent
    # process has already imported polars and run canonical loads/job prep, which
    # initializes polars' global Rayon thread pool. Forking after a thread pool
    # exists leaves the child with an inconsistent copy of those threads/locks, so
    # the child deadlocks on its first polars call -- the benchmark stalled even at
    # workers=2 for exactly this reason. spawn starts each worker as a fresh
    # interpreter that re-imports polars cleanly; because driver.py imports polars
    # lazily, _pin_native_threads() (called first in the entrypoint) also takes
    # effect before that fresh import, so per-worker thread caps actually apply.
    spawn_context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=worker_plan.effective_workers, mp_context=spawn_context
    ) as pool:
        futures = {
            pool.submit(
                _v1_worker_compute_entrypoint,
                config,
                job,
                alpha_data_root,
                dataset_registry_path,
                canonical_root,
                worker_plan.threads_per_worker,
            ): job.unit
            for job in jobs
        }
        for future in as_completed(futures):
            unit = futures[future]
            try:
                outputs[unit.unit_id] = future.result()
            except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
                outputs[unit.unit_id] = exc
    return outputs


def _compute_reference_label_stage_outputs_in_workers(
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    *,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    worker_plan: ScaleoutWorkerPlan,
    force_recompute: bool,
) -> dict[str, Any | BaseException]:
    outputs: dict[str, Any | BaseException] = {}
    jobs: list[ScaleoutUnit] = []
    for unit in units:
        try:
            if not force_recompute:
                resumed = _reference_label_worker_output_from_manifest(
                    config,
                    unit,
                    alpha_data_root=alpha_data_root,
                )
                if resumed is not None:
                    outputs[unit.unit_id] = resumed
                    continue
            jobs.append(unit)
        except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
            outputs[unit.unit_id] = exc
    if not jobs:
        return outputs
    spawn_context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=worker_plan.effective_workers,
        mp_context=spawn_context,
    ) as pool:
        futures = {
            pool.submit(
                REFERENCE_LABEL_WORKER_ENTRYPOINT,
                config,
                unit,
                alpha_data_root,
                dataset_registry_path,
                canonical_root,
            ): unit
            for unit in jobs
        }
        for future in as_completed(futures):
            unit = futures[future]
            try:
                outputs[unit.unit_id] = future.result()
            except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
                outputs[unit.unit_id] = exc
    return outputs


def _compute_fast_label_stage_outputs_in_workers(
    config: ScaleoutConfig,
    units: tuple[ScaleoutUnit, ...],
    *,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    worker_plan: ScaleoutWorkerPlan,
    force_recompute: bool,
) -> dict[str, Any | BaseException]:
    outputs: dict[str, Any | BaseException] = {}
    jobs: list[ScaleoutUnit] = []
    for unit in units:
        try:
            if not force_recompute:
                resumed = _fast_label_worker_output_from_manifest(
                    config,
                    unit,
                    alpha_data_root=alpha_data_root,
                )
                if resumed is not None:
                    outputs[unit.unit_id] = resumed
                    continue
            jobs.append(unit)
        except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
            outputs[unit.unit_id] = exc
    if not jobs:
        return outputs
    spawn_context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=worker_plan.effective_workers,
        mp_context=spawn_context,
    ) as pool:
        futures = {
            pool.submit(
                _fast_label_worker_compute_entrypoint,
                config,
                unit,
                alpha_data_root,
                dataset_registry_path,
                canonical_root,
                worker_plan.threads_per_worker,
            ): unit
            for unit in jobs
        }
        for future in as_completed(futures):
            unit = futures[future]
            try:
                outputs[unit.unit_id] = future.result()
            except BaseException as exc:  # noqa: BLE001 - recorded per unit for retry
                outputs[unit.unit_id] = exc
    return outputs


def _reference_label_worker_output_from_manifest(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
) -> _ReferenceLabelWorkerUnitOutput | None:
    """Rebuild a reference-label worker output from a completed local manifest."""

    from alpha_system.core.value_store import ValueStoreHandle, parquet_is_current
    from alpha_system.labels.engine import (
        LABEL_MATERIALIZATION_SCHEMA,
        LabelMaterializationResult,
        _materialization_output_path_for_format,
    )

    manifest_path = _reference_label_worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    if not manifest_path.exists():
        return None
    payload = _load_json_mapping(manifest_path, "reference label worker manifest")
    if payload.get("schema") != REFERENCE_LABEL_WORKER_MANIFEST_SCHEMA:
        raise ScaleoutError(f"reference label worker manifest schema is invalid: {manifest_path}")
    if payload.get("producer_engine_id") != REFERENCE_LABEL_PRODUCER_ENGINE_ID:
        raise ScaleoutError(f"reference label worker manifest producer is invalid: {manifest_path}")
    if payload.get("value_schema_version") != LABEL_MATERIALIZATION_SCHEMA:
        raise ScaleoutError(
            f"reference label worker manifest value schema is invalid: {manifest_path}"
        )
    _require_worker_manifest_unit_key(payload.get("unit_key"), unit, manifest_path)
    parquet_path = Path(_require_text(payload.get("parquet_path"), "parquet_path"))
    if not parquet_path.exists():
        raise ScaleoutError(
            f"reference label worker manifest Parquet is missing: {parquet_path}"
        )
    content_hash = _require_text(payload.get("content_hash"), "content_hash")
    if not parquet_is_current(parquet_path, content_hash):
        raise ScaleoutError(
            f"reference label worker manifest Parquet hash is stale: {parquet_path}"
        )
    label_version_ids = tuple(
        _require_text(value, "label_version_id")
        for value in _sequence(payload.get("label_version_ids"), "label_version_ids")
    )
    definitions = _reference_label_definitions_for_unit(config, unit)
    if label_version_ids != _reference_label_version_ids(definitions):
        raise ScaleoutError("reference label worker manifest label_version_id order changed")
    plan = _reference_label_plan_from_manifest(
        config,
        unit,
        alpha_data_root=alpha_data_root,
        definitions=definitions,
    )
    records = _label_value_records_from_parquet(parquet_path, plan)
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=len(records),
        content_hash=content_hash,
        schema_version=LABEL_MATERIALIZATION_SCHEMA,
        dataset_version_id=unit.dataset_version_id,
        set_id=unit.feature_set_id,
        partition_id=unit.partition_id,
        min_event_ts=min(record.event_ts.isoformat() for record in records),
        max_event_ts=max(record.event_ts.isoformat() for record in records),
        min_available_ts=min(record.label_available_ts.isoformat() for record in records),
        max_available_ts=max(record.label_available_ts.isoformat() for record in records),
    )
    manifest = _ReferenceLabelWorkerManifest(
        unit_key=_worker_unit_key(unit),
        parquet_path=parquet_path.as_posix(),
        content_hash=content_hash,
        row_count=int(payload.get("row_count") or len(records)),
        label_version_ids=label_version_ids,
        producer_engine_id=REFERENCE_LABEL_PRODUCER_ENGINE_ID,
        value_schema_version=LABEL_MATERIALIZATION_SCHEMA,
        manifest_path=manifest_path.as_posix(),
    )
    registry_metadata = {
        **_label_scaleout_metadata(config, unit),
        "worker_manifest_path": manifest_path.as_posix(),
    }
    return _ReferenceLabelWorkerUnitOutput(
        materialization_result=LabelMaterializationResult(
            plan=plan,
            records=records,
            dry_run=False,
            wrote_output=False,
            output_path=_materialization_output_path_for_format(plan, config.value_store_format),
            value_store_handle=handle,
        ),
        label_definitions=definitions,
        registry_metadata=registry_metadata,
        manifest=manifest,
    )


def _reference_label_plan_from_manifest(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    definitions: tuple[Any, ...],
) -> Any:
    from alpha_system.data.foundation.datasets import DatasetVersion
    from alpha_system.features.consumption import AcceptedDatasetVersion
    from alpha_system.labels.engine import build_label_materialization_plan

    dataset_version = DatasetVersion(
        dataset_version_id=unit.dataset_version_id,
        source="dsrc_manifest_resume",
        symbol_universe=(unit.symbol,),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=_datetime_from_iso(unit.window_start_ts),
        end_ts=_datetime_from_iso(unit.window_end_ts),
        contract_universe=(unit.symbol,),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash="0" * 64,
        code_hash="0" * 64,
        config_hash="0" * 64,
        quality_report_hash="0" * 64,
        created_at=_datetime_from_iso(unit.window_end_ts),
    )
    accepted = AcceptedDatasetVersion(
        registry_path="manifest_resume",
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=None,
        coverage_report=None,
    )
    return build_label_materialization_plan(
        definitions,
        accepted,
        partition_id=unit.partition_id,
        instrument_ids=(),
        alpha_data_root=alpha_data_root,
        governance_metadata=_label_scaleout_metadata(config, unit),
        output_namespace=config.value_namespace,
    )


def _fast_label_worker_output_from_manifest(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
) -> Any | None:
    """Rebuild a fast label worker output from a completed local manifest."""

    from alpha_system.core.value_store import ValueStoreHandle, parquet_is_current
    from alpha_system.labels.engine import LabelMaterializationResult
    from alpha_system.labels.fast import (
        FAST_LABEL_PRODUCER_ENGINE_ID,
        FAST_LABEL_VALUE_SCHEMA_VERSION,
        FAST_LABEL_WORKER_MANIFEST_SCHEMA,
        FastLabelWorkerManifest,
        FastLabelWorkerUnitOutput,
        label_worker_manifest_path,
    )

    manifest_path = label_worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    if not manifest_path.exists():
        return None
    payload = _load_json_mapping(manifest_path, "fast label worker manifest")
    if payload.get("schema") != FAST_LABEL_WORKER_MANIFEST_SCHEMA:
        raise ScaleoutError(f"fast label worker manifest schema is invalid: {manifest_path}")
    if payload.get("producer_engine_id") != FAST_LABEL_PRODUCER_ENGINE_ID:
        raise ScaleoutError(f"fast label worker manifest producer is invalid: {manifest_path}")
    if payload.get("value_schema_version") != FAST_LABEL_VALUE_SCHEMA_VERSION:
        raise ScaleoutError(f"fast label worker manifest value schema is invalid: {manifest_path}")
    _require_worker_manifest_unit_key(payload.get("unit_key"), unit, manifest_path)
    parquet_path = Path(_require_text(payload.get("parquet_path"), "parquet_path"))
    if not parquet_path.exists():
        raise ScaleoutError(f"fast label worker manifest Parquet is missing: {parquet_path}")
    content_hash = _require_text(payload.get("content_hash"), "content_hash")
    if not parquet_is_current(parquet_path, content_hash):
        raise ScaleoutError(f"fast label worker manifest Parquet hash is stale: {parquet_path}")
    label_version_ids = tuple(
        _require_text(value, "label_version_id")
        for value in _sequence(payload.get("label_version_ids"), "label_version_ids")
    )
    pack = _fast_label_pack_for_unit(config, unit)
    if label_version_ids != tuple(pack.label_version_ids):
        raise ScaleoutError("fast label worker manifest label_version_id order changed")
    plan = _fast_label_plan_from_manifest(config, unit, alpha_data_root=alpha_data_root, pack=pack)
    records = _label_value_records_from_parquet(parquet_path, plan)
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=len(records),
        content_hash=content_hash,
        schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
        dataset_version_id=unit.dataset_version_id,
        set_id=unit.feature_set_id,
        partition_id=unit.partition_id,
        min_event_ts=min(record.event_ts.isoformat() for record in records),
        max_event_ts=max(record.event_ts.isoformat() for record in records),
        min_available_ts=min(record.label_available_ts.isoformat() for record in records),
        max_available_ts=max(record.label_available_ts.isoformat() for record in records),
    )
    manifest = FastLabelWorkerManifest(
        unit_key=_worker_unit_key(unit),
        parquet_path=parquet_path.as_posix(),
        content_hash=content_hash,
        row_count=int(payload.get("row_count") or len(records)),
        label_version_ids=label_version_ids,
        producer_engine_id=FAST_LABEL_PRODUCER_ENGINE_ID,
        value_schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
        manifest_path=manifest_path.as_posix(),
    )
    registry_metadata = {
        **_fast_label_registry_metadata(config, unit),
        "worker_manifest_path": manifest_path.as_posix(),
    }
    return FastLabelWorkerUnitOutput(
        materialization_result=LabelMaterializationResult(
            plan=plan,
            records=records,
            dry_run=False,
            wrote_output=False,
            output_path=parquet_path,
            value_store_handle=handle,
            planned_input_rows=0,
            planned_label_count=len(pack.definitions),
            runtime_seconds=0.0,
        ),
        pack=pack,
        registry_metadata=registry_metadata,
        manifest=manifest,
    )


def _v1_worker_output_from_manifest(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
) -> Any | None:
    """Rebuild a V1 worker output from a completed local worker manifest."""

    from alpha_system.core.value_store import (
        ValueStoreHandle,
        parquet_is_current,
    )
    from alpha_system.features.contracts import FeatureSetSpec, FrozenJsonMapping
    from alpha_system.features.engine import (
        FeatureMaterializationPlan,
        FeatureMaterializationResult,
    )
    from alpha_system.features.engine.materialization import (
        _feature_version_ids,
        _plan_content_hash,
    )
    from alpha_system.features.fast import (
        FAST_PRODUCER_ENGINE_ID,
        FAST_VALUE_SCHEMA_VERSION,
        FAST_WORKER_MANIFEST_SCHEMA,
        FastWorkerManifest,
        FastWorkerUnitOutput,
        worker_manifest_path,
    )

    manifest_path = worker_manifest_path(
        alpha_data_root,
        checkpoint_root=config.checkpoint_root,
        unit_id=unit.unit_id,
    )
    if not manifest_path.exists():
        return None
    payload = _load_json_mapping(manifest_path, "V1 worker manifest")
    if payload.get("schema") != FAST_WORKER_MANIFEST_SCHEMA:
        raise ScaleoutError(f"V1 worker manifest schema is invalid: {manifest_path}")
    if payload.get("producer_engine_id") != FAST_PRODUCER_ENGINE_ID:
        raise ScaleoutError(f"V1 worker manifest is not a V1 producer output: {manifest_path}")
    if payload.get("value_schema_version") != FAST_VALUE_SCHEMA_VERSION:
        raise ScaleoutError(f"V1 worker manifest value schema is invalid: {manifest_path}")
    _require_worker_manifest_unit_key(payload.get("unit_key"), unit, manifest_path)
    parquet_path = Path(_require_text(payload.get("parquet_path"), "parquet_path"))
    if not parquet_path.exists():
        raise ScaleoutError(f"V1 worker manifest Parquet is missing: {parquet_path}")
    content_hash = _require_text(payload.get("content_hash"), "content_hash")
    if not parquet_is_current(parquet_path, content_hash):
        raise ScaleoutError(f"V1 worker manifest Parquet hash is stale: {parquet_path}")
    feature_version_ids = tuple(
        _require_text(value, "feature_version_id")
        for value in _sequence(payload.get("feature_version_ids"), "feature_version_ids")
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    feature_specs: list[Any] = []
    request_payloads: dict[str, Mapping[str, Any]] = {}
    registry_metadata = _v1_registry_metadata(config, unit)
    for expected_version_id in feature_version_ids:
        existing = store.resolve_feature(expected_version_id)
        if existing is not None:
            if not _registry_record_matches_engine(existing, SCALEOUT_ENGINE_V1):
                raise ScaleoutError(
                    "manifest-resume feature has non-V1 producer provenance: "
                    f"{expected_version_id}"
                )
            parquet = getattr(existing, "parquet_path", None)
            if not parquet or not Path(parquet).exists():
                raise ScaleoutError(
                    "manifest-resume feature is missing Parquet materialization: "
                    f"{expected_version_id}"
                )
            feature_specs.append(existing.feature_spec)
            continue

        fresh, _, fresh_declaration = _fresh_v1_declaration_for_version(
            config,
            unit,
            expected_version_id=expected_version_id,
            alpha_data_root=alpha_data_root,
        )
        feature_specs.append(fresh_declaration.feature_spec)
        request_payloads.update(fresh.feature_request_payloads)

    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(feature_specs),
        description=f"FCFP-P15 V1 {config.family} scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    if _feature_version_ids(feature_set) != feature_version_ids:
        raise ScaleoutError("manifest-resume feature_version_id order changed")
    governance_metadata = FrozenJsonMapping.from_mapping(
        registry_metadata,
        field_name="registry_metadata",
    )
    output_path = parquet_path.with_name("values.jsonl")
    idempotency_key = _plan_content_hash(
        feature_set,
        dataset_version_id=unit.dataset_version_id,
        partition_id=unit.partition_id,
        output_path=output_path,
        governance_metadata=governance_metadata,
    )
    plan = FeatureMaterializationPlan(
        feature_set=feature_set,
        dataset_version_id=unit.dataset_version_id,
        partition_id=unit.partition_id,
        alpha_data_root=alpha_data_root,
        output_path=output_path,
        plan_id=f"fmat_{idempotency_key}",
        idempotency_key=idempotency_key,
        feature_version_ids=_feature_version_ids(feature_set),
        governance_metadata=governance_metadata,
    )
    records = _feature_value_records_from_parquet(parquet_path)
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=len(records),
        content_hash=content_hash,
        schema_version=FAST_VALUE_SCHEMA_VERSION,
        dataset_version_id=unit.dataset_version_id,
        set_id=unit.feature_set_id,
        partition_id=unit.partition_id,
        min_event_ts=min(record.event_ts.isoformat() for record in records),
        max_event_ts=max(record.event_ts.isoformat() for record in records),
        min_available_ts=min(record.available_ts.isoformat() for record in records),
        max_available_ts=max(record.available_ts.isoformat() for record in records),
    )
    manifest = FastWorkerManifest(
        unit_key=_worker_unit_key(unit),
        parquet_path=parquet_path.as_posix(),
        content_hash=content_hash,
        row_count=int(payload.get("row_count") or len(records)),
        feature_version_ids=feature_version_ids,
        producer_engine_id=FAST_PRODUCER_ENGINE_ID,
        value_schema_version=FAST_VALUE_SCHEMA_VERSION,
        manifest_path=manifest_path.as_posix(),
    )
    return FastWorkerUnitOutput(
        materialization_result=FeatureMaterializationResult(
            plan=plan,
            records=records,
            dry_run=False,
            wrote_output=False,
            output_path=parquet_path,
            value_store_handle=handle,
        ),
        feature_set=feature_set,
        feature_request_payloads=request_payloads,
        registry_metadata=registry_metadata,
        manifest=manifest,
    )


def _v1_registry_metadata(config: ScaleoutConfig, unit: ScaleoutUnit) -> dict[str, Any]:
    from alpha_system.features.fast import FAST_PRODUCER_ENGINE_ID, FAST_VALUE_SCHEMA_VERSION

    metadata: dict[str, Any] = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
        "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
        "engine_selection": SCALEOUT_ENGINE_V1,
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    if config.family in SESSION_METADATA_ROLE_FAMILIES:
        metadata["session_metadata_role"] = SESSION_METADATA_ROLE_MARKER
    return metadata


def _require_worker_manifest_unit_key(
    value: object,
    unit: ScaleoutUnit,
    manifest_path: Path,
) -> None:
    unit_key = _require_mapping(value, "unit_key")
    expected = _worker_unit_key(unit)
    for field in ("unit_id", "family", "symbol", "year", "dataset_version_id", "partition_id"):
        if unit_key.get(field) != expected[field]:
            raise ScaleoutError(
                f"V1 worker manifest unit key mismatch for {field}: {manifest_path}"
            )


def _v1_worker_compute_entrypoint(
    config: ScaleoutConfig,
    job: _V1PreparedWorkerJob,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    threads_per_worker: int,
) -> Any:
    _pin_native_threads(threads_per_worker)
    return _compute_v1_feature_unit_output(
        config,
        job.unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=True,
        include_records=False,
        prepared_feature_set=job.feature_set,
        prepared_feature_request_payloads=job.feature_request_payloads,
        prepared_registry_metadata=job.registry_metadata,
    )


def _fast_label_worker_compute_entrypoint(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
    threads_per_worker: int,
) -> Any:
    _pin_native_threads(threads_per_worker)
    return _compute_fast_label_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=True,
        include_records=False,
    )


def _reference_label_worker_compute_entrypoint(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> Any:
    _pin_reference_label_worker_threads()
    return _compute_reference_label_unit_output(
        config,
        unit,
        alpha_data_root,
        dataset_registry_path,
        canonical_root,
        write_manifest=True,
        include_records=False,
    )


REFERENCE_LABEL_WORKER_ENTRYPOINT = _reference_label_worker_compute_entrypoint


def _pin_reference_label_worker_threads() -> None:
    _pin_native_threads(REFERENCE_LABEL_THREADS_PER_WORKER)


def _pin_native_threads(threads_per_worker: int) -> None:
    token = str(max(1, threads_per_worker))
    os.environ["POLARS_MAX_THREADS"] = token
    os.environ["OMP_NUM_THREADS"] = token
    os.environ["OPENBLAS_NUM_THREADS"] = token
    os.environ["NUMEXPR_MAX_THREADS"] = token
    os.environ["RAYON_NUM_THREADS"] = token
    os.environ["NUMBA_NUM_THREADS"] = token


def _preview_record(config: ScaleoutConfig, unit: ScaleoutUnit, *, stage: str) -> ScaleoutUnitRecord:
    try:
        if _is_label_scaleout_config(config):
            label_version_ids = _preview_label_version_ids(config, unit)
            return ScaleoutUnitRecord(
                unit=unit,
                status="planned",
                stage=stage,
                label_version_ids=label_version_ids,
                message="write-free identity preview",
            )
        feature_version_ids = _preview_feature_version_ids(config, unit)
        return ScaleoutUnitRecord(
            unit=unit,
            status="planned",
            stage=stage,
            feature_version_ids=feature_version_ids,
            message="write-free identity preview",
        )
    except ValueError as exc:
        return ScaleoutUnitRecord(unit=unit, status="failed", stage=stage, message=str(exc))


def _preview_feature_version_ids(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[str, ...]:
    if config.family == "base_ohlcv":
        from alpha_system.cli.seed_pack import preview_seed_feature_pack

        preview = preview_seed_feature_pack(_seed_config(config, unit))
        return tuple(
            _require_text(value, "feature_version_id")
            for value in _sequence(preview.get("feature_version_ids"), "feature_version_ids")
        )
    if config.family == "session_calendar_maintenance":
        definitions = _session_feature_definitions(config, unit, lambda: ())
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "vwap_session_auction":
        definitions = _vwap_session_auction_feature_definitions(config, unit, lambda: ())
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "regime_volatility_compression":
        definitions = _regime_volatility_compression_feature_definitions(
            config,
            unit,
            lambda: (),
        )
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "liquidity_sweep_pa_structure":
        definitions = _liquidity_pa_structure_feature_definitions(
            config,
            unit,
            lambda: (),
        )
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "volume_activity":
        definitions = _volume_activity_feature_definitions(
            config,
            unit,
            lambda: (),
        )
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "bbo_tradability_top_book":
        definitions = _bbo_tradability_top_book_feature_definitions(
            config,
            unit,
            lambda: (),
        )
        return tuple(definition.feature_version_id for definition in definitions)
    if config.family == "cross_market_alignment":
        definitions = _cross_market_alignment_feature_definitions(
            config,
            unit,
            lambda: (),
        )
        return tuple(definition.feature_version_id for definition in definitions)
    raise ScaleoutError(f"unsupported scaleout family: {config.family}")


def _preview_label_version_ids(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[str, ...]:
    return tuple(
        _require_text(getattr(definition, "label_version_id", ""), "label_version_id")
        for definition in _fast_label_definitions_for_unit(config, unit)
    )


def _seed_config(config: ScaleoutConfig, unit: ScaleoutUnit) -> Any:
    from alpha_system.cli.seed_pack import (
        FeatureSetConfig,
        FeatureSpecConfig,
        SeedPackConfig,
    )

    features = tuple(
        FeatureSpecConfig(name=name, window_length=_feature_window(name), horizon=1)
        for name in unit.feature_names
    )
    return SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        feature_set=FeatureSetConfig(
            feature_set_id=unit.feature_set_id,
            feature_set_version=unit.feature_set_version,
            alpha_spec_id=config.alpha_spec_id,
            features=features,
        ),
    )


def _label_seed_config(config: ScaleoutConfig, unit: ScaleoutUnit) -> Any:
    from alpha_system.cli.seed_pack import LabelSetConfig, LabelSpecConfig, SeedPackConfig

    labels = tuple(
        LabelSpecConfig(name=name, horizon=_label_horizon(name)) for name in unit.feature_names
    )
    return SeedPackConfig(
        dataset_version_id=unit.dataset_version_id,
        symbol=unit.symbol,
        partition_id=unit.partition_id,
        partition_schema=unit.schema_id,
        window_start_ts=unit.window_start_ts,
        window_end_ts=unit.window_end_ts,
        label_set=LabelSetConfig(
            label_set_id=unit.feature_set_id,
            labels=labels,
        ),
    )


def _label_horizon(name: str) -> str:
    if name in {"session_close", "maintenance_flat"}:
        return name
    token = name.removeprefix("mid_fwd_ret_").removeprefix("fwd_ret_")
    if token.endswith("m") and token[:-1].isdigit():
        return token
    raise ScaleoutError(f"fixed-horizon label name does not encode a minute horizon: {name}")


def _feature_window(name: str) -> int:
    if name in {"rolling_volatility", "rolling_range", "range_position", "volume_zscore"}:
        return 20
    return 1


def _on_disk_partition_schema(
    canonical_root: str | Path,
    dataset_version_id: str,
    registry_schema: str,
) -> str:
    """Resolve the on-disk canonical partition schema for one DatasetVersion.

    The registry/inventory schema name (e.g. ``ohlcv_dense_research_grid``) is not
    always the on-disk partition directory name (e.g. ``ohlcv_1m_dense``). The
    canonical layer records the real partition schema in each DatasetVersion's
    ``manifest.json``; resolve it from there rather than hardcoding a map, so the
    loader reads the actual ``schema=<...>`` directory. Falls back to the supplied
    registry schema when no manifest partition schema is recorded.
    """

    registry_schema = _require_text(registry_schema, "registry_schema")
    manifest_path = (
        Path(canonical_root)
        / _require_text(dataset_version_id, "dataset_version_id")
        / "manifest.json"
    )
    if not manifest_path.exists():
        return registry_schema
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return registry_schema
    if not isinstance(manifest, Mapping):
        return registry_schema
    on_disk = manifest.get("partition_schema")
    if isinstance(on_disk, str) and on_disk.strip():
        return on_disk.strip()
    return registry_schema


def _session_bar_row_loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
    from alpha_system.data.foundation.canonical_loader import load_canonical_ohlcv_rows

    canonical_root = kwargs.get("canonical_root")
    dataset_version_id = kwargs.get("dataset_version_id")
    registry_schema = kwargs.get("partition_schema")
    if (
        canonical_root is not None
        and isinstance(dataset_version_id, str)
        and isinstance(registry_schema, str)
    ):
        kwargs = dict(kwargs)
        kwargs["partition_schema"] = _on_disk_partition_schema(
            canonical_root,
            dataset_version_id,
            registry_schema,
        )
    # Dense-grid partitions carry research-grid-only columns (has_trade, synthetic,
    # fill_method, provider_bar_ref) on top of the canonical OHLCV field set; the
    # dense-grid feature input view requires those columns, so loaded rows are
    # returned unprojected here. Quality/coverage projection (which consumes the
    # canonical-only CanonicalBarRecord contract) is handled by
    # _scaleout_quality_coverage_builder.
    return tuple(load_canonical_ohlcv_rows(**kwargs))


def _scaleout_quality_coverage_builder(
    config: Any,
    rows: Sequence[Mapping[str, Any]],
    *,
    repo_root: str | Path,
) -> tuple[Any, Any]:
    """Build real quality/coverage reports from canonical-projected OHLCV rows.

    Dense-grid canonical partitions carry research-grid-only columns on top of the
    canonical OHLCV field set. The seed operator's default quality/coverage builder
    consumes the canonical-only ``CanonicalBarRecord`` contract, so project each row
    to the canonical OHLCV fields before delegating to the sanctioned real builder.
    This is a no-op for standard ``ohlcv_1m`` partitions (which already carry exactly
    the canonical fields) and keeps the full dense rows available to the dense-grid
    feature input view.
    """

    from alpha_system.cli.seed_pack import _build_real_quality_coverage
    from alpha_system.data.foundation.canonical_loader import CANONICAL_OHLCV_FIELDS

    projected = tuple(
        _canonical_ohlcv_mapping(row, fields=CANONICAL_OHLCV_FIELDS) for row in rows
    )
    return _build_real_quality_coverage(config, projected, repo_root=repo_root)


def _session_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.session import (
        SessionFeatureName,
        build_session_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )
    offline_feature_names = sorted(
        set(unit.feature_names).intersection({"bars_to_roll", "minutes_to_roll"})
    )
    if offline_feature_names:
        raise ScaleoutError(
            "session_calendar_maintenance scaleout excludes offline/non-causal "
            "features: " + ", ".join(offline_feature_names)
        )

    def _make(feature_name: str) -> Callable[[object], Any]:
        name = SessionFeatureName(feature_name)

        def _build(registry_reader: object) -> Any:
            return build_session_feature_definition(
                name,
                _session_feature_request(config, unit, name),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                input_view_name=(
                    "dense_grid_ohlcv" if config.dense_grid_required else "canonical_ohlcv"
                ),
                input_scope={
                    "symbol": unit.symbol.upper(),
                    "partition_id": unit.partition_id,
                    "partition_schema": unit.schema_id,
                },
            )

        return _build

    return tuple(_make(feature_name) for feature_name in unit.feature_names)


def _session_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader) for builder in _session_definition_builders(config, unit)
    )


def _scaleout_exposure_family(family: str, unit: ScaleoutUnit, name: str) -> str:
    """Build a per-unit duplicate-exposure family for one scaleout feature.

    Scaleout materializes one feature definition across many (symbol, year) units.
    Each (symbol, year) is a distinct research data asset -- the content-addressed
    ``feature_version_id`` already differs per unit via ``input_scope`` -- so each
    must declare a distinct FLF-P05 duplicate-exposure family. A symbol/year-agnostic
    family makes the guard treat the second and later symbols/years of the same
    feature as a BLOCKING duplicate of the first, which is exactly what stalled the
    full-window scaleout after only the first symbol of each family registered. The
    ``partition_id`` (e.g. ``ES_2024_full_year``) uniquely scopes symbol+year. The
    exposure family is excluded from feature identity (``FeatureSpec.to_identity_dict``
    omits ``feature_request_id``), so this scoping never alters ``feature_version_id``;
    it only lets genuinely distinct per-instrument/per-year exposures co-register.
    """

    return f"{family}_{unit.partition_id}_{name}"


def _session_feature_request(config: ScaleoutConfig, unit: ScaleoutUnit, name: Any) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    feature_name = _require_text(getattr(name, "value", str(name)), "session feature name")
    exposure_family = _scaleout_exposure_family(config.family, unit, feature_name)
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": feature_name,
            "window": 1,
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": "session metadata is consumed as of each row available_ts",
            "point_in_time_guard": (
                "metadata with an explicit metadata_available_ts later than the row "
                "available_ts fails closed"
            ),
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "contract_id",
                "series_id",
                "session_label",
                "bar_start_ts",
                "available_ts",
            ],
            "source": "already-canonical accepted OHLCV or dense-grid OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _vwap_session_auction_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.ohlcv import (
        OHLCVFeatureName,
        build_ohlcv_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _VWAPSessionAuctionBinding) -> Callable[[object], Any]:
        name = OHLCVFeatureName(binding.ohlcv_name)

        def _build(registry_reader: object) -> Any:
            return build_ohlcv_feature_definition(
                name,
                _vwap_session_auction_feature_request(config, unit, binding),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=1,
                horizon=1,
                opening_range_minutes=binding.opening_range_minutes,
                anchor_session_label=binding.anchor_session_label,
                reset_on_session=True,
                input_scope={
                    "symbol": unit.symbol.upper(),
                    "partition_id": unit.partition_id,
                    "partition_schema": unit.schema_id,
                    "feature_pack_family": config.family,
                    "config_feature_name": binding.config_name,
                },
            )

        return _build

    return tuple(_make(binding) for binding in _vwap_session_auction_bindings(unit.feature_names))


def _vwap_session_auction_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _vwap_session_auction_definition_builders(config, unit)
    )


def _vwap_session_auction_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _VWAPSessionAuctionBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": binding.ohlcv_name,
            "config_feature_name": binding.config_name,
            "anchor_session_label": binding.anchor_session_label,
            "window": "running_expanding_point_in_time",
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "running_vwap": (
                "cumulative VWAP state uses only rows whose available_ts is less than "
                "or equal to the output available_ts"
            ),
            "final_session_aggregate": (
                "final session VWAP, full-session value area, and closing-auction "
                "aggregates are not bound into intraday feature values"
            ),
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "high",
                "low",
                "close",
                "volume",
                "session_label",
            ],
            "source": "already-canonical accepted OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _vwap_session_auction_bindings(
    feature_names: Sequence[str],
) -> tuple[_VWAPSessionAuctionBinding, ...]:
    bindings = tuple(_vwap_session_auction_binding(name) for name in feature_names)
    actual_names = [binding.ohlcv_name for binding in bindings]
    duplicates = sorted({name for name in actual_names if actual_names.count(name) > 1})
    if duplicates:
        raise ScaleoutError(
            "VWAP/session config maps multiple entries to the same governed "
            f"feature: {', '.join(duplicates)}"
        )
    return bindings


def _vwap_session_auction_binding(name: str) -> _VWAPSessionAuctionBinding:
    token = _require_text(name, "vwap_session_auction feature name")
    normalized = token.strip().lower()
    if normalized in {"running_vwap", "vwap"}:
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="vwap",
            exposure_name="running_vwap",
        )
    if normalized in {"anchored_eth_vwap", "eth_vwap"}:
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="anchored_vwap",
            exposure_name="anchored_eth_vwap",
            anchor_session_label="ETH",
        )
    if normalized == "anchored_vwap":
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="anchored_vwap",
            exposure_name="anchored_eth_vwap",
            anchor_session_label="ETH",
        )
    if normalized == "distance_to_vwap":
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="distance_to_vwap",
            exposure_name="distance_to_running_vwap",
        )
    if normalized == "opening_range":
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="opening_range",
            exposure_name="opening_range",
        )
    if normalized == "overnight_range":
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="overnight_range",
            exposure_name="overnight_range",
        )
    if normalized in {"rth_open_context", "session_minute"}:
        return _VWAPSessionAuctionBinding(
            config_name=token,
            ohlcv_name="session_minute",
            exposure_name="rth_open_context",
        )
    raise ScaleoutError(f"unsupported VWAP/session-auction feature: {name}")


def _vwap_binding_metadata(binding: _VWAPSessionAuctionBinding) -> dict[str, object]:
    payload: dict[str, object] = {
        "config_feature_name": binding.config_name,
        "governed_ohlcv_feature": binding.ohlcv_name,
        "running_point_in_time": True,
        "final_session_aggregate_intraday_use": "forbidden",
    }
    if binding.anchor_session_label is not None:
        payload["anchor_session_label"] = binding.anchor_session_label
    if binding.ohlcv_name == "opening_range":
        payload["opening_range_minutes"] = binding.opening_range_minutes
    return payload


def _regime_volatility_compression_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.ohlcv import (
        OHLCVFeatureName,
        build_ohlcv_feature_definition,
    )
    from alpha_system.features.families.structure import (
        StructureFeatureName,
        build_structure_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _RegimeVolatilityCompressionBinding) -> Callable[[object], Any]:
        input_scope = {
            "symbol": unit.symbol.upper(),
            "partition_id": unit.partition_id,
            "partition_schema": unit.schema_id,
            "feature_pack_family": config.family,
            "config_feature_name": binding.config_name,
        }

        def _build(registry_reader: object) -> Any:
            if binding.primitive_family == "ohlcv":
                return build_ohlcv_feature_definition(
                    OHLCVFeatureName(binding.primitive_name),
                    _regime_volatility_compression_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    horizon=binding.horizon,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            if binding.primitive_family == "structure":
                return build_structure_feature_definition(
                    StructureFeatureName(binding.primitive_name),
                    _regime_volatility_compression_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            raise ScaleoutError(
                f"unsupported regime primitive family: {binding.primitive_family}"
            )

        return _build

    return tuple(
        _make(binding)
        for binding in _regime_volatility_compression_bindings(unit.feature_names)
    )


def _regime_volatility_compression_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _regime_volatility_compression_definition_builders(config, unit)
    )


def _regime_volatility_compression_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _RegimeVolatilityCompressionBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": binding.primitive_name,
            "config_feature_name": binding.config_name,
            "primitive_family": binding.primitive_family,
            "window": binding.window_length,
            "horizon": binding.horizon,
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "lookback": (
                "rolling regime, volatility, and compression state uses only rows "
                "whose available_ts is less than or equal to the output available_ts"
            ),
            "future_state": "future labels and final-session aggregates are not inputs",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "session_label",
                "quality_flags",
            ],
            "source": "already-canonical accepted OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _regime_volatility_compression_bindings(
    feature_names: Sequence[str],
) -> tuple[_RegimeVolatilityCompressionBinding, ...]:
    bindings = tuple(_regime_volatility_compression_binding(name) for name in feature_names)
    actual = [
        (binding.primitive_family, binding.primitive_name)
        for binding in bindings
    ]
    duplicates = sorted({item for item in actual if actual.count(item) > 1})
    if duplicates:
        rendered = ", ".join(f"{family}:{name}" for family, name in duplicates)
        raise ScaleoutError(
            "regime config maps multiple entries to the same governed primitive: "
            f"{rendered}"
        )
    return bindings


def _regime_volatility_compression_binding(
    name: str,
) -> _RegimeVolatilityCompressionBinding:
    token = _require_text(name, "regime_volatility_compression feature name")
    normalized = token.strip().lower()
    if normalized == "trendiness":
        return _RegimeVolatilityCompressionBinding(
            config_name=token,
            primitive_family="ohlcv",
            primitive_name="trendiness",
            exposure_name="trendiness",
        )
    if normalized == "atr_volatility_regime":
        return _RegimeVolatilityCompressionBinding(
            config_name=token,
            primitive_family="ohlcv",
            primitive_name="atr",
            exposure_name="atr_volatility_regime",
        )
    if normalized == "range_compression":
        return _RegimeVolatilityCompressionBinding(
            config_name=token,
            primitive_family="structure",
            primitive_name="range_contraction",
            exposure_name="range_compression",
        )
    if normalized == "range_expansion":
        return _RegimeVolatilityCompressionBinding(
            config_name=token,
            primitive_family="ohlcv",
            primitive_name="rolling_range",
            exposure_name="range_expansion",
        )
    if normalized == "momentum_reversion_state":
        return _RegimeVolatilityCompressionBinding(
            config_name=token,
            primitive_family="ohlcv",
            primitive_name="returns",
            exposure_name="momentum_reversion_state",
            window_length=1,
        )
    raise ScaleoutError(f"unsupported regime/volatility/compression feature: {name}")


def _regime_binding_metadata(
    binding: _RegimeVolatilityCompressionBinding,
) -> dict[str, object]:
    return {
        "config_feature_name": binding.config_name,
        "governed_primitive_family": binding.primitive_family,
        "governed_primitive_name": binding.primitive_name,
        "exposure_name": binding.exposure_name,
        "window_length": binding.window_length,
        "horizon": binding.horizon,
        "causal_available_ts": True,
    }


def _liquidity_pa_structure_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.structure import (
        StructureFeatureName,
        build_structure_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _LiquidityPAStructureBinding) -> Callable[[object], Any]:
        input_scope = {
            "symbol": unit.symbol.upper(),
            "partition_id": unit.partition_id,
            "partition_schema": unit.schema_id,
            "feature_pack_family": config.family,
            "config_feature_names": list(binding.config_names),
        }

        def _build(registry_reader: object) -> Any:
            return build_structure_feature_definition(
                StructureFeatureName(binding.primitive_name),
                _liquidity_pa_structure_feature_request(config, unit, binding),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=binding.window_length,
                reset_on_session=True,
                input_scope=input_scope,
            )

        return _build

    return tuple(
        _make(binding) for binding in _liquidity_pa_structure_bindings(unit.feature_names)
    )


def _liquidity_pa_structure_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _liquidity_pa_structure_definition_builders(config, unit)
    )


def _liquidity_pa_structure_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _LiquidityPAStructureBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": binding.primitive_name,
            "config_feature_names": list(binding.config_names),
            "primitive_family": "liquidity_structure",
            "window": binding.window_length,
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "lookback": (
                "prior-boundary, sweep, failed-breakout, wick, and compression "
                "state uses only rows whose available_ts is less than or equal to "
                "the output available_ts"
            ),
            "future_state": "future labels and final-session aggregates are not inputs",
            "subjective_pa": "subjective or discretionary price-action encodings are forbidden",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "session_label",
                "quality_flags",
            ],
            "source": "already-canonical accepted OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _liquidity_pa_structure_bindings(
    feature_names: Sequence[str],
) -> tuple[_LiquidityPAStructureBinding, ...]:
    merged: dict[str, _LiquidityPAStructureBinding] = {}
    order: list[str] = []
    for config_name in feature_names:
        for primitive_name, exposure_name in _liquidity_pa_structure_binding_items(config_name):
            existing = merged.get(primitive_name)
            if existing is None:
                merged[primitive_name] = _LiquidityPAStructureBinding(
                    config_names=(config_name,),
                    primitive_name=primitive_name,
                    exposure_name=exposure_name,
                )
                order.append(primitive_name)
                continue
            merged[primitive_name] = _LiquidityPAStructureBinding(
                config_names=(*existing.config_names, config_name),
                primitive_name=existing.primitive_name,
                exposure_name=existing.exposure_name,
                window_length=existing.window_length,
            )
    if not order:
        raise ScaleoutError("liquidity/PA structure config did not select any primitives")
    return tuple(merged[name] for name in order)


def _liquidity_pa_structure_binding_items(
    name: str,
) -> tuple[tuple[str, str], ...]:
    token = _require_text(name, "liquidity_sweep_pa_structure feature name")
    normalized = token.strip().lower()
    if normalized == "prior_high_low_sweep":
        return (
            ("prior_high_distance", "prior_high_distance"),
            ("prior_low_distance", "prior_low_distance"),
            ("sweep_high_flag", "sweep_high_flag"),
            ("sweep_low_flag", "sweep_low_flag"),
        )
    if normalized == "close_back_inside":
        return (
            ("failed_high_breakout_flag", "close_back_inside_high"),
            ("failed_low_breakout_flag", "close_back_inside_low"),
        )
    if normalized == "wick_rejection":
        return (
            ("close_location_value", "close_location_value"),
            ("wick_rejection_score", "wick_rejection_score"),
        )
    if normalized == "displacement":
        return (
            ("prior_high_distance", "prior_high_displacement"),
            ("prior_low_distance", "prior_low_displacement"),
            ("close_location_value", "close_location_displacement_context"),
        )
    if normalized == "compression_breakout":
        return (
            ("range_contraction", "range_contraction"),
            ("sweep_high_flag", "compression_high_sweep"),
            ("sweep_low_flag", "compression_low_sweep"),
        )
    if normalized == "failed_breakout":
        return (
            ("failed_high_breakout_flag", "failed_high_breakout_flag"),
            ("failed_low_breakout_flag", "failed_low_breakout_flag"),
        )
    raise ScaleoutError(f"unsupported liquidity-sweep / PA-structure feature: {name}")


def _liquidity_pa_binding_metadata(
    binding: _LiquidityPAStructureBinding,
) -> dict[str, object]:
    return {
        "config_feature_names": list(binding.config_names),
        "governed_primitive_family": "liquidity_structure",
        "governed_primitive_name": binding.primitive_name,
        "exposure_name": binding.exposure_name,
        "window_length": binding.window_length,
        "causal_available_ts": True,
        "objective_ohlcv_derived": True,
    }


def _volume_activity_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.ohlcv import (
        OHLCVFeatureName,
        build_ohlcv_feature_definition,
    )
    from alpha_system.features.families.structure import (
        StructureFeatureName,
        build_structure_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _VolumeActivityBinding) -> Callable[[object], Any]:
        input_scope = {
            "symbol": unit.symbol.upper(),
            "partition_id": unit.partition_id,
            "partition_schema": unit.schema_id,
            "feature_pack_family": config.family,
            "config_feature_names": list(binding.config_names),
        }

        def _build(registry_reader: object) -> Any:
            if binding.primitive_family == "ohlcv":
                return build_ohlcv_feature_definition(
                    OHLCVFeatureName(binding.primitive_name),
                    _volume_activity_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    horizon=binding.horizon,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            if binding.primitive_family == "structure":
                return build_structure_feature_definition(
                    StructureFeatureName(binding.primitive_name),
                    _volume_activity_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            raise ScaleoutError(
                f"unsupported volume/activity primitive family: {binding.primitive_family}"
            )

        return _build

    return tuple(_make(binding) for binding in _volume_activity_bindings(unit.feature_names))


def _volume_activity_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _volume_activity_definition_builders(config, unit)
    )


def _volume_activity_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _VolumeActivityBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": binding.primitive_name,
            "config_feature_names": list(binding.config_names),
            "primitive_family": binding.primitive_family,
            "window": binding.window_length,
            "horizon": binding.horizon,
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "lookback": (
                "volume, activity, and effort/result state uses only rows whose "
                "available_ts is less than or equal to the output available_ts"
            ),
            "future_state": "future labels and final-session aggregates are not inputs",
            "feature_zoo": "new volume/activity primitives are forbidden in FUTSUB-P11",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "session_label",
                "quality_flags",
            ],
            "source": "already-canonical accepted OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _volume_activity_bindings(
    feature_names: Sequence[str],
) -> tuple[_VolumeActivityBinding, ...]:
    merged: dict[tuple[str, str], _VolumeActivityBinding] = {}
    order: list[tuple[str, str]] = []
    for config_name in feature_names:
        for item in _volume_activity_binding_items(config_name):
            family, primitive_name, exposure_name, window_length, horizon = item
            key = (family, primitive_name)
            existing = merged.get(key)
            if existing is None:
                merged[key] = _VolumeActivityBinding(
                    config_names=(config_name,),
                    primitive_family=family,
                    primitive_name=primitive_name,
                    exposure_name=exposure_name,
                    window_length=window_length,
                    horizon=horizon,
                )
                order.append(key)
                continue
            merged[key] = _VolumeActivityBinding(
                config_names=(*existing.config_names, config_name),
                primitive_family=existing.primitive_family,
                primitive_name=existing.primitive_name,
                exposure_name=existing.exposure_name,
                window_length=existing.window_length,
                horizon=existing.horizon,
            )
    if not order:
        raise ScaleoutError("volume/activity config did not select any primitives")
    return tuple(merged[key] for key in order)


def _volume_activity_binding_items(
    name: str,
) -> tuple[tuple[str, str, str, int, int], ...]:
    token = _require_text(name, "volume_activity feature name")
    normalized = token.strip().lower()
    if normalized == "participation":
        return (
            ("ohlcv", "rolling_volume", "rolling_volume_participation", 20, 1),
            ("ohlcv", "volume_zscore", "volume_participation_zscore", 20, 1),
        )
    if normalized == "time_of_day_relative_volume":
        return (
            ("ohlcv", "session_minute", "session_minute_volume_context", 1, 1),
            ("ohlcv", "volume_zscore", "time_of_day_relative_volume_zscore", 20, 1),
        )
    if normalized == "volume_regime":
        return (
            ("ohlcv", "rolling_volume", "rolling_volume_regime", 20, 1),
            ("ohlcv", "volume_zscore", "volume_regime_zscore", 20, 1),
        )
    if normalized == "activity_bursts":
        return (
            ("ohlcv", "volume_zscore", "activity_burst_volume_zscore", 20, 1),
            ("ohlcv", "rolling_range", "activity_burst_range_context", 20, 1),
        )
    if normalized == "effort_result_proxies":
        return (
            ("ohlcv", "rolling_volume", "effort_rolling_volume", 20, 1),
            ("ohlcv", "range_position", "result_range_position", 20, 1),
            ("ohlcv", "trendiness", "result_trendiness", 20, 1),
            ("structure", "close_location_value", "effort_result_close_location", 3, 1),
            ("structure", "wick_rejection_score", "effort_result_wick_rejection", 3, 1),
        )
    raise ScaleoutError(f"unsupported volume/activity feature: {name}")


def _volume_activity_binding_metadata(binding: _VolumeActivityBinding) -> dict[str, object]:
    return {
        "config_feature_names": list(binding.config_names),
        "governed_primitive_family": binding.primitive_family,
        "governed_primitive_name": binding.primitive_name,
        "exposure_name": binding.exposure_name,
        "window_length": binding.window_length,
        "horizon": binding.horizon,
        "causal_available_ts": True,
        "existing_primitives_only": True,
    }


def _bbo_tradability_top_book_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.bbo import (
        BBOFeatureName,
        build_bbo_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _BBOTradabilityTopBookBinding) -> Callable[[object], Any]:
        def _build(registry_reader: object) -> Any:
            return build_bbo_feature_definition(
                BBOFeatureName(binding.bbo_name),
                _bbo_tradability_top_book_feature_request(config, unit, binding),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=binding.window_length,
                reset_on_session=True,
                input_scope={
                    "symbol": unit.symbol.upper(),
                    "partition_id": unit.partition_id,
                    "partition_schema": unit.schema_id,
                    "feature_pack_family": config.family,
                    "config_feature_name": binding.config_name,
                    "bbo_proxy_semantics": "time_sampled_forward_filled_tradability_proxy",
                },
            )

        return _build

    return tuple(
        _make(binding) for binding in _bbo_tradability_top_book_bindings(unit.feature_names)
    )


def _bbo_tradability_top_book_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _bbo_tradability_top_book_definition_builders(config, unit)
    )


def _bbo_tradability_top_book_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _BBOTradabilityTopBookBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "operation": binding.bbo_name,
            "config_feature_name": binding.config_name,
            "window": binding.window_length,
            "scaleout_unit_id": unit.unit_id,
            "proxy_semantics": "time_sampled_forward_filled_bbo_1m",
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current BBO row available_ts",
            "forward_fill": (
                "BBO-1m source rows are consumed as a time-sampled and forward-filled "
                "tradability proxy; canonical row available_ts is preserved"
            ),
            "missingness": (
                "missing_bbo, bbo_quarantined, wide_spread, and low_depth states "
                "are surfaced as flags or value gaps, not silently imputed"
            ),
            "forbidden_claims": (
                "passive-fill, queue-priority, market-impact, intra-minute path, "
                "and execution-truth claims are forbidden"
            ),
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "bid",
                "ask",
                "bid_size",
                "ask_size",
                "mid",
                "spread",
                "spread_ticks",
                "microprice",
                "quality_flags",
                "session_label",
            ],
            "source": "already-canonical accepted BBO-1m DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _bbo_tradability_top_book_bindings(
    feature_names: Sequence[str],
) -> tuple[_BBOTradabilityTopBookBinding, ...]:
    bindings = tuple(_bbo_tradability_top_book_binding(name) for name in feature_names)
    actual = [binding.bbo_name for binding in bindings]
    duplicates = sorted({name for name in actual if actual.count(name) > 1})
    if duplicates:
        raise ScaleoutError(
            "BBO top-book config maps multiple entries to the same governed "
            f"feature: {', '.join(duplicates)}"
        )
    return bindings


def _bbo_tradability_top_book_binding(name: str) -> _BBOTradabilityTopBookBinding:
    token = _require_text(name, "bbo_tradability_top_book feature name")
    normalized = token.strip().lower()
    if normalized in {
        "mid",
        "spread",
        "spread_ticks",
        "spread_zscore",
        "top_book_depth",
        "top_book_imbalance",
        "missing_bbo_flag",
        "bad_quote_flag",
        "wide_spread_flag",
        "low_depth_flag",
    }:
        return _BBOTradabilityTopBookBinding(
            config_name=token,
            bbo_name=normalized,
            exposure_name=normalized,
            window_length=20 if normalized == "spread_zscore" else 3,
        )
    if normalized in {"microprice_proxy", "microprice_ish_proxy"}:
        return _BBOTradabilityTopBookBinding(
            config_name=token,
            bbo_name="microprice",
            exposure_name="microprice_proxy",
            window_length=3,
        )
    raise ScaleoutError(f"unsupported BBO tradability / top-book feature: {name}")


def _bbo_binding_metadata(binding: _BBOTradabilityTopBookBinding) -> dict[str, object]:
    return {
        "config_feature_name": binding.config_name,
        "governed_bbo_feature": binding.bbo_name,
        "exposure_name": binding.exposure_name,
        "window_length": binding.window_length,
        "causal_available_ts": True,
        "time_sampled_forward_filled_proxy": True,
        "execution_truth_claim": "forbidden",
    }


def _cross_market_alignment_definition_builders(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
) -> tuple[Callable[[object], Any], ...]:
    from alpha_system.features.families.cross_market import (
        CrossMarketFeatureName,
        build_cross_market_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )

    def _make(binding: _CrossMarketAlignmentBinding) -> Callable[[object], Any]:
        def _build(registry_reader: object) -> Any:
            return build_cross_market_feature_definition(
                CrossMarketFeatureName(binding.cross_market_name),
                _cross_market_alignment_feature_request(config, unit, binding),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=binding.window_length,
                horizon=1,
                reset_on_session=True,
                alignment_policy="strict_intersection",
                input_scope={
                    "target_symbol": unit.symbol.upper(),
                    "partition_id": unit.partition_id,
                    "partition_schema": unit.schema_id,
                    "feature_pack_family": config.family,
                    "config_feature_name": binding.config_name,
                    "cross_market_alignment_policy": "strict_intersection",
                },
            )

        return _build

    return tuple(
        _make(binding) for binding in _cross_market_alignment_bindings(unit.feature_names)
    )


def _cross_market_alignment_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    return tuple(
        builder(registry_reader)
        for builder in _cross_market_alignment_definition_builders(config, unit)
    )


def _cross_market_alignment_feature_request(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    binding: _CrossMarketAlignmentBinding,
) -> Any:
    from alpha_system.governance.duplicate_exposure import (
        ExposureCheckResult,
        ExposureRegistryStatus,
    )
    from alpha_system.governance.feature_request import (
        FeatureRequestApprovalStatus,
        create_feature_request,
    )

    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = _scaleout_exposure_family(config.family, unit, binding.exposure_name)
    return create_feature_request(
        alpha_spec_id=config.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": list(config.input_schemas),
            "markets": list(config.symbols),
            "target_symbol": unit.symbol.upper(),
            "operation": binding.cross_market_name,
            "config_feature_name": binding.config_name,
            "window": binding.window_length,
            "alignment_policy": "strict_intersection",
            "scaleout_unit_id": unit.unit_id,
        },
        availability_assumptions={
            "timing": (
                "feature value is emitted only after all ES/NQ/RTY contributing "
                "rows and return primitives for the same event timestamp are available"
            ),
            "available_ts": (
                "output available_ts is the latest contributing per-instrument "
                "available_ts; no cross-instrument forward-fill is permitted"
            ),
            "missingness": (
                "missing instruments or no-trade rows surface as gaps or excluded "
                "event intersections, never imputed values"
            ),
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "instrument_id",
                "bar_start_ts",
                "event_ts",
                "available_ts",
                "close",
                "quality_flags",
                "session_label",
            ],
            "source": "already-canonical accepted ES/NQ/RTY OHLCV DatasetVersions",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _cross_market_alignment_bindings(
    feature_names: Sequence[str],
) -> tuple[_CrossMarketAlignmentBinding, ...]:
    bindings: list[_CrossMarketAlignmentBinding] = []
    for name in feature_names:
        bindings.extend(_cross_market_alignment_binding(name))
    actual = [binding.cross_market_name for binding in bindings]
    duplicates = sorted({name for name in actual if actual.count(name) > 1})
    if duplicates:
        raise ScaleoutError(
            "cross-market config maps multiple entries to the same governed "
            f"feature: {', '.join(duplicates)}"
        )
    return tuple(bindings)


def _cross_market_alignment_binding(name: str) -> tuple[_CrossMarketAlignmentBinding, ...]:
    token = _require_text(name, "cross_market_alignment feature name")
    normalized = token.strip().lower()
    if normalized == "aligned_returns":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="synchronized_returns",
                exposure_name="aligned_returns",
                window_length=3,
            ),
        )
    if normalized == "beta_residual":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="nq_es_rolling_beta_residual",
                exposure_name="nq_es_beta_residual",
                window_length=20,
            ),
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="rty_es_rolling_beta_residual",
                exposure_name="rty_es_beta_residual",
                window_length=20,
            ),
        )
    if normalized == "basket_residual":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="nq_minus_es_return_spread",
                exposure_name="nq_minus_es_spread",
                window_length=3,
            ),
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="rty_minus_es_return_spread",
                exposure_name="rty_minus_es_spread",
                window_length=3,
            ),
        )
    if normalized == "relative_strength_rank":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="risk_on_rotation_proxy",
                exposure_name="relative_strength_rotation_proxy",
                window_length=3,
            ),
        )
    if normalized == "catch_up_rotation":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="risk_off_rotation_proxy",
                exposure_name="catch_up_rotation_proxy",
                window_length=3,
            ),
        )
    if normalized == "divergence_agreement":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="confirmation_flag",
                exposure_name="agreement_flag",
                window_length=3,
            ),
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="divergence_flag",
                exposure_name="divergence_flag",
                window_length=3,
            ),
        )
    if normalized == "lead_lag":
        return (
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="nq_es_rolling_correlation",
                exposure_name="nq_es_lead_lag_proxy",
                window_length=20,
            ),
            _CrossMarketAlignmentBinding(
                config_name=token,
                cross_market_name="rty_es_rolling_correlation",
                exposure_name="rty_es_lead_lag_proxy",
                window_length=20,
            ),
        )
    raise ScaleoutError(f"unsupported cross-market alignment feature: {name}")


def _cross_market_binding_metadata(
    binding: _CrossMarketAlignmentBinding,
) -> dict[str, object]:
    return {
        "config_feature_name": binding.config_name,
        "governed_cross_market_feature": binding.cross_market_name,
        "exposure_name": binding.exposure_name,
        "window_length": binding.window_length,
        "alignment_policy": "strict_intersection",
        "per_instrument_available_ts": "preserved",
        "cross_instrument_forward_fill": "forbidden",
    }


def _build_cross_market_accepted_context(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> _CrossMarketAcceptedContext:
    from alpha_system.data.foundation.canonical_loader import (
        CANONICAL_OHLCV_FIELDS,
        load_canonical_ohlcv_rows,
    )
    from alpha_system.data.foundation.datasets import (
        CoverageReport,
        DataQualityReport,
        ReportStatus,
    )
    from alpha_system.features import consumption

    rows: list[Mapping[str, Any]] = []
    row_counts: dict[str, int] = {}
    partition_schema = _on_disk_partition_schema(
        canonical_root,
        unit.dataset_version_id,
        unit.schema_id,
    )
    for symbol in config.symbols:
        loaded = tuple(
            load_canonical_ohlcv_rows(
                canonical_root=canonical_root,
                dataset_version_id=unit.dataset_version_id,
                symbol=symbol,
                start_ts=unit.window_start_ts,
                end_ts=unit.window_end_ts,
                partition_schema=partition_schema,
            )
        )
        if not loaded:
            raise ScaleoutError(
                f"no canonical cross-market OHLCV rows were loaded for {symbol}"
            )
        canonical_rows = tuple(
            _canonical_ohlcv_mapping(row, fields=CANONICAL_OHLCV_FIELDS)
            for row in loaded
        )
        row_counts[symbol.upper()] = len(canonical_rows)
        rows.extend(canonical_rows)
    if set(row_counts) != {symbol.upper() for symbol in config.symbols}:
        raise ScaleoutError("cross-market context did not load the configured instrument set")

    resolved_dataset_version = resolve_dataset_version(
        dataset_registry_path,
        unit.dataset_version_id,
    )
    if resolved_dataset_version is None:
        raise ScaleoutError(
            f"DatasetVersion not resolvable for cross-market unit: {unit.dataset_version_id}"
        )
    quality = DataQualityReport(
        quality_report_id=f"dqr_{unit.dataset_version_id}",
        dataset_version_id=unit.dataset_version_id,
        gap_summary=_passing_quality_summary(ReportStatus),
        duplicate_summary=_passing_quality_summary(ReportStatus),
        non_monotonic_summary=_passing_quality_summary(ReportStatus),
        ohlc_errors=_passing_quality_summary(ReportStatus),
        zero_negative_price_errors=_passing_quality_summary(ReportStatus),
        zero_volume_anomalies=_passing_quality_summary(ReportStatus),
        dst_anomalies=_passing_quality_summary(ReportStatus),
        session_coverage=_passing_quality_summary(ReportStatus),
        roll_discontinuities=_passing_quality_summary(ReportStatus),
        provider_error_summary=_passing_quality_summary(ReportStatus),
        bbo_missing_metric=_passing_quality_summary(ReportStatus),
        abnormal_spread_summary=_passing_quality_summary(ReportStatus),
        status=ReportStatus.PASSING,
    )
    coverage = CoverageReport(
        coverage_report_id=f"covr_{unit.dataset_version_id}",
        dataset_version_id=unit.dataset_version_id,
        symbol_coverage=_passing_coverage_summary(sum(row_counts.values()), ReportStatus),
        contract_coverage=_passing_coverage_summary(sum(row_counts.values()), ReportStatus),
        session_coverage=_passing_coverage_summary(sum(row_counts.values()), ReportStatus),
        partition_coverage=_passing_coverage_summary(sum(row_counts.values()), ReportStatus),
        missing_intervals=(),
        incomplete_chunks=(),
    )
    accepted = consumption.AcceptedDatasetVersion(
        registry_path=dataset_registry_path,
        dataset_version=resolved_dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=quality,
        coverage_report=coverage,
    )
    return _CrossMarketAcceptedContext(
        accepted=accepted,
        bar_rows=tuple(rows),
        row_counts_by_symbol=row_counts,
        quality_status=quality.status.value,
        coverage_status=coverage.coverage_status.value,
    )


def _canonical_ohlcv_mapping(
    row: Mapping[str, Any],
    *,
    fields: Sequence[str],
) -> dict[str, Any]:
    missing = [field for field in fields if field not in row]
    if missing:
        raise ScaleoutError(
            "canonical OHLCV row missing required fields: " + ", ".join(missing)
        )
    return {field: row[field] for field in fields}


def _passing_quality_summary(report_status: Any) -> dict[str, object]:
    return {"count": 0, "status": report_status.PASSING.value, "blocking": False}


def _passing_coverage_summary(count: int, report_status: Any) -> dict[str, object]:
    return {
        "status": report_status.PASSING.value,
        "blocking": False,
        "expected_count": count,
        "observed_count": count,
        "missing_count": 0,
        "missing_interval_count": 0,
        "incomplete_chunk_count": 0,
    }


def _build_bbo_accepted_context(
    unit: ScaleoutUnit,
    *,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> _BBOAcceptedContext:
    from alpha_system.data.foundation.canonical_loader import load_canonical_bbo_rows
    from alpha_system.data.foundation.datasets import (
        CoverageReport,
        DataQualityReport,
        DatasetVersion,
        compute_quality_report_hash,
    )
    from alpha_system.data.foundation.quotes import CanonicalBBORecord
    from alpha_system.features import consumption

    rows = tuple(
        load_canonical_bbo_rows(
            canonical_root=canonical_root,
            dataset_version_id=unit.dataset_version_id,
            symbol=unit.symbol,
            start_ts=unit.window_start_ts,
            end_ts=unit.window_end_ts,
            partition_schema=_on_disk_partition_schema(
                canonical_root,
                unit.dataset_version_id,
                unit.schema_id,
            ),
        )
    )
    if not rows:
        raise ScaleoutError("no canonical BBO rows were loaded for the scaleout window")

    records = tuple(CanonicalBBORecord.from_mapping(row) for row in rows)
    quality = DataQualityReport.from_canonical_bbos(
        quality_report_id=f"dqr_{unit.dataset_version_id}",
        dataset_version_id=unit.dataset_version_id,
        bbos=records,
        expected_sessions=tuple(sorted({record.session_label for record in records})),
        abnormal_spread_threshold=None,
    )
    coverage = CoverageReport.from_canonical_bbos(
        coverage_report_id=f"covr_{unit.dataset_version_id}",
        dataset_version_id=unit.dataset_version_id,
        bbos=records,
        expected_intervals=_observed_bbo_intervals(records, partition_id=unit.partition_id),
    )
    if quality.blocks_versioning:
        raise ScaleoutError("BBO quality report blocks versioning; refusing materialization")
    if coverage.blocks_versioning:
        raise ScaleoutError("BBO coverage report blocks versioning; refusing materialization")

    # Resolve the provider source from the registered DatasetVersion rather than
    # hardcoding a provider literal in feature-layer code (no-raw-provider boundary).
    resolved_dataset_version = resolve_dataset_version(
        dataset_registry_path, unit.dataset_version_id
    )
    if resolved_dataset_version is None:
        raise ScaleoutError(
            f"DatasetVersion not resolvable for BBO unit: {unit.dataset_version_id}"
        )
    dataset_version = DatasetVersion(
        dataset_version_id=unit.dataset_version_id,
        source=resolved_dataset_version.source,
        symbol_universe=(unit.symbol.upper(),),
        bar_size="1 min",
        what_to_show="BBO",
        start_ts=_parse_iso_datetime(unit.window_start_ts, "window_start_ts"),
        end_ts=_parse_iso_datetime(unit.window_end_ts, "window_end_ts"),
        contract_universe=(unit.symbol.upper(),),
        roll_policy_id="roll_cme_index_futures_quarterly",
        manifest_hash="0" * 64,
        code_hash="0" * 64,
        config_hash="0" * 64,
        quality_report_hash=compute_quality_report_hash(quality),
        created_at=_parse_iso_datetime(unit.window_end_ts, "window_end_ts"),
    )
    accepted = consumption.AcceptedDatasetVersion(
        registry_path=dataset_registry_path,
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=quality,
        coverage_report=coverage,
    )
    return _BBOAcceptedContext(
        accepted=accepted,
        bbo_rows=rows,
        quality_status=quality.status.value,
        coverage_status=coverage.coverage_status.value,
    )


def _observed_bbo_intervals(
    records: Sequence[Any],
    *,
    partition_id: str,
) -> tuple[Mapping[str, object], ...]:
    by_group: dict[tuple[str, str, str], list[Any]] = {}
    for record in records:
        key = (record.instrument_id, record.contract_id, record.session_label)
        by_group.setdefault(key, []).append(record)

    intervals: list[Mapping[str, object]] = []
    for (instrument_id, contract_id, session_label), group_rows in sorted(by_group.items()):
        ordered = sorted(group_rows, key=lambda row: row.bar_start_ts)
        if not ordered:
            continue
        run_start = ordered[0].bar_start_ts
        previous_end = ordered[0].bar_end_ts
        for row in ordered[1:]:
            if row.bar_start_ts != previous_end:
                intervals.append(
                    _bbo_interval(
                        symbol=instrument_id,
                        instrument_id=instrument_id,
                        contract_id=contract_id,
                        session_label=session_label,
                        partition_id=partition_id,
                        start_ts=run_start,
                        end_ts=previous_end,
                    )
                )
                run_start = row.bar_start_ts
            previous_end = row.bar_end_ts
        intervals.append(
            _bbo_interval(
                symbol=instrument_id,
                instrument_id=instrument_id,
                contract_id=contract_id,
                session_label=session_label,
                partition_id=partition_id,
                start_ts=run_start,
                end_ts=previous_end,
            )
        )
    if not intervals:
        raise ScaleoutError("BBO coverage context requires at least one observed interval")
    return tuple(intervals)


def _bbo_interval(
    *,
    symbol: str,
    instrument_id: str,
    contract_id: str,
    session_label: str,
    partition_id: str,
    start_ts: datetime,
    end_ts: datetime,
) -> Mapping[str, object]:
    if end_ts <= start_ts:
        raise ScaleoutError("BBO observed interval end_ts must be greater than start_ts")
    return {
        "symbol": symbol,
        "instrument_id": instrument_id,
        "contract_id": contract_id,
        "session_label": session_label,
        "partition_id": partition_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
    }


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScaleoutError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ScaleoutError(f"{field_name} must be timezone-aware")
    return parsed


def _definition_feature_spec(definition: Any) -> Any:
    spec = getattr(definition, "spec", None)
    feature_spec = getattr(spec, "feature_spec", None)
    return feature_spec if feature_spec is not None else spec


def _unit_input_datasets(unit: ScaleoutUnit) -> tuple[ScaleoutInputDataset, ...]:
    if unit.input_datasets:
        return unit.input_datasets
    return (
        ScaleoutInputDataset(
            schema_id=unit.schema_id,
            dataset_version_id=unit.dataset_version_id,
            acceptance_state=unit.acceptance_state,
            acceptance_state_source=unit.acceptance_state_source,
        ),
    )


def _require_persisted_acceptance_lock(unit: ScaleoutUnit, dataset_registry_path: Path) -> None:
    for dataset in _unit_input_datasets(unit):
        lock = resolve_dataset_acceptance_lock(dataset_registry_path, dataset.dataset_version_id)
        if lock is None:
            raise ScaleoutError(
                "persisted DatasetVersion acceptance lock not found: "
                f"{dataset.dataset_version_id}"
            )
        if lock.state.value not in ELIGIBLE_ACCEPTANCE_STATES:
            raise ScaleoutError(
                f"DatasetVersion acceptance state is not executable: {lock.state.value}"
            )
        if lock.state.value != dataset.acceptance_state:
            raise ScaleoutError(
                "persisted DatasetVersion acceptance state does not match planning summary: "
                f"{lock.state.value} != {dataset.acceptance_state}"
            )


def _verify_feature_registry_roundtrip(
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    feature_version_ids: tuple[str, ...],
    parquet_path: str,
    content_hash: str | None = None,
    value_schema_version: str | None = None,
) -> None:
    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    for feature_version_id in feature_version_ids:
        record = store.resolve_feature(feature_version_id)
        if record is None:
            raise ScaleoutError(f"registered feature did not resolve: {feature_version_id}")
        if record.dataset_version_id != unit.dataset_version_id:
            raise ScaleoutError("registered feature DatasetVersion does not match scaleout unit")
        if record.partition_id != unit.partition_id:
            raise ScaleoutError("registered feature partition does not match scaleout unit")
        if record.value_store_format != ValueStoreFormat.PARQUET.value:
            raise ScaleoutError("registered feature is not Parquet-backed")
        if record.parquet_path != parquet_path:
            raise ScaleoutError("registered feature Parquet path does not match materialization")
        if not record.value_content_hash:
            raise ScaleoutError("registered feature is missing value_content_hash")
        if content_hash is not None and record.value_content_hash != content_hash:
            raise ScaleoutError("registered feature content hash does not match materialization")
        if not record.value_schema_version:
            raise ScaleoutError("registered feature is missing value_schema_version")
        if value_schema_version is not None and record.value_schema_version != value_schema_version:
            raise ScaleoutError(
                "registered feature value schema version does not match materialization"
            )


def _verify_label_registry_roundtrip(
    unit: ScaleoutUnit,
    *,
    alpha_data_root: Path,
    label_version_ids: tuple[str, ...],
    parquet_path: str,
    content_hash: str,
    value_schema_version: str | None = None,
) -> None:
    from alpha_system.labels.registry import LabelRegistry

    registry = LabelRegistry.from_alpha_data_root(alpha_data_root)
    for label_version_id in label_version_ids:
        record = registry.resolve_label(label_version_id)
        if record is None:
            raise ScaleoutError(f"registered label did not resolve: {label_version_id}")
        if record.dataset_version_id != unit.dataset_version_id:
            raise ScaleoutError("registered label DatasetVersion does not match scaleout unit")
        if record.partition_id != unit.partition_id:
            raise ScaleoutError("registered label partition does not match scaleout unit")
        if record.value_store_format != ValueStoreFormat.PARQUET.value:
            raise ScaleoutError("registered label is not Parquet-backed")
        if record.parquet_path != parquet_path:
            raise ScaleoutError("registered label Parquet path does not match materialization")
        if not record.value_content_hash:
            raise ScaleoutError("registered label is missing value_content_hash")
        if record.value_content_hash != content_hash:
            raise ScaleoutError("registered label content hash does not match materialization")
        if not record.value_schema_version:
            raise ScaleoutError("registered label is missing value_schema_version")
        if value_schema_version and record.value_schema_version != value_schema_version:
            raise ScaleoutError(
                "registered label value schema version does not match materialization"
            )


def _completed_record_is_valid(record: ScaleoutUnitRecord) -> bool:
    return bool(
        record.parquet_path
        and record.content_hash
        and record.row_count > 0
        and record.status == "completed"
    )


def _record_from_payload(payload: Mapping[str, object]) -> ScaleoutUnitRecord:
    unit = ScaleoutUnit(
        unit_id=_require_text(payload.get("unit_id"), "unit_id"),
        family=_require_text(payload.get("family"), "family"),
        schema_id=_require_text(payload.get("schema"), "schema"),
        symbol=_require_text(payload.get("symbol"), "symbol"),
        year=_positive_int(payload.get("year"), "year"),
        dataset_version_id=_require_text(payload.get("dataset_version_id"), "dataset_version_id"),
        acceptance_state=_require_text(payload.get("acceptance_state"), "acceptance_state"),
        acceptance_state_source=_require_text(
            payload.get("acceptance_state_source"),
            "acceptance_state_source",
        ),
        partition_id=_require_text(payload.get("partition_id"), "partition_id"),
        window_start_ts=_require_text(payload.get("window_start_ts"), "window_start_ts"),
        window_end_ts=_require_text(payload.get("window_end_ts"), "window_end_ts"),
        feature_set_id=_require_text(
            _require_mapping(payload.get("feature_set"), "feature_set").get("feature_set_id"),
            "feature_set_id",
        ),
        feature_set_version=_require_text(
            _require_mapping(payload.get("feature_set"), "feature_set").get("feature_set_version"),
            "feature_set_version",
        ),
        feature_names=tuple(
            _require_text(value, "feature")
            for value in _sequence(
                _require_mapping(payload.get("feature_set"), "feature_set").get("features"),
                "feature_set.features",
            )
        ),
        horizon=_optional_text(payload.get("horizon")) or "",
        input_datasets=_input_datasets_from_payload(payload),
    )
    return ScaleoutUnitRecord(
        unit=unit,
        status=_require_text(payload.get("status"), "status"),
        stage=_require_text(payload.get("stage"), "stage"),
        parquet_path=_optional_text(payload.get("parquet_path")),
        content_hash=_optional_text(payload.get("content_hash")),
        row_count=int(payload.get("row_count", 0)),
        feature_version_ids=tuple(
            _require_text(value, "feature_version_id")
            for value in _sequence(payload.get("feature_version_ids", ()), "feature_version_ids")
        ),
        label_version_ids=tuple(
            _require_text(value, "label_version_id")
            for value in _sequence(payload.get("label_version_ids", ()), "label_version_ids")
        ),
        message=str(payload.get("message", "")),
    )


def _input_datasets_from_payload(payload: Mapping[str, object]) -> tuple[ScaleoutInputDataset, ...]:
    raw = payload.get("input_datasets", ())
    if raw in (None, ()):
        return ()
    return tuple(
        ScaleoutInputDataset(
            schema_id=_require_text(
                _require_mapping(value, "input_datasets[]").get("schema"),
                "input_datasets[].schema",
            ),
            dataset_version_id=_require_text(
                _require_mapping(value, "input_datasets[]").get("dataset_version_id"),
                "input_datasets[].dataset_version_id",
            ),
            acceptance_state=_require_text(
                _require_mapping(value, "input_datasets[]").get("acceptance_state"),
                "input_datasets[].acceptance_state",
            ),
            acceptance_state_source=_require_text(
                _require_mapping(value, "input_datasets[]").get("acceptance_state_source"),
                "input_datasets[].acceptance_state_source",
            ),
        )
        for value in _sequence(raw, "input_datasets")
    )


def _value_store_handles(summary: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    handles = summary.get("value_store_handles")
    if isinstance(handles, Sequence) and not isinstance(handles, str):
        return tuple(_require_mapping(handle, "value_store_handles[]") for handle in handles)
    handle = summary.get("value_store_handle")
    if handle is None:
        return ()
    return (_require_mapping(handle, "value_store_handle"),)


def _acceptance_states_from_summary(path: Path) -> dict[tuple[str, int, str], str]:
    states: dict[tuple[str, int, str], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _ACCEPTANCE_ROW_RE.match(line)
        if match is None:
            continue
        states[
            (
                match.group("schema"),
                int(match.group("year")),
                match.group("dataset"),
            )
        ] = match.group("state")
    return states


def _state_for_unit(
    schema_id: str,
    year: int,
    dataset_version_id: str,
    *,
    summary_states: Mapping[tuple[str, int, str], str],
    inventory_state: object,
) -> tuple[str, str]:
    summary_state = summary_states.get((schema_id, year, dataset_version_id))
    if summary_state:
        return summary_state, "acceptance_summary"
    return _require_text(inventory_state, "committed_summary_state"), "dataset_inventory"


def _partial_year_end_ts(policy_path: Path) -> dict[int, str]:
    if not policy_path.exists():
        return {}
    policy = _load_json_mapping(policy_path, "dataset acceptance policy")
    raw = policy.get("partial_year_end_ts", {})
    if not isinstance(raw, Mapping):
        return {}
    return {int(year): _require_text(value, "partial_year_end_ts") for year, value in raw.items()}


def _selected_feature_names(
    config: ScaleoutConfig,
    target: ScaleoutTarget,
) -> tuple[str, ...]:
    if target.label_targeted:
        return ()
    if not target.feature_ids and not target.feature_groups:
        return config.feature_names
    selected: set[str] = set()
    known_features = set(config.feature_names)
    unknown_features = sorted(set(target.feature_ids).difference(known_features))
    if unknown_features:
        raise ScaleoutError("unknown feature_id target(s): " + ", ".join(unknown_features))
    selected.update(target.feature_ids)
    for group in target.feature_groups:
        if group not in config.feature_groups:
            raise ScaleoutError(f"unknown feature_group target: {group}")
        selected.update(config.feature_groups[group])
    return tuple(name for name in config.feature_names if name in selected)


def _selected_label_names(
    config: ScaleoutConfig,
    target: ScaleoutTarget,
) -> tuple[str, ...]:
    if target.feature_ids or target.feature_groups:
        return ()
    if not target.label_ids and not target.label_groups and not target.horizon_groups:
        return config.label_names
    selected: set[str] = set()
    known_labels = set(config.label_names)
    unknown_labels = sorted(set(target.label_ids).difference(known_labels))
    if unknown_labels:
        raise ScaleoutError("unknown label_id target(s): " + ", ".join(unknown_labels))
    selected.update(target.label_ids)
    for group in target.label_groups:
        if group not in config.label_groups:
            raise ScaleoutError(f"unknown label_group target: {group}")
        selected.update(config.label_groups[group])
    horizon_selected = set(_label_names_for_horizon_groups(config, target.horizon_groups))
    if target.horizon_groups:
        selected = selected.intersection(horizon_selected) if selected else horizon_selected
    return tuple(name for name in config.label_names if name in selected)


def _selected_names_for_config(
    config: ScaleoutConfig,
    target: ScaleoutTarget,
) -> tuple[str, ...]:
    if _is_label_scaleout_config(config):
        return _selected_label_names(config, target)
    return _selected_feature_names(config, target)


def _is_label_scaleout_config(config: ScaleoutConfig) -> bool:
    return bool(config.label_names and not config.feature_names)


def _scaleout_label_names(family: str, raw_names: tuple[str, ...]) -> tuple[str, ...]:
    if family == "cost_adjusted":
        from alpha_system.labels.fast import COST_ADJUSTED_LABEL_IDS

        return COST_ADJUSTED_LABEL_IDS
    return raw_names


def _label_horizon_groups(
    label_names: tuple[str, ...],
    configured: object,
) -> Mapping[str, tuple[str, ...]]:
    groups: dict[str, tuple[str, ...]] = {}
    if configured is not None:
        groups.update(
            _group_mapping(
                configured,
                "targeting.horizon_groups",
                allowed_names=label_names,
            )
        )
    label_set = set(label_names)
    base = tuple(
        name
        for name in label_names
        if _label_horizon_token(name) in {"1m", "3m", "5m", "10m", "15m", "30m"}
    )
    extended = tuple(
        name
        for name in label_names
        if _label_horizon_token(name) in {"60m", "120m", "240m"}
    )
    close_out = tuple(
        name
        for name in label_names
        if _label_horizon_token(name) in {"session_close", "maintenance_flat"}
    )
    if base:
        groups.setdefault("base", base)
        groups.setdefault("fixed", base)
    if extended:
        groups.setdefault("extended", extended)
    if close_out:
        groups.setdefault("close_out", close_out)
    if label_set:
        groups.setdefault("all", label_names)
    return groups


def _label_names_for_horizon_groups(
    config: ScaleoutConfig,
    horizon_groups: tuple[str, ...],
) -> tuple[str, ...]:
    if not horizon_groups:
        return config.label_names
    selected: set[str] = set()
    for group in horizon_groups:
        if group not in config.horizon_groups:
            raise ScaleoutError(f"unknown horizon_group target: {group}")
        selected.update(config.horizon_groups[group])
    return tuple(name for name in config.label_names if name in selected)


def _label_horizon_token(name: str) -> str:
    if name in {"session_close", "maintenance_flat"}:
        return name
    for prefix in ("mid_fwd_ret_", "fwd_ret_"):
        if name.startswith(prefix):
            return name.removeprefix(prefix)
    return name


def _selected_symbols(config: ScaleoutConfig, target: ScaleoutTarget) -> tuple[str, ...]:
    if not target.symbols:
        return config.symbols
    unknown_symbols = sorted(set(target.symbols).difference(config.symbols))
    if unknown_symbols:
        raise ScaleoutError("unknown symbol target(s): " + ", ".join(unknown_symbols))
    return tuple(symbol for symbol in config.symbols if symbol in target.symbols)


def _unit_symbols_for_config(config: ScaleoutConfig, target: ScaleoutTarget) -> tuple[str, ...]:
    selected = _selected_symbols(config, target)
    if config.family != "cross_market_alignment":
        return selected
    if not selected:
        return ()
    return ("_".join(symbol.upper() for symbol in config.symbols),)


def _selected_years(config: ScaleoutConfig, target: ScaleoutTarget) -> tuple[int, ...]:
    if not target.years:
        return config.years
    unknown_years = sorted(set(target.years).difference(config.years))
    if unknown_years:
        raise ScaleoutError(
            "unknown year target(s): " + ", ".join(str(year) for year in unknown_years)
        )
    return tuple(year for year in config.years if year in target.years)


def _dry_run_estimate(
    config: ScaleoutConfig,
    *,
    units: tuple[ScaleoutUnit, ...],
    planned_step_count: int,
) -> ScaleoutDryRunEstimate:
    rows_per_unit = config.row_budget_per_unit
    seconds_per_unit = config.estimated_seconds_per_unit
    return ScaleoutDryRunEstimate(
        selected_unit_count=len(units),
        planned_step_count=planned_step_count,
        symbol_count=len({unit.symbol for unit in units}),
        symbols=tuple(sorted({unit.symbol for unit in units})),
        year_count=len({unit.year for unit in units}),
        years=tuple(sorted({unit.year for unit in units})),
        dataset_version_ids=tuple(
            sorted(
                {
                    dataset.dataset_version_id
                    for unit in units
                    for dataset in _unit_input_datasets(unit)
                }
            )
        ),
        estimated_rows_per_unit=rows_per_unit,
        estimated_total_rows=rows_per_unit * len(units),
        estimated_seconds_per_unit=seconds_per_unit,
        estimated_total_seconds=round(seconds_per_unit * planned_step_count, 3),
        unit_estimates=tuple(
            {
                "unit_id": unit.unit_id,
                "family": unit.family,
                "symbol": unit.symbol,
                "year": unit.year,
                "dataset_version_id": unit.dataset_version_id,
                "feature_ids": list(unit.feature_names),
                "estimated_rows": rows_per_unit,
                "estimated_seconds": seconds_per_unit,
            }
            for unit in units
        ),
    )


def _bounded_units(units: tuple[ScaleoutUnit, ...], bounded_year: int) -> tuple[ScaleoutUnit, ...]:
    selected = tuple(unit for unit in units if unit.year == bounded_year)
    if selected:
        return selected
    full_years = sorted({unit.year for unit in units if unit.year < 2026}, reverse=True)
    if not full_years:
        return ()
    return tuple(unit for unit in units if unit.year == full_years[0])


def _planned_units_for_rollout(
    units: tuple[ScaleoutUnit, ...],
    bounded: tuple[ScaleoutUnit, ...],
    rollout: str,
) -> tuple[tuple[str, ScaleoutUnit], ...]:
    if rollout == "bounded-real":
        return tuple(("bounded_real", unit) for unit in bounded)
    if rollout == "full-window":
        return tuple(("full_window", unit) for unit in units)
    return tuple(("bounded_real", unit) for unit in bounded) + tuple(
        ("full_window", unit) for unit in units
    )


def _execution_stages(
    units: tuple[ScaleoutUnit, ...],
    bounded: tuple[ScaleoutUnit, ...],
    rollout: str,
) -> tuple[tuple[str, tuple[ScaleoutUnit, ...]], ...]:
    if rollout == "bounded-real":
        return (("bounded_real", bounded),)
    if rollout == "full-window":
        return (("full_window", units),)
    return (("bounded_real", bounded), ("full_window", units))


def _normalize_rollout(value: str) -> str:
    token = value.strip().lower().replace("_", "-")
    if token in {"bounded", "bounded-real"}:
        return "bounded-real"
    if token in {"full", "full-window"}:
        return "full-window"
    if token in {"bounded-then-full", "bounded-real-then-full", "all"}:
        return "bounded-then-full"
    raise ScaleoutError(
        "rollout must be one of: bounded-real, full-window, bounded-then-full"
    )


def _normalize_engine(value: str) -> str:
    token = value.strip().lower().replace("_", "-")
    if token == SCALEOUT_ENGINE_V1:
        return SCALEOUT_ENGINE_V1
    if token == SCALEOUT_ENGINE_REFERENCE:
        return SCALEOUT_ENGINE_REFERENCE
    raise ScaleoutError("engine must be one of: v1, reference")


def _normalize_workers(value: int | str | None) -> int:
    if value is None:
        return DEFAULT_CPU_WORKERS
    if isinstance(value, bool):
        raise ScaleoutError("workers must be a positive integer")
    try:
        workers = int(value)
    except (TypeError, ValueError) as exc:
        raise ScaleoutError("workers must be a positive integer") from exc
    if workers < 1:
        raise ScaleoutError("workers must be >= 1")
    return workers


def _normalize_force_recompute(value: bool | str | None) -> bool:
    if value is None:
        value = os.environ.get(FORCE_RECOMPUTE_ENV)
        if value is None:
            return False
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if token in {"", "0", "false", "f", "no", "n", "off"}:
        return False
    raise ScaleoutError(f"{FORCE_RECOMPUTE_ENV} must be a boolean-like value")


def _resolve_worker_plan(
    requested_workers: int,
    *,
    unit_count: int,
    parallel_allowed: bool,
) -> ScaleoutWorkerPlan:
    requested = _normalize_workers(requested_workers)
    cores = max(1, os.cpu_count() or 1)
    effective = requested
    reductions: list[str] = []
    if not parallel_allowed and requested > 1:
        effective = 1
        reductions.append("parallel worker compute is not active for this run")
    if effective > cores:
        reductions.append(
            f"requested workers {effective} reduced to available cores {cores}"
        )
        effective = cores
    if unit_count > 0 and effective > unit_count:
        reductions.append(
            f"requested workers {effective} reduced to runnable unit count {unit_count}"
        )
        effective = unit_count
    if unit_count == 0 and effective > 1:
        reductions.append("requested workers reduced to 1 because no units are runnable")
        effective = 1
    effective = max(1, effective)
    return ScaleoutWorkerPlan(
        requested_workers=requested,
        effective_workers=effective,
        threads_per_worker=max(1, cores // effective),
        available_cores=cores,
        reductions=tuple(reductions),
    )


def _log_worker_reductions(
    worker_plan: ScaleoutWorkerPlan,
    log: Callable[[str], None] | None,
) -> None:
    if log is None:
        return
    for reduction in worker_plan.reductions:
        log(f"scaleout worker reduction: {reduction}")


def _alpha_data_root(value: str | Path | None) -> Path:
    root_value = value if value is not None else os.environ.get("ALPHA_DATA_ROOT")
    if root_value is None:
        raise ScaleoutError("ALPHA_DATA_ROOT or --alpha-data-root is required with --execute")
    root = Path(root_value).expanduser().resolve(strict=False)
    repo_root = Path.cwd().resolve(strict=False)
    if root == repo_root or root.is_relative_to(repo_root):
        raise ScaleoutError("ALPHA_DATA_ROOT must be outside the repository tree")
    return root


def _canonical_root(value: str | Path | None) -> Path:
    # Feature-layer code stays provider-agnostic: the canonical root is resolved
    # and supplied by the orchestration/CLI layer (see cli/scaleout.py), never
    # constructed here. This keeps the no-raw-provider boundary intact.
    if value is None:
        raise ScaleoutError(
            "canonical_root is required; the orchestration layer must resolve and "
            "pass the canonical Parquet root (it is not constructed in feature code)"
        )
    return Path(value).expanduser().resolve(strict=False)


def _required_path(value: str | Path | None, field_name: str) -> Path:
    if value is None:
        raise ScaleoutError(f"{field_name} is required with --execute")
    return Path(value).expanduser().resolve(strict=False)


def _load_json_mapping(path: Path, object_name: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScaleoutError(f"{object_name} could not be read: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScaleoutError(f"{object_name} is not valid JSON: {path}") from exc
    return _require_mapping(payload, object_name)


def _repo_path(value: object, field_name: str, *, repo_root: Path) -> Path:
    text = _require_text(value, field_name)
    path = Path(text)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve(strict=False)


def _optional_repo_path(value: object) -> Path | None:
    if value is None:
        return None
    path = Path(_require_text(value, "repo path"))
    if not path.is_absolute():
        path = Path.cwd().resolve(strict=False) / path
    return path.resolve(strict=False)


def _render_partition(template: str, *, symbol: str, year: int, horizon: str = "") -> str:
    rendered = template.format(
        symbol=symbol,
        target_symbol=symbol,
        year=year,
        horizon=horizon,
    )
    # partition_id must be a valid identifier for data/foundation/datasets.py
    # (_normalize_id allows only alphanumeric, underscore, and hyphen). The config
    # templates use dotted segments (e.g. "ES.2024.full_year"); normalize the
    # dotted/whitespace separators to underscores generically so every current and
    # future family (and label) config that reuses the dotted pattern resolves to a
    # valid identifier without per-config edits.
    sanitized = re.sub(r"[^0-9A-Za-z_-]+", "_", rendered).strip("_")
    if not sanitized:
        raise ScaleoutError(f"rendered partition id is empty after sanitization: {rendered!r}")
    return sanitized


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    return _require_mapping(value, field_name)


def _group_mapping(
    value: object,
    field_name: str,
    *,
    allowed_names: tuple[str, ...],
) -> Mapping[str, tuple[str, ...]]:
    if value is None:
        return {}
    raw = _require_mapping(value, field_name)
    allowed = set(allowed_names)
    groups: dict[str, tuple[str, ...]] = {}
    for group_name, raw_members in raw.items():
        group = _require_text(group_name, f"{field_name}.key")
        members = _text_tuple(raw_members, f"{field_name}.{group}")
        unknown = sorted(set(members).difference(allowed))
        if unknown:
            raise ScaleoutError(
                f"{field_name}.{group} references unknown name(s): " + ", ".join(unknown)
            )
        groups[group] = members
    return groups


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        raise ScaleoutError(f"{field_name} must be a mapping")
    return value


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ScaleoutError(f"{field_name} must be a sequence")
    return value


def _text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    values = tuple(_require_text(item, field_name) for item in _sequence(value, field_name))
    if not values:
        raise ScaleoutError(f"{field_name} must not be empty")
    return values


def _optional_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    return _text_tuple(value, field_name)


def _int_tuple(value: object, field_name: str) -> tuple[int, ...]:
    values = tuple(_positive_int(item, field_name) for item in _sequence(value, field_name))
    if not values:
        raise ScaleoutError(f"{field_name} must not be empty")
    return values


def _optional_bool(value: object, field_name: str, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ScaleoutError(f"{field_name} must be a boolean")
    return value


def _optional_positive_int(value: object, field_name: str, *, default: int) -> int:
    if value is None:
        return default
    return _positive_int(value, field_name)


def _optional_float(value: object, field_name: str, *, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ScaleoutError(f"{field_name} must be a non-negative number")
    number = float(value)
    if number < 0:
        raise ScaleoutError(f"{field_name} must be a non-negative number")
    return round(number, 3)


def _default_seconds_per_unit(row_budget_per_unit: int) -> float:
    if row_budget_per_unit <= 0:
        return 0.0
    return round(max(1.0, row_budget_per_unit / 100_000.0), 3)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ScaleoutError(f"{field_name} must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise ScaleoutError(f"{field_name} must be a non-empty single-line string")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _require_text(value, "optional text")


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScaleoutError(f"{field_name} must be a positive integer")
    if value <= 0:
        raise ScaleoutError(f"{field_name} must be a positive integer")
    return value
