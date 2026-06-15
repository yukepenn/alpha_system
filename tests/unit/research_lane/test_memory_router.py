from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.requeue import REQUEUE_REASON
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.research_lane import memory_router as memory_router_module
from alpha_system.research_lane.memory_router import route_verdict_to_memory

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")
TIMESTAMP = "2026-06-14T00:00:00Z"


def test_reject_routes_to_graveyard_keyed_by_alpha_spec_id() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "REJECT",
            "reason_code": "DATA_QUALITY",
            "why": "Pre-test gate failed before interpretation.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "graveyard"
    assert payload["record_type"] == "RejectedIdeaRecord"
    assert payload["memory_record"]["alpha_spec_id_or_hypothesis_id"] == (
        bundle.idea_draft.alpha_spec_id
    )
    assert payload["memory_record"]["rejected_id"].startswith("rej_")
    assert payload["promotion_eligible"] is False
    assert payload["probe_spent"] is False
    assert payload["exploratory_refusal"]["status"] == "refused"


def test_reject_fails_closed_before_graveyard_write_without_alpha_spec_id(monkeypatch) -> None:
    bundle = _bundle()
    called = False

    def forbidden_write(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("graveyard write must not be reached")

    monkeypatch.setattr(memory_router_module, "create_rejected_idea_record", forbidden_write)
    idea = bundle.idea_draft.to_dict()
    del idea["alpha_spec_id"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory("REJECT", idea, _readout(bundle), created_at=TIMESTAMP)

    assert called is False
    assert exc_info.value.issues[0].field == "alpha_spec_id"


def test_data_gap_routes_to_valid_requeue_without_spending_probe() -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "DATA_GAP",
            "reason_code": "SUBSTRATE_GAP",
            "why": "Pre-test gate reports missing bounded slice metadata.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    assert payload["record_type"] == "RequeuedVerdictRecord"
    assert payload["memory_record"]["requeue_reason"] == REQUEUE_REASON
    assert payload["memory_record"]["eligible"] is False
    assert payload["memory_record"]["original_verdict_ref"] == "readout:unit_readout"
    assert payload["probe_spent"] is False
    assert payload["promotion_eligible"] is False


def test_inconclusive_routes_to_requeue_preserving_verdict_label() -> None:
    # INCONCLUSIVE (real probe ran, clean surrogate, but underpowered / no establishable
    # effect) routes to a reason-coded requeue like DATA_GAP, but the honest verdict label
    # is preserved on the result (not relabeled DATA_GAP).
    bundle = _bundle()

    result = route_verdict_to_memory(
        {
            "verdict": "INCONCLUSIVE",
            "reason_code": "UNDERPOWERED",
            "why": "Real probe ran with a clean surrogate gate but the effect is underpowered.",
        },
        bundle.idea_draft,
        _readout(bundle),
        created_at=TIMESTAMP,
    )

    payload = result.to_dict()
    assert payload["action"] == "requeue"
    assert payload["verdict"] == "INCONCLUSIVE"
    assert payload["record_type"] == "RequeuedVerdictRecord"
    assert payload["memory_record"]["eligible"] is False
    assert payload["probe_spent"] is False
    assert payload["promotion_eligible"] is False


@pytest.mark.parametrize("verdict", ["WATCH", "CANDIDATE"])
def test_watch_candidate_require_reviewer_verdict_id(verdict: str) -> None:
    bundle = _bundle()

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory(
            {"verdict": verdict, "reason_code": "REGIME_UNSTABLE"},
            bundle.idea_draft,
            _readout(bundle),
            created_at=TIMESTAMP,
            evidence_bundle_id=_id(GovernanceIdKind.EVIDENCE_BUNDLE, "evb"),
            trial_ledger_refs=(_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, "trial"),),
        )

    assert any(issue.field == "reviewer_verdict_id" for issue in exc_info.value.issues)


@pytest.mark.parametrize("verdict", ["WATCH", "CANDIDATE"])
def test_watch_candidate_create_only_reviewer_gated_promotion(verdict: str) -> None:
    bundle = _bundle()

    result = route_verdict_to_memory(
        {"verdict": verdict, "reason_code": "REGIME_UNSTABLE"},
        bundle.idea_draft,
        _readout(bundle),
        reviewer_verdict_id=_id(GovernanceIdKind.REVIEWER_VERDICT, "rver"),
        evidence_bundle_id=_id(GovernanceIdKind.EVIDENCE_BUNDLE, "evb"),
        trial_ledger_refs=(_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, "trial"),),
        created_at=TIMESTAMP,
        probe_spent=True,
    )

    payload = result.to_dict()
    assert payload["action"] == "reviewer_gated_promotion"
    assert payload["record_type"] == "PromotionDecision"
    assert payload["memory_record"]["reviewer_verdict_id"].startswith("rver_")
    assert payload["memory_record"]["decision"] == verdict
    assert payload["memory_record"]["next_state"] == verdict
    assert payload["promotion_eligible"] is False


def test_exploratory_guard_must_refuse_the_readout() -> None:
    bundle = _bundle()
    readout = {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "status": "INCONCLUSIVE",
        "promotion_eligible": False,
        "row_access": {"status": "unresolved", "fabricated_values": False},
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        route_verdict_to_memory("DATA_GAP", bundle.idea_draft, readout, created_at=TIMESTAMP)

    assert exc_info.value.issues[0].code == "exploratory_refusal_missing"


def test_memory_router_source_never_writes_survivor_libraries() -> None:
    source = inspect.getsource(memory_router_module)

    assert "FactorLibrary" not in source
    assert "factor_library" not in source
    assert "AlphaBook" not in source
    assert "alpha_book" not in source


def _bundle():
    return build_idea_validation_bundle(
        json.loads(FIXTURE_IDEA.read_text(encoding="utf-8")),
        source=FIXTURE_IDEA.as_posix(),
    )


def _readout(bundle) -> dict[str, object]:
    return {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "readout_id": "unit_readout",
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
        "mechanism_card": bundle.mechanism_card.to_dict(),
        "slice_spec": {"slice_id": "unit-slice", "study_kind": "main_effect"},
        "row_access": {
            "status": "unresolved",
            "reason": "unit fixture has no materialized slice",
            "fabricated_values": False,
        },
    }


def _id(kind: GovernanceIdKind, salt: str) -> str:
    return generate_governance_id(kind, {"test": "memory_router", "salt": salt})
