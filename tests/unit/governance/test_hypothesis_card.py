from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.hypothesis_card import (
    HYPOTHESIS_CARD_REQUIRED_FIELDS,
    HypothesisCard,
    generate_hypothesis_id,
    validate_hypothesis_card,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/hypothesis_card_valid.json")


def load_valid_hypothesis_card_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_hypothesis_card_fixture_contains_all_required_fields() -> None:
    payload = load_valid_hypothesis_card_payload()

    card = validate_hypothesis_card(payload)

    assert isinstance(card, HypothesisCard)
    assert tuple(card.to_dict()) == HYPOTHESIS_CARD_REQUIRED_FIELDS
    assert card.hypothesis_id == generate_hypothesis_id(payload)
    assert card.hypothesis_id.startswith("hyp_")


def test_hypothesis_card_canonical_round_trip_is_deterministic() -> None:
    payload = load_valid_hypothesis_card_payload()
    reordered = dict(reversed(list(payload.items())))

    card = validate_hypothesis_card(payload)
    serialized = card.to_canonical_json()
    round_tripped = HypothesisCard.from_canonical_json(serialized)

    assert round_tripped == card
    assert deserialize(serialized) == card.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_hypothesis_card_rejects_missing_required_field() -> None:
    payload = load_valid_hypothesis_card_payload()
    del payload["expected_mechanism"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == "expected_mechanism"


def test_hypothesis_card_rejects_null_required_field() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["rationale"] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == "rationale"


def test_hypothesis_card_rejects_unknown_fields_without_dropping_them() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["implementation_allowed"] = False

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "implementation_allowed" in payload


def test_hypothesis_card_rejects_malformed_hypothesis_id() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["hypothesis_id"] = "aspec_af848bc999a4c4b11a421bd0"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "unexpected_kind"
    assert exc_info.value.issues[0].field == "hypothesis_id"


def test_hypothesis_card_rejects_empty_required_text() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["title"] = " "

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "empty_required_field"
    assert exc_info.value.issues[0].field == "title"


def test_hypothesis_card_rejects_vague_substantive_text() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["expected_mechanism"] = "TBD"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "vague_required_field"
    assert exc_info.value.issues[0].field == "expected_mechanism"


def test_hypothesis_card_rejects_empty_falsification_criteria() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["falsification_criteria"] = []

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "empty_required_field"
    assert exc_info.value.issues[0].field == "falsification_criteria"


def test_hypothesis_card_rejects_placeholder_falsification_criteria() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["falsification_criteria"] = ["placeholder"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "vague_required_field"
    assert exc_info.value.issues[0].field == "falsification_criteria[0]"


def test_hypothesis_card_rejects_falsification_without_rejection_condition() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["falsification_criteria"] = [
        "Future governance will review the research narrative using ordinary documentation."
    ]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "missing_falsification_condition"
    assert exc_info.value.issues[0].field == "falsification_criteria[0]"


def test_hypothesis_card_rejects_non_serializable_nested_values() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["risks"] = [
        "This synthetic risk is sufficiently detailed for validation.",
        object(),
    ]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "invalid_item_type"
    assert exc_info.value.issues[0].field == "risks[1]"


def test_hypothesis_card_rejects_malformed_created_at() -> None:
    payload = load_valid_hypothesis_card_payload()
    payload["created_at"] = "2026-06-03T13:52:09"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(payload)

    assert exc_info.value.issues[0].code == "missing_timestamp_timezone"
    assert exc_info.value.issues[0].field == "created_at"


def test_hypothesis_card_rejects_id_that_does_not_match_content() -> None:
    payload = load_valid_hypothesis_card_payload()
    changed = deepcopy(payload)
    changed["family"] = "synthetic fixture governance"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_hypothesis_card(changed)

    assert exc_info.value.issues[0].code == "hypothesis_id_mismatch"
    assert exc_info.value.issues[0].field == "hypothesis_id"
