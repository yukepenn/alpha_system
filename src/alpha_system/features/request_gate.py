"""FeatureRequest implementation gate for the feature layer.

This module adapts existing governance contracts. It does not define new
FeatureRequest or duplicate-exposure logic; it validates requests and exposure
checks through ``alpha_system.governance`` and fails closed by default.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureFinding,
    ExposureFindingKind,
    ExposureFindingSeverity,
    ExposureRegistryStatus,
    RegistryReader,
    apply_duplicate_exposure_notes,
    check_duplicate_exposure,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    validate_feature_request,
)
from alpha_system.governance.validation import GovernanceValidationError


class FeatureRequestGateRejectionReason(StrEnum):
    """Typed fail-closed reasons from the feature implementation gate."""

    MISSING_REQUEST = "MISSING_REQUEST"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNAPPROVED_REQUEST = "UNAPPROVED_REQUEST"
    BLOCKED_DUPLICATE = "BLOCKED_DUPLICATE"
    MISSING_EXPOSURE_RECORD = "MISSING_EXPOSURE_RECORD"
    INVALID_EXPOSURE_RECORD = "INVALID_EXPOSURE_RECORD"


@dataclass(frozen=True, slots=True)
class EquivalentFeatureGroup:
    """Read-only feature-layer view over one governance exposure finding."""

    kind: ExposureFindingKind
    severity: ExposureFindingSeverity
    matched_registry_reference: Mapping[str, str]
    rationale: str

    @classmethod
    def from_finding(cls, finding: ExposureFinding) -> EquivalentFeatureGroup:
        """Create a read-only view from a governance ``ExposureFinding``."""

        return cls(
            kind=finding.kind,
            severity=finding.severity,
            matched_registry_reference=MappingProxyType(
                dict(finding.matched_registry_reference)
            ),
            rationale=finding.rationale,
        )

    @property
    def is_blocking(self) -> bool:
        """Return whether this governance finding blocks implementation."""

        return self.severity is ExposureFindingSeverity.BLOCKING

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-shaped representation of the view."""

        return {
            "kind": self.kind.value,
            "severity": self.severity.value,
            "matched_registry_reference": dict(self.matched_registry_reference),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class DuplicateExposureReport:
    """Read-only feature-layer view over a governance exposure check result."""

    registry_status: ExposureRegistryStatus
    registry_entries_checked: int
    registry_error: str
    equivalent_feature_groups: tuple[EquivalentFeatureGroup, ...]

    @classmethod
    def from_result(cls, result: ExposureCheckResult) -> DuplicateExposureReport:
        """Create a feature-layer report from governance guard output."""

        return cls(
            registry_status=result.registry_status,
            registry_entries_checked=result.registry_entries_checked,
            registry_error=result.registry_error,
            equivalent_feature_groups=tuple(
                EquivalentFeatureGroup.from_finding(finding)
                for finding in result.findings
            ),
        )

    @property
    def has_findings(self) -> bool:
        """Return whether the governance guard found duplicate/equivalent exposure."""

        return bool(self.equivalent_feature_groups)

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether any governance finding blocks implementation."""

        return any(group.is_blocking for group in self.equivalent_feature_groups)

    @property
    def registry_was_available(self) -> bool:
        """Return whether the read-only registry check completed."""

        return self.registry_status is not ExposureRegistryStatus.UNAVAILABLE

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-shaped representation of the report."""

        return {
            "registry_status": self.registry_status.value,
            "registry_entries_checked": self.registry_entries_checked,
            "registry_error": self.registry_error,
            "equivalent_feature_groups": [
                group.to_dict() for group in self.equivalent_feature_groups
            ],
        }


@dataclass(frozen=True, slots=True)
class FeatureRequestGateDecision:
    """Outcome from evaluating the sole feature implementation gate."""

    implementation_allowed: bool
    feature_request: FeatureRequest | None
    checked_feature_request: FeatureRequest | None
    duplicate_exposure_report: DuplicateExposureReport | None
    rejection_reason: FeatureRequestGateRejectionReason | None
    message: str

    @property
    def feature_request_id(self) -> str | None:
        """Return the most recent governed request id available to this decision."""

        if self.checked_feature_request is not None:
            return self.checked_feature_request.feature_request_id
        if self.feature_request is not None:
            return self.feature_request.feature_request_id
        return None


class FeatureRequestGateError(RuntimeError):
    """Raised when a caller requires implementation access and the gate rejects."""

    def __init__(self, decision: FeatureRequestGateDecision) -> None:
        self.decision = decision
        super().__init__(decision.message)


def evaluate_feature_request_gate(
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
) -> FeatureRequestGateDecision:
    """Evaluate whether a governed request admits feature implementation.

    Every valid request is checked against the governance duplicate-exposure
    guard before an implementation decision is returned. Only a request whose
    checked governance status remains ``APPROVED`` is admitted.
    """

    request, invalid_message = _coerce_feature_request(feature_request)
    if request is None:
        reason = (
            FeatureRequestGateRejectionReason.MISSING_REQUEST
            if feature_request is None
            else FeatureRequestGateRejectionReason.INVALID_REQUEST
        )
        return _reject(
            reason=reason,
            feature_request=None,
            checked_feature_request=None,
            duplicate_exposure_report=None,
            message=invalid_message,
        )

    result = check_duplicate_exposure(request, registry_reader)
    report = DuplicateExposureReport.from_result(result)
    status = FeatureRequestApprovalStatus(request.approval_status)

    if status is FeatureRequestApprovalStatus.BLOCKED_DUPLICATE:
        checked_request = _try_apply_duplicate_notes(request, result)
        return _reject(
            reason=FeatureRequestGateRejectionReason.BLOCKED_DUPLICATE,
            feature_request=request,
            checked_feature_request=checked_request,
            duplicate_exposure_report=report,
            message=(
                "FeatureRequest is BLOCKED_DUPLICATE and cannot admit feature "
                "implementation"
            ),
        )

    if report.registry_status is ExposureRegistryStatus.UNAVAILABLE:
        return _reject(
            reason=FeatureRequestGateRejectionReason.MISSING_EXPOSURE_RECORD,
            feature_request=request,
            checked_feature_request=None,
            duplicate_exposure_report=report,
            message=(
                "FeatureRequest duplicate-exposure registry check was unavailable; "
                "implementation is not allowed"
            ),
        )

    if report.has_blocking_findings:
        checked_request = _try_apply_duplicate_notes(request, result)
        return _reject(
            reason=FeatureRequestGateRejectionReason.BLOCKED_DUPLICATE,
            feature_request=request,
            checked_feature_request=checked_request,
            duplicate_exposure_report=report,
            message=(
                "FeatureRequest duplicate-exposure guard found a blocking exposure; "
                "implementation is not allowed"
            ),
        )

    checked_request = _try_apply_duplicate_notes(request, result)
    if checked_request is None:
        return _reject(
            reason=FeatureRequestGateRejectionReason.INVALID_EXPOSURE_RECORD,
            feature_request=request,
            checked_feature_request=None,
            duplicate_exposure_report=report,
            message=(
                "FeatureRequest duplicate-exposure guard output could not be applied "
                "to the governed request"
            ),
        )

    checked_status = FeatureRequestApprovalStatus(checked_request.approval_status)
    if checked_status is not FeatureRequestApprovalStatus.APPROVED:
        return _reject(
            reason=FeatureRequestGateRejectionReason.UNAPPROVED_REQUEST,
            feature_request=request,
            checked_feature_request=checked_request,
            duplicate_exposure_report=report,
            message=(
                "FeatureRequest approval_status must be APPROVED before feature "
                f"implementation; got {checked_request.approval_status}"
            ),
        )

    return FeatureRequestGateDecision(
        implementation_allowed=True,
        feature_request=request,
        checked_feature_request=checked_request,
        duplicate_exposure_report=report,
        rejection_reason=None,
        message="FeatureRequest is APPROVED and duplicate-exposure guard check passed",
    )


def require_feature_request_implementation_allowed(
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
) -> FeatureRequestGateDecision:
    """Return the gate decision or raise ``FeatureRequestGateError`` fail-closed."""

    decision = evaluate_feature_request_gate(feature_request, registry_reader)
    if not decision.implementation_allowed:
        raise FeatureRequestGateError(decision)
    return decision


def is_feature_implementation_allowed(
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
) -> bool:
    """Predicate form of the gate that still performs the governance check."""

    return evaluate_feature_request_gate(
        feature_request,
        registry_reader,
    ).implementation_allowed


def _coerce_feature_request(
    value: FeatureRequest | Mapping[str, Any] | None,
) -> tuple[FeatureRequest | None, str]:
    if value is None:
        return None, "FeatureRequest is required before feature implementation"
    try:
        if isinstance(value, FeatureRequest):
            return validate_feature_request(value.to_dict()), ""
        if isinstance(value, Mapping):
            return validate_feature_request(value), ""
    except GovernanceValidationError as exc:
        return None, f"FeatureRequest is invalid: {exc}"
    return None, "FeatureRequest must be a governance FeatureRequest or mapping"


def _try_apply_duplicate_notes(
    request: FeatureRequest,
    result: ExposureCheckResult,
) -> FeatureRequest | None:
    try:
        return apply_duplicate_exposure_notes(request, result)
    except GovernanceValidationError:
        return None


def _reject(
    *,
    reason: FeatureRequestGateRejectionReason,
    feature_request: FeatureRequest | None,
    checked_feature_request: FeatureRequest | None,
    duplicate_exposure_report: DuplicateExposureReport | None,
    message: str,
) -> FeatureRequestGateDecision:
    return FeatureRequestGateDecision(
        implementation_allowed=False,
        feature_request=feature_request,
        checked_feature_request=checked_feature_request,
        duplicate_exposure_report=duplicate_exposure_report,
        rejection_reason=reason,
        message=message,
    )


__all__ = [
    "DuplicateExposureReport",
    "EquivalentFeatureGroup",
    "FeatureRequestGateDecision",
    "FeatureRequestGateError",
    "FeatureRequestGateRejectionReason",
    "evaluate_feature_request_gate",
    "is_feature_implementation_allowed",
    "require_feature_request_implementation_allowed",
]
