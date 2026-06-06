from __future__ import annotations

import importlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

import alpha_system.agent_factory.roles as roles_package
import alpha_system.agent_factory.roles.registry as registry_module
from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_HEAVY_SUFFIXES as FORBIDDEN_RESULT_HEAVY_SUFFIXES,
)
from alpha_system.agent_factory.tools.results import (
    FORBIDDEN_RESULT_MARKERS,
    AgentToolResult,
    AgentToolStatus,
)
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
)

MODULE_NAME = "alpha_system.agent_factory.roles.statistical_reviewer"
ROLE_ID = "statistical_reviewer"
EXPECTED_TOOLS = ("review.statistical_evidence", "review.issue_verdict")


def test_module_imports_and_registers_statistical_reviewer_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.STATISTICAL_REVIEWER_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.STATISTICAL_REVIEWER_ROLE


def test_contract_is_populated_and_value_free() -> None:
    role = _registered_role()

    assert isinstance(role, AgentRole)
    assert role.validate() is role
    for field in fields(AgentRole):
        value = getattr(role, field.name)
        values = value if isinstance(value, tuple) else (value,)
        assert values
        for item in values:
            lowered = item.lower()
            assert item
            assert not any(marker in lowered for marker in FORBIDDEN_PAYLOAD_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_HEAVY_SUFFIXES)


def test_callable_tools_match_permission_matrix_and_mismatch_fails_closed() -> None:
    module = importlib.import_module(MODULE_NAME)
    role = _registered_role()
    permissions = permission_for(ROLE_ID)

    assert role.callable_tools == EXPECTED_TOOLS
    assert role.callable_tools == permissions.tool.allowed_tool_ids

    mismatched_role = replace(role, callable_tools=("review.ungranted_tool",))
    with pytest.raises(RuntimeError, match="permission matrix"):
        module._assert_callable_tools_match_matrix(mismatched_role)


def test_permissions_have_no_promotion_or_direct_registry_write_authority() -> None:
    role = _registered_role()
    permissions = permission_for(ROLE_ID)

    assert permissions.write.allowed_scopes == ("statistical_review.record",)
    assert not permissions.write.direct_registry_write
    assert permissions.review.can_issue_verdict
    assert permissions.review.verdict_scopes == ("runtime_evidence_review",)
    assert permissions.review.independence_required
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access
    assert "promotion" not in " ".join(role.callable_tools)
    assert "registry" not in " ".join(role.callable_tools)

    forbidden_text = " ".join(role.forbidden_decisions).lower()
    for required_fragment in (
        "promote",
        "write_feature_label_dataset_or_promotion_registry",
        "run_retry_or_reimplement_diagnostics",
        "review_own_implementation",
        "recompute_statistics_from_raw_values",
        "read_raw_provider_data",
        "external_provider_calls",
        "capital_risk_live_paper_broker_order",
    ):
        assert required_fragment in forbidden_text


def test_declares_required_inputs_outputs_decisions_and_independence() -> None:
    role = _registered_role()

    readable_text = " ".join(role.readable_inputs)
    for required in (
        "RuntimeRunSummary",
        "RuntimeToolResult",
        "diagnostics_summary",
        "cost_summary",
        "no-lookahead audit",
        "alpha_spec_id",
        "study_spec_id",
        "dataset_version_id",
        "feature_pack_refs",
        "label_pack_refs",
        "runtime_run_id",
    ):
        assert required in readable_text

    output_text = " ".join(role.producible_outputs)
    for required in (
        "AgentToolResult",
        "PASS",
        "REJECT",
        "WATCH",
        "INCONCLUSIVE",
        "ReviewerVerdict",
        "rejection_reasons",
        "blocking_findings",
        "next_required_gate",
        "artifacts",
        "limitations",
    ):
        assert required in output_text

    allowed_text = " ".join(role.allowed_decisions)
    for outcome in ("PASS", "REJECT", "WATCH", "INCONCLUSIVE"):
        assert outcome in allowed_text
    assert "promote" not in allowed_text.lower()

    independence_text = " ".join(role.reviewer_independence).lower()
    assert "!=" in independence_text
    assert "diagnostics_runner" in independence_text
    assert "own_work" in independence_text
    assert "own_diagnostics" in independence_text
    assert "no_lookahead_audit_pass" in independence_text


@pytest.mark.parametrize(
    ("verdict", "expected_status", "rejection_reasons", "blocking_findings"),
    (
        ("PASS", AgentToolStatus.OK, (), ()),
        ("REJECT", AgentToolStatus.REJECTED, ("insufficient_statistical_evidence",), ()),
        ("WATCH", AgentToolStatus.WARN, (), ("monitor_with_human_judgment",)),
        ("INCONCLUSIVE", AgentToolStatus.INCONCLUSIVE, ("insufficient_summary_refs",), ()),
    ),
)
def test_all_verdict_outcomes_are_representable_as_value_free_results(
    verdict: str,
    expected_status: AgentToolStatus,
    rejection_reasons: tuple[str, ...],
    blocking_findings: tuple[str, ...],
) -> None:
    module = importlib.import_module(MODULE_NAME)

    result = _review_result(
        module,
        verdict,
        rejection_reasons=rejection_reasons,
        blocking_findings=blocking_findings,
    )

    assert isinstance(result, AgentToolResult)
    assert result.status is expected_status
    assert f"statistical_review_verdict:{verdict}" in result.diagnostics_summary
    assert result.role == ROLE_ID
    assert result.next_required_gate == module.NEXT_REQUIRED_GATE
    _assert_value_free_tool_result(result)


def test_agent_tool_result_rejects_forbidden_payload_refs() -> None:
    module = importlib.import_module(MODULE_NAME)

    with pytest.raises(ValueError):
        _review_result(module, "PASS", evidence_summary_ref="data/raw/evidence")

    with pytest.raises(ValueError):
        _review_result(module, "PASS", artifacts=("review_output.parquet",))


def test_fail_closed_missing_evidence_non_pass_audit_and_missing_specs() -> None:
    module = importlib.import_module(MODULE_NAME)

    missing_evidence = module.inconclusive_missing_evidence_result(
        "request_stat_review_001",
        ("runtime_run_summary_ref", "diagnostics_summary"),
        alpha_spec_id="alpha_spec_001",
        study_spec_id="study_spec_001",
        dataset_version_id="dataset_version_001",
        feature_pack_refs=("feature_pack_001",),
        label_pack_refs=("label_pack_001",),
        runtime_run_id="runtime_run_001",
    )
    assert missing_evidence.status is AgentToolStatus.INCONCLUSIVE
    assert missing_evidence.status is not AgentToolStatus.OK
    assert missing_evidence.next_required_gate == module.MISSING_EVIDENCE_INCONCLUSIVE_GATE
    assert "silent PASS" in " ".join(_registered_role().failure_modes)

    blocked_audit = module.blocked_non_pass_no_lookahead_result(
        "request_stat_review_002",
        "BLOCKED",
        no_lookahead_audit_summary_ref="no_lookahead_audit_summary_001",
        alpha_spec_id="alpha_spec_001",
        study_spec_id="study_spec_001",
        dataset_version_id="dataset_version_001",
    )
    assert blocked_audit.status is AgentToolStatus.BLOCKED
    assert blocked_audit.status is not AgentToolStatus.OK
    assert blocked_audit.next_required_gate == module.NON_PASS_LOOKAHEAD_BLOCKED_GATE
    assert blocked_audit.blocking_findings == ("no_lookahead_audit_status:BLOCKED",)

    missing_specs = module.blocked_missing_bound_specs_result(
        "request_stat_review_003",
        ("alpha_spec_id", "study_spec_id"),
        dataset_version_id="dataset_version_001",
        evidence_summary_ref="runtime_evidence_summary_001",
    )
    assert missing_specs.status is AgentToolStatus.BLOCKED
    assert missing_specs.status is not AgentToolStatus.OK
    assert missing_specs.next_required_gate == module.MISSING_BOUND_SPEC_BLOCKED_GATE
    assert missing_specs.blocking_findings == (
        "missing_bound_spec:alpha_spec_id",
        "missing_bound_spec:study_spec_id",
    )

    with pytest.raises(ValueError):
        _review_result(module, "PASS", no_lookahead_status="BLOCKED")
    with pytest.raises(ValueError):
        _review_result(module, "PASS", alpha_spec_id="")


def test_consumed_governance_primitive_is_imported_not_duplicated() -> None:
    module = importlib.import_module(MODULE_NAME)

    assert module.CONSUMED_PRIMITIVES == (
        ReviewerVerdict,
        ReviewerVerdictOutcome,
    )

    source_text = Path(module.__file__).read_text(encoding="utf-8")
    assert "class ReviewerVerdict" not in source_text
    assert "class ReviewerVerdictOutcome" not in source_text
    assert "def validate_reviewer_verdict" not in source_text


def test_import_does_not_require_shared_role_file_edits() -> None:
    importlib.import_module(MODULE_NAME)
    package_text = Path(roles_package.__file__).read_text(encoding="utf-8")
    registry_text = Path(registry_module.__file__).read_text(encoding="utf-8")

    assert ROLE_ID not in package_text
    assert ROLE_ID not in registry_text
    assert registry_module.role_ids().count(ROLE_ID) == 1


def _registered_role() -> AgentRole:
    importlib.import_module(MODULE_NAME)
    return registry_module.get(ROLE_ID)


def _review_result(
    module: object,
    verdict: str,
    *,
    evidence_summary_ref: str = "runtime_evidence_summary_001",
    no_lookahead_status: str = "PASS",
    alpha_spec_id: str = "alpha_spec_001",
    rejection_reasons: tuple[str, ...] = (),
    blocking_findings: tuple[str, ...] = (),
    artifacts: tuple[str, ...] = (),
) -> AgentToolResult:
    return module.statistical_review_verdict_result(
        "request_stat_review_001",
        verdict,
        evidence_summary_ref=evidence_summary_ref,
        no_lookahead_audit_summary_ref="no_lookahead_audit_summary_001",
        no_lookahead_status=no_lookahead_status,
        alpha_spec_id=alpha_spec_id,
        study_spec_id="study_spec_001",
        dataset_version_id="dataset_version_001",
        feature_pack_refs=("feature_pack_001",),
        label_pack_refs=("label_pack_001",),
        runtime_run_id="runtime_run_001",
        rejection_reasons=rejection_reasons,
        blocking_findings=blocking_findings,
        artifacts=artifacts,
    )


def _assert_value_free_tool_result(result: AgentToolResult) -> None:
    for field in result.__dataclass_fields__:
        value = getattr(result, field)
        values = value if isinstance(value, tuple) else (value,)
        for item in values:
            if item is None or isinstance(item, AgentToolStatus):
                continue
            lowered = item.lower()
            assert not any(marker in lowered for marker in FORBIDDEN_RESULT_MARKERS)
            assert not any(suffix in lowered for suffix in FORBIDDEN_RESULT_HEAVY_SUFFIXES)
