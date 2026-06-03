from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.feature_request import (
    FEATURE_REQUEST_REQUIRED_FIELDS,
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
    generate_feature_request_id,
    validate_feature_request,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/feature_request_valid.json")


def load_valid_feature_request_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_feature_request_fixture_contains_all_required_fields() -> None:
    payload = load_valid_feature_request_payload()

    request = validate_feature_request(payload)

    assert isinstance(request, FeatureRequest)
    assert tuple(request.to_dict()) == FEATURE_REQUEST_REQUIRED_FIELDS
    assert request.feature_request_id == generate_feature_request_id(payload)
    assert request.feature_request_id.startswith("freq_")
    assert request.alpha_spec_id.startswith("aspec_")
    assert request.approval_status == FeatureRequestApprovalStatus.PENDING.value


@pytest.mark.parametrize("field", FEATURE_REQUEST_REQUIRED_FIELDS)
def test_feature_request_rejects_each_missing_required_field(field: str) -> None:
    payload = load_valid_feature_request_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("requested_inputs", [], "empty_required_field"),
        ("formula_sketch", {}, "empty_required_field"),
        ("availability_assumptions", {}, "empty_required_field"),
        ("duplicate_or_equivalent_exposure_notes", {}, "empty_required_field"),
        ("data_requirements", {}, "empty_required_field"),
        ("approval_status", "AUTO_APPROVED", "invalid_approval_status"),
    ],
)
def test_feature_request_rejects_invalid_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = load_valid_feature_request_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_feature_request_rejects_unchecked_duplicate_notes() -> None:
    payload = load_valid_feature_request_payload()
    notes = dict(payload["duplicate_or_equivalent_exposure_notes"])
    notes["checked"] = False
    payload["duplicate_or_equivalent_exposure_notes"] = notes

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert exc_info.value.issues[0].code == "unchecked_duplicate_exposure"
    assert exc_info.value.issues[0].field == "duplicate_or_equivalent_exposure_notes.checked"


def test_feature_request_rejects_malformed_reference_ids() -> None:
    payload = load_valid_feature_request_payload()
    payload["feature_request_id"] = "aspec_af848bc999a4c4b11a421bd0"
    payload["alpha_spec_id"] = "freq_eb180e1226ce34c048c7e6eb"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert [issue.field for issue in exc_info.value.issues] == [
        "feature_request_id",
        "alpha_spec_id",
    ]


def test_feature_request_rejects_id_that_does_not_match_content() -> None:
    payload = load_valid_feature_request_payload()
    changed = deepcopy(payload)
    changed["requested_inputs"] = ["synthetic_volume_rank_variant"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(changed)

    assert exc_info.value.issues[0].code == "feature_request_id_mismatch"
    assert exc_info.value.issues[0].field == "feature_request_id"


def test_feature_request_rejects_unknown_fields_without_dropping_them() -> None:
    payload = load_valid_feature_request_payload()
    payload["implementation_allowed"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "implementation_allowed" in payload


def test_feature_request_canonical_round_trip_is_deterministic() -> None:
    payload = load_valid_feature_request_payload()
    reordered = dict(reversed(list(payload.items())))

    request = validate_feature_request(payload)
    serialized = request.to_canonical_json()
    round_tripped = FeatureRequest.from_canonical_json(serialized)

    assert round_tripped == request
    assert deserialize(serialized) == request.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_feature_request_defaults_to_pending_not_approved() -> None:
    payload = load_valid_feature_request_payload()

    request = create_feature_request(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        requested_inputs=list(payload["requested_inputs"]),
        formula_sketch=dict(payload["formula_sketch"]),
        availability_assumptions=dict(payload["availability_assumptions"]),
        duplicate_or_equivalent_exposure_notes=dict(
            payload["duplicate_or_equivalent_exposure_notes"]
        ),
        data_requirements=dict(payload["data_requirements"]),
    )

    assert request.approval_status == FeatureRequestApprovalStatus.PENDING.value
    assert request.approval_status != FeatureRequestApprovalStatus.APPROVED.value


def test_feature_request_cannot_be_approved_with_blocking_duplicate() -> None:
    payload = load_valid_feature_request_payload()
    notes = dict(payload["duplicate_or_equivalent_exposure_notes"])
    notes["registry_status"] = "CHECKED"
    notes["registry_entries_checked"] = 1
    notes["findings"] = [
        {
            "kind": "DUPLICATE",
            "severity": "BLOCKING",
            "matched_registry_reference": {
                "factor_id": "synthetic_close_return_1d",
                "factor_version": "v1",
            },
            "rationale": "synthetic duplicate fixture match",
        }
    ]
    payload["duplicate_or_equivalent_exposure_notes"] = notes
    payload["approval_status"] = FeatureRequestApprovalStatus.APPROVED.value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_feature_request(payload)

    assert exc_info.value.issues[0].code == "approved_with_blocking_duplicate"
    assert exc_info.value.issues[0].field == "approval_status"
