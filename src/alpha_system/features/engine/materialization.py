"""Plan and execute local-only feature materialization.

Materialization is deliberately an orchestration layer. Feature formulas remain
in the approved family modules, DatasetVersion acceptance remains in the FLF-P01
consumption adapter, and governance request admission remains in the FLF-P05
request gate carried by family definitions.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from alpha_system.data.foundation.datasets import DatasetPartitionPlan
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.features import consumption
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    FrozenJsonMapping,
    WindowCausality,
)
from alpha_system.features.families.bbo import BBOFeatureDefinition, compute_bbo_feature
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureDefinition,
    compute_cross_market_feature,
)
from alpha_system.features.families.ohlcv import OHLCVFeatureDefinition, compute_ohlcv_feature
from alpha_system.features.families.session import (
    SessionCalendarRollMetadata,
    SessionFeatureDefinition,
    compute_session_feature,
)
from alpha_system.features.families.structure import (
    StructureFeatureDefinition,
    StructureInputBundle,
    compute_structure_feature,
)
from alpha_system.features.input_views import (
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
    build_bbo_input_view,
    build_canonical_input_views,
)
from alpha_system.features.semantics import is_synthetic_no_trade_bar
from alpha_system.governance.serialization import JsonValue, canonical_serialize, content_hash

FEATURE_MATERIALIZATION_SCHEMA = "alpha_system.features.materialization.v1"
FEATURE_MATERIALIZATION_PURPOSE = "feature_materialization"

type SupportedFeatureDefinition = (
    OHLCVFeatureDefinition
    | BBOFeatureDefinition
    | SessionFeatureDefinition
    | CrossMarketFeatureDefinition
    | StructureFeatureDefinition
)


class FeatureMaterializationError(ValueError):
    """Raised when feature materialization fails closed."""


@dataclass(frozen=True, slots=True)
class FeatureMaterializationPlan:
    """Deterministic local-only plan for materializing one feature set partition."""

    feature_set: FeatureSetSpec
    dataset_version_id: str
    partition_id: str
    alpha_data_root: Path
    output_path: Path
    plan_id: str
    idempotency_key: str
    feature_version_ids: tuple[str, ...]
    governance_metadata: FrozenJsonMapping = field(default_factory=FrozenJsonMapping)

    def __post_init__(self) -> None:
        if not isinstance(self.feature_set, FeatureSetSpec):
            raise FeatureMaterializationError(
                "FeatureMaterializationPlan.feature_set must be a FeatureSetSpec"
            )
        dataset_version_id = _require_text(self.dataset_version_id, "dataset_version_id")
        partition_id = _require_text(self.partition_id, "partition_id")
        alpha_data_root = _require_path(self.alpha_data_root, "alpha_data_root")
        output_path = _require_path(self.output_path, "output_path")
        _require_under_root(output_path, alpha_data_root)
        feature_version_ids = _feature_version_ids(self.feature_set)
        supplied_ids = tuple(self.feature_version_ids)
        if supplied_ids != feature_version_ids:
            raise FeatureMaterializationError(
                "FeatureMaterializationPlan.feature_version_ids must match FeatureSetSpec"
            )
        governance_metadata = _freeze_json_mapping(
            self.governance_metadata,
            "FeatureMaterializationPlan.governance_metadata",
        )
        expected_idempotency_key = _plan_content_hash(
            self.feature_set,
            dataset_version_id=dataset_version_id,
            partition_id=partition_id,
            output_path=output_path,
            governance_metadata=governance_metadata,
        )
        expected_plan_id = f"fmat_{expected_idempotency_key}"
        if self.idempotency_key != expected_idempotency_key:
            raise FeatureMaterializationError(
                "FeatureMaterializationPlan.idempotency_key is not deterministic"
            )
        if self.plan_id != expected_plan_id:
            raise FeatureMaterializationError(
                "FeatureMaterializationPlan.plan_id must be fmat_<idempotency_key>"
            )
        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        object.__setattr__(self, "partition_id", partition_id)
        object.__setattr__(self, "alpha_data_root", alpha_data_root)
        object.__setattr__(self, "output_path", output_path)
        object.__setattr__(self, "feature_version_ids", feature_version_ids)
        object.__setattr__(self, "governance_metadata", governance_metadata)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible plan payload."""

        return {
            "schema": FEATURE_MATERIALIZATION_SCHEMA,
            "plan_id": self.plan_id,
            "idempotency_key": self.idempotency_key,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "alpha_data_root": str(self.alpha_data_root),
            "output_path": str(self.output_path),
            "feature_set": self.feature_set.to_dict(),
            "feature_version_ids": list(self.feature_version_ids),
            "governance_metadata": self.governance_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FeatureMaterializationInputs:
    """Canonical in-memory inputs for one accepted DatasetVersion partition."""

    accepted_version: AcceptedDatasetVersion
    bar_rows: Iterable[Mapping[str, object]] = ()
    bbo_rows: Iterable[Mapping[str, object]] = ()
    dense_grid_bar_rows: Iterable[Mapping[str, object]] = ()
    governance_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)
    partition_plan: DatasetPartitionPlan | None = None
    session_metadata: SessionCalendarRollMetadata | Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.accepted_version, AcceptedDatasetVersion):
            raise FeatureMaterializationError(
                "FeatureMaterializationInputs.accepted_version must be an AcceptedDatasetVersion"
            )
        object.__setattr__(
            self,
            "bar_rows",
            _mapping_rows(self.bar_rows, "bar_rows"),
        )
        object.__setattr__(
            self,
            "bbo_rows",
            _mapping_rows(self.bbo_rows, "bbo_rows"),
        )
        object.__setattr__(
            self,
            "dense_grid_bar_rows",
            _mapping_rows(self.dense_grid_bar_rows, "dense_grid_bar_rows"),
        )
        object.__setattr__(
            self,
            "governance_metadata",
            _freeze_json_mapping(
                self.governance_metadata,
                "FeatureMaterializationInputs.governance_metadata",
            ),
        )


@dataclass(frozen=True, slots=True)
class FeatureMaterializationResult:
    """Result returned by dry-run or executed feature materialization."""

    plan: FeatureMaterializationPlan
    records: tuple[FeatureValueRecord, ...]
    dry_run: bool
    wrote_output: bool
    output_path: Path | None = None

    @property
    def record_count(self) -> int:
        """Return the number of feature values produced."""

        return len(self.records)


def resolve_feature_materialization_dataset(
    registry_path: str | Path,
    dataset_version_id: object,
    *,
    lifecycle_state: object,
    quality_report: object,
    coverage_report: object,
    source_manifest: object,
    code_hash: object,
    config_hash: object,
) -> AcceptedDatasetVersion:
    """Resolve an accepted DatasetVersion through the sanctioned adapter."""

    return consumption.resolve_accepted_dataset_version(
        registry_path,
        dataset_version_id,
        lifecycle_state=lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )


def build_feature_materialization_plan(
    feature_set: FeatureSetSpec,
    accepted_version: AcceptedDatasetVersion,
    *,
    partition_id: object,
    alpha_data_root: str | Path | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
    output_namespace: str = "features/materialized",
) -> FeatureMaterializationPlan:
    """Build and validate a deterministic plan without writing values."""

    if not isinstance(accepted_version, AcceptedDatasetVersion):
        raise FeatureMaterializationError("accepted_version must be an AcceptedDatasetVersion")
    feature_set = _require_feature_set(feature_set)
    partition = _require_text(partition_id, "partition_id")
    metadata = _freeze_json_mapping(governance_metadata or {}, "governance_metadata")
    accepted_version.require_partition_access(
        partition_id=partition,
        purpose=FEATURE_MATERIALIZATION_PURPOSE,
        governance_metadata=metadata.to_dict(),
        partition_plan=partition_plan,
    )
    alpha_root = _alpha_data_root(alpha_data_root)
    output_path = _feature_output_path(
        alpha_root,
        output_namespace=output_namespace,
        feature_set=feature_set,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
    )
    idempotency_key = _plan_content_hash(
        feature_set,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
        output_path=output_path,
        governance_metadata=metadata,
    )
    return FeatureMaterializationPlan(
        feature_set=feature_set,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
        alpha_data_root=alpha_root,
        output_path=output_path,
        plan_id=f"fmat_{idempotency_key}",
        idempotency_key=idempotency_key,
        feature_version_ids=_feature_version_ids(feature_set),
        governance_metadata=metadata,
    )


def materialize_features(
    plan: FeatureMaterializationPlan,
    inputs: FeatureMaterializationInputs,
    feature_definitions: Iterable[SupportedFeatureDefinition],
    *,
    dry_run: bool = False,
) -> FeatureMaterializationResult:
    """Execute a feature materialization plan, or validate it in dry-run mode."""

    plan = _require_plan(plan)
    inputs = _require_inputs(inputs)
    definitions_by_feature_id = _definitions_by_feature_id(feature_definitions, plan.feature_set)
    if inputs.accepted_version.dataset_version_id != plan.dataset_version_id:
        raise FeatureMaterializationError(
            "materialization inputs must match the plan DatasetVersion id"
        )
    inputs.accepted_version.require_partition_access(
        partition_id=plan.partition_id,
        purpose=FEATURE_MATERIALIZATION_PURPOSE,
        governance_metadata=_merged_governance_metadata(plan, inputs),
        partition_plan=inputs.partition_plan,
    )

    if dry_run:
        return FeatureMaterializationResult(
            plan=plan,
            records=(),
            dry_run=True,
            wrote_output=False,
            output_path=None,
        )

    views = _build_input_views(plan, inputs)
    records = _compute_records(plan.feature_set, definitions_by_feature_id, views, inputs)
    _validate_materialized_records(plan, records)
    wrote_output = _write_records_idempotently(plan, records)
    return FeatureMaterializationResult(
        plan=plan,
        records=records,
        dry_run=False,
        wrote_output=wrote_output,
        output_path=plan.output_path,
    )


def _require_feature_set(feature_set: object) -> FeatureSetSpec:
    if not isinstance(feature_set, FeatureSetSpec):
        raise FeatureMaterializationError("materialization requires a FeatureSetSpec")
    for feature in feature_set.features:
        _validate_materializable_feature_spec(feature)
    return feature_set


def _validate_materializable_feature_spec(feature: object) -> FeatureSpec:
    if not isinstance(feature, FeatureSpec):
        raise FeatureMaterializationError("FeatureSetSpec contains a non-FeatureSpec entry")
    if not feature.implementation_eligible:
        raise FeatureMaterializationError(
            f"FeatureSpec {feature.feature_id} is not implementation eligible"
        )
    if not feature.live or not feature.window.is_live_compatible:
        raise FeatureMaterializationError(
            f"FeatureSpec {feature.feature_id} must use a causal live-compatible window"
        )
    if feature.window.causality is not WindowCausality.CAUSAL:
        raise FeatureMaterializationError(
            f"FeatureSpec {feature.feature_id} must use causal primitives only"
        )
    rule = feature.available_ts_derivation_rule.lower()
    if "available_ts" not in rule:
        raise FeatureMaterializationError(
            f"FeatureSpec {feature.feature_id} must derive values from available_ts"
        )
    return feature


def _require_plan(plan: object) -> FeatureMaterializationPlan:
    if not isinstance(plan, FeatureMaterializationPlan):
        raise FeatureMaterializationError("materialize_features requires a plan")
    _require_feature_set(plan.feature_set)
    return plan


def _require_inputs(inputs: object) -> FeatureMaterializationInputs:
    if not isinstance(inputs, FeatureMaterializationInputs):
        raise FeatureMaterializationError("materialize_features requires materialization inputs")
    return inputs


def _definitions_by_feature_id(
    definitions: Iterable[SupportedFeatureDefinition],
    feature_set: FeatureSetSpec,
) -> dict[str, SupportedFeatureDefinition]:
    expected = {feature.feature_id: feature for feature in feature_set.features}
    by_id: dict[str, SupportedFeatureDefinition] = {}
    for definition in definitions:
        supported = _require_supported_definition(definition)
        definition_spec = _definition_feature_spec(supported)
        _validate_materializable_feature_spec(definition_spec)
        if not _definition_gate_allows_implementation(supported):
            raise FeatureMaterializationError(
                f"FeatureRequest gate did not admit {definition_spec.feature_id}"
            )
        expected_spec = expected.get(definition_spec.feature_id)
        if expected_spec is None:
            raise FeatureMaterializationError(
                f"definition {definition_spec.feature_id} is not in the FeatureSetSpec"
            )
        if definition_spec != expected_spec:
            raise FeatureMaterializationError(
                f"definition {definition_spec.feature_id} does not match the FeatureSetSpec"
            )
        if (
            _definition_feature_version_id(supported)
            != expected_spec.derive_feature_version().feature_version_id
        ):
            raise FeatureMaterializationError(
                f"definition {definition_spec.feature_id} has a mismatched FeatureVersion"
            )
        if definition_spec.feature_id in by_id:
            raise FeatureMaterializationError(
                f"duplicate feature definition for {definition_spec.feature_id}"
            )
        by_id[definition_spec.feature_id] = supported
    missing = tuple(feature_id for feature_id in expected if feature_id not in by_id)
    if missing:
        raise FeatureMaterializationError(
            "missing approved feature definitions: " + ", ".join(missing)
        )
    return by_id


def _require_supported_definition(definition: object) -> SupportedFeatureDefinition:
    if isinstance(
        definition,
        (
            OHLCVFeatureDefinition,
            BBOFeatureDefinition,
            SessionFeatureDefinition,
            CrossMarketFeatureDefinition,
            StructureFeatureDefinition,
        ),
    ):
        return definition
    raise FeatureMaterializationError("unsupported feature definition type")


def _definition_feature_spec(definition: SupportedFeatureDefinition) -> FeatureSpec:
    spec = definition.spec
    if isinstance(spec, FeatureSpec):
        return spec
    feature_spec = getattr(spec, "feature_spec", None)
    if isinstance(feature_spec, FeatureSpec):
        return feature_spec
    raise FeatureMaterializationError("feature definition does not expose a FeatureSpec")


def _definition_feature_version_id(definition: SupportedFeatureDefinition) -> str:
    version_id = getattr(definition, "feature_version_id", None)
    if isinstance(version_id, str) and version_id:
        return version_id
    raise FeatureMaterializationError("feature definition does not expose a FeatureVersion id")


def _definition_gate_allows_implementation(definition: SupportedFeatureDefinition) -> bool:
    decision = getattr(definition, "request_gate_decision", None)
    return bool(getattr(decision, "implementation_allowed", False))


def _build_input_views(
    plan: FeatureMaterializationPlan,
    inputs: FeatureMaterializationInputs,
) -> CanonicalInputViews:
    metadata = _merged_governance_metadata(plan, inputs)
    if _requires_dense_grid(plan.feature_set):
        ohlcv = _dense_grid_ohlcv_input_view(
            inputs,
            partition_id=plan.partition_id,
            governance_metadata=metadata,
        )
        bbo = build_bbo_input_view(
            inputs.accepted_version,
            inputs.bbo_rows,
            partition_id=plan.partition_id,
            purpose=FEATURE_MATERIALIZATION_PURPOSE,
            governance_metadata=metadata,
            partition_plan=inputs.partition_plan,
        )
        return CanonicalInputViews(ohlcv=ohlcv, bbo=bbo)
    return build_canonical_input_views(
        inputs.accepted_version,
        bar_rows=inputs.bar_rows,
        bbo_rows=inputs.bbo_rows,
        partition_id=plan.partition_id,
        purpose=FEATURE_MATERIALIZATION_PURPOSE,
        governance_metadata=metadata,
        partition_plan=inputs.partition_plan,
    )


def _requires_dense_grid(feature_set: FeatureSetSpec) -> bool:
    return any("dense_grid_ohlcv" in feature.inputs.input_views for feature in feature_set.features)


def _dense_grid_ohlcv_input_view(
    inputs: FeatureMaterializationInputs,
    *,
    partition_id: str,
    governance_metadata: Mapping[str, object],
) -> OHLCVInputView:
    if not inputs.dense_grid_bar_rows:
        raise FeatureMaterializationError(
            "FeatureSetSpec requires dense_grid_ohlcv but no dense-grid rows were supplied"
        )
    dense_records = consumption.dense_grid_bars_from_mappings(
        inputs.accepted_version,
        inputs.dense_grid_bar_rows,
        partition_id=partition_id,
        purpose=FEATURE_MATERIALIZATION_PURPOSE,
        governance_metadata=governance_metadata,
        partition_plan=inputs.partition_plan,
    )
    return OHLCVInputView(tuple(_ohlcv_row_from_dense_record(record) for record in dense_records))


def _ohlcv_row_from_dense_record(record: DenseGridBarRecord) -> OHLCVInputRow:
    if record.synthetic and not is_synthetic_no_trade_bar(record):
        raise FeatureMaterializationError(
            "synthetic dense-grid rows must carry the canonical no-trade signature"
        )
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


def _compute_records(
    feature_set: FeatureSetSpec,
    definitions_by_feature_id: Mapping[str, SupportedFeatureDefinition],
    views: CanonicalInputViews,
    inputs: FeatureMaterializationInputs,
) -> tuple[FeatureValueRecord, ...]:
    records: list[FeatureValueRecord] = []
    for feature in feature_set.features:
        definition = definitions_by_feature_id[feature.feature_id]
        records.extend(_compute_feature_records(feature.family, definition, views, inputs))
    return tuple(records)


def _compute_feature_records(
    family: FeatureFamily,
    definition: SupportedFeatureDefinition,
    views: CanonicalInputViews,
    inputs: FeatureMaterializationInputs,
) -> tuple[FeatureValueRecord, ...]:
    if family is FeatureFamily.BASE_OHLCV and isinstance(definition, OHLCVFeatureDefinition):
        return compute_ohlcv_feature(definition, views.ohlcv)
    if family is FeatureFamily.BBO_TRADABILITY and isinstance(definition, BBOFeatureDefinition):
        return compute_bbo_feature(definition, views.bbo)
    if family is FeatureFamily.SESSION_CALENDAR_ROLL and isinstance(
        definition,
        SessionFeatureDefinition,
    ):
        return compute_session_feature(definition, views.ohlcv, inputs.session_metadata)
    if family is FeatureFamily.CROSS_MARKET and isinstance(
        definition, CrossMarketFeatureDefinition
    ):
        return compute_cross_market_feature(definition, views)
    if family is FeatureFamily.LIQUIDITY_STRUCTURE and isinstance(
        definition,
        StructureFeatureDefinition,
    ):
        return compute_structure_feature(
            definition,
            StructureInputBundle(ohlcv=views.ohlcv, bbo=views.bbo),
        )
    raise FeatureMaterializationError("feature definition family does not match FeatureSpec")


def _validate_materialized_records(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
) -> None:
    allowed_versions = set(plan.feature_version_ids)
    for record in records:
        if not isinstance(record, FeatureValueRecord):
            raise FeatureMaterializationError("materialization produced a non-FeatureValueRecord")
        if record.feature_version_id not in allowed_versions:
            raise FeatureMaterializationError(
                "materialization produced a FeatureValueRecord outside the plan"
            )
        _require_aware_datetime(record.event_ts, "FeatureValueRecord.event_ts")
        _require_aware_datetime(record.available_ts, "FeatureValueRecord.available_ts")
        if record.available_ts < record.event_ts:
            raise FeatureMaterializationError(
                "FeatureValueRecord.available_ts must not precede event_ts"
            )


def _write_records_idempotently(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
) -> bool:
    _require_under_root(plan.output_path, plan.alpha_data_root)
    payload = _render_jsonl(plan, records)
    existing = plan.output_path.read_text(encoding="utf-8") if plan.output_path.exists() else None
    if existing == payload:
        return False
    plan.output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=plan.output_path.parent,
        prefix=f".{plan.output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(payload)
    temp_path.replace(plan.output_path)
    return True


def _render_jsonl(
    plan: FeatureMaterializationPlan,
    records: tuple[FeatureValueRecord, ...],
) -> str:
    lines = [
        canonical_serialize(
            {
                "record_type": "feature_materialization_plan",
                "plan": plan.to_dict(),
            }
        )
    ]
    for record in records:
        lines.append(
            canonical_serialize(
                {
                    "record_type": "feature_value",
                    "plan_id": plan.plan_id,
                    "dataset_version_id": plan.dataset_version_id,
                    "partition_id": plan.partition_id,
                    "value": record.to_dict(),
                }
            )
        )
    return "\n".join(lines) + "\n"


def _alpha_data_root(alpha_data_root: str | Path | None) -> Path:
    root_value = (
        alpha_data_root if alpha_data_root is not None else os.environ.get("ALPHA_DATA_ROOT")
    )
    if root_value is None:
        raise FeatureMaterializationError("ALPHA_DATA_ROOT is required for materialization plans")
    root = _require_path(root_value, "ALPHA_DATA_ROOT")
    repo_root = Path.cwd().resolve(strict=False)
    if root == repo_root or root.is_relative_to(repo_root):
        raise FeatureMaterializationError("ALPHA_DATA_ROOT must be outside the repository tree")
    return root


def _feature_output_path(
    alpha_data_root: Path,
    *,
    output_namespace: str,
    feature_set: FeatureSetSpec,
    dataset_version_id: str,
    partition_id: str,
) -> Path:
    namespace_parts = tuple(_safe_path_token(part) for part in output_namespace.split("/"))
    output_path = alpha_data_root
    for part in namespace_parts:
        output_path /= part
    output_path = (
        output_path
        / _safe_path_token(feature_set.feature_set_id)
        / _safe_path_token(feature_set.feature_set_version)
        / _safe_path_token(dataset_version_id)
        / _safe_path_token(partition_id)
        / "values.jsonl"
    )
    _require_under_root(output_path, alpha_data_root)
    return output_path


def _plan_content_hash(
    feature_set: FeatureSetSpec,
    *,
    dataset_version_id: str,
    partition_id: str,
    output_path: Path,
    governance_metadata: FrozenJsonMapping,
) -> str:
    return content_hash(
        {
            "schema": FEATURE_MATERIALIZATION_SCHEMA,
            "feature_set": feature_set.to_dict(),
            "dataset_version_id": dataset_version_id,
            "partition_id": partition_id,
            "output_path": str(output_path),
            "governance_metadata": governance_metadata.to_dict(),
        }
    )


def _feature_version_ids(feature_set: FeatureSetSpec) -> tuple[str, ...]:
    return tuple(version.feature_version_id for version in feature_set.feature_versions)


def _merged_governance_metadata(
    plan: FeatureMaterializationPlan,
    inputs: FeatureMaterializationInputs,
) -> dict[str, JsonValue]:
    merged: dict[str, JsonValue] = {}
    merged.update(plan.governance_metadata.to_dict())
    merged.update(inputs.governance_metadata.to_dict())
    return merged


def _mapping_rows(
    rows: Iterable[Mapping[str, object]],
    field_name: str,
) -> tuple[Mapping[str, object], ...]:
    if isinstance(rows, str):
        raise FeatureMaterializationError(f"{field_name} must be an iterable of mappings")
    normalized = tuple(rows)
    for row in normalized:
        if isinstance(row, str) or not isinstance(row, Mapping):
            raise FeatureMaterializationError(f"{field_name} must contain mappings")
    return normalized


def _freeze_json_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    try:
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    except FeatureContractError as exc:
        raise FeatureMaterializationError(str(exc)) from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise FeatureMaterializationError(f"{field_name} must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FeatureMaterializationError(f"{field_name} must be a non-empty single-line string")
    return text


def _require_path(value: str | Path, field_name: str) -> Path:
    if not isinstance(value, str | Path):
        raise FeatureMaterializationError(f"{field_name} must be a path")
    try:
        return Path(value).expanduser().resolve(strict=False)
    except RuntimeError as exc:
        raise FeatureMaterializationError(f"{field_name} could not be resolved") from exc


def _require_under_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise FeatureMaterializationError(
            "materialized output path must stay under ALPHA_DATA_ROOT"
        )


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FeatureMaterializationError(f"{field_name} must be timezone-aware")
    if value.tzinfo is None or value.utcoffset() is None:
        raise FeatureMaterializationError(f"{field_name} must be timezone-aware")
    return value


def _safe_path_token(value: object) -> str:
    text = _require_text(value, "path token")
    normalized = text.replace(".", "_").replace("-", "_")
    if not normalized.replace("_", "").isalnum():
        raise FeatureMaterializationError(f"path token contains unsupported characters: {text}")
    return normalized


__all__ = [
    "FEATURE_MATERIALIZATION_PURPOSE",
    "FEATURE_MATERIALIZATION_SCHEMA",
    "FeatureMaterializationError",
    "FeatureMaterializationInputs",
    "FeatureMaterializationPlan",
    "FeatureMaterializationResult",
    "SupportedFeatureDefinition",
    "build_feature_materialization_plan",
    "materialize_features",
    "resolve_feature_materialization_dataset",
]
