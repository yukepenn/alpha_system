"""Polars-based label pack materialization core for governed label definitions.

The fast label path computes values only. Label identity remains the
content-addressed ``LabelVersion`` derived from the governed
``LabelContractSpec``, and registration goes through ``LabelRegistry``.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from time import perf_counter
from typing import Any

from alpha_system.backtest.costs import BpsCost, CostInput, SpreadCost
from alpha_system.core.value_store import (
    ValueStoreFormat,
    ValueStoreHandle,
    compute_value_content_hash,
    parquet_is_current,
    write_parquet_values,
)
from alpha_system.data.foundation.canonical_loader import (
    DEFAULT_BBO_PARTITION_SCHEMA,
    DEFAULT_OHLCV_PARTITION_SCHEMA,
    load_canonical_bbo_rows,
    load_canonical_ohlcv_rows,
)
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
from alpha_system.data.storage import require_dependency
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.governance.serialization import JsonValue, canonical_serialize, content_hash
from alpha_system.labels.engine import (
    LabelMaterializationPlan,
    LabelMaterializationResult,
    SupportedLabelDefinition,
    build_label_materialization_plan,
)
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    CostAdjustedLabelName,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelError,
    compute_horizon_overlap_metadata,
)
from alpha_system.labels.registry import LabelRegistry
from alpha_system.labels.version import (
    FrozenJsonMapping,
    LabelContractSpec,
    LabelFamily,
    LabelLineageRecord,
    LabelValueRecord,
    LabelVersion,
)

FAST_LABEL_PRODUCER_ENGINE_ID = "alpha_system.labels.fast.pack_materializer.v1"
FAST_LABEL_VALUE_SCHEMA_VERSION = "alpha_system.labels.fast.values.v1"
_REGISTRY_WRITE_LOCK = Lock()

type CanonicalRowLoader = Callable[..., Sequence[Mapping[str, Any]]]
type FastSupportedLabelDefinition = FixedHorizonLabelDefinition | CostAdjustedLabelDefinition


class FastLabelPackError(ValueError):
    """Raised when fast label pack declaration or execution fails closed."""


@dataclass(frozen=True, slots=True)
class LabelPanelFrameRequest:
    """Request to load one symbol-year OHLCV+BBO label panel through local readers."""

    canonical_root: str | Path
    dataset_version_id: str
    symbol: str
    year: int
    start_ts: str | None = None
    end_ts: str | None = None
    ohlcv_partition_schema: str = DEFAULT_OHLCV_PARTITION_SCHEMA
    bbo_partition_schema: str = DEFAULT_BBO_PARTITION_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_version_id", _require_text(self.dataset_version_id))
        object.__setattr__(self, "symbol", _require_text(self.symbol).upper())
        if isinstance(self.year, bool) or not isinstance(self.year, int) or self.year < 1970:
            raise FastLabelPackError("year must be an integer >= 1970")
        object.__setattr__(
            self,
            "ohlcv_partition_schema",
            _require_text(self.ohlcv_partition_schema),
        )
        object.__setattr__(
            self,
            "bbo_partition_schema",
            _require_text(self.bbo_partition_schema),
        )
        if self.start_ts is not None:
            object.__setattr__(self, "start_ts", _require_text(self.start_ts))
        if self.end_ts is not None:
            object.__setattr__(self, "end_ts", _require_text(self.end_ts))

    @property
    def resolved_start_ts(self) -> str:
        return self.start_ts or f"{self.year:04d}-01-01T00:00:00+00:00"

    @property
    def resolved_end_ts(self) -> str:
        return self.end_ts or f"{self.year + 1:04d}-01-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class FastLabelDeclaration:
    """One governed label definition in a vectorized pack."""

    definition: FastSupportedLabelDefinition

    def __post_init__(self) -> None:
        _definition_contract(self.definition)

    @property
    def label_contract(self) -> LabelContractSpec:
        return _definition_contract(self.definition)

    @property
    def label_version(self) -> LabelVersion:
        return self.definition.version

    @property
    def label_version_id(self) -> str:
        return self.definition.label_version_id


@dataclass(frozen=True, slots=True)
class FastLabelPack:
    """A governed label pack and its reference-derived identities."""

    pack_id: str
    definitions: Sequence[FastSupportedLabelDefinition]
    declarations: Sequence[FastLabelDeclaration]
    metadata: Mapping[str, Any] | FrozenJsonMapping = FrozenJsonMapping()

    def __post_init__(self) -> None:
        pack_id = _require_text(self.pack_id)
        definitions = tuple(self.definitions)
        declarations = tuple(self.declarations)
        if not definitions:
            raise FastLabelPackError("FastLabelPack.definitions must be non-empty")
        if len(definitions) != len(declarations):
            raise FastLabelPackError("FastLabelPack declarations must match definitions")
        for definition, declaration in zip(definitions, declarations, strict=True):
            if declaration.definition != definition:
                raise FastLabelPackError("FastLabelPack declaration order must match definitions")
            expected = LabelVersion.derive(_definition_contract(definition))
            if _definition_version(definition) != expected:
                raise FastLabelPackError("fast label definition identity mismatch")
        object.__setattr__(self, "pack_id", pack_id)
        object.__setattr__(self, "definitions", definitions)
        object.__setattr__(self, "declarations", declarations)
        object.__setattr__(
            self,
            "metadata",
            FrozenJsonMapping.from_mapping(
                self.metadata.to_dict()
                if isinstance(self.metadata, FrozenJsonMapping)
                else dict(self.metadata),
                field_name="metadata",
            ),
        )

    @property
    def label_contracts(self) -> tuple[LabelContractSpec, ...]:
        return tuple(_definition_contract(definition) for definition in self.definitions)

    @property
    def label_version_ids(self) -> tuple[str, ...]:
        return tuple(definition.label_version_id for definition in self.definitions)


@dataclass(frozen=True, slots=True)
class FastFixedHorizonLabelMetadata:
    """Value-free per-label N_eff and overlap metadata."""

    label_id: str
    label_version_id: str
    price_basis: str
    horizon_minutes: int
    n_eff: int
    null_value_count: int
    horizon_overlap_event_count: int
    horizon_overlap_metadata: Mapping[str, JsonValue] | FrozenJsonMapping = FrozenJsonMapping()
    label_family: str = ""
    terminal_kind: str = ""

    def to_dict(self) -> dict[str, JsonValue]:
        overlap_metadata = (
            self.horizon_overlap_metadata.to_dict()
            if isinstance(self.horizon_overlap_metadata, FrozenJsonMapping)
            else dict(self.horizon_overlap_metadata)
        )
        return {
            "label_id": self.label_id,
            "label_version_id": self.label_version_id,
            "price_basis": self.price_basis,
            "horizon_minutes": self.horizon_minutes,
            "n_eff": self.n_eff,
            "null_value_count": self.null_value_count,
            "horizon_overlap_event_count": self.horizon_overlap_event_count,
            "horizon_overlap_metadata": overlap_metadata,
            "label_family": self.label_family,
            "terminal_kind": self.terminal_kind,
        }


@dataclass(frozen=True, slots=True)
class FastLabelComputationMetadata:
    """Value-free summary of one fast label pack computation."""

    producer_engine_id: str
    value_schema_version: str
    pack_id: str
    shared_panel_rows_by_basis: Mapping[str, int]
    prepared_guard_columns: tuple[str, ...]
    labels: tuple[FastFixedHorizonLabelMetadata, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "producer_engine_id": self.producer_engine_id,
            "value_schema_version": self.value_schema_version,
            "pack_id": self.pack_id,
            "shared_panel_rows_by_basis": dict(self.shared_panel_rows_by_basis),
            "prepared_guard_columns": list(self.prepared_guard_columns),
            "labels": [label.to_dict() for label in self.labels],
        }


@dataclass(frozen=True, slots=True)
class FastLabelComputation:
    """Fast label records plus value-free computation metadata."""

    records: tuple[LabelValueRecord, ...]
    metadata: FastLabelComputationMetadata


class FastLabelMaterializer:
    """Compute, persist, and register governed label packs through label keystones."""

    def __init__(
        self,
        *,
        canonical_ohlcv_loader: CanonicalRowLoader = load_canonical_ohlcv_rows,
        canonical_bbo_loader: CanonicalRowLoader = load_canonical_bbo_rows,
    ) -> None:
        self._canonical_ohlcv_loader = canonical_ohlcv_loader
        self._canonical_bbo_loader = canonical_bbo_loader
        self._frame_cache: dict[LabelPanelFrameRequest, Any] = {}

    def load_symbol_year_price_frame(self, request: LabelPanelFrameRequest) -> Any:
        """Load and cache one symbol-year OHLCV+BBO panel through sanctioned readers."""

        require_dependency("polars")
        if not isinstance(request, LabelPanelFrameRequest):
            raise FastLabelPackError("load request must be a LabelPanelFrameRequest")
        cached = self._frame_cache.get(request)
        if cached is not None:
            return cached
        ohlcv_rows = self._canonical_ohlcv_loader(
            canonical_root=request.canonical_root,
            dataset_version_id=request.dataset_version_id,
            symbol=request.symbol,
            start_ts=request.resolved_start_ts,
            end_ts=request.resolved_end_ts,
            partition_schema=request.ohlcv_partition_schema,
        )
        bbo_rows = self._canonical_bbo_loader(
            canonical_root=request.canonical_root,
            dataset_version_id=request.dataset_version_id,
            symbol=request.symbol,
            start_ts=request.resolved_start_ts,
            end_ts=request.resolved_end_ts,
            partition_schema=request.bbo_partition_schema,
        )
        frame = self.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=bbo_rows)
        self._frame_cache[request] = frame
        return frame

    def frame_from_rows(
        self,
        *,
        ohlcv_rows: Sequence[Mapping[str, Any]],
        bbo_rows: Sequence[Mapping[str, Any]],
        polars: Any | None = None,
    ) -> Any:
        """Build one normalized Polars price panel from OHLCV and BBO mappings."""

        pl = polars or require_dependency("polars")
        rows: list[dict[str, Any]] = []
        rows.extend(_ohlcv_panel_row(row) for row in ohlcv_rows)
        rows.extend(_bbo_panel_row(row) for row in bbo_rows)
        if not rows:
            raise FastLabelPackError("label price panel rows must be non-empty")
        # infer_schema_length=None scans all rows for schema inference: real
        # canonical data has columns that are integral in the first rows then
        # float later (e.g. a price 6053 then 6053.5), which the default bounded
        # inference rejects ("could not append f64 to the builder"). Scanning all
        # rows widens int->float deterministically. (FCFP-P13 real-data label run.)
        frame = pl.DataFrame(rows, infer_schema_length=None)
        _require_columns(
            frame,
            (
                "price_basis",
                "series_id",
                "event_ts",
                "bar_end_ts",
                "available_ts",
                "price",
                "quality_flags",
            ),
        )
        return frame.sort(("price_basis", "series_id", "event_ts", "available_ts"))

    def materialize_pack(
        self,
        pack: FastLabelPack,
        accepted_version: AcceptedDatasetVersion,
        *,
        partition_id: str,
        price_frame: Any | None = None,
        load_request: LabelPanelFrameRequest | None = None,
        instrument_ids: Sequence[str] = (),
        alpha_data_root: str | Path | None = None,
        governance_metadata: Mapping[str, Any] | None = None,
        partition_plan: Any | None = None,
        output_namespace: str = "labels/fast_materialized",
        value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
    ) -> LabelMaterializationResult:
        """Compute and persist a label pack as Parquet plus optional JSONL audit rows."""

        pack = _require_pack(pack)
        if not isinstance(accepted_version, AcceptedDatasetVersion):
            raise FastLabelPackError("accepted_version must be an AcceptedDatasetVersion")
        frame = price_frame
        if frame is None:
            if load_request is None:
                raise FastLabelPackError("price_frame or load_request is required")
            if load_request.dataset_version_id != accepted_version.dataset_version_id:
                raise FastLabelPackError("load request DatasetVersion must match accepted input")
            frame = self.load_symbol_year_price_frame(load_request)
        plan = build_label_materialization_plan(
            pack.definitions,
            accepted_version,
            partition_id=partition_id,
            instrument_ids=instrument_ids,
            alpha_data_root=alpha_data_root,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
            output_namespace=output_namespace,
        )
        return self.materialize_values(plan, frame, pack, value_store_format=value_store_format)

    def materialize_values(
        self,
        plan: LabelMaterializationPlan,
        price_frame: Any,
        pack: FastLabelPack,
        *,
        value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
    ) -> LabelMaterializationResult:
        """Compute values for an existing label plan and write the value store."""

        started = perf_counter()
        if not isinstance(plan, LabelMaterializationPlan):
            raise FastLabelPackError("plan must be a LabelMaterializationPlan")
        pack = _require_pack(pack)
        _validate_plan_matches_pack(plan, pack)
        computation = self.compute_values_with_metadata(price_frame, pack)
        _validate_records(plan, computation.records)
        write_result = _write_records(
            plan,
            computation.records,
            metadata=computation.metadata,
            value_store_format=value_store_format,
        )
        return LabelMaterializationResult(
            plan=plan,
            records=computation.records,
            dry_run=False,
            wrote_output=write_result.wrote_output,
            output_path=write_result.output_path,
            value_store_handle=write_result.handle,
            planned_input_rows=sum(computation.metadata.shared_panel_rows_by_basis.values()),
            planned_label_count=len(pack.definitions),
            runtime_seconds=perf_counter() - started,
        )

    def compute_values(self, price_frame: Any, pack: FastLabelPack) -> tuple[LabelValueRecord, ...]:
        """Evaluate all governed labels and return aligned LabelValueRecords.

        Records-only path: it does NOT compute the value-free N_eff/overlap
        metadata (that is only needed by materialize_pack via
        compute_values_with_metadata). Callers that need both should call
        compute_values_with_metadata directly; this keeps record production -- the
        hot path used at scale and in the benchmark -- free of the per-pack
        metadata scan.
        """

        pl = require_dependency("polars")
        pack = _require_pack(pack)
        frame = self.prepare_price_panel(price_frame)
        return self.compute_values_from_panel(frame, pack)

    def prepare_price_panel(self, price_frame: Any) -> Any:
        """Adapt a raw canonical price frame into the prepared label price panel.

        This is the V1 engine's input-adaptation step -- the analogue of the
        reference engine's CanonicalInputViews. It is a once-per-batch cost
        (independent of how many label horizons are computed), so callers that
        evaluate many declarations from one canonical load (the real materialize
        path and the benchmark) prepare the panel ONCE here and feed it to
        compute_values_from_panel, rather than re-preparing per call.
        """

        pl = require_dependency("polars")
        return _prepare_panel(_coerce_frame(price_frame, pl), pl)

    def compute_values_from_panel(
        self, prepared_panel: Any, pack: FastLabelPack
    ) -> tuple[LabelValueRecord, ...]:
        """Compute all label records from an already-prepared price panel.

        Pure compute step (no input adaptation): given the prepared panel from
        prepare_price_panel, evaluate every governed fixed-minute label using
        the P02 shared panel and cached terminal-index models.
        """

        pl = require_dependency("polars")
        pack = _require_pack(pack)
        panel = _shared_label_panel_from_prepared_panel(prepared_panel, pl)
        terminal_models = _terminal_models_for_pack(panel, pack)
        all_records: list[LabelValueRecord] = []
        for declaration in pack.declarations:
            all_records.extend(
                _compute_definition_records_from_panel(
                    panel,
                    declaration.definition,
                    terminal_models,
                )
            )
        return tuple(all_records)

    def compute_values_with_metadata(
        self,
        price_frame: Any,
        pack: FastLabelPack,
    ) -> FastLabelComputation:
        """Evaluate all labels once from a prepared shared price panel."""

        pl = require_dependency("polars")
        pack = _require_pack(pack)
        frame = _prepare_panel(_coerce_frame(price_frame, pl), pl)
        panel = _shared_label_panel_from_prepared_panel(frame, pl)
        terminal_models = _terminal_models_for_pack(panel, pack)
        records_by_label: dict[str, tuple[LabelValueRecord, ...]] = {}
        event_sets: dict[str, dict[str, set[datetime]]] = defaultdict(dict)
        all_records: list[LabelValueRecord] = []

        for declaration in pack.declarations:
            definition = declaration.definition
            records = _compute_definition_records_from_panel(
                panel,
                definition,
                terminal_models,
            )
            records_by_label[definition.label_version_id] = records
            event_sets[_definition_price_basis(definition)][definition.label_version_id] = {
                record.event_ts for record in records
            }
            all_records.extend(records)

        metadata = _computation_metadata(
            panel,
            pack,
            records_by_label=records_by_label,
            event_sets=event_sets,
        )
        return FastLabelComputation(records=tuple(all_records), metadata=metadata)

    def register_pack(
        self,
        materialization_result: LabelMaterializationResult,
        pack: FastLabelPack,
        *,
        store: LabelRegistry | None = None,
        registry_metadata: Mapping[str, Any] | None = None,
    ) -> tuple[Any, ...]:
        """Register every label through ``LabelRegistry`` using serial writes."""

        pack = _require_pack(pack)
        if not isinstance(materialization_result, LabelMaterializationResult):
            raise FastLabelPackError("registration requires a LabelMaterializationResult")
        label_registry = store or LabelRegistry.from_alpha_data_root(
            materialization_result.plan.alpha_data_root
        )
        metadata = _registry_metadata(registry_metadata)
        records: list[Any] = []
        with _REGISTRY_WRITE_LOCK:
            for declaration in pack.declarations:
                definition = declaration.definition
                contract = _definition_contract(definition)
                lineage = LabelLineageRecord(
                    label_version=_definition_version(definition),
                    label_contract=contract,
                    label_spec_id=contract.label_spec_id,
                    contract_provenance={
                        "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
                        "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
                    },
                )
                records.append(
                    label_registry.register_materialized_label(
                        materialization_result,
                        label_contract=contract,
                        label_version=_definition_version(definition),
                        lineage=lineage,
                        registry_metadata=metadata,
                    )
                )
        return tuple(records)


@dataclass(frozen=True, slots=True)
class _WriteResult:
    wrote_output: bool
    output_path: Path
    handle: ValueStoreHandle


def _terminal_models_for_pack(panel: Any, pack: FastLabelPack) -> dict[tuple[str, str], Any]:
    from alpha_system.labels.fast.panel import (
        TerminalKind,
        TerminalRequest,
        resolve_terminal_indices,
    )

    models: dict[tuple[str, str], Any] = {}
    for definition in pack.definitions:
        if not isinstance(definition, FixedHorizonLabelDefinition):
            continue
        terminal_key = _terminal_model_key(definition)
        if terminal_key in models:
            continue
        horizon_minutes = _fixed_horizon_minutes_or_none(definition)
        if horizon_minutes is not None:
            models[terminal_key] = resolve_terminal_indices(
                panel,
                TerminalRequest(
                    kind=TerminalKind.FIXED_HORIZON,
                    horizon_minutes=horizon_minutes,
                    price_basis=definition.price_basis,
                ),
            )
            continue
        models[terminal_key] = resolve_terminal_indices(
            panel,
            TerminalRequest(
                kind=_close_out_terminal_kind(definition),
                price_basis=definition.price_basis,
            ),
        )
    return models


def _compute_definition_records_from_panel(
    panel: Any,
    definition: FastSupportedLabelDefinition,
    terminal_models: Mapping[tuple[str, str], Any],
) -> tuple[LabelValueRecord, ...]:
    if isinstance(definition, FixedHorizonLabelDefinition):
        terminal_model = terminal_models[_terminal_model_key(definition)]
        if _fixed_horizon_minutes_or_none(definition) is not None:
            return _compute_fixed_horizon_records_from_panel(panel, definition, terminal_model)
        return _compute_close_out_records_from_panel(panel, definition, terminal_model)
    if isinstance(definition, CostAdjustedLabelDefinition):
        return _compute_cost_adjusted_records_from_panel(panel, definition)
    raise FastLabelPackError("fast pack contains an unsupported label definition")


def _compute_fixed_horizon_records_from_panel(
    panel: Any,
    definition: FixedHorizonLabelDefinition,
    terminal_model: Any,
) -> tuple[LabelValueRecord, ...]:
    from alpha_system.labels.fast.panel import (
        LabelAvailabilityFamily,
        TerminalGuardDisposition,
        derive_label_available_ts,
    )

    records: list[LabelValueRecord] = []
    for resolution in terminal_model.resolutions:
        if resolution.disposition in {
            TerminalGuardDisposition.DROP,
            TerminalGuardDisposition.INVALID,
        }:
            continue
        if resolution.terminal_index is None:
            continue
        source = panel.row_at(resolution.source_index)
        terminal = panel.row_at(resolution.terminal_index)
        value, flags = _label_value_and_flags_from_panel(source, terminal, definition)
        label_available_ts = derive_label_available_ts(
            LabelAvailabilityFamily.FIXED_HORIZON,
            definition.contract.availability_policy,
            horizon_end_ts=terminal.event_ts,
            terminal_available_ts=terminal.available_ts,
        )
        records.append(
            LabelValueRecord(
                label_version_id=definition.label_version_id,
                entity_id=source.series_id,
                event_ts=source.event_ts,
                horizon_end_ts=terminal.event_ts,
                label_available_ts=label_available_ts,
                value=value,
                label_contract=definition.contract,
                quality_flags=_quality_flags((*flags, *resolution.quality_flags)),
            )
        )
    return tuple(records)


def _compute_close_out_records_from_panel(
    panel: Any,
    definition: FixedHorizonLabelDefinition,
    terminal_model: Any,
) -> tuple[LabelValueRecord, ...]:
    from alpha_system.labels.fast.panel import (
        LabelAvailabilityFamily,
        TerminalGuardDisposition,
        derive_label_available_ts,
    )

    records: list[LabelValueRecord] = []
    for resolution in terminal_model.resolutions:
        if resolution.disposition in {
            TerminalGuardDisposition.DROP,
            TerminalGuardDisposition.INVALID,
        }:
            continue
        if resolution.terminal_index is None:
            continue
        source = panel.row_at(resolution.source_index)
        terminal = panel.row_at(resolution.terminal_index)
        value, flags = _label_value_and_flags_from_panel(source, terminal, definition)
        label_available_ts = derive_label_available_ts(
            LabelAvailabilityFamily.FIXED_HORIZON,
            definition.contract.availability_policy,
            horizon_end_ts=terminal.event_ts,
            terminal_available_ts=terminal.available_ts,
        )
        records.append(
            LabelValueRecord(
                label_version_id=definition.label_version_id,
                entity_id=source.series_id,
                event_ts=source.event_ts,
                horizon_end_ts=terminal.event_ts,
                label_available_ts=label_available_ts,
                value=value,
                label_contract=definition.contract,
                quality_flags=_quality_flags((*flags, *resolution.quality_flags)),
            )
        )
    return tuple(records)


def _compute_cost_adjusted_records_from_panel(
    panel: Any,
    definition: CostAdjustedLabelDefinition,
) -> tuple[LabelValueRecord, ...]:
    from alpha_system.labels.fast.panel import (
        LabelAvailabilityFamily,
        derive_label_available_ts,
    )

    horizon = _cost_horizon_delta(definition)
    bbo_rows_by_key = _cost_bbo_rows_by_key(panel)
    records: list[LabelValueRecord] = []
    for source in panel.rows:
        if not _panel_has_bbo_row(source):
            continue
        horizon_end_ts = source.event_ts + horizon
        terminal = bbo_rows_by_key.get((source.series_id, horizon_end_ts))
        label_available_ts = derive_label_available_ts(
            LabelAvailabilityFamily.COST_ADJUSTED,
            definition.spec.label_contract.availability_policy,
            horizon_end_ts=horizon_end_ts,
            terminal_available_ts=terminal.available_ts if terminal is not None else None,
        )
        value, flags = _cost_adjusted_value_and_flags(
            source,
            terminal,
            definition,
        )
        records.append(
            LabelValueRecord(
                label_version_id=definition.label_version_id,
                entity_id=source.series_id,
                event_ts=source.event_ts,
                horizon_end_ts=horizon_end_ts,
                label_available_ts=label_available_ts,
                value=value,
                label_contract=definition.spec.label_contract,
                quality_flags=flags,
            )
        )
    return tuple(records)


def _label_value_and_flags_from_panel(
    source: Any,
    terminal: Any,
    definition: FixedHorizonLabelDefinition,
) -> tuple[float | None, tuple[str, ...]]:
    if definition.is_midprice:
        flags = _midprice_flags_from_panel(source, terminal)
    else:
        flags = _trade_price_flags_from_panel(source, terminal)
    if flags:
        return None, flags

    source_price = _panel_price(source, definition.price_basis, "source price")
    terminal_price = _panel_price(terminal, definition.price_basis, "terminal price")
    value = terminal_price / source_price - 1.0
    if not math.isfinite(value):
        return None, ("non_finite_return",)
    return value, ()


def _cost_adjusted_value_and_flags(
    source: Any,
    terminal: Any | None,
    definition: CostAdjustedLabelDefinition,
) -> tuple[float | None, tuple[str, ...]]:
    if not _is_valid_panel_bbo_quote(source):
        return None, _cost_gap_flags(
            "entry_bbo_gap",
            extra_flags=_cost_bbo_gap_flags(source),
        )
    if terminal is None:
        return None, _cost_gap_flags("missing_terminal_bbo")
    if not _is_valid_panel_bbo_quote(terminal):
        return None, _cost_gap_flags(
            "terminal_bbo_gap",
            extra_flags=_cost_bbo_gap_flags(terminal),
        )

    source_mid = _decimal_from_panel(source.mid, "source mid")
    terminal_mid = _decimal_from_panel(terminal.mid, "terminal mid")
    if source_mid <= 0 or terminal_mid <= 0:
        return None, _cost_gap_flags("zero_or_negative_mid")

    raw_return = (terminal_mid / source_mid) - Decimal("1")
    adjusted_return = raw_return - _cost_adjustment_return(definition, source, terminal)
    if not adjusted_return.is_finite():
        return None, _cost_gap_flags("non_finite_return")
    return float(adjusted_return), ()


def _cost_adjustment_return(
    definition: CostAdjustedLabelDefinition,
    source: Any,
    terminal: Any,
) -> Decimal:
    payload = definition.spec.cost_adjustment.cost_model.to_dict()
    spread_model = _spread_cost_profile(payload)
    entry_fill = _cost_input(source, side="buy")
    exit_fill = _cost_input(terminal, side="sell")
    adjustment = (
        spread_model.cost_for_fill(entry_fill).total / entry_fill.notional
        + spread_model.cost_for_fill(exit_fill).total / exit_fill.notional
    )
    if definition.name is CostAdjustedLabelName.COST_ADJUSTED_FWD_RET:
        fixed_bps = _decimal_from_payload(
            payload.get("fixed_cost_bps"),
            "cost_model.fixed_cost_bps",
        )
        bps_model = BpsCost(fixed_bps)
        adjustment += bps_model.cost_for_fill(entry_fill).total / entry_fill.notional
    return adjustment


def _spread_cost_profile(payload: Mapping[str, Any]) -> SpreadCost:
    adjustment = _require_text(payload.get("spread_adjustment"))
    if adjustment == "half_spread_round_trip":
        return SpreadCost("half_spread")
    if adjustment == "full_spread_round_trip":
        return SpreadCost("full_spread")
    raise FastLabelPackError(
        "fast cost-adjusted labels support backtest SpreadCost half/full spread "
        "profiles only"
    )


def _cost_input(row: Any, *, side: str) -> CostInput:
    return CostInput(
        price=_decimal_from_panel(row.mid, "BBO mid"),
        quantity=Decimal("1"),
        side=side,
        bid=_decimal_from_panel(row.bid, "BBO bid"),
        ask=_decimal_from_panel(row.ask, "BBO ask"),
        spread=_decimal_from_panel(row.spread, "BBO spread"),
    )


def _cost_gap_flags(reason: str, *, extra_flags: Sequence[str] = ()) -> tuple[str, ...]:
    return _ordered_quality_flags(("label_gap", reason, *extra_flags))


def _cost_bbo_gap_flags(row: Any) -> tuple[str, ...]:
    flags = {"bbo_gap", *_quality_flags(row.bbo_quality_flags)}
    if row.bbo_missing:
        flags.add(MISSING_BBO_QUALITY_FLAG)
    if row.bbo_quarantined:
        flags.add(BBO_QUARANTINE_QUALITY_FLAG)
    if not _panel_bbo_invariants_hold(row):
        flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _ordered_quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise FastLabelPackError("quality flag entries must be non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


def _cost_bbo_rows_by_key(panel: Any) -> dict[tuple[str, datetime], Any]:
    by_key: dict[tuple[str, datetime], Any] = {}
    for row in panel.rows:
        if not _panel_has_bbo_row(row):
            continue
        key = (row.series_id, row.event_ts)
        if key in by_key:
            raise FastLabelPackError("cost-adjusted BBO rows must not duplicate series_id/event_ts")
        by_key[key] = row
    return by_key


def _panel_has_bbo_row(row: Any) -> bool:
    return (
        row.bid is not None
        or row.ask is not None
        or row.mid is not None
        or row.spread is not None
        or bool(row.bbo_quality_flags)
    )


def _cost_horizon_delta(definition: CostAdjustedLabelDefinition) -> timedelta:
    value = definition.spec.label_contract.horizon.horizon
    text = _require_text(value).lower()
    if text.endswith("m"):
        return _positive_horizon_delta(float(text[:-1]), multiplier=60)
    if text.endswith("s"):
        return _positive_horizon_delta(float(text[:-1]), multiplier=1)
    if text.endswith("h"):
        return _positive_horizon_delta(float(text[:-1]), multiplier=3600)
    raise FastLabelPackError("cost-adjusted horizon must use an s, m, or h duration suffix")


def _positive_horizon_delta(value: float, *, multiplier: int) -> timedelta:
    if not math.isfinite(value) or value <= 0:
        raise FastLabelPackError("cost-adjusted horizon must be positive and finite")
    return timedelta(seconds=value * multiplier)


def _decimal_from_panel(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise FastLabelPackError(f"{field_name} must be numeric")
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        raise FastLabelPackError(f"{field_name} must be finite")
    return parsed


def _decimal_from_payload(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise FastLabelPackError(f"{field_name} must be numeric")
    parsed = Decimal(str(value))
    if not parsed.is_finite() or parsed < 0:
        raise FastLabelPackError(f"{field_name} must be finite and non-negative")
    return parsed


def _trade_price_flags_from_panel(source: Any, terminal: Any) -> tuple[str, ...]:
    flags: set[str] = set()
    if "no_trade" in source.quality_flags:
        flags.update(("source_not_trade", *source.quality_flags))
    if "no_trade" in terminal.quality_flags:
        flags.update(("horizon_not_trade", *terminal.quality_flags))
    return tuple(sorted(flags))


def _midprice_flags_from_panel(source: Any, terminal: Any) -> tuple[str, ...]:
    flags: set[str] = set()
    if not _is_valid_panel_bbo_quote(source):
        flags.update(
            _bbo_gap_flags(
                source.bbo_quality_flags,
                reason="source_bbo_gap",
                missing=bool(source.bbo_missing),
                quarantined=bool(source.bbo_quarantined),
                invariant_violation=not _panel_bbo_invariants_hold(source),
            )
        )
    if not _is_valid_panel_bbo_quote(terminal):
        flags.update(
            _bbo_gap_flags(
                terminal.bbo_quality_flags,
                reason="horizon_bbo_gap",
                missing=bool(terminal.bbo_missing),
                quarantined=bool(terminal.bbo_quarantined),
                invariant_violation=not _panel_bbo_invariants_hold(terminal),
            )
        )
    return tuple(sorted(flags))


def _bbo_gap_flags(
    quality_flags: object,
    *,
    reason: str,
    missing: bool,
    quarantined: bool,
    invariant_violation: bool,
) -> tuple[str, ...]:
    flags = {"bbo_gap", reason, *_quality_flags(quality_flags)}
    if missing:
        flags.add(MISSING_BBO_QUALITY_FLAG)
    if quarantined:
        flags.add(BBO_QUARANTINE_QUALITY_FLAG)
    if invariant_violation:
        flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _panel_price(row: Any, price_basis: str, field_name: str) -> float:
    if price_basis == "mid":
        return _to_positive_float(row.mid, field_name)
    return _to_positive_float(row.trade_price, field_name)


def _is_valid_panel_bbo_quote(row: Any) -> bool:
    return (
        not row.bbo_missing
        and not row.bbo_quarantined
        and _panel_bbo_invariants_hold(row)
    )


def _panel_bbo_invariants_hold(row: Any) -> bool:
    bid = _to_float_or_none(row.bid)
    ask = _to_float_or_none(row.ask)
    bid_size = _to_float_or_none(row.bid_size)
    ask_size = _to_float_or_none(row.ask_size)
    mid = _to_float_or_none(row.mid)
    spread = _to_float_or_none(row.spread)
    if None in {bid, ask, bid_size, ask_size, mid, spread}:
        return False
    assert bid is not None
    assert ask is not None
    assert bid_size is not None
    assert ask_size is not None
    assert mid is not None
    assert spread is not None
    if ask < bid:
        return False
    if not math.isclose(mid, (bid + ask) / 2.0, rel_tol=0.0, abs_tol=1e-9):
        return False
    if not math.isclose(spread, ask - bid, rel_tol=0.0, abs_tol=1e-9):
        return False
    if row.available_ts < row.bar_end_ts:
        return False
    microprice = _to_float_or_none(row.microprice)
    if microprice is None:
        return True
    if bid_size <= 0.0 or ask_size <= 0.0:
        return False
    return bid <= microprice <= ask


def _shared_label_panel_from_prepared_panel(panel_or_frame: Any, polars: Any) -> Any:
    from alpha_system.labels.fast.panel import SharedLabelPanel, build_shared_label_panel

    if isinstance(panel_or_frame, SharedLabelPanel):
        return panel_or_frame

    frame = _coerce_frame(panel_or_frame, polars)
    close_rows = tuple(
        _ohlcv_mapping_from_price_row(row)
        for row in frame.filter(polars.col("price_basis") == "close").iter_rows(named=True)
    )
    if not close_rows:
        raise FastLabelPackError("shared fixed-horizon panel requires close basis rows")
    bbo_rows = tuple(
        _bbo_mapping_from_price_row(row)
        for row in frame.filter(polars.col("price_basis") == "mid").iter_rows(named=True)
    )
    first_event_ts = min(_coerce_datetime(row["event_ts"], "event_ts") for row in close_rows)
    symbol = _panel_symbol(close_rows[0])
    return build_shared_label_panel(
        symbol=symbol,
        year=first_event_ts.year,
        ohlcv_rows=close_rows,
        bbo_rows=bbo_rows,
    )


def _ohlcv_mapping_from_price_row(row: Mapping[str, Any]) -> dict[str, Any]:
    price = _to_positive_float(row["price"], "close")
    high = row.get("high")
    low = row.get("low")
    return {
        "instrument_id": _require_text(row["instrument_id"]),
        "contract_id": _require_text(row["contract_id"]),
        "series_id": _require_text(row["series_id"]),
        "bar_end_ts": _coerce_datetime(row["bar_end_ts"], "bar_end_ts"),
        "event_ts": _coerce_datetime(row["event_ts"], "event_ts"),
        "available_ts": _coerce_datetime(row["available_ts"], "available_ts"),
        "close": price,
        "high": _to_positive_float(high, "high") if high is not None else price,
        "low": _to_positive_float(low, "low") if low is not None else price,
        "volume": row.get("volume"),
        "quality_flags": list(_quality_flags(row["quality_flags"])),
        "session_label": str(row.get("session_label") or ""),
    }


def _bbo_mapping_from_price_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "instrument_id": _require_text(row["instrument_id"]),
        "contract_id": _require_text(row["contract_id"]),
        "series_id": _require_text(row["series_id"]),
        "bar_end_ts": _coerce_datetime(row["bar_end_ts"], "bar_end_ts"),
        "event_ts": _coerce_datetime(row["event_ts"], "event_ts"),
        "available_ts": _coerce_datetime(row["available_ts"], "available_ts"),
        "bid": row.get("bid"),
        "ask": row.get("ask"),
        "bid_size": row.get("bid_size"),
        "ask_size": row.get("ask_size"),
        "mid": row.get("mid", row["price"]),
        "spread": row.get("spread"),
        "microprice": row.get("microprice"),
        "quality_flags": list(_quality_flags(row["quality_flags"])),
        "session_label": str(row.get("session_label") or ""),
    }


def _panel_symbol(row: Mapping[str, Any]) -> str:
    instrument = _require_text(row["instrument_id"]).upper()
    for separator in ("_", "-", " "):
        if separator in instrument:
            return instrument.split(separator, 1)[0]
    return "".join(character for character in instrument if character.isalpha()) or instrument


def _prepare_panel(frame: Any, polars: Any) -> Any:
    pl = polars
    prepared_rows = []
    for row in frame.iter_rows(named=True):
        flags = _quality_flags(row["quality_flags"])
        basis = _require_text(row["price_basis"])
        prepared = dict(row)
        prepared["quality_flags"] = list(flags)
        prepared["is_real_trade_bar"] = basis != "close" or "no_trade" not in flags
        prepared["bbo_missing"] = MISSING_BBO_QUALITY_FLAG in flags
        prepared["bbo_quarantined"] = BBO_QUARANTINE_QUALITY_FLAG in flags
        prepared["bbo_invariant_violation"] = (
            basis == "mid" and not _bbo_invariants_hold(prepared)
        )
        prepared["is_valid_bbo_quote"] = (
            basis != "mid"
            or (
                not prepared["bbo_missing"]
                and not prepared["bbo_quarantined"]
                and not prepared["bbo_invariant_violation"]
            )
        )
        prepared_rows.append(prepared)
    if not prepared_rows:
        raise FastLabelPackError("prepared label price panel must be non-empty")
    # infer_schema_length=None: scan all rows so int->float widening (real-data
    # prices) is inferred deterministically rather than failing on a later f64.
    return pl.DataFrame(prepared_rows, infer_schema_length=None).sort(
        ("price_basis", "series_id", "event_ts", "available_ts")
    )


def _bbo_invariants_hold(row: Mapping[str, Any]) -> bool:
    bid = _to_float_or_none(row.get("bid"))
    ask = _to_float_or_none(row.get("ask"))
    bid_size = _to_float_or_none(row.get("bid_size"))
    ask_size = _to_float_or_none(row.get("ask_size"))
    mid = _to_float_or_none(row.get("mid"))
    spread = _to_float_or_none(row.get("spread"))
    if None in {bid, ask, bid_size, ask_size, mid, spread}:
        return False
    assert bid is not None
    assert ask is not None
    assert bid_size is not None
    assert ask_size is not None
    assert mid is not None
    assert spread is not None
    if ask < bid:
        return False
    if not math.isclose(mid, (bid + ask) / 2.0, rel_tol=0.0, abs_tol=0.0):
        return False
    if not math.isclose(spread, ask - bid, rel_tol=0.0, abs_tol=0.0):
        return False
    if _coerce_datetime(row["available_ts"], "available_ts") < _coerce_datetime(
        row["bar_end_ts"],
        "bar_end_ts",
    ):
        return False
    microprice = _to_float_or_none(row.get("microprice"))
    if microprice is None:
        return True
    if bid_size <= 0.0 or ask_size <= 0.0:
        return False
    return bid <= microprice <= ask


def _ohlcv_panel_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "price_basis": "close",
        "instrument_id": _require_text(row["instrument_id"]),
        "contract_id": _require_text(row["contract_id"]),
        "series_id": _require_text(row["series_id"]),
        "bar_end_ts": _coerce_datetime(row["bar_end_ts"], "bar_end_ts"),
        "event_ts": _coerce_datetime(row["event_ts"], "event_ts"),
        "available_ts": _coerce_datetime(row["available_ts"], "available_ts"),
        "price": _to_positive_float(row["close"], "close"),
        "high": _to_positive_float(row.get("high", row["close"]), "high"),
        "low": _to_positive_float(row.get("low", row["close"]), "low"),
        "volume": _to_float_or_none(row.get("volume")),
        "bid": None,
        "ask": None,
        "bid_size": None,
        "ask_size": None,
        "mid": None,
        "spread": None,
        "microprice": None,
        "quality_flags": list(_quality_flags(row["quality_flags"])),
        "session_label": str(row.get("session_label") or ""),
    }


def _bbo_panel_row(row: Mapping[str, Any]) -> dict[str, Any]:
    mid = _to_float(row["mid"], "mid")
    return {
        "price_basis": "mid",
        "instrument_id": _require_text(row["instrument_id"]),
        "contract_id": _require_text(row["contract_id"]),
        "series_id": _require_text(row["series_id"]),
        "bar_end_ts": _coerce_datetime(row["bar_end_ts"], "bar_end_ts"),
        "event_ts": _coerce_datetime(row["event_ts"], "event_ts"),
        "available_ts": _coerce_datetime(row["available_ts"], "available_ts"),
        "price": mid,
        "bid": _to_float(row["bid"], "bid"),
        "ask": _to_float(row["ask"], "ask"),
        "bid_size": _to_float(row["bid_size"], "bid_size"),
        "ask_size": _to_float(row["ask_size"], "ask_size"),
        "mid": mid,
        "spread": _to_float(row["spread"], "spread"),
        "microprice": _to_float_or_none(row.get("microprice")),
        "quality_flags": list(_quality_flags(row["quality_flags"])),
        "session_label": str(row.get("session_label") or ""),
    }


def _computation_metadata(
    panel: Any,
    pack: FastLabelPack,
    *,
    records_by_label: Mapping[str, tuple[LabelValueRecord, ...]],
    event_sets: Mapping[str, Mapping[str, set[datetime]]],
) -> FastLabelComputationMetadata:
    shared_counts = {"close": len(panel.rows)}
    if any(_definition_price_basis(definition) == "mid" for definition in pack.definitions):
        shared_counts["mid"] = len(panel.rows)
    labels: list[FastFixedHorizonLabelMetadata] = []
    for definition in pack.definitions:
        records = records_by_label[definition.label_version_id]
        price_basis = _definition_price_basis(definition)
        same_basis_events = event_sets[price_basis]
        peer_events = set().union(
            *(
                events
                for version_id, events in same_basis_events.items()
                if version_id != definition.label_version_id
            )
        )
        overlap_count = len({record.event_ts for record in records}.intersection(peer_events))
        labels.append(
            FastFixedHorizonLabelMetadata(
                label_id=definition.label_id,
                label_version_id=definition.label_version_id,
                price_basis=price_basis,
                horizon_minutes=_metadata_horizon_minutes(definition),
                n_eff=len(records),
                null_value_count=sum(1 for record in records if record.value is None),
                horizon_overlap_event_count=overlap_count,
                horizon_overlap_metadata=_metadata_horizon_overlap(definition, len(records)),
                label_family=_definition_contract(definition).family.value,
                terminal_kind=_metadata_terminal_kind(definition),
            )
        )
    return FastLabelComputationMetadata(
        producer_engine_id=FAST_LABEL_PRODUCER_ENGINE_ID,
        value_schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
        pack_id=pack.pack_id,
        shared_panel_rows_by_basis=shared_counts,
        prepared_guard_columns=(
            "is_real_trade_bar",
            "is_valid_bbo_quote",
            "bbo_missing",
            "bbo_quarantined",
            "bbo_invariant_violation",
        ),
        labels=tuple(labels),
    )


def _write_records(
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
    *,
    metadata: FastLabelComputationMetadata,
    value_store_format: ValueStoreFormat,
) -> _WriteResult:
    store_format = _coerce_value_store_format(value_store_format)
    record_dicts = _canonical_record_dicts(records)
    value_content_hash = compute_value_content_hash(record_dicts)
    jsonl_path: Path | None = None
    parquet_path: Path | None = None
    wrote_output = False

    if store_format in (ValueStoreFormat.JSONL, ValueStoreFormat.DUAL):
        jsonl_path = plan.output_path
        wrote_output = _write_jsonl_if_changed(
            jsonl_path,
            _render_jsonl(plan, records, metadata=metadata),
        )

    if store_format in (ValueStoreFormat.PARQUET, ValueStoreFormat.DUAL):
        parquet_path = plan.output_path.with_name(_parquet_filename())
        _require_under_root(parquet_path, plan.alpha_data_root)
        if not parquet_is_current(parquet_path, value_content_hash):
            write_parquet_values(
                record_dicts,
                parquet_path,
                plan_dict={
                    **plan.to_dict(),
                    "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
                    "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
                    "fast_label_metadata": metadata.to_dict(),
                },
                content_hash=value_content_hash,
                schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
                value_count=len(record_dicts),
            )
            wrote_output = True

    output_path = parquet_path if store_format is ValueStoreFormat.PARQUET else plan.output_path
    event_ts_values = tuple(record.event_ts.isoformat() for record in records)
    available_ts_values = tuple(record.label_available_ts.isoformat() for record in records)
    return _WriteResult(
        wrote_output=wrote_output,
        output_path=output_path,
        handle=ValueStoreHandle(
            format=store_format,
            jsonl_path=jsonl_path.as_posix() if jsonl_path is not None else None,
            parquet_path=parquet_path.as_posix() if parquet_path is not None else None,
            value_count=len(records),
            content_hash=value_content_hash,
            schema_version=FAST_LABEL_VALUE_SCHEMA_VERSION,
            dataset_version_id=plan.dataset_version_id,
            set_id=_label_set_id(plan.label_contracts),
            partition_id=plan.partition_id,
            min_event_ts=min(event_ts_values),
            max_event_ts=max(event_ts_values),
            min_available_ts=min(available_ts_values),
            max_available_ts=max(available_ts_values),
        ),
    )


def _canonical_record_dicts(
    records: Sequence[LabelValueRecord],
) -> list[Mapping[str, Any]]:
    """Return label value records in byte-stable content-hash order."""

    return [
        record.to_dict()
        for record in sorted(
            records,
            key=lambda item: (
                item.label_version_id,
                item.entity_id,
                item.event_ts.isoformat(),
                item.label_available_ts.isoformat(),
            ),
        )
    ]


def _render_jsonl(
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
    *,
    metadata: FastLabelComputationMetadata,
) -> str:
    lines = [
        canonical_serialize(
            {
                "record_type": "fast_label_materialization_plan",
                "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
                "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
                "plan": plan.to_dict(),
                "fast_label_metadata": metadata.to_dict(),
            }
        )
    ]
    for record in records:
        lines.append(
            canonical_serialize(
                {
                    "record_type": "fast_label_value",
                    "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
                    "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
                    "plan_id": plan.plan_id,
                    "dataset_version_id": plan.dataset_version_id,
                    "partition_id": plan.partition_id,
                    "value": record.to_dict(),
                }
            )
        )
    return "\n".join(lines) + "\n"


def _write_jsonl_if_changed(path: Path, payload: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(payload)
    temp_path.replace(path)
    return True


def _validate_plan_matches_pack(plan: LabelMaterializationPlan, pack: FastLabelPack) -> None:
    contracts_by_version = {
        contract.derive_label_version().label_version_id: contract
        for contract in plan.label_contracts
    }
    pack_contracts_by_version = {
        definition.label_version_id: _definition_contract(definition)
        for definition in pack.definitions
    }
    if contracts_by_version != pack_contracts_by_version:
        raise FastLabelPackError("LabelMaterializationPlan contracts must match fast pack")


def _validate_records(
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
) -> None:
    if not records:
        raise FastLabelPackError("fast label materialization produced no records")
    contracts_by_version = {
        contract.derive_label_version().label_version_id: contract
        for contract in plan.label_contracts
    }
    seen_versions: set[str] = set()
    for record in records:
        if not isinstance(record, LabelValueRecord):
            raise FastLabelPackError("fast materialization produced a non-LabelValueRecord")
        contract = contracts_by_version.get(record.label_version_id)
        if contract is None:
            raise FastLabelPackError("fast record outside LabelMaterializationPlan")
        seen_versions.add(record.label_version_id)
        if record.horizon_end_ts < record.event_ts:
            raise FastLabelPackError("LabelValueRecord.horizon_end_ts precedes event_ts")
        if record.label_available_ts < record.horizon_end_ts:
            raise FastLabelPackError("LabelValueRecord.label_available_ts precedes horizon_end_ts")
        if record.label_available_ts < contract.availability_policy.availability_time:
            raise FastLabelPackError("LabelValueRecord.label_available_ts precedes LabelSpec")
    missing = tuple(
        label_version_id
        for label_version_id in plan.label_version_ids
        if label_version_id not in seen_versions
    )
    if missing:
        raise FastLabelPackError("fast materialization missing labels: " + ", ".join(missing))


def _registry_metadata(metadata: Mapping[str, Any] | None) -> dict[str, JsonValue]:
    merged: dict[str, Any] = {
        "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
        "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
    }
    if metadata:
        merged.update(metadata)
    return FrozenJsonMapping.from_mapping(merged, field_name="registry_metadata").to_dict()


def _definition_contract(definition: object) -> LabelContractSpec:
    if isinstance(definition, FixedHorizonLabelDefinition):
        return definition.contract
    if isinstance(definition, CostAdjustedLabelDefinition):
        return definition.spec.label_contract
    raise FastLabelPackError("fast label packs support fixed-horizon and cost-adjusted definitions")


def _definition_version(definition: object) -> LabelVersion:
    if isinstance(definition, (FixedHorizonLabelDefinition, CostAdjustedLabelDefinition)):
        return definition.version
    raise FastLabelPackError("fast label definition does not expose a LabelVersion")


def _definition_price_basis(definition: FastSupportedLabelDefinition) -> str:
    if isinstance(definition, FixedHorizonLabelDefinition):
        return definition.price_basis
    if isinstance(definition, CostAdjustedLabelDefinition):
        return "mid"
    raise FastLabelPackError("unsupported fast label definition")


def _fixed_horizon_minutes_or_none(definition: FixedHorizonLabelDefinition) -> int | None:
    try:
        return definition.horizon_minutes
    except FixedHorizonLabelError as exc:
        if definition.label_id in {"session_close", "maintenance_flat"}:
            return None
        raise FastLabelPackError(str(exc)) from exc


def _terminal_model_key(definition: FixedHorizonLabelDefinition) -> tuple[str, str]:
    horizon_minutes = _fixed_horizon_minutes_or_none(definition)
    if horizon_minutes is not None:
        return ("fixed_horizon", f"{definition.price_basis}:{horizon_minutes}")
    return ("close_out", definition.label_id)


def _close_out_terminal_kind(definition: FixedHorizonLabelDefinition) -> Any:
    from alpha_system.labels.fast.panel import TerminalKind

    if definition.label_id == "session_close":
        return TerminalKind.SESSION_CLOSE
    if definition.label_id == "maintenance_flat":
        return TerminalKind.MAINTENANCE_FLAT
    raise FastLabelPackError(f"unsupported close-out label: {definition.label_id}")


def _metadata_horizon_minutes(definition: FastSupportedLabelDefinition) -> int:
    if isinstance(definition, FixedHorizonLabelDefinition):
        horizon_minutes = _fixed_horizon_minutes_or_none(definition)
        return horizon_minutes if horizon_minutes is not None else 0
    if isinstance(definition, CostAdjustedLabelDefinition):
        seconds = int(_cost_horizon_delta(definition).total_seconds())
        return seconds // 60 if seconds % 60 == 0 else 0
    raise FastLabelPackError("unsupported fast label metadata definition")


def _metadata_horizon_overlap(
    definition: FastSupportedLabelDefinition,
    record_count: int,
) -> Mapping[str, JsonValue]:
    if isinstance(definition, FixedHorizonLabelDefinition):
        horizon_minutes = _fixed_horizon_minutes_or_none(definition)
        if horizon_minutes is not None:
            return compute_horizon_overlap_metadata(
                definition.name,
                raw_row_count=record_count,
            ).to_dict()
        metadata = definition.contract.contract_metadata.to_dict().get(
            "horizon_overlap_metadata",
            {},
        )
        return dict(metadata) if isinstance(metadata, Mapping) else {}
    return {}


def _metadata_terminal_kind(definition: FastSupportedLabelDefinition) -> str:
    if isinstance(definition, FixedHorizonLabelDefinition):
        return (
            "fixed_horizon"
            if _fixed_horizon_minutes_or_none(definition) is not None
            else definition.label_id
        )
    if isinstance(definition, CostAdjustedLabelDefinition):
        return "cost_adjusted_exact_bbo_horizon"
    raise FastLabelPackError("unsupported fast label metadata definition")


def _coerce_frame(frame: Any, polars: Any) -> Any:
    if isinstance(frame, polars.LazyFrame):
        frame = frame.collect()
    if not isinstance(frame, polars.DataFrame):
        raise FastLabelPackError("price_frame must be a Polars DataFrame or LazyFrame")
    _require_columns(
        frame,
        (
            "price_basis",
            "series_id",
            "event_ts",
            "bar_end_ts",
            "available_ts",
            "price",
            "quality_flags",
        ),
    )
    return frame.sort(("price_basis", "series_id", "event_ts", "available_ts"))


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise FastLabelPackError("label price panel missing columns: " + ", ".join(missing))


def _coerce_value_store_format(value: object) -> ValueStoreFormat:
    try:
        if isinstance(value, ValueStoreFormat):
            return value
        if isinstance(value, str):
            return ValueStoreFormat(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ValueStoreFormat)
        raise FastLabelPackError(f"value_store_format must be one of: {allowed}") from exc
    raise FastLabelPackError("value_store_format must be a ValueStoreFormat")


def _label_set_id(label_contracts: tuple[LabelContractSpec, ...]) -> str:
    return "lset_" + content_hash(
        {
            "schema": "alpha_system.labels.materialization.v1",
            "label_contracts": [contract.to_contract_dict() for contract in label_contracts],
        }
    )


def _require_pack(pack: FastLabelPack) -> FastLabelPack:
    if not isinstance(pack, FastLabelPack):
        raise FastLabelPackError("fast label materialization requires a FastLabelPack")
    for definition in pack.definitions:
        contract = _definition_contract(definition)
        if contract.family not in {LabelFamily.FIXED_HORIZON, LabelFamily.COST_ADJUSTED}:
            raise FastLabelPackError(
                "fast label pack supports fixed-horizon and cost-adjusted labels only"
            )
        if isinstance(definition, FixedHorizonLabelDefinition):
            _fixed_horizon_minutes_or_none(definition)
    return pack


def _require_under_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise FastLabelPackError("materialized label output path must stay under ALPHA_DATA_ROOT")


def _parquet_filename() -> str:
    return "values." + "parquet"


def _quality_flags(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        flags = (value,)
    elif isinstance(value, Sequence):
        flags = tuple(value)
    else:
        raise FastLabelPackError("quality_flags must be a sequence of strings")
    normalized: set[str] = set()
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise FastLabelPackError("quality_flags entries must be non-empty strings")
        normalized.add(flag.strip().lower())
    return tuple(sorted(normalized))


def _coerce_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise FastLabelPackError(f"{field_name} must be timezone-aware")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FastLabelPackError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _to_positive_float(value: object, field_name: str) -> float:
    parsed = _to_float(value, field_name)
    if parsed <= 0.0:
        raise FastLabelPackError(f"{field_name} must be positive")
    return parsed


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise FastLabelPackError(f"{field_name} must be numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise FastLabelPackError(f"{field_name} must be numeric") from exc
    if not math.isfinite(parsed):
        raise FastLabelPackError(f"{field_name} must be finite")
    return parsed


def _to_float_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    return _to_float(value, "optional numeric field")


def _require_text(value: object) -> str:
    if not isinstance(value, str):
        raise FastLabelPackError("value must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FastLabelPackError("value must be a non-empty single-line string")
    return text


__all__ = [
    "FAST_LABEL_PRODUCER_ENGINE_ID",
    "FAST_LABEL_VALUE_SCHEMA_VERSION",
    "FastFixedHorizonLabelMetadata",
    "FastLabelComputation",
    "FastLabelComputationMetadata",
    "FastLabelDeclaration",
    "FastLabelMaterializer",
    "FastLabelPack",
    "FastLabelPackError",
    "LabelPanelFrameRequest",
    "SupportedLabelDefinition",
]
