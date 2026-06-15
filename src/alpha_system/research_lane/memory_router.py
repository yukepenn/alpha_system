"""Verdict-to-memory routing for the idea-to-verdict loop."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.governance.family_fdr_correction import (
    DEFAULT_FDR_ALPHA,
    DEFAULT_FDR_METHOD,
    REASON_FAMILY_FDR_NOT_CLEARED,
    REASON_RESOLUTION_INADEQUATE,
    FamilyFdrVerdict,
    correct_family,
    surrogate_p_upper_bound,
)
from alpha_system.governance.family_fdr_ledger import (
    FamilyFdrLedger,
    create_family_fdr_ledger_record,
    family_batch_key,
    utc_now_iso,
)
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
    STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER,
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
from alpha_system.research_lane.fast_readout import (
    FastReadout,
    FastReadoutContractError,
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
# Provisional family-FDR requeue reasons (mirror the Stage-A REASON_* vocabulary).
FAMILY_FDR_REQUEUE_REASONS = frozenset(
    {REASON_FAMILY_FDR_NOT_CLEARED, REASON_RESOLUTION_INADEQUATE}
)


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
    family_fdr_ledger_path: str | Path | None = None,
    family_fdr_alpha: float = DEFAULT_FDR_ALPHA,
    family_fdr_method: str = DEFAULT_FDR_METHOD,
) -> MemoryRouteResult:
    """Route one governed verdict to a value-free memory action.

    The router exercises the existing exploratory-promotion guard before any
    memory record is created. It does not persist records, mint reviewer verdicts,
    or write survivor libraries.

    When ``family_fdr_ledger_path`` is supplied and the verdict is a setup-lane
    (``context_not_equal_trigger``) SIGNAL_PENDING_REVIEWER, the family-wise
    multiplicity gate runs (CROSS_IDEA_FDR_BUDGET_V1 Stage B): this idea's per-test
    surrogate p is recorded into the append-only ``FamilyFdrLedger`` keyed by its
    co-mined batch ``(alpha_spec_id, slice_id, family_id)``, all sibling records are
    re-corrected together, and this idea routes to the reviewer shelf only if the
    family-corrected verdict is eligible; otherwise it routes to requeue. The
    correction is PROVISIONAL and accumulating -- siblings arrive across runs, so the
    gate refines as the batch fills (see the Stage-B no-retro-mutation note). The
    machine still NEVER auto-promotes. main_effect signal routing is unchanged
    (it has no surrogate-p in the same sense -- main_effect family-FDR is follow-up).
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
            prior_power_estimate=prior_power_estimate,
            new_power_estimate=new_power_estimate,
            data_accrued_months=data_accrued_months,
            family_fdr_ledger_path=family_fdr_ledger_path,
            family_fdr_alpha=family_fdr_alpha,
            family_fdr_method=family_fdr_method,
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
    prior_power_estimate: float = 0.0,
    new_power_estimate: float = 0.0,
    data_accrued_months: int = 0,
    family_fdr_ledger_path: str | Path | None = None,
    family_fdr_alpha: float = DEFAULT_FDR_ALPHA,
    family_fdr_method: str = DEFAULT_FDR_METHOD,
) -> MemoryRouteResult:
    alpha_spec_id = _require_alpha_spec_id(idea)
    original_verdict_ref = _verdict_reference(
        alpha_spec_id, readout, report_ref=report_ref, verdict=verdict
    )
    # A SIGNAL_PENDING_REVIEWER readout is a RECORDED probe (main_effect or setup);
    # parse it through the typed FastReadout contract once and read typed attributes
    # (no recursive searches, no mirror parsers, single canonical n_eff accessor).
    parsed = _parse_fast_readout(readout)
    if parsed.study_kind == STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER:
        # CROSS_IDEA_FDR_BUDGET_V1 Stage B: when a family-FDR ledger is supplied, the
        # setup-lane signal must clear the family-wise multiplicity gate before it may
        # reach the reviewer shelf. A signal that passed its single surrogate test but
        # fails the family correction (or whose surrogate run_count cannot resolve the
        # corrected threshold) routes to requeue -- NOT graveyard -- because the
        # correction is provisional and may clear as the batch fills or with more
        # surrogates (mirrors the reviewer's REWORK prescription).
        family_verdict = _evaluate_family_fdr_gate(
            idea,
            readout,
            parsed,
            alpha_spec_id=alpha_spec_id,
            slice_id=_main_effect_slice_id(readout),
            family_fdr_ledger_path=family_fdr_ledger_path,
            family_fdr_alpha=family_fdr_alpha,
            family_fdr_method=family_fdr_method,
            created_at=created_at,
        )
        if family_verdict is not None and not family_verdict.eligible:
            return _route_family_fdr_requeue(
                idea,
                verdict,
                readout,
                exploratory_refusal=exploratory_refusal,
                created_at=created_at,
                report_ref=report_ref,
                prior_power_estimate=prior_power_estimate,
                new_power_estimate=new_power_estimate,
                data_accrued_months=data_accrued_months,
                family_verdict=family_verdict,
            )
        record = _setup_lane_signal_record(
            readout,
            parsed,
            alpha_spec_id=alpha_spec_id,
            original_verdict_ref=original_verdict_ref,
            created_at=created_at,
        )
        family_fdr_attachment = (
            _family_fdr_attachment(family_verdict) if family_verdict is not None else None
        )
    else:
        # main_effect path: typed IC quality summary. The family-FDR gate is setup-lane
        # only (main_effect has no surrogate-p in the same sense -- follow-up work needs
        # an IC p-value definition that does not exist yet), so main_effect routing is
        # UNCHANGED here.
        quality = parsed.ic_quality_summary
        if quality is None:
            raise _missing_main_effect_quality_summary_error()
        record = create_signal_pending_reviewer_record(
            alpha_spec_id_or_hypothesis_id=alpha_spec_id,
            original_verdict_ref=original_verdict_ref,
            factor_id=_main_effect_factor_id(readout),
            slice_id=_main_effect_slice_id(readout),
            pearson_ic=_required_float(quality.pearson_ic, field="pearson_ic"),
            rank_ic=_required_float(quality.rank_ic, field="rank_ic"),
            n_eff=_required_int(quality.ic_power_n_eff, field="ic_power_n_eff"),
            detectable_abs_ic=_required_float(
                quality.ic_power_mde_abs_ic, field="ic_power_mde_abs_ic"
            ),
            bucket_rank_correlation=_required_float(
                quality.bucket_rank_correlation, field="bucket_rank_correlation"
            ),
            created_at=created_at,
        )
        family_fdr_attachment = None
    memory_record = dict(record.to_dict())
    if family_fdr_attachment is not None:
        # Attach the corrected verdict so the independent reviewer sees the
        # family-wise multiplicity context (method, alpha_fw, corrected_threshold,
        # family_size, p_value) alongside the shelved signal.
        memory_record["family_fdr_verdict"] = family_fdr_attachment
    return MemoryRouteResult(
        verdict="INCONCLUSIVE",
        action=ROUTE_SIGNAL_SHELF,
        record_type="SignalPendingReviewerRecord",
        memory_record=memory_record,
        exploratory_refusal=exploratory_refusal,
        alpha_spec_id=alpha_spec_id,
        promotion_eligible=False,
        probe_spent=False,
    )


def _evaluate_family_fdr_gate(
    idea: IdeaDraft,
    readout: Mapping[str, Any],
    parsed: FastReadout,
    *,
    alpha_spec_id: str,
    slice_id: str,
    family_fdr_ledger_path: str | Path | None,
    family_fdr_alpha: float,
    family_fdr_method: str,
    created_at: str,
) -> FamilyFdrVerdict | None:
    """Record this setup-lane idea into the family-FDR ledger and correct its batch.

    Returns this idea's ``FamilyFdrVerdict`` from the (provisional, accumulating)
    re-correction of all sibling records sharing its co-mined batch key, or ``None``
    when no ledger path is supplied (the gate is opt-in; callers that do not wire a
    ledger keep the pre-Stage-B always-shelf behavior).

    The correction is monotonically refined: siblings arrive across separate
    ``alpha idea run`` invocations, so the ledger is the accumulator and the gate
    applies at routing time. Earlier-shelved siblings are NOT retroactively
    de-shelved (no retro-mutation of append-only memory) -- a future batch-close
    re-evaluation could tighten that; see the Stage-B design note.
    """

    if family_fdr_ledger_path is None:
        return None
    gate = parsed.surrogate_fdr_gate
    if gate is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="readout.surrogate_fdr_gate",
                code="missing_setup_lane_gate",
                message="setup-lane family-FDR routing requires a surrogate_fdr_gate",
                expected="surrogate-FDR gate mapping",
                actual="missing",
            )
        )
    # Per-test surrogate p upper bound from the typed gate (reuse the Stage-A
    # primitive; no string-spelunking of the readout dict).
    p_value = surrogate_p_upper_bound(gate.gate_pass_count, gate.run_count)
    family_id = _family_id_for_batch(readout, alpha_spec_id=alpha_spec_id)
    idea_key = _family_fdr_idea_key(idea, readout, alpha_spec_id=alpha_spec_id)

    ledger = FamilyFdrLedger(family_fdr_ledger_path)
    # Idempotent append of THIS idea's per-test outcome under a provisional verdict;
    # the binding verdict is computed below from the full batch.
    this_record = create_family_fdr_ledger_record(
        family_id=family_id,
        slice_id=slice_id,
        alpha_spec_id=alpha_spec_id,
        idea_key=idea_key,
        p_value=p_value,
        run_count=gate.run_count,
        verdict=_provisional_self_verdict(
            idea_key=idea_key,
            p_value=p_value,
            run_count=gate.run_count,
            alpha_fw=family_fdr_alpha,
            method=family_fdr_method,
        ),
        created_at=created_at or utc_now_iso(),
    )
    ledger.append_records((this_record,))

    # Load ALL sibling records for the same batch key and re-correct together. The
    # latest p/run for each idea_key wins (a re-run idea refines its own entry).
    batch_key = family_batch_key(
        alpha_spec_id=alpha_spec_id, slice_id=slice_id, family_id=family_id
    )
    entries = _batch_entries(ledger, batch_key, this_idea_key=idea_key, this_record=this_record)
    verdicts = correct_family(entries, alpha_fw=family_fdr_alpha, method=family_fdr_method)
    for verdict in verdicts:
        if verdict.idea_key == idea_key:
            return verdict
    # Defensive: the just-appended idea must be in its own batch.
    raise GovernanceValidationError(
        ValidationIssue(
            field="family_fdr",
            code="family_fdr_self_missing",
            message="family-FDR correction did not return this idea's verdict",
            expected=idea_key,
            actual="absent",
        )
    )


def _provisional_self_verdict(
    *,
    idea_key: str,
    p_value: float,
    run_count: int,
    alpha_fw: float,
    method: str,
) -> FamilyFdrVerdict:
    """Correct THIS idea alone (a family-of-one) for its provisional ledger record.

    The binding cross-idea verdict is recomputed over the full batch after append;
    this provisional self-correction only seeds the append-only record (each record
    carries a verdict by the Stage-A schema) and is monotonically superseded as the
    batch fills.
    """

    (verdict,) = correct_family(
        ({"idea_key": idea_key, "p_value": p_value, "run_count": run_count},),
        alpha_fw=alpha_fw,
        method=method,
    )
    return verdict


def _batch_entries(
    ledger: FamilyFdrLedger,
    batch_key: str,
    *,
    this_idea_key: str,
    this_record,
) -> tuple[dict[str, Any], ...]:
    """Collect one (idea_key, p_value, run_count) entry per idea in the batch.

    The most recent record per idea_key wins so a re-run idea refines its own entry
    rather than duplicating it (correct_family forbids duplicate idea_keys).
    """

    latest: dict[str, dict[str, Any]] = {}
    for record in ledger.load_records():
        if record.batch_key != batch_key:
            continue
        latest[record.idea_key] = {
            "idea_key": record.idea_key,
            "p_value": record.p_value,
            "run_count": record.run_count,
        }
    # Ensure this idea is present even if the load races behind the append.
    latest[this_idea_key] = {
        "idea_key": this_record.idea_key,
        "p_value": this_record.p_value,
        "run_count": this_record.run_count,
    }
    return tuple(latest[key] for key in sorted(latest))


def _family_fdr_attachment(verdict: FamilyFdrVerdict) -> dict[str, JsonValue]:
    """Value-free family-FDR context attached to a shelved setup signal."""

    return {
        "method": verdict.method,
        "alpha_fw": verdict.alpha_fw,
        "corrected_threshold": verdict.corrected_threshold,
        "family_size": verdict.family_size,
        "p_value": verdict.p_value,
        "rejected_null": verdict.rejected_null,
        "resolution_adequate": verdict.resolution_adequate,
        "eligible": verdict.eligible,
        "reason": verdict.reason,
        "provisional": True,
    }


def _route_family_fdr_requeue(
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
    family_verdict: FamilyFdrVerdict,
) -> MemoryRouteResult:
    """Route a setup signal that failed the family-wise gate to a value-free requeue.

    Requeue (not graveyard) because the provisional correction may clear as the batch
    fills or with more surrogates. The Stage-A REASON_* constant is the value-free
    reason: ``family_fdr_not_cleared`` (corrected null not rejected) or
    ``surrogate_resolution_inadequate`` (run_count cannot resolve the corrected
    threshold). The honest verdict label stays INCONCLUSIVE.
    """

    result = _route_requeue(
        idea,
        verdict,
        readout,
        exploratory_refusal=exploratory_refusal,
        created_at=created_at,
        report_ref=report_ref,
        prior_power_estimate=prior_power_estimate,
        new_power_estimate=new_power_estimate,
        data_accrued_months=data_accrued_months,
        requeue_verdict="INCONCLUSIVE",
    )
    memory_record = dict(result.memory_record)
    memory_record["family_fdr_requeue_reason"] = _family_fdr_requeue_reason(family_verdict)
    memory_record["family_fdr_verdict"] = _family_fdr_attachment(family_verdict)
    return MemoryRouteResult(
        verdict=result.verdict,
        action=result.action,
        record_type=result.record_type,
        memory_record=memory_record,
        exploratory_refusal=result.exploratory_refusal,
        alpha_spec_id=result.alpha_spec_id,
        promotion_eligible=False,
        probe_spent=False,
    )


def _family_fdr_requeue_reason(verdict: FamilyFdrVerdict) -> str:
    """Map the corrected verdict to a value-free requeue reason.

    ``family_fdr_not_cleared`` when the corrected null is not rejected;
    ``surrogate_resolution_inadequate`` when the surrogate run_count cannot resolve
    the corrected threshold (reuses the Stage-A reason vocabulary; the
    resolution-inadequate path mirrors the reviewer's historical REWORK arithmetic).
    """

    if not verdict.rejected_null:
        return REASON_FAMILY_FDR_NOT_CLEARED
    return "surrogate_resolution_inadequate"


def _family_id_for_batch(readout: Mapping[str, Any], *, alpha_spec_id: str) -> str:
    """Resolve the co-mined family identity for the batch key.

    Prefer the declared ``mechanism_card.duplicate_exposure.family_id`` (the same
    family used by ``family_budget``). When no family is declared, the idea is its
    own singleton family keyed by its AlphaSpec id -- an honest family-of-one.
    """

    mechanism = readout.get("mechanism_card")
    if isinstance(mechanism, Mapping):
        duplicate = mechanism.get("duplicate_exposure")
        if isinstance(duplicate, Mapping):
            family_id = duplicate.get("family_id")
            if isinstance(family_id, str) and family_id.strip():
                return family_id.strip()
    return alpha_spec_id


def _family_fdr_idea_key(
    idea: IdeaDraft, readout: Mapping[str, Any], *, alpha_spec_id: str
) -> str:
    """Stable per-idea key INSIDE a co-mined batch.

    The batch key is ``(alpha_spec_id, slice_id, family_id)`` -- co-mined siblings
    share all three. The per-idea distinguisher within that batch is the mechanism
    id (each sibling is a distinct mechanism/variant), falling back to the hypothesis
    id and finally the AlphaSpec id for a singleton idea. This is what makes the 7
    sibling pa_setup ideas land in ONE batch rather than 7 batches of one.
    """

    if idea.mechanism_id:
        return idea.mechanism_id
    if idea.hypothesis_id:
        return idea.hypothesis_id
    return alpha_spec_id


def _setup_lane_signal_record(
    readout: Mapping[str, Any],
    parsed: FastReadout,
    *,
    alpha_spec_id: str,
    original_verdict_ref: str,
    created_at: str,
):
    """Build a context_not_equal_trigger signal-shelf record from the typed readout.

    The setup/path-outcome lane has no IC numbers; it carries a signed
    continuous-outcome ``mean_lift`` (``FastReadout.continuous_lift_summary``) plus
    the enriched surrogate-FDR gate (conditioned overlap-aware n_eff, observed effect,
    gate pass/run counts -- ``FastReadout.surrogate_fdr_gate``). ``FastReadout.n_eff``
    is the single canonical accessor (top-level power, falling back to the gate's
    conditioned_n_eff). The machine still NEVER promotes; this only routes the
    non-promoting signal to the reviewer shelf.
    """

    lift = parsed.continuous_lift_summary
    if lift is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="readout.continuous_outcome_mean_lift",
                code="missing_setup_lane_lift",
                message="setup-lane signal routing requires a continuous_outcome_mean_lift",
                expected="continuous-outcome mean_lift mapping",
                actual="missing",
            )
        )
    gate = parsed.surrogate_fdr_gate
    if gate is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="readout.surrogate_fdr_gate",
                code="missing_setup_lane_gate",
                message="setup-lane signal routing requires a surrogate_fdr_gate",
                expected="surrogate-FDR gate mapping",
                actual="missing",
            )
        )
    return create_signal_pending_reviewer_record(
        alpha_spec_id_or_hypothesis_id=alpha_spec_id,
        original_verdict_ref=original_verdict_ref,
        factor_id=_main_effect_factor_id(readout),
        slice_id=_main_effect_slice_id(readout),
        n_eff=parsed.n_eff,
        net_mean_lift=_required_float(lift.mean_lift, field="mean_lift"),
        outcome_label_type=_required_outcome_label_type(lift.outcome_label_type),
        observed_effect=gate.observed_effect,
        surrogate_gate_pass_count=gate.gate_pass_count,
        surrogate_run_count=gate.run_count,
        created_at=created_at,
        study_kind=STUDY_KIND_CONTEXT_NOT_EQUAL_TRIGGER,
    )


def _parse_fast_readout(readout: Mapping[str, Any]) -> FastReadout:
    """Parse a RECORDED signal readout through the typed contract.

    Surfaces drift loudly at the boundary (``FastReadoutContractError``) instead of a
    silent downstream ``.get()`` returning ``None``. Raised as a governance issue so
    the router's failure mode stays consistent with the rest of the seam.
    """

    try:
        return FastReadout.from_dict(readout)
    except FastReadoutContractError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="readout",
                code="invalid_fast_readout_contract",
                message=f"signal-shelf routing requires a contract-valid fast readout: {exc}",
                expected="FastReadout-parseable readout",
                actual="contract drift",
            )
        ) from exc


def _missing_main_effect_quality_summary_error() -> GovernanceValidationError:
    return GovernanceValidationError(
        ValidationIssue(
            field="readout.factor_diagnostics_report.quality_summary",
            code="missing_main_effect_quality_summary",
            message="signal-shelf routing requires a main_effect IC quality summary",
            expected="factor_diagnostics_report.quality_summary mapping",
            actual="missing",
        )
    )


def _required_outcome_label_type(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise GovernanceValidationError(
            ValidationIssue(
                field="outcome_label_type",
                code="missing_setup_lane_metric",
                message="setup-lane signal routing requires an outcome_label_type",
                expected="non-empty string",
                actual=str(value),
            )
        )
    return text


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
