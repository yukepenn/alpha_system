from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import DiagnosticsFamily, DiagnosticsRunSpecRef
from alpha_system.runtime.diagnostics.splits import (
    RegimeSplitReport,
    SessionSplitReport,
    SplitDefinition,
    build_regime_split_report,
    build_session_split_report,
    build_split_diagnostics_reports,
)
from alpha_system.runtime.input_resolver import (
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
)

FIXTURE_PATH = (
    Path(__file__).parents[4]
    / "fixtures"
    / "runtime"
    / "diagnostics"
    / "splits"
    / "synthetic_observations.json"
)


def test_session_and_regime_split_reports_are_contract_compliant() -> None:
    session_report, regime_report = build_split_diagnostics_reports(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations(),
    )

    assert isinstance(session_report, SessionSplitReport)
    assert isinstance(regime_report, RegimeSplitReport)
    assert session_report.diagnostics_family is DiagnosticsFamily.SPLITS
    assert regime_report.diagnostics_family is DiagnosticsFamily.SPLITS
    assert session_report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert regime_report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE

    session_payload = session_report.to_dict()
    regime_payload = regime_report.to_dict()
    assert session_payload["descriptive_only"] is True
    assert regime_payload["non_promotional"] is True
    assert session_payload["raw_or_heavy_data_embedded"] is False
    assert regime_payload["diagnostic_pass_is_alpha_validation"] is False

    session_splits = {summary.split_id: summary for summary in session_report.split_summaries}
    regime_splits = {summary.split_id: summary for summary in regime_report.split_summaries}
    assert {"session:RTH", "session:ETH", "segment:open", "segment:mid", "segment:close"} <= set(
        session_splits
    )
    assert {
        "volatility:low",
        "volatility:high",
        "spread:narrow",
        "spread:wide",
        "liquidity:thin",
        "liquidity:thick",
        "trend:trend",
        "trend:range",
    } <= set(regime_splits)
    assert session_splits["session:RTH"].sample_count == 4
    assert session_splits["session:ETH"].sample_count == 2
    assert regime_splits["volatility:low"].coverage_ratio == pytest.approx(0.5)
    assert regime_splits["spread:wide"].sample_count == 3


def test_regime_report_orchestrates_research_regimes(monkeypatch: pytest.MonkeyPatch) -> None:
    from alpha_system.runtime.diagnostics.splits import core

    calls: list[str] = []

    def coverage(observations, *, filter_field: str = "regime_filter"):
        calls.append(f"coverage:{filter_field}:{len(tuple(observations))}")
        return {"coverage": 0.5, "retained": 1, "total": 2}

    def uplift(observations, *, filter_field: str = "regime_filter"):
        calls.append(f"uplift:{filter_field}:{len(tuple(observations))}")
        return {"with_filter_n": 1, "without_filter_n": 1, "uplift": 0.1}

    def false_rejection(observations, *, filter_field: str = "regime_filter"):
        calls.append(f"false_rejection:{filter_field}:{len(tuple(observations))}")
        return {"false_rejection_rate": 0.0, "positive_count": 1}

    def conditional(observations, *, filter_field: str = "regime_filter"):
        calls.append(f"conditional:{filter_field}:{len(tuple(observations))}")
        return {
            "retained_n": 1,
            "all_n": 2,
            "mean_return_improvement": 0.1,
            "hit_rate_improvement": 0.0,
        }

    monkeypatch.setattr(core.regimes, "regime_filter_coverage", coverage)
    monkeypatch.setattr(core.regimes, "regime_filter_uplift", uplift)
    monkeypatch.setattr(core.regimes, "false_rejection_rate", false_rejection)
    monkeypatch.setattr(core.regimes, "conditional_strategy_improvement", conditional)

    report = build_regime_split_report(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations()[:2],
        min_sample_count=1,
        split_definitions=(SplitDefinition("volatility:low", "volatility", "volatility_bucket", "low"),),
    )

    assert report.split_summaries[0].sample_count == 1
    assert {call.split(":")[0] for call in calls} == {
        "coverage",
        "uplift",
        "false_rejection",
        "conditional",
    }


def test_low_sample_split_fails_closed_with_visible_reason() -> None:
    report = build_session_split_report(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations()[:1],
        min_sample_count=2,
        split_definitions=(SplitDefinition("session:RTH", "session", "session_label", "RTH"),),
    )

    assert report.status is StudyRunResultState.INCONCLUSIVE
    assert report.rejection_reasons[0].code == "low_sample"
    assert report.split_summaries[0].status == "inconclusive"
    assert report.split_summaries[0].rejection_reason_code == "low_sample"


def test_available_ts_drives_session_assignment_and_label_is_not_conditioning() -> None:
    report = build_session_split_report(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack={
            "dataset_version_id": "dsv_rt_p09_fixture",
            "alpha_spec_ref": "alpha_rt_p09_fixture",
            "study_spec_ref": "study_rt_p09_fixture",
            "feature_packs": (),
            "label_packs": (),
            "session_scope": {"rth": {"start": "09:30", "end": "16:00"}},
        },
        observations=[
            {
                "event_ts": "2026-01-05T10:00:00+00:00",
                "available_ts": "2026-01-05T20:00:00+00:00",
                "label_available_ts": "2026-01-05T20:05:00+00:00",
                "label_value": 0.2,
            }
        ],
        min_sample_count=1,
        split_definitions=(
            SplitDefinition("session:RTH", "session", "session_label", "RTH"),
            SplitDefinition("session:ETH", "session", "session_label", "ETH"),
        ),
    )

    summaries = {summary.split_id: summary for summary in report.split_summaries}
    assert summaries["session:RTH"].sample_count == 0
    assert summaries["session:ETH"].sample_count == 1

    unsafe_report = build_regime_split_report(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations(),
        min_sample_count=1,
        split_definitions=(SplitDefinition("unsafe", "regime", "label_value", "positive"),),
    )
    assert unsafe_report.status is StudyRunResultState.REJECTED
    assert unsafe_report.rejection_reasons[0].code == "leakage_risk"
    assert unsafe_report.split_summaries == ()


def test_split_reports_do_not_emit_promotional_claim_phrases() -> None:
    session_report, regime_report = build_split_diagnostics_reports(
        diagnostics_run_spec_ref=_diagnostics_spec_ref(),
        runtime_input_pack=_runtime_input_pack(),
        observations=_observations(),
    )
    combined_payload = f"{session_report.to_dict()} {regime_report.to_dict()}".lower()

    for phrase in (
        "alpha validated",
        "validated alpha",
        "tradable",
        "profitable",
        "candidate approved",
        "factor promoted",
        "strategy ready",
        "live ready",
        "paper ready",
        "production ready",
    ):
        assert phrase not in combined_payload


def _observations() -> tuple[dict[str, object], ...]:
    return tuple(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _diagnostics_spec_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _runtime_input_pack() -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref="alpha_rt_p09_fixture",
        study_spec_ref="study_rt_p09_fixture",
        study_input_pack={
            "alpha_spec_id": "alpha_rt_p09_fixture",
            "study_spec_id": "study_rt_p09_fixture",
        },
        dataset_version_id="dsv_rt_p09_fixture",
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        dataset_source="synthetic_fixture",
        dataset_reproducibility_hashes={"synthetic_hash": "rt_p09"},
        canonical_input_views=(),
        feature_packs=(
            FeaturePackHandle(
                feature_version_id="feature_rt_p09_fixture_v1",
                feature_request_id="feature_request_rt_p09",
                feature_set_id="feature_set_rt_p09",
                feature_set_version="1",
                dataset_version_id="dsv_rt_p09_fixture",
                partition_id="train_fixture",
                materialization_plan_id="feature_plan_rt_p09",
                first_event_ts="2026-01-05T09:30:00+00:00",
                last_event_ts="2026-01-06T16:00:00+00:00",
                first_available_ts="2026-01-05T09:35:00+00:00",
                last_available_ts="2026-01-06T16:05:00+00:00",
                lifecycle_state="VERSIONED",
            ),
        ),
        label_packs=(
            LabelPackHandle(
                label_version_id="label_rt_p09_fixture_v1",
                label_spec_id="label_spec_rt_p09",
                label_id="label_rt_p09",
                dataset_version_id="dsv_rt_p09_fixture",
                partition_id="train_fixture",
                materialization_plan_id="label_plan_rt_p09",
                first_event_ts="2026-01-05T09:30:00+00:00",
                last_event_ts="2026-01-06T16:00:00+00:00",
                first_label_available_ts="2026-01-05T09:40:00+00:00",
                last_label_available_ts="2026-01-06T16:10:00+00:00",
                lifecycle_state="VERSIONED",
            ),
        ),
        dataset_scope={"dataset_version_id": "dsv_rt_p09_fixture"},
        partition_scope={"partition_id": "train_fixture"},
        session_scope={
            "rth": {"start": "09:30", "end": "16:00"},
            "segments": [
                {"name": "open", "start": "09:30", "end": "10:30"},
                {"name": "mid", "start": "10:30", "end": "15:00"},
                {"name": "close", "start": "15:00", "end": "16:00"},
            ],
        },
        governance_metadata={"fixture": "rt_p09"},
    )
