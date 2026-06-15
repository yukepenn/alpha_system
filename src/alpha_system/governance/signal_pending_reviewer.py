"""Non-promoting signal-shelf record for the idea-to-verdict loop.

A ``SignalPendingReviewerRecord`` captures a main_effect IC probe that resolved
a statistically detectable signal (an IC above the report-provided detectable
floor) at adequate power. It is deliberately **non-promoting**: it is NOT a
WATCH, CANDIDATE, survivor, FactorLibrary entry, strategy, or tradable claim.
It exists so the autonomous loop can record real research signals to a
reviewer-pending shelf instead of burying them in a generic INCONCLUSIVE
requeue, while the independent reviewer/trusted gate stays the only path to any
promotion. The record stores value-free diagnostic numbers (ICs, N_eff,
detectable floor, bucket rank correlation) and the feature/slice references; it
makes no profitability, tradability, or alpha claim.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue, canonical_serialize
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    validate_schema,
)

SIGNAL_PENDING_REVIEWER_STATUS = "SIGNAL_PENDING_REVIEWER"
SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS = (
    "alpha_spec_id_or_hypothesis_id",
    "original_verdict_ref",
    "factor_id",
    "slice_id",
    "study_kind",
    "pearson_ic",
    "rank_ic",
    "n_eff",
    "detectable_abs_ic",
    "bucket_rank_correlation",
    "requires_reviewer",
    "eligible",
    "created_at",
)
SIGNAL_PENDING_REVIEWER_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "alpha_spec_id_or_hypothesis_id": str,
    "original_verdict_ref": str,
    "factor_id": str,
    "slice_id": str,
    "study_kind": str,
    "pearson_ic": (int, float),
    "rank_ic": (int, float),
    "n_eff": int,
    "detectable_abs_ic": (int, float),
    "bucket_rank_correlation": (int, float),
    "requires_reviewer": bool,
    "eligible": bool,
    "created_at": str,
}
_UTC_SECONDS_SUFFIX = "Z"


@dataclass(frozen=True, slots=True)
class SignalPendingReviewerRecord:
    """Validated non-promoting signal-shelf record."""

    alpha_spec_id_or_hypothesis_id: str
    original_verdict_ref: str
    factor_id: str
    slice_id: str
    study_kind: str
    pearson_ic: float
    rank_ic: float
    n_eff: int
    detectable_abs_ic: float
    bucket_rank_correlation: float
    requires_reviewer: bool
    eligible: bool
    created_at: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SignalPendingReviewerRecord:
        return validate_signal_pending_reviewer_record(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "alpha_spec_id_or_hypothesis_id": self.alpha_spec_id_or_hypothesis_id,
            "original_verdict_ref": self.original_verdict_ref,
            "factor_id": self.factor_id,
            "slice_id": self.slice_id,
            "study_kind": self.study_kind,
            "pearson_ic": self.pearson_ic,
            "rank_ic": self.rank_ic,
            "n_eff": self.n_eff,
            "detectable_abs_ic": self.detectable_abs_ic,
            "bucket_rank_correlation": self.bucket_rank_correlation,
            "requires_reviewer": self.requires_reviewer,
            "eligible": self.eligible,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        return canonical_serialize(self.to_dict())


def create_signal_pending_reviewer_record(
    *,
    alpha_spec_id_or_hypothesis_id: str,
    original_verdict_ref: str,
    factor_id: str,
    slice_id: str,
    pearson_ic: float,
    rank_ic: float,
    n_eff: int,
    detectable_abs_ic: float,
    bucket_rank_correlation: float,
    created_at: str,
    study_kind: str = "main_effect",
) -> SignalPendingReviewerRecord:
    """Build a validated, non-promoting signal-shelf record.

    ``eligible`` and ``requires_reviewer`` are fixed by construction: the record
    is never promotion-eligible and always requires the independent reviewer
    gate before any WATCH/CANDIDATE/survivor decision.
    """

    return validate_signal_pending_reviewer_record(
        {
            "alpha_spec_id_or_hypothesis_id": alpha_spec_id_or_hypothesis_id,
            "original_verdict_ref": original_verdict_ref,
            "factor_id": factor_id,
            "slice_id": slice_id,
            "study_kind": study_kind,
            "pearson_ic": pearson_ic,
            "rank_ic": rank_ic,
            "n_eff": n_eff,
            "detectable_abs_ic": detectable_abs_ic,
            "bucket_rank_correlation": bucket_rank_correlation,
            "requires_reviewer": True,
            "eligible": False,
            "created_at": created_at,
        }
    )


def validate_signal_pending_reviewer_record(
    payload: Mapping[str, Any],
) -> SignalPendingReviewerRecord:
    """Validate a ``SignalPendingReviewerRecord`` mapping fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS,
        field_types=SIGNAL_PENDING_REVIEWER_RECORD_FIELD_TYPES,
        allowed_fields=SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS,
        object_name="SignalPendingReviewerRecord",
    )
    issues: list[ValidationIssue] = []
    for field in (
        "alpha_spec_id_or_hypothesis_id",
        "original_verdict_ref",
        "factor_id",
        "slice_id",
        "study_kind",
        "created_at",
    ):
        if not str(mapping[field]).strip():
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"SignalPendingReviewerRecord.{field} must be explicit",
                    expected="non-empty string",
                    actual=str(mapping[field]),
                )
            )
    for field in ("pearson_ic", "rank_ic", "bucket_rank_correlation"):
        number = float(mapping[field])
        if not math.isfinite(number):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_numeric_value",
                    message=f"SignalPendingReviewerRecord.{field} must be a finite number",
                    expected="finite number",
                    actual=str(mapping[field]),
                )
            )
    detectable = float(mapping["detectable_abs_ic"])
    if not math.isfinite(detectable) or detectable <= 0:
        issues.append(
            ValidationIssue(
                field="detectable_abs_ic",
                code="invalid_detectable_floor",
                message="SignalPendingReviewerRecord.detectable_abs_ic must be a positive float",
                expected="finite number > 0",
                actual=str(mapping["detectable_abs_ic"]),
            )
        )
    if type(mapping["n_eff"]) is not int or mapping["n_eff"] < 2:
        issues.append(
            ValidationIssue(
                field="n_eff",
                code="invalid_n_eff",
                message="SignalPendingReviewerRecord.n_eff must be an integer >= 2",
                expected="integer >= 2",
                actual=str(mapping["n_eff"]),
            )
        )
    if mapping["requires_reviewer"] is not True:
        issues.append(
            ValidationIssue(
                field="requires_reviewer",
                code="signal_must_require_reviewer",
                message="SignalPendingReviewerRecord.requires_reviewer must be True",
                expected="True",
                actual=str(mapping["requires_reviewer"]),
            )
        )
    if mapping["eligible"] is not False:
        issues.append(
            ValidationIssue(
                field="eligible",
                code="signal_must_be_non_promoting",
                message="SignalPendingReviewerRecord.eligible must be False (non-promoting)",
                expected="False",
                actual=str(mapping["eligible"]),
            )
        )
    if not str(mapping["created_at"]).endswith(_UTC_SECONDS_SUFFIX):
        issues.append(
            ValidationIssue(
                field="created_at",
                code="invalid_utc_timestamp",
                message="SignalPendingReviewerRecord.created_at must be a UTC seconds timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(mapping["created_at"]),
            )
        )
    issues.extend(_validate_canonical_serializable(cast(Mapping[str, Any], mapping)))
    if issues:
        raise GovernanceValidationError(issues)

    return SignalPendingReviewerRecord(
        alpha_spec_id_or_hypothesis_id=mapping["alpha_spec_id_or_hypothesis_id"],
        original_verdict_ref=mapping["original_verdict_ref"],
        factor_id=mapping["factor_id"],
        slice_id=mapping["slice_id"],
        study_kind=mapping["study_kind"],
        pearson_ic=float(mapping["pearson_ic"]),
        rank_ic=float(mapping["rank_ic"]),
        n_eff=mapping["n_eff"],
        detectable_abs_ic=float(mapping["detectable_abs_ic"]),
        bucket_rank_correlation=float(mapping["bucket_rank_correlation"]),
        requires_reviewer=mapping["requires_reviewer"],
        eligible=mapping["eligible"],
        created_at=mapping["created_at"],
    )


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(cast(JsonValue, dict(mapping)))
    except (TypeError, ValueError) as exc:
        return [
            ValidationIssue(
                field="$",
                code="not_canonical_serializable",
                message=str(exc),
                expected="strict JSON-compatible governance record",
                actual=type(exc).__name__,
            )
        ]
    return []


__all__ = [
    "SIGNAL_PENDING_REVIEWER_STATUS",
    "SignalPendingReviewerRecord",
    "create_signal_pending_reviewer_record",
    "validate_signal_pending_reviewer_record",
]
