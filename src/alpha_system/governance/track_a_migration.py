"""Track-A legacy card migration into canonical idea-intake objects."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.governance.idea_draft import (
    MAIN_EFFECT,
    IdeaValidationBundle,
    build_idea_validation_bundle,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

TRACK_A_CARD_DIR = Path("research/differentiated_substrate_v1/cards")
TRACK_A_GOVERNANCE_PATH = Path(
    "research/idea_to_verdict_loop_v0/track_a_migration_governance.json"
)
TRACK_A_OUTPUT_DIR = Path("research/idea_to_verdict_loop_v0/migrated_cards")
TRACK_A_CREATED_AT = "2026-06-14T00:00:00Z"
TRACK_A_CREATED_BY = "ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01"

TRACK_A_GAP_FIELDS = (
    "primary_horizon",
    "cost_sensitivity",
    "variant_budget",
    "duplicate_exposure",
)
TRACK_A_GOVERNANCE_REQUIRED_FIELDS = TRACK_A_GAP_FIELDS + ("target_instruments",)
TRACK_A_GOVERNANCE_FIELD_TYPES = {
    "primary_horizon": str,
    "cost_sensitivity": dict,
    "variant_budget": int,
    "duplicate_exposure": dict,
    "target_instruments": list,
}


@dataclass(frozen=True, slots=True)
class MigratedTrackACard:
    """One legacy Track-A card mapped to the canonical object family."""

    slug: str
    legacy_path: str
    data_dependency_class: str
    migration_route: str
    selected_horizon: str
    bundle: IdeaValidationBundle

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the value-free migrated record."""

        return {
            "legacy": {
                "mechanism_id": self.slug,
                "path": self.legacy_path,
                "data_dependency_class": self.data_dependency_class,
            },
            "migration": {
                "campaign": "ALPHA_IDEA_TO_VERDICT_LOOP_V0",
                "phase": "IVL-P01",
                "study_kind": MAIN_EFFECT,
                "migration_route": self.migration_route,
                "selected_horizon": self.selected_horizon,
                "lineage_source": f"track_a:{self.slug}",
            },
            "canonical": self.bundle.to_dict(),
        }


def load_track_a_cards(card_dir: Path | str = TRACK_A_CARD_DIR) -> tuple[tuple[Path, Mapping[str, Any]], ...]:
    """Load the eight legacy Track-A JSON cards as read-only mappings."""

    root = Path(card_dir)
    paths = tuple(sorted(root.glob("*.json")))
    cards: list[tuple[Path, Mapping[str, Any]]] = []
    for path in paths:
        cards.append((path, _load_json_mapping(path, object_name=f"Track-A card {path.name}")))
    return tuple(cards)


def load_track_a_governance(path: Path | str = TRACK_A_GOVERNANCE_PATH) -> Mapping[str, Any]:
    """Load explicit migration governance metadata for fail-closed gap fields."""

    return _load_json_mapping(Path(path), object_name="Track-A migration governance")


def migrate_track_a_card(
    card: Mapping[str, Any],
    *,
    governance: Mapping[str, Any],
    legacy_path: Path | str,
) -> MigratedTrackACard:
    """Map one Track-A card into validated canonical intake objects."""

    slug = _require_text(card, "mechanism_id")
    card_governance = _card_governance(governance, slug)
    selected_horizon = _selected_horizon(card, card_governance, slug)
    data_dependency = require_mapping(
        card.get("data_dependency"),
        object_name=f"Track-A card {slug}.data_dependency",
    )
    data_dependency_class = _require_text(data_dependency, "class")
    migration_route = _migration_route(slug, data_dependency_class)
    bundle = build_idea_validation_bundle(
        _idea_payload_from_track_a(
            card,
            slug=slug,
            card_governance=card_governance,
            selected_horizon=selected_horizon,
            migration_route=migration_route,
        ),
        source=f"track_a:{slug}",
    )
    return MigratedTrackACard(
        slug=slug,
        legacy_path=Path(legacy_path).as_posix(),
        data_dependency_class=data_dependency_class,
        migration_route=migration_route,
        selected_horizon=selected_horizon,
        bundle=bundle,
    )


def migrate_all_track_a_cards(
    *,
    card_dir: Path | str = TRACK_A_CARD_DIR,
    governance_path: Path | str = TRACK_A_GOVERNANCE_PATH,
) -> tuple[MigratedTrackACard, ...]:
    """Migrate every legacy Track-A card found under the read-only card directory."""

    governance = load_track_a_governance(governance_path)
    return tuple(
        migrate_track_a_card(card, governance=governance, legacy_path=path)
        for path, card in load_track_a_cards(card_dir)
    )


def write_migrated_track_a_cards(
    *,
    output_dir: Path | str = TRACK_A_OUTPUT_DIR,
    migrations: Sequence[MigratedTrackACard] | None = None,
) -> tuple[Path, ...]:
    """Write value-free canonical migration records under the new IVL directory."""

    records = tuple(migrations) if migrations is not None else migrate_all_track_a_cards()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for record in records:
        path = destination / f"{record.slug}.json"
        path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return tuple(written)


def legacy_label_reference_id(label_name: str) -> str:
    """Derive an AlphaSpec-compatible label reference from a legacy label name."""

    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {
            "source": "track_a_legacy_label_name",
            "label_name": label_name,
            "campaign": "ALPHA_IDEA_TO_VERDICT_LOOP_V0",
        },
    )


def _load_json_mapping(path: Path, *, object_name: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field=path.as_posix(),
                code="invalid_json",
                message=f"{object_name} must be valid JSON: {exc.msg}",
                expected="JSON mapping",
                actual=f"line {exc.lineno}",
            )
        ) from exc
    return require_mapping(value, object_name=object_name)


def _card_governance(governance: Mapping[str, Any], slug: str) -> Mapping[str, Any]:
    cards = require_mapping(governance.get("cards"), object_name="Track-A governance cards")
    if slug not in cards:
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"cards.{slug}",
                code="missing_required_field",
                message="Track-A migration governance must provide explicit gap fields",
                expected="per-card governance metadata",
                actual="missing",
            )
        )
    return validate_schema(
        require_mapping(cards[slug], object_name=f"Track-A governance {slug}"),
        required_fields=TRACK_A_GOVERNANCE_REQUIRED_FIELDS,
        field_types=TRACK_A_GOVERNANCE_FIELD_TYPES,
        allowed_fields=TRACK_A_GOVERNANCE_REQUIRED_FIELDS,
        object_name=f"Track-A governance {slug}",
    )


def _selected_horizon(
    card: Mapping[str, Any],
    card_governance: Mapping[str, Any],
    slug: str,
) -> str:
    horizons = _require_text_list(card, "expected_horizon")
    selected = _require_text(card_governance, "primary_horizon")
    if selected not in horizons:
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"cards.{slug}.primary_horizon",
                code="invalid_primary_horizon",
                message="primary_horizon must be one of the legacy expected_horizon values",
                expected="|".join(horizons),
                actual=selected,
            )
        )
    return selected


def _idea_payload_from_track_a(
    card: Mapping[str, Any],
    *,
    slug: str,
    card_governance: Mapping[str, Any],
    selected_horizon: str,
    migration_route: str,
) -> dict[str, JsonValue]:
    hypothesis = require_mapping(card.get("hypothesis"), object_name=f"Track-A card {slug}.hypothesis")
    required_features = require_mapping(
        card.get("required_features"),
        object_name=f"Track-A card {slug}.required_features",
    )
    required_labels = require_mapping(
        card.get("required_labels"),
        object_name=f"Track-A card {slug}.required_labels",
    )
    data_dependency = require_mapping(
        card.get("data_dependency"),
        object_name=f"Track-A card {slug}.data_dependency",
    )
    lookahead_risk = require_mapping(
        card.get("lookahead_risk"),
        object_name=f"Track-A card {slug}.lookahead_risk",
    )
    orthogonality = require_mapping(
        card.get("expected_orthogonality_to_dead_mechanisms"),
        object_name=f"Track-A card {slug}.expected_orthogonality_to_dead_mechanisms",
    )
    existing_features = _require_text_list(required_features, "existing")
    existing_labels = _require_text_list(required_labels, "existing")
    new_features = _new_input_names(required_features.get("new", []))
    new_labels = _new_input_names(required_labels.get("new", []))

    return {
        "source": f"track_a:{slug}",
        "study_kind": MAIN_EFFECT,
        "hypothesis_card": {
            "title": f"Track-A migrated main-effect hypothesis: {slug}",
            "family": "track_a_main_effect_migration",
            "rationale": _require_text(hypothesis, "economic_rationale"),
            "expected_mechanism": _require_text(hypothesis, "statement"),
            "falsification_criteria": [
                (
                    "Reject or requeue this migrated record if required governed "
                    "features or labels are unavailable before diagnostics."
                ),
                (
                    "Block any later verdict if no-lookahead controls or duplicate "
                    "exposure checks fail before a metric is inspected."
                ),
            ],
            "risks": [
                _require_text(lookahead_risk, "description"),
                _require_text(orthogonality, "statement"),
                _require_text(data_dependency, "detail"),
            ],
            "author": TRACK_A_CREATED_BY,
            "created_at": TRACK_A_CREATED_AT,
        },
        "alpha_spec": {
            "target_instruments": list(card_governance["target_instruments"]),
            "data_assumptions": {
                "legacy_source": f"track_a:{slug}",
                "data_dependency_class": _require_text(data_dependency, "class"),
                "data_dependency_detail": _require_text(data_dependency, "detail"),
                "migration_route": migration_route,
                "missing_feature_candidates": _metadata_list_or_note(
                    new_features,
                    empty_note="No new feature candidates are declared by this legacy card.",
                ),
                "missing_label_candidates": _metadata_list_or_note(
                    new_labels,
                    empty_note="No new label candidates are declared by this legacy card.",
                ),
            },
            "factor_inputs": existing_features,
            "label_references": [legacy_label_reference_id(label) for label in existing_labels],
            "exclusion_rules": [
                _require_text(lookahead_risk, "mitigation"),
                "Do not test needs_paid_data records in V0; paid-data sourcing is RED-deferred.",
                (
                    "Do not edit or delete the legacy Track-A card until a later "
                    "retirement phase is authorized."
                ),
            ],
            "timestamp_assumptions": {
                "lookahead_level": (
                    f"{_require_text(lookahead_risk, 'level')} lookahead risk declared "
                    "by the legacy Track-A card"
                ),
                "lookahead_description": _require_text(lookahead_risk, "description"),
                "pre_event_knowable_features": _metadata_list_or_note(
                    _optional_text_list(lookahead_risk.get("pre_event_knowable_features", [])),
                    empty_note=(
                        "The legacy card declares no pre-event knowable feature list."
                    ),
                ),
                "post_event_knowable_features": _metadata_list_or_note(
                    _optional_text_list(lookahead_risk.get("post_event_knowable_features", [])),
                    empty_note=(
                        "The legacy card declares no post-event knowable feature list."
                    ),
                ),
            },
            "cost_assumptions": {
                "cost_sensitivity": dict(card_governance["cost_sensitivity"]),
                "scope": "research planning only; no execution or tradability claim",
            },
            "expected_failure_modes": [
                _require_text(orthogonality, "statement"),
                _require_text(orthogonality, "diagnostic_check"),
                _require_text(data_dependency, "detail"),
            ],
            "promotion_criteria": [
                (
                    "Any future WATCH or CANDIDATE routing requires reviewer-gated "
                    "evidence and must preserve EXPLORATORY promotion guards."
                ),
                (
                    "Any future diagnostic must pass no-lookahead, duplicate-exposure, "
                    "and testability checks before interpretation."
                ),
            ],
            "created_by": TRACK_A_CREATED_BY,
            "created_at": TRACK_A_CREATED_AT,
        },
        "mechanism_card": {
            "source": f"track_a:{slug}",
            "rationale": _require_text(hypothesis, "economic_rationale"),
            "expected_mechanism": _require_text(hypothesis, "statement"),
            "expected_direction": _require_text(card, "expected_sign"),
            "horizon": selected_horizon,
            "session": _require_text(card, "expected_session"),
            "required_features": existing_features,
            "required_labels": existing_labels,
            "cost_sensitivity": dict(card_governance["cost_sensitivity"]),
            "variant_budget": card_governance["variant_budget"],
            "duplicate_exposure": dict(card_governance["duplicate_exposure"]),
        },
    }


def _migration_route(slug: str, data_dependency_class: str) -> str:
    if slug == "day_of_week_effect" and data_dependency_class == "existing_substrate":
        return "live_main_effect_exemplar"
    if data_dependency_class == "existing_substrate":
        return "existing_substrate_record_not_selected"
    if data_dependency_class == "derivable_from_exchange_calendar":
        return "data_gap_requeue_candidate"
    if data_dependency_class == "needs_paid_data":
        return "record_only_red_deferred"
    raise GovernanceValidationError(
        ValidationIssue(
            field=f"{slug}.data_dependency.class",
            code="unknown_data_dependency_class",
            message="Track-A data_dependency.class is not declared in the IVL map",
            expected="existing_substrate|derivable_from_exchange_calendar|needs_paid_data",
            actual=data_dependency_class,
        )
    )


def _require_text(mapping: Mapping[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be a non-empty string",
                expected="non-empty string",
                actual=type(value).__name__ if value is not None else "missing",
            )
        )
    return value.strip()


def _require_text_list(mapping: Mapping[str, Any], field: str) -> list[str]:
    value = mapping.get(field)
    return _text_list(value, field=field)


def _text_list(value: Any, *, field: str = "list") -> list[str]:
    if not isinstance(value, list) or not value:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be a non-empty list of strings",
                expected="non-empty list[str]",
                actual=type(value).__name__,
            )
        )
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"{field}[{index}]",
                    code="empty_required_field",
                    message=f"{field}[{index}] must be a non-empty string",
                    expected="non-empty string",
                    actual=type(item).__name__,
                )
            )
        result.append(item.strip())
    return result


def _optional_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise GovernanceValidationError(
            ValidationIssue(
                field="list",
                code="invalid_field_type",
                message="optional list metadata must be a list",
                expected="list",
                actual=type(value).__name__,
            )
        )
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"list[{index}]",
                    code="empty_required_field",
                    message=f"list[{index}] must be a non-empty string",
                    expected="non-empty string",
                    actual=type(item).__name__,
                )
            )
        result.append(item.strip())
    return result


def _metadata_list_or_note(values: Sequence[str], *, empty_note: str) -> list[str] | str:
    return list(values) if values else empty_note


def _new_input_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise GovernanceValidationError(
            ValidationIssue(
                field="new",
                code="invalid_field_type",
                message="new input declarations must be a list",
                expected="list",
                actual=type(value).__name__,
            )
        )
    names: list[str] = []
    for index, item in enumerate(value):
        if isinstance(item, Mapping):
            names.append(_require_text(item, "name"))
        elif isinstance(item, str) and item.strip():
            names.append(item.strip())
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"new[{index}]",
                    code="invalid_field_type",
                    message="new input declarations must be strings or mappings with name",
                    expected="string|mapping",
                    actual=type(item).__name__,
                )
            )
    return names


__all__ = [
    "MigratedTrackACard",
    "TRACK_A_CARD_DIR",
    "TRACK_A_GOVERNANCE_PATH",
    "TRACK_A_OUTPUT_DIR",
    "legacy_label_reference_id",
    "load_track_a_cards",
    "load_track_a_governance",
    "migrate_all_track_a_cards",
    "migrate_track_a_card",
    "write_migrated_track_a_cards",
]
