from __future__ import annotations

from pathlib import Path

from alpha_system.research.study_outputs import DiagnosticSummary, no_forbidden_claims


def test_study_summary_avoids_unsupported_positive_claims() -> None:
    summary = DiagnosticSummary(
        run_id="study_test",
        study_id="claim-check",
        factor_id="fixture_close_delta",
        factor_version="v1",
        label_id="forward_return_1m",
        label_version="labels:v1",
        data_version="data:v1",
        engine_version="intraday_factor_diagnostics_v1",
        sample_size=2,
        missing_label_count=0,
        missing_factor_count=0,
        warnings=("research diagnostics only",),
        diagnostics={"directional": {"pearson_ic": {"ic": 0.1, "n": 2}}},
    )

    assert no_forbidden_claims(summary.to_dict())


def test_factor_diagnostics_docs_do_not_make_positive_claims() -> None:
    text = Path("docs/FACTOR_DIAGNOSTICS.md").read_text(encoding="utf-8").lower()

    for phrase in ("tradable", "profitable", "production-ready", "robust alpha", "approved"):
        assert phrase not in text
    assert "not strategy pnl truth" in text
    assert "not tradability evidence" in text
