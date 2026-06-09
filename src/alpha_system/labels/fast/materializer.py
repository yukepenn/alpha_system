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
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from time import perf_counter
from typing import Any

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
from alpha_system.labels.families.fixed_horizon import FixedHorizonLabelDefinition
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

    definition: FixedHorizonLabelDefinition

    def __post_init__(self) -> None:
        if not isinstance(self.definition, FixedHorizonLabelDefinition):
            raise FastLabelPackError("fast label declarations require fixed-horizon definitions")

    @property
    def label_contract(self) -> LabelContractSpec:
        return self.definition.contract

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
    definitions: Sequence[FixedHorizonLabelDefinition]
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
            if not isinstance(definition, FixedHorizonLabelDefinition):
                raise FastLabelPackError(
                    "FastLabelPack currently supports fixed-horizon definitions only"
                )
            if declaration.definition != definition:
                raise FastLabelPackError("FastLabelPack declaration order must match definitions")
            expected = LabelVersion.derive(definition.contract)
            if definition.version != expected:
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
        return tuple(definition.contract for definition in self.definitions)

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

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "label_id": self.label_id,
            "label_version_id": self.label_version_id,
            "price_basis": self.price_basis,
            "horizon_minutes": self.horizon_minutes,
            "n_eff": self.n_eff,
            "null_value_count": self.null_value_count,
            "horizon_overlap_event_count": self.horizon_overlap_event_count,
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
        prepare_price_panel, evaluate every governed label horizon in one pass.
        """

        pl = require_dependency("polars")
        pack = _require_pack(pack)
        all_records: list[LabelValueRecord] = []
        for declaration in pack.declarations:
            all_records.extend(
                _compute_fixed_horizon_records(prepared_panel, declaration.definition, pl)
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
        records_by_label: dict[str, tuple[LabelValueRecord, ...]] = {}
        event_sets: dict[str, dict[str, set[datetime]]] = defaultdict(dict)
        all_records: list[LabelValueRecord] = []

        for declaration in pack.declarations:
            definition = declaration.definition
            records = _compute_fixed_horizon_records(frame, definition, pl)
            records_by_label[definition.label_version_id] = records
            event_sets[definition.price_basis][definition.label_version_id] = {
                record.event_ts for record in records
            }
            all_records.extend(records)

        metadata = _computation_metadata(
            frame,
            pack,
            records_by_label=records_by_label,
            event_sets=event_sets,
            polars=pl,
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
                lineage = LabelLineageRecord(
                    label_version=definition.version,
                    label_contract=definition.contract,
                    label_spec_id=definition.label_spec_id,
                    contract_provenance={
                        "producer_engine_id": FAST_LABEL_PRODUCER_ENGINE_ID,
                        "value_schema_version": FAST_LABEL_VALUE_SCHEMA_VERSION,
                    },
                )
                records.append(
                    label_registry.register_materialized_label(
                        materialization_result,
                        label_contract=definition.contract,
                        label_version=definition.version,
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


def _compute_fixed_horizon_records(
    frame: Any,
    definition: FixedHorizonLabelDefinition,
    polars: Any,
) -> tuple[LabelValueRecord, ...]:
    basis_frame = frame.filter(polars.col("price_basis") == definition.price_basis)
    if basis_frame.is_empty():
        raise FastLabelPackError(f"price panel missing {definition.price_basis} basis rows")
    horizon = definition.horizon_minutes
    sources = basis_frame.with_columns(
        (polars.col("event_ts") + polars.duration(minutes=horizon)).alias(
            "__terminal_event_ts"
        )
    )
    terminals = basis_frame.select(
        (
            polars.col("series_id"),
            polars.col("event_ts").alias("__terminal_event_ts"),
            polars.col("available_ts").alias("__terminal_available_ts"),
            polars.col("price").alias("__terminal_price"),
            polars.col("quality_flags").alias("__terminal_quality_flags"),
            polars.col("is_real_trade_bar").alias("__terminal_is_real_trade_bar"),
            polars.col("is_valid_bbo_quote").alias("__terminal_is_valid_bbo_quote"),
            polars.col("bbo_missing").alias("__terminal_bbo_missing"),
            polars.col("bbo_quarantined").alias("__terminal_bbo_quarantined"),
            polars.col("bbo_invariant_violation").alias(
                "__terminal_bbo_invariant_violation"
            ),
        )
    )
    joined = sources.join(
        terminals,
        on=("series_id", "__terminal_event_ts"),
        how="inner",
    ).sort(("series_id", "event_ts", "available_ts"))

    # Vectorize the common case (valid, unflagged bars) instead of running the
    # per-row Python flag/value path over every joined row via iter_rows(named=True)
    # -- that loop was ~91% of the label fast-path wall-clock (FCFP-P13 profile).
    # The value (terminal/source - 1), the price-validity guard, and the flag
    # TRIGGER are computed as columns; valid+unflagged rows then read a precomputed
    # return with empty flags, while flagged or non-positive-price rows (the
    # minority) fall through to the EXACT same `_label_value_and_flags` Python path
    # on a lazily materialized row dict -- so reference parity is preserved bit for
    # bit. label_available_ts keeps its exact max(terminal, floor) semantics.
    if definition.is_midprice:
        trigger_expr = ~(
            polars.col("is_valid_bbo_quote") & polars.col("__terminal_is_valid_bbo_quote")
        )
    else:
        trigger_expr = ~(
            polars.col("is_real_trade_bar") & polars.col("__terminal_is_real_trade_bar")
        )
    joined = joined.with_columns(
        (polars.col("__terminal_price") / polars.col("price") - 1.0).alias("__fhl_ret"),
        (
            (polars.col("price") > 0.0) & (polars.col("__terminal_price") > 0.0)
        ).alias("__fhl_price_valid"),
        trigger_expr.fill_null(True).alias("__fhl_trigger"),
    )
    series_col = joined["series_id"].to_list()
    event_col = joined["event_ts"].to_list()
    horizon_col = joined["__terminal_event_ts"].to_list()
    term_avail_col = joined["__terminal_available_ts"].to_list()
    ret_col = joined["__fhl_ret"].to_list()
    price_valid_col = joined["__fhl_price_valid"].to_list()
    trigger_col = joined["__fhl_trigger"].to_list()

    label_version_id = definition.label_version_id
    contract = definition.contract
    availability_floor = contract.availability_policy.availability_time

    records: list[LabelValueRecord] = []
    for i in range(joined.height):
        if trigger_col[i] or not price_valid_col[i]:
            # Rare path: exact reference-parity Python logic on the full row.
            value, flags = _label_value_and_flags(joined.row(i, named=True), definition)
        else:
            ret = ret_col[i]
            if ret is not None and math.isfinite(ret):
                value, flags = ret, ()
            else:
                value, flags = None, ("non_finite_return",)
        # The polars panel stores Datetime(time_zone="UTC"); .to_list() yields
        # tz-aware UTC datetimes, and LabelValueRecord.__post_init__ already
        # validates/normalizes each field via _require_aware_datetime. Re-coercing
        # here (3x per record) was ~0.74s of redundant fast-path-only overhead the
        # reference engine never pays. Pass the values straight through -- the
        # record's own validation preserves exact reference parity.
        terminal_available_ts = term_avail_col[i]
        if terminal_available_ts < availability_floor:
            terminal_available_ts = availability_floor
        records.append(
            LabelValueRecord(
                label_version_id=label_version_id,
                entity_id=_require_text(series_col[i]),
                event_ts=event_col[i],
                horizon_end_ts=horizon_col[i],
                label_available_ts=terminal_available_ts,
                value=value,
                label_contract=contract,
                quality_flags=flags,
            )
        )
    return tuple(records)


def _label_value_and_flags(
    row: Mapping[str, Any],
    definition: FixedHorizonLabelDefinition,
) -> tuple[float | None, tuple[str, ...]]:
    if definition.is_midprice:
        flags = _midprice_flags(row)
    else:
        flags = _trade_price_flags(row)
    if flags:
        return None, flags

    source_price = _to_positive_float(row["price"], "source price")
    terminal_price = _to_positive_float(row["__terminal_price"], "terminal price")
    value = terminal_price / source_price - 1.0
    if not math.isfinite(value):
        return None, ("non_finite_return",)
    return value, ()


def _trade_price_flags(row: Mapping[str, Any]) -> tuple[str, ...]:
    flags: set[str] = set()
    if not bool(row["is_real_trade_bar"]):
        flags.update(("source_not_trade", *_quality_flags(row["quality_flags"])))
    if not bool(row["__terminal_is_real_trade_bar"]):
        flags.update(
            ("horizon_not_trade", *_quality_flags(row["__terminal_quality_flags"]))
        )
    return tuple(sorted(flags))


def _midprice_flags(row: Mapping[str, Any]) -> tuple[str, ...]:
    flags: set[str] = set()
    if not bool(row["is_valid_bbo_quote"]):
        flags.update(
            _bbo_gap_flags(
                row["quality_flags"],
                reason="source_bbo_gap",
                missing=bool(row["bbo_missing"]),
                quarantined=bool(row["bbo_quarantined"]),
                invariant_violation=bool(row["bbo_invariant_violation"]),
            )
        )
    if not bool(row["__terminal_is_valid_bbo_quote"]):
        flags.update(
            _bbo_gap_flags(
                row["__terminal_quality_flags"],
                reason="horizon_bbo_gap",
                missing=bool(row["__terminal_bbo_missing"]),
                quarantined=bool(row["__terminal_bbo_quarantined"]),
                invariant_violation=bool(row["__terminal_bbo_invariant_violation"]),
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
        "bid": None,
        "ask": None,
        "bid_size": None,
        "ask_size": None,
        "mid": None,
        "spread": None,
        "microprice": None,
        "quality_flags": list(_quality_flags(row["quality_flags"])),
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
    }


def _computation_metadata(
    frame: Any,
    pack: FastLabelPack,
    *,
    records_by_label: Mapping[str, tuple[LabelValueRecord, ...]],
    event_sets: Mapping[str, Mapping[str, set[datetime]]],
    polars: Any,
) -> FastLabelComputationMetadata:
    shared_counts = {
        str(row["price_basis"]): int(row["count"])
        for row in frame.group_by("price_basis")
        .agg(polars.len().alias("count"))
        .iter_rows(named=True)
    }
    labels: list[FastFixedHorizonLabelMetadata] = []
    for definition in pack.definitions:
        records = records_by_label[definition.label_version_id]
        same_basis_events = event_sets[definition.price_basis]
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
                price_basis=definition.price_basis,
                horizon_minutes=definition.horizon_minutes,
                n_eff=len(records),
                null_value_count=sum(1 for record in records if record.value is None),
                horizon_overlap_event_count=overlap_count,
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
        definition.label_version_id: definition.contract for definition in pack.definitions
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
        if definition.contract.family is not LabelFamily.FIXED_HORIZON:
            raise FastLabelPackError("fast label pack supports fixed-horizon labels only")
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
