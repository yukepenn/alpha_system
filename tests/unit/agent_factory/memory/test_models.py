from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from alpha_system.agent_factory.memory import (
    RejectedIdeaMemoryRecord,
    RejectedIdeaMemoryStatus,
    ResearchMemoryRecord,
    ResearchMemoryStatus,
    detect_duplicate_idea,
    ensure_rejected_ideas_visible,
    idea_fingerprint,
    idea_key,
    models,
    prior_rejection_reasons,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaReasonCategory,
    RejectedIdeaRecord,
    ResearchGraveyardLedger,
    create_rejected_idea_record,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
SECOND_ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd1"
HYPOTHESIS_ID = "hyp_438ceffd40855205de5497f0"
TRIAL_ID = "trial_e49649b00c617b1f713df3fa"
EVIDENCE_BUNDLE_ID = "evb_6a52db0eaf5d1335e0c78152"
CREATED_AT = "2026-06-06T19:35:14Z"


def test_memory_contracts_import_and_validate() -> None:
    record = valid_rejected_memory_record()
    research_record = valid_research_memory_record(record)

    assert record.status is RejectedIdeaMemoryStatus.REJECTED
    assert research_record.status is ResearchMemoryStatus.REJECTED
    assert record.graveyard_rejected_ids == (valid_rejected_record().rejected_id,)
    assert research_record.related_rejected_memory_refs == (record.memory_id,)


def test_memory_records_are_immutable() -> None:
    record = valid_rejected_memory_record()

    with pytest.raises(FrozenInstanceError):
        record.summary = "changed"  # type: ignore[misc]


def test_idea_key_and_fingerprint_are_deterministic_and_normalized() -> None:
    first = candidate_idea(title="ES Opening Range Fade")
    second = candidate_idea(title="  es   opening range fade  ")

    assert idea_key(first) == idea_key(second)
    assert idea_fingerprint(first) == idea_fingerprint(second)
    assert idea_key(first).startswith("idea:")
    assert idea_fingerprint(first).startswith("idea_fingerprint:sha256:")


def test_duplicate_detection_surfaces_memory_and_graveyard_reasons() -> None:
    rejected_record = valid_rejected_record()
    ledger = ResearchGraveyardLedger([rejected_record])
    memory_record = valid_rejected_memory_record(rejected_record=rejected_record)

    report = detect_duplicate_idea(candidate_idea(), [memory_record], ledger)

    assert report.already_rejected is True
    assert report.matched_memory_refs == (memory_record.memory_id,)
    assert report.matched_graveyard_refs == (rejected_record.rejected_id,)
    assert "librarian recorded weak evidence from synthetic fixture only" in (
        report.rejection_reasons
    )
    assert any(reason.startswith("weak_evidence:") for reason in report.rejection_reasons)
    assert report.next_required_gate == "hypothesis_scout_prior_rejection_review"


def test_duplicate_detection_can_consume_graveyard_without_memory_match() -> None:
    rejected_record = valid_rejected_record()
    ledger = ResearchGraveyardLedger([rejected_record])

    report = detect_duplicate_idea(
        {
            "title": "new spelling of prior idea",
            "alpha_spec_id_or_hypothesis_id": ALPHA_SPEC_ID,
        },
        [],
        ledger,
    )

    assert report.already_rejected is True
    assert report.matched_memory_refs == ()
    assert report.matched_graveyard_refs == (rejected_record.rejected_id,)
    assert any(reason.startswith("weak_evidence:") for reason in report.rejection_reasons)


def test_prior_rejection_reason_query_surfaces_known_idea_key_reasons() -> None:
    rejected_record = valid_rejected_record()
    ledger = ResearchGraveyardLedger([rejected_record])
    memory_record = valid_rejected_memory_record(rejected_record=rejected_record)

    reasons = prior_rejection_reasons(idea_key(candidate_idea()), [memory_record], ledger)

    assert "librarian recorded weak evidence from synthetic fixture only" in reasons
    assert (
        "weak_evidence: Synthetic fixture did not satisfy the documented evidence gate."
        in reasons
    )


def test_hidden_or_dropped_rejected_idea_is_rejected_by_visibility_contract() -> None:
    first = valid_rejected_record()
    second = create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=SECOND_ALPHA_SPEC_ID,
        reason_category=RejectedIdeaReasonCategory.COST,
        evidence_references=[TRIAL_ID],
        duplicate_links=[HYPOTHESIS_ID],
        leakage_cost_weakness_notes=["Cost review blocked the synthetic fixture idea."],
        reviewer="reviewer:independent-governance-reviewer",
        created_at="2026-06-06T19:36:14Z",
    )
    ledger = ResearchGraveyardLedger([first, second])

    with pytest.raises(ValueError, match=second.rejected_id):
        ensure_rejected_ideas_visible(
            [valid_rejected_memory_record(rejected_record=first)],
            ledger,
        )


def test_visibility_contract_rejects_unknown_graveyard_refs() -> None:
    record = valid_rejected_memory_record(
        rejected_record=valid_rejected_record(),
        graveyard_rejected_ids=("rej_111111111111111111111111",),
    )

    with pytest.raises(ValueError, match="unknown graveyard"):
        ensure_rejected_ideas_visible([record], ResearchGraveyardLedger([valid_rejected_record()]))


@pytest.mark.parametrize(
    ("factory", "field_name", "bad_value"),
    [
        (
            lambda: valid_rejected_memory_record(),
            "summary",
            "raw_payload=data/raw/es_ticks.parquet",
        ),
        (
            lambda: valid_rejected_memory_record(),
            "rejection_reasons",
            ["mutable list is not a value-free tuple"],
        ),
        (
            lambda: valid_rejected_memory_record(),
            "spec_refs",
            ("artifact:diagnostics.arrow",),
        ),
        (
            lambda: valid_research_memory_record(),
            "prior_outcome_summary",
            "numpy ndarray values were embedded",
        ),
        (
            lambda: valid_research_memory_record(),
            "limitations",
            (b"raw-bytes",),
        ),
    ],
)
def test_memory_records_reject_raw_heavy_or_mutable_payloads(
    factory: object,
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(factory(), **{field_name: bad_value})


def test_research_memory_rejected_status_requires_rejected_memory_ref() -> None:
    with pytest.raises(ValueError, match="rejected memory ref"):
        valid_research_memory_record(related_rejected_memory_refs=())


def test_candidate_fingerprint_rejects_raw_or_heavy_payload_markers() -> None:
    with pytest.raises(ValueError, match="raw/heavy"):
        idea_key({"title": "raw_payload", "description": "data/raw/file.parquet"})


def test_model_consumes_governance_graveyard_without_redefining_it() -> None:
    assert models.RejectedIdeaRecord is RejectedIdeaRecord
    assert models.ResearchGraveyardLedger is ResearchGraveyardLedger
    assert models.RejectedIdeaRecord.__module__ == "alpha_system.governance.rejected_idea"
    assert models.ResearchGraveyardLedger.__module__ == "alpha_system.governance.rejected_idea"


def candidate_idea(*, title: str = "ES Opening Range Fade") -> dict[str, object]:
    return {
        "title": title,
        "description": "Fade opening range extension after failed diagnostics.",
        "alpha_spec_id_or_hypothesis_id": ALPHA_SPEC_ID,
    }


def valid_rejected_record() -> RejectedIdeaRecord:
    return create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=ALPHA_SPEC_ID,
        reason_category=RejectedIdeaReasonCategory.WEAK_EVIDENCE,
        evidence_references=[TRIAL_ID, EVIDENCE_BUNDLE_ID],
        duplicate_links=[HYPOTHESIS_ID],
        leakage_cost_weakness_notes=[
            "Synthetic fixture did not satisfy the documented evidence gate."
        ],
        reviewer="reviewer:independent-governance-reviewer",
        created_at=CREATED_AT,
    )


def valid_rejected_memory_record(
    *,
    rejected_record: RejectedIdeaRecord | None = None,
    graveyard_rejected_ids: tuple[str, ...] | None = None,
) -> RejectedIdeaMemoryRecord:
    record = rejected_record if rejected_record is not None else valid_rejected_record()
    key = idea_key(candidate_idea())
    return RejectedIdeaMemoryRecord(
        memory_id=f"rejected_idea_memory:{key.removeprefix('idea:')}",
        idea_key=key,
        idea_fingerprint=idea_fingerprint(candidate_idea()),
        status=RejectedIdeaMemoryStatus.REJECTED,
        alpha_spec_id="alpha_spec:opening_range_fade",
        originating_role_id="librarian",
        graveyard_rejected_ids=(
            (record.rejected_id,) if graveyard_rejected_ids is None else graveyard_rejected_ids
        ),
        rejection_reasons=("librarian recorded weak evidence from synthetic fixture only",),
        decision_refs=("agent_decision:record_rejection",),
        handoff_refs=("agent_handoff:librarian_rejection",),
        tool_invocation_refs=("tool_invocation:memory_lookup",),
        spec_refs=(
            "alpha_spec:opening_range_fade",
            "study_spec:opening_range_synthetic",
        ),
        next_required_gate="hypothesis_scout_prior_rejection_review",
        summary="Visible memory row for a rejected synthetic fixture idea.",
        limitations=("contract_only",),
    )


def valid_research_memory_record(
    rejected_memory: RejectedIdeaMemoryRecord | None = None,
    *,
    related_rejected_memory_refs: tuple[str, ...] | None = None,
) -> ResearchMemoryRecord:
    memory = rejected_memory if rejected_memory is not None else valid_rejected_memory_record()
    related_refs = (
        (memory.memory_id,)
        if related_rejected_memory_refs is None
        else related_rejected_memory_refs
    )
    return ResearchMemoryRecord(
        memory_id="research_memory:opening_range_fade",
        idea_key=memory.idea_key,
        idea_fingerprint=memory.idea_fingerprint,
        status=ResearchMemoryStatus.REJECTED,
        originating_role_id="librarian",
        prior_outcome_summary="Prior outcome is rejected; see linked rejected memory ref.",
        decision_refs=("agent_decision:record_rejection",),
        handoff_refs=("agent_handoff:librarian_rejection",),
        tool_invocation_refs=("tool_invocation:memory_lookup",),
        spec_refs=("alpha_spec:opening_range_fade",),
        related_rejected_memory_refs=related_refs,
        next_required_gate="hypothesis_scout_prior_rejection_review",
        limitations=("contract_only",),
    )
