"""Research-lane orchestration helpers outside the loader-free research package."""

from alpha_system.research_lane.testability_gate import (
    GateCheckResult,
    GateStatus,
    TestabilityGateError,
    TestabilityGateResult,
    TestabilitySlice,
    evaluate_testability_gate,
    slice_spec_from_idea_payload,
    summarize_label_class_balance,
)

__all__ = [
    "GateCheckResult",
    "GateStatus",
    "TestabilityGateError",
    "TestabilityGateResult",
    "TestabilitySlice",
    "evaluate_testability_gate",
    "slice_spec_from_idea_payload",
    "summarize_label_class_balance",
]
