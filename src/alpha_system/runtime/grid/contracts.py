"""Bounded-grid guard contracts for Tier 1 research runtime studies.

The grid package is an orchestration boundary: combination counting and hard
limit checks are delegated to ``alpha_system.experiments.limits`` and overfit
context is delegated to ``alpha_system.experiments.overfit_controls``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from alpha_system.experiments.limits import CombinationLimit, GridLimitError, product_count
from alpha_system.experiments.overfit_controls import (
    ManagementOverfitAssessment,
    assess_management_overfit_controls,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    content_hash,
    deserialize,
)
from alpha_system.runtime.contracts.run_spec import RuntimeContractError
from alpha_system.runtime.entry_contract import RuntimeEntryReason, RuntimeEntryStatus
from alpha_system.runtime.input_resolver import LOCKED_PARTITION_IDS

BOUNDED_GRID_SPEC_SCHEMA = "alpha_system.runtime.grid.spec.v1"
BOUNDED_GRID_RUN_RECORD_SCHEMA = "alpha_system.runtime.grid.run_record.v1"
BOUNDED_GRID_SPEC_ID_PREFIX = "bgrid"
BOUNDED_GRID_RECORD_ID_PREFIX = "bgrecord"
DEFAULT_GRID_PARTITIONS: tuple[str, ...] = ("development", "validation")


class BoundedGridOutcome(StrEnum):
    """Guard outcomes for descriptive bounded-grid records."""

    GUARD_PASSED = "GUARD_PASSED"
    GUARD_REJECTED = "GUARD_REJECTED"


class BoundedGridContractError(RuntimeContractError):
    """Fail-closed bounded-grid error with rejection-shaped reasons."""

    def __init__(
        self,
        reasons: RuntimeEntryReason | Sequence[RuntimeEntryReason],
        *,
        realized_variant_count: int | None = None,
        variant_budget: VariantBudget | None = None,
        binding_ref: BoundedGridBindingRef | None = None,
        partition_scope_ids: Sequence[str] = (),
    ) -> None:
        super().__init__(reasons)
        self.realized_variant_count = realized_variant_count
        self.variant_budget = variant_budget
        self.binding_ref = binding_ref
        self.partition_scope_ids = tuple(partition_scope_ids)


@dataclass(frozen=True, slots=True)
class VariantBudget:
    """Finite hard caps consumed before a bounded grid can run."""

    max_variants: int
    max_grid_points: int | None = None
    max_compute_units: int | None = None
    max_distinct_parameter_combinations: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_variants",
            _positive_int(self.max_variants, field="max_variants"),
        )
        for field in (
            "max_grid_points",
            "max_compute_units",
            "max_distinct_parameter_combinations",
        ):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _positive_int(value, field=field))

    @property
    def effective_max_combinations(self) -> int:
        """Return the strictest declared finite combination cap."""

        caps = [
            self.max_variants,
            self.max_grid_points,
            self.max_compute_units,
            self.max_distinct_parameter_combinations,
        ]
        return min(cap for cap in caps if cap is not None)

    def to_combination_limit(self) -> CombinationLimit:
        """Return the consumed experiments primitive limit object."""

        return CombinationLimit(self.effective_max_combinations)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible budget payload."""

        return {
            "max_variants": self.max_variants,
            "max_grid_points": self.max_grid_points,
            "max_compute_units": self.max_compute_units,
            "max_distinct_parameter_combinations": self.max_distinct_parameter_combinations,
            "effective_max_combinations": self.effective_max_combinations,
            "limit_primitive": "alpha_system.experiments.limits.CombinationLimit",
        }


@dataclass(frozen=True, slots=True, init=False)
class ParameterAxis:
    """One bounded parameter path and its finite candidate values."""

    parameter_path: str
    candidate_values_json: tuple[str, ...]

    def __init__(self, parameter_path: str, candidate_values: Sequence[JsonValue]) -> None:
        normalized_path = _required_text(parameter_path, field="parameter_path")
        if isinstance(candidate_values, str) or not isinstance(candidate_values, Sequence):
            raise ValueError("candidate_values must be a finite sequence")
        if not candidate_values:
            raise ValueError("candidate_values must not be empty")

        serialized_values: list[str] = []
        for index, value in enumerate(candidate_values):
            try:
                serialized_values.append(canonical_serialize(cast(JsonValue, value)))
            except GovernanceSerializationError as exc:
                raise ValueError(
                    f"candidate_values[{index}] must be JSON-compatible: {exc}"
                ) from exc
        if len(set(serialized_values)) != len(serialized_values):
            raise ValueError("candidate_values must not contain duplicates")

        object.__setattr__(self, "parameter_path", normalized_path)
        object.__setattr__(self, "candidate_values_json", tuple(serialized_values))

    @property
    def candidate_count(self) -> int:
        """Return the declared candidate count for this axis."""

        return len(self.candidate_values_json)

    @property
    def candidate_values(self) -> tuple[JsonValue, ...]:
        """Return candidate values as a defensive tuple."""

        return tuple(deserialize(value) for value in self.candidate_values_json)

    def to_dict(self) -> dict[str, object]:
        """Return a stable axis payload."""

        return {
            "parameter_path": self.parameter_path,
            "candidate_count": self.candidate_count,
            "candidate_values": list(self.candidate_values),
        }


@dataclass(frozen=True, slots=True)
class BoundedGridBindingRef:
    """Reference-only binding from a bounded grid to the study/probe context."""

    alpha_spec_ref: str
    study_spec_ref: str
    study_run_spec_id: str | None = None
    study_run_spec_content_hash: str | None = None
    signal_probe_spec_id: str | None = None
    signal_probe_spec_content_hash: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "alpha_spec_ref",
            _required_text(self.alpha_spec_ref, field="alpha_spec_ref"),
        )
        object.__setattr__(
            self,
            "study_spec_ref",
            _required_text(self.study_spec_ref, field="study_spec_ref"),
        )
        for field in (
            "study_run_spec_id",
            "study_run_spec_content_hash",
            "signal_probe_spec_id",
            "signal_probe_spec_content_hash",
        ):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _required_text(value, field=field))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> BoundedGridBindingRef:
        """Build a binding reference from JSON-compatible metadata."""

        _reject_extra_keys(
            value,
            allowed={
                "alpha_spec_ref",
                "study_spec_ref",
                "study_run_spec_id",
                "study_run_spec_content_hash",
                "signal_probe_spec_id",
                "signal_probe_spec_content_hash",
            },
            field="binding_ref",
        )
        return cls(
            alpha_spec_ref=value.get("alpha_spec_ref"),
            study_spec_ref=value.get("study_spec_ref"),
            study_run_spec_id=value.get("study_run_spec_id"),
            study_run_spec_content_hash=value.get("study_run_spec_content_hash"),
            signal_probe_spec_id=value.get("signal_probe_spec_id"),
            signal_probe_spec_content_hash=value.get("signal_probe_spec_content_hash"),
        )

    @classmethod
    def from_study_run_spec(cls, value: Any) -> BoundedGridBindingRef:
        """Build a binding from a StudyRunSpec-like object without editing contracts."""

        runtime_request = getattr(value, "runtime_request", None)
        return cls(
            alpha_spec_ref=getattr(runtime_request, "alpha_spec_ref", None),
            study_spec_ref=getattr(runtime_request, "study_spec_ref", None),
            study_run_spec_id=getattr(value, "study_run_spec_id", None),
            study_run_spec_content_hash=getattr(value, "content_hash", None),
        )

    def to_dict(self) -> dict[str, str | None]:
        """Return a stable reference payload."""

        return {
            "alpha_spec_ref": self.alpha_spec_ref,
            "study_spec_ref": self.study_spec_ref,
            "study_run_spec_id": self.study_run_spec_id,
            "study_run_spec_content_hash": self.study_run_spec_content_hash,
            "signal_probe_spec_id": self.signal_probe_spec_id,
            "signal_probe_spec_content_hash": self.signal_probe_spec_content_hash,
        }


@dataclass(frozen=True, slots=True)
class BoundedGridSpecRef:
    """Reference to a bounded-grid spec without copying parameter values."""

    bounded_grid_spec_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "bounded_grid_spec_id",
            _required_text(self.bounded_grid_spec_id, field="bounded_grid_spec_id"),
        )
        object.__setattr__(
            self,
            "content_hash",
            _required_text(self.content_hash, field="content_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable spec reference payload."""

        return {
            "bounded_grid_spec_id": self.bounded_grid_spec_id,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True, init=False)
class BoundedGridSpec:
    """Immutable contract for a finite candidate variant space."""

    bounded_grid_spec_id: str
    binding_ref: BoundedGridBindingRef
    parameter_axes: tuple[ParameterAxis, ...]
    variant_budget: VariantBudget
    partition_scope_jsons: tuple[str, ...]
    partition_purpose: str
    governance_metadata_json: str
    realized_variant_count: int
    content_hash: str

    def __init__(
        self,
        *,
        binding_ref: BoundedGridBindingRef | Mapping[str, Any] | Any,
        parameter_axes: Mapping[str, Sequence[JsonValue]]
        | Sequence[ParameterAxis | Mapping[str, Any]],
        variant_budget: VariantBudget | Mapping[str, Any] | None,
        partition_scope: Sequence[str | Mapping[str, Any]] | Mapping[str, Any] | None = None,
        partition_purpose: str = "grid_selection",
        governance_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        reasons: list[RuntimeEntryReason] = []
        normalized_binding = _coerce_binding_ref(binding_ref, reasons)
        normalized_axes = _coerce_parameter_axes(parameter_axes, reasons)
        normalized_budget = _coerce_variant_budget(variant_budget, reasons)
        normalized_partition_jsons = _coerce_partition_scope(partition_scope, reasons)
        normalized_purpose = _coerce_required_text(
            partition_purpose,
            field="partition_purpose",
            reasons=reasons,
        )
        metadata_json = _coerce_mapping(
            governance_metadata or {},
            field="governance_metadata",
            reasons=reasons,
        )

        count = _realized_variant_count(
            normalized_axes,
            grid_id="bounded_grid_spec",
            reasons=reasons,
        )
        if normalized_budget is not None and count is not None:
            _enforce_variant_budget(
                budget=normalized_budget,
                realized_variant_count=count,
                grid_id="bounded_grid_spec",
                reasons=reasons,
            )

        if reasons:
            raise BoundedGridContractError(
                tuple(reasons),
                realized_variant_count=count,
                variant_budget=normalized_budget,
                binding_ref=normalized_binding,
                partition_scope_ids=_partition_ids_from_jsons(normalized_partition_jsons),
            )

        assert normalized_binding is not None
        assert normalized_budget is not None
        assert normalized_purpose is not None
        assert count is not None
        assert metadata_json is not None

        payload = _bounded_grid_spec_payload(
            binding_ref=normalized_binding,
            parameter_axes=normalized_axes,
            variant_budget=normalized_budget,
            partition_scope_jsons=normalized_partition_jsons,
            partition_purpose=normalized_purpose,
            governance_metadata_json=metadata_json,
            realized_variant_count=count,
        )
        digest = content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "bounded_grid_spec_id",
            f"{BOUNDED_GRID_SPEC_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "binding_ref", normalized_binding)
        object.__setattr__(self, "parameter_axes", normalized_axes)
        object.__setattr__(self, "variant_budget", normalized_budget)
        object.__setattr__(self, "partition_scope_jsons", normalized_partition_jsons)
        object.__setattr__(self, "partition_purpose", normalized_purpose)
        object.__setattr__(self, "governance_metadata_json", metadata_json)
        object.__setattr__(self, "realized_variant_count", count)
        object.__setattr__(self, "content_hash", digest)

    @property
    def partition_scope(self) -> tuple[dict[str, JsonValue], ...]:
        """Return partition scope mappings as defensive copies."""

        return tuple(
            _json_dict(value, field="partition_scope")
            for value in self.partition_scope_jsons
        )

    @property
    def partition_scope_ids(self) -> tuple[str, ...]:
        """Return partition ids in their declared order."""

        return _partition_ids_from_jsons(self.partition_scope_jsons)

    @property
    def governance_metadata(self) -> dict[str, JsonValue]:
        """Return governance metadata as a defensive copy."""

        return _json_dict(self.governance_metadata_json, field="governance_metadata")

    def to_ref(self) -> BoundedGridSpecRef:
        """Return a compact bounded-grid spec reference."""

        return BoundedGridSpecRef(
            bounded_grid_spec_id=self.bounded_grid_spec_id,
            content_hash=self.content_hash,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable bounded-grid spec payload."""

        return {
            "schema": BOUNDED_GRID_SPEC_SCHEMA,
            "bounded_grid_spec_id": self.bounded_grid_spec_id,
            "binding_ref": self.binding_ref.to_dict(),
            "parameter_axes": [axis.to_dict() for axis in self.parameter_axes],
            "variant_budget": self.variant_budget.to_dict(),
            "partition_scope": list(self.partition_scope),
            "partition_purpose": self.partition_purpose,
            "governance_metadata_present": bool(self.governance_metadata),
            "realized_variant_count": self.realized_variant_count,
            "content_hash": self.content_hash,
            "bounded": True,
            "promotion_basis_allowed": False,
        }


@dataclass(frozen=True, slots=True, init=False)
class BoundedGridRunRecord:
    """Durable, value-free record for one bounded-grid guard evaluation."""

    record_id: str
    run_id: str
    bounded_grid_spec_ref: BoundedGridSpecRef
    binding_ref: BoundedGridBindingRef | None
    guard_outcome: BoundedGridOutcome
    variant_budget: VariantBudget | None
    realized_variant_count: int | None
    partition_scope_ids: tuple[str, ...]
    rejection_reasons: tuple[RuntimeEntryReason, ...]
    overfit_warning_count: int
    overfit_control_keys: tuple[str, ...]
    repeated_run_index: int
    previous_run_record_ids: tuple[str, ...]
    content_hash: str

    def __init__(
        self,
        *,
        run_id: str,
        bounded_grid_spec_ref: BoundedGridSpec | BoundedGridSpecRef | Mapping[str, Any],
        binding_ref: BoundedGridBindingRef | Mapping[str, Any] | None,
        guard_outcome: BoundedGridOutcome | str,
        variant_budget: VariantBudget | Mapping[str, Any] | None,
        realized_variant_count: int | None,
        partition_scope_ids: Sequence[str],
        rejection_reasons: Sequence[RuntimeEntryReason | Mapping[str, Any]] = (),
        overfit_assessment: ManagementOverfitAssessment | None = None,
        repeated_run_index: int = 1,
        previous_run_record_ids: Sequence[str] = (),
    ) -> None:
        normalized_run_id = _required_text(run_id, field="run_id")
        spec_ref = _coerce_spec_ref(bounded_grid_spec_ref)
        normalized_binding = _coerce_optional_binding_ref(binding_ref)
        outcome = _coerce_guard_outcome(guard_outcome)
        budget = _coerce_optional_budget_for_record(variant_budget)
        count = _coerce_optional_non_negative_int(
            realized_variant_count,
            field="realized_variant_count",
        )
        partitions = tuple(
            _required_text(value, field="partition_scope_id")
            for value in partition_scope_ids
        )
        reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)
        if outcome is BoundedGridOutcome.GUARD_REJECTED and not reasons:
            raise ValueError("rejected bounded-grid records require visible reasons")
        if outcome is BoundedGridOutcome.GUARD_PASSED and reasons:
            raise ValueError("successful bounded-grid records must not carry rejection reasons")
        overfit_keys = _overfit_control_keys(overfit_assessment)
        overfit_warning_count = (
            0 if overfit_assessment is None else len(overfit_assessment.warnings)
        )
        index = _positive_int(repeated_run_index, field="repeated_run_index")
        previous_ids = tuple(
            _required_text(value, field="previous_run_record_id")
            for value in previous_run_record_ids
        )

        payload = _bounded_grid_record_payload(
            run_id=normalized_run_id,
            bounded_grid_spec_ref=spec_ref,
            binding_ref=normalized_binding,
            guard_outcome=outcome,
            variant_budget=budget,
            realized_variant_count=count,
            partition_scope_ids=partitions,
            rejection_reasons=reasons,
            overfit_warning_count=overfit_warning_count,
            overfit_control_keys=overfit_keys,
            repeated_run_index=index,
            previous_run_record_ids=previous_ids,
        )
        digest = content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "record_id",
            f"{BOUNDED_GRID_RECORD_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "run_id", normalized_run_id)
        object.__setattr__(self, "bounded_grid_spec_ref", spec_ref)
        object.__setattr__(self, "binding_ref", normalized_binding)
        object.__setattr__(self, "guard_outcome", outcome)
        object.__setattr__(self, "variant_budget", budget)
        object.__setattr__(self, "realized_variant_count", count)
        object.__setattr__(self, "partition_scope_ids", partitions)
        object.__setattr__(self, "rejection_reasons", reasons)
        object.__setattr__(self, "overfit_warning_count", overfit_warning_count)
        object.__setattr__(self, "overfit_control_keys", overfit_keys)
        object.__setattr__(self, "repeated_run_index", index)
        object.__setattr__(self, "previous_run_record_ids", previous_ids)
        object.__setattr__(self, "content_hash", digest)

    def to_dict(self) -> dict[str, object]:
        """Return a stable value-free guard record."""

        return _bounded_grid_record_payload(
            run_id=self.run_id,
            bounded_grid_spec_ref=self.bounded_grid_spec_ref,
            binding_ref=self.binding_ref,
            guard_outcome=self.guard_outcome,
            variant_budget=self.variant_budget,
            realized_variant_count=self.realized_variant_count,
            partition_scope_ids=self.partition_scope_ids,
            rejection_reasons=self.rejection_reasons,
            overfit_warning_count=self.overfit_warning_count,
            overfit_control_keys=self.overfit_control_keys,
            repeated_run_index=self.repeated_run_index,
            previous_run_record_ids=self.previous_run_record_ids,
            record_id=self.record_id,
            content_hash=self.content_hash,
        )


@dataclass(frozen=True, slots=True)
class BoundedGridValidationResult:
    """Outcome returned when construction and guard evaluation are requested together."""

    status: BoundedGridOutcome | RuntimeEntryStatus
    reasons: tuple[RuntimeEntryReason, ...]
    spec: BoundedGridSpec | None
    record: BoundedGridRunRecord

    @property
    def accepted(self) -> bool:
        """Return true only when the guard accepted the bounded grid."""

        return self.status is BoundedGridOutcome.GUARD_PASSED

    @property
    def rejected(self) -> bool:
        """Return true when construction or guard evaluation failed closed."""

        return self.status in {
            BoundedGridOutcome.GUARD_REJECTED,
            RuntimeEntryStatus.INPUTS_BLOCKED,
            RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
        }

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible validation outcome."""

        return {
            "status": self.status.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
            "spec": None if self.spec is None else self.spec.to_dict(),
            "record": self.record.to_dict(),
        }


def guard_bounded_grid(
    spec: BoundedGridSpec,
    *,
    run_id: str,
    survivor_warning_count: int = 0,
    rejected_count: int = 0,
    repeated_run_index: int = 1,
    previous_run_record_ids: Sequence[str] = (),
) -> BoundedGridRunRecord:
    """Evaluate the bounded-grid guard and return a durable visible record."""

    if not isinstance(spec, BoundedGridSpec):
        raise TypeError("guard_bounded_grid requires a BoundedGridSpec")
    survivor_warnings = _coerce_non_negative_int(
        survivor_warning_count,
        field="survivor_warning_count",
    )
    existing_rejections = _coerce_non_negative_int(rejected_count, field="rejected_count")
    reasons = _locked_partition_reasons(spec)
    overfit_assessment = assess_management_overfit_controls(
        combination_count=spec.realized_variant_count,
        max_combinations=spec.variant_budget.effective_max_combinations,
        parameter_paths=(axis.parameter_path for axis in spec.parameter_axes),
        survivor_warning_count=survivor_warnings,
        rejected_count=existing_rejections + len(reasons),
    )
    outcome = (
        BoundedGridOutcome.GUARD_REJECTED
        if reasons
        else BoundedGridOutcome.GUARD_PASSED
    )
    return BoundedGridRunRecord(
        run_id=run_id,
        bounded_grid_spec_ref=spec.to_ref(),
        binding_ref=spec.binding_ref,
        guard_outcome=outcome,
        variant_budget=spec.variant_budget,
        realized_variant_count=spec.realized_variant_count,
        partition_scope_ids=spec.partition_scope_ids,
        rejection_reasons=reasons,
        overfit_assessment=overfit_assessment,
        repeated_run_index=repeated_run_index,
        previous_run_record_ids=previous_run_record_ids,
    )


def validate_bounded_grid_request(
    *,
    run_id: str,
    binding_ref: BoundedGridBindingRef | Mapping[str, Any] | Any,
    parameter_axes: Mapping[str, Sequence[JsonValue]]
    | Sequence[ParameterAxis | Mapping[str, Any]],
    variant_budget: VariantBudget | Mapping[str, Any] | None,
    partition_scope: Sequence[str | Mapping[str, Any]] | Mapping[str, Any] | None = None,
    partition_purpose: str = "grid_selection",
    governance_metadata: Mapping[str, Any] | None = None,
    repeated_run_index: int = 1,
    previous_run_record_ids: Sequence[str] = (),
) -> BoundedGridValidationResult:
    """Construct and guard a bounded-grid request while keeping failures visible."""

    try:
        spec = BoundedGridSpec(
            binding_ref=binding_ref,
            parameter_axes=parameter_axes,
            variant_budget=variant_budget,
            partition_scope=partition_scope,
            partition_purpose=partition_purpose,
            governance_metadata=governance_metadata,
        )
    except BoundedGridContractError as exc:
        fallback_ref = BoundedGridSpecRef(
            bounded_grid_spec_id="bgrid_unbuilt",
            content_hash="unbuilt",
        )
        record = BoundedGridRunRecord(
            run_id=run_id,
            bounded_grid_spec_ref=fallback_ref,
            binding_ref=exc.binding_ref,
            guard_outcome=BoundedGridOutcome.GUARD_REJECTED,
            variant_budget=exc.variant_budget,
            realized_variant_count=exc.realized_variant_count,
            partition_scope_ids=exc.partition_scope_ids or DEFAULT_GRID_PARTITIONS,
            rejection_reasons=exc.reasons,
            overfit_assessment=None,
            repeated_run_index=repeated_run_index,
            previous_run_record_ids=previous_run_record_ids,
        )
        status = (
            RuntimeEntryStatus.INPUTS_BLOCKED
            if any(
                reason.decision_state is RuntimeEntryStatus.INPUTS_BLOCKED
                for reason in exc.reasons
            )
            else RuntimeEntryStatus.INPUTS_INCONCLUSIVE
        )
        return BoundedGridValidationResult(
            status=status,
            reasons=exc.reasons,
            spec=None,
            record=record,
        )

    record = guard_bounded_grid(
        spec,
        run_id=run_id,
        repeated_run_index=repeated_run_index,
        previous_run_record_ids=previous_run_record_ids,
    )
    return BoundedGridValidationResult(
        status=record.guard_outcome,
        reasons=record.rejection_reasons,
        spec=spec,
        record=record,
    )


def _bounded_grid_spec_payload(
    *,
    binding_ref: BoundedGridBindingRef,
    parameter_axes: tuple[ParameterAxis, ...],
    variant_budget: VariantBudget,
    partition_scope_jsons: tuple[str, ...],
    partition_purpose: str,
    governance_metadata_json: str,
    realized_variant_count: int,
) -> dict[str, object]:
    return {
        "schema": BOUNDED_GRID_SPEC_SCHEMA,
        "binding_ref": binding_ref.to_dict(),
        "parameter_axes": [axis.to_dict() for axis in parameter_axes],
        "variant_budget": variant_budget.to_dict(),
        "partition_scope": [
            _json_dict(value, field="partition_scope")
            for value in partition_scope_jsons
        ],
        "partition_purpose": partition_purpose,
        "governance_metadata": _json_dict(
            governance_metadata_json,
            field="governance_metadata",
        ),
        "realized_variant_count": realized_variant_count,
        "bounded": True,
        "promotion_basis_allowed": False,
    }


def _bounded_grid_record_payload(
    *,
    run_id: str,
    bounded_grid_spec_ref: BoundedGridSpecRef,
    binding_ref: BoundedGridBindingRef | None,
    guard_outcome: BoundedGridOutcome,
    variant_budget: VariantBudget | None,
    realized_variant_count: int | None,
    partition_scope_ids: tuple[str, ...],
    rejection_reasons: tuple[RuntimeEntryReason, ...],
    overfit_warning_count: int,
    overfit_control_keys: tuple[str, ...],
    repeated_run_index: int,
    previous_run_record_ids: tuple[str, ...],
    record_id: str | None = None,
    content_hash: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": BOUNDED_GRID_RUN_RECORD_SCHEMA,
        "run_id": run_id,
        "bounded_grid_spec_ref": bounded_grid_spec_ref.to_dict(),
        "binding_ref": None if binding_ref is None else binding_ref.to_dict(),
        "guard_outcome": guard_outcome.value,
        "variant_budget": None if variant_budget is None else variant_budget.to_dict(),
        "realized_variant_count": realized_variant_count,
        "partition_scope_ids": list(partition_scope_ids),
        "rejection_reasons": [reason.to_dict() for reason in rejection_reasons],
        "overfit_context": {
            "assessment_primitive": (
                "alpha_system.experiments.overfit_controls."
                "assess_management_overfit_controls"
            ),
            "warning_count": overfit_warning_count,
            "control_keys": list(overfit_control_keys),
        },
        "repeated_run_index": repeated_run_index,
        "previous_run_record_ids": list(previous_run_record_ids),
        "value_free": True,
        "raw_or_heavy_data_embedded": False,
        "promotion_basis_allowed": False,
    }
    if record_id is not None:
        payload["record_id"] = record_id
    if content_hash is not None:
        payload["content_hash"] = content_hash
    return payload


def _coerce_binding_ref(
    value: BoundedGridBindingRef | Mapping[str, Any] | Any,
    reasons: list[RuntimeEntryReason],
) -> BoundedGridBindingRef | None:
    try:
        if isinstance(value, BoundedGridBindingRef):
            return value
        if isinstance(value, Mapping):
            return BoundedGridBindingRef.from_mapping(value)
        return BoundedGridBindingRef.from_study_run_spec(value)
    except (TypeError, ValueError) as exc:
        reasons.append(
            _reason(
                code="invalid_grid_binding_ref",
                message="BoundedGridSpec requires a reference-only study/probe binding",
                field="binding_ref",
                expected="BoundedGridBindingRef",
                actual=str(exc),
            )
        )
        return None


def _coerce_optional_binding_ref(
    value: BoundedGridBindingRef | Mapping[str, Any] | None,
) -> BoundedGridBindingRef | None:
    if value is None:
        return None
    if isinstance(value, BoundedGridBindingRef):
        return value
    if isinstance(value, Mapping):
        return BoundedGridBindingRef.from_mapping(value)
    raise ValueError("binding_ref must be BoundedGridBindingRef, mapping, or None")


def _coerce_parameter_axes(
    value: Mapping[str, Sequence[JsonValue]] | Sequence[ParameterAxis | Mapping[str, Any]],
    reasons: list[RuntimeEntryReason],
) -> tuple[ParameterAxis, ...]:
    axes: list[ParameterAxis] = []
    try:
        if isinstance(value, Mapping):
            axes = [
                ParameterAxis(path, value[path])
                for path in sorted(value)
            ]
        elif isinstance(value, str) or not isinstance(value, Sequence):
            raise ValueError("parameter_axes must be a mapping or finite sequence")
        else:
            axes = [_coerce_axis(item) for item in value]
        paths = [axis.parameter_path for axis in axes]
        if len(paths) != len(set(paths)):
            raise ValueError("parameter_axes must not contain duplicate parameter paths")
    except (TypeError, ValueError) as exc:
        reasons.append(
            _reason(
                code="invalid_parameter_axes",
                message="BoundedGridSpec requires finite parameter axes",
                field="parameter_axes",
                expected="non-empty finite candidate axes",
                actual=str(exc),
            )
        )
        return ()
    return tuple(axes)


def _coerce_axis(value: ParameterAxis | Mapping[str, Any]) -> ParameterAxis:
    if isinstance(value, ParameterAxis):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={"parameter_path", "candidate_values"},
            field="parameter_axis",
        )
        candidate_values = value.get("candidate_values")
        if isinstance(candidate_values, str) or not isinstance(candidate_values, Sequence):
            raise ValueError("parameter_axis.candidate_values must be a finite sequence")
        return ParameterAxis(
            parameter_path=value.get("parameter_path"),
            candidate_values=cast(Sequence[JsonValue], candidate_values),
        )
    raise ValueError("parameter axis must be ParameterAxis or mapping")


def _coerce_variant_budget(
    value: VariantBudget | Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> VariantBudget | None:
    if value is None:
        reasons.append(
            _reason(
                code="unbounded_grid",
                message="BoundedGridSpec requires an explicit finite VariantBudget",
                field="variant_budget",
                expected="VariantBudget",
                actual="missing",
            )
        )
        return None
    try:
        if isinstance(value, VariantBudget):
            return value
        if isinstance(value, Mapping):
            _reject_extra_keys(
                value,
                allowed={
                    "max_variants",
                    "max_grid_points",
                    "max_compute_units",
                    "max_distinct_parameter_combinations",
                },
                field="variant_budget",
            )
            return VariantBudget(
                max_variants=value.get("max_variants"),
                max_grid_points=value.get("max_grid_points"),
                max_compute_units=value.get("max_compute_units"),
                max_distinct_parameter_combinations=value.get(
                    "max_distinct_parameter_combinations"
                ),
            )
    except (TypeError, ValueError, GridLimitError) as exc:
        reasons.append(
            _reason(
                code="unbounded_grid",
                message="VariantBudget must declare positive finite caps",
                field="variant_budget",
                expected="positive finite VariantBudget",
                actual=str(exc),
            )
        )
        return None
    reasons.append(
        _reason(
            code="unbounded_grid",
            message="VariantBudget must be explicit and finite",
            field="variant_budget",
            expected="VariantBudget",
            actual=type(value).__name__,
        )
    )
    return None


def _coerce_optional_budget_for_record(
    value: VariantBudget | Mapping[str, Any] | None,
) -> VariantBudget | None:
    if value is None:
        return None
    if isinstance(value, VariantBudget):
        return value
    if isinstance(value, Mapping):
        return VariantBudget(
            max_variants=value.get("max_variants"),
            max_grid_points=value.get("max_grid_points"),
            max_compute_units=value.get("max_compute_units"),
            max_distinct_parameter_combinations=value.get(
                "max_distinct_parameter_combinations"
            ),
        )
    raise ValueError("variant_budget must be VariantBudget, mapping, or None")


def _coerce_partition_scope(
    value: Sequence[str | Mapping[str, Any]] | Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> tuple[str, ...]:
    raw_scope: Sequence[str | Mapping[str, Any]]
    if value is None:
        raw_scope = tuple(DEFAULT_GRID_PARTITIONS)
    elif isinstance(value, Mapping):
        raw_scope = (value,)
    elif isinstance(value, str) or not isinstance(value, Sequence):
        reasons.append(
            _reason(
                code="invalid_partition_scope",
                message="partition_scope must be a finite partition sequence",
                field="partition_scope",
                expected="development/validation partition scope",
                actual=type(value).__name__,
            )
        )
        return ()
    else:
        raw_scope = value

    if not raw_scope:
        reasons.append(
            _reason(
                code="invalid_partition_scope",
                message="partition_scope must not be empty",
                field="partition_scope",
                expected="development/validation partition scope",
                actual="empty",
            )
        )
        return ()

    serialized: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_scope):
        try:
            if isinstance(item, str):
                partition = {"partition_id": _required_text(item, field="partition_id")}
            elif isinstance(item, Mapping):
                partition_id = _required_text(item.get("partition_id"), field="partition_id")
                partition = dict(item)
                partition["partition_id"] = partition_id
            else:
                raise ValueError("partition scope item must be a partition id or mapping")
        except ValueError as exc:
            reasons.append(
                _reason(
                    code="invalid_partition_scope",
                    message="partition_scope items must declare partition ids",
                    field=f"partition_scope[{index}]",
                    expected="partition id or mapping",
                    actual=str(exc),
                )
            )
            continue
        partition_id = str(partition["partition_id"])
        if partition_id in seen_ids:
            reasons.append(
                _reason(
                    code="invalid_partition_scope",
                    message="partition_scope must not repeat partition ids",
                    field="partition_scope",
                    expected="unique partition ids",
                    actual=partition_id,
                )
            )
            continue
        seen_ids.add(partition_id)
        try:
            serialized.append(canonical_serialize(cast(JsonValue, partition)))
        except GovernanceSerializationError as exc:
            reasons.append(
                _reason(
                    code="invalid_partition_scope",
                    message="partition_scope must be JSON-compatible",
                    field=f"partition_scope[{index}]",
                    expected="JSON-compatible partition scope",
                    actual=str(exc),
                )
            )
    return tuple(serialized)


def _coerce_mapping(
    value: Mapping[str, Any],
    *,
    field: str,
    reasons: list[RuntimeEntryReason],
) -> str | None:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except (TypeError, ValueError, GovernanceSerializationError) as exc:
        reasons.append(
            _reason(
                code="invalid_metadata",
                message=f"{field} must be JSON-compatible metadata",
                field=field,
                expected="JSON-compatible mapping",
                actual=str(exc),
            )
        )
        return None


def _coerce_required_text(
    value: object,
    *,
    field: str,
    reasons: list[RuntimeEntryReason],
) -> str | None:
    try:
        return _required_text(value, field=field)
    except ValueError as exc:
        reasons.append(
            _reason(
                code=f"invalid_{field}",
                message=f"{field} is required",
                field=field,
                expected="non-empty string",
                actual=str(exc),
            )
        )
        return None


def _realized_variant_count(
    axes: tuple[ParameterAxis, ...],
    *,
    grid_id: str,
    reasons: list[RuntimeEntryReason],
) -> int | None:
    try:
        return product_count(axis.candidate_count for axis in axes)
    except GridLimitError as exc:
        reasons.append(
            _reason(
                code="unbounded_grid",
                message="BoundedGridSpec requires at least one finite candidate per axis",
                field="parameter_axes",
                expected="finite non-empty parameter axes",
                actual=str(exc),
            )
        )
        _ = grid_id
        return exc.count


def _enforce_variant_budget(
    *,
    budget: VariantBudget,
    realized_variant_count: int,
    grid_id: str,
    reasons: list[RuntimeEntryReason],
) -> None:
    try:
        budget.to_combination_limit().enforce(realized_variant_count, grid_id=grid_id)
    except GridLimitError as exc:
        reasons.append(
            _reason(
                code="variant_budget_exceeded",
                message="BoundedGridSpec candidate space exceeds its VariantBudget",
                field="variant_budget",
                expected=str(exc.max_combinations or budget.effective_max_combinations),
                actual=str(exc.count or realized_variant_count),
            )
        )


def _locked_partition_reasons(spec: BoundedGridSpec) -> tuple[RuntimeEntryReason, ...]:
    reasons: list[RuntimeEntryReason] = []
    locked_ids = [
        partition_id
        for partition_id in spec.partition_scope_ids
        if _is_locked_partition_id(partition_id)
    ]
    if not locked_ids:
        return ()

    normalized_purpose = _normalize_token(spec.partition_purpose)
    if "selection" in normalized_purpose:
        reasons.append(
            _reason(
                code="locked_test_selection",
                message="Bounded-grid selection must not use locked or shadow partitions",
                field="partition_scope",
                expected="development/validation selection scope",
                actual=",".join(locked_ids),
            )
        )
    if not _contains_contamination_metadata(spec.governance_metadata):
        reasons.append(
            _reason(
                code="locked_partition_governance_metadata_missing",
                message="Locked or shadow partition use requires governance contamination metadata",
                field="governance_metadata",
                expected="substantive governance contamination metadata",
                actual="missing",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            )
        )
    return tuple(reasons)


def _coerce_spec_ref(
    value: BoundedGridSpec | BoundedGridSpecRef | Mapping[str, Any],
) -> BoundedGridSpecRef:
    if isinstance(value, BoundedGridSpec):
        return value.to_ref()
    if isinstance(value, BoundedGridSpecRef):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={"bounded_grid_spec_id", "content_hash"},
            field="bounded_grid_spec_ref",
        )
        return BoundedGridSpecRef(
            bounded_grid_spec_id=value.get("bounded_grid_spec_id"),
            content_hash=value.get("content_hash"),
        )
    raise ValueError("bounded_grid_spec_ref must be BoundedGridSpec, ref, or mapping")


def _coerce_guard_outcome(value: BoundedGridOutcome | str) -> BoundedGridOutcome:
    if isinstance(value, BoundedGridOutcome):
        return value
    if isinstance(value, str):
        return BoundedGridOutcome(value)
    raise ValueError("guard_outcome must be a BoundedGridOutcome or str")


def _coerce_rejection_reason(
    value: RuntimeEntryReason | Mapping[str, Any],
) -> RuntimeEntryReason:
    if isinstance(value, RuntimeEntryReason):
        return value
    if isinstance(value, Mapping):
        return RuntimeEntryReason(
            code=value.get("code"),
            message=value.get("message"),
            field=value.get("field"),
            decision_state=RuntimeEntryStatus(value.get("decision_state")),
            expected=value.get("expected"),
            actual=value.get("actual"),
        )
    raise ValueError("rejection reason must be RuntimeEntryReason or mapping")


def _overfit_control_keys(
    assessment: ManagementOverfitAssessment | None,
) -> tuple[str, ...]:
    if assessment is None:
        return ()
    return tuple(sorted(str(key) for key in assessment.controls))


def _partition_ids_from_jsons(values: Sequence[str]) -> tuple[str, ...]:
    ids: list[str] = []
    for value in values:
        scope = _json_dict(value, field="partition_scope")
        ids.append(str(scope["partition_id"]))
    return tuple(ids)


def _json_dict(text: str, *, field: str) -> dict[str, JsonValue]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise ValueError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{field} must serialize to a mapping")
    return dict(value)


def _contains_contamination_metadata(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(key)
            if "contamination" in normalized_key and not _is_missing(item):
                return True
            if normalized_key == "governance_metadata" and not _is_missing(item):
                return True
            if _contains_contamination_metadata(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_contamination_metadata(item) for item in value)
    return False


def _is_locked_partition_id(value: str) -> bool:
    normalized = _normalize_token(value)
    return any(
        _normalize_token(partition_id) in normalized
        for partition_id in LOCKED_PARTITION_IDS
    )


def _normalize_token(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _reason(
    *,
    code: str,
    message: str,
    field: str,
    expected: str,
    actual: str,
    state: RuntimeEntryStatus = RuntimeEntryStatus.INPUTS_BLOCKED,
) -> RuntimeEntryReason:
    return RuntimeEntryReason(
        code=code,
        message=message,
        field=field,
        decision_state=state,
        expected=expected,
        actual=actual,
    )


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _coerce_non_negative_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _coerce_optional_non_negative_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    return _coerce_non_negative_int(value, field=field)


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise ValueError(f"{field} contains unsupported fields: {', '.join(sorted(extra))}")


__all__ = [
    "BOUNDED_GRID_RECORD_ID_PREFIX",
    "BOUNDED_GRID_RUN_RECORD_SCHEMA",
    "BOUNDED_GRID_SPEC_ID_PREFIX",
    "BOUNDED_GRID_SPEC_SCHEMA",
    "DEFAULT_GRID_PARTITIONS",
    "BoundedGridBindingRef",
    "BoundedGridContractError",
    "BoundedGridOutcome",
    "BoundedGridRunRecord",
    "BoundedGridSpec",
    "BoundedGridSpecRef",
    "BoundedGridValidationResult",
    "ParameterAxis",
    "VariantBudget",
    "guard_bounded_grid",
    "validate_bounded_grid_request",
]
