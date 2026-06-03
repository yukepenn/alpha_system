"""Catalog of required governance negative controls.

The catalog is a contract for future canary execution. It does not execute
canaries, ingest data, run diagnostics, or make any market claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.validation import GovernanceValidationError, ValidationIssue


class NegativeControlType(StrEnum):
    """Closed MVP vocabulary for required negative-control canaries."""

    RANDOM_TARGET = "random_target"
    PERMUTED_LABELS = "permuted_labels"
    FUTURE_SHIFT = "future_shift"
    OPTIMISTIC_FILL = "optimistic_fill"


REQUIRED_NEGATIVE_CONTROL_TYPES = tuple(control.value for control in NegativeControlType)


@dataclass(frozen=True, slots=True)
class NegativeControlCatalogEntry:
    """One required negative control and its fail-closed expectation."""

    canary_type: NegativeControlType
    title: str
    guard_family: str
    injected_fault: str
    expected_failure: str
    study_spec_negative_control: str
    evidence_bundle_result_contract: str
    risk_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        """Return an explicit JSON-compatible catalog representation."""

        return {
            "canary_type": self.canary_type.value,
            "title": self.title,
            "guard_family": self.guard_family,
            "injected_fault": self.injected_fault,
            "expected_failure": self.expected_failure,
            "study_spec_negative_control": self.study_spec_negative_control,
            "evidence_bundle_result_contract": self.evidence_bundle_result_contract,
            "risk_refs": list(self.risk_refs),
        }


_CATALOG_ENTRIES = (
    NegativeControlCatalogEntry(
        canary_type=NegativeControlType.RANDOM_TARGET,
        title="Random target",
        guard_family="statistical_sanity",
        injected_fault=(
            "Replace the study target with random noise so any admissible-looking "
            "signal is known-bad."
        ),
        expected_failure="guard_rejects_or_flags_random_target_signal",
        study_spec_negative_control="random_target",
        evidence_bundle_result_contract=(
            "EvidenceBundle.negative_control_results records a "
            "NegativeControlResult with canary_type=random_target."
        ),
        risk_refs=("R-010",),
    ),
    NegativeControlCatalogEntry(
        canary_type=NegativeControlType.PERMUTED_LABELS,
        title="Permuted labels",
        guard_family="label_integrity",
        injected_fault=(
            "Permute labels away from their original examples so label alignment is "
            "known-bad."
        ),
        expected_failure="guard_rejects_or_flags_permuted_label_signal",
        study_spec_negative_control="permuted_labels",
        evidence_bundle_result_contract=(
            "EvidenceBundle.negative_control_results records a "
            "NegativeControlResult with canary_type=permuted_labels."
        ),
        risk_refs=("R-010",),
    ),
    NegativeControlCatalogEntry(
        canary_type=NegativeControlType.FUTURE_SHIFT,
        title="Future shift",
        guard_family="no_lookahead",
        injected_fault=(
            "Shift future information into the feature or label path so lookahead "
            "is known-bad."
        ),
        expected_failure="guard_rejects_or_flags_future_shift_lookahead",
        study_spec_negative_control="future_shift",
        evidence_bundle_result_contract=(
            "EvidenceBundle.negative_control_results records a "
            "NegativeControlResult with canary_type=future_shift."
        ),
        risk_refs=("R-010", "R-011"),
    ),
    NegativeControlCatalogEntry(
        canary_type=NegativeControlType.OPTIMISTIC_FILL,
        title="Optimistic fill",
        guard_family="execution_assumption",
        injected_fault=(
            "Use an unrealistically favorable fill assumption so execution-cost "
            "handling is known-bad."
        ),
        expected_failure="guard_rejects_or_flags_optimistic_fill_assumption",
        study_spec_negative_control="optimistic_fill",
        evidence_bundle_result_contract=(
            "EvidenceBundle.negative_control_results records a "
            "NegativeControlResult with canary_type=optimistic_fill."
        ),
        risk_refs=("R-010",),
    ),
)

NEGATIVE_CONTROL_CATALOG = MappingProxyType(
    {entry.canary_type.value: entry for entry in _CATALOG_ENTRIES}
)


def iter_negative_control_catalog() -> tuple[NegativeControlCatalogEntry, ...]:
    """Return the required MVP negative controls in canonical order."""

    return tuple(
        NEGATIVE_CONTROL_CATALOG[canary_type]
        for canary_type in REQUIRED_NEGATIVE_CONTROL_TYPES
    )


def catalogued_negative_control_types() -> tuple[str, ...]:
    """Return the exact canary type strings valid for `StudySpec.negative_controls`."""

    return REQUIRED_NEGATIVE_CONTROL_TYPES


def get_negative_control_entry(
    canary_type: NegativeControlType | str,
) -> NegativeControlCatalogEntry:
    """Return the catalog entry for a canary type or fail closed."""

    key = _canary_type_value(canary_type)
    return NEGATIVE_CONTROL_CATALOG[key]


def expected_failure_for_canary_type(canary_type: NegativeControlType | str) -> str:
    """Return the required fail-closed expectation for a catalogued canary."""

    return get_negative_control_entry(canary_type).expected_failure


def _canary_type_value(value: NegativeControlType | str | Any) -> str:
    try:
        return NegativeControlType(value).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="canary_type",
                code="invalid_canary_type",
                message="negative-control canary_type must be catalogued",
                expected=" | ".join(REQUIRED_NEGATIVE_CONTROL_TYPES),
                actual=str(value),
            )
        ) from exc


__all__ = [
    "NEGATIVE_CONTROL_CATALOG",
    "REQUIRED_NEGATIVE_CONTROL_TYPES",
    "NegativeControlCatalogEntry",
    "NegativeControlType",
    "catalogued_negative_control_types",
    "expected_failure_for_canary_type",
    "get_negative_control_entry",
    "iter_negative_control_catalog",
]
