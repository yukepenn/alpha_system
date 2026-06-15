"""Unit tests for the pure cross-idea family-FDR correction math."""

from __future__ import annotations

import math

import pytest

from alpha_system.governance.family_fdr_correction import (
    DEFAULT_FDR_ALPHA,
    DEFAULT_FDR_METHOD,
    FDR_METHOD_BENJAMINI_HOCHBERG,
    FDR_METHOD_BONFERRONI,
    REASON_ELIGIBLE,
    FamilyFdrVerdict,
    correct_family,
    resolution_adequate,
    surrogate_p_upper_bound,
)
from alpha_system.governance.validation import GovernanceValidationError

# Classic Benjamini-Hochberg (1995) ordered p-value vector (m = 15).
_BH_1995 = (
    0.0001,
    0.0004,
    0.0019,
    0.0095,
    0.0201,
    0.0278,
    0.0298,
    0.0344,
    0.0459,
    0.3240,
    0.4262,
    0.5719,
    0.6528,
    0.7590,
    1.0000,
)


def test_defaults_are_bh_010() -> None:
    assert DEFAULT_FDR_METHOD == FDR_METHOD_BENJAMINI_HOCHBERG
    assert DEFAULT_FDR_ALPHA == 0.10


def test_surrogate_p_upper_bound_add_one() -> None:
    assert surrogate_p_upper_bound(0, 64) == pytest.approx(1.0 / 65.0)
    assert surrogate_p_upper_bound(3, 199) == pytest.approx(4.0 / 200.0)


def test_surrogate_p_upper_bound_rejects_bad_inputs() -> None:
    with pytest.raises(GovernanceValidationError):
        surrogate_p_upper_bound(-1, 10)
    with pytest.raises(GovernanceValidationError):
        surrogate_p_upper_bound(5, 4)  # pass > run
    with pytest.raises(GovernanceValidationError):
        surrogate_p_upper_bound(0, -1)


def test_resolution_adequate_boundary() -> None:
    # m=7, alpha=0.05 -> required run_count = ceil(7/0.05) - 1 = 139.
    assert math.ceil(7 / 0.05) - 1 == 139
    assert resolution_adequate(139, 7, 0.05) is True
    assert resolution_adequate(138, 7, 0.05) is False
    assert resolution_adequate(64, 7, 0.05) is False
    # m=5, alpha=0.10 -> required = ceil(5/0.10) - 1 = 49.
    assert resolution_adequate(49, 5, 0.10) is True
    assert resolution_adequate(48, 5, 0.10) is False


def test_resolution_adequate_validates() -> None:
    with pytest.raises(GovernanceValidationError):
        resolution_adequate(-1, 5, 0.05)
    with pytest.raises(GovernanceValidationError):
        resolution_adequate(100, 0, 0.05)
    with pytest.raises(GovernanceValidationError):
        resolution_adequate(100, 5, 0.0)
    with pytest.raises(GovernanceValidationError):
        resolution_adequate(100, 5, 1.0)


def _bh_entries(run_count: int = 1_000_000) -> list[dict[str, object]]:
    return [
        {"idea_key": f"i{index}", "p_value": p_value, "run_count": run_count}
        for index, p_value in enumerate(_BH_1995)
    ]


def test_benjamini_hochberg_textbook_vector() -> None:
    verdicts = correct_family(_bh_entries(), alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    rejected = {v.idea_key for v in verdicts if v.rejected_null}
    # BH step-up at 0.05 rejects the first four (the classic answer).
    assert rejected == {"i0", "i1", "i2", "i3"}
    assert all(v.method == FDR_METHOD_BENJAMINI_HOCHBERG for v in verdicts)
    assert all(v.family_size == 15 for v in verdicts)


def test_bonferroni_textbook_vector() -> None:
    verdicts = correct_family(_bh_entries(), alpha_fw=0.05, method=FDR_METHOD_BONFERRONI)
    rejected = {v.idea_key for v in verdicts if v.rejected_null}
    # Bonferroni threshold 0.05/15 = 0.003333 -> rejects the first three.
    assert rejected == {"i0", "i1", "i2"}
    for verdict in verdicts:
        assert verdict.corrected_threshold == pytest.approx(0.05 / 15.0)


def test_bh_is_at_least_as_powerful_as_bonferroni() -> None:
    bh = correct_family(_bh_entries(), alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    bonf = correct_family(_bh_entries(), alpha_fw=0.05, method=FDR_METHOD_BONFERRONI)
    bh_rejected = {v.idea_key for v in bh if v.rejected_null}
    bonf_rejected = {v.idea_key for v in bonf if v.rejected_null}
    assert bonf_rejected <= bh_rejected


def test_historical_pa_setup_rework_m7() -> None:
    entries: list[dict[str, object]] = [
        {"idea_key": "prior_high_sweep", "gate_pass_count": 0, "run_count": 64}
    ]
    for sibling in range(6):  # total m = 7
        entries.append({"idea_key": f"sib{sibling}", "gate_pass_count": 20, "run_count": 64})
    verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BONFERRONI)
    signal = next(v for v in verdicts if v.idea_key == "prior_high_sweep")
    assert signal.family_size == 7
    assert signal.p_value == pytest.approx(1.0 / 65.0)
    assert signal.resolution_adequate is False
    assert signal.rejected_null is False  # 0.01538 > 0.05/7 = 0.00714
    assert signal.eligible is False
    assert "resolution_inadequate" in signal.reason


def test_historical_pa_setup_rework_m5_net_excursion() -> None:
    entries: list[dict[str, object]] = [
        {"idea_key": "prior_high_sweep", "gate_pass_count": 0, "run_count": 64}
    ]
    for sibling in range(4):  # total m = 5
        entries.append({"idea_key": f"sib{sibling}", "gate_pass_count": 20, "run_count": 64})
    verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BONFERRONI)
    signal = next(v for v in verdicts if v.idea_key == "prior_high_sweep")
    assert signal.family_size == 5
    assert signal.resolution_adequate is False
    assert signal.eligible is False


def test_non_vacuous_eligible() -> None:
    entries: list[dict[str, object]] = [
        {"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000}
    ]
    for sibling in range(4):  # m = 5
        entries.append({"idea_key": f"weak{sibling}", "p_value": 0.9, "run_count": 10_000})
    verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    strong = next(v for v in verdicts if v.idea_key == "strong")
    assert strong.resolution_adequate is True
    assert strong.rejected_null is True
    assert strong.eligible is True
    assert strong.reason == REASON_ELIGIBLE


def test_rejected_but_unresolved_is_not_eligible() -> None:
    # m=1, alpha=0.10 -> required run_count = ceil(1/0.10) - 1 = 9. run_count=5 is
    # below that, so the idea is significant under the correction but cannot
    # resolve the corrected threshold -> not eligible.
    entries = [{"idea_key": "x", "p_value": 0.01, "run_count": 5}]
    verdict = correct_family(entries, alpha_fw=0.10, method=FDR_METHOD_BENJAMINI_HOCHBERG)[0]
    assert verdict.rejected_null is True
    assert verdict.resolution_adequate is False
    assert verdict.eligible is False
    assert verdict.reason == "resolution_inadequate"


def test_gate_pass_count_entries_supported() -> None:
    entries = [
        {"idea_key": "a", "gate_pass_count": 0, "run_count": 999},
        {"idea_key": "b", "gate_pass_count": 100, "run_count": 999},
    ]
    verdicts = correct_family(entries, alpha_fw=0.10, method=FDR_METHOD_BONFERRONI)
    by_key = {v.idea_key: v for v in verdicts}
    assert by_key["a"].p_value == pytest.approx(1.0 / 1000.0)
    assert by_key["b"].p_value == pytest.approx(101.0 / 1000.0)


def test_empty_family_returns_empty() -> None:
    assert correct_family([], alpha_fw=0.10, method=FDR_METHOD_BONFERRONI) == ()


def test_invalid_method_and_alpha_raise() -> None:
    entries = [{"idea_key": "a", "p_value": 0.01, "run_count": 100}]
    with pytest.raises(GovernanceValidationError):
        correct_family(entries, alpha_fw=0.10, method="holm")
    with pytest.raises(GovernanceValidationError):
        correct_family(entries, alpha_fw=1.5, method=FDR_METHOD_BONFERRONI)


def test_invalid_entries_raise() -> None:
    with pytest.raises(GovernanceValidationError):
        correct_family([{"idea_key": "", "p_value": 0.1, "run_count": 10}])
    with pytest.raises(GovernanceValidationError):
        correct_family([{"idea_key": "a", "p_value": 1.5, "run_count": 10}])
    with pytest.raises(GovernanceValidationError):
        correct_family([{"idea_key": "a", "run_count": 10}])  # no p / gate_pass
    with pytest.raises(GovernanceValidationError):
        correct_family(
            [
                {"idea_key": "a", "p_value": 0.1, "run_count": 10},
                {"idea_key": "a", "p_value": 0.2, "run_count": 10},
            ]
        )  # duplicate idea_key
    with pytest.raises(GovernanceValidationError):
        correct_family({"idea_key": "a"})  # not an iterable of entries


def test_verdict_round_trip() -> None:
    verdict = correct_family(
        [{"idea_key": "a", "p_value": 0.0001, "run_count": 10_000}],
        alpha_fw=0.10,
        method=FDR_METHOD_BENJAMINI_HOCHBERG,
    )[0]
    restored = FamilyFdrVerdict.from_dict(verdict.to_dict())
    assert restored == verdict
