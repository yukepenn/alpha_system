from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.rejected_idea import (
    REJECTED_IDEA_REASON_CATEGORY_DESCRIPTIONS,
    REJECTED_IDEA_REQUIRED_FIELDS,
    REJECTION_IS_PERMANENT_BAN,
    RejectedIdeaReasonCategory,
    RejectedIdeaRecord,
    ResearchGraveyardLedger,
    create_rejected_idea_reconsideration,
    create_rejected_idea_record,
    generate_rejected_idea_id,
    validate_rejected_idea_record,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
HYPOTHESIS_ID = "hyp_438ceffd40855205de5497f0"
SECOND_HYPOTHESIS_ID = "hyp_4c82b590a90a7d4971ac48c6"
TRIAL_ID = "trial_e49649b00c617b1f713df3fa"
EVIDENCE_BUNDLE_ID = "evb_6a52db0eaf5d1335e0c78152"
REVIEWER = "reviewer:independent-governance-reviewer"
CREATED_AT = "2026-06-03T13:52:09Z"


def valid_rejected_payload(
    *,
    alpha_spec_id_or_hypothesis_id: str = ALPHA_SPEC_ID,
    reason_category: RejectedIdeaReasonCategory | str = RejectedIdeaReasonCategory.WEAK_EVIDENCE,
    evidence_references: list[str] | None = None,
    duplicate_links: list[str] | None = None,
    leakage_cost_weakness_notes: list[str] | None = None,
    reviewer: str = REVIEWER,
    created_at: str = CREATED_AT,
) -> dict[str, object]:
    record = create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=alpha_spec_id_or_hypothesis_id,
        reason_category=reason_category,
        evidence_references=(
            [TRIAL_ID, EVIDENCE_BUNDLE_ID] if evidence_references is None else evidence_references
        ),
        duplicate_links=[HYPOTHESIS_ID] if duplicate_links is None else duplicate_links,
        leakage_cost_weakness_notes=(
            ["Synthetic evidence did not meet the governance threshold."]
            if leakage_cost_weakness_notes is None
            else leakage_cost_weakness_notes
        ),
        reviewer=reviewer,
        created_at=created_at,
    )
    return record.to_dict()


def payload_with_generated_id(payload: dict[str, object]) -> dict[str, object]:
    updated = deepcopy(payload)
    updated["rejected_id"] = generate_rejected_idea_id(updated)
    return updated


def test_valid_rejected_idea_record_contains_required_fields() -> None:
    payload = valid_rejected_payload()

    record = validate_rejected_idea_record(payload)

    assert isinstance(record, RejectedIdeaRecord)
    assert tuple(record.to_dict()) == REJECTED_IDEA_REQUIRED_FIELDS
    assert record.rejected_id == generate_rejected_idea_id(payload)
    assert record.rejected_id.startswith("rej_")
    assert record.alpha_spec_id_or_hypothesis_id == ALPHA_SPEC_ID
    assert record.reason_category is RejectedIdeaReasonCategory.WEAK_EVIDENCE
    assert record.evidence_references == (TRIAL_ID, EVIDENCE_BUNDLE_ID)
    assert record.implies_permanent_ban is False
    assert REJECTION_IS_PERMANENT_BAN is False


def test_create_rejected_idea_record_accepts_hypothesis_reference() -> None:
    payload = valid_rejected_payload(
        alpha_spec_id_or_hypothesis_id=HYPOTHESIS_ID,
        reason_category=RejectedIdeaReasonCategory.DUPLICATE,
    )

    record = validate_rejected_idea_record(payload)

    assert record.alpha_spec_id_or_hypothesis_id == HYPOTHESIS_ID
    assert record.reason_category is RejectedIdeaReasonCategory.DUPLICATE


def test_reason_category_set_is_closed_and_documented() -> None:
    assert {category.value for category in RejectedIdeaReasonCategory} == {
        "duplicate",
        "leakage",
        "weak_evidence",
        "cost",
        "failed_diagnostics",
        "out_of_scope",
        "other",
    }
    assert set(REJECTED_IDEA_REASON_CATEGORY_DESCRIPTIONS) == {
        category.value for category in RejectedIdeaReasonCategory
    }


@pytest.mark.parametrize("field", REJECTED_IDEA_REQUIRED_FIELDS)
def test_rejected_idea_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_rejected_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", REJECTED_IDEA_REQUIRED_FIELDS)
def test_rejected_idea_rejects_each_null_required_field(field: str) -> None:
    payload = valid_rejected_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("rejected_id", "", "malformed_id"),
        ("alpha_spec_id_or_hypothesis_id", "", "invalid_referenced_idea_id"),
        ("reason_category", "", "invalid_reason_category"),
        ("evidence_references", [], "empty_required_field"),
        ("evidence_references", [""], "empty_required_field"),
        ("duplicate_links", [], "empty_required_field"),
        ("duplicate_links", ["unknown"], "empty_required_field"),
        ("leakage_cost_weakness_notes", [], "empty_required_field"),
        ("leakage_cost_weakness_notes", ["n/a"], "empty_required_field"),
        ("reviewer", "placeholder", "empty_required_field"),
        ("created_at", "", "empty_required_field"),
        ("created_at", "2026-06-03", "invalid_created_at"),
    ],
)
def test_rejected_idea_rejects_empty_or_malformed_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_rejected_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_rejected_idea_rejects_unknown_reason_category() -> None:
    payload = valid_rejected_payload()
    payload["reason_category"] = "interesting_but_later"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(payload)

    assert exc_info.value.issues[0].code == "invalid_reason_category"
    assert exc_info.value.issues[0].field == "reason_category"


def test_rejected_idea_rejects_unknown_fields_without_dropping_them() -> None:
    payload = valid_rejected_payload()
    payload["promotion_decision"] = "not part of this phase"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "promotion_decision" in payload


def test_rejected_idea_rejects_id_that_does_not_match_content() -> None:
    payload = valid_rejected_payload()
    changed = deepcopy(payload)
    changed["reason_category"] = RejectedIdeaReasonCategory.COST.value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_rejected_idea_record(changed)

    assert exc_info.value.issues[0].code == "rejected_id_mismatch"
    assert exc_info.value.issues[0].field == "rejected_id"


def test_rejected_idea_canonical_round_trip_is_deterministic() -> None:
    payload = valid_rejected_payload()
    reordered = dict(reversed(list(payload.items())))

    record = validate_rejected_idea_record(payload)
    serialized = record.to_canonical_json()
    round_tripped = RejectedIdeaRecord.from_canonical_json(serialized)

    assert round_tripped == record
    assert deserialize(serialized) == record.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_graveyard_ledger_appends_lists_and_looks_up_rejected_records() -> None:
    record = validate_rejected_idea_record(valid_rejected_payload())
    second = validate_rejected_idea_record(
        valid_rejected_payload(
            alpha_spec_id_or_hypothesis_id=HYPOTHESIS_ID,
            reason_category=RejectedIdeaReasonCategory.DUPLICATE,
            evidence_references=[TRIAL_ID],
            duplicate_links=[ALPHA_SPEC_ID],
            leakage_cost_weakness_notes=["Duplicate exposure found by synthetic fixture."],
            created_at="2026-06-03T13:53:00Z",
        )
    )

    ledger = ResearchGraveyardLedger()
    ledger.append(record)
    ledger.append(second.to_dict())

    assert len(ledger) == 2
    assert ledger.list_records() == (record, second)
    assert tuple(ledger) == (record, second)
    assert ledger.lookup_by_id(record.rejected_id) == record
    assert ledger.lookup_by_referenced_idea(ALPHA_SPEC_ID) == (record,)
    assert ledger.lookup_by_referenced_idea(HYPOTHESIS_ID) == (second,)


def test_graveyard_ledger_blocks_overwrite_and_has_no_delete_api() -> None:
    record = validate_rejected_idea_record(valid_rejected_payload())
    ledger = ResearchGraveyardLedger([record])

    with pytest.raises(GovernanceValidationError) as exc_info:
        ledger.append(record.to_dict())

    assert exc_info.value.issues[0].code == "duplicate_rejected_id"
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "remove")
    assert not hasattr(ledger, "overwrite")
    assert ledger.list_records() == (record,)


def test_reconsideration_is_explicit_linked_and_does_not_mutate_rejection() -> None:
    record = validate_rejected_idea_record(valid_rejected_payload())
    ledger = ResearchGraveyardLedger([record])
    before_reconsideration = record.to_dict()

    reconsideration = create_rejected_idea_reconsideration(
        rejected_id=record.rejected_id,
        reconsidered_idea_id=SECOND_HYPOTHESIS_ID,
        reconsideration_reference="reconsideration-note-001",
        rationale="New hypothesis narrows the original rejected scope.",
        reviewer="reviewer:second-independent-reviewer",
        created_at="2026-06-03T14:00:00Z",
    )
    ledger.append_reconsideration(reconsideration)

    assert record.to_dict() == before_reconsideration
    assert ledger.lookup_by_id(record.rejected_id) == record
    assert ledger.list_reconsiderations(record.rejected_id) == (reconsideration,)
    assert ledger.list_reconsiderations()[0].rejected_id == record.rejected_id


def test_reconsideration_must_link_existing_rejected_record() -> None:
    record = validate_rejected_idea_record(valid_rejected_payload())
    reconsideration = create_rejected_idea_reconsideration(
        rejected_id=record.rejected_id,
        reconsidered_idea_id=SECOND_HYPOTHESIS_ID,
        reconsideration_reference="reconsideration-note-001",
        rationale="New hypothesis narrows the original rejected scope.",
        reviewer="reviewer:second-independent-reviewer",
        created_at="2026-06-03T14:00:00Z",
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        ResearchGraveyardLedger().append_reconsideration(reconsideration)

    assert exc_info.value.issues[0].code == "unknown_rejected_id"
    assert exc_info.value.issues[0].field == "rejected_id"


def test_graveyard_ledger_serialized_round_trip_is_deterministic() -> None:
    record = validate_rejected_idea_record(valid_rejected_payload())
    reconsideration = create_rejected_idea_reconsideration(
        rejected_id=record.rejected_id,
        reconsidered_idea_id=SECOND_HYPOTHESIS_ID,
        reconsideration_reference="reconsideration-note-001",
        rationale="New hypothesis narrows the original rejected scope.",
        reviewer="reviewer:second-independent-reviewer",
        created_at="2026-06-03T14:00:00Z",
    )
    ledger = ResearchGraveyardLedger([record], [reconsideration])

    serialized = ledger.to_canonical_json()
    round_tripped = ResearchGraveyardLedger.from_canonical_json(serialized)

    assert round_tripped.to_dict() == ledger.to_dict()
    assert canonical_serialize(ledger.to_dict()) == serialized
