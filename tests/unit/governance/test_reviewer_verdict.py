from __future__ import annotations

import copy

import pytest

from alpha_system.governance.reviewer_verdict import (
    MERGE_ELIGIBLE_REVIEWER_VERDICTS,
    REVIEWER_VERDICT_REQUIRED_FIELDS,
    ReviewerVerdict,
    ReviewerVerdictOutcome,
    create_reviewer_verdict,
    generate_reviewer_verdict_id,
    validate_reviewer_verdict,
)
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.verdict_reason_code import VerdictReasonCode

TIMESTAMP = "2026-06-03T13:52:09Z"


def valid_payload() -> dict[str, object]:
    return {
        "reviewer_id": "claude:independent-governance-reviewer",
        "role": "claude_reviewer",
        "independence_statement": (
            "Reviewer identity and role are independent from the Codex implementer."
        ),
        "verdict": "PASS_WITH_WARNINGS",
        "blocking_issues": [],
        "warnings": ["Synthetic governance review only; no market claim is made."],
        "checked_artifacts": [
            "src/alpha_system/governance/reviewer_verdict.py",
            "src/alpha_system/governance/promotion_gate.py",
        ],
        "checked_commands": [
            "python -m pytest tests/unit/governance/test_reviewer_verdict.py -q"
        ],
        "timestamp": TIMESTAMP,
    }


def test_reviewer_verdict_validates_required_contract() -> None:
    payload = valid_payload()

    verdict = validate_reviewer_verdict(payload)

    assert verdict.to_dict() == payload
    assert verdict.verdict is ReviewerVerdictOutcome.PASS_WITH_WARNINGS
    assert verdict.is_merge_eligible is True
    assert verdict.reviewer_verdict_id == generate_reviewer_verdict_id(payload)
    assert verdict.reviewer_verdict_id.startswith("rver_")


@pytest.mark.parametrize("field", REVIEWER_VERDICT_REQUIRED_FIELDS)
def test_reviewer_verdict_missing_required_fields_fail_closed(field: str) -> None:
    payload = valid_payload()
    payload.pop(field)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    assert any(issue.field == field for issue in exc_info.value.issues)
    assert any(issue.code == "missing_required_field" for issue in exc_info.value.issues)


@pytest.mark.parametrize(
    "field",
    [
        "reviewer_id",
        "role",
        "independence_statement",
        "timestamp",
    ],
)
def test_reviewer_verdict_empty_text_fields_fail_closed(field: str) -> None:
    payload = valid_payload()
    payload[field] = ""

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    assert any(issue.field == field for issue in exc_info.value.issues)
    assert any(issue.code == "empty_required_field" for issue in exc_info.value.issues)


@pytest.mark.parametrize("field", ["checked_artifacts", "checked_commands"])
def test_reviewer_verdict_empty_checked_lists_fail_closed(field: str) -> None:
    payload = valid_payload()
    payload[field] = []

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    assert exc_info.value.issues[0].field == field
    assert exc_info.value.issues[0].code == "empty_required_field"


def test_reviewer_verdict_rejects_invalid_verdict() -> None:
    payload = valid_payload()
    payload["verdict"] = "APPROVED"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    codes = {issue.code for issue in exc_info.value.issues}
    assert "invalid_reviewer_verdict" in codes


def test_reviewer_verdict_rejects_unknown_fields() -> None:
    payload = valid_payload()
    payload["market_truth"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    codes = {issue.code for issue in exc_info.value.issues}
    assert "unknown_field" in codes


def test_reviewer_verdict_rejects_invalid_list_items() -> None:
    payload = valid_payload()
    payload["checked_artifacts"] = ["docs/governance/REVIEWER_INDEPENDENCE.md", ""]
    payload["checked_commands"] = [
        "python -m pytest tests/unit/governance/test_reviewer_verdict.py -q",
        7,
    ]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    codes = {issue.code for issue in exc_info.value.issues}
    assert "empty_required_field" in codes
    assert "invalid_item_type" in codes


def test_reviewer_verdict_id_generation_is_deterministic() -> None:
    payload = valid_payload()
    first = validate_reviewer_verdict(payload)
    second = validate_reviewer_verdict(copy.deepcopy(payload))
    changed_payload = valid_payload()
    changed_payload["warnings"] = ["Different warning text changes the content ID."]

    assert first.reviewer_verdict_id == second.reviewer_verdict_id
    assert first.reviewer_verdict_id == generate_reviewer_verdict_id(payload)
    assert first.reviewer_verdict_id != generate_reviewer_verdict_id(changed_payload)


def test_reviewer_verdict_id_generation_fails_closed_on_invalid_content() -> None:
    payload = valid_payload()
    payload["independence_statement"] = ""

    with pytest.raises(GovernanceValidationError) as exc_info:
        generate_reviewer_verdict_id(payload)

    assert exc_info.value.issues[0].field == "independence_statement"
    assert exc_info.value.issues[0].code == "empty_required_field"


def test_reviewer_verdict_round_trip_serialization_is_canonical() -> None:
    verdict = ReviewerVerdict.from_mapping(valid_payload())

    serialized = verdict.to_canonical_json()
    round_trip = ReviewerVerdict.from_canonical_json(serialized)

    assert round_trip == verdict
    assert round_trip.to_canonical_json() == serialized
    assert round_trip.reviewer_verdict_id == verdict.reviewer_verdict_id


def test_create_reviewer_verdict_uses_closed_vocabulary() -> None:
    verdict = create_reviewer_verdict(
        reviewer_id="claude:independent-governance-reviewer",
        role="claude_reviewer",
        independence_statement="Reviewer is independent from the implementer.",
        verdict=ReviewerVerdictOutcome.PASS,
        blocking_issues=[],
        warnings=[],
        checked_artifacts=["handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P12.md"],
        checked_commands=["python tools/verify.py --smoke"],
        timestamp=TIMESTAMP,
    )

    assert verdict.verdict is ReviewerVerdictOutcome.PASS
    assert set(MERGE_ELIGIBLE_REVIEWER_VERDICTS) == {
        ReviewerVerdictOutcome.PASS,
        ReviewerVerdictOutcome.PASS_WITH_WARNINGS,
    }


def test_reviewer_verdict_inconclusive_requires_reason_code() -> None:
    payload = valid_payload()
    payload["verdict"] = ReviewerVerdictOutcome.INCONCLUSIVE.value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    assert any(
        issue.code == "missing_reason_code_for_inconclusive"
        for issue in exc_info.value.issues
    )


def test_reviewer_verdict_rejects_free_text_reason_code() -> None:
    payload = valid_payload()
    payload["verdict"] = ReviewerVerdictOutcome.INCONCLUSIVE.value
    payload["reason_code"] = "not enough evidence"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_reviewer_verdict(payload)

    assert any(issue.code == "invalid_verdict_reason_code" for issue in exc_info.value.issues)


def test_reviewer_verdict_inconclusive_reason_code_is_not_merge_eligible() -> None:
    payload = valid_payload()
    payload["verdict"] = ReviewerVerdictOutcome.INCONCLUSIVE.value
    payload["reason_code"] = VerdictReasonCode.SUBSTRATE_GAP.value

    verdict = validate_reviewer_verdict(payload)

    assert verdict.verdict is ReviewerVerdictOutcome.INCONCLUSIVE
    assert verdict.reason_code is VerdictReasonCode.SUBSTRATE_GAP
    assert verdict.is_merge_eligible is False
    assert ReviewerVerdictOutcome.INCONCLUSIVE not in MERGE_ELIGIBLE_REVIEWER_VERDICTS
    assert verdict.to_dict()["reason_code"] == "SUBSTRATE_GAP"


def test_reviewer_verdict_present_reason_code_changes_id_without_affecting_absent_id() -> None:
    payload = valid_payload()
    without_reason = validate_reviewer_verdict(payload)
    with_reason_payload = copy.deepcopy(payload)
    with_reason_payload["reason_code"] = VerdictReasonCode.DATA_QUALITY.value

    with_reason = validate_reviewer_verdict(with_reason_payload)

    assert without_reason.to_dict() == payload
    assert "reason_code" not in without_reason.to_dict()
    assert with_reason.reviewer_verdict_id != without_reason.reviewer_verdict_id
