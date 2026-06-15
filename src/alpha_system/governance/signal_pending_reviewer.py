"""Non-promoting signal-shelf record for the idea-to-verdict loop.

A ``SignalPendingReviewerRecord`` captures a research probe that resolved a
non-promoting signal worth an independent reviewer's attention. It supports two
lanes keyed by ``study_kind``:

- ``main_effect``: an IC probe that resolved a statistically detectable signal
  (an IC above the report-provided detectable floor) at adequate power. The
  record stores the value-free IC diagnostics (Pearson/rank IC, N_eff, the
  detectable floor, bucket rank correlation).
- ``context_not_equal_trigger`` (the setup/path-outcome lane): a surrogate-FDR
  gated conditioned-mean lift on a signed net-excursion outcome. This lane has
  no IC numbers; instead it stores the signed ``net_mean_lift`` + the surrogate
  evidence (observed effect, gate pass/run counts) and the conditioned
  overlap-aware ``n_eff``.

It is deliberately **non-promoting** in both lanes: it is NOT a WATCH,
CANDIDATE, survivor, FactorLibrary entry, strategy, or tradable claim. It exists
so the autonomous loop can record real research signals to a reviewer-pending
shelf instead of burying them in a generic INCONCLUSIVE requeue, while the
independent reviewer/trusted gate stays the only path to any promotion. The
record stores value-free diagnostic numbers and the feature/slice references; it
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
STUDY_KIND_MAIN_EFFECT = "main_effect"
STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER = "context_not_equal_trigger"
# Fields required + populated in every lane.
SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS = (
    "alpha_spec_id_or_hypothesis_id",
    "original_verdict_ref",
    "factor_id",
    "slice_id",
    "study_kind",
    "n_eff",
    "requires_reviewer",
    "eligible",
    "created_at",
)
# main_effect IC diagnostics: required for main_effect, None for the setup lane.
SIGNAL_PENDING_REVIEWER_RECORD_IC_FIELDS = (
    "pearson_ic",
    "rank_ic",
    "detectable_abs_ic",
    "bucket_rank_correlation",
)
# context_not_equal_trigger evidence: required for the setup lane, None otherwise.
SIGNAL_PENDING_REVIEWER_RECORD_SETUP_FIELDS = (
    "net_mean_lift",
    "observed_effect",
    "surrogate_gate_pass_count",
    "surrogate_run_count",
    "outcome_label_type",
)
SIGNAL_PENDING_REVIEWER_RECORD_ALLOWED_FIELDS = (
    *SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS,
    *SIGNAL_PENDING_REVIEWER_RECORD_IC_FIELDS,
    *SIGNAL_PENDING_REVIEWER_RECORD_SETUP_FIELDS,
)
# Optional (lane-dependent) fields accept None at the type layer; the lane
# branch in validation enforces which fields must actually be present non-None.
_NONE = type(None)
SIGNAL_PENDING_REVIEWER_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "alpha_spec_id_or_hypothesis_id": str,
    "original_verdict_ref": str,
    "factor_id": str,
    "slice_id": str,
    "study_kind": str,
    "pearson_ic": (int, float, _NONE),
    "rank_ic": (int, float, _NONE),
    "n_eff": int,
    "detectable_abs_ic": (int, float, _NONE),
    "bucket_rank_correlation": (int, float, _NONE),
    "net_mean_lift": (int, float, _NONE),
    "observed_effect": (int, float, _NONE),
    "surrogate_gate_pass_count": (int, _NONE),
    "surrogate_run_count": (int, _NONE),
    "outcome_label_type": (str, _NONE),
    "requires_reviewer": bool,
    "eligible": bool,
    "created_at": str,
}
_UTC_SECONDS_SUFFIX = "Z"


@dataclass(frozen=True, slots=True)
class SignalPendingReviewerRecord:
    """Validated non-promoting signal-shelf record (lane keyed by study_kind)."""

    alpha_spec_id_or_hypothesis_id: str
    original_verdict_ref: str
    factor_id: str
    slice_id: str
    study_kind: str
    n_eff: int
    requires_reviewer: bool
    eligible: bool
    created_at: str
    # main_effect IC diagnostics (None for the setup lane).
    pearson_ic: float | None = None
    rank_ic: float | None = None
    detectable_abs_ic: float | None = None
    bucket_rank_correlation: float | None = None
    # context_not_equal_trigger evidence (None for the main_effect lane).
    net_mean_lift: float | None = None
    observed_effect: float | None = None
    surrogate_gate_pass_count: int | None = None
    surrogate_run_count: int | None = None
    outcome_label_type: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SignalPendingReviewerRecord:
        return validate_signal_pending_reviewer_record(payload)

    # Alias kept so callers may construct from any mapping.
    from_mapping = from_dict

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
            "net_mean_lift": self.net_mean_lift,
            "observed_effect": self.observed_effect,
            "surrogate_gate_pass_count": self.surrogate_gate_pass_count,
            "surrogate_run_count": self.surrogate_run_count,
            "outcome_label_type": self.outcome_label_type,
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
    n_eff: int,
    created_at: str,
    study_kind: str = STUDY_KIND_MAIN_EFFECT,
    pearson_ic: float | None = None,
    rank_ic: float | None = None,
    detectable_abs_ic: float | None = None,
    bucket_rank_correlation: float | None = None,
    net_mean_lift: float | None = None,
    observed_effect: float | None = None,
    surrogate_gate_pass_count: int | None = None,
    surrogate_run_count: int | None = None,
    outcome_label_type: str | None = None,
) -> SignalPendingReviewerRecord:
    """Build a validated, non-promoting signal-shelf record.

    ``eligible`` and ``requires_reviewer`` are fixed by construction: the record
    is never promotion-eligible and always requires the independent reviewer
    gate before any WATCH/CANDIDATE/survivor decision.

    For ``study_kind == "main_effect"`` (the default) the IC diagnostics
    (``pearson_ic``/``rank_ic``/``detectable_abs_ic``/``bucket_rank_correlation``)
    are required and the setup-lane fields stay None. For
    ``study_kind == "context_not_equal_trigger"`` the setup-lane fields
    (``net_mean_lift``/``outcome_label_type`` + surrogate evidence) are required
    and the IC fields stay None.
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
            "net_mean_lift": net_mean_lift,
            "observed_effect": observed_effect,
            "surrogate_gate_pass_count": surrogate_gate_pass_count,
            "surrogate_run_count": surrogate_run_count,
            "outcome_label_type": outcome_label_type,
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
        allowed_fields=SIGNAL_PENDING_REVIEWER_RECORD_ALLOWED_FIELDS,
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
    study_kind = str(mapping.get("study_kind") or "").strip()
    if study_kind == STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER:
        issues.extend(_validate_setup_lane(mapping))
    else:
        issues.extend(_validate_main_effect_lane(mapping))
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
        n_eff=mapping["n_eff"],
        requires_reviewer=mapping["requires_reviewer"],
        eligible=mapping["eligible"],
        created_at=mapping["created_at"],
        pearson_ic=_optional_float(mapping.get("pearson_ic")),
        rank_ic=_optional_float(mapping.get("rank_ic")),
        detectable_abs_ic=_optional_float(mapping.get("detectable_abs_ic")),
        bucket_rank_correlation=_optional_float(mapping.get("bucket_rank_correlation")),
        net_mean_lift=_optional_float(mapping.get("net_mean_lift")),
        observed_effect=_optional_float(mapping.get("observed_effect")),
        surrogate_gate_pass_count=_optional_int(mapping.get("surrogate_gate_pass_count")),
        surrogate_run_count=_optional_int(mapping.get("surrogate_run_count")),
        outcome_label_type=_optional_str(mapping.get("outcome_label_type")),
    )


def _validate_main_effect_lane(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    """Require the IC diagnostics for a main_effect record (UNCHANGED contract)."""

    issues: list[ValidationIssue] = []
    for field in ("pearson_ic", "rank_ic", "bucket_rank_correlation"):
        value = mapping.get(field)
        if value is None:
            issues.append(_missing_lane_field(field, "main_effect IC diagnostic"))
            continue
        if not math.isfinite(float(value)):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_numeric_value",
                    message=f"SignalPendingReviewerRecord.{field} must be a finite number",
                    expected="finite number",
                    actual=str(value),
                )
            )
    detectable_raw = mapping.get("detectable_abs_ic")
    if detectable_raw is None:
        issues.append(_missing_lane_field("detectable_abs_ic", "main_effect IC diagnostic"))
    else:
        detectable = float(detectable_raw)
        if not math.isfinite(detectable) or detectable <= 0:
            issues.append(
                ValidationIssue(
                    field="detectable_abs_ic",
                    code="invalid_detectable_floor",
                    message=(
                        "SignalPendingReviewerRecord.detectable_abs_ic must be a positive float"
                    ),
                    expected="finite number > 0",
                    actual=str(detectable_raw),
                )
            )
    return issues


def _validate_setup_lane(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    """Require the setup-lane evidence; the IC fields must stay None."""

    issues: list[ValidationIssue] = []
    net_lift_raw = mapping.get("net_mean_lift")
    if net_lift_raw is None:
        issues.append(_missing_lane_field("net_mean_lift", "setup-lane net excursion lift"))
    elif not math.isfinite(float(net_lift_raw)):
        issues.append(
            ValidationIssue(
                field="net_mean_lift",
                code="invalid_numeric_value",
                message="SignalPendingReviewerRecord.net_mean_lift must be a finite number",
                expected="finite number",
                actual=str(net_lift_raw),
            )
        )
    if not str(mapping.get("outcome_label_type") or "").strip():
        issues.append(
            _missing_lane_field("outcome_label_type", "setup-lane outcome label type")
        )
    for field in SIGNAL_PENDING_REVIEWER_RECORD_IC_FIELDS:
        if mapping.get(field) is not None:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="ic_field_not_allowed_for_setup_lane",
                    message=(
                        f"SignalPendingReviewerRecord.{field} must be None for a "
                        "context_not_equal_trigger record (the setup lane has no IC)"
                    ),
                    expected="None",
                    actual=str(mapping.get(field)),
                )
            )
    return issues


def _missing_lane_field(field: str, description: str) -> ValidationIssue:
    return ValidationIssue(
        field=field,
        code="missing_lane_field",
        message=f"SignalPendingReviewerRecord.{field} is required ({description})",
        expected="present non-null value",
        actual="missing",
    )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


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
    "SIGNAL_PENDING_REVIEWER_RECORD_ALLOWED_FIELDS",
    "SIGNAL_PENDING_REVIEWER_RECORD_IC_FIELDS",
    "SIGNAL_PENDING_REVIEWER_RECORD_REQUIRED_FIELDS",
    "SIGNAL_PENDING_REVIEWER_RECORD_SETUP_FIELDS",
    "SIGNAL_PENDING_REVIEWER_STATUS",
    "STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER",
    "STUDY_KIND_MAIN_EFFECT",
    "SignalPendingReviewerRecord",
    "create_signal_pending_reviewer_record",
    "validate_signal_pending_reviewer_record",
]
