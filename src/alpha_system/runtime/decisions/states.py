"""Fail-closed runtime decision states for visible run outcomes."""

from __future__ import annotations

from enum import StrEnum

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState
from alpha_system.runtime.entry_contract import RuntimeEntryStatus


class RuntimeDecisionStateError(ValueError):
    """Raised when a runtime decision state would hide or promote an outcome."""


class RuntimeDecisionState(StrEnum):
    """Closed runtime decision-state surface for RT-P15.

    The enum intentionally omits promotional MVP states and hides
    ``DIAGNOSTICS_FAILED`` behind the terminal ``REJECTED`` decision.
    """

    RUNTIME_REQUESTED = RuntimeLifecycleState.RUNTIME_REQUESTED.value
    INPUTS_RESOLVED = RuntimeLifecycleState.INPUTS_RESOLVED.value
    PLAN_VALIDATED = RuntimeLifecycleState.PLAN_VALIDATED.value
    DIAGNOSTICS_READY = StudyRunResultState.DIAGNOSTICS_READY.value
    DIAGNOSTICS_RUNNING = StudyRunResultState.DIAGNOSTICS_RUNNING.value
    DIAGNOSTICS_COMPLETE = StudyRunResultState.DIAGNOSTICS_COMPLETE.value
    SIGNAL_PROBE_READY = StudyRunResultState.SIGNAL_PROBE_READY.value
    SIGNAL_PROBE_COMPLETE = StudyRunResultState.SIGNAL_PROBE_COMPLETE.value
    COST_STRESS_COMPLETE = StudyRunResultState.COST_STRESS_COMPLETE.value
    EVIDENCE_DRAFT_READY = StudyRunResultState.EVIDENCE_DRAFT_READY.value
    REFERENCE_HANDOFF_READY = StudyRunResultState.REFERENCE_HANDOFF_READY.value
    REJECTED = StudyRunResultState.REJECTED.value
    INCONCLUSIVE = StudyRunResultState.INCONCLUSIVE.value
    BLOCKED = StudyRunResultState.BLOCKED.value


TERMINAL_DECISION_STATES: frozenset[RuntimeDecisionState] = frozenset(
    {
        RuntimeDecisionState.REJECTED,
        RuntimeDecisionState.INCONCLUSIVE,
        RuntimeDecisionState.BLOCKED,
    }
)
FORWARD_DECISION_STATES: frozenset[RuntimeDecisionState] = frozenset(
    state for state in RuntimeDecisionState if state not in TERMINAL_DECISION_STATES
)

_PROHIBITED_MVP_STATE_VALUES: frozenset[str] = frozenset(
    {
        "ALPHA_VALIDATED",
        "FACTOR_PROMOTED",
        "STRATEGY_READY",
        "PORTFOLIO_READY",
        "LIVE_READY",
        "PAPER_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
    }
)


def coerce_runtime_decision_state(
    value: RuntimeDecisionState | RuntimeLifecycleState | StudyRunResultState | RuntimeEntryStatus | str,
) -> RuntimeDecisionState:
    """Normalize upstream lifecycle/result states into the RT-P15 decision surface."""

    if isinstance(value, RuntimeDecisionState):
        return value
    if isinstance(value, RuntimeLifecycleState):
        return decision_state_from_runtime_lifecycle_state(value)
    if isinstance(value, StudyRunResultState):
        return decision_state_from_study_run_result_state(value)
    if isinstance(value, RuntimeEntryStatus):
        return decision_state_from_runtime_entry_status(value)
    if isinstance(value, str):
        return _coerce_string_decision_state(value)
    raise RuntimeDecisionStateError(
        f"unsupported runtime decision state type: {type(value).__name__}"
    )


def decision_state_from_runtime_lifecycle_state(
    value: RuntimeLifecycleState | str,
) -> RuntimeDecisionState:
    """Map successful runtime lifecycle states to forward decision states."""

    lifecycle = value if isinstance(value, RuntimeLifecycleState) else RuntimeLifecycleState(value)
    return RuntimeDecisionState(lifecycle.value)


def decision_state_from_runtime_entry_status(
    value: RuntimeEntryStatus | str,
) -> RuntimeDecisionState:
    """Map entry-contract states into the runtime decision surface."""

    status = value if isinstance(value, RuntimeEntryStatus) else RuntimeEntryStatus(value)
    if status is RuntimeEntryStatus.INPUTS_RESOLVED:
        return RuntimeDecisionState.INPUTS_RESOLVED
    if status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE:
        return RuntimeDecisionState.INCONCLUSIVE
    return RuntimeDecisionState.BLOCKED


def decision_state_from_study_run_result_state(
    value: StudyRunResultState | str,
) -> RuntimeDecisionState:
    """Map study-run result states into terminal or forward runtime decisions."""

    result_state = value if isinstance(value, StudyRunResultState) else StudyRunResultState(value)
    if result_state is StudyRunResultState.DIAGNOSTICS_FAILED:
        return RuntimeDecisionState.REJECTED
    if result_state in {
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    }:
        return RuntimeDecisionState(result_state.value)
    return RuntimeDecisionState(result_state.value)


def is_terminal_decision_state(value: RuntimeDecisionState | str) -> bool:
    """Return true only for terminal non-success decision states."""

    return coerce_runtime_decision_state(value) in TERMINAL_DECISION_STATES


def is_forward_decision_state(value: RuntimeDecisionState | str) -> bool:
    """Return true only for forward/success lifecycle decision states."""

    return coerce_runtime_decision_state(value) in FORWARD_DECISION_STATES


def is_prohibited_mvp_state_value(value: object) -> bool:
    """Return true for MVP states that the runtime decision surface must reject."""

    return _normalize_state_text(value) in _PROHIBITED_MVP_STATE_VALUES


def _coerce_string_decision_state(value: str) -> RuntimeDecisionState:
    text = _normalize_state_text(value)
    if text in _PROHIBITED_MVP_STATE_VALUES:
        raise RuntimeDecisionStateError(f"prohibited MVP state is not reachable: {text}")

    for enum_type, mapper in (
        (RuntimeDecisionState, lambda item: item),
        (RuntimeEntryStatus, decision_state_from_runtime_entry_status),
        (RuntimeLifecycleState, decision_state_from_runtime_lifecycle_state),
        (StudyRunResultState, decision_state_from_study_run_result_state),
    ):
        try:
            return mapper(enum_type(text))
        except ValueError:
            continue
    raise RuntimeDecisionStateError(f"unsupported runtime decision state: {text}")


def _normalize_state_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeDecisionStateError("runtime decision state is required")
    return value.strip().upper()


__all__ = [
    "FORWARD_DECISION_STATES",
    "TERMINAL_DECISION_STATES",
    "RuntimeDecisionState",
    "RuntimeDecisionStateError",
    "coerce_runtime_decision_state",
    "decision_state_from_runtime_entry_status",
    "decision_state_from_runtime_lifecycle_state",
    "decision_state_from_study_run_result_state",
    "is_forward_decision_state",
    "is_prohibited_mvp_state_value",
    "is_terminal_decision_state",
]
