"""Polars-based pack materialization core for governed feature specs.

The fast path computes values only. Feature identity still comes from
``FeatureVersion.derive(FeatureSpec)`` and registry writes still go through
``FeatureStore``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any

from alpha_system.core.value_store import (
    ValueStoreFormat,
    ValueStoreHandle,
    compute_value_content_hash,
    parquet_is_current,
    write_parquet_values,
)
from alpha_system.data.foundation.canonical_loader import (
    DEFAULT_OHLCV_PARTITION_SCHEMA,
    load_canonical_ohlcv_rows,
)
from alpha_system.data.storage import require_dependency
from alpha_system.features.contracts import (
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
    FrozenJsonMapping,
)
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.engine import (
    FeatureMaterializationPlan,
    FeatureMaterializationResult,
    build_feature_materialization_plan,
)
from alpha_system.features.store import FeatureStore
from alpha_system.governance.feature_request import FeatureRequest
from alpha_system.governance.serialization import JsonValue, canonical_serialize

FAST_PRODUCER_ENGINE_ID = "alpha_system.features.fast.pack_materializer.v1"
FAST_VALUE_SCHEMA_VERSION = "alpha_system.features.fast.values.v1"
_REGISTRY_WRITE_LOCK = Lock()

type CanonicalOhlcvRowLoader = Callable[..., Sequence[Mapping[str, Any]]]


class PackMaterializerError(ValueError):
    """Raised when fast-path materialization fails closed."""


@dataclass(frozen=True, slots=True)
class SymbolYearFrameRequest:
    """Request to load one symbol-year canonical OHLCV frame through a caller root."""

    canonical_root: str | Path
    dataset_version_id: str
    symbol: str
    year: int
    start_ts: str | None = None
    end_ts: str | None = None
    partition_schema: str = DEFAULT_OHLCV_PARTITION_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_version_id", _require_text(self.dataset_version_id))
        object.__setattr__(self, "symbol", _require_text(self.symbol).upper())
        if isinstance(self.year, bool) or not isinstance(self.year, int) or self.year < 1970:
            raise PackMaterializerError("year must be an integer >= 1970")
        object.__setattr__(self, "partition_schema", _require_text(self.partition_schema))
        if self.start_ts is not None:
            object.__setattr__(self, "start_ts", _require_text(self.start_ts))
        if self.end_ts is not None:
            object.__setattr__(self, "end_ts", _require_text(self.end_ts))

    @property
    def resolved_start_ts(self) -> str:
        """Return the explicit or calendar-year UTC lower bound."""

        return self.start_ts or f"{self.year:04d}-01-01T00:00:00+00:00"

    @property
    def resolved_end_ts(self) -> str:
        """Return the explicit or calendar-year UTC upper bound."""

        return self.end_ts or f"{self.year + 1:04d}-01-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class FastFeatureDeclaration:
    """One governed feature value expression in a vectorized pack."""

    feature_spec: FeatureSpec
    value_expr: Any
    quality_flags_expr: Any | None = None
    entity_id_expr: Any | None = None
    event_ts_expr: Any | None = None
    available_ts_expr: Any | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.feature_spec, FeatureSpec):
            raise PackMaterializerError("FastFeatureDeclaration requires a FeatureSpec")

    @property
    def feature_version(self) -> FeatureVersion:
        """Return the reference-engine identity for this feature spec."""

        return FeatureVersion.derive(self.feature_spec)

    @property
    def feature_version_id(self) -> str:
        """Return the reference-engine feature version id."""

        return self.feature_version.feature_version_id


@dataclass(frozen=True, slots=True)
class FastFeaturePack:
    """A governed feature set plus the Polars expressions that compute it."""

    feature_set: FeatureSetSpec
    declarations: Sequence[FastFeatureDeclaration]
    prepare_frame: Callable[[Any], Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.feature_set, FeatureSetSpec):
            raise PackMaterializerError("FastFeaturePack.feature_set must be a FeatureSetSpec")
        declarations = tuple(self.declarations)
        if not declarations:
            raise PackMaterializerError("FastFeaturePack.declarations must be non-empty")
        if tuple(declaration.feature_spec for declaration in declarations) != tuple(
            self.feature_set.features
        ):
            raise PackMaterializerError(
                "FastFeaturePack declarations must match FeatureSetSpec feature order"
            )
        for declaration in declarations:
            expected = FeatureVersion.derive(declaration.feature_spec)
            if declaration.feature_version != expected:
                raise PackMaterializerError("fast declaration FeatureVersion mismatch")
        if self.prepare_frame is not None and not callable(self.prepare_frame):
            raise PackMaterializerError("FastFeaturePack.prepare_frame must be callable")
        object.__setattr__(self, "declarations", declarations)


class PackMaterializer:
    """Compute, persist, and register governed feature packs through the keystone path."""

    def __init__(
        self,
        *,
        canonical_ohlcv_loader: CanonicalOhlcvRowLoader = load_canonical_ohlcv_rows,
    ) -> None:
        self._canonical_ohlcv_loader = canonical_ohlcv_loader
        self._frame_cache: dict[SymbolYearFrameRequest, Any] = {}

    def load_symbol_year_ohlcv_frame(self, request: SymbolYearFrameRequest) -> Any:
        """Load one symbol-year canonical OHLCV frame once and cache it in memory."""

        polars = require_dependency("polars")
        if not isinstance(request, SymbolYearFrameRequest):
            raise PackMaterializerError("load request must be a SymbolYearFrameRequest")
        cached = self._frame_cache.get(request)
        if cached is not None:
            return cached
        rows = self._canonical_ohlcv_loader(
            canonical_root=request.canonical_root,
            dataset_version_id=request.dataset_version_id,
            symbol=request.symbol,
            start_ts=request.resolved_start_ts,
            end_ts=request.resolved_end_ts,
            partition_schema=request.partition_schema,
        )
        frame = self.frame_from_rows(rows, polars=polars)
        self._frame_cache[request] = frame
        return frame

    def frame_from_rows(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        polars: Any | None = None,
    ) -> Any:
        """Build a Polars frame from canonical row mappings."""

        pl = polars or require_dependency("polars")
        normalized = tuple(dict(row) for row in rows)
        if not normalized:
            raise PackMaterializerError("canonical frame rows must be non-empty")
        frame = pl.DataFrame(list(normalized))
        _require_columns(frame, ("series_id", "event_ts", "available_ts"))
        return frame.sort("available_ts")

    def materialize_pack(
        self,
        pack: FastFeaturePack,
        accepted_version: AcceptedDatasetVersion,
        *,
        partition_id: str,
        canonical_frame: Any | None = None,
        load_request: SymbolYearFrameRequest | None = None,
        alpha_data_root: str | Path | None = None,
        governance_metadata: Mapping[str, Any] | None = None,
        partition_plan: Any | None = None,
        output_namespace: str = "features/fast_materialized",
        value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
    ) -> FeatureMaterializationResult:
        """Compute and persist a pack as Parquet plus optional JSONL audit output."""

        pack = _require_pack(pack)
        if not isinstance(accepted_version, AcceptedDatasetVersion):
            raise PackMaterializerError("accepted_version must be an AcceptedDatasetVersion")
        frame = canonical_frame
        if frame is None:
            if load_request is None:
                raise PackMaterializerError("canonical_frame or load_request is required")
            if load_request.dataset_version_id != accepted_version.dataset_version_id:
                raise PackMaterializerError("load request DatasetVersion must match accepted input")
            frame = self.load_symbol_year_ohlcv_frame(load_request)
        plan = build_feature_materialization_plan(
            pack.feature_set,
            accepted_version,
            partition_id=partition_id,
            alpha_data_root=alpha_data_root,
            governance_metadata=governance_metadata,
            partition_plan=partition_plan,
            output_namespace=output_namespace,
        )
        return self.materialize_values(plan, frame, pack, value_store_format=value_store_format)

    def materialize_values(
        self,
        plan: FeatureMaterializationPlan,
        canonical_frame: Any,
        pack: FastFeaturePack,
        *,
        value_store_format: ValueStoreFormat = ValueStoreFormat.DUAL,
    ) -> FeatureMaterializationResult:
        """Compute values for an existing plan and write the official value store."""

        if not isinstance(plan, FeatureMaterializationPlan):
            raise PackMaterializerError("plan must be a FeatureMaterializationPlan")
        pack = _require_pack(pack)
        if plan.feature_set != pack.feature_set:
            raise PackMaterializerError("plan FeatureSetSpec must match fast pack")
        records = self.compute_values(canonical_frame, pack)
        _validate_records(plan, records)
        write_result = _write_records(plan, records, value_store_format=value_store_format)
        return FeatureMaterializationResult(
            plan=plan,
            records=records,
            dry_run=False,
            wrote_output=write_result.wrote_output,
            output_path=write_result.output_path,
            value_store_handle=write_result.handle,
        )

    def compute_values(
        self,
        canonical_frame: Any,
        pack: FastFeaturePack,
    ) -> tuple[FeatureValueRecord, ...]:
        """Evaluate all pack expressions and return aligned FeatureValueRecords."""

        polars = require_dependency("polars")
        pack = _require_pack(pack)
        frame = _coerce_frame(canonical_frame, polars)
        _require_columns(frame, ("series_id", "event_ts", "available_ts"))
        if pack.prepare_frame is not None:
            frame = pack.prepare_frame(frame)
            if isinstance(frame, polars.LazyFrame):
                frame = frame.collect()
            if not isinstance(frame, polars.DataFrame):
                raise PackMaterializerError(
                    "FastFeaturePack.prepare_frame must return a Polars DataFrame"
                )
            _require_columns(frame, ("series_id", "event_ts", "available_ts"))

        value_columns: list[tuple[FastFeatureDeclaration, str, str, str, str, str]] = []
        expressions: list[Any] = []
        for index, declaration in enumerate(pack.declarations):
            prefix = f"__fast_{index}"
            entity_col = f"{prefix}_entity_id"
            event_col = f"{prefix}_event_ts"
            available_col = f"{prefix}_available_ts"
            value_col = f"{prefix}_value"
            flags_col = f"{prefix}_quality_flags"
            expressions.extend(
                (
                    _expr_or_default(
                        declaration.entity_id_expr,
                        polars.col("series_id"),
                        polars=polars,
                    ).alias(entity_col),
                    _expr_or_default(
                        declaration.event_ts_expr,
                        polars.col("event_ts"),
                        polars=polars,
                    ).alias(event_col),
                    _expr_or_default(
                        declaration.available_ts_expr,
                        polars.col("available_ts"),
                        polars=polars,
                    ).alias(available_col),
                    _require_expr(declaration.value_expr, polars=polars).alias(value_col),
                    _expr_or_default(
                        declaration.quality_flags_expr,
                        _empty_flags_expr(polars),
                        polars=polars,
                    ).alias(flags_col),
                )
            )
            value_columns.append(
                (declaration, entity_col, event_col, available_col, value_col, flags_col)
            )

        computed = frame.with_columns(expressions)
        records: list[FeatureValueRecord] = []
        for (
            declaration,
            entity_col,
            event_col,
            available_col,
            value_col,
            flags_col,
        ) in value_columns:
            selected = computed.select(
                (
                    entity_col,
                    event_col,
                    available_col,
                    value_col,
                    flags_col,
                )
            )
            for row in selected.iter_rows(named=True):
                records.append(
                    FeatureValueRecord(
                        feature_version_id=declaration.feature_version_id,
                        entity_id=_coerce_text(row[entity_col], "entity_id"),
                        event_ts=_coerce_datetime(row[event_col], "event_ts"),
                        available_ts=_coerce_datetime(row[available_col], "available_ts"),
                        value=_coerce_value(row[value_col]),
                        quality_flags=_coerce_quality_flags(row[flags_col]),
                    )
                )
        return tuple(records)

    def register_pack(
        self,
        materialization_result: FeatureMaterializationResult,
        pack: FastFeaturePack,
        *,
        feature_requests: Mapping[str, FeatureRequest | Mapping[str, Any]],
        store: FeatureStore | None = None,
        registry_metadata: Mapping[str, Any] | None = None,
    ) -> tuple[Any, ...]:
        """Register every feature through ``FeatureStore`` using serial writes."""

        pack = _require_pack(pack)
        if not isinstance(materialization_result, FeatureMaterializationResult):
            raise PackMaterializerError("registration requires a FeatureMaterializationResult")
        feature_store = store or FeatureStore.from_alpha_data_root(
            materialization_result.plan.alpha_data_root
        )
        metadata = _registry_metadata(registry_metadata)
        records: list[Any] = []
        with _REGISTRY_WRITE_LOCK:
            for declaration in pack.declarations:
                request = feature_requests.get(declaration.feature_spec.feature_id)
                if request is None:
                    raise PackMaterializerError(
                        "feature_requests missing "
                        f"{declaration.feature_spec.feature_id}"
                    )
                version = declaration.feature_version
                lineage = FeatureLineageRecord(
                    feature_version=version,
                    feature_spec=declaration.feature_spec,
                    feature_request_id=declaration.feature_spec.feature_request_id,
                    contract_provenance={
                        "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                        "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
                    },
                )
                records.append(
                    feature_store.register_materialized_feature(
                        materialization_result,
                        feature_spec=declaration.feature_spec,
                        feature_version=version,
                        feature_request=request,
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


def _write_records(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
    *,
    value_store_format: ValueStoreFormat,
) -> _WriteResult:
    store_format = _coerce_value_store_format(value_store_format)
    record_dicts = [record.to_dict() for record in records]
    content_hash = compute_value_content_hash(record_dicts)
    jsonl_path: Path | None = None
    parquet_path: Path | None = None
    wrote_output = False

    if store_format in (ValueStoreFormat.JSONL, ValueStoreFormat.DUAL):
        jsonl_path = plan.output_path
        wrote_output = _write_jsonl_if_changed(jsonl_path, _render_jsonl(plan, records))

    if store_format in (ValueStoreFormat.PARQUET, ValueStoreFormat.DUAL):
        parquet_path = plan.output_path.with_name("values.parquet")
        _require_under_root(parquet_path, plan.alpha_data_root)
        if not parquet_is_current(parquet_path, content_hash):
            write_parquet_values(
                record_dicts,
                parquet_path,
                plan_dict=plan.to_dict(),
                content_hash=content_hash,
                schema_version=FAST_VALUE_SCHEMA_VERSION,
                value_count=len(record_dicts),
            )
            wrote_output = True

    output_path = parquet_path if store_format is ValueStoreFormat.PARQUET else plan.output_path
    event_ts_values = tuple(record.event_ts.isoformat() for record in records)
    available_ts_values = tuple(record.available_ts.isoformat() for record in records)
    return _WriteResult(
        wrote_output=wrote_output,
        output_path=output_path,
        handle=ValueStoreHandle(
            format=store_format,
            jsonl_path=jsonl_path.as_posix() if jsonl_path is not None else None,
            parquet_path=parquet_path.as_posix() if parquet_path is not None else None,
            value_count=len(records),
            content_hash=content_hash,
            schema_version=FAST_VALUE_SCHEMA_VERSION,
            dataset_version_id=plan.dataset_version_id,
            set_id=plan.feature_set.feature_set_id,
            partition_id=plan.partition_id,
            min_event_ts=min(event_ts_values),
            max_event_ts=max(event_ts_values),
            min_available_ts=min(available_ts_values),
            max_available_ts=max(available_ts_values),
        ),
    )


def _render_jsonl(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
) -> str:
    lines = [
        canonical_serialize(
            {
                "record_type": "fast_feature_materialization_plan",
                "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
                "plan": plan.to_dict(),
            }
        )
    ]
    for record in records:
        lines.append(
            canonical_serialize(
                {
                    "record_type": "fast_feature_value",
                    "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                    "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
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


def _validate_records(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
) -> None:
    if not records:
        raise PackMaterializerError("fast materialization produced no value records")
    allowed_versions = set(plan.feature_version_ids)
    for record in records:
        if record.feature_version_id not in allowed_versions:
            raise PackMaterializerError("fast record outside FeatureMaterializationPlan")
        if record.available_ts < record.event_ts:
            raise PackMaterializerError("FeatureValueRecord.available_ts precedes event_ts")


def _registry_metadata(metadata: Mapping[str, Any] | None) -> dict[str, JsonValue]:
    merged: dict[str, Any] = {
        "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
        "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
    }
    if metadata:
        merged.update(metadata)
    return FrozenJsonMapping.from_mapping(merged, field_name="registry_metadata").to_dict()


def _require_pack(pack: FastFeaturePack) -> FastFeaturePack:
    if not isinstance(pack, FastFeaturePack):
        raise PackMaterializerError("fast materialization requires a FastFeaturePack")
    return pack


def _coerce_frame(frame: Any, polars: Any) -> Any:
    if isinstance(frame, polars.LazyFrame):
        frame = frame.collect()
    if not isinstance(frame, polars.DataFrame):
        raise PackMaterializerError("canonical_frame must be a Polars DataFrame or LazyFrame")
    frame = _with_optional_semantic_columns(frame, polars)
    return frame.sort("available_ts")


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


def _with_optional_semantic_columns(frame: Any, polars: Any) -> Any:
    """Supply defaults for dense-grid semantic columns when canonical rows omit them."""

    defaults = {
        "has_trade": polars.lit(None, dtype=polars.Boolean),
        "synthetic": polars.lit(False, dtype=polars.Boolean),
        "fill_method": polars.lit(None, dtype=polars.Utf8),
        "provider_bar_ref": polars.lit(None, dtype=polars.Utf8),
    }
    expressions = [
        expression.alias(column)
        for column, expression in defaults.items()
        if column not in frame.columns
    ]
    if not expressions:
        return frame
    return frame.with_columns(expressions)


def _expr_or_default(expr: Any | None, default: Any, *, polars: Any) -> Any:
    return default if expr is None else _require_expr(expr, polars=polars)


def _require_expr(expr: Any, *, polars: Any) -> Any:
    if not isinstance(expr, polars.Expr):
        raise PackMaterializerError("fast feature declarations must use Polars expressions")
    return expr


def _empty_flags_expr(polars: Any) -> Any:
    return polars.lit([], dtype=polars.List(polars.Utf8))


def _coerce_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackMaterializerError(f"{field_name} must be a non-empty string")
    return value.strip()


def _coerce_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise PackMaterializerError(f"{field_name} must be a timezone-aware datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PackMaterializerError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _coerce_value(value: object) -> object:
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _coerce_quality_flags(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if not isinstance(value, Sequence):
        raise PackMaterializerError("quality flags must be a sequence of strings")
    flags: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise PackMaterializerError("quality flags must contain non-empty strings")
        text = item.strip()
        if text not in flags:
            flags.append(text)
    return tuple(flags)


def _coerce_value_store_format(value: object) -> ValueStoreFormat:
    try:
        if isinstance(value, ValueStoreFormat):
            return value
        if isinstance(value, str):
            return ValueStoreFormat(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ValueStoreFormat)
        raise PackMaterializerError(f"value_store_format must be one of: {allowed}") from exc
    raise PackMaterializerError("value_store_format must be a ValueStoreFormat")


def _require_under_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise PackMaterializerError("materialized output path must stay under ALPHA_DATA_ROOT")


def _require_text(value: object) -> str:
    if not isinstance(value, str):
        raise PackMaterializerError("value must be a non-empty string")
    text = value.strip()
    if not text:
        raise PackMaterializerError("value must be a non-empty string")
    return text


__all__ = [
    "FAST_PRODUCER_ENGINE_ID",
    "FAST_VALUE_SCHEMA_VERSION",
    "FastFeatureDeclaration",
    "FastFeaturePack",
    "PackMaterializer",
    "PackMaterializerError",
    "SymbolYearFrameRequest",
]
