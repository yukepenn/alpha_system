"""Canonical runtime decision states and rejection-reason records."""

from alpha_system.runtime.decisions.models import RuntimeDecision, RuntimeStopCondition
from alpha_system.runtime.decisions.records import (
    REJECTION_REASON_CODES,
    RejectionReasonCode,
    RejectionReasonRecord,
    RejectionReasonRecordError,
    RuntimeDecisionStage,
    canonical_reason_code_from_source,
    normalize_bounded_grid_reasons,
    normalize_rejection_reason,
    normalize_rejection_reasons,
)
from alpha_system.runtime.decisions.states import (
    FORWARD_DECISION_STATES,
    TERMINAL_DECISION_STATES,
    RuntimeDecisionState,
    RuntimeDecisionStateError,
    coerce_runtime_decision_state,
    decision_state_from_runtime_entry_status,
    decision_state_from_runtime_lifecycle_state,
    decision_state_from_study_run_result_state,
    is_forward_decision_state,
    is_prohibited_mvp_state_value,
    is_terminal_decision_state,
)

__all__ = [
    "FORWARD_DECISION_STATES",
    "REJECTION_REASON_CODES",
    "TERMINAL_DECISION_STATES",
    "RejectionReasonCode",
    "RejectionReasonRecord",
    "RejectionReasonRecordError",
    "RuntimeDecision",
    "RuntimeDecisionStage",
    "RuntimeDecisionState",
    "RuntimeDecisionStateError",
    "RuntimeStopCondition",
    "canonical_reason_code_from_source",
    "coerce_runtime_decision_state",
    "decision_state_from_runtime_entry_status",
    "decision_state_from_runtime_lifecycle_state",
    "decision_state_from_study_run_result_state",
    "is_forward_decision_state",
    "is_prohibited_mvp_state_value",
    "is_terminal_decision_state",
    "normalize_bounded_grid_reasons",
    "normalize_rejection_reason",
    "normalize_rejection_reasons",
]
