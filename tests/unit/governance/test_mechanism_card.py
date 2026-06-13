from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MECHANISM_CARD_REQUIRED_FIELDS,
    MechanismCard,
    create_mechanism_card,
    generate_mechanism_id,
    validate_mechanism_card,
)
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.validation import GovernanceValidationError


def valid_mechanism_payload() -> dict[str, object]:
    return create_mechanism_card(
        source="SSRL synthetic fixture for strategy-shaped contract tests",
        rationale=(
            "Session compression followed by a clean sweep can expose resting "
            "liquidity and define a bounded exploratory path outcome."
        ),
        expected_mechanism=(
            "The setup expects volatility expansion after a liquidity sweep, "
            "with continuation only if the reclaim trigger confirms."
        ),
        expected_direction="long after bullish reclaim trigger",
        horizon="120m",
        session="RTH",
        required_features=[
            "range_contraction_context_bucket",
            "prior_high_sweep_reclaim_trigger",
        ],
        required_labels=["path_target_before_stop_label_spec"],
        cost_sensitivity={
            "assumption": "reject if expected edge is only visible before transaction costs",
            "tracked_costs": ["fees", "slippage"],
        },
        variant_budget=3,
        duplicate_exposure={
            "status": "checked",
            "note": "No equivalent governed exposure is declared in the synthetic fixture.",
        },
    ).to_dict()


def test_valid_mechanism_card_payload_contains_all_required_fields() -> None:
    payload = valid_mechanism_payload()

    card = validate_mechanism_card(payload)

    assert isinstance(card, MechanismCard)
    assert tuple(card.to_dict()) == MECHANISM_CARD_REQUIRED_FIELDS
    assert card.mechanism_id == generate_mechanism_id(payload)
    assert card.mechanism_id.startswith("mech_")
    assert card.stamp == EXPLORATORY_STAMP


@pytest.mark.parametrize("field", MECHANISM_CARD_REQUIRED_FIELDS)
def test_mechanism_card_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_mechanism_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", MECHANISM_CARD_REQUIRED_FIELDS)
def test_mechanism_card_rejects_each_null_required_field(field: str) -> None:
    payload = valid_mechanism_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", 123),
        ("required_features", "range_contraction_context_bucket"),
        ("required_labels", "path_target_before_stop_label_spec"),
        ("cost_sensitivity", []),
        ("duplicate_exposure", []),
        ("variant_budget", "unbounded"),
    ],
)
def test_mechanism_card_rejects_invalid_field_types(field: str, value: object) -> None:
    payload = valid_mechanism_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == "invalid_field_type"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("rationale", "TBD", "vague_required_field"),
        ("required_features", [], "empty_required_field"),
        ("required_labels", ["placeholder"], "empty_required_field"),
        ("cost_sensitivity", {}, "empty_required_field"),
        ("cost_sensitivity", {"basis": "TBD"}, "vague_required_field"),
        ("variant_budget", 0, "invalid_variant_budget"),
        ("stamp", "TRUSTED", "invalid_stamp"),
    ],
)
def test_mechanism_card_rejects_vague_or_invalid_values(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_mechanism_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_mechanism_card_rejects_unknown_fields_without_dropping_them() -> None:
    payload = valid_mechanism_payload()
    payload["promotion_eligible"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "promotion_eligible" in payload


def test_mechanism_card_rejects_id_that_does_not_match_content() -> None:
    payload = valid_mechanism_payload()
    changed = deepcopy(payload)
    changed["expected_direction"] = "short after bearish rejection trigger"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(changed)

    assert exc_info.value.issues[0].code == "mechanism_id_mismatch"
    assert exc_info.value.issues[0].field == "mechanism_id"


def test_mechanism_card_id_is_deterministic_and_changes_with_component_content() -> None:
    payload = valid_mechanism_payload()
    reordered = dict(reversed(list(payload.items())))
    changed = deepcopy(payload)
    changed["horizon"] = "240m"

    assert generate_mechanism_id(payload) == payload["mechanism_id"]
    assert generate_mechanism_id(reordered) == payload["mechanism_id"]
    assert generate_mechanism_id(changed) != payload["mechanism_id"]


def test_mechanism_card_canonical_round_trip_is_deterministic() -> None:
    payload = valid_mechanism_payload()
    reordered = dict(reversed(list(payload.items())))

    card = validate_mechanism_card(payload)
    serialized = card.to_canonical_json()
    round_tripped = MechanismCard.from_canonical_json(serialized)

    assert round_tripped == card
    assert deserialize(serialized) == card.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_mechanism_card_defaults_to_exploratory_stamp() -> None:
    payload = valid_mechanism_payload()

    card = create_mechanism_card(
        source=str(payload["source"]),
        rationale=str(payload["rationale"]),
        expected_mechanism=str(payload["expected_mechanism"]),
        expected_direction=str(payload["expected_direction"]),
        horizon=str(payload["horizon"]),
        session=str(payload["session"]),
        required_features=list(payload["required_features"]),
        required_labels=list(payload["required_labels"]),
        cost_sensitivity=dict(payload["cost_sensitivity"]),
        variant_budget=int(payload["variant_budget"]),
        duplicate_exposure=dict(payload["duplicate_exposure"]),
    )

    assert card.stamp == EXPLORATORY_STAMP
    assert card.mechanism_id == generate_mechanism_id(card.to_dict())


def test_mechanism_card_rejects_non_serializable_nested_values() -> None:
    payload = valid_mechanism_payload()
    payload["cost_sensitivity"] = {"bad": object()}

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_mechanism_card(payload)

    assert exc_info.value.issues[0].code == "unsupported_value_type"
