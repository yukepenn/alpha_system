from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.idea_draft import (
    CONTEXT_NOT_EQUAL_TRIGGER,
    IDEA_BUNDLE_SLICE_PASSTHROUGH_FIELDS,
    MAIN_EFFECT,
    build_idea_validation_bundle,
    validate_idea_draft,
    validate_study_kind,
)
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.validation import GovernanceValidationError


def test_build_idea_validation_bundle_defaults_to_main_effect() -> None:
    bundle = build_idea_validation_bundle(valid_idea_payload(), source="fixture:idea")

    assert bundle.idea_draft.study_kind == MAIN_EFFECT
    assert bundle.idea_draft.source == "fixture:idea"
    assert bundle.idea_draft.hypothesis_id == bundle.hypothesis_card.hypothesis_id
    assert bundle.idea_draft.alpha_spec_id == bundle.alpha_spec.alpha_spec_id
    assert bundle.idea_draft.mechanism_id == bundle.mechanism_card.mechanism_id
    assert bundle.idea_draft.setup_spec_id is None
    assert bundle.setup_spec is None
    assert bundle.mechanism_card.stamp == "EXPLORATORY"
    assert "study_kind" not in bundle.alpha_spec.to_dict()
    assert "study_kind" not in bundle.mechanism_card.to_dict()


def test_build_idea_validation_bundle_emits_setup_for_context_not_equal_trigger() -> None:
    payload = valid_idea_payload()
    payload["study_kind"] = CONTEXT_NOT_EQUAL_TRIGGER
    payload["setup_spec"] = valid_setup_payload()

    bundle = build_idea_validation_bundle(payload, source="fixture:context")

    assert bundle.setup_spec is not None
    assert bundle.setup_spec.mechanism_id == bundle.mechanism_card.mechanism_id
    assert bundle.idea_draft.setup_spec_id == bundle.setup_spec.setup_spec_id
    assert "study_kind" not in bundle.setup_spec.to_dict()


def test_build_idea_validation_bundle_ignores_slice_passthrough_for_ids() -> None:
    base_payload = valid_idea_payload()
    base_payload["study_kind"] = CONTEXT_NOT_EQUAL_TRIGGER
    base_payload["setup_spec"] = valid_setup_payload()
    passthrough_payload = deepcopy(base_payload)
    passthrough_payload.update(_slice_passthrough_payloads())

    base = build_idea_validation_bundle(base_payload, source="fixture:context")
    with_slice = build_idea_validation_bundle(passthrough_payload, source="fixture:context")

    assert with_slice.hypothesis_card.hypothesis_id == base.hypothesis_card.hypothesis_id
    assert with_slice.alpha_spec.alpha_spec_id == base.alpha_spec.alpha_spec_id
    assert with_slice.mechanism_card.mechanism_id == base.mechanism_card.mechanism_id
    assert with_slice.setup_spec is not None
    assert base.setup_spec is not None
    assert with_slice.setup_spec.setup_spec_id == base.setup_spec.setup_spec_id
    for field in IDEA_BUNDLE_SLICE_PASSTHROUGH_FIELDS:
        assert field not in with_slice.alpha_spec.to_dict()
        assert field not in with_slice.mechanism_card.to_dict()
        assert field not in with_slice.setup_spec.to_dict()


def test_build_idea_validation_bundle_rejects_non_slice_unknown_field() -> None:
    payload = valid_idea_payload()
    payload["slice_typo"] = {"slice_id": "typo"}

    with pytest.raises(GovernanceValidationError) as exc_info:
        build_idea_validation_bundle(payload, source="fixture:idea")

    assert exc_info.value.issues[0].code == "unknown_field"
    assert exc_info.value.issues[0].field == "slice_typo"


def test_validate_study_kind_rejects_unknown_value() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_kind("shape_bearing")

    assert exc_info.value.issues[0].code == "invalid_study_kind"


def test_validate_idea_draft_rejects_setup_for_main_effect() -> None:
    payload = build_idea_validation_bundle(valid_idea_payload(), source="fixture:idea").idea_draft.to_dict()
    payload["setup_spec_id"] = generate_governance_id(
        GovernanceIdKind.SETUP_SPEC,
        {"fixture": "unexpected setup"},
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_idea_draft(payload)

    assert exc_info.value.issues[0].code == "unexpected_setup_spec"
    assert exc_info.value.issues[0].field == "setup_spec_id"


@pytest.mark.parametrize(
    "field",
    ["source", "cost_sensitivity", "variant_budget", "duplicate_exposure"],
)
def test_build_idea_validation_bundle_fails_closed_on_mechanism_gap_fields(field: str) -> None:
    payload = valid_idea_payload()
    del payload["mechanism_card"][field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        build_idea_validation_bundle(payload, source="fixture:idea")

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


def test_build_idea_validation_bundle_rejects_setup_for_main_effect() -> None:
    payload = valid_idea_payload()
    payload["setup_spec"] = valid_setup_payload()

    with pytest.raises(GovernanceValidationError) as exc_info:
        build_idea_validation_bundle(payload, source="fixture:idea")

    assert exc_info.value.issues[0].code == "unexpected_setup_spec"
    assert exc_info.value.issues[0].field == "setup_spec"


def valid_idea_payload() -> dict[str, object]:
    return {
        "study_kind": MAIN_EFFECT,
        "hypothesis_card": {
            "title": "Synthetic intake validation fixture",
            "family": "idea_to_verdict_fixture",
            "rationale": (
                "A known-ahead synthetic calendar conditioner can be registered before "
                "any diagnostic is allowed to inspect outcomes."
            ),
            "expected_mechanism": (
                "The proposed mechanism is that a declared context may condition later "
                "rows only after availability and testability checks pass."
            ),
            "falsification_criteria": [
                "Reject the fixture if required inputs are unavailable before decision time.",
                "Block the fixture if duplicate exposure checks cannot separate the context.",
            ],
            "risks": [
                "Synthetic fixtures may not represent later data availability constraints.",
                "A future diagnostic could find that the context duplicates existing factors.",
            ],
            "author": "codex-fixture",
            "created_at": "2026-06-14T00:00:00Z",
        },
        "alpha_spec": {
            "target_instruments": ["SYNTH_FUTURE"],
            "data_assumptions": {
                "coverage": "Synthetic fixture rows are complete for intake validation only.",
                "source": "Unit-test fixture; no market data is loaded.",
            },
            "factor_inputs": ["known_ahead_context"],
            "label_references": [valid_label_spec_id()],
            "exclusion_rules": [
                "Exclude rows where known-ahead context is unavailable before decision time.",
                "Exclude any future metric until duplicate exposure checks pass.",
            ],
            "timestamp_assumptions": {
                "availability": "The fixture context is available before decision time.",
                "timezone": "Fixture timestamps retain explicit UTC timestamps.",
            },
            "cost_assumptions": {
                "model": "Research planning must account for fees, slippage, and spread assumptions.",
                "scope": "Value-free fixture only; no execution cost estimate is produced.",
            },
            "expected_failure_modes": [
                "The context may duplicate a broader synthetic calendar feature.",
                "The bounded future slice may be too small for a later diagnostic.",
            ],
            "promotion_criteria": [
                "Future routing requires reviewer-gated evidence before WATCH or CANDIDATE.",
                "Future diagnostics must pass no-lookahead and testability checks first.",
            ],
            "created_by": "codex-fixture",
            "created_at": "2026-06-14T00:00:00Z",
        },
        "mechanism_card": {
            "source": "unit:idea_draft",
            "rationale": (
                "Known-ahead context can be registered as an exploratory mechanism before "
                "any result-bearing diagnostic is allowed."
            ),
            "expected_mechanism": (
                "The mechanism expects the declared context to gate later rows while "
                "remaining separate from any outcome label."
            ),
            "expected_direction": "undirected",
            "horizon": "30m",
            "session": "RTH",
            "required_features": ["known_ahead_context"],
            "required_labels": ["fixed_horizon"],
            "cost_sensitivity": {
                "rule": "Reject interpretation if costs dominate any later readout.",
            },
            "variant_budget": 1,
            "duplicate_exposure": {
                "status": "requires_pre_metric_duplicate_exposure_check",
                "note": "No equivalent fixture exposure is declared in this unit test.",
            },
        },
    }


def valid_setup_payload() -> dict[str, object]:
    return {
        "entry_context": {
            "feature": "known_ahead_context",
            "condition": "context is present before decision time",
        },
        "event_trigger": {
            "feature": "separate_event_trigger",
            "condition": "trigger is observed after the entry context is defined",
        },
        "regime_filter": {
            "session": "RTH",
            "rule": "fixture regular-session rows only",
        },
        "confirmation": {"rule": "confirmation remains separate from context"},
        "invalidation": {"rule": "invalidate when trigger separation is lost"},
        "stop": {"binding": "fixture path stop from governed label"},
        "target": {"binding": "fixture path target from governed label"},
        "hold_time": {"max_minutes": 30, "policy": "fixture horizon only"},
        "horizon": "30m",
        "path_label": valid_label_spec_id(),
        "allowed_variants": ["baseline"],
        "forbidden_post_hoc_changes": [
            "Do not change context after reading outcomes.",
            "Do not change trigger separation after reading outcomes.",
        ],
    }


def valid_label_spec_id() -> str:
    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "fixture_path", "name": "target_before_stop", "version": 1},
    )


def cloned_valid_idea_payload() -> dict[str, object]:
    return deepcopy(valid_idea_payload())


def _slice_passthrough_payloads() -> dict[str, object]:
    testability_slice = {
        "slice_id": "passthrough-testability",
        "dataset_version_id": "dsv_passthrough",
        "partition_id": "partition_passthrough",
        "path_label_class_counts": {"false": 2, "true": 1},
    }
    fast_probe_slice = {
        "slice_id": "passthrough-fast-probe",
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "dataset_version_id": "dsv_passthrough",
        "partition_id": "partition_passthrough",
        "instrument_id": "SYNTH",
        "session_id": "TEST:SYNTH:RTH",
        "data_version": "dsv_passthrough",
        "features": [
            {
                "role": "context",
                "factor_id": "known_ahead_context",
                "factor_version": "ctx:v1",
                "relative_path": "features/context.parquet",
                "pack_ref": "fver_" + "a" * 64,
            }
        ],
        "labels": [
            {
                "role": "path",
                "label_id": valid_label_spec_id(),
                "relative_path": "labels/path.parquet",
                "pack_ref": "lver_" + "b" * 64,
                "label_spec_id": valid_label_spec_id(),
            }
        ],
    }
    return {
        "testability_slice": testability_slice,
        "testability_slices": {"default": testability_slice},
        "slice_spec": fast_probe_slice,
        "slice_specs": {"default": fast_probe_slice},
        "fast_probe_slice": fast_probe_slice,
        "fast_probe_slice_spec": fast_probe_slice,
        "slice": fast_probe_slice,
        "slices": {"default": fast_probe_slice},
    }
