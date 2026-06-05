from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance import study_input_pack as input_pack_module
from alpha_system.governance import study_spec as study_spec_module
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.study_input_pack import (
    STUDY_INPUT_PACK_REQUIRED_FIELDS,
    StudyInputPack,
    create_study_input_pack,
    validate_study_input_pack,
    validate_study_input_pack_references,
)
from alpha_system.governance.study_spec import generate_study_spec_id
from alpha_system.governance.validation import GovernanceValidationError

FEATURE_REQUEST_FIXTURE = Path("tests/fixtures/governance/feature_request_valid.json")
LABEL_SPEC_FIXTURE = Path("tests/fixtures/governance/label_spec_valid.json")
ALPHA_SPEC_FIXTURE = Path("tests/fixtures/governance/alpha_spec_valid.json")
STUDY_SPEC_FIXTURE = Path("tests/fixtures/governance/study_spec_valid.json")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def valid_pack_payload() -> dict[str, object]:
    feature_request = load_json(FEATURE_REQUEST_FIXTURE)
    label_spec = load_json(LABEL_SPEC_FIXTURE)
    study_spec = load_json(STUDY_SPEC_FIXTURE)
    return {
        "feature_request_ids": [feature_request["feature_request_id"]],
        "label_spec_ids": [label_spec["label_spec_id"]],
        "alpha_spec_id": feature_request["alpha_spec_id"],
        "dataset_scope": deepcopy(study_spec["dataset_scope"]),
    }


def test_study_input_pack_validates_and_round_trips_canonically() -> None:
    payload = valid_pack_payload()
    reordered = dict(reversed(list(payload.items())))

    pack = validate_study_input_pack(payload)
    serialized = pack.to_canonical_json()
    round_tripped = StudyInputPack.from_canonical_json(serialized)

    assert isinstance(pack, StudyInputPack)
    assert tuple(pack.to_dict()) == STUDY_INPUT_PACK_REQUIRED_FIELDS
    assert pack == round_tripped
    assert hash(pack) == hash(round_tripped)
    assert pack.feature_request_ids == tuple(payload["feature_request_ids"])
    assert pack.label_spec_ids == tuple(payload["label_spec_ids"])
    assert pack.alpha_spec_id == payload["alpha_spec_id"]
    assert pack.dataset_scope == payload["dataset_scope"]
    assert deserialize(serialized) == pack.to_dict()
    assert canonical_serialize(reordered) == serialized

    returned_scope = pack.dataset_scope
    returned_scope["local_mutation"] = "does not mutate the pack"
    assert "local_mutation" not in pack.dataset_scope


def test_create_study_input_pack_uses_the_same_validation_surface() -> None:
    payload = valid_pack_payload()

    created = create_study_input_pack(
        feature_request_ids=list(payload["feature_request_ids"]),
        label_spec_ids=list(payload["label_spec_ids"]),
        alpha_spec_id=str(payload["alpha_spec_id"]),
        dataset_scope=dict(payload["dataset_scope"]),
    )

    assert created == validate_study_input_pack(payload)


def test_study_input_pack_resolved_contract_validation_consumes_public_validators() -> None:
    payload = valid_pack_payload()
    feature_request = load_json(FEATURE_REQUEST_FIXTURE)
    label_spec = load_json(LABEL_SPEC_FIXTURE)
    alpha_spec = load_json(ALPHA_SPEC_FIXTURE)
    study_spec = load_json(STUDY_SPEC_FIXTURE)

    pack = validate_study_input_pack_references(
        payload,
        feature_requests=[feature_request],
        label_specs=[label_spec],
        alpha_spec=alpha_spec,
        study_spec=study_spec,
    )

    assert pack.to_dict() == validate_study_input_pack(payload).to_dict()


def test_resolved_study_spec_reference_must_match_pack_dataset_scope() -> None:
    payload = valid_pack_payload()
    study_spec = load_json(STUDY_SPEC_FIXTURE)
    study_spec["dataset_scope"] = {
        "instrument_universe": "DIFFERENT_SYNTHETIC_FIXTURE_UNIVERSE",
        "source": "different synthetic fixture metadata, not market data",
        "time_range": "2026-02-01 through 2026-02-28 synthetic timestamps",
    }
    study_spec["study_spec_id"] = generate_study_spec_id(study_spec)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_input_pack_references(payload, study_spec=study_spec)

    assert exc_info.value.issues[0].code == "study_spec_dataset_scope_mismatch"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("feature_request_ids", ["not-a-governance-id"], "malformed_id"),
        ("feature_request_ids", ["lspec_8663589ca7a9f1e5859289c7"], "unexpected_prefix"),
        ("feature_request_ids", ["zzzz_000000000000000000000000"], "unknown_prefix"),
        ("alpha_spec_id", "lspec_8663589ca7a9f1e5859289c7", "unexpected_prefix"),
        ("feature_request_ids", [], "empty_required_field"),
        ("label_spec_ids", [], "empty_required_field"),
        (
            "feature_request_ids",
            ["freq_eb180e1226ce34c048c7e6eb", "freq_eb180e1226ce34c048c7e6eb"],
            "duplicate_governance_id",
        ),
        (
            "label_spec_ids",
            ["lspec_8663589ca7a9f1e5859289c7", "lspec_8663589ca7a9f1e5859289c7"],
            "duplicate_governance_id",
        ),
        ("dataset_scope", {}, "empty_required_field"),
        ("dataset_scope", {"source": "TBD"}, "vague_required_field"),
        ("dataset_scope", {"source": []}, "empty_required_field"),
    ],
)
def test_study_input_pack_rejects_invalid_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_pack_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_input_pack(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_study_input_pack_rejects_non_serializable_dataset_scope() -> None:
    payload = valid_pack_payload()
    dataset_scope = dict(payload["dataset_scope"])
    dataset_scope["bad"] = object()
    payload["dataset_scope"] = dataset_scope

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_input_pack(payload)

    assert exc_info.value.issues[0].code == "unsupported_value_type"


def test_study_input_pack_does_not_mutate_study_spec_schema_or_private_helpers() -> None:
    required_fields_before = study_spec_module.STUDY_SPEC_REQUIRED_FIELDS
    dataclass_fields_before = tuple(study_spec_module.StudySpec.__dataclass_fields__)
    source = inspect.getsource(input_pack_module)

    validate_study_input_pack(valid_pack_payload())

    assert study_spec_module.STUDY_SPEC_REQUIRED_FIELDS == required_fields_before
    assert tuple(study_spec_module.StudySpec.__dataclass_fields__) == dataclass_fields_before
    assert "study_input_pack" not in study_spec_module.StudySpec.__dataclass_fields__
    assert "from alpha_system.governance.study_spec import _" not in source
    assert "from alpha_system.governance.feature_request import _" not in source
    assert "from alpha_system.governance.label_spec import _" not in source
