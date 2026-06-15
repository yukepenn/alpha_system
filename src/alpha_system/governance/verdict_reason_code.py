"""Machine-readable reason codes for inconclusive governance verdicts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from alpha_system.governance.validation import GovernanceValidationError, ValidationIssue


class VerdictReasonCode(StrEnum):
    """Closed reason-code taxonomy for non-final or blocked verdict evidence."""

    UNDERPOWERED = "UNDERPOWERED"
    SUBSTRATE_GAP = "SUBSTRATE_GAP"
    COST_FRAGILE = "COST_FRAGILE"
    DATA_QUALITY = "DATA_QUALITY"
    LEAKAGE_BLOCKED = "LEAKAGE_BLOCKED"
    DUPLICATE_EXPOSURE = "DUPLICATE_EXPOSURE"
    REGIME_UNSTABLE = "REGIME_UNSTABLE"
    BBO_PROXY_LIMITATION = "BBO_PROXY_LIMITATION"
    # main_effect autonomous evidence triage (non-promoting): a factor screened
    # at adequate power with no detectable IC (REJECT), a resolved IC above the
    # detectable floor awaiting the independent reviewer gate (non-promoting
    # INCONCLUSIVE routed to the signal shelf), and mixed/ambiguous IC evidence
    # that a reviewer must adjudicate.
    WELL_POWERED_NULL = "WELL_POWERED_NULL"
    SIGNAL_PENDING_REVIEWER = "SIGNAL_PENDING_REVIEWER"
    REVIEW_NEEDED = "REVIEW_NEEDED"


def validate_verdict_reason_code(
    value: VerdictReasonCode | str | Any,
    *,
    field: str = "reason_code",
) -> VerdictReasonCode:
    """Validate an exact taxonomy reason code and reject free text."""

    if isinstance(value, VerdictReasonCode):
        return value
    if type(value) is str:
        try:
            return VerdictReasonCode(value)
        except ValueError:
            pass
    raise GovernanceValidationError(
        ValidationIssue(
            field=field,
            code="invalid_verdict_reason_code",
            message="reason_code must be one of the closed VerdictReasonCode values",
            expected=" | ".join(code.value for code in VerdictReasonCode),
            actual=str(value),
        )
    )


def validate_optional_verdict_reason_code(
    value: VerdictReasonCode | str | Any | None,
    *,
    field: str = "reason_code",
) -> VerdictReasonCode | None:
    """Validate an optional reason code when it is present."""

    if value is None:
        return None
    return validate_verdict_reason_code(value, field=field)


def missing_inconclusive_reason_issue(
    *,
    field: str = "reason_code",
    state_field: str = "state",
) -> ValidationIssue:
    """Return the common fail-closed issue for INCONCLUSIVE without reason_code."""

    return ValidationIssue(
        field=field,
        code="missing_reason_code_for_inconclusive",
        message=f"{field} is required when {state_field} is INCONCLUSIVE",
        expected="valid VerdictReasonCode",
        actual="missing",
    )


__all__ = [
    "VerdictReasonCode",
    "missing_inconclusive_reason_issue",
    "validate_optional_verdict_reason_code",
    "validate_verdict_reason_code",
]
