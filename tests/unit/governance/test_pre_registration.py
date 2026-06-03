from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.alpha_spec import generate_alpha_spec_id
from alpha_system.governance.hypothesis_card import (
    DRAFT_STATE,
    REGISTERED_STATE,
    RegisteredResearchPair,
    assert_pre_registered,
    validate_pre_registration,
)
from alpha_system.governance.validation import GovernanceValidationError


CARD_FIXTURE_PATH = Path("tests/fixtures/governance/hypothesis_card_valid.json")
SPEC_FIXTURE_PATH = Path("tests/fixtures/governance/alpha_spec_valid.json")


def load_valid_hypothesis_card_payload() -> dict[str, object]:
    return json.loads(CARD_FIXTURE_PATH.read_text(encoding="utf-8"))


def load_valid_alpha_spec_payload() -> dict[str, object]:
    return json.loads(SPEC_FIXTURE_PATH.read_text(encoding="utf-8"))


def linked_alpha_spec_payload(card_payload: dict[str, object]) -> dict[str, object]:
    payload = load_valid_alpha_spec_payload()
    payload["hypothesis_id"] = card_payload["hypothesis_id"]
    payload["alpha_spec_id"] = generate_alpha_spec_id(payload)
    return payload


def test_pre_registration_blocks_missing_hypothesis_card() -> None:
    spec_payload = load_valid_alpha_spec_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(None, spec_payload)

    assert exc_info.value.issues[0].code == "missing_hypothesis_card"
    assert exc_info.value.issues[0].field == "hypothesis_card"


def test_pre_registration_blocks_missing_alpha_spec() -> None:
    card_payload = load_valid_hypothesis_card_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(card_payload, None)

    assert exc_info.value.issues[0].code == "missing_alpha_spec"
    assert exc_info.value.issues[0].field == "alpha_spec"


def test_pre_registration_blocks_invalid_hypothesis_card() -> None:
    card_payload = load_valid_hypothesis_card_payload()
    card_payload["falsification_criteria"] = ["TBD"]
    spec_payload = linked_alpha_spec_payload(load_valid_hypothesis_card_payload())

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(card_payload, spec_payload)

    assert exc_info.value.issues[0].code == "vague_required_field"
    assert exc_info.value.issues[0].field == "falsification_criteria[0]"


def test_pre_registration_blocks_invalid_alpha_spec() -> None:
    card_payload = load_valid_hypothesis_card_payload()
    spec_payload = linked_alpha_spec_payload(card_payload)
    spec_payload["expected_failure_modes"] = []

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(card_payload, spec_payload)

    assert exc_info.value.issues[0].code == "empty_required_field"
    assert exc_info.value.issues[0].field == "expected_failure_modes"


def test_pre_registration_blocks_mismatched_hypothesis_id() -> None:
    card_payload = load_valid_hypothesis_card_payload()
    spec_payload = load_valid_alpha_spec_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(card_payload, spec_payload)

    assert exc_info.value.issues[0].code == "hypothesis_id_mismatch"
    assert exc_info.value.issues[0].field == "alpha_spec.hypothesis_id"


def test_pre_registration_rejects_other_transition_use() -> None:
    card_payload = load_valid_hypothesis_card_payload()
    spec_payload = linked_alpha_spec_payload(card_payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_pre_registration(
            card_payload,
            spec_payload,
            from_state=REGISTERED_STATE,
            to_state="IMPLEMENTATION_ALLOWED",
        )

    assert exc_info.value.issues[0].code == "unsupported_pre_registration_transition"
    assert exc_info.value.issues[0].field == "transition"


def test_pre_registration_returns_valid_linked_pair() -> None:
    card_payload = load_valid_hypothesis_card_payload()
    spec_payload = linked_alpha_spec_payload(card_payload)

    pair = validate_pre_registration(
        card_payload,
        spec_payload,
        from_state=DRAFT_STATE,
        to_state=REGISTERED_STATE,
    )

    assert isinstance(pair, RegisteredResearchPair)
    assert pair.hypothesis_card.hypothesis_id == card_payload["hypothesis_id"]
    assert pair.alpha_spec.hypothesis_id == pair.hypothesis_card.hypothesis_id
    assert assert_pre_registered(pair.hypothesis_card, pair.alpha_spec) == pair
