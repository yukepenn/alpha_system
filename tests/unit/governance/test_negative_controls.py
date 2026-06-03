from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.canaries import (
    NEGATIVE_CONTROL_CATALOG,
    NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY,
    NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS,
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    NegativeControlResult,
    NegativeControlType,
    catalogued_negative_control_types,
    expected_failure_for_canary_type,
    generate_negative_control_result_id,
    iter_negative_control_catalog,
    validate_negative_control_result,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.serialization import deserialize
from alpha_system.governance.validation import GovernanceValidationError


STUDY_SPEC_ID = generate_governance_id(
    GovernanceIdKind.STUDY_SPEC,
    {"fixture": "negative-control-result"},
)


def valid_payload(
    *,
    canary_type: NegativeControlType = NegativeControlType.RANDOM_TARGET,
    observed_result: str | None = None,
    pass_fail: NegativeControlPassFail = NegativeControlPassFail.PASS,
) -> dict[str, object]:
    expected_failure = expected_failure_for_canary_type(canary_type)
    payload: dict[str, object] = {
        "canary_type": canary_type.value,
        "expected_failure": expected_failure,
        "observed_result": expected_failure if observed_result is None else observed_result,
        "pass_fail": pass_fail.value,
        "related_study_or_evidence": STUDY_SPEC_ID,
        "notes": "Synthetic metadata record; validates guard behavior only.",
    }
    payload["canary_id"] = generate_negative_control_result_id(payload)
    return payload


def test_negative_control_result_round_trips_deterministically() -> None:
    payload = valid_payload()

    result = validate_negative_control_result(payload)
    serialized = result.to_canonical_json()
    round_trip = NegativeControlResult.from_canonical_json(serialized)

    assert tuple(result.to_dict()) == NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS
    assert result.to_dict() == payload
    assert result.canary_id == generate_negative_control_result_id(payload)
    assert result.canary_id.startswith("nctrl_")
    assert result.canary_type is NegativeControlType.RANDOM_TARGET
    assert result.pass_fail is NegativeControlPassFail.PASS
    assert result.guard_caught_injected_fault is True
    assert result.expected_failure_observed is True
    assert result.implies_alpha_validity is False
    assert NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY is False
    assert round_trip == result
    assert deserialize(serialized) == result.to_dict()
    assert round_trip.to_canonical_json() == serialized


@pytest.mark.parametrize(
    "field",
    ["canary_type", "expected_failure", "observed_result", "pass_fail"],
)
def test_negative_control_result_missing_required_fields_fail_closed(field: str) -> None:
    payload = valid_payload()
    payload.pop(field)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_negative_control_result(payload)

    assert any(issue.field == field for issue in exc_info.value.issues)
    assert any(issue.code == "missing_required_field" for issue in exc_info.value.issues)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("canary_type", "not_catalogued", "invalid_canary_type"),
        ("expected_failure", "", "empty_required_field"),
        ("expected_failure", "guard_accepts_known_bad_input", "unexpected_expected_failure"),
        ("observed_result", "", "empty_required_field"),
        ("pass_fail", "MAYBE", "invalid_pass_fail"),
    ],
)
def test_negative_control_result_invalid_required_fields_fail_closed(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_negative_control_result(payload)

    assert any(issue.field == field for issue in exc_info.value.issues)
    assert any(issue.code == code for issue in exc_info.value.issues)


def test_negative_control_result_rejects_unknown_fields() -> None:
    payload = valid_payload()
    payload["alpha_validity"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_negative_control_result(payload)

    assert exc_info.value.issues[0].field == "alpha_validity"
    assert exc_info.value.issues[0].code == "unknown_field"


def test_negative_control_result_rejects_wrong_id_kind_and_content_mismatch() -> None:
    payload = valid_payload()
    payload["canary_id"] = generate_governance_id(
        GovernanceIdKind.EVIDENCE_BUNDLE,
        {"fixture": "wrong-kind"},
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_negative_control_result(payload)

    assert any(issue.field == "canary_id" for issue in exc_info.value.issues)
    assert any(issue.code == "unexpected_kind" for issue in exc_info.value.issues)

    changed = deepcopy(valid_payload())
    changed["notes"] = "Changing content must change the deterministic nctrl ID."

    with pytest.raises(GovernanceValidationError) as changed_exc:
        validate_negative_control_result(changed)

    assert changed_exc.value.issues[0].field == "canary_id"
    assert changed_exc.value.issues[0].code == "negative_control_result_id_mismatch"


def test_negative_control_catalog_is_complete_and_has_no_silent_extras() -> None:
    assert catalogued_negative_control_types() == (
        "random_target",
        "permuted_labels",
        "future_shift",
        "optimistic_fill",
    )
    assert REQUIRED_NEGATIVE_CONTROL_TYPES == catalogued_negative_control_types()
    assert tuple(NEGATIVE_CONTROL_CATALOG) == REQUIRED_NEGATIVE_CONTROL_TYPES
    assert (
        tuple(entry.canary_type.value for entry in iter_negative_control_catalog())
        == REQUIRED_NEGATIVE_CONTROL_TYPES
    )

    for entry in iter_negative_control_catalog():
        assert entry.study_spec_negative_control == entry.canary_type.value
        assert entry.expected_failure
        assert entry.guard_family
        assert "NegativeControlResult" in entry.evidence_bundle_result_contract


@pytest.mark.parametrize("canary_type", list(NegativeControlType))
def test_negative_control_result_pass_means_guard_catches_fault(
    canary_type: NegativeControlType,
) -> None:
    result = validate_negative_control_result(valid_payload(canary_type=canary_type))

    assert result.observed_result == result.expected_failure
    assert result.pass_fail is NegativeControlPassFail.PASS
    assert result.guard_caught_injected_fault is True


def test_mismatched_observed_result_is_recordable_as_failed_control() -> None:
    payload = valid_payload(
        observed_result="guard_accepted_known_bad_random_target_signal",
        pass_fail=NegativeControlPassFail.FAIL,
    )

    result = validate_negative_control_result(payload)

    assert result.observed_result != result.expected_failure
    assert result.pass_fail is NegativeControlPassFail.FAIL
    assert result.guard_caught_injected_fault is False
    assert result.expected_failure_observed is False


def test_mismatched_observed_result_cannot_silently_pass() -> None:
    payload = valid_payload(observed_result="guard_accepted_known_bad_random_target_signal")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_negative_control_result(payload)

    assert any(issue.field == "pass_fail" for issue in exc_info.value.issues)
    assert any(issue.code == "inconsistent_pass_fail" for issue in exc_info.value.issues)
