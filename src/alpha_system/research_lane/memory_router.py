"""Verdict-to-memory routing for the idea-to-verdict loop."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from alpha_system.governance.idea_draft import IdeaDraft, validate_idea_draft
from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaReasonCategory,
    create_rejected_idea_record,
)
from alpha_system.governance.requeue import REQUEUE_REASON, validate_requeued_verdict_record
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.signal_pending_reviewer import (
    create_signal_pending_reviewer_record,
)
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
)
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    validate_optional_verdict_reason_code,
    validate_verdict_reason_code,
)

MEMORY_ROUTER_SCHEMA = "alpha_system.research_lane.memory_router.v1"
ROUTE_REJECT = "graveyard"
ROUTE_REQUEUE = "requeue"
ROUTE_SIGNAL_SHELF = "reviewer_pending_shelf"
ROUTE_PROMOTION_REVIEW = "reviewer_gated_promotion"
ALLOWED_MEMORY_VERDICTS = frozenset({"REJECT", "DATA_GAP", "INCONCLUSIVE", "WATCH", "CANDIDATE"})
_REQUEUE_VERDICTS = frozenset({"DATA_GAP", "INCONCLUSIVE"})
_PROMOTION_VERDICTS = frozenset({"WATCH", "CANDIDATE"})
_DEFAULT_REVIEWER = "alpha_idea_run"


@dataclass(frozen=True, slots=True)
class MemoryRouteResult:
    """Value-free result of routing a governed verdict to memory."""

    verdict: str
    action: str
    record_type: str
    memory_record: Mapping[str, JsonValue]
    exploratory_refusal: Mapping[str, JsonValue]
    alpha_spec_id: str
    promotion_eligible: bool = False
    probe_spent: bool = False

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema": MEMORY_ROUTER_SCHEMA,
            "verdict": self.verdict,
            "action": self.action,
            "record_type": self.record_type,
            "alpha_spec_id": self.alpha_spec_id,
            "promotion_eligible": self.promotion_eligible,
            "probe_spent": self.probe_spent,
            "exploratory_refusal": dict(self.exploratory_refusal),
            "memory_record": dict(self.memory_record),
        }


def route_verdict_to_memory(
    verdict: str | Mapping[str, Any],
    idea_draft: IdeaDraft | Mapping[str, Any],
    readout: Mapping[str, Any],
    *,
    reviewer_verdict_id: str | None = None,
    evidence_bundle_id: str | None = None,
    trial_ledger_refs: Sequence[str] = (),
    reviewer: str = _DEFAULT_REVIEWER,
    created_at: str | None = None,
    report_ref: str | None = None,
    prior_power_estimate: float = 0.0,
    new_power_estimate: float = 0.0,
    data_accrued_months: int = 0,
    reason_code: VerdictReasonCode | str | None = None,
    rationale: str | None = None,
    warnings: Sequence[str] = (),
    probe_spent: bool = False,
) -> MemoryRouteResult:
    """Route one governed verdict to a value-free memory action.

    The router exercises the existing exploratory-promotion guard before any
    memory record is created. It does not persist records, mint reviewer verdicts,
    or write survivor libraries.
    """

    idea = _coerce_idea_draft(idea_draft)
    readout_payload = dict(require_mapping(readout, object_name="fast readout"))
    _require_promotion_ineligible(readout_payload)
    exploratory_refusal = _confirm_exploratory_refusal(readout_payload)

    verdict_payload = _coerce_verdict_payload(verdict, reason_code=reason_code)
    normalized_verdict = verdict_payload["verdict"]
    timestamp = created_at or _utc_now_seconds()

    if normalized_verdict == "REJECT":
        return _route_reject(
            idea,
            verdict_payload,
            readout_payload,
            exploratory_refusal=exploratory_refusal,
            reviewer=reviewer,
            created_at=timestamp,
            report_ref=report_ref,
        )
    if (
        normalized_verdict == "INCONCLUSIVE"
        and verdict_payload.get("reason_code")
        == VerdictReasonCode.SIGNAL_PENDING_REVIEWER.value
    ):
        # A well-powered main_effect probe that resolved a detectable IC. The
        # primary verdict stays INCONCLUSIVE (a non-promoting verdict in the
        # closed taxonomy); the signal is preserved on a reviewer-pending shelf
        # so it is not buried in a generic requeue. The machine never promotes.
        return _route_signal_pending_reviewer(
            idea,
            verdict_payload,
            readout_payload,
            exploratory_refusal=exploratory_refusal,
            created_at=timestamp,
            report_ref=report_ref,
        )
    if normalized_verdict in _REQUEUE_VERDICTS:
        # DATA_GAP (missing substrate) and INCONCLUSIVE (ran but underpowered / no
        # establishable effect) both route to a reason-coded requeue (revisit when
        # data/power improves); the honest verdict label is preserved on the result.
        return _route_requeue(
            idea,
            verdict_payload,
            readout_payload,
            exploratory_refusal=exploratory_refusal,
            created_at=timestamp,
            report_ref=report_ref,
            prior_power_estimate=prior_power_estimate,
            new_power_estimate=new_power_estimate,
            data_accrued_months=data_accrued_months,
            requeue_verdict=normalized_verdict,
        )
    if normalized_verdict in _PROMOTION_VERDICTS:
        return _route_promotion_review(
            idea,
            verdict_payload,
            readout_payload,
            exploratory_refusal=exploratory_refusal,
            reviewer_verdict_id=reviewer_verdict_id,
            evidence_bundle_id=evidence_bundle_id,
            trial_ledger_refs=trial_ledger_refs,
            created_at=timestamp,
            warnings=warnings,
            probe_spent=probe_spent,
        )
    raise AssertionError(f"unhandled memory verdict: {normalized_verdict}")


def _route_reject(
    idea: IdeaDraft,
    verdict: Mapping[str, Any],
    readout: Mapping[str, Any],
    *,
    exploratory_refusal: Mapping[str, JsonValue],
    reviewer: str,
    created_at: str,
    report_ref: str | None,
) -> MemoryRouteResult:
    alpha_spec_id = _require_alpha_spec_id(idea)
    record = create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=alpha_spec_id,
        reason_category=_rejection_category(verdict.get("reason_code")),
        evidence_references=[_evidence_reference(readout, report_ref=report_ref)],
        duplicate_links=[_duplicate_reference(readout)],
        leakage_cost_weakness_notes=[_rationale(verdict)],
        reviewer=reviewer,
        created_at=created_at,
    )
    return MemoryRouteResult(
        verdict="REJECT",
        action=ROUTE_REJECT,
        record_type="RejectedIdeaRecord",
        memory_record=record.to_dict(),
        exploratory_refusal=exploratory_refusal,
        alpha_spec_id=alpha_spec_id,
        promotion_eligible=False,
        probe_spent=False,
    )


def _route_requeue(
    idea: IdeaDraft,
    verdict: Mapping[str, Any],
    readout: Mapping[str, Any],
    *,
    exploratory_refusal: Mapping[str, JsonValue],
    created_at: str,
    report_ref: str | None,
    prior_power_estimate: float,
    new_power_estimate: float,
    data_accrued_months: int,
    requeue_verdict: str = "DATA_GAP",
) -> MemoryRouteResult:
    alpha_spec_id = _require_alpha_spec_id(idea)
    record = validate_requeued_verdict_record(
        {
            "original_verdict_ref": _verdict_reference(
                alpha_spec_id,
                readout,
                report_ref=report_ref,
                verdict=verdict,
            ),
            "requeue_reason": REQUEUE_REASON,
            "prior_power_estimate": prior_power_estimate,
            "new_power_estimate": new_power_estimate,
            "data_accrued_months": data_accrued_months,
            "eligible": False,
            "created_at": created_at,
        }
    )
    return MemoryRouteResult(
        verdict=requeue_verdict,
        action=ROUTE_REQUEUE,
        record_type="RequeuedVerdictRecord",
        memory_record=record.to_dict(),
        exploratory_refusal=exploratory_refusal,
        alpha_spec_id=alpha_spec_id,
        promotion_eligible=False,
        probe_spent=False,
    )


def _route_signal_pending_reviewer(
    idea: IdeaDraft,
    verdict: Mapping[str, Any],
    readout: Mapping[str, Any],
    *,
    exploratory_refusal: Mapping[str, JsonValue],
    created_at: str,
    report_ref: str | None,
) -> MemoryRouteResult:
    alpha_spec_id = _require_alpha_spec_id(idea)
    quality = _main_effect_quality_summary(readout)
    record = create_signal_pending_reviewer_record(
        alpha_spec_id_or_hypothesis_id=alpha_spec_id,
        original_verdict_ref=_verdict_reference(
            alpha_spec_id, readout, report_ref=report_ref, verdict=verdict
        ),
        factor_id=_main_effect_factor_id(readout),
        slice_id=_main_effect_slice_id(readout),
        pearson_ic=_required_float(quality.get("pearson_ic"), field="pearson_ic"),
        rank_ic=_required_float(quality.get("rank_ic"), field="rank_ic"),
        n_eff=_required_int(quality.get("ic_power_n_eff"), field="ic_power_n_eff"),
        detectable_abs_ic=_required_float(
            quality.get("ic_power_mde_abs_ic"), field="ic_power_mde_abs_ic"
        ),
        bucket_rank_correlation=_required_float(
            quality.get("bucket_rank_correlation"), field="bucket_rank_correlation"
        ),
        created_at=created_at,
    )
    return MemoryRouteResult(
        verdict="INCONCLUSIVE",
        action=ROUTE_SIGNAL_SHELF,
        record_type="SignalPendingReviewerRecord",
        memory_record=record.to_dict(),
        exploratory_refusal=exploratory_refusal,
        alpha_spec_id=alpha_spec_id,
        promotion_eligible=False,
        probe_spent=False,
    )


def _main_effect_quality_summary(readout: Mapping[str, Any]) -> Mapping[str, Any]:
    inner = readout.get("readout")
    if isinstance(inner, Mapping):
        report = inner.get("factor_diagnostics_report")
        if isinstance(report, Mapping):
            quality = report.get("quality_summary")
            if isinstance(quality, Mapping):
                return quality
    raise GovernanceValidationError(
        ValidationIssue(
            field="readout.factor_diagnostics_report.quality_summary",
            code="missing_main_effect_quality_summary",
            message="signal-shelf routing requires a main_effect IC quality summary",
            expected="factor_diagnostics_report.quality_summary mapping",
            actual="missing",
        )
    )


def _main_effect_factor_id(readout: Mapping[str, Any]) -> str:
    slice_spec = readout.get("slice_spec")
    if isinstance(slice_spec, Mapping):
        for feature in slice_spec.get("feature_inputs") or ():
            if isinstance(feature, Mapping) and str(feature.get("role")) == "factor":
                factor_id = feature.get("factor_id")
                if factor_id:
                    return str(factor_id)
    mechanism = readout.get("mechanism_card")
    if isinstance(mechanism, Mapping):
        required = mechanism.get("required_features") or ()
        if required:
            return str(required[0])
    return "unknown_factor"


def _main_effect_slice_id(readout: Mapping[str, Any]) -> str:
    slice_spec = readout.get("slice_spec")
    if isinstance(slice_spec, Mapping):
        slice_id = slice_spec.get("slice_id")
        if slice_id:
            return str(slice_id)
    return "unknown_slice"


def _required_float(value: Any, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float("nan")
    if value is None or isinstance(value, bool) or number != number:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="missing_main_effect_metric",
                message=f"signal-shelf routing requires a finite {field}",
                expected="finite number",
                actual=str(value),
            )
        )
    return number


def _required_int(value: Any, *, field: str) -> int:
    if value is None or isinstance(value, bool):
        value = None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="missing_main_effect_metric",
                message=f"signal-shelf routing requires an integer {field}",
                expected="integer",
                actual=str(value),
            )
        ) from None


def _route_promotion_review(
    idea: IdeaDraft,
    verdict: Mapping[str, Any],
    readout: Mapping[str, Any],
    *,
    exploratory_refusal: Mapping[str, JsonValue],
    reviewer_verdict_id: str | None,
    evidence_bundle_id: str | None,
    trial_ledger_refs: Sequence[str],
    created_at: str,
    warnings: Sequence[str],
    probe_spent: bool,
) -> MemoryRouteResult:
    alpha_spec_id = _require_alpha_spec_id(idea)
    missing = [
        field
        for field, value in (
            ("reviewer_verdict_id", reviewer_verdict_id),
            ("evidence_bundle_id", evidence_bundle_id),
        )
        if not value
    ]
    if not trial_ledger_refs:
        missing.append("trial_ledger_refs")
    if missing:
        raise GovernanceValidationError(
            [
                ValidationIssue(
                    field=field,
                    code="missing_reviewer_gated_promotion_input",
                    message=f"{field} is required for WATCH/CANDIDATE memory routing",
                    expected="reviewer-gated promotion input",
                    actual="missing",
                )
                for field in missing
            ]
        )
    decision = verdict["verdict"]
    record = create_promotion_decision(
        alpha_spec_id=alpha_spec_id,
        evidence_bundle_id=str(evidence_bundle_id),
        trial_ledger_refs=[str(ref) for ref in trial_ledger_refs],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=decision,
        decision=PromotionDecisionOutcome(decision),
        rationale=_rationale(verdict),
        reviewer_verdict_id=str(reviewer_verdict_id),
        warnings=list(warnings)
        or ["Reviewer-gated research memory routing; not an automatic promotion."],
        timestamp=created_at,
        reason_code=verdict.get("reason_code"),
    )
    return MemoryRouteResult(
        verdict=decision,
        action=ROUTE_PROMOTION_REVIEW,
        record_type="PromotionDecision",
        memory_record=record.to_dict(),
        exploratory_refusal=exploratory_refusal,
        alpha_spec_id=alpha_spec_id,
        promotion_eligible=False,
        probe_spent=probe_spent,
    )


def _coerce_idea_draft(value: IdeaDraft | Mapping[str, Any]) -> IdeaDraft:
    if isinstance(value, IdeaDraft):
        return validate_idea_draft(value.to_dict())
    if isinstance(value, Mapping):
        return validate_idea_draft(value)
    raise GovernanceValidationError(
        ValidationIssue(
            field="idea_draft",
            code="invalid_idea_draft_type",
            message="idea_draft must be an IdeaDraft or mapping",
            expected="IdeaDraft or mapping",
            actual=type(value).__name__,
        )
    )


def _coerce_verdict_payload(
    value: str | Mapping[str, Any],
    *,
    reason_code: VerdictReasonCode | str | None,
) -> dict[str, Any]:
    if isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = {"verdict": value}
    raw_verdict = str(payload.get("verdict") or "").strip().upper()
    if raw_verdict not in ALLOWED_MEMORY_VERDICTS:
        raise GovernanceValidationError(
            ValidationIssue(
                field="verdict",
                code="unsupported_memory_verdict",
                message="verdict is not routable by the V0 memory router",
                expected=" | ".join(sorted(ALLOWED_MEMORY_VERDICTS)),
                actual=str(payload.get("verdict")),
            )
        )
    payload["verdict"] = raw_verdict
    raw_reason = reason_code if reason_code is not None else payload.get("reason_code")
    if raw_reason is None:
        raw_reason = _default_reason(raw_verdict)
    payload["reason_code"] = validate_verdict_reason_code(raw_reason).value
    return payload


def _confirm_exploratory_refusal(readout: Mapping[str, Any]) -> dict[str, JsonValue]:
    try:
        reject_exploratory_promotion_artifact(readout, field="readout")
    except GovernanceValidationError as exc:
        refusal_issues = [
            issue for issue in exc.issues if issue.code == EXPLORATORY_PROMOTION_REFUSAL_CODE
        ]
        if refusal_issues:
            return {
                "status": "refused",
                "issue_codes": [issue.code for issue in refusal_issues],
                "fields": [issue.field for issue in refusal_issues],
            }
        raise
    raise GovernanceValidationError(
        ValidationIssue(
            field="readout",
            code="exploratory_refusal_missing",
            message="EXPLORATORY readout was not refused by the promotion guard",
            expected="reject_exploratory_promotion_artifact failure",
            actual="accepted",
        )
    )


def _require_promotion_ineligible(readout: Mapping[str, Any]) -> None:
    if readout.get("promotion_eligible") is False:
        return
    raise GovernanceValidationError(
        ValidationIssue(
            field="readout.promotion_eligible",
            code="unexpected_promotion_eligible_readout",
            message="exploratory memory routing requires promotion_eligible=false",
            expected="False",
            actual=str(readout.get("promotion_eligible")),
        )
    )


def _require_alpha_spec_id(idea: IdeaDraft) -> str:
    if idea.alpha_spec_id:
        return idea.alpha_spec_id
    raise GovernanceValidationError(
        ValidationIssue(
            field="idea_draft.alpha_spec_id",
            code="missing_alpha_spec_id",
            message="REJECT/DATA_GAP/WATCH/CANDIDATE routing requires the minted AlphaSpec id",
            expected="AlphaSpec id",
            actual="missing",
        )
    )


def _rejection_category(reason_code: Any) -> RejectedIdeaReasonCategory:
    reason = validate_optional_verdict_reason_code(reason_code)
    if reason is VerdictReasonCode.DUPLICATE_EXPOSURE:
        return RejectedIdeaReasonCategory.DUPLICATE
    if reason is VerdictReasonCode.LEAKAGE_BLOCKED:
        return RejectedIdeaReasonCategory.LEAKAGE
    if reason is VerdictReasonCode.COST_FRAGILE:
        return RejectedIdeaReasonCategory.COST
    if reason in {
        VerdictReasonCode.UNDERPOWERED,
        VerdictReasonCode.SUBSTRATE_GAP,
        VerdictReasonCode.DATA_QUALITY,
        VerdictReasonCode.BBO_PROXY_LIMITATION,
        VerdictReasonCode.WELL_POWERED_NULL,
    }:
        return RejectedIdeaReasonCategory.WEAK_EVIDENCE
    return RejectedIdeaReasonCategory.OTHER


def _evidence_reference(readout: Mapping[str, Any], *, report_ref: str | None) -> str:
    if report_ref:
        return f"report:{report_ref}"
    readout_id = readout.get("readout_id")
    if readout_id:
        return f"readout:{readout_id}"
    return "readout:exploratory_memory_route"


def _verdict_reference(
    alpha_spec_id: str,
    readout: Mapping[str, Any],
    *,
    report_ref: str | None,
    verdict: Mapping[str, Any],
) -> str:
    if report_ref:
        return f"report:{report_ref}"
    if readout.get("readout_id"):
        return f"readout:{readout['readout_id']}"
    return f"{alpha_spec_id}:{verdict['verdict']}"


def _duplicate_reference(readout: Mapping[str, Any]) -> str:
    mechanism = readout.get("mechanism_card")
    if isinstance(mechanism, Mapping):
        duplicate = mechanism.get("duplicate_exposure")
        if isinstance(duplicate, Mapping):
            family_id = duplicate.get("family_id")
            status = duplicate.get("status")
            variant_id = duplicate.get("variant_id")
            parts = [
                part
                for part in (
                    f"family={family_id}" if family_id else None,
                    f"status={status}" if status else None,
                    f"variant={variant_id}" if variant_id else None,
                )
                if part
            ]
            if parts:
                return "duplicate_exposure:" + ";".join(parts)
    return "duplicate_exposure:checked_or_not_declared"


def _rationale(verdict: Mapping[str, Any]) -> str:
    for key in ("why", "rationale", "next_action"):
        value = verdict.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"Governed {verdict['verdict']} verdict routed by alpha idea run."


def _default_reason(verdict: str) -> VerdictReasonCode:
    if verdict == "REJECT":
        return VerdictReasonCode.DATA_QUALITY
    if verdict == "DATA_GAP":
        return VerdictReasonCode.SUBSTRATE_GAP
    if verdict == "WATCH":
        return VerdictReasonCode.REGIME_UNSTABLE
    return VerdictReasonCode.UNDERPOWERED


def _utc_now_seconds() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "ALLOWED_MEMORY_VERDICTS",
    "MEMORY_ROUTER_SCHEMA",
    "MemoryRouteResult",
    "route_verdict_to_memory",
]
