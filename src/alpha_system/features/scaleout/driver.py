"""Restart-safe scaleout driver for governed FeaturePack materialization.

The driver is deliberately thin. Family formulas stay in the approved feature
family modules, canonical rows are loaded through the sanctioned loader used by
the seed operator, and registry writes go through ``FeatureStore`` via
``run_seed_feature_pack``.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.foundation.datasets import (
    DatasetAcceptanceState,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.store import FeatureStore
from alpha_system.governance.serialization import canonical_serialize

SCALEOUT_CONFIG_SCHEMA = "alpha_system.futures_substrate_scaleout.feature_scaleout_config.v1"
DEFAULT_SCALEOUT_CONFIG = "configs/features/scaleout/base_ohlcv.json"
DEFAULT_POLICY_CONFIG = "configs/data/dataset_acceptance/futsub_p02_policy.json"
DEFAULT_ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
DEFAULT_BOUNDED_YEAR = 2024
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
class ScaleoutConfig:
    """Parsed feature scaleout configuration."""

    config_path: Path
    campaign_id: str
    phase_id: str
    family: str
    feature_names: tuple[str, ...]
    symbols: tuple[str, ...]
    years: tuple[int, ...]
    input_schemas: tuple[str, ...]
    dense_grid_required: bool
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
    input_datasets: tuple[ScaleoutInputDataset, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible unit summary."""

        return {
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


@dataclass(frozen=True, slots=True)
class MaterializedUnitEvidence:
    """Value-free evidence returned by one completed unit materialization."""

    parquet_path: str
    content_hash: str
    row_count: int
    feature_version_ids: tuple[str, ...] = ()


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
class ScaleoutRunSummary:
    """Summary for a scaleout plan or execution run."""

    campaign_id: str
    phase_id: str
    family: str
    rollout: str
    dry_run: bool
    bounded_year: int
    accepted_unit_count: int
    bounded_unit_count: int
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
            "rollout": self.rollout,
            "dry_run": self.dry_run,
            "bounded_year": self.bounded_year,
            "accepted_unit_count": self.accepted_unit_count,
            "bounded_unit_count": self.bounded_unit_count,
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
    if payload.get("schema") != SCALEOUT_CONFIG_SCHEMA:
        raise ScaleoutError(f"scaleout config schema must be {SCALEOUT_CONFIG_SCHEMA}")

    grid = _require_mapping(payload.get("batch_unit_grid"), "batch_unit_grid")
    dataset_selection = _require_mapping(payload.get("dataset_selection"), "dataset_selection")
    value_store = _require_mapping(payload.get("value_store"), "value_store")
    checkpoint = _require_mapping(payload.get("checkpoint"), "checkpoint")
    identity = _require_mapping(payload.get("identity"), "identity")

    repo_root = Path.cwd().resolve(strict=False)
    value_store_format = ValueStoreFormat(_require_text(value_store.get("format"), "value_store.format"))
    if value_store_format is not ValueStoreFormat.PARQUET:
        raise ScaleoutError("scaleout research-scale value_store.format must be parquet")

    checkpoint_root = Path(_require_text(checkpoint.get("checkpoint_root"), "checkpoint_root"))
    return ScaleoutConfig(
        config_path=config_path,
        campaign_id=_require_text(payload.get("campaign_id"), "campaign_id"),
        phase_id=_require_text(payload.get("phase_id"), "phase_id"),
        family=_require_text(payload.get("family"), "family"),
        feature_names=_text_tuple(payload.get("governed_scope"), "governed_scope"),
        symbols=_text_tuple(grid.get("symbols"), "batch_unit_grid.symbols"),
        years=_int_tuple(grid.get("years"), "batch_unit_grid.years"),
        input_schemas=_text_tuple(grid.get("input_schemas"), "batch_unit_grid.input_schemas"),
        dense_grid_required=_optional_bool(
            grid.get("dense_grid_required"),
            "batch_unit_grid.dense_grid_required",
            default=False,
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


def build_scaleout_units(config: ScaleoutConfig) -> tuple[ScaleoutUnit, ...]:
    """Build the accepted family x symbol x year grid from value-free locks."""

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
    for year in config.years:
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
        primary = _primary_input_dataset(config, tuple(input_datasets))
        for symbol in config.symbols:
            partition_id = _render_partition(config.partition_template, symbol=symbol, year=year)
            feature_set_id = f"feature_set_futures_scaleout_{config.family}"
            feature_set_version = f"v1_{symbol.lower()}_{year}"
            unit_payload = _unit_identity_payload(
                config,
                symbol=symbol,
                year=year,
                primary=primary,
                input_datasets=tuple(input_datasets),
                feature_set_id=feature_set_id,
                feature_set_version=feature_set_version,
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
                    feature_set_id=feature_set_id,
                    feature_set_version=feature_set_version,
                    feature_names=config.feature_names,
                    input_datasets=tuple(input_datasets),
                )
            )
    return tuple(sorted(units, key=lambda item: (item.year, item.symbol, item.schema_id)))


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
    if len(input_datasets) > 1:
        payload["input_dataset_versions"] = [dataset.to_dict() for dataset in input_datasets]
    return payload


def run_scaleout(
    config: ScaleoutConfig,
    *,
    alpha_data_root: str | Path | None = None,
    dataset_registry_path: str | Path | None = None,
    canonical_root: str | Path | None = None,
    rollout: str = "bounded-then-full",
    execute: bool = False,
    bounded_year: int | None = None,
    unit_executor: UnitExecutor | None = None,
) -> ScaleoutRunSummary:
    """Plan or execute scaleout units.

    Execution is serial. Bounded-then-full runs the bounded accepted year first;
    full-window expansion is skipped when any bounded unit fails.
    """

    rollout_token = _normalize_rollout(rollout)
    units = build_scaleout_units(config)
    bounded = _bounded_units(units, bounded_year or config.bounded_year)
    records: list[ScaleoutUnitRecord] = []

    if not execute:
        planned = _planned_units_for_rollout(units, bounded, rollout_token)
        records.extend(
            _preview_record(config, unit, stage=stage)
            for stage, unit in planned
        )
        return ScaleoutRunSummary(
            campaign_id=config.campaign_id,
            phase_id=config.phase_id,
            family=config.family,
            rollout=rollout_token,
            dry_run=True,
            bounded_year=bounded_year or config.bounded_year,
            accepted_unit_count=len(units),
            bounded_unit_count=len(bounded),
            records=tuple(records),
        )

    alpha_root = _alpha_data_root(alpha_data_root)
    dataset_registry = _required_path(dataset_registry_path, "dataset_registry_path")
    canonical = _canonical_root(canonical_root)
    ledger = _ScaleoutLedger(alpha_root, config)
    executor = unit_executor or _unit_executor_for_family(config.family)

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
        )
        records.extend(stage_records)
        if stage == "bounded_real" and any(record.status == "failed" for record in stage_records):
            break

    return ScaleoutRunSummary(
        campaign_id=config.campaign_id,
        phase_id=config.phase_id,
        family=config.family,
        rollout=rollout_token,
        dry_run=False,
        bounded_year=bounded_year or config.bounded_year,
        accepted_unit_count=len(units),
        bounded_unit_count=len(bounded),
        records=tuple(records),
    )


def materialize_base_ohlcv_unit(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    alpha_data_root: Path,
    dataset_registry_path: Path,
    canonical_root: Path,
) -> MaterializedUnitEvidence:
    """Materialize one Base OHLCV unit through the sanctioned seed-pack path."""

    from alpha_system.cli.seed_pack import run_seed_feature_pack

    if config.family != "base_ohlcv" or unit.family != "base_ohlcv":
        raise ScaleoutError("FUTSUB-P06 executor supports only the base_ohlcv family")

    seed_config = _seed_config(config, unit)
    summary = run_seed_feature_pack(
        seed_config,
        alpha_data_root=alpha_data_root,
        canonical_root=canonical_root,
        datasets_registry_path=dataset_registry_path,
        repo_root=Path.cwd(),
        value_store_format=ValueStoreFormat.PARQUET,
    )
    handles = _value_store_handles(summary)
    if not handles:
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_paths = {
        _require_text(handle.get("parquet_path"), "value_store_handle.parquet_path")
        for handle in handles
    }
    content_hashes = {
        _require_text(handle.get("content_hash"), "value_store_handle.content_hash")
        for handle in handles
    }
    value_counts = [
        _positive_int(handle.get("value_count"), "value_store_handle.value_count")
        for handle in handles
    ]
    if len(parquet_paths) != 1:
        raise ScaleoutError("unit produced multiple Parquet paths")
    if len(content_hashes) != 1:
        raise ScaleoutError("unit produced multiple content hashes")
    feature_version_ids = tuple(
        _require_text(value, "feature_version_id")
        for value in _sequence(summary.get("feature_version_ids"), "feature_version_ids")
    )
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=feature_version_ids,
        parquet_path=next(iter(parquet_paths)),
    )
    return MaterializedUnitEvidence(
        parquet_path=next(iter(parquet_paths)),
        content_hash=next(iter(content_hashes)),
        row_count=sum(value_counts),
        feature_version_ids=feature_version_ids,
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
    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.contracts import FeatureSetSpec
    from alpha_system.features.engine.materialization import (
        FeatureMaterializationInputs,
        build_feature_materialization_plan,
        materialize_features,
    )
    from alpha_system.features.store import FeatureStore

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
        quality_coverage_builder=None,
        repo_root=Path.cwd(),
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    definitions = _session_feature_definitions(config, unit, store.registry)
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(definition.spec.feature_spec for definition in definitions),
        description="FUTSUB-P07 session/calendar/maintenance FeaturePack scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "point_in_time_session_metadata_guard": "enforced",
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    governance_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "point_in_time_session_metadata_guard": "enforced",
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    plan = build_feature_materialization_plan(
        feature_set,
        context.accepted,
        partition_id=unit.partition_id,
        alpha_data_root=alpha_data_root,
        governance_metadata=governance_metadata,
        output_namespace=config.value_namespace,
    )
    inputs = FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=() if config.dense_grid_required else context.bar_rows,
        dense_grid_bar_rows=context.bar_rows if config.dense_grid_required else (),
        governance_metadata=governance_metadata,
    )
    result = materialize_features(
        plan,
        inputs,
        definitions,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no session feature values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    feature_version_ids: list[str] = []
    for definition in definitions:
        checked_request = definition.request_gate_decision.checked_feature_request
        if checked_request is None:
            raise ScaleoutError("session FeatureRequest gate did not return a checked request")
        record = store.register_materialized_feature(
            result,
            feature_spec=definition.spec.feature_spec,
            feature_version=definition.version,
            feature_request=checked_request,
            registry_metadata=governance_metadata,
        )
        feature_version_ids.append(record.feature_version_id)
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=tuple(feature_version_ids),
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        feature_version_ids=tuple(feature_version_ids),
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
    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.contracts import FeatureSetSpec
    from alpha_system.features.engine.materialization import (
        FeatureMaterializationInputs,
        build_feature_materialization_plan,
        materialize_features,
    )
    from alpha_system.features.store import FeatureStore

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
        quality_coverage_builder=None,
        repo_root=Path.cwd(),
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    definitions = _vwap_session_auction_feature_definitions(config, unit, store.registry)
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(definition.spec for definition in definitions),
        description="FUTSUB-P08 VWAP / session-auction FeaturePack scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "running_vwap_point_in_time_guard": "enforced",
            "final_session_aggregate_intraday_use": "forbidden",
            "feature_bindings": [_vwap_binding_metadata(binding) for binding in bindings],
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    governance_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "running_vwap_point_in_time_guard": "enforced",
        "final_session_aggregate_intraday_use": "forbidden",
        "feature_bindings": [_vwap_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    plan = build_feature_materialization_plan(
        feature_set,
        context.accepted,
        partition_id=unit.partition_id,
        alpha_data_root=alpha_data_root,
        governance_metadata=governance_metadata,
        output_namespace=config.value_namespace,
    )
    inputs = FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
        governance_metadata=governance_metadata,
    )
    result = materialize_features(
        plan,
        inputs,
        definitions,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no VWAP/session feature values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    feature_version_ids: list[str] = []
    for definition in definitions:
        checked_request = definition.request_gate_decision.checked_feature_request
        if checked_request is None:
            raise ScaleoutError("VWAP/session FeatureRequest gate did not return a checked request")
        record = store.register_materialized_feature(
            result,
            feature_spec=definition.spec,
            feature_version=definition.version,
            feature_request=checked_request,
            registry_metadata=governance_metadata,
        )
        feature_version_ids.append(record.feature_version_id)
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=tuple(feature_version_ids),
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        feature_version_ids=tuple(feature_version_ids),
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
    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.contracts import FeatureSetSpec, FeatureSpec
    from alpha_system.features.engine.materialization import (
        FeatureMaterializationInputs,
        build_feature_materialization_plan,
        materialize_features,
    )
    from alpha_system.features.store import FeatureStore

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
        quality_coverage_builder=None,
        repo_root=Path.cwd(),
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    definitions = _regime_volatility_compression_feature_definitions(
        config,
        unit,
        store.registry,
    )
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(_definition_feature_spec(definition) for definition in definitions),
        description="FUTSUB-P09 regime / volatility / compression FeaturePack scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "available_ts_regime_guard": "enforced",
            "feature_bindings": [_regime_binding_metadata(binding) for binding in bindings],
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    governance_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "available_ts_regime_guard": "enforced",
        "feature_bindings": [_regime_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    plan = build_feature_materialization_plan(
        feature_set,
        context.accepted,
        partition_id=unit.partition_id,
        alpha_data_root=alpha_data_root,
        governance_metadata=governance_metadata,
        output_namespace=config.value_namespace,
    )
    inputs = FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
        governance_metadata=governance_metadata,
    )
    result = materialize_features(
        plan,
        inputs,
        definitions,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no regime feature values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    feature_version_ids: list[str] = []
    for definition in definitions:
        checked_request = definition.request_gate_decision.checked_feature_request
        if checked_request is None:
            raise ScaleoutError("regime FeatureRequest gate did not return a checked request")
        feature_spec = _definition_feature_spec(definition)
        if not isinstance(feature_spec, FeatureSpec):
            raise ScaleoutError("regime definition did not expose a FeatureSpec")
        record = store.register_materialized_feature(
            result,
            feature_spec=feature_spec,
            feature_version=definition.version,
            feature_request=checked_request,
            registry_metadata=governance_metadata,
        )
        feature_version_ids.append(record.feature_version_id)
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=tuple(feature_version_ids),
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        feature_version_ids=tuple(feature_version_ids),
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
    from alpha_system.core.value_store import ValueStoreHandle
    from alpha_system.features.contracts import FeatureSetSpec, FeatureSpec
    from alpha_system.features.engine.materialization import (
        FeatureMaterializationInputs,
        build_feature_materialization_plan,
        materialize_features,
    )
    from alpha_system.features.store import FeatureStore

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
        quality_coverage_builder=None,
        repo_root=Path.cwd(),
    )

    store = FeatureStore.from_alpha_data_root(alpha_data_root)
    definitions = _liquidity_pa_structure_feature_definitions(
        config,
        unit,
        store.registry,
    )
    feature_set = FeatureSetSpec(
        feature_set_id=unit.feature_set_id,
        feature_set_version=unit.feature_set_version,
        features=tuple(_definition_feature_spec(definition) for definition in definitions),
        description="FUTSUB-P10 liquidity-sweep / PA-structure FeaturePack scaleout unit",
        metadata={
            "campaign_id": config.campaign_id,
            "phase_id": config.phase_id,
            "family": config.family,
            "objective_pa_guard": "enforced",
            "subjective_pa_encoding": "forbidden",
            "feature_bindings": [_liquidity_pa_binding_metadata(binding) for binding in bindings],
            "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
        },
    )
    governance_metadata = {
        "campaign_id": config.campaign_id,
        "phase_id": config.phase_id,
        "unit_id": unit.unit_id,
        "family": config.family,
        "objective_pa_guard": "enforced",
        "subjective_pa_encoding": "forbidden",
        "feature_bindings": [_liquidity_pa_binding_metadata(binding) for binding in bindings],
        "input_dataset_versions": [dataset.to_dict() for dataset in unit.input_datasets],
    }
    plan = build_feature_materialization_plan(
        feature_set,
        context.accepted,
        partition_id=unit.partition_id,
        alpha_data_root=alpha_data_root,
        governance_metadata=governance_metadata,
        output_namespace=config.value_namespace,
    )
    inputs = FeatureMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
        governance_metadata=governance_metadata,
    )
    result = materialize_features(
        plan,
        inputs,
        definitions,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    if result.record_count == 0:
        raise ScaleoutError(f"unit {unit.unit_id} produced no liquidity/PA feature values")
    handle = result.value_store_handle
    if not isinstance(handle, ValueStoreHandle):
        raise ScaleoutError(f"unit {unit.unit_id} did not return a value-store handle")
    parquet_path = _require_text(handle.parquet_path, "value_store_handle.parquet_path")
    content_hash = _require_text(handle.content_hash, "value_store_handle.content_hash")
    feature_version_ids: list[str] = []
    for definition in definitions:
        checked_request = definition.request_gate_decision.checked_feature_request
        if checked_request is None:
            raise ScaleoutError("liquidity/PA FeatureRequest gate did not return a checked request")
        feature_spec = _definition_feature_spec(definition)
        if not isinstance(feature_spec, FeatureSpec):
            raise ScaleoutError("liquidity/PA definition did not expose a FeatureSpec")
        record = store.register_materialized_feature(
            result,
            feature_spec=feature_spec,
            feature_version=definition.version,
            feature_request=checked_request,
            registry_metadata=governance_metadata,
        )
        feature_version_ids.append(record.feature_version_id)
    _verify_feature_registry_roundtrip(
        unit,
        alpha_data_root=alpha_data_root,
        feature_version_ids=tuple(feature_version_ids),
        parquet_path=parquet_path,
        content_hash=content_hash,
        value_schema_version=handle.schema_version,
    )
    return MaterializedUnitEvidence(
        parquet_path=parquet_path,
        content_hash=content_hash,
        row_count=handle.value_count,
        feature_version_ids=tuple(feature_version_ids),
    )


def _unit_executor_for_family(family: str) -> UnitExecutor:
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
    raise ScaleoutError(f"unsupported scaleout family: {family}")


def render_scaleout_summary_markdown(summary: ScaleoutRunSummary) -> str:
    """Render a compact value-free Markdown summary."""

    states: dict[str, int] = {}
    for record in summary.records:
        states[record.unit.acceptance_state] = states.get(record.unit.acceptance_state, 0) + 1
    lines = [
        f"# {summary.family} Scaleout Summary",
        "",
        "Value-free scaleout summary. It contains no raw rows, canonical values,",
        "feature values, provider responses, SQLite content, or Parquet payloads.",
        "",
        f"- Campaign: `{summary.campaign_id}`",
        f"- Phase: `{summary.phase_id}`",
        f"- Rollout: `{summary.rollout}`",
        f"- Dry run: `{'yes' if summary.dry_run else 'no'}`",
        f"- Accepted unit count: `{summary.accepted_unit_count}`",
        f"- Bounded-real year: `{summary.bounded_year}`",
        f"- Bounded-real unit count: `{summary.bounded_unit_count}`",
        f"- Planned: `{summary.planned_count}`",
        f"- Completed: `{summary.completed_count}`",
        f"- Skipped: `{summary.skipped_count}`",
        f"- Failed: `{summary.failed_count}`",
        "",
        "## Acceptance States",
        "",
        "| State | Unit count |",
        "| --- | ---: |",
    ]
    for state in sorted(states):
        lines.append(f"| `{state}` | {states[state]} |")
    lines.extend(
        [
            "",
            "## Window Policy",
            "",
            "- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.",
            "- Dataset-level fallback is used for 2018: the blocked 2018 `ohlcv_1m`",
            "  DatasetVersion is excluded rather than fabricating per-symbol acceptance.",
            "- 2019 warning metadata and 2026 partial-year warning metadata are preserved",
            "  through the accepted/warned DatasetVersion state.",
            "- Multi-input units require every configured input schema/year to carry an",
            "  accepted or accepted-with-warnings DatasetVersion before execution.",
            "",
            "## Point-In-Time Guard",
            "",
            "- Feature values are emitted at the current source row `available_ts`.",
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
) -> tuple[ScaleoutUnitRecord, ...]:
    records: list[ScaleoutUnitRecord] = []
    for unit in units:
        completed = ledger.latest_completed(unit)
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
                message=(
                    "completed unit skipped from local ledger"
                    if status == "skipped"
                    else completed.message
                ),
            )
            records.append(record)
            continue
        try:
            _require_persisted_acceptance_lock(unit, dataset_registry_path)
            evidence = executor(config, unit, alpha_data_root, dataset_registry_path, canonical_root)
            record = ScaleoutUnitRecord(
                unit=unit,
                status="completed",
                stage=stage,
                parquet_path=evidence.parquet_path,
                content_hash=evidence.content_hash,
                row_count=evidence.row_count,
                feature_version_ids=evidence.feature_version_ids,
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
        records.append(record)
    return tuple(records)


def _preview_record(config: ScaleoutConfig, unit: ScaleoutUnit, *, stage: str) -> ScaleoutUnitRecord:
    try:
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
    raise ScaleoutError(f"unsupported scaleout family: {config.family}")


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


def _feature_window(name: str) -> int:
    if name in {"rolling_volatility", "rolling_range", "range_position", "volume_zscore"}:
        return 20
    return 1


def _session_bar_row_loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
    from alpha_system.data.foundation.canonical_loader import load_canonical_ohlcv_rows

    return load_canonical_ohlcv_rows(**kwargs)


def _session_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    from alpha_system.features.families.session import (
        SessionFeatureName,
        build_session_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )
    definitions = []
    for feature_name in unit.feature_names:
        name = SessionFeatureName(feature_name)
        definitions.append(
            build_session_feature_definition(
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
        )
    return tuple(definitions)


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
    exposure_family = f"{config.family}_{feature_name}"
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


def _vwap_session_auction_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    from alpha_system.features.families.ohlcv import (
        OHLCVFeatureName,
        build_ohlcv_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )
    definitions = []
    for binding in _vwap_session_auction_bindings(unit.feature_names):
        name = OHLCVFeatureName(binding.ohlcv_name)
        definitions.append(
            build_ohlcv_feature_definition(
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
        )
    return tuple(definitions)


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
    exposure_family = f"{config.family}_{binding.exposure_name}"
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


def _regime_volatility_compression_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
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
    definitions = []
    for binding in _regime_volatility_compression_bindings(unit.feature_names):
        input_scope = {
            "symbol": unit.symbol.upper(),
            "partition_id": unit.partition_id,
            "partition_schema": unit.schema_id,
            "feature_pack_family": config.family,
            "config_feature_name": binding.config_name,
        }
        if binding.primitive_family == "ohlcv":
            definitions.append(
                build_ohlcv_feature_definition(
                    OHLCVFeatureName(binding.primitive_name),
                    _regime_volatility_compression_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    horizon=binding.horizon,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            )
        elif binding.primitive_family == "structure":
            definitions.append(
                build_structure_feature_definition(
                    StructureFeatureName(binding.primitive_name),
                    _regime_volatility_compression_feature_request(config, unit, binding),
                    registry_reader,
                    dataset_version_ids=dataset_version_ids,
                    window_length=binding.window_length,
                    reset_on_session=True,
                    input_scope=input_scope,
                )
            )
        else:
            raise ScaleoutError(f"unsupported regime primitive family: {binding.primitive_family}")
    return tuple(definitions)


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
    exposure_family = f"{config.family}_{binding.exposure_name}"
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


def _liquidity_pa_structure_feature_definitions(
    config: ScaleoutConfig,
    unit: ScaleoutUnit,
    registry_reader: object,
) -> tuple[Any, ...]:
    from alpha_system.features.families.structure import (
        StructureFeatureName,
        build_structure_feature_definition,
    )

    dataset_version_ids = tuple(
        dataset.dataset_version_id for dataset in _unit_input_datasets(unit)
    )
    definitions = []
    for binding in _liquidity_pa_structure_bindings(unit.feature_names):
        input_scope = {
            "symbol": unit.symbol.upper(),
            "partition_id": unit.partition_id,
            "partition_schema": unit.schema_id,
            "feature_pack_family": config.family,
            "config_feature_names": list(binding.config_names),
        }
        definitions.append(
            build_structure_feature_definition(
                StructureFeatureName(binding.primitive_name),
                _liquidity_pa_structure_feature_request(config, unit, binding),
                registry_reader,
                dataset_version_ids=dataset_version_ids,
                window_length=binding.window_length,
                reset_on_session=True,
                input_scope=input_scope,
            )
        )
    return tuple(definitions)


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
    exposure_family = f"{config.family}_{binding.exposure_name}"
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


def _render_partition(template: str, *, symbol: str, year: int) -> str:
    return template.format(symbol=symbol, year=year)


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
