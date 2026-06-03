from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.label_spec import (
    LABEL_SPEC_REQUIRED_FIELDS,
    LabelSpec,
    create_label_spec,
    generate_label_spec_id,
    validate_label_spec,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/label_spec_valid.json")


def load_valid_label_spec_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_label_spec_fixture_contains_all_required_fields() -> None:
    payload = load_valid_label_spec_payload()

    label_spec = validate_label_spec(payload)

    assert isinstance(label_spec, LabelSpec)
    assert all(field in label_spec.to_dict() for field in LABEL_SPEC_REQUIRED_FIELDS)
    assert label_spec.label_spec_id == generate_label_spec_id(payload)
    assert label_spec.label_spec_id.startswith("lspec_")
    assert label_spec.alpha_spec_id == "aspec_af848bc999a4c4b11a421bd0"
    assert label_spec.leakage_checks == ["label_as_feature", "availability_time"]


@pytest.mark.parametrize("field", LABEL_SPEC_REQUIRED_FIELDS)
def test_label_spec_rejects_each_missing_required_field(field: str) -> None:
    payload = load_valid_label_spec_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("horizon", "", "empty_required_field"),
        ("availability_time", "TBD", "empty_required_field"),
        ("availability_time", "2026-01-10", "missing_availability_timezone"),
        ("path_rules", {}, "empty_required_field"),
        ("cost_model", {}, "empty_required_field"),
        ("target_stop_rules", {}, "empty_required_field"),
        ("forbidden_feature_overlap", {}, "empty_required_field"),
        ("leakage_checks", [], "empty_required_field"),
        ("leakage_checks", ["label_as_feature"], "missing_leakage_check"),
    ],
)
def test_label_spec_rejects_invalid_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = load_valid_label_spec_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_label_spec_rejects_malformed_reference_ids() -> None:
    payload = load_valid_label_spec_payload()
    payload["label_spec_id"] = "aspec_af848bc999a4c4b11a421bd0"
    payload["alpha_spec_id"] = "lspec_8663589ca7a9f1e5859289c7"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(payload)

    assert [issue.field for issue in exc_info.value.issues] == [
        "label_spec_id",
        "alpha_spec_id",
    ]


def test_label_spec_rejects_id_that_does_not_match_content() -> None:
    payload = load_valid_label_spec_payload()
    changed = deepcopy(payload)
    changed["horizon"] = "synthetic 10 day forward return horizon"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(changed)

    assert exc_info.value.issues[0].code == "label_spec_id_mismatch"
    assert exc_info.value.issues[0].field == "label_spec_id"


def test_label_spec_rejects_unknown_fields_without_dropping_them() -> None:
    payload = load_valid_label_spec_payload()
    payload["label_quality"] = "not allowed"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "label_quality" in payload


def test_label_spec_rejects_non_serializable_nested_values() -> None:
    payload = load_valid_label_spec_payload()
    cost_model = dict(payload["cost_model"])
    cost_model["bad"] = object()
    payload["cost_model"] = cost_model

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_label_spec(payload)

    assert exc_info.value.issues[0].code == "unsupported_value_type"


def test_label_spec_canonical_round_trip_is_deterministic() -> None:
    payload = load_valid_label_spec_payload()
    reordered = dict(reversed(list(payload.items())))

    label_spec = validate_label_spec(payload)
    serialized = label_spec.to_canonical_json()
    round_tripped = LabelSpec.from_canonical_json(serialized)

    assert round_tripped == label_spec
    assert deserialize(serialized) == label_spec.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_label_spec_generates_content_bound_id() -> None:
    payload = load_valid_label_spec_payload()

    label_spec = create_label_spec(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        horizon=str(payload["horizon"]),
        path_rules=dict(payload["path_rules"]),
        cost_model=dict(payload["cost_model"]),
        target_stop_rules=dict(payload["target_stop_rules"]),
        availability_time=str(payload["availability_time"]),
        forbidden_feature_overlap=dict(payload["forbidden_feature_overlap"]),
        leakage_checks=list(payload["leakage_checks"]),
    )

    assert label_spec.label_spec_id == payload["label_spec_id"]
    assert label_spec.label_spec_id.startswith("lspec_")
