from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.alpha_spec import (
    ALPHA_SPEC_REQUIRED_FIELDS,
    AlphaSpec,
    generate_alpha_spec_id,
    validate_alpha_spec,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/alpha_spec_valid.json")


def load_valid_alpha_spec_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_alpha_spec_fixture_contains_all_required_fields() -> None:
    payload = load_valid_alpha_spec_payload()

    spec = validate_alpha_spec(payload)

    assert isinstance(spec, AlphaSpec)
    assert tuple(spec.to_dict()) == ALPHA_SPEC_REQUIRED_FIELDS
    assert spec.alpha_spec_id == generate_alpha_spec_id(payload)
    assert spec.hypothesis_id.startswith("hyp_")
    assert spec.label_references == ["lspec_d3c81d3601f3b4b30c08a9a6"]


def test_alpha_spec_canonical_round_trip_is_deterministic() -> None:
    payload = load_valid_alpha_spec_payload()
    reordered = dict(reversed(list(payload.items())))

    spec = validate_alpha_spec(payload)
    serialized = spec.to_canonical_json()
    round_tripped = AlphaSpec.from_canonical_json(serialized)

    assert round_tripped == spec
    assert deserialize(serialized) == spec.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_alpha_spec_rejects_missing_required_field() -> None:
    payload = load_valid_alpha_spec_payload()
    del payload["promotion_criteria"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == "promotion_criteria"


def test_alpha_spec_rejects_empty_required_collection() -> None:
    payload = load_valid_alpha_spec_payload()
    payload["expected_failure_modes"] = []

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(payload)

    assert exc_info.value.issues[0].code == "empty_required_field"
    assert exc_info.value.issues[0].field == "expected_failure_modes"


def test_alpha_spec_rejects_vague_substantive_assumption() -> None:
    payload = load_valid_alpha_spec_payload()
    payload["data_assumptions"] = {"source": "TBD"}

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(payload)

    assert exc_info.value.issues[0].code == "vague_required_field"
    assert exc_info.value.issues[0].field == "data_assumptions.source"


def test_alpha_spec_rejects_malformed_reference_ids() -> None:
    payload = load_valid_alpha_spec_payload()
    payload["hypothesis_id"] = "aspec_af848bc999a4c4b11a421bd0"
    payload["label_references"] = ["not-a-label-id"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(payload)

    assert [issue.field for issue in exc_info.value.issues] == [
        "hypothesis_id",
        "label_references[0]",
    ]


def test_alpha_spec_rejects_id_that_does_not_match_content() -> None:
    payload = load_valid_alpha_spec_payload()
    changed = deepcopy(payload)
    changed["target_instruments"] = ["SYNTH_US_EQUITY_SMALL_CAP"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(changed)

    assert exc_info.value.issues[0].code == "alpha_spec_id_mismatch"
    assert exc_info.value.issues[0].field == "alpha_spec_id"


def test_alpha_spec_rejects_unknown_fields_without_dropping_them() -> None:
    payload = load_valid_alpha_spec_payload()
    payload["candidate_status"] = "not allowed"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_alpha_spec(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "candidate_status" in payload
