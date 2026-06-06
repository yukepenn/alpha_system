from __future__ import annotations

import pytest

from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditReason,
    NoLookaheadRejectionCategory,
)
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState
from alpha_system.runtime.decisions import (
    REJECTION_REASON_CODES,
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    RuntimeDecisionStateError,
    RuntimeStopCondition,
    coerce_runtime_decision_state,
    normalize_bounded_grid_reasons,
    normalize_rejection_reason,
)
from alpha_system.runtime.entry_contract import RuntimeEntryReason, RuntimeEntryStatus
from alpha_system.runtime.grid import VariantBudget, validate_bounded_grid_request

EXPECTED_REASON_CODES = {
    "data_unavailable",
    "leakage_risk",
    "weak_diagnostics",
    "cost_fragile",
    "low_sample",
    "variant_budget_exceeded",
    "duplicate_exposure",
    "blocked_by_policy",
    "inconclusive",
}
PROHIBITED_MVP_STATES = {
    "ALPHA_VALIDATED",
    "FACTOR_PROMOTED",
    "STRATEGY_READY",
    "PORTFOLIO_READY",
    "LIVE_READY",
    "PAPER_READY",
    "PROFITABLE",
    "TRADABLE",
    "PRODUCTION_READY",
}


def test_terminal_decisions_require_visible_reasons() -> None:
    with pytest.raises(RuntimeDecisionStateError, match="require visible reasons"):
        RuntimeDecision(state=RuntimeDecisionState.REJECTED)

    with pytest.raises(RuntimeDecisionStateError, match="must not carry rejection reasons"):
        RuntimeDecision(
            state=RuntimeLifecycleState.PLAN_VALIDATED,
            reasons=(_reason(RuntimeDecisionState.REJECTED),),
        )

    decision = RuntimeDecision(
        state=StudyRunResultState.DIAGNOSTICS_FAILED,
        reasons=(_reason(RuntimeDecisionState.REJECTED),),
    )

    assert decision.state is RuntimeDecisionState.REJECTED
    assert decision.source_state == "DIAGNOSTICS_FAILED"
    assert decision.to_dict()["reasons"][0]["decision_state"] == "REJECTED"


def test_reason_codes_round_trip_through_value_free_payloads() -> None:
    assert REJECTION_REASON_CODES == EXPECTED_REASON_CODES
    assert {code.value for code in RejectionReasonCode} == EXPECTED_REASON_CODES

    for code in RejectionReasonCode:
        record = RejectionReasonRecord(
            code=code,
            message=f"{code.value} kept visible for runtime decision handling.",
            decision_state=RuntimeDecisionState.REJECTED,
            stage=RuntimeDecisionStage.DIAGNOSTICS,
            source_code=f"upstream_{code.value}",
            source_id=f"reason_{code.value}",
        )

        payload = record.to_dict()
        assert set(payload) <= {
            "code",
            "message",
            "decision_state",
            "stage",
            "source_code",
            "source_id",
        }
        assert "rows" not in str(payload).lower()
        assert "values" not in str(payload).lower()
        assert "parquet" not in str(payload).lower()
        assert RejectionReasonRecord.from_dict(payload) == record
        assert hash(record)


def test_upstream_reason_shapes_normalize_with_source_code_and_stage() -> None:
    run_reason = normalize_rejection_reason(
        RunRejectionReason(
            code="double_cost_fragility",
            message="Cost stress became fragile under the double-cost profile.",
        ),
        stage=RuntimeDecisionStage.COST_STRESS,
        decision_state=StudyRunResultState.REJECTED,
    )
    assert run_reason.code is RejectionReasonCode.COST_FRAGILE
    assert run_reason.source_code == "double_cost_fragility"
    assert run_reason.stage == "cost_stress"

    entry_reason = normalize_rejection_reason(
        RuntimeEntryReason(
            code="missing_target_dataset_version_id",
            message="Runtime entry requires an accepted DatasetVersion reference.",
            field="target_dataset_version_id",
            decision_state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected="dsv_ DatasetVersion id",
            actual="missing",
        )
    )
    assert entry_reason.code is RejectionReasonCode.DATA_UNAVAILABLE
    assert entry_reason.decision_state is RuntimeDecisionState.BLOCKED
    assert entry_reason.source_code == "missing_target_dataset_version_id"
    assert entry_reason.stage == "inputs"

    inconclusive_entry = normalize_rejection_reason(
        RuntimeEntryReason(
            code="dataset_scope_mismatch",
            message="Runtime entry dataset_scope did not match governance metadata.",
            field="dataset_scope",
            decision_state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            expected="governance StudyInputPack scope",
            actual="runtime request scope",
        )
    )
    assert inconclusive_entry.code is RejectionReasonCode.INCONCLUSIVE
    assert inconclusive_entry.decision_state is RuntimeDecisionState.INCONCLUSIVE

    audit_reason = normalize_rejection_reason(
        NoLookaheadAuditReason(
            code="feature_available_ts_after_decision_ts",
            category=NoLookaheadRejectionCategory.LEAKAGE_RISK,
            message="Feature availability timestamp occurs after the decision timestamp.",
            field="feature.available_ts",
            expected="available_ts <= decision_ts",
            actual="after decision timestamp",
        )
    )
    assert audit_reason.code is RejectionReasonCode.LEAKAGE_RISK
    assert audit_reason.decision_state is RuntimeDecisionState.REJECTED
    assert audit_reason.source_code == "feature_available_ts_after_decision_ts"
    assert audit_reason.stage == "no_lookahead_audit"

    grid_reasons = normalize_bounded_grid_reasons(_bounded_grid_budget_exceeded())
    assert len(grid_reasons) == 1
    assert grid_reasons[0].code is RejectionReasonCode.VARIANT_BUDGET_EXCEEDED
    assert grid_reasons[0].decision_state is RuntimeDecisionState.REJECTED
    assert grid_reasons[0].source_code == "variant_budget_exceeded"
    assert grid_reasons[0].stage == "bounded_grid"


def test_prohibited_mvp_states_are_not_constructible_or_reachable() -> None:
    state_values = {state.value for state in RuntimeDecisionState}
    assert state_values.isdisjoint(PROHIBITED_MVP_STATES)

    for prohibited_state in sorted(PROHIBITED_MVP_STATES):
        with pytest.raises(RuntimeDecisionStateError):
            coerce_runtime_decision_state(prohibited_state)
        with pytest.raises(RuntimeDecisionStateError):
            RuntimeDecision(state=prohibited_state)

    assert coerce_runtime_decision_state(RuntimeLifecycleState.PLAN_VALIDATED) is (
        RuntimeDecisionState.PLAN_VALIDATED
    )
    assert coerce_runtime_decision_state(RuntimeEntryStatus.INPUTS_BLOCKED) is (
        RuntimeDecisionState.BLOCKED
    )


def test_runtime_stop_condition_maps_to_blocked_and_is_not_operator_stop_file() -> None:
    condition = RuntimeStopCondition.blocked_by_policy(
        message="Runtime policy prevents continuation until review metadata exists.",
        source_id="runtime_stop_unit",
    )

    decision = condition.to_decision()
    payload = condition.to_dict()

    assert condition.decision_state is RuntimeDecisionState.BLOCKED
    assert decision.state is RuntimeDecisionState.BLOCKED
    assert decision.reasons == (condition.reason,)
    assert payload["condition_type"] == "runtime_decision_stop_condition"
    assert "runs/" not in str(payload)
    assert "/STOP" not in str(payload)

    with pytest.raises(RuntimeDecisionStateError, match="must map to BLOCKED"):
        RuntimeStopCondition(reason=_reason(RuntimeDecisionState.REJECTED))


def _reason(state: RuntimeDecisionState) -> RejectionReasonRecord:
    code = (
        RejectionReasonCode.BLOCKED_BY_POLICY
        if state is RuntimeDecisionState.BLOCKED
        else RejectionReasonCode.WEAK_DIAGNOSTICS
    )
    return RejectionReasonRecord(
        code=code,
        message="Synthetic runtime decision reason remains visible.",
        decision_state=state,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code=f"source_{code.value}",
    )


def _bounded_grid_budget_exceeded():
    return validate_bounded_grid_request(
        run_id="run_decision_grid_budget_exceeded",
        binding_ref={
            "alpha_spec_ref": "aspec_af848bc999a4c4b11a421bd0",
            "study_spec_ref": "sspec_438ceffd40855205de5497f0",
            "study_run_spec_id": "srun_0123456789abcdef01234567",
            "study_run_spec_content_hash": "a" * 64,
            "signal_probe_spec_id": "sprobe_0123456789abcdef012345",
            "signal_probe_spec_content_hash": "b" * 64,
        },
        parameter_axes={"threshold": ["0.5", "0.6"], "direction_policy": ["long", "short"]},
        variant_budget=VariantBudget(max_variants=3),
    )
