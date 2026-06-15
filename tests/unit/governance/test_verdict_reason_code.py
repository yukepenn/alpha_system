from __future__ import annotations

import pytest

from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    validate_verdict_reason_code,
)


def test_verdict_reason_code_taxonomy_is_exactly_the_compass_set() -> None:
    assert {code.value for code in VerdictReasonCode} == {
        "UNDERPOWERED",
        "SUBSTRATE_GAP",
        "COST_FRAGILE",
        "DATA_QUALITY",
        "LEAKAGE_BLOCKED",
        "DUPLICATE_EXPOSURE",
        "REGIME_UNSTABLE",
        "BBO_PROXY_LIMITATION",
        # main_effect autonomous evidence triage (non-promoting): no detectable
        # IC at adequate power, a resolved IC awaiting the reviewer gate, and
        # mixed/sign-conflicting IC evidence a reviewer must adjudicate.
        "WELL_POWERED_NULL",
        "SIGNAL_PENDING_REVIEWER",
        "REVIEW_NEEDED",
    }


@pytest.mark.parametrize("code", list(VerdictReasonCode))
def test_verdict_reason_code_accepts_enum_instances_and_exact_values(
    code: VerdictReasonCode,
) -> None:
    assert validate_verdict_reason_code(code) is code
    assert validate_verdict_reason_code(code.value) is code


@pytest.mark.parametrize(
    "value",
    [
        "",
        "substrate_gap",
        "SUBSTRATE GAP",
        "SUBSTRATE_GAP ",
        "UNKNOWN",
        "placeholder",
        "missing substrate",
    ],
)
def test_verdict_reason_code_rejects_free_text_near_misses_and_placeholders(
    value: str,
) -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_verdict_reason_code(value)

    issue = exc_info.value.issues[0]
    assert issue.field == "reason_code"
    assert issue.code == "invalid_verdict_reason_code"
