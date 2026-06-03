from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.study_spec import (
    DIAGNOSTICS_ALLOWED_STATE,
    IMPLEMENTED_STATE,
    STUDY_SPEC_REQUIRED_FIELDS,
    StudySpec,
    create_study_spec,
    generate_study_spec_id,
    validate_diagnostics_gate,
    validate_study_spec,
)
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")


def load_valid_study_spec_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_study_spec_fixture_contains_all_required_fields() -> None:
    payload = load_valid_study_spec_payload()

    spec = validate_study_spec(payload)

    assert isinstance(spec, StudySpec)
    assert tuple(spec.to_dict()) == STUDY_SPEC_REQUIRED_FIELDS
    assert spec.study_spec_id == generate_study_spec_id(payload)
    assert spec.study_spec_id.startswith("sspec_")
    assert spec.alpha_spec_id.startswith("aspec_")
    assert spec.label_spec_id.startswith("lspec_")
    assert spec.variant_budget == 4
    assert spec.negative_controls == [
        "random target control",
        "permuted labels control",
        "future shift control",
        "optimistic fill control",
    ]


@pytest.mark.parametrize("field", STUDY_SPEC_REQUIRED_FIELDS)
def test_study_spec_rejects_each_missing_required_field(field: str) -> None:
    payload = load_valid_study_spec_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", STUDY_SPEC_REQUIRED_FIELDS)
def test_study_spec_rejects_each_null_required_field(field: str) -> None:
    payload = load_valid_study_spec_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("study_spec_id", "aspec_af848bc999a4c4b11a421bd0", "unexpected_kind"),
        ("alpha_spec_id", "lspec_8663589ca7a9f1e5859289c7", "unexpected_kind"),
        ("label_spec_id", "aspec_af848bc999a4c4b11a421bd0", "unexpected_kind"),
        ("dataset_scope", {}, "empty_required_field"),
        ("split_protocol", {}, "empty_required_field"),
        ("metrics", [], "empty_required_field"),
        ("cost_assumptions", {}, "empty_required_field"),
        ("variant_budget", 0, "invalid_variant_budget"),
        ("variant_budget", "unbounded", "invalid_field_type"),
        ("locked_test_policy", {}, "empty_required_field"),
        (
            "locked_test_policy",
            {"contact_flag": False},
            "missing_locked_test_declaration",
        ),
        ("negative_controls", [], "empty_required_field"),
        ("stopping_rules", [], "empty_required_field"),
    ],
)
def test_study_spec_rejects_invalid_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = load_valid_study_spec_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_study_spec_rejects_id_that_does_not_match_content() -> None:
    payload = load_valid_study_spec_payload()
    changed = deepcopy(payload)
    changed["metrics"] = ["rank_ic", "turnover", "coverage", "synthetic_hit_rate"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(changed)

    assert exc_info.value.issues[0].code == "study_spec_id_mismatch"
    assert exc_info.value.issues[0].field == "study_spec_id"


def test_study_spec_rejects_unknown_fields_without_dropping_them() -> None:
    payload = load_valid_study_spec_payload()
    payload["diagnostics_passed"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "diagnostics_passed" in payload


def test_study_spec_rejects_non_serializable_nested_values() -> None:
    payload = load_valid_study_spec_payload()
    dataset_scope = dict(payload["dataset_scope"])
    dataset_scope["bad"] = object()
    payload["dataset_scope"] = dataset_scope

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(payload)

    assert exc_info.value.issues[0].code == "unsupported_value_type"


def test_study_spec_canonical_round_trip_is_deterministic() -> None:
    payload = load_valid_study_spec_payload()
    reordered = dict(reversed(list(payload.items())))

    spec = validate_study_spec(payload)
    serialized = spec.to_canonical_json()
    round_tripped = StudySpec.from_canonical_json(serialized)

    assert round_tripped == spec
    assert deserialize(serialized) == spec.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_study_spec_generates_content_bound_id() -> None:
    payload = load_valid_study_spec_payload()

    spec = create_study_spec(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        label_spec_id=str(payload["label_spec_id"]),
        dataset_scope=dict(payload["dataset_scope"]),
        split_protocol=dict(payload["split_protocol"]),
        metrics=list(payload["metrics"]),
        cost_assumptions=dict(payload["cost_assumptions"]),
        variant_budget=int(payload["variant_budget"]),
        locked_test_policy=dict(payload["locked_test_policy"]),
        negative_controls=list(payload["negative_controls"]),
        stopping_rules=list(payload["stopping_rules"]),
    )

    assert spec.study_spec_id == payload["study_spec_id"]
    assert spec.study_spec_id.startswith("sspec_")


def test_diagnostics_gate_allows_only_valid_study_spec() -> None:
    payload = load_valid_study_spec_payload()

    spec = validate_diagnostics_gate(payload)

    assert spec == validate_study_spec(payload)


def test_diagnostics_gate_blocks_without_study_spec() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_diagnostics_gate(None)

    issue = exc_info.value.issues[0]
    assert issue.code == "missing_study_spec"
    assert issue.field == "study_spec"


def test_diagnostics_gate_blocks_invalid_study_spec() -> None:
    payload = load_valid_study_spec_payload()
    payload["variant_budget"] = -1

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_diagnostics_gate(payload)

    assert exc_info.value.issues[0].code == "invalid_variant_budget"
    assert exc_info.value.issues[0].field == "variant_budget"


def test_diagnostics_gate_rejects_other_transitions() -> None:
    payload = load_valid_study_spec_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_diagnostics_gate(
            payload,
            from_state="DIAGNOSTICS_ALLOWED",
            to_state="DIAGNOSTICS_RUN",
        )

    issue = exc_info.value.issues[0]
    assert issue.code == "unsupported_diagnostics_gate_transition"
    assert issue.expected == f"{IMPLEMENTED_STATE}->{DIAGNOSTICS_ALLOWED_STATE}"
