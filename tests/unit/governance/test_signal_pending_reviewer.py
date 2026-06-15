from __future__ import annotations

import pytest

from alpha_system.governance.signal_pending_reviewer import (
    SignalPendingReviewerRecord,
    create_signal_pending_reviewer_record,
    validate_signal_pending_reviewer_record,
)
from alpha_system.governance.validation import GovernanceValidationError

TIMESTAMP = "2026-06-15T00:00:00Z"


def _record() -> SignalPendingReviewerRecord:
    return create_signal_pending_reviewer_record(
        alpha_spec_id_or_hypothesis_id="aspec_unit",
        original_verdict_ref="readout:fpmain_unit",
        factor_id="base_ohlcv_distance_to_vwap",
        slice_id="ES_2020_60m",
        pearson_ic=-0.0557,
        rank_ic=-0.0150,
        n_eff=327155,
        detectable_abs_ic=0.0034,
        bucket_rank_correlation=-0.805,
        created_at=TIMESTAMP,
    )


def test_create_signal_pending_reviewer_record_is_non_promoting() -> None:
    record = _record()

    assert record.requires_reviewer is True
    assert record.eligible is False
    assert record.study_kind == "main_effect"
    payload = record.to_dict()
    assert payload["pearson_ic"] == pytest.approx(-0.0557)
    assert payload["n_eff"] == 327155
    # Round-trips through the validator unchanged.
    assert validate_signal_pending_reviewer_record(payload).to_dict() == payload


def test_signal_record_rejects_promotion_eligible_state() -> None:
    payload = _record().to_dict()
    payload["eligible"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "eligible" for issue in exc_info.value.issues)


def test_signal_record_requires_reviewer_flag() -> None:
    payload = _record().to_dict()
    payload["requires_reviewer"] = False

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "requires_reviewer" for issue in exc_info.value.issues)


def test_signal_record_rejects_non_positive_detectable_floor() -> None:
    payload = _record().to_dict()
    payload["detectable_abs_ic"] = 0.0

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "detectable_abs_ic" for issue in exc_info.value.issues)


def _setup_record() -> SignalPendingReviewerRecord:
    return create_signal_pending_reviewer_record(
        alpha_spec_id_or_hypothesis_id="aspec_setup",
        original_verdict_ref="readout:fpsetup_unit",
        factor_id="prior_session_high",
        slice_id="ES_2020_120m",
        n_eff=412,
        net_mean_lift=-0.0031,
        outcome_label_type="net_excursion",
        observed_effect=-0.0031,
        surrogate_gate_pass_count=0,
        surrogate_run_count=200,
        created_at=TIMESTAMP,
        study_kind="context_not_equal_trigger",
    )


def test_setup_lane_record_validates_with_net_evidence_and_no_ic() -> None:
    record = _setup_record()

    assert record.study_kind == "context_not_equal_trigger"
    assert record.requires_reviewer is True
    assert record.eligible is False
    # No IC numbers in the setup lane.
    assert record.pearson_ic is None
    assert record.rank_ic is None
    assert record.detectable_abs_ic is None
    assert record.bucket_rank_correlation is None
    # The signed net excursion + surrogate evidence is preserved.
    assert record.net_mean_lift == pytest.approx(-0.0031)
    assert record.observed_effect == pytest.approx(-0.0031)
    assert record.outcome_label_type == "net_excursion"
    assert record.surrogate_gate_pass_count == 0
    assert record.surrogate_run_count == 200
    assert record.n_eff == 412
    # Round-trips through the validator (and from_mapping alias) unchanged.
    payload = record.to_dict()
    assert validate_signal_pending_reviewer_record(payload).to_dict() == payload
    assert SignalPendingReviewerRecord.from_mapping(payload).to_dict() == payload


def test_setup_lane_record_requires_net_mean_lift() -> None:
    payload = _setup_record().to_dict()
    payload["net_mean_lift"] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "net_mean_lift" for issue in exc_info.value.issues)


def test_setup_lane_record_rejects_stray_ic_fields() -> None:
    payload = _setup_record().to_dict()
    payload["pearson_ic"] = 0.1

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "pearson_ic" for issue in exc_info.value.issues)


def test_main_effect_record_still_requires_ic_fields() -> None:
    # The main_effect contract is UNCHANGED: dropping an IC field fails closed.
    payload = _record().to_dict()
    payload["pearson_ic"] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_signal_pending_reviewer_record(payload)

    assert any(issue.field == "pearson_ic" for issue in exc_info.value.issues)
