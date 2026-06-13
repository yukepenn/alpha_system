from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP, create_mechanism_card
from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.setup_spec import (
    SETUP_SPEC_REQUIRED_FIELDS,
    SetupSpec,
    create_setup_spec,
    generate_setup_spec_id,
    validate_setup_spec,
)
from alpha_system.governance.validation import GovernanceValidationError


def valid_mechanism_id() -> str:
    return create_mechanism_card(
        source="SSRL synthetic fixture for setup contract tests",
        rationale=(
            "A compressed context can make a later reclaim event informative "
            "when the path outcome remains bounded by a declared label."
        ),
        expected_mechanism=(
            "The mechanism expects a separate event trigger to reveal post-sweep "
            "demand while the context only gates when the setup is considered."
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
            "assumption": "reject if cost-adjusted path outcome is not robust enough",
        },
        variant_budget=3,
        duplicate_exposure={
            "status": "checked",
            "note": "No equivalent setup is declared in the fixture registry review.",
        },
    ).mechanism_id


def valid_path_label_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "path", "name": "target_before_stop", "version": 1},
    )


def valid_setup_payload() -> dict[str, object]:
    return create_setup_spec(
        entry_context={
            "feature": "range_contraction_context_bucket",
            "condition": "lower volatility bucket is observed before decision time",
        },
        event_trigger={
            "feature": "prior_high_sweep_reclaim_trigger",
            "condition": "sweep occurs and bar closes back inside the prior high",
        },
        regime_filter={
            "session": "RTH",
            "allowed_regime": "liquid regular trading hours only",
        },
        confirmation={
            "rule": "next bar holds above the reclaimed reference level",
        },
        invalidation={
            "rule": "setup is invalid if reclaim level is lost before entry",
        },
        stop={
            "binding": "path label stop side from the governed label specification",
        },
        target={
            "binding": "path label target side from the governed label specification",
        },
        hold_time={
            "max_minutes": 120,
            "policy": "close the exploratory path after the declared horizon",
        },
        horizon="120m",
        path_label=valid_path_label_id(),
        allowed_variants=["baseline", "stricter confirmation"],
        forbidden_post_hoc_changes=[
            "Do not change context buckets after reading outcomes.",
            "Do not change target or stop binding after reading outcomes.",
        ],
        mechanism_id=valid_mechanism_id(),
    ).to_dict()


def test_valid_setup_spec_payload_contains_all_required_fields() -> None:
    payload = valid_setup_payload()

    spec = validate_setup_spec(payload)

    assert isinstance(spec, SetupSpec)
    assert tuple(spec.to_dict()) == SETUP_SPEC_REQUIRED_FIELDS
    assert spec.setup_spec_id == generate_setup_spec_id(payload)
    assert spec.setup_spec_id.startswith("setup_")
    assert spec.mechanism_id.startswith("mech_")
    assert spec.path_label.startswith("lspec_")
    assert spec.stamp == EXPLORATORY_STAMP
    assert spec.entry_context != spec.event_trigger


@pytest.mark.parametrize("field", SETUP_SPEC_REQUIRED_FIELDS)
def test_setup_spec_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_setup_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize("field", SETUP_SPEC_REQUIRED_FIELDS)
def test_setup_spec_rejects_each_null_required_field(field: str) -> None:
    payload = valid_setup_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entry_context", "context"),
        ("event_trigger", "trigger"),
        ("hold_time", []),
        ("path_label", 123),
        ("allowed_variants", {}),
        ("forbidden_post_hoc_changes", {}),
    ],
)
def test_setup_spec_rejects_invalid_field_types(field: str, value: object) -> None:
    payload = valid_setup_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "invalid_field_type"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("entry_context", {}, "empty_required_field"),
        ("entry_context", {"feature": "TBD"}, "vague_required_field"),
        ("event_trigger", {}, "empty_required_field"),
        ("allowed_variants", [], "empty_required_field"),
        ("forbidden_post_hoc_changes", ["placeholder"], "empty_required_field"),
        ("horizon", "TBD", "empty_required_field"),
        ("stamp", "TRUSTED", "invalid_stamp"),
    ],
)
def test_setup_spec_rejects_vague_or_invalid_values(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_setup_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_setup_spec_rejects_wrong_mechanism_kind() -> None:
    payload = valid_setup_payload()
    payload["mechanism_id"] = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"fixture": "not a mechanism"},
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "unexpected_kind"
    assert exc_info.value.issues[0].field == "mechanism_id"


def test_setup_spec_rejects_wrong_path_label_kind() -> None:
    payload = valid_setup_payload()
    payload["path_label"] = generate_governance_id(
        GovernanceIdKind.MECHANISM_CARD,
        {"fixture": "not a label"},
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "unexpected_kind"
    assert exc_info.value.issues[0].field == "path_label"


def test_setup_spec_rejects_unknown_fields_without_dropping_them() -> None:
    payload = valid_setup_payload()
    payload["promotion_eligible"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "promotion_eligible" in payload


def test_setup_spec_rejects_id_that_does_not_match_content() -> None:
    payload = valid_setup_payload()
    changed = deepcopy(payload)
    changed["horizon"] = "240m"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(changed)

    assert exc_info.value.issues[0].code == "setup_spec_id_mismatch"
    assert exc_info.value.issues[0].field == "setup_spec_id"


def test_setup_spec_id_is_deterministic_and_changes_with_component_content() -> None:
    payload = valid_setup_payload()
    reordered = dict(reversed(list(payload.items())))
    changed = deepcopy(payload)
    changed["hold_time"] = {
        "max_minutes": 60,
        "policy": "close the exploratory path after the shorter declared horizon",
    }

    assert generate_setup_spec_id(payload) == payload["setup_spec_id"]
    assert generate_setup_spec_id(reordered) == payload["setup_spec_id"]
    assert generate_setup_spec_id(changed) != payload["setup_spec_id"]


def test_setup_spec_canonical_round_trip_is_deterministic() -> None:
    payload = valid_setup_payload()
    reordered = dict(reversed(list(payload.items())))

    setup = validate_setup_spec(payload)
    serialized = setup.to_canonical_json()
    round_tripped = SetupSpec.from_canonical_json(serialized)

    assert round_tripped == setup
    assert deserialize(serialized) == setup.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_setup_spec_defaults_to_exploratory_stamp_and_links_mechanism() -> None:
    mechanism_id = valid_mechanism_id()
    setup = create_setup_spec(
        entry_context={
            "feature": "range_contraction_context_bucket",
            "condition": "context gate is evaluated before the event trigger",
        },
        event_trigger={
            "feature": "prior_high_sweep_reclaim_trigger",
            "condition": "event trigger is evaluated separately from the context gate",
        },
        regime_filter={"session": "RTH"},
        confirmation={"rule": "confirm only after the trigger bar completes"},
        invalidation={"rule": "invalidate if the trigger level is lost before entry"},
        stop={"binding": "governed path label stop side"},
        target={"binding": "governed path label target side"},
        hold_time={"max_minutes": 120},
        horizon="120m",
        path_label=valid_path_label_id(),
        allowed_variants=["baseline"],
        forbidden_post_hoc_changes=["Do not change declared trigger after outcomes."],
        mechanism_id=mechanism_id,
    )

    assert setup.stamp == EXPLORATORY_STAMP
    assert setup.mechanism_id == mechanism_id
    assert setup.setup_spec_id == generate_setup_spec_id(setup.to_dict())


def test_event_trigger_is_required_as_a_separate_field() -> None:
    payload = valid_setup_payload()
    del payload["event_trigger"]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == "event_trigger"


def test_event_trigger_must_not_alias_entry_context_object() -> None:
    payload = valid_setup_payload()
    shared = {
        "feature": "range_contraction_context_bucket",
        "condition": "same object is not an independent event trigger",
    }
    payload["entry_context"] = shared
    payload["event_trigger"] = shared

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "event_trigger_aliases_entry_context"
    assert exc_info.value.issues[0].field == "event_trigger"


def test_event_trigger_must_not_duplicate_entry_context_content() -> None:
    payload = valid_setup_payload()
    payload["event_trigger"] = dict(payload["entry_context"])

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "event_trigger_matches_entry_context"
    assert exc_info.value.issues[0].field == "event_trigger"


def test_event_trigger_must_not_be_derived_from_entry_context() -> None:
    payload = valid_setup_payload()
    payload["event_trigger"] = {
        "derived_from": "entry_context",
        "condition": "aliasing the context gate is not a separate event trigger",
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "event_trigger_derived_from_entry_context"
    assert exc_info.value.issues[0].field == "event_trigger"


def test_setup_spec_rejects_non_serializable_nested_values() -> None:
    payload = valid_setup_payload()
    payload["confirmation"] = {"bad": object()}

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_setup_spec(payload)

    assert exc_info.value.issues[0].code == "unsupported_value_type"
