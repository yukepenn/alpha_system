from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.alpha_spec import (
    IMPLEMENTATION_ALLOWED_STATE,
    REGISTERED_STATE,
    assert_implementation_allowed,
    validate_no_code_gate,
)
from alpha_system.governance.validation import GovernanceValidationError


FIXTURE_PATH = Path("tests/fixtures/governance/alpha_spec_valid.json")


def load_valid_alpha_spec_payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_no_code_gate_blocks_missing_alpha_spec() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_no_code_gate(None)

    assert exc_info.value.issues[0].code == "missing_alpha_spec"
    assert exc_info.value.issues[0].field == "alpha_spec"


def test_no_code_gate_blocks_invalid_alpha_spec() -> None:
    payload = load_valid_alpha_spec_payload()
    payload["promotion_criteria"] = []

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_no_code_gate(payload)

    assert exc_info.value.issues[0].code == "empty_required_field"


def test_no_code_gate_allows_registered_to_implementation_allowed_with_valid_spec() -> None:
    payload = load_valid_alpha_spec_payload()

    spec = validate_no_code_gate(
        payload,
        from_state=REGISTERED_STATE,
        to_state=IMPLEMENTATION_ALLOWED_STATE,
    )

    assert spec.alpha_spec_id == payload["alpha_spec_id"]
    assert assert_implementation_allowed(spec) == spec


def test_no_code_gate_rejects_other_transition_use() -> None:
    payload = load_valid_alpha_spec_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_no_code_gate(payload, from_state="IMPLEMENTED", to_state="DIAGNOSTICS_ALLOWED")

    assert exc_info.value.issues[0].code == "unsupported_no_code_gate_transition"
