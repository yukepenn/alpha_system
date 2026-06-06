from __future__ import annotations

import json

from alpha_system.runtime.audit.no_lookahead import NoLookaheadAuditOutcome
from alpha_system.runtime.decisions import RejectionReasonRecord, RuntimeDecisionState
from alpha_system.runtime.dry_run import (
    PROHIBITED_MVP_STATES,
    RuntimeDryRunConfig,
    run_runtime_dry_run,
)
from alpha_system.runtime.grid import BoundedGridOutcome, VariantBudget
from alpha_system.runtime.handoff import REFERENCE_VALIDATION_REQUIRED


def test_synthetic_dry_run_reaches_reference_handoff_ready_without_promotional_state() -> None:
    result = run_runtime_dry_run()

    assert result.terminal_decision_state is RuntimeDecisionState.REFERENCE_HANDOFF_READY
    assert result.reference_handoff is not None
    assert result.reference_handoff.decision_state is RuntimeDecisionState.REFERENCE_HANDOFF_READY
    assert result.run_summary is not None
    assert result.tool_result is not None
    assert result.run_summary.status is RuntimeDecisionState.REFERENCE_HANDOFF_READY
    assert result.terminal_decision_state.value not in PROHIBITED_MVP_STATES
    assert PROHIBITED_MVP_STATES.isdisjoint({state.value for state in RuntimeDecisionState})
    assert result.pass_with_warnings_recorded is True
    assert result.dry_run_status == "PASS_WITH_WARNINGS"
    assert result.warning_reasons == (
        "local registry/data absent; used in-memory synthetic DatasetVersion and pack resolvers",
    )


def test_missing_alpha_or_study_spec_blocks_before_runtime_execution() -> None:
    no_alpha = run_runtime_dry_run(RuntimeDryRunConfig(include_alpha_spec=False))
    no_study = run_runtime_dry_run(RuntimeDryRunConfig(include_study_spec=False))

    for result in (no_alpha, no_study):
        assert result.terminal_decision_state is RuntimeDecisionState.BLOCKED
        assert result.executed is False
        assert result.runtime_input_pack is None
        assert result.tool_result is None
        assert result.run_summary is None
        assert result.rejection_reasons
        assert all(isinstance(reason, RejectionReasonRecord) for reason in result.rejection_reasons)

    assert "missing_alpha_spec_ref" in {reason.source_code for reason in no_alpha.rejection_reasons}
    assert "missing_study_spec_ref" in {
        reason.source_code for reason in no_study.rejection_reasons
    }


def test_cost_stress_grid_audit_evidence_and_handoff_guards_are_visible() -> None:
    result = run_runtime_dry_run()

    assert result.cost_sensitivity_report is not None
    profile_names = {summary.profile_name for summary in result.cost_sensitivity_report.profile_summaries}
    assert {"base", "double_cost"} <= profile_names
    assert result.cost_sensitivity_report.slippage_labeled_proxy is True
    assert result.cost_sensitivity_report.double_cost_summary.profile_name == "double_cost"
    assert result.signal_probe_report is not None
    assert result.signal_probe_report.cost_stress_evidence_state == "COST_STRESS_COMPLETE"
    assert result.signal_probe_report.position_summary["same_bar_fill_count"] == 0

    assert result.bounded_grid_result is not None
    assert result.bounded_grid_result.status is BoundedGridOutcome.GUARD_PASSED
    assert result.bounded_grid_result.spec is not None
    assert isinstance(result.bounded_grid_result.spec.variant_budget, VariantBudget)
    assert result.bounded_grid_result.record.realized_variant_count <= (
        result.bounded_grid_result.spec.variant_budget.effective_max_combinations
    )
    assert "locked_test_candidate" not in result.bounded_grid_result.record.partition_scope_ids
    assert "latest_shadow_candidate" not in result.bounded_grid_result.record.partition_scope_ids

    assert result.no_lookahead_audit_result is not None
    assert result.no_lookahead_audit_result.outcome is NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
    assert set(result.no_lookahead_audit_coverage) == {
        "available_ts",
        "label_available_ts",
        "same_bar_fills",
        "locked_test_metadata",
    }

    assert result.evidence_draft is not None
    assert result.evidence_draft.not_a_candidate is True
    assert result.evidence_draft.not_reference_truth is True
    assert result.reference_handoff is not None
    assert result.reference_handoff.strategy_not_validated is True
    assert result.reference_handoff.reference_requirements.next_required_gate == (
        REFERENCE_VALIDATION_REQUIRED
    )
    assert result.reference_handoff.reference_requirements.reference_validation_performed is False


def test_agent_facing_outputs_are_value_free_and_reference_only() -> None:
    result = run_runtime_dry_run()
    assert result.tool_result is not None
    assert result.run_summary is not None

    payload = {
        "tool_result": result.tool_result.to_dict(),
        "run_summary": result.run_summary.to_dict(),
    }
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "feature_values",
        "label_values",
        "canonical_bars",
        "provider_payload",
        "provider_response",
        "raw_values",
        ".parquet",
        ".arrow",
        ".feather",
        ".dbn",
        ".zst",
        ".sqlite",
        "data/raw/",
        "artifacts/",
    ):
        assert forbidden not in rendered

    assert payload["tool_result"]["status"] == "REFERENCE_HANDOFF_READY"
    assert payload["tool_result"]["next_required_gate"] == REFERENCE_VALIDATION_REQUIRED
    assert payload["tool_result"]["cost_summary"]["slippage_labeled_proxy"] is True
