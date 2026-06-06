"""Immutable request and run-spec contracts for bounded research runtime jobs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, cast

from alpha_system.governance.alpha_spec import (
    IMPLEMENTATION_ALLOWED_STATE,
    AlphaSpec,
    validate_alpha_spec,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    content_hash,
    deserialize,
)
from alpha_system.governance.study_input_pack import (
    StudyInputPack,
    validate_study_input_pack,
    validate_study_input_pack_references,
)
from alpha_system.governance.study_spec import (
    DIAGNOSTICS_ALLOWED_STATE,
    StudySpec,
    validate_study_spec,
)
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.runtime.entry_contract import (
    ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES,
    RuntimeEntryReason,
    RuntimeEntryStatus,
)
from alpha_system.runtime.input_resolver import RuntimeInputPack

RUNTIME_REQUEST_SCHEMA = "alpha_system.runtime.request.v1"
STUDY_RUN_SPEC_SCHEMA = "alpha_system.runtime.study_run_spec.v1"
REQUEST_ID_PREFIX = "rreq"
STUDY_RUN_SPEC_ID_PREFIX = "srun"


class RuntimeLifecycleState(StrEnum):
    """Successful pre-execution lifecycle states for runtime contracts."""

    RUNTIME_REQUESTED = "RUNTIME_REQUESTED"
    INPUTS_RESOLVED = "INPUTS_RESOLVED"
    PLAN_VALIDATED = "PLAN_VALIDATED"


class RuntimeContractError(ValueError):
    """Fail-closed runtime contract error carrying rejection-shaped reasons."""

    def __init__(
        self,
        reasons: RuntimeEntryReason | Sequence[RuntimeEntryReason],
    ) -> None:
        if isinstance(reasons, RuntimeEntryReason):
            normalized = (reasons,)
        else:
            normalized = tuple(reasons)
        if not normalized:
            msg = "runtime contract error requires at least one reason"
            raise ValueError(msg)
        self.reasons = normalized
        super().__init__("; ".join(reason.message for reason in normalized))


class _RuntimePlanLike(Protocol):
    status: RuntimeLifecycleState
    request_content_hash: str
    content_hash: str

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible runtime plan payload."""


@dataclass(frozen=True, slots=True, init=False)
class RuntimeRequest:
    """Pre-execution request bound to governed specs and resolved inputs."""

    request_id: str
    alpha_spec_ref: str
    study_spec_ref: str
    study_input_pack: StudyInputPack
    target_dataset_version_id: str
    runtime_input_pack: RuntimeInputPack
    alpha_spec_state: str
    study_spec_state: str
    lifecycle_state: RuntimeLifecycleState
    alpha_spec_content_hash: str
    study_spec_content_hash: str
    runtime_input_pack_content_hash: str
    request_metadata_json: str
    content_hash: str

    def __init__(
        self,
        *,
        alpha_spec: AlphaSpec | Mapping[str, Any] | None,
        study_spec: StudySpec | Mapping[str, Any] | None,
        study_input_pack: StudyInputPack | Mapping[str, Any] | None,
        target_dataset_version_id: str | None,
        runtime_input_pack: RuntimeInputPack | None,
        alpha_spec_state: str = IMPLEMENTATION_ALLOWED_STATE,
        study_spec_state: str = DIAGNOSTICS_ALLOWED_STATE,
        request_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        reasons: list[RuntimeEntryReason] = []

        resolved_alpha_spec = _coerce_alpha_spec(alpha_spec, reasons)
        resolved_study_spec = _coerce_study_spec(study_spec, reasons)
        resolved_pack = _coerce_study_input_pack(study_input_pack, reasons)
        resolved_runtime_pack = _coerce_runtime_input_pack(runtime_input_pack, reasons)
        metadata_json = _canonical_json(request_metadata or {}, "request_metadata", reasons)

        _require_approved_state(
            alpha_spec_state,
            expected=IMPLEMENTATION_ALLOWED_STATE,
            field="alpha_spec_state",
            code="alpha_spec_not_approved",
            message="RuntimeRequest requires an approved AlphaSpec state",
            reasons=reasons,
        )
        _require_approved_state(
            study_spec_state,
            expected=DIAGNOSTICS_ALLOWED_STATE,
            field="study_spec_state",
            code="study_spec_not_approved",
            message="RuntimeRequest requires an approved StudySpec state",
            reasons=reasons,
        )

        if _is_missing(target_dataset_version_id):
            reasons.append(
                _reason(
                    code="missing_target_dataset_version_id",
                    message="RuntimeRequest requires a target accepted DatasetVersion reference",
                    field="target_dataset_version_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="dsv_ DatasetVersion id",
                    actual=_actual(target_dataset_version_id),
                )
            )
        elif not isinstance(
            target_dataset_version_id, str
        ) or not target_dataset_version_id.startswith("dsv_"):
            reasons.append(
                _reason(
                    code="invalid_dataset_version_reference",
                    message="RuntimeRequest target DatasetVersion must be a dsv_ reference",
                    field="target_dataset_version_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="dsv_ DatasetVersion id",
                    actual=_actual(target_dataset_version_id),
                )
            )

        if (
            resolved_pack is not None
            and resolved_alpha_spec is not None
            and resolved_study_spec is not None
        ):
            try:
                resolved_pack = validate_study_input_pack_references(
                    resolved_pack,
                    alpha_spec=resolved_alpha_spec,
                    study_spec=resolved_study_spec,
                )
            except GovernanceValidationError as exc:
                reasons.extend(
                    _governance_error_reasons(
                        exc,
                        field_prefix="study_input_pack",
                        message_prefix="StudyInputPack reference validation failed",
                    )
                )

        if (
            resolved_alpha_spec is not None
            and resolved_study_spec is not None
            and resolved_pack is not None
            and resolved_runtime_pack is not None
            and isinstance(target_dataset_version_id, str)
        ):
            reasons.extend(
                _runtime_input_pack_binding_reasons(
                    alpha_spec=resolved_alpha_spec,
                    study_spec=resolved_study_spec,
                    study_input_pack=resolved_pack,
                    target_dataset_version_id=target_dataset_version_id,
                    runtime_input_pack=resolved_runtime_pack,
                )
            )

        if reasons:
            raise RuntimeContractError(tuple(reasons))

        assert resolved_alpha_spec is not None
        assert resolved_study_spec is not None
        assert resolved_pack is not None
        assert resolved_runtime_pack is not None
        assert isinstance(target_dataset_version_id, str)
        assert metadata_json is not None

        alpha_hash = content_hash(cast(JsonValue, resolved_alpha_spec.to_dict()))
        study_hash = content_hash(cast(JsonValue, resolved_study_spec.to_dict()))
        input_pack_hash = _runtime_input_pack_hash(resolved_runtime_pack)
        payload = _runtime_request_payload(
            alpha_spec_ref=resolved_alpha_spec.alpha_spec_id,
            study_spec_ref=resolved_study_spec.study_spec_id,
            study_input_pack=resolved_pack,
            target_dataset_version_id=target_dataset_version_id,
            runtime_input_pack_hash=input_pack_hash,
            alpha_spec_state=alpha_spec_state,
            study_spec_state=study_spec_state,
            alpha_spec_hash=alpha_hash,
            study_spec_hash=study_hash,
            request_metadata_json=metadata_json,
        )
        request_hash = content_hash(cast(JsonValue, payload))

        object.__setattr__(self, "request_id", _prefixed_hash(REQUEST_ID_PREFIX, request_hash))
        object.__setattr__(self, "alpha_spec_ref", resolved_alpha_spec.alpha_spec_id)
        object.__setattr__(self, "study_spec_ref", resolved_study_spec.study_spec_id)
        object.__setattr__(self, "study_input_pack", resolved_pack)
        object.__setattr__(self, "target_dataset_version_id", target_dataset_version_id)
        object.__setattr__(self, "runtime_input_pack", resolved_runtime_pack)
        object.__setattr__(self, "alpha_spec_state", alpha_spec_state)
        object.__setattr__(self, "study_spec_state", study_spec_state)
        object.__setattr__(self, "lifecycle_state", RuntimeLifecycleState.RUNTIME_REQUESTED)
        object.__setattr__(self, "alpha_spec_content_hash", alpha_hash)
        object.__setattr__(self, "study_spec_content_hash", study_hash)
        object.__setattr__(self, "runtime_input_pack_content_hash", input_pack_hash)
        object.__setattr__(self, "request_metadata_json", metadata_json)
        object.__setattr__(self, "content_hash", request_hash)

    @property
    def request_metadata(self) -> dict[str, JsonValue]:
        """Return request metadata as a defensive JSON-compatible copy."""

        return _json_dict(self.request_metadata_json, object_name="RuntimeRequest.request_metadata")

    def to_dict(self) -> dict[str, object]:
        """Return a stable, value-free request payload."""

        return {
            "schema": RUNTIME_REQUEST_SCHEMA,
            "request_id": self.request_id,
            "lifecycle_state": self.lifecycle_state.value,
            "alpha_spec_ref": self.alpha_spec_ref,
            "study_spec_ref": self.study_spec_ref,
            "study_input_pack": self.study_input_pack.to_dict(),
            "target_dataset_version_id": self.target_dataset_version_id,
            "runtime_input_pack": self.runtime_input_pack.to_dict(),
            "alpha_spec_state": self.alpha_spec_state,
            "study_spec_state": self.study_spec_state,
            "alpha_spec_content_hash": self.alpha_spec_content_hash,
            "study_spec_content_hash": self.study_spec_content_hash,
            "runtime_input_pack_content_hash": self.runtime_input_pack_content_hash,
            "request_metadata": self.request_metadata,
            "content_hash": self.content_hash,
            "value_free": True,
        }


@dataclass(frozen=True, slots=True, init=False)
class StudyRunSpec:
    """Validated, pre-execution run specification for one bounded runtime plan."""

    study_run_spec_id: str
    runtime_request: RuntimeRequest
    runtime_plan: _RuntimePlanLike
    lifecycle_state: RuntimeLifecycleState
    run_metadata_json: str
    content_hash: str

    def __init__(
        self,
        *,
        runtime_request: RuntimeRequest,
        runtime_plan: _RuntimePlanLike,
        run_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        reasons: list[RuntimeEntryReason] = []
        if not isinstance(runtime_request, RuntimeRequest):
            reasons.append(
                _reason(
                    code="invalid_runtime_request",
                    message="StudyRunSpec requires a RuntimeRequest object",
                    field="runtime_request",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="RuntimeRequest",
                    actual=type(runtime_request).__name__,
                )
            )

        plan_status = getattr(runtime_plan, "status", None)
        if plan_status is not RuntimeLifecycleState.PLAN_VALIDATED:
            reasons.append(
                _reason(
                    code="runtime_plan_not_validated",
                    message="StudyRunSpec requires a RuntimePlan at PLAN_VALIDATED",
                    field="runtime_plan.status",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=RuntimeLifecycleState.PLAN_VALIDATED.value,
                    actual=_actual(plan_status),
                )
            )

        plan_request_hash = getattr(runtime_plan, "request_content_hash", None)
        request_hash = getattr(runtime_request, "content_hash", None)
        if plan_request_hash != request_hash:
            reasons.append(
                _reason(
                    code="runtime_plan_request_mismatch",
                    message="RuntimePlan must be bound to the supplied RuntimeRequest",
                    field="runtime_plan.request_content_hash",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=_actual(request_hash),
                    actual=_actual(plan_request_hash),
                )
            )

        plan_to_dict = getattr(runtime_plan, "to_dict", None)
        if not callable(plan_to_dict):
            reasons.append(
                _reason(
                    code="invalid_runtime_plan",
                    message="StudyRunSpec requires a RuntimePlan-compatible object",
                    field="runtime_plan",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="RuntimePlan with to_dict",
                    actual=type(runtime_plan).__name__,
                )
            )

        metadata_json = _canonical_json(run_metadata or {}, "run_metadata", reasons)
        if reasons:
            raise RuntimeContractError(tuple(reasons))

        assert isinstance(runtime_request, RuntimeRequest)
        assert metadata_json is not None
        plan_payload = plan_to_dict()
        payload = {
            "schema": STUDY_RUN_SPEC_SCHEMA,
            "runtime_request_content_hash": runtime_request.content_hash,
            "runtime_plan_content_hash": runtime_plan.content_hash,
            "run_metadata": _json_dict(metadata_json, object_name="StudyRunSpec.run_metadata"),
            "lifecycle_state": RuntimeLifecycleState.PLAN_VALIDATED.value,
        }
        spec_hash = content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "study_run_spec_id",
            _prefixed_hash(STUDY_RUN_SPEC_ID_PREFIX, spec_hash),
        )
        object.__setattr__(self, "runtime_request", runtime_request)
        object.__setattr__(self, "runtime_plan", runtime_plan)
        object.__setattr__(self, "lifecycle_state", RuntimeLifecycleState.PLAN_VALIDATED)
        object.__setattr__(self, "run_metadata_json", metadata_json)
        object.__setattr__(self, "content_hash", spec_hash)

        # Keep the plan payload construction above type-checked without storing a duplicate.
        _ = plan_payload

    @property
    def run_metadata(self) -> dict[str, JsonValue]:
        """Return run metadata as a defensive JSON-compatible copy."""

        return _json_dict(self.run_metadata_json, object_name="StudyRunSpec.run_metadata")

    def to_dict(self) -> dict[str, object]:
        """Return a stable pre-execution run-spec payload."""

        return {
            "schema": STUDY_RUN_SPEC_SCHEMA,
            "study_run_spec_id": self.study_run_spec_id,
            "lifecycle_state": self.lifecycle_state.value,
            "runtime_request": self.runtime_request.to_dict(),
            "runtime_plan": self.runtime_plan.to_dict(),
            "run_metadata": self.run_metadata,
            "content_hash": self.content_hash,
            "value_free": True,
            "execution_outcome": None,
        }


def _coerce_alpha_spec(
    value: AlphaSpec | Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> AlphaSpec | None:
    if value is None:
        reasons.append(
            _reason(
                code="missing_alpha_spec",
                message="RuntimeRequest requires an approved AlphaSpec",
                field="alpha_spec",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="AlphaSpec",
                actual="missing",
            )
        )
        return None
    try:
        return value if isinstance(value, AlphaSpec) else validate_alpha_spec(value)
    except GovernanceValidationError as exc:
        reasons.extend(
            _governance_error_reasons(
                exc,
                field_prefix="alpha_spec",
                message_prefix="AlphaSpec validation failed",
            )
        )
        return None


def _coerce_study_spec(
    value: StudySpec | Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> StudySpec | None:
    if value is None:
        reasons.append(
            _reason(
                code="missing_study_spec",
                message="RuntimeRequest requires an approved StudySpec",
                field="study_spec",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="StudySpec",
                actual="missing",
            )
        )
        return None
    try:
        return value if isinstance(value, StudySpec) else validate_study_spec(value)
    except GovernanceValidationError as exc:
        reasons.extend(
            _governance_error_reasons(
                exc,
                field_prefix="study_spec",
                message_prefix="StudySpec validation failed",
            )
        )
        return None


def _coerce_study_input_pack(
    value: StudyInputPack | Mapping[str, Any] | None,
    reasons: list[RuntimeEntryReason],
) -> StudyInputPack | None:
    if value is None:
        reasons.append(
            _reason(
                code="missing_study_input_pack",
                message="RuntimeRequest requires a governance StudyInputPack",
                field="study_input_pack",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="StudyInputPack",
                actual="missing",
            )
        )
        return None
    try:
        return value if isinstance(value, StudyInputPack) else validate_study_input_pack(value)
    except GovernanceValidationError as exc:
        reasons.extend(
            _governance_error_reasons(
                exc,
                field_prefix="study_input_pack",
                message_prefix="StudyInputPack validation failed",
            )
        )
        return None


def _coerce_runtime_input_pack(
    value: RuntimeInputPack | None,
    reasons: list[RuntimeEntryReason],
) -> RuntimeInputPack | None:
    if value is None:
        reasons.append(
            _reason(
                code="missing_runtime_input_pack",
                message="RuntimeRequest requires a resolved RuntimeInputPack",
                field="runtime_input_pack",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="RuntimeInputPack",
                actual="missing",
            )
        )
        return None
    if not isinstance(value, RuntimeInputPack):
        reasons.append(
            _reason(
                code="invalid_runtime_input_pack",
                message="RuntimeRequest requires a RuntimeInputPack from the input resolver",
                field="runtime_input_pack",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="RuntimeInputPack",
                actual=type(value).__name__,
            )
        )
        return None
    return value


def _runtime_input_pack_binding_reasons(
    *,
    alpha_spec: AlphaSpec,
    study_spec: StudySpec,
    study_input_pack: StudyInputPack,
    target_dataset_version_id: str,
    runtime_input_pack: RuntimeInputPack,
) -> tuple[RuntimeEntryReason, ...]:
    reasons: list[RuntimeEntryReason] = []
    if runtime_input_pack.alpha_spec_ref != alpha_spec.alpha_spec_id:
        reasons.append(
            _reason(
                code="runtime_input_alpha_spec_mismatch",
                message="RuntimeInputPack AlphaSpec reference must match the approved AlphaSpec",
                field="runtime_input_pack.alpha_spec_ref",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=alpha_spec.alpha_spec_id,
                actual=runtime_input_pack.alpha_spec_ref,
            )
        )

    if runtime_input_pack.study_spec_ref != study_spec.study_spec_id:
        reasons.append(
            _reason(
                code="runtime_input_study_spec_mismatch",
                message="RuntimeInputPack StudySpec reference must match the approved StudySpec",
                field="runtime_input_pack.study_spec_ref",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=study_spec.study_spec_id,
                actual=runtime_input_pack.study_spec_ref,
            )
        )

    if runtime_input_pack.dataset_version_id != target_dataset_version_id:
        reasons.append(
            _reason(
                code="runtime_input_dataset_version_mismatch",
                message="RuntimeInputPack DatasetVersion must match the RuntimeRequest target",
                field="runtime_input_pack.dataset_version_id",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=target_dataset_version_id,
                actual=runtime_input_pack.dataset_version_id,
            )
        )

    if runtime_input_pack.dataset_lifecycle_state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
        reasons.append(
            _reason(
                code="runtime_input_dataset_version_not_accepted",
                message="RuntimeInputPack must be bound to an accepted DatasetVersion",
                field="runtime_input_pack.dataset_lifecycle_state",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=",".join(sorted(ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES)),
                actual=runtime_input_pack.dataset_lifecycle_state,
            )
        )

    if runtime_input_pack.study_input_pack != study_input_pack.to_dict():
        reasons.append(
            _reason(
                code="runtime_input_study_input_pack_mismatch",
                message="RuntimeInputPack StudyInputPack payload must match the request",
                field="runtime_input_pack.study_input_pack",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=canonical_serialize(cast(JsonValue, study_input_pack.to_dict())),
                actual=canonical_serialize(cast(JsonValue, runtime_input_pack.study_input_pack)),
            )
        )

    if runtime_input_pack.dataset_scope != study_input_pack.dataset_scope:
        reasons.append(
            _reason(
                code="runtime_input_dataset_scope_mismatch",
                message="RuntimeInputPack dataset scope must match the StudyInputPack",
                field="runtime_input_pack.dataset_scope",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=canonical_serialize(cast(JsonValue, study_input_pack.dataset_scope)),
                actual=canonical_serialize(cast(JsonValue, runtime_input_pack.dataset_scope)),
            )
        )
    return tuple(reasons)


def _require_approved_state(
    value: str,
    *,
    expected: str,
    field: str,
    code: str,
    message: str,
    reasons: list[RuntimeEntryReason],
) -> None:
    if value != expected:
        reasons.append(
            _reason(
                code=code,
                message=message,
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=expected,
                actual=_actual(value),
            )
        )


def _runtime_request_payload(
    *,
    alpha_spec_ref: str,
    study_spec_ref: str,
    study_input_pack: StudyInputPack,
    target_dataset_version_id: str,
    runtime_input_pack_hash: str,
    alpha_spec_state: str,
    study_spec_state: str,
    alpha_spec_hash: str,
    study_spec_hash: str,
    request_metadata_json: str,
) -> dict[str, JsonValue]:
    return {
        "schema": RUNTIME_REQUEST_SCHEMA,
        "lifecycle_state": RuntimeLifecycleState.RUNTIME_REQUESTED.value,
        "alpha_spec_ref": alpha_spec_ref,
        "study_spec_ref": study_spec_ref,
        "study_input_pack": study_input_pack.to_dict(),
        "target_dataset_version_id": target_dataset_version_id,
        "runtime_input_pack_content_hash": runtime_input_pack_hash,
        "alpha_spec_state": alpha_spec_state,
        "study_spec_state": study_spec_state,
        "alpha_spec_content_hash": alpha_spec_hash,
        "study_spec_content_hash": study_spec_hash,
        "request_metadata": _json_dict(
            request_metadata_json,
            object_name="RuntimeRequest.request_metadata",
        ),
    }


def _runtime_input_pack_hash(runtime_input_pack: RuntimeInputPack) -> str:
    return content_hash(cast(JsonValue, runtime_input_pack.to_dict()))


def _governance_error_reasons(
    exc: GovernanceValidationError,
    *,
    field_prefix: str,
    message_prefix: str,
) -> tuple[RuntimeEntryReason, ...]:
    return tuple(
        _reason(
            code=issue.code,
            message=f"{message_prefix}: {issue.message}",
            field=f"{field_prefix}.{issue.field}",
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected=issue.expected,
            actual=issue.actual,
        )
        for issue in exc.issues
    )


def _canonical_json(
    value: Mapping[str, Any],
    field: str,
    reasons: list[RuntimeEntryReason],
) -> str | None:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except (TypeError, ValueError, GovernanceSerializationError) as exc:
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


def _json_dict(text: str, *, object_name: str) -> dict[str, JsonValue]:
    value = deserialize(text)
    if not isinstance(value, Mapping):
        raise RuntimeContractError(
            _reason(
                code="invalid_json_mapping",
                message=f"{object_name} must deserialize to a mapping",
                field=object_name,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="mapping",
                actual=type(value).__name__,
            )
        )
    return cast(dict[str, JsonValue], dict(value))


def _prefixed_hash(prefix: str, digest: str) -> str:
    return f"{prefix}_{digest[:24]}"


def _reason(
    *,
    code: str,
    message: str,
    field: str,
    state: RuntimeEntryStatus,
    expected: str,
    actual: str,
) -> RuntimeEntryReason:
    return RuntimeEntryReason(
        code=code,
        message=message,
        field=field,
        decision_state=state,
        expected=expected,
        actual=actual,
    )


def _actual(value: object) -> str:
    if value is None:
        return "missing"
    if isinstance(value, StrEnum):
        return value.value
    return str(value)


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


__all__ = [
    "RuntimeContractError",
    "RuntimeLifecycleState",
    "RuntimeRequest",
    "StudyRunSpec",
]
