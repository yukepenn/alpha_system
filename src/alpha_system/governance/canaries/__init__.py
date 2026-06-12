"""Negative-control canary catalog and result records."""

from alpha_system.governance.canaries.catalog import (
    NEGATIVE_CONTROL_CATALOG,
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlCatalogEntry,
    NegativeControlType,
    catalogued_negative_control_types,
    expected_failure_for_canary_type,
    get_negative_control_entry,
    iter_negative_control_catalog,
)
from alpha_system.governance.canaries.harness import (
    DEFAULT_CANARY_FIXTURE_PATHS,
    EXECUTABLE_NEGATIVE_CONTROL_TYPES,
    CanaryFixture,
    CanaryGuard,
    load_default_canary_fixture,
    run_future_shift_canary,
    run_governance_canary,
    run_label_leakage_canary,
    run_optimistic_fill_canary,
    run_random_target_canary,
    run_required_governance_canaries,
)
from alpha_system.governance.canaries.negative_control_result import (
    NEGATIVE_CONTROL_RESULT_FIELD_TYPES,
    NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS,
    NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY,
    NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS,
    NegativeControlPassFail,
    NegativeControlResult,
    create_negative_control_result,
    generate_negative_control_result_id,
    validate_negative_control_result,
    validate_negative_control_result_id,
)
_PLANTED_FAKE_ALPHA_EXPORTS = {
    "DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH",
    "EXPECTED_BLOCK_CODE",
    "PlantedFakeAlphaStudyCanaryResult",
    "load_default_planted_fake_alpha_fixture",
    "run_planted_fake_alpha_canary",
}


def __getattr__(name: str):
    """Lazily expose the planted canary without creating import cycles."""

    if name in _PLANTED_FAKE_ALPHA_EXPORTS:
        from alpha_system.governance.canaries import planted_fake_alpha

        return getattr(planted_fake_alpha, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_CANARY_FIXTURE_PATHS",
    "DEFAULT_PLANTED_FAKE_ALPHA_FIXTURE_PATH",
    "EXECUTABLE_NEGATIVE_CONTROL_TYPES",
    "EXPECTED_BLOCK_CODE",
    "NEGATIVE_CONTROL_CATALOG",
    "NEGATIVE_CONTROL_RESULT_FIELD_TYPES",
    "NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS",
    "NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY",
    "NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS",
    "REQUIRED_NEGATIVE_CONTROL_TYPES",
    "CanaryFixture",
    "CanaryGuard",
    "NegativeControlCatalogEntry",
    "NegativeControlPassFail",
    "NegativeControlResult",
    "NegativeControlType",
    "PlantedFakeAlphaStudyCanaryResult",
    "catalogued_negative_control_types",
    "create_negative_control_result",
    "expected_failure_for_canary_type",
    "generate_negative_control_result_id",
    "get_negative_control_entry",
    "iter_negative_control_catalog",
    "load_default_canary_fixture",
    "load_default_planted_fake_alpha_fixture",
    "run_future_shift_canary",
    "run_governance_canary",
    "run_label_leakage_canary",
    "run_optimistic_fill_canary",
    "run_planted_fake_alpha_canary",
    "run_random_target_canary",
    "run_required_governance_canaries",
    "validate_negative_control_result",
    "validate_negative_control_result_id",
]
