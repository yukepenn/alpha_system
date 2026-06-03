from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.promotion import (
    PROMOTION_DECISION_REQUIRED_FIELDS,
    PROMOTION_IMPLIES_CAPITAL_ALLOCATION,
    PROMOTION_IMPLIES_LIVE_APPROVAL,
    PROMOTION_IMPLIES_PRODUCTION_READINESS,
    PromotionDecision,
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
    generate_promotion_decision_id,
    validate_promotion_decision,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
EVIDENCE_BUNDLE_ID = "evb_6a52db0eaf5d1335e0c78152"
TRIAL_ID = "trial_e49649b00c617b1f713df3fa"
SECOND_TRIAL_ID = "trial_4c82b590a90a7d4971ac48c6"
REVIEWER_VERDICT_ID = "rver_aaaaaaaaaaaaaaaaaaaaaaaa"
TIMESTAMP = "2026-06-03T13:52:09Z"


def valid_promotion_payload(
    *,
    next_state: PromotionLifecycleState | str = PromotionLifecycleState.CANDIDATE,
    decision: PromotionDecisionOutcome | str = PromotionDecisionOutcome.CANDIDATE,
    trial_ledger_refs: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "alpha_spec_id": ALPHA_SPEC_ID,
        "evidence_bundle_id": EVIDENCE_BUNDLE_ID,
        "trial_ledger_refs": (
            [TRIAL_ID, SECOND_TRIAL_ID] if trial_ledger_refs is None else trial_ledger_refs
        ),
        "previous_state": PromotionLifecycleState.REVIEWED.value,
        "next_state": PromotionLifecycleState(next_state).value,
        "decision": PromotionDecisionOutcome(decision).value,
        "rationale": (
            "Synthetic governance evidence is complete enough for candidate review state."
        ),
        "reviewer_verdict_id": REVIEWER_VERDICT_ID,
        "warnings": (
            ["PromotionDecision is governance metadata only."] if warnings is None else warnings
        ),
        "timestamp": TIMESTAMP,
    }
    payload["promotion_id"] = generate_promotion_decision_id(payload)
    return payload


def payload_with_generated_id(payload: dict[str, object]) -> dict[str, object]:
    updated = deepcopy(payload)
    updated["promotion_id"] = generate_promotion_decision_id(updated)
    return updated


def test_valid_promotion_decision_contains_all_required_fields() -> None:
    payload = valid_promotion_payload()

    decision = validate_promotion_decision(payload)

    assert isinstance(decision, PromotionDecision)
    assert tuple(decision.to_dict()) == PROMOTION_DECISION_REQUIRED_FIELDS
    assert decision.promotion_id == generate_promotion_decision_id(payload)
    assert decision.promotion_id.startswith("prom_")
    assert decision.alpha_spec_id == ALPHA_SPEC_ID
    assert decision.evidence_bundle_id == EVIDENCE_BUNDLE_ID
    assert decision.trial_ledger_refs == (TRIAL_ID, SECOND_TRIAL_ID)
    assert decision.previous_state is PromotionLifecycleState.REVIEWED
    assert decision.next_state is PromotionLifecycleState.CANDIDATE
    assert decision.decision is PromotionDecisionOutcome.CANDIDATE
    assert decision.reviewer_verdict_id == REVIEWER_VERDICT_ID


def test_create_promotion_decision_generates_content_bound_id() -> None:
    payload = valid_promotion_payload(warnings=[])

    decision = create_promotion_decision(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        evidence_bundle_id=str(payload["evidence_bundle_id"]),
        trial_ledger_refs=list(payload["trial_ledger_refs"]),
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale=str(payload["rationale"]),
        reviewer_verdict_id=str(payload["reviewer_verdict_id"]),
        warnings=[],
        timestamp=str(payload["timestamp"]),
    )

    assert decision.promotion_id == payload["promotion_id"]
    assert decision.warnings == ()


@pytest.mark.parametrize("field", PROMOTION_DECISION_REQUIRED_FIELDS)
def test_promotion_decision_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_promotion_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_promotion_decision(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", PROMOTION_DECISION_REQUIRED_FIELDS)
def test_promotion_decision_rejects_each_null_required_field(field: str) -> None:
    payload = valid_promotion_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_promotion_decision(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("promotion_id", "", "malformed_id"),
        ("alpha_spec_id", TRIAL_ID, "unexpected_kind"),
        ("evidence_bundle_id", ALPHA_SPEC_ID, "unexpected_kind"),
        ("trial_ledger_refs", [], "empty_required_field"),
        ("trial_ledger_refs", [ALPHA_SPEC_ID], "unexpected_kind"),
        ("trial_ledger_refs", [TRIAL_ID, TRIAL_ID], "duplicate_trial_ledger_ref"),
        ("previous_state", "DRAFT", "invalid_promotion_source_state"),
        ("previous_state", "LIVE_APPROVED", "prohibited_mvp_state"),
        ("next_state", "PRODUCTION_READY", "prohibited_mvp_state"),
        ("next_state", "EVIDENCE_READY", "invalid_promotion_target_state"),
        ("decision", "WATCH", "decision_target_mismatch"),
        ("decision", "APPROVED", "invalid_promotion_decision"),
        ("rationale", "", "empty_required_field"),
        ("reviewer_verdict_id", "", "malformed_id"),
        ("warnings", ["n/a"], "empty_required_field"),
        ("timestamp", "2026-06-03", "invalid_timestamp"),
    ],
)
def test_promotion_decision_rejects_invalid_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_promotion_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_promotion_decision(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_promotion_decision_rejects_unknown_fields_without_dropping_them() -> None:
    payload = valid_promotion_payload()
    payload["live_approved"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_promotion_decision(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "live_approved" in payload


def test_promotion_decision_rejects_id_that_does_not_match_content() -> None:
    payload = valid_promotion_payload()
    changed = deepcopy(payload)
    changed["rationale"] = "Changed rationale after the deterministic ID was generated."

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_promotion_decision(changed)

    assert exc_info.value.issues[0].code == "promotion_id_mismatch"
    assert exc_info.value.issues[0].field == "promotion_id"


def test_promotion_decision_canonical_round_trip_is_deterministic() -> None:
    payload = valid_promotion_payload()
    reordered = dict(reversed(list(payload.items())))

    decision = validate_promotion_decision(payload)
    serialized = decision.to_canonical_json()
    round_tripped = PromotionDecision.from_canonical_json(serialized)

    assert round_tripped == decision
    assert deserialize(serialized) == decision.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_promotion_decision_does_not_imply_live_capital_or_production_status() -> None:
    decision = validate_promotion_decision(valid_promotion_payload())

    assert decision.implies_live_approval is False
    assert decision.implies_capital_allocation is False
    assert decision.implies_production_readiness is False
    assert PROMOTION_IMPLIES_LIVE_APPROVAL is False
    assert PROMOTION_IMPLIES_CAPITAL_ALLOCATION is False
    assert PROMOTION_IMPLIES_PRODUCTION_READINESS is False
