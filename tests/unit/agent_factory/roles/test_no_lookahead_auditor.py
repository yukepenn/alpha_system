from __future__ import annotations

import importlib
from dataclasses import fields
from pathlib import Path

import alpha_system.agent_factory.roles as roles_package
import alpha_system.agent_factory.roles.registry as registry_module
from alpha_system.agent_factory.permissions.matrix import permission_for
from alpha_system.agent_factory.roles.contracts import (
    FORBIDDEN_HEAVY_SUFFIXES,
    FORBIDDEN_PAYLOAD_MARKERS,
    AgentRole,
)
from alpha_system.agent_factory.tools.results import AgentToolResult, AgentToolStatus
from alpha_system.governance.label_leakage_guard import (
    LabelLeakageFinding,
    LabelLeakageResult,
    check_label_leakage,
)
from alpha_system.runtime.audit.no_lookahead import (
    NoLookaheadAuditOutcome,
    NoLookaheadAuditResult,
    NoLookaheadRejectionCategory,
    NoLookaheadRuntimeAudit,
)

MODULE_NAME = "alpha_system.agent_factory.roles.no_lookahead_auditor"
ROLE_ID = "no_lookahead_auditor"
EXPECTED_TOOLS = ("runtime.audit_no_lookahead", "governance.check_label_leakage")


def test_module_imports_and_registers_no_lookahead_auditor_once() -> None:
    before_ids = set(registry_module.role_ids())

    module = importlib.import_module(MODULE_NAME)

    after_ids = registry_module.role_ids()
    assert set(after_ids).difference(before_ids) <= {ROLE_ID}
    assert after_ids.count(ROLE_ID) == 1
    registered = registry_module.get(ROLE_ID)
    assert registered == module.NO_LOOKAHEAD_AUDITOR_ROLE
    assert registered.role_id == ROLE_ID


def test_repeated_import_or_reload_does_not_duplicate_registration() -> None:
    module = importlib.import_module(MODULE_NAME)

    importlib.import_module(MODULE_NAME)
    reloaded = importlib.reload(module)

    assert registry_module.role_ids().count(ROLE_ID) == 1
    assert registry_module.get(ROLE_ID) == reloaded.NO_LOOKAHEAD_AUDITOR_ROLE


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


def test_callable_tools_match_permission_matrix_without_promotion_or_guard_weakening() -> None:
    role = _registered_role()
    permissions = permission_for(ROLE_ID)

    assert role.callable_tools == EXPECTED_TOOLS
    assert role.callable_tools == permissions.tool.allowed_tool_ids
    assert permissions.write.allowed_scopes == ("lookahead_audit.record",)
    assert not permissions.write.direct_registry_write
    assert not permissions.review.can_issue_verdict
    assert not permissions.promotion.can_promote
    assert not permissions.data.raw_provider_access
    assert "promotion" not in " ".join(role.callable_tools)

    forbidden_text = " ".join(role.forbidden_decisions).lower()
    for required_fragment in (
        "promote",
        "weaken_bypass_or_reimplement_no_lookahead_guard",
        "run_diagnostics",
        "read_raw_provider_data",
        "external_provider_calls",
        "bypass_runtime_input_resolver_or_tool_surface",
        "write_feature_label_dataset_or_promotion_registry",
        "capital_risk_live_paper_broker_order",
    ):
        assert required_fragment in forbidden_text


def test_role_imports_consumed_primitives_without_reimplementing_them() -> None:
    module = importlib.import_module(MODULE_NAME)

    assert module.CONSUMED_PRIMITIVES == (
        NoLookaheadRuntimeAudit,
        NoLookaheadAuditResult,
        NoLookaheadAuditOutcome,
        NoLookaheadRejectionCategory,
        check_label_leakage,
        LabelLeakageResult,
        LabelLeakageFinding,
    )

    source_text = Path(module.__file__).read_text(encoding="utf-8")
    assert "class NoLookaheadRuntimeAudit" not in source_text
    assert "def check_label_leakage" not in source_text


def test_declares_required_inputs_outputs_decisions_and_independence() -> None:
    role = _registered_role()

    readable_text = " ".join(role.readable_inputs)
    for required in (
        "RuntimeToolResult",
        "RuntimeRunSummary",
        "NoLookaheadAuditResult",
        "LabelLeakageResult",
        "AlphaSpec",
        "StudySpec",
        "dataset_version_id",
    ):
        assert required in readable_text

    output_text = " ".join(role.producible_outputs)
    for required in (
        "AgentToolResult",
        "PASS",
        "BLOCKED",
        "role",
        "request_id",
        "blocking_findings",
        "rejection_reasons",
        "next_required_gate",
        "artifacts",
        "limitations",
    ):
        assert required in output_text

    allowed_text = " ".join(role.allowed_decisions).lower()
    assert "lookahead_pass" in allowed_text
    assert "blocked" in allowed_text
    assert "independent_downstream_review" in allowed_text
    assert "promote" not in allowed_text
    assert "candidate" not in allowed_text

    independence_text = " ".join(role.reviewer_independence).lower()
    assert "drafter" in independence_text
    assert "implementation" in independence_text
    assert "diagnostics_runner" in independence_text
    assert "independent_downstream_review" in independence_text


def test_missing_field_input_returns_blocked_never_silent_pass() -> None:
    module = importlib.import_module(MODULE_NAME)

    result = module.blocked_missing_audit_fields_result(
        "request_no_lookahead_001",
        ("available_ts", "label_available_ts"),
        alpha_spec_id="alpha_spec_001",
        study_spec_id="study_spec_001",
        dataset_version_id="dataset_version_001",
        feature_pack_refs=("feature_pack_001",),
        label_pack_refs=("label_pack_001",),
        runtime_run_id="runtime_run_001",
    )

    assert isinstance(result, AgentToolResult)
    assert result.status is AgentToolStatus.BLOCKED
    assert result.status is not AgentToolStatus.OK
    assert result.role == ROLE_ID
    assert result.blocking_findings == (
        "missing_required_audit_field:available_ts",
        "missing_required_audit_field:label_available_ts",
    )
    assert result.rejection_reasons == ("missing_required_audit_fields",)
    assert result.next_required_gate == module.MISSING_FIELD_BLOCKED_GATE
    assert "silent PASS" in " ".join(_registered_role().failure_modes)


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
