from __future__ import annotations

from alpha_system.governance.detection_statistic import (
    TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
)
from alpha_system.governance.canaries import (
    DETECTED,
    NOT_DETECTED,
    load_default_planted_fake_alpha_clean_twin_fixture,
    load_default_planted_fake_alpha_fixture,
    load_default_true_alpha_detection_fixture,
    run_planted_fake_alpha_clean_twin_canary,
    run_true_alpha_detection_canary,
)
from tools.hooks.canary_runner import scenarios


def test_strong_true_signal_fixture_is_detected_through_gated_path(tmp_path) -> None:
    result = run_true_alpha_detection_canary("strong", workspace=tmp_path)

    assert result.promotion_outcome == "EVIDENCE_READY"
    assert result.evidence_transition == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    assert result.diagnostics_status == "PASS"
    assert result.detected is True
    assert result.expected_detection is True
    assert result.detection_outcome == DETECTED
    assert result.expectation_met is True
    assert result.declared_signal_to_noise >= result.declared_detectable_floor_signal_to_noise
    assert result.measured_abs_pearson_ic >= result.detection_threshold_abs_pearson_ic
    assert result.sample_count == 12


def test_weak_true_signal_fixture_is_not_detected_below_declared_floor(tmp_path) -> None:
    result = run_true_alpha_detection_canary("weak", workspace=tmp_path)

    assert result.promotion_outcome == "EVIDENCE_READY"
    assert result.evidence_transition == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    assert result.diagnostics_status == "PASS"
    assert result.detected is False
    assert result.expected_detection is False
    assert result.detection_outcome == NOT_DETECTED
    assert result.expectation_met is True
    assert result.declared_signal_to_noise < result.declared_detectable_floor_signal_to_noise
    assert result.measured_abs_pearson_ic < result.detection_threshold_abs_pearson_ic
    assert result.sample_count == 12


def test_planted_fake_alpha_clean_twin_passes_gate_stack(tmp_path) -> None:
    result = run_planted_fake_alpha_clean_twin_canary(workspace=tmp_path)

    assert result.passed_gate_stack is True
    assert result.promotion_outcome == "EVIDENCE_READY"
    assert result.evidence_transition == "DIAGNOSTICS_RUN->EVIDENCE_READY"
    assert result.blocked_issue_code == "none"


def test_clean_twin_matches_p04_shape_without_contamination() -> None:
    contaminated = load_default_planted_fake_alpha_fixture()
    clean = load_default_planted_fake_alpha_clean_twin_fixture()

    assert [bar["bar_id"] for bar in clean["bars"]] == [
        bar["bar_id"] for bar in contaminated["bars"]
    ]
    assert len(clean["labels"]) == len(contaminated["labels"])
    assert clean["lookahead_k"] == 0
    assert all(label["lookahead_k"] == 0 for label in clean["labels"])
    assert all(label["bar_id"] == label["source_bar_id"] for label in clean["labels"])


def test_detection_fixtures_declare_threshold_pair() -> None:
    strong = load_default_true_alpha_detection_fixture("strong")
    weak = load_default_true_alpha_detection_fixture("weak")

    assert strong["detection_threshold_abs_pearson_ic"] == weak[
        "detection_threshold_abs_pearson_ic"
    ]
    assert (
        strong["detection_threshold_abs_pearson_ic"]
        == TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC
    )
    assert strong["declared_detectable_floor_signal_to_noise"] == weak[
        "declared_detectable_floor_signal_to_noise"
    ]
    assert strong["declared_signal_to_noise"] > weak["declared_signal_to_noise"]
    assert strong["expected_detection"] is True
    assert weak["expected_detection"] is False


def test_canary_runner_registers_detection_pair() -> None:
    by_name = {canary.name: canary for canary in scenarios()}

    assert "true_alpha_detection_detect_strong" in by_name
    assert by_name["true_alpha_detection_detect_strong"].expect_block is False
    assert "true_alpha_detection_no_detect_weak" in by_name
    assert by_name["true_alpha_detection_no_detect_weak"].expect_block is False
