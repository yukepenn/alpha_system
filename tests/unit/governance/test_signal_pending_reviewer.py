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
