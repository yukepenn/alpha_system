"""Plan and execute local-only label materialization.

The engine consumes approved label-family definitions, one accepted
DatasetVersion handle, and canonical in-memory row mappings. It does not read
provider files, call external providers, register labels, or expose labels as
live features.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any

from alpha_system.data.foundation.datasets import DatasetPartitionPlan
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.features import consumption
from alpha_system.features.consumption import (
    ACCEPTED_DATASET_VERSION_STATES,
    AcceptedDatasetVersion,
)
from alpha_system.features.input_views import (
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
    build_bbo_input_view,
    build_ohlcv_input_view,
)
from alpha_system.features.semantics import is_synthetic_no_trade_bar
from alpha_system.governance.label_leakage_guard import FeatureReferences
from alpha_system.governance.serialization import JsonValue, canonical_serialize, content_hash
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    compute_cost_adjusted_label,
)
from alpha_system.labels.families.event import EventLabelDefinition, compute_event_label
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    compute_fixed_horizon_label,
)
from alpha_system.labels.families.path import PathLabelDefinition, compute_path_label
from alpha_system.labels.version import (
    FrozenJsonMapping,
    LabelAvailabilityConsumer,
    LabelContractError,
    LabelContractSpec,
    LabelFamily,
    LabelValueRecord,
    LabelVersion,
)

LABEL_MATERIALIZATION_SCHEMA = "alpha_system.labels.materialization.v1"
LABEL_MATERIALIZATION_PURPOSE = "label_materialization"
LABEL_MATERIALIZATION_ALLOWED = "MATERIALIZATION_ALLOWED"

type SupportedLabelDefinition = (
    FixedHorizonLabelDefinition
    | CostAdjustedLabelDefinition
    | PathLabelDefinition
    | EventLabelDefinition
)


class LabelMaterializationError(ValueError):
    """Raised when label materialization fails closed."""


@dataclass(frozen=True, slots=True)
class LabelMaterializationPlan:
    """Deterministic local-only plan for one label-set DatasetVersion partition."""

    label_contracts: tuple[LabelContractSpec, ...]
    dataset_version_id: str
    partition_id: str
    instrument_ids: tuple[str, ...]
    alpha_data_root: Path
    output_path: Path
    plan_id: str
    idempotency_key: str
    label_version_ids: tuple[str, ...]
    label_spec_ids: tuple[str, ...]
    label_families: tuple[str, ...]
    dry_run: bool = False
    label_lifecycle_state: str = LABEL_MATERIALIZATION_ALLOWED
    legal_consumer: str = LabelAvailabilityConsumer.LABELS_ONLY.value
    governance_metadata: FrozenJsonMapping = field(default_factory=FrozenJsonMapping)

    def __post_init__(self) -> None:
        contracts = _label_contracts(self.label_contracts)
        dataset_version_id = _require_text(self.dataset_version_id, "dataset_version_id")
        partition_id = _require_text(self.partition_id, "partition_id")
        instrument_ids = _text_tuple(self.instrument_ids, "instrument_ids", allow_empty=True)
        alpha_data_root = _require_path(self.alpha_data_root, "alpha_data_root")
        output_path = _require_path(self.output_path, "output_path")
        _require_under_root(output_path, alpha_data_root)
        dry_run = _require_bool(self.dry_run, "dry_run")
        lifecycle_state = _require_lifecycle_state(self.label_lifecycle_state)
        legal_consumer = _require_label_consumer(self.legal_consumer)
        governance_metadata = _freeze_json_mapping(
            self.governance_metadata,
            "LabelMaterializationPlan.governance_metadata",
        )

        expected_label_version_ids = _label_version_ids(contracts)
        expected_label_spec_ids = tuple(contract.label_spec_id for contract in contracts)
        expected_families = tuple(contract.family.value for contract in contracts)
        if tuple(self.label_version_ids) != expected_label_version_ids:
            raise LabelMaterializationError(
                "LabelMaterializationPlan.label_version_ids must match label contracts"
            )
        if tuple(self.label_spec_ids) != expected_label_spec_ids:
            raise LabelMaterializationError(
                "LabelMaterializationPlan.label_spec_ids must match label contracts"
            )
        if tuple(self.label_families) != expected_families:
            raise LabelMaterializationError(
                "LabelMaterializationPlan.label_families must match label contracts"
            )

        expected_idempotency_key = _plan_content_hash(
            contracts,
            dataset_version_id=dataset_version_id,
            partition_id=partition_id,
            instrument_ids=instrument_ids,
            output_path=output_path,
            governance_metadata=governance_metadata,
            dry_run=dry_run,
            label_lifecycle_state=lifecycle_state,
            legal_consumer=legal_consumer,
        )
        expected_plan_id = f"lmat_{expected_idempotency_key}"
        if self.idempotency_key != expected_idempotency_key:
            raise LabelMaterializationError(
                "LabelMaterializationPlan.idempotency_key is not deterministic"
            )
        if self.plan_id != expected_plan_id:
            raise LabelMaterializationError(
                "LabelMaterializationPlan.plan_id must be lmat_<idempotency_key>"
            )

        object.__setattr__(self, "label_contracts", contracts)
        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        object.__setattr__(self, "partition_id", partition_id)
        object.__setattr__(self, "instrument_ids", instrument_ids)
        object.__setattr__(self, "alpha_data_root", alpha_data_root)
        object.__setattr__(self, "output_path", output_path)
        object.__setattr__(self, "dry_run", dry_run)
        object.__setattr__(self, "label_lifecycle_state", lifecycle_state)
        object.__setattr__(self, "legal_consumer", legal_consumer)
        object.__setattr__(self, "label_version_ids", expected_label_version_ids)
        object.__setattr__(self, "label_spec_ids", expected_label_spec_ids)
        object.__setattr__(self, "label_families", expected_families)
        object.__setattr__(self, "governance_metadata", governance_metadata)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible plan payload."""

        return {
            "schema": LABEL_MATERIALIZATION_SCHEMA,
            "plan_id": self.plan_id,
            "idempotency_key": self.idempotency_key,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "instrument_ids": list(self.instrument_ids),
            "alpha_data_root": str(self.alpha_data_root),
            "output_path": str(self.output_path),
            "label_contracts": [contract.to_contract_dict() for contract in self.label_contracts],
            "label_version_ids": list(self.label_version_ids),
            "label_spec_ids": list(self.label_spec_ids),
            "label_families": list(self.label_families),
            "dry_run": self.dry_run,
            "label_lifecycle_state": self.label_lifecycle_state,
            "legal_consumer": self.legal_consumer,
            "governance_metadata": self.governance_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class LabelMaterializationInputs:
    """Canonical in-memory inputs for one accepted DatasetVersion partition."""

    accepted_version: AcceptedDatasetVersion
    bar_rows: Iterable[Mapping[str, object]] = ()
    bbo_rows: Iterable[Mapping[str, object]] = ()
    dense_grid_bar_rows: Iterable[Mapping[str, object]] = ()
    governance_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)
    partition_plan: DatasetPartitionPlan | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.accepted_version, AcceptedDatasetVersion):
            raise LabelMaterializationError(
                "LabelMaterializationInputs.accepted_version must be an AcceptedDatasetVersion"
            )
        _require_accepted_lifecycle(self.accepted_version)
        object.__setattr__(self, "bar_rows", _mapping_rows(self.bar_rows, "bar_rows"))
        object.__setattr__(self, "bbo_rows", _mapping_rows(self.bbo_rows, "bbo_rows"))
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
                "LabelMaterializationInputs.governance_metadata",
            ),
        )

    @property
    def input_row_count(self) -> int:
        """Return the total supplied canonical row count."""

        return len(self.bar_rows) + len(self.bbo_rows) + len(self.dense_grid_bar_rows)


@dataclass(frozen=True, slots=True)
class LabelMaterializationResult:
    """Result returned by dry-run or executed label materialization."""

    plan: LabelMaterializationPlan
    records: tuple[LabelValueRecord, ...]
    dry_run: bool
    wrote_output: bool
    output_path: Path | None = None
    planned_input_rows: int = 0
    planned_label_count: int = 0
    runtime_seconds: float = 0.0

    @property
    def record_count(self) -> int:
        """Return the number of label values produced."""

        return len(self.records)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a compact JSON-compatible result summary."""

        return {
            "plan_id": self.plan.plan_id,
            "dataset_version_id": self.plan.dataset_version_id,
            "partition_id": self.plan.partition_id,
            "dry_run": self.dry_run,
            "wrote_output": self.wrote_output,
            "output_path": str(self.output_path) if self.output_path is not None else None,
            "record_count": self.record_count,
            "planned_input_rows": self.planned_input_rows,
            "planned_label_count": self.planned_label_count,
            "runtime_seconds": self.runtime_seconds,
        }


def resolve_label_materialization_dataset(
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


def build_label_materialization_plan(
    label_definitions: Iterable[SupportedLabelDefinition],
    accepted_version: AcceptedDatasetVersion,
    *,
    partition_id: object,
    instrument_ids: Sequence[str] = (),
    alpha_data_root: str | Path | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
    partition_plan: DatasetPartitionPlan | None = None,
    dry_run: bool = False,
    label_lifecycle_state: str = LABEL_MATERIALIZATION_ALLOWED,
    legal_consumer: str = LabelAvailabilityConsumer.LABELS_ONLY.value,
    feature_references: FeatureReferences = (),
    output_namespace: str = "labels/materialized",
) -> LabelMaterializationPlan:
    """Build and validate a deterministic label materialization plan."""

    if not isinstance(accepted_version, AcceptedDatasetVersion):
        raise LabelMaterializationError("accepted_version must be an AcceptedDatasetVersion")
    _require_accepted_lifecycle(accepted_version)
    lifecycle_state = _require_lifecycle_state(label_lifecycle_state)
    consumer = _require_label_consumer(legal_consumer)
    partition = _require_text(partition_id, "partition_id")
    instruments = _text_tuple(instrument_ids, "instrument_ids", allow_empty=True)
    metadata = _freeze_json_mapping(governance_metadata or {}, "governance_metadata")
    definitions = _ordered_definitions(label_definitions)
    contracts = tuple(_definition_contract(definition) for definition in definitions)
    _validate_contracts_for_plan(
        contracts,
        accepted_version=accepted_version,
        feature_references=feature_references,
    )

    accepted_version.require_partition_access(
        partition_id=partition,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=metadata.to_dict(),
        partition_plan=partition_plan,
    )
    alpha_root = _alpha_data_root(alpha_data_root)
    output_path = _label_output_path(
        alpha_root,
        output_namespace=output_namespace,
        label_contracts=contracts,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
    )
    idempotency_key = _plan_content_hash(
        contracts,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
        instrument_ids=instruments,
        output_path=output_path,
        governance_metadata=metadata,
        dry_run=dry_run,
        label_lifecycle_state=lifecycle_state,
        legal_consumer=consumer,
    )
    return LabelMaterializationPlan(
        label_contracts=contracts,
        dataset_version_id=accepted_version.dataset_version_id,
        partition_id=partition,
        instrument_ids=instruments,
        alpha_data_root=alpha_root,
        output_path=output_path,
        plan_id=f"lmat_{idempotency_key}",
        idempotency_key=idempotency_key,
        label_version_ids=_label_version_ids(contracts),
        label_spec_ids=tuple(contract.label_spec_id for contract in contracts),
        label_families=tuple(contract.family.value for contract in contracts),
        dry_run=dry_run,
        label_lifecycle_state=lifecycle_state,
        legal_consumer=consumer,
        governance_metadata=metadata,
    )


def materialize_labels(
    plan: LabelMaterializationPlan,
    inputs: LabelMaterializationInputs,
    label_definitions: Iterable[SupportedLabelDefinition],
) -> LabelMaterializationResult:
    """Execute a label materialization plan, or validate it in dry-run mode."""

    started = perf_counter()
    plan = _require_plan(plan)
    inputs = _require_inputs(inputs)
    if inputs.accepted_version.dataset_version_id != plan.dataset_version_id:
        raise LabelMaterializationError(
            "materialization inputs must match the plan DatasetVersion id"
        )
    _require_accepted_lifecycle(inputs.accepted_version)
    definitions_by_version = _definitions_by_version_id(label_definitions, plan)
    inputs.accepted_version.require_partition_access(
        partition_id=plan.partition_id,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=_merged_governance_metadata(plan, inputs),
        partition_plan=inputs.partition_plan,
    )

    if plan.dry_run:
        return LabelMaterializationResult(
            plan=plan,
            records=(),
            dry_run=True,
            wrote_output=False,
            output_path=None,
            planned_input_rows=inputs.input_row_count,
            planned_label_count=len(plan.label_contracts),
            runtime_seconds=perf_counter() - started,
        )

    views = _build_input_views(plan, inputs)
    records = _compute_records(plan, definitions_by_version, views)
    _validate_materialized_records(plan, records)
    wrote_output = _write_records_idempotently(plan, records)
    return LabelMaterializationResult(
        plan=plan,
        records=records,
        dry_run=False,
        wrote_output=wrote_output,
        output_path=plan.output_path,
        planned_input_rows=inputs.input_row_count,
        planned_label_count=len(plan.label_contracts),
        runtime_seconds=perf_counter() - started,
    )


def _ordered_definitions(
    definitions: Iterable[SupportedLabelDefinition],
) -> tuple[SupportedLabelDefinition, ...]:
    if isinstance(definitions, str):
        raise LabelMaterializationError(
            "label materialization requires approved governed label definitions"
        )
    normalized = tuple(_require_supported_definition(definition) for definition in definitions)
    if not normalized:
        raise LabelMaterializationError("at least one label definition is required")
    by_version: dict[str, SupportedLabelDefinition] = {}
    for definition in normalized:
        version_id = _definition_version(definition).label_version_id
        if version_id in by_version:
            raise LabelMaterializationError(f"duplicate label definition: {version_id}")
        by_version[version_id] = definition
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                _definition_contract(item).family.value,
                _definition_contract(item).label_id,
                _definition_version(item).label_version_id,
            ),
        )
    )


def _definitions_by_version_id(
    definitions: Iterable[SupportedLabelDefinition],
    plan: LabelMaterializationPlan,
) -> dict[str, SupportedLabelDefinition]:
    ordered = _ordered_definitions(definitions)
    expected_contracts = {
        contract.derive_label_version().label_version_id: contract
        for contract in plan.label_contracts
    }
    by_version: dict[str, SupportedLabelDefinition] = {}
    for definition in ordered:
        contract = _definition_contract(definition)
        version = _definition_version(definition)
        expected_contract = expected_contracts.get(version.label_version_id)
        if expected_contract is None:
            raise LabelMaterializationError(
                f"definition {version.label_version_id} is not in the materialization plan"
            )
        if contract != expected_contract:
            raise LabelMaterializationError(
                f"definition {version.label_version_id} does not match the plan contract"
            )
        _validate_definition_matches_contract(definition, contract, version)
        by_version[version.label_version_id] = definition
    missing = tuple(
        label_version_id
        for label_version_id in plan.label_version_ids
        if label_version_id not in by_version
    )
    if missing:
        raise LabelMaterializationError("missing approved label definitions: " + ", ".join(missing))
    return by_version


def _require_supported_definition(definition: object) -> SupportedLabelDefinition:
    if isinstance(
        definition,
        (
            FixedHorizonLabelDefinition,
            CostAdjustedLabelDefinition,
            PathLabelDefinition,
            EventLabelDefinition,
        ),
    ):
        return definition
    raise LabelMaterializationError(
        "label materialization requires approved governed label definitions"
    )


def _definition_contract(definition: SupportedLabelDefinition) -> LabelContractSpec:
    if isinstance(definition, CostAdjustedLabelDefinition):
        contract = definition.spec.label_contract
    else:
        contract = definition.contract
    if not isinstance(contract, LabelContractSpec):
        raise LabelMaterializationError("label definition does not expose a LabelContractSpec")
    return contract


def _definition_version(definition: SupportedLabelDefinition) -> LabelVersion:
    version = definition.version
    if not isinstance(version, LabelVersion):
        raise LabelMaterializationError("label definition does not expose a LabelVersion")
    return version


def _validate_contracts_for_plan(
    contracts: tuple[LabelContractSpec, ...],
    *,
    accepted_version: AcceptedDatasetVersion,
    feature_references: FeatureReferences,
) -> None:
    for contract in contracts:
        _validate_materializable_contract(contract, accepted_version=accepted_version)
        try:
            contract.validate_live_feature_references(feature_references)
        except LabelContractError as exc:
            raise LabelMaterializationError(
                "labels cannot be exposed as live feature inputs"
            ) from exc


def _validate_materializable_contract(
    contract: object,
    *,
    accepted_version: AcceptedDatasetVersion,
) -> LabelContractSpec:
    if not isinstance(contract, LabelContractSpec):
        raise LabelMaterializationError("materialization requires validated LabelContractSpec")
    if not contract.availability_policy.future_data_legal_only_for_labels:
        raise LabelMaterializationError("future-looking data is legal only for labels")
    if contract.availability_policy.legal_consumer is not LabelAvailabilityConsumer.LABELS_ONLY:
        raise LabelMaterializationError("label contract legal_consumer must be labels_only")
    if "label_available_ts" not in (
        contract.availability_policy.label_available_ts_derivation_rule.lower()
    ):
        raise LabelMaterializationError("label_available_ts derivation rule is required")
    dataset_ids = tuple(contract.inputs.dataset_version_ids)
    if dataset_ids and accepted_version.dataset_version_id not in dataset_ids:
        raise LabelMaterializationError(
            "label contract DatasetVersion ids do not include the accepted DatasetVersion"
        )
    return contract


def _validate_definition_matches_contract(
    definition: SupportedLabelDefinition,
    contract: LabelContractSpec,
    version: LabelVersion,
) -> None:
    if version != contract.derive_label_version():
        raise LabelMaterializationError("LabelVersion does not match LabelContractSpec")
    if isinstance(definition, FixedHorizonLabelDefinition):
        expected_family = LabelFamily.FIXED_HORIZON
    elif isinstance(definition, CostAdjustedLabelDefinition):
        expected_family = LabelFamily.COST_ADJUSTED
    elif isinstance(definition, PathLabelDefinition):
        expected_family = LabelFamily.PATH
    elif isinstance(definition, EventLabelDefinition):
        expected_family = LabelFamily.EVENT
    else:
        raise LabelMaterializationError("unsupported label definition")
    if contract.family is not expected_family:
        raise LabelMaterializationError("label definition family does not match contract")


def _require_plan(plan: object) -> LabelMaterializationPlan:
    if not isinstance(plan, LabelMaterializationPlan):
        raise LabelMaterializationError("materialize_labels requires a LabelMaterializationPlan")
    _label_contracts(plan.label_contracts)
    _require_lifecycle_state(plan.label_lifecycle_state)
    _require_label_consumer(plan.legal_consumer)
    return plan


def _require_inputs(inputs: object) -> LabelMaterializationInputs:
    if not isinstance(inputs, LabelMaterializationInputs):
        raise LabelMaterializationError("materialize_labels requires LabelMaterializationInputs")
    return inputs


@dataclass(frozen=True, slots=True)
class _LabelInputViews:
    ohlcv: OHLCVInputView
    bbo: BBOInputView

    @property
    def canonical(self) -> CanonicalInputViews:
        """Return aligned canonical views for families that require both surfaces."""

        return CanonicalInputViews(self.ohlcv, self.bbo)


def _build_input_views(
    plan: LabelMaterializationPlan,
    inputs: LabelMaterializationInputs,
) -> _LabelInputViews:
    metadata = _merged_governance_metadata(plan, inputs)
    bar_rows = _filter_rows_for_instruments(inputs.bar_rows, plan.instrument_ids)
    bbo_rows = _filter_rows_for_instruments(inputs.bbo_rows, plan.instrument_ids)
    dense_rows = _filter_rows_for_instruments(inputs.dense_grid_bar_rows, plan.instrument_ids)

    if dense_rows and _requires_dense_grid(plan.label_contracts):
        ohlcv = _dense_grid_ohlcv_input_view(
            inputs,
            dense_rows=dense_rows,
            partition_id=plan.partition_id,
            governance_metadata=metadata,
        )
    else:
        ohlcv = build_ohlcv_input_view(
            inputs.accepted_version,
            bar_rows,
            partition_id=plan.partition_id,
            purpose=LABEL_MATERIALIZATION_PURPOSE,
            governance_metadata=metadata,
            partition_plan=inputs.partition_plan,
        )
    bbo = build_bbo_input_view(
        inputs.accepted_version,
        bbo_rows,
        partition_id=plan.partition_id,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=metadata,
        partition_plan=inputs.partition_plan,
    )
    return _LabelInputViews(ohlcv=ohlcv, bbo=bbo)


def _requires_dense_grid(contracts: tuple[LabelContractSpec, ...]) -> bool:
    return any("dense_grid_ohlcv" in contract.inputs.input_views for contract in contracts)


def _dense_grid_ohlcv_input_view(
    inputs: LabelMaterializationInputs,
    *,
    dense_rows: Iterable[Mapping[str, object]],
    partition_id: str,
    governance_metadata: Mapping[str, object],
) -> OHLCVInputView:
    dense_records = consumption.dense_grid_bars_from_mappings(
        inputs.accepted_version,
        dense_rows,
        partition_id=partition_id,
        purpose=LABEL_MATERIALIZATION_PURPOSE,
        governance_metadata=governance_metadata,
        partition_plan=inputs.partition_plan,
    )
    return OHLCVInputView(tuple(_ohlcv_row_from_dense_record(record) for record in dense_records))


def _ohlcv_row_from_dense_record(record: DenseGridBarRecord) -> OHLCVInputRow:
    if record.synthetic and not is_synthetic_no_trade_bar(record):
        raise LabelMaterializationError(
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
    plan: LabelMaterializationPlan,
    definitions_by_version: Mapping[str, SupportedLabelDefinition],
    views: _LabelInputViews,
) -> tuple[LabelValueRecord, ...]:
    records: list[LabelValueRecord] = []
    for contract in plan.label_contracts:
        version_id = contract.derive_label_version().label_version_id
        definition = definitions_by_version[version_id]
        records.extend(_compute_definition_records(definition, views))
    return tuple(records)


def _compute_definition_records(
    definition: SupportedLabelDefinition,
    views: _LabelInputViews,
) -> tuple[LabelValueRecord, ...]:
    if isinstance(definition, FixedHorizonLabelDefinition):
        return compute_fixed_horizon_label(definition, views.canonical)
    if isinstance(definition, CostAdjustedLabelDefinition):
        return compute_cost_adjusted_label(
            definition,
            views.canonical,
            trade_rows=views.ohlcv.rows,
        )
    if isinstance(definition, PathLabelDefinition):
        return compute_path_label(definition, views.ohlcv)
    if isinstance(definition, EventLabelDefinition):
        return compute_event_label(definition, views.canonical)
    raise LabelMaterializationError("unsupported label definition")


def _validate_materialized_records(
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
) -> None:
    contracts_by_version = {
        contract.derive_label_version().label_version_id: contract
        for contract in plan.label_contracts
    }
    for record in records:
        if not isinstance(record, LabelValueRecord):
            raise LabelMaterializationError("materialization produced a non-LabelValueRecord")
        contract = contracts_by_version.get(record.label_version_id)
        if contract is None:
            raise LabelMaterializationError(
                "materialization produced a LabelValueRecord outside the plan"
            )
        event_ts = _require_aware_datetime(record.event_ts, "LabelValueRecord.event_ts")
        horizon_end_ts = _require_aware_datetime(
            record.horizon_end_ts,
            "LabelValueRecord.horizon_end_ts",
        )
        label_available_ts = _require_aware_datetime(
            record.label_available_ts,
            "LabelValueRecord.label_available_ts",
        )
        if horizon_end_ts < event_ts:
            raise LabelMaterializationError(
                "LabelValueRecord.horizon_end_ts must not precede event_ts"
            )
        if label_available_ts < horizon_end_ts:
            raise LabelMaterializationError(
                "LabelValueRecord.label_available_ts must be at or after horizon_end_ts"
            )
        if label_available_ts < contract.availability_policy.availability_time:
            raise LabelMaterializationError(
                "LabelValueRecord.label_available_ts must not precede LabelSpec.availability_time"
            )


def _write_records_idempotently(
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
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
    plan: LabelMaterializationPlan,
    records: tuple[LabelValueRecord, ...],
) -> str:
    lines = [
        canonical_serialize(
            {
                "record_type": "label_materialization_plan",
                "plan": plan.to_dict(),
            }
        )
    ]
    for record in records:
        lines.append(
            canonical_serialize(
                {
                    "record_type": "label_value",
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
        raise LabelMaterializationError("ALPHA_DATA_ROOT is required for materialization plans")
    root = _require_path(root_value, "ALPHA_DATA_ROOT")
    repo_root = Path.cwd().resolve(strict=False)
    if root == repo_root or root.is_relative_to(repo_root):
        raise LabelMaterializationError("ALPHA_DATA_ROOT must be outside the repository tree")
    return root


def _label_output_path(
    alpha_data_root: Path,
    *,
    output_namespace: str,
    label_contracts: tuple[LabelContractSpec, ...],
    dataset_version_id: str,
    partition_id: str,
) -> Path:
    namespace_parts = tuple(_safe_path_token(part) for part in output_namespace.split("/"))
    output_path = alpha_data_root
    for part in namespace_parts:
        output_path /= part
    output_path = (
        output_path
        / _safe_path_token(_label_set_id(label_contracts))
        / _safe_path_token(dataset_version_id)
        / _safe_path_token(partition_id)
        / "values.jsonl"
    )
    _require_under_root(output_path, alpha_data_root)
    return output_path


def _label_set_id(label_contracts: tuple[LabelContractSpec, ...]) -> str:
    return "lset_" + content_hash(
        {
            "schema": LABEL_MATERIALIZATION_SCHEMA,
            "label_contracts": [contract.to_contract_dict() for contract in label_contracts],
        }
    )


def _plan_content_hash(
    label_contracts: tuple[LabelContractSpec, ...],
    *,
    dataset_version_id: str,
    partition_id: str,
    instrument_ids: tuple[str, ...],
    output_path: Path,
    governance_metadata: FrozenJsonMapping,
    dry_run: bool,
    label_lifecycle_state: str,
    legal_consumer: str,
) -> str:
    return content_hash(
        {
            "schema": LABEL_MATERIALIZATION_SCHEMA,
            "label_contracts": [contract.to_contract_dict() for contract in label_contracts],
            "dataset_version_id": dataset_version_id,
            "partition_id": partition_id,
            "instrument_ids": list(instrument_ids),
            "output_path": str(output_path),
            "governance_metadata": governance_metadata.to_dict(),
            "dry_run": dry_run,
            "label_lifecycle_state": label_lifecycle_state,
            "legal_consumer": legal_consumer,
        }
    )


def _label_contracts(value: object) -> tuple[LabelContractSpec, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LabelMaterializationError("label_contracts must be a sequence")
    contracts = tuple(_validate_label_contract(item) for item in value)
    if not contracts:
        raise LabelMaterializationError("label_contracts must not be empty")
    return contracts


def _validate_label_contract(value: object) -> LabelContractSpec:
    if not isinstance(value, LabelContractSpec):
        raise LabelMaterializationError("label_contracts must contain LabelContractSpec objects")
    _validate_materializable_contract(
        value,
        accepted_version=_AcceptedVersionPlaceholder(tuple(value.inputs.dataset_version_ids)),
    )
    return value


@dataclass(frozen=True, slots=True)
class _AcceptedVersionPlaceholder:
    dataset_ids: tuple[str, ...]

    @property
    def dataset_version_id(self) -> str:
        return self.dataset_ids[0] if self.dataset_ids else "__unbound__"


def _label_version_ids(label_contracts: tuple[LabelContractSpec, ...]) -> tuple[str, ...]:
    return tuple(contract.derive_label_version().label_version_id for contract in label_contracts)


def _merged_governance_metadata(
    plan: LabelMaterializationPlan,
    inputs: LabelMaterializationInputs,
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
        raise LabelMaterializationError(f"{field_name} must be an iterable of mappings")
    normalized = tuple(rows)
    for row in normalized:
        if isinstance(row, str) or not isinstance(row, Mapping):
            raise LabelMaterializationError(f"{field_name} must contain mappings")
    return normalized


def _filter_rows_for_instruments(
    rows: Iterable[Mapping[str, object]],
    instrument_ids: tuple[str, ...],
) -> tuple[Mapping[str, object], ...]:
    if not instrument_ids:
        return tuple(rows)
    allowed = set(instrument_ids)
    return tuple(row for row in rows if str(row.get("instrument_id", "")) in allowed)


def _freeze_json_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    try:
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    except LabelContractError as exc:
        raise LabelMaterializationError(str(exc)) from exc


def _require_accepted_lifecycle(accepted_version: AcceptedDatasetVersion) -> None:
    lifecycle_state = _require_text(
        accepted_version.lifecycle_state,
        "AcceptedDatasetVersion.lifecycle_state",
    ).upper()
    if lifecycle_state not in ACCEPTED_DATASET_VERSION_STATES:
        allowed = ", ".join(sorted(ACCEPTED_DATASET_VERSION_STATES))
        raise LabelMaterializationError(f"DatasetVersion lifecycle_state must be one of {allowed}")


def _require_lifecycle_state(value: object) -> str:
    state = _require_text(value, "label_lifecycle_state").upper()
    if state != LABEL_MATERIALIZATION_ALLOWED:
        raise LabelMaterializationError("LabelSpec lifecycle gate must be MATERIALIZATION_ALLOWED")
    return state


def _require_label_consumer(value: object) -> str:
    consumer = _require_text(value, "legal_consumer").lower()
    if consumer != LabelAvailabilityConsumer.LABELS_ONLY.value:
        raise LabelMaterializationError("labels cannot be exposed as live feature inputs")
    return consumer


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise LabelMaterializationError(f"{field_name} must be a bool")
    return value


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise LabelMaterializationError(f"{field_name} must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise LabelMaterializationError(f"{field_name} must be a non-empty single-line string")
    return text


def _text_tuple(
    values: Sequence[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise LabelMaterializationError(f"{field_name} must be a sequence of strings")
    normalized = tuple(_require_text(value, f"{field_name}[]") for value in values)
    if not normalized and not allow_empty:
        raise LabelMaterializationError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise LabelMaterializationError(f"{field_name} must not contain duplicates")
    return normalized


def _require_path(value: str | Path, field_name: str) -> Path:
    if not isinstance(value, str | Path):
        raise LabelMaterializationError(f"{field_name} must be a path")
    try:
        return Path(value).expanduser().resolve(strict=False)
    except RuntimeError as exc:
        raise LabelMaterializationError(f"{field_name} could not be resolved") from exc


def _require_under_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if resolved_path != resolved_root and not resolved_path.is_relative_to(resolved_root):
        raise LabelMaterializationError(
            "materialized label output path must stay under ALPHA_DATA_ROOT"
        )


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LabelMaterializationError(f"{field_name} must be timezone-aware")
    if value.tzinfo is None or value.utcoffset() is None:
        raise LabelMaterializationError(f"{field_name} must be timezone-aware")
    return value


def _safe_path_token(value: object) -> str:
    text = _require_text(value, "path token")
    normalized = text.replace(".", "_").replace("-", "_")
    if not normalized.replace("_", "").isalnum():
        raise LabelMaterializationError(f"path token contains unsupported characters: {text}")
    return normalized


__all__ = [
    "LABEL_MATERIALIZATION_ALLOWED",
    "LABEL_MATERIALIZATION_PURPOSE",
    "LABEL_MATERIALIZATION_SCHEMA",
    "LabelMaterializationError",
    "LabelMaterializationInputs",
    "LabelMaterializationPlan",
    "LabelMaterializationResult",
    "SupportedLabelDefinition",
    "build_label_materialization_plan",
    "materialize_labels",
    "resolve_label_materialization_dataset",
]
