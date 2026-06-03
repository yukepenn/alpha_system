from __future__ import annotations

from pathlib import Path

from alpha_system.experiments.grid_outputs import no_forbidden_claims


def test_grid_summary_language_avoids_prohibited_claims() -> None:
    summary = {
        "decision_status": "research_evidence_only",
        "status_message": "offline review evidence, not approval",
    }

    assert no_forbidden_claims(summary)


def test_grid_docs_avoid_positive_claim_phrases() -> None:
    text = (
        Path("docs/GRID_ENGINE.md").read_text(encoding="utf-8")
        + "\n"
        + Path("docs/GRID_OVERFIT_POLICY.md").read_text(encoding="utf-8")
    ).lower()

    for phrase in (
        "profitable",
        "tradable",
        "production-ready",
        "guaranteed alpha",
        "market-beating",
        "approved",
    ):
        assert phrase not in text
    assert "evidence, not approval" in text
