"""Validated bounded-plan contracts for pre-execution research runtime jobs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, cast

from alpha_system.experiments.limits import CombinationLimit, GridLimitError
from alpha_system.governance.serialization import JsonValue, canonical_serialize, content_hash
from alpha_system.runtime.contracts.run_spec import (
    RuntimeContractError,
    RuntimeLifecycleState,
    RuntimeRequest,
    _actual,
    _is_missing,
    _json_dict,
    _prefixed_hash,
    _reason,
)
from alpha_system.runtime.entry_contract import RuntimeEntryReason, RuntimeEntryStatus
from alpha_system.runtime.input_resolver import LOCKED_PARTITION_IDS

RUNTIME_PLAN_SCHEMA = "alpha_system.runtime.plan.v1"
RUNTIME_PLAN_ID_PREFIX = "rplan"
DOUBLE_COST_PROFILE = "double_cost"

CAMPAIGN_PARTITIONS = MappingProxyType(
    {
        "development": MappingProxyType({"start": "2018-01-01", "end": "2022-12-31"}),
        "validation": MappingProxyType({"start": "2023-01-01", "end": "2024-12-31"}),
        "locked_test_candidate": MappingProxyType({"start": "2025-01-01", "end": "as_of_run"}),
        "latest_shadow_candidate": MappingProxyType({"start": "2025-01-01", "end": "as_of_run"}),
    }
)


@dataclass(frozen=True, slots=True, init=False)
class RuntimePlan:
    """Validated bounded execution plan; still no execution outcome."""

    plan_id: str
    runtime_request: RuntimeRequest
    request_content_hash: str
    partition_scope_json: str
    session_scope_json: str
    include_signal_probe: bool
    bounded: bool
    variant_grid_ref: str | None
    variant_budget: CombinationLimit | None
    cost_stress_profiles: tuple[str, ...]
    governance_metadata_json: str
    partition_purpose: str
    plan_metadata_json: str
    status: RuntimeLifecycleState
    content_hash: str

    def __init__(
        self,
        *,
        runtime_request: RuntimeRequest,
        partition_scope: Mapping[str, Any] | None,
        session_scope: Mapping[str, Any] | None,
        include_signal_probe: bool = False,
        bounded: bool = True,
        variant_grid_ref: str | None = None,
        variant_budget: CombinationLimit | int | None = None,
        cost_stress_profiles: Sequence[str] | Mapping[str, Any] = (),
        governance_metadata: Mapping[str, Any] | None = None,
        partition_purpose: str = "research_runtime_plan",
        plan_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        reasons: list[RuntimeEntryReason] = []
        request = _coerce_runtime_request(runtime_request, reasons)
        partition_id, partition_json = _coerce_partition_scope(partition_scope, reasons)
        session_json = _coerce_required_mapping(
            session_scope,
            field="session_scope",
            expected="non-empty session scope mapping",
            reasons=reasons,
        )
        metadata_json = _coerce_mapping(
            governance_metadata or {},
            field="governance_metadata",
            reasons=reasons,
        )
        plan_metadata_json = _coerce_mapping(
            plan_metadata or {},
            field="plan_metadata",
            reasons=reasons,
        )
        profiles = _normalize_cost_stress_profiles(cost_stress_profiles, reasons)
        budget = _coerce_variant_budget(variant_budget, reasons)

        if bounded is not True:
            reasons.append(
                _reason(
                    code="unbounded_runtime_plan",
                    message="RuntimePlan must declare a bounded job",
                    field="bounded",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="True",
                    actual=_actual(bounded),
                )
            )

        if include_signal_probe:
            _validate_probe_budget_and_cost_stress(
                variant_grid_ref=variant_grid_ref,
                variant_budget=budget,
                cost_stress_profiles=profiles,
                reasons=reasons,
            )

        if request is not None and partition_json is not None:
            _require_scope_match(
                expected=request.runtime_input_pack.partition_scope,
                actual_json=partition_json,
                field="partition_scope",
                code="partition_scope_runtime_input_mismatch",
                message="RuntimePlan partition scope must match the RuntimeInputPack",
                reasons=reasons,
            )
        if request is not None and session_json is not None:
            _require_scope_match(
                expected=request.runtime_input_pack.session_scope,
                actual_json=session_json,
                field="session_scope",
                code="session_scope_runtime_input_mismatch",
                message="RuntimePlan session scope must match the RuntimeInputPack",
                reasons=reasons,
            )

        if partition_id is not None:
            _validate_locked_partition_scope(
                partition_id=partition_id,
                partition_scope=partition_scope or {},
                governance_metadata=governance_metadata or {},
                governance_metadata_json=metadata_json,
                partition_purpose=partition_purpose,
                reasons=reasons,
            )

        if reasons:
            raise RuntimeContractError(tuple(reasons))

        assert request is not None
        assert partition_json is not None
        assert session_json is not None
        assert metadata_json is not None
        assert plan_metadata_json is not None

        payload = _runtime_plan_payload(
            request=request,
            partition_scope_json=partition_json,
            session_scope_json=session_json,
            include_signal_probe=include_signal_probe,
            bounded=bounded,
            variant_grid_ref=variant_grid_ref,
            variant_budget=budget,
            cost_stress_profiles=profiles,
            governance_metadata_json=metadata_json,
            partition_purpose=partition_purpose,
            plan_metadata_json=plan_metadata_json,
        )
        plan_hash = content_hash(cast(JsonValue, payload))

        object.__setattr__(self, "plan_id", _prefixed_hash(RUNTIME_PLAN_ID_PREFIX, plan_hash))
        object.__setattr__(self, "runtime_request", request)
        object.__setattr__(self, "request_content_hash", request.content_hash)
        object.__setattr__(self, "partition_scope_json", partition_json)
        object.__setattr__(self, "session_scope_json", session_json)
        object.__setattr__(self, "include_signal_probe", include_signal_probe)
        object.__setattr__(self, "bounded", bounded)
        object.__setattr__(self, "variant_grid_ref", variant_grid_ref)
        object.__setattr__(self, "variant_budget", budget)
        object.__setattr__(self, "cost_stress_profiles", profiles)
        object.__setattr__(self, "governance_metadata_json", metadata_json)
        object.__setattr__(self, "partition_purpose", partition_purpose)
        object.__setattr__(self, "plan_metadata_json", plan_metadata_json)
        object.__setattr__(self, "status", RuntimeLifecycleState.PLAN_VALIDATED)
        object.__setattr__(self, "content_hash", plan_hash)

    @property
    def partition_scope(self) -> dict[str, JsonValue]:
        """Return the bound campaign partition scope."""

        return _json_dict(self.partition_scope_json, object_name="RuntimePlan.partition_scope")

    @property
    def session_scope(self) -> dict[str, JsonValue]:
        """Return the bound session scope."""

        return _json_dict(self.session_scope_json, object_name="RuntimePlan.session_scope")

    @property
    def governance_metadata(self) -> dict[str, JsonValue]:
        """Return governance contamination metadata as a defensive copy."""

        return _json_dict(
            self.governance_metadata_json,
            object_name="RuntimePlan.governance_metadata",
        )

    @property
    def plan_metadata(self) -> dict[str, JsonValue]:
        """Return plan metadata as a defensive copy."""

        return _json_dict(self.plan_metadata_json, object_name="RuntimePlan.plan_metadata")

    def to_dict(self) -> dict[str, object]:
        """Return a stable validated-plan payload without execution results."""

        return {
            "schema": RUNTIME_PLAN_SCHEMA,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "request_content_hash": self.request_content_hash,
            "partition_scope": self.partition_scope,
            "session_scope": self.session_scope,
            "include_signal_probe": self.include_signal_probe,
            "bounded": self.bounded,
            "variant_grid_ref": self.variant_grid_ref,
            "variant_budget": _variant_budget_payload(self.variant_budget),
            "cost_stress_profiles": list(self.cost_stress_profiles),
            "governance_metadata": self.governance_metadata,
            "partition_purpose": self.partition_purpose,
            "plan_metadata": self.plan_metadata,
            "content_hash": self.content_hash,
            "execution_outcome": None,
        }


@dataclass(frozen=True, slots=True)
class RuntimePlanValidationResult:
    """Plan validation result with either PLAN_VALIDATED or fail-closed reasons."""

    status: RuntimeLifecycleState | RuntimeEntryStatus
    reasons: tuple[RuntimeEntryReason, ...]
    plan: RuntimePlan | None = None

    @property
    def validated(self) -> bool:
        """Return true only for the successful pre-execution plan state."""

        return self.status is RuntimeLifecycleState.PLAN_VALIDATED

    @property
    def blocked(self) -> bool:
        """Return true only for hard fail-closed validation failures."""

        return self.status is RuntimeEntryStatus.INPUTS_BLOCKED

    @property
    def inconclusive(self) -> bool:
        """Return true only when governance metadata is under-specified."""

        return self.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible validation result."""

        return {
            "status": self.status.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
            "plan": None if self.plan is None else self.plan.to_dict(),
        }


def validate_runtime_plan(**kwargs: Any) -> RuntimePlanValidationResult:
    """Validate a RuntimePlan and return a PLAN_VALIDATED outcome or fail closed."""

    try:
        plan = RuntimePlan(**kwargs)
    except RuntimeContractError as exc:
        status = (
            RuntimeEntryStatus.INPUTS_BLOCKED
            if any(
                reason.decision_state is RuntimeEntryStatus.INPUTS_BLOCKED for reason in exc.reasons
            )
            else RuntimeEntryStatus.INPUTS_INCONCLUSIVE
        )
        return RuntimePlanValidationResult(status=status, reasons=exc.reasons, plan=None)
    return RuntimePlanValidationResult(
        status=RuntimeLifecycleState.PLAN_VALIDATED,
        reasons=(
            _reason(
                code="runtime_plan_validated",
                message="RuntimePlan reached PLAN_VALIDATED without executing the job",
                field="runtime_plan",
                state=RuntimeEntryStatus.INPUTS_RESOLVED,
                expected="bounded pre-execution plan",
                actual="bounded pre-execution plan",
            ),
        ),
        plan=plan,
    )


def _coerce_runtime_request(
    value: RuntimeRequest,
    reasons: list[RuntimeEntryReason],
) -> RuntimeRequest | None:
    if not isinstance(value, RuntimeRequest):
        reasons.append(
            _reason(
                code="invalid_runtime_request",
                message="RuntimePlan requires a RuntimeRequest",
                field="runtime_request",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="RuntimeRequest",
                actual=type(value).__name__,
            )
        )
        return None
    return value


def _coerce_partition_scope(
    value: Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> tuple[str | None, str | None]:
    scope_json = _coerce_required_mapping(
        value,
        field="partition_scope",
        expected="campaign partition scope mapping",
        reasons=reasons,
    )
    if scope_json is None or value is None:
        return None, None

    partition_id = value.get("partition_id")
    if _is_missing(partition_id) or not isinstance(partition_id, str):
        reasons.append(
            _reason(
                code="missing_partition_id",
                message="RuntimePlan partition scope must declare a campaign partition id",
                field="partition_scope.partition_id",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=(
                    "development, validation, locked_test_candidate, or latest_shadow_candidate"
                ),
                actual=_actual(partition_id),
            )
        )
        return None, scope_json

    expected_window = CAMPAIGN_PARTITIONS.get(partition_id)
    if expected_window is None:
        reasons.append(
            _reason(
                code="unknown_campaign_partition",
                message="RuntimePlan partition scope must bind to campaign partitions",
                field="partition_scope.partition_id",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=",".join(CAMPAIGN_PARTITIONS),
                actual=partition_id,
            )
        )
        return partition_id, scope_json

    actual_start = value.get("start")
    actual_end = value.get("end")
    if actual_start != expected_window["start"] or actual_end != expected_window["end"]:
        reasons.append(
            _reason(
                code="partition_scope_not_campaign_bound",
                message="RuntimePlan partition dates must match the campaign partition contract",
                field="partition_scope",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=f"{partition_id} {expected_window['start']}..{expected_window['end']}",
                actual=f"{_actual(actual_start)}..{_actual(actual_end)}",
            )
        )
    return partition_id, scope_json


def _coerce_required_mapping(
    value: Mapping[str, Any] | None,
    *,
    field: str,
    expected: str,
    reasons: list[RuntimeEntryReason],
) -> str | None:
    if not isinstance(value, Mapping) or not value:
        reasons.append(
            _reason(
                code=f"missing_{field}",
                message=f"RuntimePlan requires {expected}",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=expected,
                actual=_actual(value),
            )
        )
        return None
    return _coerce_mapping(value, field=field, reasons=reasons)


def _coerce_mapping(
    value: Mapping[str, Any],
    *,
    field: str,
    reasons: list[RuntimeEntryReason],
) -> str | None:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except (TypeError, ValueError) as exc:
        reasons.append(
            _reason(
                code="invalid_metadata",
                message=f"{field} must be canonical JSON-compatible metadata",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="JSON-compatible mapping",
                actual=str(exc),
            )
        )
        return None


def _coerce_variant_budget(
    value: CombinationLimit | int | None,
    reasons: list[RuntimeEntryReason],
) -> CombinationLimit | None:
    if value is None:
        return None
    if isinstance(value, CombinationLimit):
        return value
    try:
        return CombinationLimit(value)
    except (TypeError, GridLimitError) as exc:
        reasons.append(
            _reason(
                code="invalid_variant_budget",
                message="RuntimePlan variant budget must be a finite CombinationLimit",
                field="variant_budget",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="positive finite CombinationLimit",
                actual=str(exc),
            )
        )
        return None


def _normalize_cost_stress_profiles(
    value: Sequence[str] | Mapping[str, Any],
    reasons: list[RuntimeEntryReason],
) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        profiles = tuple(
            sorted(str(profile).strip() for profile, enabled in value.items() if enabled)
        )
    elif isinstance(value, str) or not isinstance(value, Sequence):
        reasons.append(
            _reason(
                code="invalid_cost_stress_profiles",
                message="RuntimePlan cost stress profiles must be a finite sequence or mapping",
                field="cost_stress_profiles",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="sequence or mapping of profile names",
                actual=type(value).__name__,
            )
        )
        return ()
    else:
        profiles = tuple(str(profile).strip() for profile in value if str(profile).strip())
    return profiles


def _validate_probe_budget_and_cost_stress(
    *,
    variant_grid_ref: str | None,
    variant_budget: CombinationLimit | None,
    cost_stress_profiles: tuple[str, ...],
    reasons: list[RuntimeEntryReason],
) -> None:
    if _is_missing(variant_grid_ref):
        reasons.append(
            _reason(
                code="missing_variant_grid_ref",
                message="Signal probe plans must declare a bounded variant grid reference",
                field="variant_grid_ref",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="bounded variant grid reference",
                actual=_actual(variant_grid_ref),
            )
        )
    if variant_budget is None:
        reasons.append(
            _reason(
                code="missing_variant_budget",
                message="Signal probe plans must declare a finite variant budget",
                field="variant_budget",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="CombinationLimit",
                actual="missing",
            )
        )
    normalized_profiles = {_normalize_token(profile) for profile in cost_stress_profiles}
    if DOUBLE_COST_PROFILE not in normalized_profiles:
        reasons.append(
            _reason(
                code="missing_double_cost_stress",
                message="Signal probe plans must include a double_cost cost-stress profile",
                field="cost_stress_profiles",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=DOUBLE_COST_PROFILE,
                actual=",".join(cost_stress_profiles) if cost_stress_profiles else "missing",
            )
        )


def _require_scope_match(
    *,
    expected: Mapping[str, JsonValue],
    actual_json: str,
    field: str,
    code: str,
    message: str,
    reasons: list[RuntimeEntryReason],
) -> None:
    actual = _json_dict(actual_json, object_name=field)
    if dict(expected) != actual:
        reasons.append(
            _reason(
                code=code,
                message=message,
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=canonical_serialize(cast(JsonValue, dict(expected))),
                actual=canonical_serialize(cast(JsonValue, actual)),
            )
        )


def _validate_locked_partition_scope(
    *,
    partition_id: str,
    partition_scope: Mapping[str, Any],
    governance_metadata: Mapping[str, Any],
    governance_metadata_json: str | None,
    partition_purpose: str,
    reasons: list[RuntimeEntryReason],
) -> None:
    normalized_purpose = _normalize_token(partition_purpose)
    if partition_id in LOCKED_PARTITION_IDS and "selection" in normalized_purpose:
        reasons.append(
            _reason(
                code="locked_test_selection_forbidden",
                message="RuntimePlan must not express selection on locked-test data",
                field="partition_purpose",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="no locked-test selection",
                actual=partition_purpose,
            )
        )
    if _selection_on_locked_marker(partition_scope):
        reasons.append(
            _reason(
                code="locked_test_selection_forbidden",
                message="RuntimePlan partition scope must not request locked-test selection",
                field="partition_scope",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="no locked-test selection",
                actual=str(partition_scope),
            )
        )
    if partition_id in LOCKED_PARTITION_IDS and not _contains_contamination_metadata(
        governance_metadata
    ):
        reasons.append(
            _reason(
                code="locked_partition_governance_metadata_missing",
                message="Locked or shadow partition use requires contamination metadata",
                field="governance_metadata",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                expected="substantive governance contamination metadata",
                actual=governance_metadata_json or "missing",
            )
        )


def _runtime_plan_payload(
    *,
    request: RuntimeRequest,
    partition_scope_json: str,
    session_scope_json: str,
    include_signal_probe: bool,
    bounded: bool,
    variant_grid_ref: str | None,
    variant_budget: CombinationLimit | None,
    cost_stress_profiles: tuple[str, ...],
    governance_metadata_json: str,
    partition_purpose: str,
    plan_metadata_json: str,
) -> dict[str, JsonValue]:
    return {
        "schema": RUNTIME_PLAN_SCHEMA,
        "status": RuntimeLifecycleState.PLAN_VALIDATED.value,
        "request_content_hash": request.content_hash,
        "partition_scope": _json_dict(partition_scope_json, object_name="partition_scope"),
        "session_scope": _json_dict(session_scope_json, object_name="session_scope"),
        "include_signal_probe": include_signal_probe,
        "bounded": bounded,
        "variant_grid_ref": variant_grid_ref,
        "variant_budget": _variant_budget_payload(variant_budget),
        "cost_stress_profiles": list(cost_stress_profiles),
        "governance_metadata": _json_dict(
            governance_metadata_json,
            object_name="governance_metadata",
        ),
        "partition_purpose": partition_purpose,
        "plan_metadata": _json_dict(plan_metadata_json, object_name="plan_metadata"),
    }


def _variant_budget_payload(value: CombinationLimit | None) -> dict[str, JsonValue] | None:
    if value is None:
        return None
    return {
        "primitive": "alpha_system.experiments.limits.CombinationLimit",
        "max_combinations": value.max_combinations,
    }


def _contains_contamination_metadata(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if "contamination" in normalized_key and not _is_missing(item):
                return True
            if normalized_key == "governance_metadata" and not _is_missing(item):
                return True
            if _contains_contamination_metadata(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_contamination_metadata(item) for item in value)
    return False


def _selection_on_locked_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if "selection" in normalized_key and _contains_locked_partition_marker(item):
                return True
            if _selection_on_locked_marker(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_selection_on_locked_marker(item) for item in value)
    return False


def _contains_locked_partition_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = _normalize_token(value)
        return any(_normalize_token(partition) in normalized for partition in LOCKED_PARTITION_IDS)
    if isinstance(value, Mapping):
        return any(
            _contains_locked_partition_marker(key) or _contains_locked_partition_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_locked_partition_marker(item) for item in value)
    return False


def _normalize_token(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


__all__ = [
    "CAMPAIGN_PARTITIONS",
    "DOUBLE_COST_PROFILE",
    "RuntimePlan",
    "RuntimePlanValidationResult",
    "validate_runtime_plan",
]
