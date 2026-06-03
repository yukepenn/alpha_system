"""Import smoke tests for the governance package skeleton."""

from importlib import import_module


GOVERNANCE_MODULES = (
    "alpha_system.governance",
    "alpha_system.governance.ids",
    "alpha_system.governance.serialization",
    "alpha_system.governance.validation",
    "alpha_system.governance.alpha_spec",
    "alpha_system.governance.hypothesis_card",
    "alpha_system.governance.feature_request",
    "alpha_system.governance.duplicate_exposure",
    "alpha_system.governance.label_spec",
    "alpha_system.governance.label_leakage_guard",
    "alpha_system.governance.study_spec",
    "alpha_system.governance.trial_ledger",
    "alpha_system.governance.evidence_bundle",
    "alpha_system.governance.rejected_idea",
    "alpha_system.governance.promotion",
    "alpha_system.governance.reviewer_verdict",
    "alpha_system.governance.canaries",
    "alpha_system.governance.registry",
    "alpha_system.governance.claims",
    "alpha_system.governance.report",
)


def test_governance_package_and_placeholder_modules_are_importable() -> None:
    for module_name in GOVERNANCE_MODULES:
        module = import_module(module_name)
        assert module.__name__ == module_name
