from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from alpha_system.governance.track_a_migration import (
    TRACK_A_CARD_DIR,
    TRACK_A_GOVERNANCE_PATH,
    legacy_label_reference_id,
    load_track_a_cards,
    load_track_a_governance,
    migrate_all_track_a_cards,
    migrate_track_a_card,
    write_migrated_track_a_cards,
)
from alpha_system.governance.validation import GovernanceValidationError


def test_track_a_migration_maps_all_legacy_cards_to_canonical_fields() -> None:
    cards = {card["mechanism_id"]: card for _, card in load_track_a_cards()}
    governance = load_track_a_governance()
    migrations = migrate_all_track_a_cards()

    assert set(cards) == {record.slug for record in migrations}
    assert len(migrations) == 8
    for record in migrations:
        card = cards[record.slug]
        card_governance = governance["cards"][record.slug]
        mechanism = record.bundle.mechanism_card
        alpha_spec = record.bundle.alpha_spec
        idea_draft = record.bundle.idea_draft

        assert re.fullmatch(r"mech_[a-f0-9]{24}", mechanism.mechanism_id)
        assert mechanism.mechanism_id != record.slug
        assert mechanism.source == f"track_a:{record.slug}"
        assert mechanism.rationale == card["hypothesis"]["economic_rationale"]
        assert mechanism.expected_mechanism == card["hypothesis"]["statement"]
        assert mechanism.expected_direction == card["expected_sign"]
        assert mechanism.horizon == card_governance["primary_horizon"]
        assert mechanism.horizon in card["expected_horizon"]
        assert mechanism.session == card["expected_session"]
        assert mechanism.required_features == card["required_features"]["existing"]
        assert mechanism.required_labels == card["required_labels"]["existing"]
        assert mechanism.cost_sensitivity == card_governance["cost_sensitivity"]
        assert mechanism.variant_budget == card_governance["variant_budget"]
        assert mechanism.duplicate_exposure == card_governance["duplicate_exposure"]

        assert idea_draft.study_kind == "main_effect"
        assert idea_draft.source == f"track_a:{record.slug}"
        assert idea_draft.setup_spec_id is None
        assert alpha_spec.factor_inputs == card["required_features"]["existing"]
        assert alpha_spec.label_references == [
            legacy_label_reference_id(label) for label in card["required_labels"]["existing"]
        ]
        assert (
            alpha_spec.data_assumptions["data_dependency_class"]
            == card["data_dependency"]["class"]
        )


def test_track_a_migration_uses_source_grounded_dependency_partition() -> None:
    migrations = migrate_all_track_a_cards()

    assert Counter(record.data_dependency_class for record in migrations) == {
        "existing_substrate": 2,
        "derivable_from_exchange_calendar": 4,
        "needs_paid_data": 2,
    }
    routes = {record.slug: record.migration_route for record in migrations}
    assert routes["day_of_week_effect"] == "live_main_effect_exemplar"
    assert routes["open_close_auction_flow"] == "existing_substrate_record_not_selected"
    assert routes["fomc_drift"] == "record_only_red_deferred"
    assert routes["cpi_surprise_reversion"] == "record_only_red_deferred"


@pytest.mark.parametrize(
    "gap_field",
    ["primary_horizon", "cost_sensitivity", "variant_budget", "duplicate_exposure"],
)
def test_track_a_migration_fails_closed_when_gap_metadata_is_missing(gap_field: str) -> None:
    path, card = next(
        (candidate_path, candidate_card)
        for candidate_path, candidate_card in load_track_a_cards()
        if candidate_card["mechanism_id"] == "day_of_week_effect"
    )
    governance = deepcopy(load_track_a_governance())
    del governance["cards"]["day_of_week_effect"][gap_field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        migrate_track_a_card(card, governance=governance, legacy_path=path)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == gap_field


def test_track_a_migration_outputs_exist_and_match_current_mapper(tmp_path: Path) -> None:
    migrations = migrate_all_track_a_cards()
    written = write_migrated_track_a_cards(output_dir=tmp_path, migrations=migrations)

    assert len(written) == 8
    fixture_paths = sorted(Path("research/idea_to_verdict_loop_v0/migrated_cards").glob("*.json"))
    assert len(fixture_paths) == 8
    generated_by_slug = {record.slug: record.to_dict() for record in migrations}
    for fixture_path in fixture_paths:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert payload == generated_by_slug[fixture_path.stem]


def test_track_a_legacy_card_directory_is_read_only_reference() -> None:
    assert TRACK_A_CARD_DIR.as_posix() == "research/differentiated_substrate_v1/cards"
    assert TRACK_A_GOVERNANCE_PATH.as_posix().startswith("research/idea_to_verdict_loop_v0/")
