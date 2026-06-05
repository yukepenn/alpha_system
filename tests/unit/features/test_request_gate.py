from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from alpha_system.features.request_gate import (
    FeatureRequestGateError,
    FeatureRequestGateRejectionReason,
    evaluate_feature_request_gate,
    is_feature_implementation_allowed,
    require_feature_request_implementation_allowed,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
    apply_duplicate_exposure_notes,
    check_duplicate_exposure,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class ReadOnlyRegistrySpy:
    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self.entries = entries
        self.read_calls = 0
        self.write_calls: list[str] = []

    def read_factor_versions(self) -> list[dict[str, Any]]:
        self.read_calls += 1
        return deepcopy(self.entries)

    def register_factor_spec(self, *_args: object, **_kwargs: object) -> None:
        self.write_calls.append("register_factor_spec")
        raise AssertionError("request gate attempted to mutate the registry")


def test_missing_request_fails_closed_without_registry_read() -> None:
    registry = ReadOnlyRegistrySpy(_distinct_registry_entries())

    decision = evaluate_feature_request_gate(None, registry)

    assert decision.implementation_allowed is False
    assert decision.rejection_reason is FeatureRequestGateRejectionReason.MISSING_REQUEST
    assert decision.duplicate_exposure_report is None
    assert registry.read_calls == 0


def test_invalid_request_fails_closed_without_registry_read() -> None:
    registry = ReadOnlyRegistrySpy(_distinct_registry_entries())
    payload = _approved_distinct_request().to_dict()
    payload["duplicate_or_equivalent_exposure_notes"] = {}

    decision = evaluate_feature_request_gate(payload, registry)

    assert decision.implementation_allowed is False
    assert decision.rejection_reason is FeatureRequestGateRejectionReason.INVALID_REQUEST
    assert "invalid" in decision.message
    assert registry.read_calls == 0


@pytest.mark.parametrize(
    "approval_status",
    [
        FeatureRequestApprovalStatus.PENDING,
        FeatureRequestApprovalStatus.NEEDS_REVIEW,
    ],
)
def test_unapproved_request_fails_closed_after_governance_exposure_check(
    approval_status: FeatureRequestApprovalStatus,
) -> None:
    registry = ReadOnlyRegistrySpy(_distinct_registry_entries())
    request = _distinct_request(approval_status=approval_status)

    decision = evaluate_feature_request_gate(request, registry)

    assert decision.implementation_allowed is False
    assert decision.rejection_reason is FeatureRequestGateRejectionReason.UNAPPROVED_REQUEST
    assert decision.duplicate_exposure_report is not None
    assert decision.duplicate_exposure_report.registry_status is ExposureRegistryStatus.CHECKED
    assert decision.checked_feature_request is not None
    assert decision.checked_feature_request.approval_status == approval_status.value
    assert registry.read_calls == 1
    assert registry.write_calls == []


def test_blocked_duplicate_request_fails_closed() -> None:
    registry = ReadOnlyRegistrySpy(_duplicate_registry_entries())
    pending_request = _duplicate_request(approval_status=FeatureRequestApprovalStatus.PENDING)
    blocked_request = apply_duplicate_exposure_notes(
        pending_request,
        check_duplicate_exposure(pending_request, registry),
    )
    assert blocked_request.approval_status == FeatureRequestApprovalStatus.BLOCKED_DUPLICATE

    decision = evaluate_feature_request_gate(blocked_request, registry)

    assert decision.implementation_allowed is False
    assert decision.rejection_reason is FeatureRequestGateRejectionReason.BLOCKED_DUPLICATE
    assert decision.duplicate_exposure_report is not None
    assert decision.duplicate_exposure_report.has_blocking_findings is True
    assert decision.checked_feature_request is not None
    assert (
        decision.checked_feature_request.approval_status
        == FeatureRequestApprovalStatus.BLOCKED_DUPLICATE
    )
    assert registry.read_calls == 2
    assert registry.write_calls == []


def test_approved_request_with_missing_exposure_record_fails_closed() -> None:
    request = _approved_distinct_request()

    decision = evaluate_feature_request_gate(request, None)

    assert decision.implementation_allowed is False
    assert (
        decision.rejection_reason
        is FeatureRequestGateRejectionReason.MISSING_EXPOSURE_RECORD
    )
    assert decision.duplicate_exposure_report is not None
    assert decision.duplicate_exposure_report.registry_status is ExposureRegistryStatus.UNAVAILABLE
    assert decision.checked_feature_request is None


def test_approved_duplicate_request_is_rechecked_and_blocked() -> None:
    registry = ReadOnlyRegistrySpy(_duplicate_registry_entries())
    request = _duplicate_request(approval_status=FeatureRequestApprovalStatus.APPROVED)

    decision = evaluate_feature_request_gate(request, registry)

    assert decision.implementation_allowed is False
    assert decision.rejection_reason is FeatureRequestGateRejectionReason.BLOCKED_DUPLICATE
    assert decision.duplicate_exposure_report is not None
    assert decision.duplicate_exposure_report.has_blocking_findings is True
    assert len(decision.duplicate_exposure_report.equivalent_feature_groups) == 1
    group = decision.duplicate_exposure_report.equivalent_feature_groups[0]
    assert group.matched_registry_reference["factor_id"] == "synthetic_close_return_1d"
    with pytest.raises(TypeError):
        group.matched_registry_reference["factor_id"] = "mutated"
    assert decision.checked_feature_request is not None
    assert (
        decision.checked_feature_request.approval_status
        == FeatureRequestApprovalStatus.BLOCKED_DUPLICATE
    )
    assert registry.read_calls == 1
    assert registry.write_calls == []


def test_approved_non_duplicate_request_admits_implementation() -> None:
    registry = ReadOnlyRegistrySpy(_distinct_registry_entries())
    request = _approved_distinct_request()

    decision = evaluate_feature_request_gate(request, registry)

    assert decision.implementation_allowed is True
    assert decision.rejection_reason is None
    assert decision.duplicate_exposure_report is not None
    assert decision.duplicate_exposure_report.registry_status is ExposureRegistryStatus.CHECKED
    assert decision.duplicate_exposure_report.registry_entries_checked == 1
    assert decision.duplicate_exposure_report.has_findings is False
    assert decision.checked_feature_request is not None
    assert decision.checked_feature_request.approval_status == FeatureRequestApprovalStatus.APPROVED
    assert (
        decision.checked_feature_request.duplicate_or_equivalent_exposure_notes[
            "registry_status"
        ]
        == "CHECKED"
    )
    assert decision.feature_request_id == decision.checked_feature_request.feature_request_id
    assert registry.read_calls == 1
    assert registry.write_calls == []


def test_require_and_predicate_helpers_preserve_fail_closed_gate() -> None:
    registry = ReadOnlyRegistrySpy(_distinct_registry_entries())
    request = _approved_distinct_request()

    allowed = require_feature_request_implementation_allowed(request, registry)

    assert allowed.implementation_allowed is True
    assert is_feature_implementation_allowed(request, registry) is True

    with pytest.raises(FeatureRequestGateError) as exc_info:
        require_feature_request_implementation_allowed(None, registry)

    assert (
        exc_info.value.decision.rejection_reason
        is FeatureRequestGateRejectionReason.MISSING_REQUEST
    )


def _approved_distinct_request() -> FeatureRequest:
    return _distinct_request(approval_status=FeatureRequestApprovalStatus.APPROVED)


def _distinct_request(
    *,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    return _make_request(
        requested_inputs=["synthetic_volume_rank_5d"],
        formula_sketch={
            "exposure_family": "synthetic_volume_rank_5d",
            "inputs": ["synthetic_volume"],
            "operation": "rank",
            "window": 5,
        },
        approval_status=approval_status,
    )


def _duplicate_request(
    *,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    return _make_request(
        requested_inputs=["synthetic_close_return_1d"],
        formula_sketch={
            "exposure_family": "synthetic_close_return_1d",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        approval_status=approval_status,
    )


def _make_request(
    *,
    requested_inputs: list[str],
    formula_sketch: dict[str, object],
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=requested_inputs,
        formula_sketch=formula_sketch,
        availability_assumptions={
            "timing": "synthetic feature inputs are available after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": requested_inputs,
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=approval_status,
    )


def _duplicate_registry_entries() -> list[dict[str, Any]]:
    return [
        {
            "factor_id": "synthetic_close_return_1d",
            "factor_version": "v1",
            "name": "synthetic_close_return_1d",
            "metadata": {
                "exposure_family": "synthetic_close_return_1d",
                "operation": "return",
                "inputs": ["synthetic_close"],
                "window": 1,
            },
            "parameters": {
                "operation": "pct_change",
                "inputs": ["synthetic_close"],
                "window": 1,
            },
        }
    ]


def _distinct_registry_entries() -> list[dict[str, Any]]:
    return [
        {
            "factor_id": "synthetic_close_return_1d",
            "factor_version": "v1",
            "name": "synthetic_close_return_1d",
            "metadata": {
                "exposure_family": "synthetic_close_return_1d",
                "operation": "return",
                "inputs": ["synthetic_close"],
                "window": 1,
            },
            "parameters": {
                "operation": "pct_change",
                "inputs": ["synthetic_close"],
                "window": 1,
            },
        }
    ]
