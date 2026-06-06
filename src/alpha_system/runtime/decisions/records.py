"""Canonical rejection-reason records and upstream normalizers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditReason,
    NoLookaheadRejectionCategory,
)
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.entry_contract import RuntimeEntryReason, RuntimeEntryStatus
from alpha_system.runtime.grid.contracts import (
    BoundedGridOutcome,
    BoundedGridRunRecord,
    BoundedGridValidationResult,
)

from .states import (
    RuntimeDecisionState,
    RuntimeDecisionStateError,
    coerce_runtime_decision_state,
    is_prohibited_mvp_state_value,
)


class RejectionReasonRecordError(ValueError):
    """Raised when a rejection reason would be non-canonical or hidden."""


class RejectionReasonCode(StrEnum):
    """Closed RT-P15 rejection category set."""

    DATA_UNAVAILABLE = "data_unavailable"
    LEAKAGE_RISK = "leakage_risk"
    WEAK_DIAGNOSTICS = "weak_diagnostics"
    COST_FRAGILE = "cost_fragile"
    LOW_SAMPLE = "low_sample"
    VARIANT_BUDGET_EXCEEDED = "variant_budget_exceeded"
    DUPLICATE_EXPOSURE = "duplicate_exposure"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    INCONCLUSIVE = "inconclusive"


REJECTION_REASON_CODES: frozenset[str] = frozenset(code.value for code in RejectionReasonCode)


class RuntimeDecisionStage(StrEnum):
    """Known originating stages for canonical runtime rejection reasons."""

    INPUTS = "inputs"
    DIAGNOSTICS = "diagnostics"
    SIGNAL_PROBE = "signal_probe"
    COST_STRESS = "cost_stress"
    BOUNDED_GRID = "bounded_grid"
    NO_LOOKAHEAD_AUDIT = "no_lookahead_audit"
    RUNTIME_STOP = "runtime_stop"


@dataclass(frozen=True, slots=True, init=False)
class RejectionReasonRecord:
    """Immutable canonical rejection reason with no raw or heavy payload fields."""

    code: RejectionReasonCode
    message: str
    decision_state: RuntimeDecisionState
    stage: str
    source_code: str
    source_id: str | None

    def __init__(
        self,
        *,
        code: RejectionReasonCode | str,
        message: str,
        decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str,
        stage: RuntimeDecisionStage | str,
        source_code: str | None = None,
        source_id: str | None = None,
    ) -> None:
        normalized_code = _coerce_reason_code(code)
        normalized_state = coerce_runtime_decision_state(decision_state)
        if normalized_state not in {
            RuntimeDecisionState.REJECTED,
            RuntimeDecisionState.INCONCLUSIVE,
            RuntimeDecisionState.BLOCKED,
        }:
            raise RejectionReasonRecordError(
                "rejection reason records must map to REJECTED, INCONCLUSIVE, or BLOCKED"
            )

        object.__setattr__(self, "code", normalized_code)
        object.__setattr__(self, "message", _required_message(message))
        object.__setattr__(self, "decision_state", normalized_state)
        object.__setattr__(self, "stage", _coerce_stage(stage))
        object.__setattr__(
            self,
            "source_code",
            _required_token(source_code or normalized_code.value, field="source_code"),
        )
        object.__setattr__(
            self,
            "source_id",
            None if source_id is None else _required_token(source_id, field="source_id"),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RejectionReasonRecord:
        """Build a canonical reason from its stable payload."""

        if not isinstance(value, Mapping):
            raise RejectionReasonRecordError("reason payload must be a mapping")
        _reject_extra_keys(
            value,
            allowed={"code", "message", "decision_state", "stage", "source_code", "source_id"},
            field="reason",
        )
        return cls(
            code=value.get("code"),
            message=value.get("message"),
            decision_state=value.get("decision_state"),
            stage=value.get("stage"),
            source_code=value.get("source_code"),
            source_id=value.get("source_id"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a deterministic value-free reason payload."""

        payload = {
            "code": self.code.value,
            "message": self.message,
            "decision_state": self.decision_state.value,
            "stage": self.stage,
            "source_code": self.source_code,
        }
        if self.source_id is not None:
            payload["source_id"] = self.source_id
        return payload


def normalize_rejection_reason(
    reason: RejectionReasonRecord
    | RunRejectionReason
    | RuntimeEntryReason
    | NoLookaheadAuditReason
    | Mapping[str, Any],
    *,
    stage: RuntimeDecisionStage | str | None = None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None = None,
) -> RejectionReasonRecord:
    """Normalize one upstream reason into a canonical ``RejectionReasonRecord``."""

    if isinstance(reason, RejectionReasonRecord):
        return reason
    if isinstance(reason, NoLookaheadAuditReason):
        return _from_no_lookahead_reason(reason, stage=stage, decision_state=decision_state)
    if isinstance(reason, RuntimeEntryReason):
        return _from_runtime_entry_reason(reason, stage=stage, decision_state=decision_state)
    if isinstance(reason, RunRejectionReason):
        return _from_run_rejection_reason(reason, stage=stage, decision_state=decision_state)
    if isinstance(reason, Mapping):
        if {"decision_state", "stage"}.issubset(reason):
            return RejectionReasonRecord.from_dict(reason)
        return _from_runtime_entry_mapping(reason, stage=stage, decision_state=decision_state)
    raise RejectionReasonRecordError(
        f"unsupported rejection reason type: {type(reason).__name__}"
    )


def normalize_rejection_reasons(
    reasons: Sequence[
        RejectionReasonRecord | RunRejectionReason | RuntimeEntryReason | NoLookaheadAuditReason
    ],
    *,
    stage: RuntimeDecisionStage | str | None = None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None = None,
) -> tuple[RejectionReasonRecord, ...]:
    """Normalize a finite sequence of upstream rejection reasons."""

    if isinstance(reasons, str):
        raise RejectionReasonRecordError("reasons must be a finite sequence of reason objects")
    return tuple(
        normalize_rejection_reason(reason, stage=stage, decision_state=decision_state)
        for reason in reasons
    )


def normalize_bounded_grid_reasons(
    value: BoundedGridRunRecord | BoundedGridValidationResult,
) -> tuple[RejectionReasonRecord, ...]:
    """Normalize rejection reasons emitted by the bounded-grid guard surface."""

    record = value.record if isinstance(value, BoundedGridValidationResult) else value
    if not isinstance(record, BoundedGridRunRecord):
        raise RejectionReasonRecordError("bounded-grid normalizer requires a grid record/result")
    if record.guard_outcome is BoundedGridOutcome.GUARD_PASSED:
        if record.rejection_reasons:
            raise RejectionReasonRecordError("passed bounded-grid records must not carry reasons")
        return ()

    normalized: list[RejectionReasonRecord] = []
    for reason in record.rejection_reasons:
        state = (
            RuntimeDecisionState.INCONCLUSIVE
            if reason.decision_state is RuntimeEntryStatus.INPUTS_INCONCLUSIVE
            else RuntimeDecisionState.REJECTED
        )
        normalized.append(
            _from_runtime_entry_reason(
                reason,
                stage=RuntimeDecisionStage.BOUNDED_GRID,
                decision_state=state,
            )
        )
    return tuple(normalized)


def canonical_reason_code_from_source(
    source_code: str,
    *,
    message: str = "",
    stage: RuntimeDecisionStage | str | None = None,
    decision_state: RuntimeDecisionState | RuntimeEntryStatus | StudyRunResultState | str | None = None,
) -> RejectionReasonCode:
    """Map an upstream reason code to the closed RT-P15 category set."""

    state = None if decision_state is None else coerce_runtime_decision_state(decision_state)
    return _canonical_code_from_source(
        source_code=source_code,
        message=message,
        stage=None if stage is None else _coerce_stage(stage),
        decision_state=state,
        category=None,
    )


def _from_run_rejection_reason(
    reason: RunRejectionReason,
    *,
    stage: RuntimeDecisionStage | str | None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None,
) -> RejectionReasonRecord:
    if stage is None:
        raise RejectionReasonRecordError(
            "RunRejectionReason normalization requires the originating stage"
        )
    state = RuntimeDecisionState.REJECTED if decision_state is None else decision_state
    canonical = canonical_reason_code_from_source(
        reason.code,
        message=reason.message,
        stage=stage,
        decision_state=state,
    )
    return RejectionReasonRecord(
        code=canonical,
        message=reason.message,
        decision_state=state,
        stage=stage,
        source_code=reason.code,
    )


def _from_runtime_entry_reason(
    reason: RuntimeEntryReason,
    *,
    stage: RuntimeDecisionStage | str | None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None,
) -> RejectionReasonRecord:
    resolved_state = (
        coerce_runtime_decision_state(reason.decision_state)
        if decision_state is None
        else coerce_runtime_decision_state(decision_state)
    )
    if resolved_state is RuntimeDecisionState.INPUTS_RESOLVED:
        raise RejectionReasonRecordError("resolved entry reasons are not rejection records")
    resolved_stage = RuntimeDecisionStage.INPUTS if stage is None else stage
    canonical = canonical_reason_code_from_source(
        reason.code,
        message=reason.message,
        stage=resolved_stage,
        decision_state=resolved_state,
    )
    return RejectionReasonRecord(
        code=canonical,
        message=reason.message,
        decision_state=resolved_state,
        stage=resolved_stage,
        source_code=reason.code,
    )


def _from_no_lookahead_reason(
    reason: NoLookaheadAuditReason,
    *,
    stage: RuntimeDecisionStage | str | None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None,
) -> RejectionReasonRecord:
    category = reason.category
    if not isinstance(category, NoLookaheadRejectionCategory):
        category = NoLookaheadRejectionCategory(str(category))
    if decision_state is not None:
        resolved_state = coerce_runtime_decision_state(decision_state)
    elif category is NoLookaheadRejectionCategory.LEAKAGE_RISK:
        resolved_state = RuntimeDecisionState.REJECTED
    else:
        resolved_state = RuntimeDecisionState.BLOCKED
    resolved_stage = RuntimeDecisionStage.NO_LOOKAHEAD_AUDIT if stage is None else stage
    canonical = _canonical_code_from_source(
        source_code=reason.code,
        message=reason.message,
        stage=_coerce_stage(resolved_stage),
        decision_state=resolved_state,
        category=category.value,
    )
    return RejectionReasonRecord(
        code=canonical,
        message=reason.message,
        decision_state=resolved_state,
        stage=resolved_stage,
        source_code=reason.code,
    )


def _from_runtime_entry_mapping(
    value: Mapping[str, Any],
    *,
    stage: RuntimeDecisionStage | str | None,
    decision_state: RuntimeDecisionState | StudyRunResultState | RuntimeEntryStatus | str | None,
) -> RejectionReasonRecord:
    _reject_extra_keys(
        value,
        allowed={"code", "message", "field", "decision_state", "expected", "actual"},
        field="runtime_entry_reason",
    )
    entry_state = decision_state if decision_state is not None else value.get("decision_state")
    return _from_runtime_entry_reason(
        RuntimeEntryReason(
            code=value.get("code"),
            message=value.get("message"),
            field=value.get("field") or "unknown",
            decision_state=RuntimeEntryStatus(entry_state),
            expected=value.get("expected") or "not copied",
            actual=value.get("actual") or "not copied",
        ),
        stage=stage,
        decision_state=decision_state,
    )


def _canonical_code_from_source(
    *,
    source_code: str,
    message: str,
    stage: str | None,
    decision_state: RuntimeDecisionState | None,
    category: str | None,
) -> RejectionReasonCode:
    for candidate in (category, source_code):
        if candidate in REJECTION_REASON_CODES:
            return RejectionReasonCode(str(candidate))

    token = _normalize_token(source_code)
    text = f"{token} {_normalize_token(message)} {stage or ''}"
    if decision_state is RuntimeDecisionState.INCONCLUSIVE:
        return RejectionReasonCode.INCONCLUSIVE
    if "leak" in text or "lookahead" in text or "label_as_feature" in text:
        return RejectionReasonCode.LEAKAGE_RISK
    if "cost" in text or "slippage" in text or "fragile" in text or "double_cost" in text:
        return RejectionReasonCode.COST_FRAGILE
    if "low_sample" in text or "sample" in text or "sparse" in text or "coverage" in text:
        return RejectionReasonCode.LOW_SAMPLE
    if "variant" in text or "grid" in text or "unbounded" in text:
        return RejectionReasonCode.VARIANT_BUDGET_EXCEEDED
    if "duplicate" in text or "exposure" in text or "overlap" in text:
        return RejectionReasonCode.DUPLICATE_EXPOSURE
    if "policy" in text or "forbidden" in text or "raw_provider" in text or "external" in text:
        return RejectionReasonCode.BLOCKED_BY_POLICY
    if "missing" in text or "unavailable" in text or "dataset" in text or "input" in text:
        return RejectionReasonCode.DATA_UNAVAILABLE
    if decision_state is RuntimeDecisionState.BLOCKED:
        return RejectionReasonCode.BLOCKED_BY_POLICY
    return RejectionReasonCode.WEAK_DIAGNOSTICS


def _coerce_reason_code(value: RejectionReasonCode | str | object) -> RejectionReasonCode:
    if isinstance(value, RejectionReasonCode):
        return value
    if isinstance(value, str):
        try:
            return RejectionReasonCode(value.strip())
        except ValueError as exc:
            raise RejectionReasonRecordError(f"unsupported rejection reason code: {value}") from exc
    raise RejectionReasonRecordError("rejection reason code is required")


def _coerce_stage(value: RuntimeDecisionStage | str | object) -> str:
    if isinstance(value, RuntimeDecisionStage):
        return value.value
    if not isinstance(value, str) or not value.strip():
        raise RejectionReasonRecordError("rejection reason stage is required")
    stage = value.strip().casefold().replace("-", "_").replace(" ", "_")
    return _required_token(stage, field="stage")


def _required_message(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RejectionReasonRecordError("rejection reason message is required")
    message = value.strip()
    normalized = _normalize_token(message)
    for word in normalized.replace("_", " ").split():
        if is_prohibited_mvp_state_value(word):
            raise RejectionReasonRecordError(
                f"rejection reason message contains prohibited MVP state: {word}"
            )
    for prohibited in (
        "alpha_validated",
        "factor_promoted",
        "strategy_ready",
        "portfolio_ready",
        "live_ready",
        "paper_ready",
        "profitable",
        "tradable",
        "production_ready",
    ):
        if prohibited in normalized:
            raise RejectionReasonRecordError(
                f"rejection reason message contains promotional claim: {prohibited}"
            )
    return message


def _required_token(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RejectionReasonRecordError(f"{field} is required")
    token = value.strip()
    allowed = token.replace("_", "").replace("-", "").replace(".", "")
    if not allowed.isascii() or not allowed.isalnum():
        raise RejectionReasonRecordError(f"{field} must be a stable code/id token")
    return token


def _normalize_token(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise RejectionReasonRecordError(
            f"{field} contains unsupported fields: {', '.join(sorted(extra))}"
        )


__all__ = [
    "REJECTION_REASON_CODES",
    "RejectionReasonCode",
    "RejectionReasonRecord",
    "RejectionReasonRecordError",
    "RuntimeDecisionStage",
    "canonical_reason_code_from_source",
    "normalize_bounded_grid_reasons",
    "normalize_rejection_reason",
    "normalize_rejection_reasons",
]
