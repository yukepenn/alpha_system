from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.experiments.promotion import (
    PromotionDecision,
    PromotionDecisionError,
    insert_promotion_decision,
    promotion_row_has_review_trail,
)


def test_promotion_decision_writes_review_trail_to_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)
    decision = PromotionDecision(
        candidate_id="candidate-1",
        source_run_id="grid-run-1",
        review_status="pass",
        decision_status="approved",
        reviewer_identity="reviewer-1",
        rationale="reviewed artifact bundle",
        artifact_references={"review": "reviews/ALPHA_SYSTEM_V1/ASV1-P22.md"},
        timestamp="2026-06-02T01:20:07Z",
    )

    with connect_registry(registry_path) as connection:
        decision_id = insert_promotion_decision(connection, decision)
        row = connection.execute(
            "SELECT * FROM promotion_decisions WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()

    assert row["subject_id"] == "candidate-1"
    assert row["run_id"] == "grid-run-1"
    assert row["reviewer"] == "reviewer-1"
    assert promotion_row_has_review_trail(row) is True


def test_candidate_cannot_self_approve() -> None:
    with pytest.raises(PromotionDecisionError, match="self-approve"):
        PromotionDecision(
            candidate_id="candidate-1",
            source_run_id="grid-run-1",
            review_status="pass",
            decision_status="approved",
            reviewer_identity="candidate-1",
            rationale="self review is invalid",
            timestamp="2026-06-02T01:20:07Z",
        )
