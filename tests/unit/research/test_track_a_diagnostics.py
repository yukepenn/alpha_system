"""DK-P03 Track A pure-research scorer tests (injected synthetic rows only)."""

from __future__ import annotations

import pytest

from alpha_system.research.track_a_scorer import (
    CLOSED_TAXONOMY_PRIMARY_STATES,
    MechanismDiagnostics,
    PRIMARY_STATE_INCONCLUSIVE,
    PRIMARY_STATE_REJECT,
    TrackAScorerError,
    score_mechanism,
)
from alpha_system.governance.verdict_reason_code import VerdictReasonCode
from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.splits.n_eff import HorizonOverlapMetadata


def _overlap(horizon_seconds: int = 1800) -> HorizonOverlapMetadata:
    discount = max(1.0, horizon_seconds / 60.0)
    return HorizonOverlapMetadata(
        horizon=float(horizon_seconds),
        horizon_unit="seconds",
        sampling_cadence=60.0,
        sampling_cadence_unit="seconds",
        discount_factor=discount,
        metadata_source="test_overlap",
    )


def _row(factor: float, label: float, *, ts: str) -> dict[str, object]:
    return {
        "factor_value": factor,
        "label_value": label,
        "horizon_seconds": 1800,
        "available_ts": ts,
        "label_available_ts": ts,
        "instrument_id": "ES",
        "event_ts": ts,
        "session_label": "ES_session",
    }


def _well_powered_rows(n: int = 4000) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(n):
        # Deterministic, mixed-sign relationship with ample sample.
        factor = float(i % 7)
        label = ((i * 37) % 11 - 5) / 1000.0
        ts = f"2024-01-01T{(i % 23) + 1:02d}:00:00+00:00"
        rows.append(_row(factor, label, ts=ts))
    return rows


def test_scorer_runs_over_injected_rows_and_emits_runtime_state() -> None:
    result = score_mechanism(
        mechanism_id="day_of_week_effect@30m",
        factor_id="session_calendar_roll_day_of_week",
        rows=_well_powered_rows(),
        horizon_overlap_metadata=_overlap(),
    )
    assert isinstance(result, MechanismDiagnostics)
    assert isinstance(result.runtime_state, StudyRunResultState)
    assert result.primary_state in CLOSED_TAXONOMY_PRIMARY_STATES
    # Every readout carries an ic_power_statement with no validity claim.
    assert result.ic_power_statement["statistical_validity_claim"] is False
    assert "mde_abs_ic" in result.ic_power_statement
    assert result.n_eff_report["statistical_validity_claim"] is False


def test_well_powered_complete_read_does_not_auto_promote() -> None:
    result = score_mechanism(
        mechanism_id="day_of_week_effect@30m",
        factor_id="session_calendar_roll_day_of_week",
        rows=_well_powered_rows(),
        horizon_overlap_metadata=_overlap(),
    )
    # A complete, well-powered descriptive read is never WATCH/CANDIDATE_RESEARCH
    # from diagnostics alone (survivor is reviewer-gated, asymmetric).
    assert result.primary_state in {PRIMARY_STATE_REJECT, PRIMARY_STATE_INCONCLUSIVE}
    assert result.is_survivor is False


def test_underpowered_rows_map_to_inconclusive_underpowered() -> None:
    # A tiny sample: usable pairs at/above the descriptive minimum but N_eff
    # collapses to 1 after the horizon-overlap discount -> no resolvable MDE.
    rows = [
        _row(float(i), (i % 3 - 1) / 1000.0, ts=f"2024-01-01T{i + 1:02d}:00:00+00:00")
        for i in range(4)
    ]
    result = score_mechanism(
        mechanism_id="opex_pinning@30m",
        factor_id="session_calendar_roll_is_opex_day_flag",
        rows=rows,
        horizon_overlap_metadata=_overlap(1800),
    )
    assert result.primary_state == PRIMARY_STATE_INCONCLUSIVE
    assert result.reason_code == VerdictReasonCode.UNDERPOWERED.value
    assert result.mde_abs_ic is None or result.n_eff <= 1


def test_missing_available_ts_maps_to_reject() -> None:
    rows = [
        {
            "factor_value": float(i),
            "label_value": (i % 5 - 2) / 1000.0,
            "horizon_seconds": 1800,
            # available_ts intentionally omitted -> runtime REJECTED.
            "label_available_ts": "2024-01-01T01:00:00+00:00",
            "instrument_id": "ES",
            "event_ts": f"2024-01-01T{i + 1:02d}:00:00+00:00",
        }
        for i in range(50)
    ]
    result = score_mechanism(
        mechanism_id="month_end_flow@30m",
        factor_id="session_calendar_roll_is_month_end_session_flag",
        rows=rows,
        horizon_overlap_metadata=_overlap(1800),
    )
    assert result.runtime_state == StudyRunResultState.REJECTED
    assert result.primary_state == PRIMARY_STATE_REJECT
    assert result.reason_code is None


def test_inconclusive_row_must_carry_reason_code() -> None:
    with pytest.raises(TrackAScorerError):
        MechanismDiagnostics(
            mechanism_id="x",
            factor_id="f",
            runtime_state=StudyRunResultState.INCONCLUSIVE,
            primary_state=PRIMARY_STATE_INCONCLUSIVE,
            pearson_ic=None,
            rank_ic=None,
            usable_pair_count=0,
            total_observations=0,
            coverage_ratio=None,
            bucket_count=0,
            bucket_populated_count=0,
            bucket_is_monotonic=False,
            bucket_direction="insufficient",
            n_eff=0,
            se_ic=None,
            mde_abs_ic=None,
            ic_power_statement={"statistical_validity_claim": False},
            n_eff_report={"statistical_validity_claim": False},
            reason_code=None,
        )


def test_primary_state_must_be_closed_taxonomy() -> None:
    with pytest.raises(TrackAScorerError):
        MechanismDiagnostics(
            mechanism_id="x",
            factor_id="f",
            runtime_state=StudyRunResultState.DIAGNOSTICS_COMPLETE,
            primary_state="PROMOTE",  # not in the closed taxonomy
            pearson_ic=0.0,
            rank_ic=0.0,
            usable_pair_count=10,
            total_observations=10,
            coverage_ratio=1.0,
            bucket_count=5,
            bucket_populated_count=5,
            bucket_is_monotonic=False,
            bucket_direction="mixed",
            n_eff=9,
            se_ic=0.3,
            mde_abs_ic=0.6,
            ic_power_statement={"statistical_validity_claim": False},
            n_eff_report={"statistical_validity_claim": False},
            reason_code=None,
        )
