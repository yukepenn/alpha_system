from __future__ import annotations

from alpha_system.governance.detection_statistic import (
    DETECTED,
    NOT_DETECTED,
    TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
    evaluate_detection_statistic,
)


def test_detection_power_statement_appears_on_detected_and_not_detected_paths() -> None:
    detected = evaluate_detection_statistic(
        _summary(0.96, n=101),
        threshold_abs_pearson_ic=TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
    )
    not_detected = evaluate_detection_statistic(
        _summary(0.10, n=101),
        threshold_abs_pearson_ic=TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
    )

    assert detected.detection_outcome == DETECTED
    assert not_detected.detection_outcome == NOT_DETECTED
    assert detected.detection_threshold_abs_pearson_ic == 0.95
    assert not_detected.detection_threshold_abs_pearson_ic == 0.95

    for result in (detected, not_detected):
        payload = result.to_dict()
        power = payload["detection_power"]
        assert power["stacked"]["n_eff"] == 101
        assert power["stacked"]["statistical_validity_claim"] is False
        assert "Could have detected IC down to" in power["stacked"]["statement"]
        assert power["per_factor"][0]["factor_id"] == "fixture_factor"
        assert power["per_factor"][0]["factor_version"] == "factor:v1"


def test_detection_power_can_report_multiple_declared_factors() -> None:
    result = evaluate_detection_statistic(
        _summary(0.2, n=100),
        threshold_abs_pearson_ic=TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC,
        n_eff=100,
        per_factor_n_eff={
            "factor_a": 25,
            "factor_b": 100,
        },
    )

    per_factor = result.detection_power["per_factor"]
    assert len(per_factor) == 2
    assert per_factor[0]["factor_id"] == "factor_a"
    assert per_factor[0]["mde_abs_ic"] > per_factor[1]["mde_abs_ic"]
    assert result.detected is False


def _summary(ic: float, *, n: int) -> dict[str, object]:
    return {
        "factor_id": "fixture_factor",
        "factor_version": "factor:v1",
        "diagnostics": {
            "directional": {
                "pearson_ic": {"ic": ic, "n": n},
            },
        },
    }
