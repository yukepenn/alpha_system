"""Generic, governed seed FeaturePack / LabelPack operator.

This module productionizes the proven real-data loop: load already-canonical
local OHLCV bars, run the REAL Databento quality/coverage builders over exactly
the loaded partition, construct an AcceptedDatasetVersion handle from the real
DatasetVersion id and real quality report, materialize a small approved feature
set and label set, and register every materialized feature/label into the
local-only registries under ``ALPHA_DATA_ROOT``.

It is config-driven (a JSON seed config plus CLI overrides) and reusable, not a
one-off script. Bar-row loading is injectable so tests can exercise the
materialize+register flow with in-memory synthetic rows (no ``polars`` needed).

Stdlib-only at import time. Heavy work (Parquet reads) flows through the
canonical loader, which guards ``polars`` via ``require_dependency``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.data.cli_validation import load_cli_config
from alpha_system.data.databento.coverage import (
    expected_intervals_for_symbols,
    ohlcv_coverage_report,
)
from alpha_system.data.databento.quality import ohlcv_quality_report

# These register_dataset helpers are module-private; importing them here couples
# the seed operator to the Databento registration helpers on purpose so that the
# REAL quality/coverage builders run exactly as during dataset registration.
from alpha_system.data.databento.register_dataset import (
    _load_calendar,
    _max_contiguous_no_trade_minutes,
    _settings_for_symbols,
)
from alpha_system.data.foundation.canonical_loader import load_canonical_ohlcv_rows
from alpha_system.data.foundation.datasets import (
    DatasetVersion,
    compute_quality_report_hash,
)
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.features import consumption
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.engine.materialization import (
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.registry import FeatureRegistry
from alpha_system.features.store import FeatureStore
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.registry import LabelRegistry

SEED_PACK_SCHEMA = "alpha_system.seed_pack.v1"
_DEFAULT_PARTITION_ID = "development_partition"
_DEFAULT_SOURCE = "dsrc_databento_historical"
_DEFAULT_ROLL_POLICY = "roll_cme_index_futures_quarterly"
_DEFAULT_WHAT_TO_SHOW = "TRADES"
_DEFAULT_BAR_SIZE = "1 min"
_HASH0 = "0" * 64

# Config repo paths used to build REAL quality/coverage over the loaded bars.
_INSTRUMENT_CONFIG_PATH = "configs/data/databento_es_nq_rty_instruments.json"
_VALIDATION_CONFIG_PATH = "configs/data/databento_materialize_validation.json"
_CALENDAR_CONFIG_PATH = "configs/data/session_templates_and_calendar.json"

# Labels that consume trade-price (OHLCV close) only and require NO BBO.
_TRADE_PRICE_LABELS: frozenset[str] = frozenset(
    {
        FixedHorizonLabelName.FWD_RET_1M.value,
        FixedHorizonLabelName.FWD_RET_3M.value,
        FixedHorizonLabelName.FWD_RET_5M.value,
        FixedHorizonLabelName.FWD_RET_10M.value,
        FixedHorizonLabelName.FWD_RET_30M.value,
    }
)

# Trade-price horizon strings for create_label_spec, keyed by label name value.
_LABEL_HORIZON_MINUTES: dict[str, int] = {
    FixedHorizonLabelName.FWD_RET_1M.value: 1,
    FixedHorizonLabelName.FWD_RET_3M.value: 3,
    FixedHorizonLabelName.FWD_RET_5M.value: 5,
    FixedHorizonLabelName.FWD_RET_10M.value: 10,
    FixedHorizonLabelName.FWD_RET_30M.value: 30,
}

BarRowLoader = Callable[..., Sequence[Mapping[str, Any]]]
# Builds (quality_report, coverage_report) over the loaded bars. The default runs
# the REAL Databento builders; tests may inject a synthetic-report builder.
QualityCoverageBuilder = Callable[..., tuple[Any, Any]]


class SeedPackError(ValueError):
    """Raised when seed FeaturePack / LabelPack construction fails closed."""


@dataclass(frozen=True, slots=True)
class FeatureSpecConfig:
    """One feature entry in the seed config feature set."""

    name: str
    window_length: int = 3
    horizon: int = 1


@dataclass(frozen=True, slots=True)
class FeatureSetConfig:
    """Seed feature-set configuration."""

    feature_set_id: str
    feature_set_version: str
    alpha_spec_id: str
    features: tuple[FeatureSpecConfig, ...]


@dataclass(frozen=True, slots=True)
class LabelSpecConfig:
    """One label entry in the seed config label set."""

    name: str
    horizon: str


@dataclass(frozen=True, slots=True)
class LabelSetConfig:
    """Seed label-set configuration."""

    label_set_id: str
    labels: tuple[LabelSpecConfig, ...]


@dataclass(frozen=True, slots=True)
class SeedPackConfig:
    """Parsed, validated seed FeaturePack / LabelPack configuration."""

    dataset_version_id: str
    symbol: str
    partition_id: str
    partition_schema: str
    window_start_ts: str
    window_end_ts: str
    feature_set: FeatureSetConfig | None = None
    label_set: LabelSetConfig | None = None

    def __post_init__(self) -> None:
        _require_text(self.dataset_version_id, "dataset_version_id")
        _require_text(self.symbol, "symbol")
        _require_text(self.partition_id, "partition_id")
        _require_text(self.partition_schema, "partition_schema")
        _require_iso(self.window_start_ts, "window.start_ts")
        _require_iso(self.window_end_ts, "window.end_ts")
        if self.feature_set is None and self.label_set is None:
            raise SeedPackError("seed config must define a feature_set or a label_set")


def load_seed_pack_config(path: str | Path) -> SeedPackConfig:
    """Parse and validate a seed FeaturePack / LabelPack JSON config."""

    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SeedPackError(f"seed config could not be read: {config_path.as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise SeedPackError(f"seed config is not valid JSON: {config_path.as_posix()}") from exc
    return parse_seed_pack_config(payload)


def parse_seed_pack_config(payload: Mapping[str, Any]) -> SeedPackConfig:
    """Validate a seed config mapping and return a typed ``SeedPackConfig``."""

    mapping = _require_mapping(payload, "seed config")
    schema = mapping.get("schema")
    if schema != SEED_PACK_SCHEMA:
        raise SeedPackError(f"seed config schema must be {SEED_PACK_SCHEMA}")
    window = _require_mapping(mapping.get("window"), "window")
    return SeedPackConfig(
        dataset_version_id=_require_text(mapping.get("dataset_version_id"), "dataset_version_id"),
        symbol=_require_text(mapping.get("symbol"), "symbol"),
        partition_id=_optional_text(
            mapping.get("partition_id"),
            "partition_id",
            default=_DEFAULT_PARTITION_ID,
        ),
        partition_schema=_optional_text(
            mapping.get("partition_schema"),
            "partition_schema",
            default="ohlcv_1m",
        ),
        window_start_ts=_require_text(window.get("start_ts"), "window.start_ts"),
        window_end_ts=_require_text(window.get("end_ts"), "window.end_ts"),
        feature_set=_parse_feature_set(mapping.get("feature_set")),
        label_set=_parse_label_set(mapping.get("label_set")),
    )


def _parse_feature_set(value: object) -> FeatureSetConfig | None:
    if value is None:
        return None
    mapping = _require_mapping(value, "feature_set")
    raw_features = mapping.get("features")
    if not isinstance(raw_features, Sequence) or isinstance(raw_features, str) or not raw_features:
        raise SeedPackError("feature_set.features must be a non-empty list")
    features = tuple(_parse_feature(entry) for entry in raw_features)
    return FeatureSetConfig(
        feature_set_id=_require_text(mapping.get("feature_set_id"), "feature_set.feature_set_id"),
        feature_set_version=_optional_text(
            mapping.get("feature_set_version"),
            "feature_set.feature_set_version",
            default="v1",
        ),
        alpha_spec_id=_require_text(mapping.get("alpha_spec_id"), "feature_set.alpha_spec_id"),
        features=features,
    )


def _parse_feature(value: object) -> FeatureSpecConfig:
    mapping = _require_mapping(value, "feature_set.features[]")
    return FeatureSpecConfig(
        name=_require_text(mapping.get("name"), "feature.name"),
        window_length=_optional_positive_int(mapping.get("window_length"), "feature.window_length"),
        horizon=_optional_positive_int(mapping.get("horizon"), "feature.horizon"),
    )


def _parse_label_set(value: object) -> LabelSetConfig | None:
    if value is None:
        return None
    mapping = _require_mapping(value, "label_set")
    raw_labels = mapping.get("labels")
    if not isinstance(raw_labels, Sequence) or isinstance(raw_labels, str) or not raw_labels:
        raise SeedPackError("label_set.labels must be a non-empty list")
    labels = tuple(_parse_label(entry) for entry in raw_labels)
    return LabelSetConfig(
        label_set_id=_require_text(mapping.get("label_set_id"), "label_set.label_set_id"),
        labels=labels,
    )


def _parse_label(value: object) -> LabelSpecConfig:
    mapping = _require_mapping(value, "label_set.labels[]")
    return LabelSpecConfig(
        name=_require_text(mapping.get("name"), "label.name"),
        horizon=_require_text(mapping.get("horizon"), "label.horizon"),
    )


@dataclass(frozen=True, slots=True)
class _AcceptedContext:
    accepted: Any
    dataset_version: DatasetVersion
    bar_rows: tuple[Mapping[str, Any], ...]
    quality_status: str
    coverage_status: str


def run_seed_feature_pack(
    config: SeedPackConfig,
    *,
    alpha_data_root: str | Path,
    canonical_root: str | Path,
    datasets_registry_path: str | Path,
    bar_rows: Sequence[Mapping[str, Any]] | None = None,
    bar_row_loader: BarRowLoader = load_canonical_ohlcv_rows,
    quality_coverage_builder: QualityCoverageBuilder | None = None,
    repo_root: str | Path = ".",
    value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
) -> dict[str, Any]:
    """Materialize and register a seed FeaturePack from real canonical bars."""

    if config.feature_set is None:
        raise SeedPackError("seed config does not define a feature_set")
    alpha_root = _assert_outside_repo_root(alpha_data_root)
    context = _build_accepted_context(
        config,
        canonical_root=canonical_root,
        datasets_registry_path=datasets_registry_path,
        bar_rows=bar_rows,
        bar_row_loader=bar_row_loader,
        quality_coverage_builder=quality_coverage_builder,
        repo_root=repo_root,
    )

    # Register features sequentially, each against the LIVE feature registry, so
    # the spec's request gate decision (request id + duplicate-exposure notes)
    # matches exactly what the FeatureStore re-checks at registration time. Each
    # feature also gets a distinct exposure family so the registry duplicate guard
    # admits distinct features that share one seed set. Mirrors the store contract
    # in tests/unit/features/test_feature_store.py.
    registry_path = Path(alpha_root) / "registry" / "features.sqlite"
    store = FeatureStore(FeatureRegistry(registry_path))
    registered_feature_version_ids: list[str] = []
    total_value_records = 0
    output_paths: list[str] = []
    value_store_handles: list[dict[str, str | int | None]] = []
    for entry in config.feature_set.features:
        request = _build_feature_request(config.feature_set, entry.name)
        definition = build_ohlcv_feature_definition(
            _coerce_feature_name(entry.name),
            request,
            store.registry,
            dataset_version_ids=(config.dataset_version_id,),
            window_length=entry.window_length,
            horizon=entry.horizon,
            reset_on_session=False,
        )
        checked_request = (
            definition.request_gate_decision.checked_feature_request or request
        )
        feature_set = FeatureSetSpec(
            feature_set_id=config.feature_set.feature_set_id,
            feature_set_version=f"{config.feature_set.feature_set_version}_{entry.name}",
            features=(definition.spec,),
        )
        plan = build_feature_materialization_plan(
            feature_set,
            context.accepted,
            partition_id=config.partition_id,
            alpha_data_root=alpha_root,
        )
        inputs = FeatureMaterializationInputs(
            accepted_version=context.accepted,
            bar_rows=context.bar_rows,
        )
        result = materialize_features(
            plan,
            inputs,
            (definition,),
            value_store_format=value_store_format,
        )
        if result.record_count == 0:
            raise SeedPackError(
                f"feature materialization produced no value records for {entry.name}"
            )
        value_store_handle = _value_store_handle_summary(result)
        if value_store_handle is not None:
            value_store_handles.append(value_store_handle)
        record = store.register_materialized_feature(
            result,
            feature_spec=definition.spec,
            feature_version=definition.version,
            feature_request=checked_request,
        )
        registered_feature_version_ids.append(record.feature_version_id)
        total_value_records += result.record_count
        output_paths.append(str(plan.output_path))

    return {
        "schema": SEED_PACK_SCHEMA,
        "pack_kind": "feature",
        "dataset_version_id": config.dataset_version_id,
        "symbol": config.symbol.upper(),
        "partition_id": config.partition_id,
        "window": {"start_ts": config.window_start_ts, "end_ts": config.window_end_ts},
        "bar_row_count": len(context.bar_rows),
        "quality_status": context.quality_status,
        "coverage_status": context.coverage_status,
        "feature_set_id": config.feature_set.feature_set_id,
        "feature_set_version": config.feature_set.feature_set_version,
        "feature_count": len(config.feature_set.features),
        "feature_version_ids": registered_feature_version_ids,
        "value_record_count": total_value_records,
        "value_store": value_store_format.value,
        "value_store_handle": value_store_handles[0] if value_store_handles else None,
        "value_store_handles": value_store_handles,
        "output_path": output_paths[0] if output_paths else "",
        "output_paths": output_paths,
        "registry_path": str(registry_path),
    }


def run_seed_label_pack(
    config: SeedPackConfig,
    *,
    alpha_data_root: str | Path,
    canonical_root: str | Path,
    datasets_registry_path: str | Path,
    bar_rows: Sequence[Mapping[str, Any]] | None = None,
    bar_row_loader: BarRowLoader = load_canonical_ohlcv_rows,
    quality_coverage_builder: QualityCoverageBuilder | None = None,
    repo_root: str | Path = ".",
    value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
) -> dict[str, Any]:
    """Materialize and register a seed LabelPack from real canonical bars."""

    if config.label_set is None:
        raise SeedPackError("seed config does not define a label_set")
    alpha_root = _assert_outside_repo_root(alpha_data_root)
    context = _build_accepted_context(
        config,
        canonical_root=canonical_root,
        datasets_registry_path=datasets_registry_path,
        bar_rows=bar_rows,
        bar_row_loader=bar_row_loader,
        quality_coverage_builder=quality_coverage_builder,
        repo_root=repo_root,
    )

    definitions = tuple(
        build_fixed_horizon_label_definition(
            _coerce_label_name(entry.name),
            _build_label_spec(config, entry),
            dataset_version_ids=(config.dataset_version_id,),
        )
        for entry in config.label_set.labels
    )
    for entry in config.label_set.labels:
        if entry.name not in _TRADE_PRICE_LABELS:
            raise SeedPackError(
                f"seed label pack supports trade-price labels only; got {entry.name}"
            )
    plan = build_label_materialization_plan(
        definitions,
        context.accepted,
        partition_id=config.partition_id,
        instrument_ids=(),
        alpha_data_root=alpha_root,
    )
    inputs = LabelMaterializationInputs(
        accepted_version=context.accepted,
        bar_rows=context.bar_rows,
    )
    result = materialize_labels(
        plan,
        inputs,
        definitions,
        value_store_format=value_store_format,
    )
    if not result.wrote_output and result.record_count == 0:
        raise SeedPackError("label materialization produced no value records")
    value_store_handle = _value_store_handle_summary(result)

    registry_path = Path(alpha_root) / "registry" / "labels.sqlite"
    registry = LabelRegistry(registry_path)
    registered_label_version_ids: list[str] = []
    for definition in definitions:
        record = registry.register_materialized_label(
            result,
            label_contract=definition.contract,
            label_version=definition.version,
        )
        registered_label_version_ids.append(record.label_version_id)

    return {
        "schema": SEED_PACK_SCHEMA,
        "pack_kind": "label",
        "dataset_version_id": config.dataset_version_id,
        "symbol": config.symbol.upper(),
        "partition_id": config.partition_id,
        "window": {"start_ts": config.window_start_ts, "end_ts": config.window_end_ts},
        "bar_row_count": len(context.bar_rows),
        "quality_status": context.quality_status,
        "coverage_status": context.coverage_status,
        "label_set_id": config.label_set.label_set_id,
        "label_count": len(definitions),
        "label_version_ids": registered_label_version_ids,
        "value_record_count": result.record_count,
        "value_store": value_store_format.value,
        "value_store_handle": value_store_handle,
        "output_path": str(plan.output_path),
        "registry_path": str(registry_path),
    }


def _value_store_handle_summary(result: Any) -> dict[str, str | int | None] | None:
    handle = getattr(result, "value_store_handle", None)
    if handle is None:
        return None
    return {
        "format": handle.format.value,
        "jsonl_path": handle.jsonl_path,
        "parquet_path": handle.parquet_path,
        "content_hash": handle.content_hash,
        "value_count": handle.value_count,
    }


def _build_accepted_context(
    config: SeedPackConfig,
    *,
    canonical_root: str | Path,
    datasets_registry_path: str | Path,
    bar_rows: Sequence[Mapping[str, Any]] | None,
    bar_row_loader: BarRowLoader,
    quality_coverage_builder: QualityCoverageBuilder | None,
    repo_root: str | Path,
) -> _AcceptedContext:
    rows = _load_bar_rows(
        config,
        canonical_root=canonical_root,
        bar_rows=bar_rows,
        bar_row_loader=bar_row_loader,
    )
    if not rows:
        raise SeedPackError("no canonical bar rows were loaded for the seed window")

    builder = quality_coverage_builder or _build_real_quality_coverage
    quality, coverage = builder(config, rows, repo_root=repo_root)
    if quality.blocks_versioning:
        raise SeedPackError("real quality report blocks versioning; refusing to seed")
    if coverage.blocks_versioning:
        raise SeedPackError("real coverage report blocks versioning; refusing to seed")

    # Construct the DatasetVersion handle directly (NOT registry-resolved). Per
    # ADR-0006 the registry persists only report hashes, so placeholder
    # manifest/code/config hashes are acceptable for a directly built handle that
    # carries the REAL quality_report and computed quality_report_hash.
    dataset_version = DatasetVersion(
        dataset_version_id=config.dataset_version_id,
        source=_DEFAULT_SOURCE,
        symbol_universe=(config.symbol.upper(),),
        bar_size=_DEFAULT_BAR_SIZE,
        what_to_show=_DEFAULT_WHAT_TO_SHOW,
        start_ts=_require_iso(config.window_start_ts, "window.start_ts"),
        end_ts=_require_iso(config.window_end_ts, "window.end_ts"),
        contract_universe=(config.symbol.upper(),),
        roll_policy_id=_DEFAULT_ROLL_POLICY,
        manifest_hash=_HASH0,
        code_hash=_HASH0,
        config_hash=_HASH0,
        quality_report_hash=compute_quality_report_hash(quality),
        created_at=_require_iso(config.window_end_ts, "window.end_ts"),
    )
    accepted = consumption.AcceptedDatasetVersion(
        registry_path=str(datasets_registry_path),
        dataset_version=dataset_version,
        lifecycle_state="VERSIONED",
        quality_report=quality,
        coverage_report=coverage,
    )
    return _AcceptedContext(
        accepted=accepted,
        dataset_version=dataset_version,
        bar_rows=tuple(rows),
        quality_status=quality.status.value,
        coverage_status=_coverage_status(coverage),
    )


def _load_bar_rows(
    config: SeedPackConfig,
    *,
    canonical_root: str | Path,
    bar_rows: Sequence[Mapping[str, Any]] | None,
    bar_row_loader: BarRowLoader,
) -> tuple[Mapping[str, Any], ...]:
    if bar_rows is not None:
        return tuple(bar_rows)
    loaded = bar_row_loader(
        canonical_root=canonical_root,
        dataset_version_id=config.dataset_version_id,
        symbol=config.symbol,
        start_ts=config.window_start_ts,
        end_ts=config.window_end_ts,
        partition_schema=config.partition_schema,
    )
    return tuple(loaded)


def _build_real_quality_coverage(
    config: SeedPackConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    repo_root: str | Path,
) -> tuple[Any, Any]:
    root = Path(repo_root)
    instrument_config = load_cli_config(str(root / _INSTRUMENT_CONFIG_PATH))
    validation_config = load_cli_config(str(root / _VALIDATION_CONFIG_PATH))
    calendar = _load_calendar(root / _CALENDAR_CONFIG_PATH, instrument_config)
    symbol = config.symbol.upper()
    settings = _settings_for_symbols(symbols=(symbol,), instrument_config=instrument_config)
    max_no_trade = _max_contiguous_no_trade_minutes(validation_config)
    expected_sessions = tuple(sorted({s.session_label for s in settings.values()}))
    expected_intervals = expected_intervals_for_symbols(
        symbols=(symbol,),
        partition_id=config.partition_id,
        settings_by_symbol=settings,
        calendar=calendar,
        start_ts=_require_iso(config.window_start_ts, "window.start_ts"),
        end_ts=_require_iso(config.window_end_ts, "window.end_ts"),
    )
    quality = ohlcv_quality_report(
        quality_report_id=f"dqr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
        bars=rows,
        expected_sessions=expected_sessions,
        expected_gap_intervals=expected_intervals,
        max_contiguous_no_trade_minutes=max_no_trade,
    )
    coverage = ohlcv_coverage_report(
        coverage_report_id=f"covr_{config.dataset_version_id}",
        dataset_version_id=config.dataset_version_id,
        bars=rows,
        expected_intervals=expected_intervals,
        incomplete_chunks=(),
        max_contiguous_no_trade_minutes=max_no_trade,
    )
    return quality, coverage


def _build_feature_request(feature_set: FeatureSetConfig, feature_name: str) -> FeatureRequest:
    # First seed into an empty target feature registry; EMPTY exposure is correct
    # and documented. If a populated registry later runs this operator, the
    # FeatureStore request gate still re-checks exposure at registration time.
    # Each feature gets a distinct exposure family so the registry duplicate
    # guard does not block distinct features that share one seed set.
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    exposure_family = f"seed_{feature_set.feature_set_id}_{feature_name}"
    return create_feature_request(
        alpha_spec_id=feature_set.alpha_spec_id,
        requested_inputs=[exposure_family],
        formula_sketch={
            "exposure_family": exposure_family,
            "inputs": ["canonical_ohlcv"],
            "operation": "seed_feature_pack",
            "window": 1,
        },
        availability_assumptions={
            "timing": "canonical bars expose available_ts at or after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "available_ts"],
            "source": "already-canonical local OHLCV parquet partition",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _build_label_spec(config: SeedPackConfig, entry: LabelSpecConfig) -> LabelSpec:
    horizon_minutes = _LABEL_HORIZON_MINUTES.get(entry.name)
    if horizon_minutes is None:
        raise SeedPackError(f"unsupported seed label: {entry.name}")
    expected_horizon = f"{horizon_minutes}m"
    if entry.horizon != expected_horizon:
        raise SeedPackError(
            f"label {entry.name} horizon must be {expected_horizon}, got {entry.horizon}"
        )
    return create_label_spec(
        horizon=expected_horizon,
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": horizon_minutes,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_family",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        # availability_time must be tz-aware ISO-8601 at/just-before the window
        # start so materialized label_available_ts never precedes it.
        availability_time=config.window_start_ts,
        forbidden_feature_overlap={
            "label_ids": [entry.name],
            "aliases": [f"forward_return_{horizon_minutes}m"],
            "transforms": [f"label({entry.name})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _coerce_feature_name(name: str) -> OHLCVFeatureName:
    try:
        return OHLCVFeatureName(name)
    except ValueError as exc:
        raise SeedPackError(f"unsupported OHLCV feature: {name}") from exc


def _coerce_label_name(name: str) -> FixedHorizonLabelName:
    try:
        return FixedHorizonLabelName(name)
    except ValueError as exc:
        raise SeedPackError(f"unsupported fixed-horizon label: {name}") from exc


def _coverage_status(coverage: Any) -> str:
    status = getattr(coverage, "status", None)
    if status is not None:
        return getattr(status, "value", str(status))
    return "BLOCKING" if coverage.blocks_versioning else "PASSING"


def _assert_outside_repo_root(alpha_data_root: str | Path) -> Path:
    root = assert_local_wsl_path(alpha_data_root)
    repo_root = Path.cwd().resolve(strict=False)
    if root == repo_root or root.is_relative_to(repo_root):
        raise SeedPackError("ALPHA_DATA_ROOT must be outside the repository tree")
    return root


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SeedPackError(f"{field_name} must be a mapping")
    return value


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SeedPackError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, field_name: str, *, default: str) -> str:
    if value is None:
        return default
    return _require_text(value, field_name)


def _optional_positive_int(value: object, field_name: str) -> int:
    if value is None:
        return 1
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SeedPackError(f"{field_name} must be a positive integer")
    return value


def _require_iso(value: object, field_name: str) -> datetime:
    text = _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SeedPackError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SeedPackError(f"{field_name} must be timezone-aware")
    return parsed


__all__ = [
    "SEED_PACK_SCHEMA",
    "FeatureSetConfig",
    "FeatureSpecConfig",
    "LabelSetConfig",
    "LabelSpecConfig",
    "SeedPackConfig",
    "SeedPackError",
    "load_seed_pack_config",
    "parse_seed_pack_config",
    "run_seed_feature_pack",
    "run_seed_label_pack",
]
