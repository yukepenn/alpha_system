"""Reference-only diagnostics run contracts for Research Runtime phases."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)
from alpha_system.runtime.contracts.plan import RuntimePlan
from alpha_system.runtime.contracts.run_record import (
    RunRejectionReason,
    StudyRunRecord,
    StudyRunResultState,
    StudyRunSpecRef,
)
from alpha_system.runtime.contracts.run_spec import StudyRunSpec

DIAGNOSTICS_RUN_SPEC_SCHEMA = "alpha_system.runtime.diagnostics.run_spec.v1"
DIAGNOSTICS_RUN_RECORD_SCHEMA = "alpha_system.runtime.diagnostics.run_record.v1"
DIAGNOSTICS_RUN_SPEC_ID_PREFIX = "dspec"
DIAGNOSTICS_RUN_RECORD_ID_PREFIX = "drecord"

DIAGNOSTICS_LIFECYCLE_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.DIAGNOSTICS_READY,
        StudyRunResultState.DIAGNOSTICS_RUNNING,
        StudyRunResultState.DIAGNOSTICS_COMPLETE,
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)
DIAGNOSTICS_FAILURE_STATES: frozenset[StudyRunResultState] = frozenset(
    {
        StudyRunResultState.DIAGNOSTICS_FAILED,
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }
)


class DiagnosticsContractError(ValueError):
    """Raised when a diagnostics contract would hide invalid or value-bearing state."""


class DiagnosticsFamily(StrEnum):
    """Diagnostics families specialized by RT-P07 through RT-P11."""

    FACTOR = "factor"
    LABEL = "label"
    SPLITS = "splits"
    CROSS_MARKET = "cross_market"
    COST = "cost"


class DiagnosticsHalfLifeProtocol(StrEnum):
    """Bounded walk-forward configuration profiles for diagnostics wiring.

    The protocol names are routing metadata only. They do not certify factor
    persistence, label independence, or statistical validity.
    """

    STRUCTURAL = "STRUCTURAL"
    MEDIUM = "MEDIUM"
    FAST = "FAST"


@dataclass(frozen=True, slots=True)
class RuntimePlanRef:
    """Reference to an RT-P04 RuntimePlan without copying the plan payload."""

    plan_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _required_string(self.plan_id, field="plan_id"))
        object.__setattr__(
            self,
            "content_hash",
            _required_string(self.content_hash, field="content_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable plan reference."""

        return {"plan_id": self.plan_id, "content_hash": self.content_hash}


@dataclass(frozen=True, slots=True)
class DiagnosticsRunSpecRef:
    """Reference to a diagnostics run spec without copying its payload."""

    diagnostics_run_spec_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "diagnostics_run_spec_id",
            _required_string(
                self.diagnostics_run_spec_id,
                field="diagnostics_run_spec_id",
            ),
        )
        object.__setattr__(
            self,
            "content_hash",
            _required_string(self.content_hash, field="content_hash"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable diagnostics run-spec reference."""

        return {
            "diagnostics_run_spec_id": self.diagnostics_run_spec_id,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class StudyRunRecordRef:
    """Reference to an RT-P05 StudyRunRecord without copying outcome payloads."""

    record_id: str
    run_id: str
    record_hash: str
    result_state: StudyRunResultState

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _required_string(self.record_id, field="record_id"))
        object.__setattr__(self, "run_id", _required_string(self.run_id, field="run_id"))
        object.__setattr__(
            self,
            "record_hash",
            _required_string(self.record_hash, field="record_hash"),
        )
        object.__setattr__(
            self,
            "result_state",
            _coerce_study_run_result_state(self.result_state),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable study-run record reference."""

        return {
            "record_id": self.record_id,
            "run_id": self.run_id,
            "record_hash": self.record_hash,
            "result_state": self.result_state.value,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsReportRef:
    """Reference to a value-free diagnostics report."""

    report_id: str
    report_hash: str
    report_kind: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", _required_string(self.report_id, field="report_id"))
        object.__setattr__(
            self,
            "report_hash",
            _required_string(self.report_hash, field="report_hash"),
        )
        object.__setattr__(
            self,
            "report_kind",
            _required_string(self.report_kind, field="report_kind"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable diagnostics report reference."""

        return {
            "report_id": self.report_id,
            "report_hash": self.report_hash,
            "report_kind": self.report_kind,
        }


@dataclass(frozen=True, slots=True, init=False)
class DiagnosticsRunSpec:
    """Pre-execution diagnostics contract bound to an RT-P04 StudyRunSpec."""

    diagnostics_run_spec_id: str
    diagnostics_family: DiagnosticsFamily
    study_run_spec_ref: StudyRunSpecRef
    runtime_plan_ref: RuntimePlanRef
    requested_state: StudyRunResultState
    spec_metadata_json: str
    content_hash: str

    def __init__(
        self,
        *,
        diagnostics_family: DiagnosticsFamily | str,
        study_run_spec: StudyRunSpec | StudyRunSpecRef | Mapping[str, Any],
        runtime_plan: RuntimePlan | RuntimePlanRef | Mapping[str, Any] | None = None,
        spec_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        family = _coerce_diagnostics_family(diagnostics_family)
        spec_ref = _coerce_study_run_spec_ref(study_run_spec)
        plan_ref = _resolve_runtime_plan_ref(study_run_spec, runtime_plan)
        metadata_json = _canonical_mapping(spec_metadata or {}, field="spec_metadata")

        payload = {
            "schema": DIAGNOSTICS_RUN_SPEC_SCHEMA,
            "diagnostics_family": family.value,
            "study_run_spec_ref": spec_ref.to_dict(),
            "runtime_plan_ref": plan_ref.to_dict(),
            "requested_state": StudyRunResultState.DIAGNOSTICS_READY.value,
            "spec_metadata": _json_dict(metadata_json, field="spec_metadata"),
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "diagnostics_run_spec_id",
            f"{DIAGNOSTICS_RUN_SPEC_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "diagnostics_family", family)
        object.__setattr__(self, "study_run_spec_ref", spec_ref)
        object.__setattr__(self, "runtime_plan_ref", plan_ref)
        object.__setattr__(self, "requested_state", StudyRunResultState.DIAGNOSTICS_READY)
        object.__setattr__(self, "spec_metadata_json", metadata_json)
        object.__setattr__(self, "content_hash", digest)

    @property
    def spec_metadata(self) -> dict[str, JsonValue]:
        """Return diagnostics spec metadata as a defensive JSON-compatible copy."""

        return _json_dict(self.spec_metadata_json, field="spec_metadata")

    def to_ref(self) -> DiagnosticsRunSpecRef:
        """Return the reference used by diagnostics run records and reports."""

        return DiagnosticsRunSpecRef(
            diagnostics_run_spec_id=self.diagnostics_run_spec_id,
            content_hash=self.content_hash,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable diagnostics run spec with no execution values."""

        return {
            "schema": DIAGNOSTICS_RUN_SPEC_SCHEMA,
            "diagnostics_run_spec_id": self.diagnostics_run_spec_id,
            "diagnostics_family": self.diagnostics_family.value,
            "study_run_spec_ref": self.study_run_spec_ref.to_dict(),
            "runtime_plan_ref": self.runtime_plan_ref.to_dict(),
            "requested_state": self.requested_state.value,
            "spec_metadata": self.spec_metadata,
            "content_hash": self.content_hash,
            "value_free": True,
            "execution_outcome": None,
        }


@dataclass(frozen=True, slots=True, init=False)
class DiagnosticsRunRecord:
    """Visible diagnostics lifecycle record bound to RT-P05 rejection reasons."""

    diagnostics_run_record_id: str
    diagnostics_run_spec_ref: DiagnosticsRunSpecRef
    status: StudyRunResultState
    study_run_record_ref: StudyRunRecordRef | None
    report_ref: DiagnosticsReportRef | None
    rejection_reasons: tuple[RunRejectionReason, ...]
    record_hash: str

    def __init__(
        self,
        *,
        diagnostics_run_spec_ref: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
        status: StudyRunResultState | str,
        study_run_record_ref: StudyRunRecord | StudyRunRecordRef | Mapping[str, Any] | None = None,
        report_ref: DiagnosticsReportRef | Mapping[str, Any] | None = None,
        rejection_reasons: Sequence[RunRejectionReason | Mapping[str, Any]] = (),
    ) -> None:
        spec_ref = _coerce_diagnostics_run_spec_ref(diagnostics_run_spec_ref)
        normalized_status = _coerce_diagnostics_status(status)
        normalized_study_record_ref = _coerce_optional_study_run_record_ref(study_run_record_ref)
        normalized_report_ref = _coerce_optional_report_ref(report_ref)
        normalized_reasons = tuple(_coerce_rejection_reason(reason) for reason in rejection_reasons)

        if normalized_status is StudyRunResultState.DIAGNOSTICS_COMPLETE and (
            normalized_report_ref is None
        ):
            raise DiagnosticsContractError("DIAGNOSTICS_COMPLETE requires a diagnostics report ref")
        if normalized_status in DIAGNOSTICS_FAILURE_STATES and not normalized_reasons:
            raise DiagnosticsContractError(
                "failed, rejected, inconclusive, and blocked diagnostics records "
                "require at least one visible rejection reason"
            )

        payload = {
            "schema": DIAGNOSTICS_RUN_RECORD_SCHEMA,
            "diagnostics_run_spec_ref": spec_ref.to_dict(),
            "status": normalized_status.value,
            "study_run_record_ref": (
                None
                if normalized_study_record_ref is None
                else normalized_study_record_ref.to_dict()
            ),
            "report_ref": None
            if normalized_report_ref is None
            else normalized_report_ref.to_dict(),
            "rejection_reason_records": [reason.to_dict() for reason in normalized_reasons],
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "diagnostics_run_record_id",
            f"{DIAGNOSTICS_RUN_RECORD_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "diagnostics_run_spec_ref", spec_ref)
        object.__setattr__(self, "status", normalized_status)
        object.__setattr__(self, "study_run_record_ref", normalized_study_record_ref)
        object.__setattr__(self, "report_ref", normalized_report_ref)
        object.__setattr__(self, "rejection_reasons", normalized_reasons)
        object.__setattr__(self, "record_hash", digest)

    def to_dict(self) -> dict[str, object]:
        """Return a stable, value-free diagnostics run record."""

        return {
            "schema": DIAGNOSTICS_RUN_RECORD_SCHEMA,
            "diagnostics_run_record_id": self.diagnostics_run_record_id,
            "diagnostics_run_spec_ref": self.diagnostics_run_spec_ref.to_dict(),
            "status": self.status.value,
            "study_run_record_ref": (
                None if self.study_run_record_ref is None else self.study_run_record_ref.to_dict()
            ),
            "report_ref": None if self.report_ref is None else self.report_ref.to_dict(),
            "rejection_reason_records": [reason.to_dict() for reason in self.rejection_reasons],
            "record_hash": self.record_hash,
            "value_free": True,
        }


def _resolve_runtime_plan_ref(
    study_run_spec: StudyRunSpec | StudyRunSpecRef | Mapping[str, Any],
    runtime_plan: RuntimePlan | RuntimePlanRef | Mapping[str, Any] | None,
) -> RuntimePlanRef:
    if runtime_plan is None:
        if not isinstance(study_run_spec, StudyRunSpec):
            raise DiagnosticsContractError(
                "runtime_plan is required when study_run_spec is supplied as a reference"
            )
        return _coerce_runtime_plan_ref(study_run_spec.runtime_plan)

    plan_ref = _coerce_runtime_plan_ref(runtime_plan)
    if isinstance(study_run_spec, StudyRunSpec):
        expected_hash = study_run_spec.runtime_plan.content_hash
        if plan_ref.content_hash != expected_hash:
            raise DiagnosticsContractError(
                "runtime_plan_ref must match the StudyRunSpec runtime_plan content hash"
            )
    return plan_ref


def _coerce_diagnostics_family(value: DiagnosticsFamily | str) -> DiagnosticsFamily:
    if isinstance(value, DiagnosticsFamily):
        return value
    if isinstance(value, str):
        try:
            return DiagnosticsFamily(value)
        except ValueError as exc:
            raise DiagnosticsContractError(f"unsupported diagnostics family: {value}") from exc
    raise DiagnosticsContractError(
        f"diagnostics_family must be DiagnosticsFamily or str, got {type(value).__name__}"
    )


def _coerce_diagnostics_status(value: StudyRunResultState | str) -> StudyRunResultState:
    state = _coerce_study_run_result_state(value)
    if state not in DIAGNOSTICS_LIFECYCLE_STATES:
        allowed = ", ".join(sorted(state.value for state in DIAGNOSTICS_LIFECYCLE_STATES))
        raise DiagnosticsContractError(f"diagnostics status must be one of: {allowed}")
    return state


def _coerce_study_run_result_state(value: StudyRunResultState | str) -> StudyRunResultState:
    if isinstance(value, StudyRunResultState):
        return value
    if isinstance(value, str):
        try:
            return StudyRunResultState(value)
        except ValueError as exc:
            raise DiagnosticsContractError(f"unsupported runtime result state: {value}") from exc
    raise DiagnosticsContractError(
        f"runtime result state must be StudyRunResultState or str, got {type(value).__name__}"
    )


def _coerce_study_run_spec_ref(
    value: StudyRunSpec | StudyRunSpecRef | Mapping[str, Any],
) -> StudyRunSpecRef:
    if isinstance(value, StudyRunSpecRef):
        return value
    if isinstance(value, StudyRunSpec):
        return StudyRunSpecRef(
            study_run_spec_id=value.study_run_spec_id,
            content_hash=value.content_hash,
        )
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            f"study_run_spec must be StudyRunSpec or reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"study_run_spec_id", "content_hash"},
        field="study_run_spec",
    )
    return StudyRunSpecRef(
        study_run_spec_id=value.get("study_run_spec_id"),
        content_hash=value.get("content_hash"),
    )


def _coerce_runtime_plan_ref(
    value: RuntimePlan | RuntimePlanRef | Mapping[str, Any],
) -> RuntimePlanRef:
    if isinstance(value, RuntimePlanRef):
        return value
    if isinstance(value, RuntimePlan):
        return RuntimePlanRef(plan_id=value.plan_id, content_hash=value.content_hash)
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            f"runtime_plan must be RuntimePlan or reference mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(value, allowed={"plan_id", "content_hash"}, field="runtime_plan")
    return RuntimePlanRef(plan_id=value.get("plan_id"), content_hash=value.get("content_hash"))


def _coerce_diagnostics_run_spec_ref(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(value, DiagnosticsRunSpecRef):
        return value
    if isinstance(value, DiagnosticsRunSpec):
        return value.to_ref()
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            "diagnostics_run_spec_ref must be DiagnosticsRunSpec or reference mapping, "
            f"got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"diagnostics_run_spec_id", "content_hash"},
        field="diagnostics_run_spec_ref",
    )
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id=value.get("diagnostics_run_spec_id"),
        content_hash=value.get("content_hash"),
    )


def _coerce_optional_study_run_record_ref(
    value: StudyRunRecord | StudyRunRecordRef | Mapping[str, Any] | None,
) -> StudyRunRecordRef | None:
    if value is None:
        return None
    if isinstance(value, StudyRunRecordRef):
        return value
    if isinstance(value, StudyRunRecord):
        return StudyRunRecordRef(
            record_id=value.record_id,
            run_id=value.run_id,
            record_hash=value.record_hash,
            result_state=value.result_state,
        )
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            "study_run_record_ref must be StudyRunRecord or reference mapping, "
            f"got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"record_id", "run_id", "record_hash", "result_state"},
        field="study_run_record_ref",
    )
    return StudyRunRecordRef(
        record_id=value.get("record_id"),
        run_id=value.get("run_id"),
        record_hash=value.get("record_hash"),
        result_state=value.get("result_state"),
    )


def _coerce_optional_report_ref(
    value: DiagnosticsReportRef | Mapping[str, Any] | None,
) -> DiagnosticsReportRef | None:
    if value is None:
        return None
    if isinstance(value, DiagnosticsReportRef):
        return value
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            f"report_ref must be DiagnosticsReportRef or mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(
        value,
        allowed={"report_id", "report_hash", "report_kind"},
        field="report_ref",
    )
    return DiagnosticsReportRef(
        report_id=value.get("report_id"),
        report_hash=value.get("report_hash"),
        report_kind=value.get("report_kind"),
    )


def _coerce_rejection_reason(value: RunRejectionReason | Mapping[str, Any]) -> RunRejectionReason:
    if isinstance(value, RunRejectionReason):
        return value
    if not isinstance(value, Mapping):
        raise DiagnosticsContractError(
            f"rejection reason must be RunRejectionReason or mapping, got {type(value).__name__}"
        )
    _reject_extra_keys(value, allowed={"code", "message"}, field="rejection_reasons")
    return RunRejectionReason(code=value.get("code"), message=value.get("message"))


def _canonical_mapping(value: Mapping[str, Any], *, field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise DiagnosticsContractError(f"{field} must be JSON-compatible: {exc}") from exc


def _json_dict(text: str, *, field: str) -> dict[str, JsonValue]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise DiagnosticsContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DiagnosticsContractError(f"{field} must serialize to a mapping")
    return dict(value)


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise DiagnosticsContractError(
            f"{field} contains non-reference fields: {', '.join(sorted(extra))}"
        )


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagnosticsContractError(f"{field} is required")
    return value.strip()


__all__ = [
    "DIAGNOSTICS_FAILURE_STATES",
    "DIAGNOSTICS_LIFECYCLE_STATES",
    "DIAGNOSTICS_RUN_RECORD_SCHEMA",
    "DIAGNOSTICS_RUN_SPEC_SCHEMA",
    "DiagnosticsContractError",
    "DiagnosticsFamily",
    "DiagnosticsReportRef",
    "DiagnosticsRunRecord",
    "DiagnosticsRunSpec",
    "DiagnosticsRunSpecRef",
    "RuntimePlanRef",
    "StudyRunRecordRef",
]
