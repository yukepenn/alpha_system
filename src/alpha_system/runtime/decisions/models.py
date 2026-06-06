"""Runtime decision and stop-condition objects for visible terminal states."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState
from alpha_system.runtime.entry_contract import RuntimeEntryStatus

from .records import (
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecisionStage,
    normalize_rejection_reason,
)
from .states import (
    FORWARD_DECISION_STATES,
    RuntimeDecisionState,
    RuntimeDecisionStateError,
    TERMINAL_DECISION_STATES,
    coerce_runtime_decision_state,
)


@dataclass(frozen=True, slots=True, init=False)
class RuntimeDecision:
    """A fail-closed runtime decision with visible reasons for terminal states."""

    state: RuntimeDecisionState
    reasons: tuple[RejectionReasonRecord, ...]
    source_state: str | None

    def __init__(
        self,
        *,
        state: RuntimeDecisionState
        | RuntimeLifecycleState
        | StudyRunResultState
        | RuntimeEntryStatus
        | str,
        reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]] = (),
        source_state: str | None = None,
    ) -> None:
        normalized_state = coerce_runtime_decision_state(state)
        normalized_reasons = tuple(_coerce_reason(reason) for reason in reasons)
        if normalized_state in TERMINAL_DECISION_STATES and not normalized_reasons:
            raise RuntimeDecisionStateError(
                "terminal REJECTED/INCONCLUSIVE/BLOCKED decisions require visible reasons"
            )
        if normalized_state in FORWARD_DECISION_STATES and normalized_reasons:
            raise RuntimeDecisionStateError(
                "forward runtime decision states must not carry rejection reasons"
            )
        mismatched = [
            reason
            for reason in normalized_reasons
            if reason.decision_state is not normalized_state
        ]
        if mismatched:
            raise RuntimeDecisionStateError(
                "runtime decision reasons must map to the decision state"
            )

        object.__setattr__(self, "state", normalized_state)
        object.__setattr__(self, "reasons", normalized_reasons)
        object.__setattr__(
            self,
            "source_state",
            _source_state_value(state) if source_state is None else _required_text(source_state),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RuntimeDecision:
        """Build a decision from its stable value-free payload."""

        if not isinstance(value, Mapping):
            raise RuntimeDecisionStateError("runtime decision payload must be a mapping")
        _reject_extra_keys(value, allowed={"state", "source_state", "reasons"}, field="decision")
        raw_reasons = value.get("reasons", ())
        if isinstance(raw_reasons, str) or not isinstance(raw_reasons, Sequence):
            raise RuntimeDecisionStateError("decision reasons must be a sequence")
        return cls(
            state=value.get("state"),
            source_state=value.get("source_state"),
            reasons=tuple(
                RejectionReasonRecord.from_dict(reason)
                if isinstance(reason, Mapping)
                else reason
                for reason in raw_reasons
            ),
        )

    @classmethod
    def from_reasons(
        cls,
        reasons: Sequence[RejectionReasonRecord | Mapping[str, Any]],
    ) -> RuntimeDecision:
        """Build a terminal decision when all reasons map to the same state."""

        normalized = tuple(_coerce_reason(reason) for reason in reasons)
        if not normalized:
            raise RuntimeDecisionStateError("terminal decisions require visible reasons")
        states = {reason.decision_state for reason in normalized}
        if len(states) != 1:
            raise RuntimeDecisionStateError("reasons must map to exactly one terminal state")
        return cls(state=next(iter(states)), reasons=normalized)

    def to_dict(self) -> dict[str, object]:
        """Return a stable value-free decision payload."""

        payload: dict[str, object] = {
            "state": self.state.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
        }
        if self.source_state is not None:
            payload["source_state"] = self.source_state
        return payload


@dataclass(frozen=True, slots=True, init=False)
class RuntimeStopCondition:
    """Runtime decision marker for a run that cannot proceed.

    This object is unrelated to the Workflow 2 operator file
    ``runs/<run_id>/STOP`` and never creates or points to that file.
    """

    condition_id: str
    reason: RejectionReasonRecord

    def __init__(
        self,
        *,
        reason: RejectionReasonRecord | Mapping[str, Any],
        condition_id: str | None = None,
    ) -> None:
        normalized_reason = _coerce_reason(reason)
        if normalized_reason.decision_state is not RuntimeDecisionState.BLOCKED:
            raise RuntimeDecisionStateError("RuntimeStopCondition must map to BLOCKED")
        object.__setattr__(
            self,
            "condition_id",
            _required_text(condition_id) if condition_id is not None else _condition_id(reason),
        )
        object.__setattr__(self, "reason", normalized_reason)

    @classmethod
    def blocked_by_policy(
        cls,
        *,
        message: str,
        source_code: str = "runtime_stop_condition",
        source_id: str | None = None,
    ) -> RuntimeStopCondition:
        """Create a policy-blocked runtime stop condition with a visible reason."""

        return cls(
            reason=RejectionReasonRecord(
                code=RejectionReasonCode.BLOCKED_BY_POLICY,
                message=message,
                decision_state=RuntimeDecisionState.BLOCKED,
                stage=RuntimeDecisionStage.RUNTIME_STOP,
                source_code=source_code,
                source_id=source_id,
            )
        )

    @property
    def decision_state(self) -> RuntimeDecisionState:
        """Return the terminal decision state for this stop condition."""

        return RuntimeDecisionState.BLOCKED

    def to_decision(self) -> RuntimeDecision:
        """Return this stop condition as a terminal ``BLOCKED`` decision."""

        return RuntimeDecision(
            state=RuntimeDecisionState.BLOCKED,
            reasons=(self.reason,),
            source_state="RuntimeStopCondition",
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable value-free stop-condition payload."""

        return {
            "condition_id": self.condition_id,
            "condition_type": "runtime_decision_stop_condition",
            "decision_state": RuntimeDecisionState.BLOCKED.value,
            "reason": self.reason.to_dict(),
        }


def _coerce_reason(value: RejectionReasonRecord | Mapping[str, Any]) -> RejectionReasonRecord:
    if isinstance(value, RejectionReasonRecord):
        return value
    if isinstance(value, Mapping):
        return normalize_rejection_reason(value)
    raise RuntimeDecisionStateError(
        f"runtime decision reason must be a RejectionReasonRecord, got {type(value).__name__}"
    )


def _source_state_value(value: object) -> str | None:
    if isinstance(
        value,
        RuntimeDecisionState | RuntimeLifecycleState | StudyRunResultState | RuntimeEntryStatus,
    ):
        return value.value
    if isinstance(value, str):
        return value.strip().upper()
    return None


def _condition_id(reason: RejectionReasonRecord | Mapping[str, Any]) -> str:
    if not isinstance(reason, RejectionReasonRecord):
        reason = normalize_rejection_reason(reason)
    payload = json.dumps(reason.to_dict(), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"rstop_{digest[:24]}"


def _required_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeDecisionStateError("stable text value is required")
    return value.strip()


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise RuntimeDecisionStateError(
            f"{field} contains unsupported fields: {', '.join(sorted(extra))}"
        )


__all__ = [
    "RuntimeDecision",
    "RuntimeStopCondition",
]
