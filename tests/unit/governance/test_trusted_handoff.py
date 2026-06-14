from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from alpha_system.governance.alpha_spec import ALPHA_SPEC_REQUIRED_FIELDS
from alpha_system.governance.feature_request import FEATURE_REQUEST_REQUIRED_FIELDS
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.label_spec import LABEL_SPEC_REQUIRED_FIELDS
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP, create_mechanism_card
from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    PromotionLifecycleState,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.promotion_gate import PromotionGateContext, assert_promotion_gate
from alpha_system.governance.setup_spec import create_setup_spec
from alpha_system.governance.study_spec import STUDY_SPEC_REQUIRED_FIELDS
from alpha_system.governance.trusted_handoff import (
    TRUSTED_HANDOFF_SCHEMA,
    TRUSTED_HANDOFF_STATUS,
    create_trusted_handoff_gap_report,
)
from alpha_system.governance.validation import GovernanceValidationError


def _synthetic_probe_artifact() -> dict[str, Any]:
    mechanism = create_mechanism_card(
        source="SSRL-P04 synthetic trusted-handoff fixture",
        rationale=(
            "A bounded setup declaration can be routed to a later trusted rerun "
            "only after the missing trusted-lane specifications are authored."
        ),
        expected_mechanism=(
            "The context gates compressed auction state while the trigger is a "
            "separate reclaim event read against a declared path label."
        ),
        expected_direction="target-before-stop path reading after reclaim event",
        horizon="120m",
        session="RTH",
        required_features=[
            "synthetic_range_contraction_context",
            "synthetic_failed_high_reclaim_trigger",
        ],
        required_labels=["synthetic_target_before_stop_path_label"],
        cost_sensitivity={
            "scope": "trusted rerun must author cost assumptions separately",
        },
        variant_budget=2,
        duplicate_exposure={
            "status": "checked",
            "note": "Synthetic fixture has no equivalent declared setup.",
        },
    )
    path_label = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "path", "name": "target_before_stop", "version": 4},
    )
    setup = create_setup_spec(
        entry_context={
            "factor_id": "synthetic_range_contraction_context",
            "factor_version": "v1_fixture_context",
            "condition": "context is available before the decision timestamp",
        },
        event_trigger={
            "factor_id": "synthetic_failed_high_reclaim_trigger",
            "factor_version": "v1_fixture_trigger",
            "condition": "trigger is separate from the context declaration",
        },
        regime_filter={
            "instrument_root": "ES",
            "session": "RTH",
        },
        confirmation={
            "rule": "fixture confirmation is declared before any trusted rerun",
        },
        invalidation={
            "rule": "fixture invalidation is declared before any trusted rerun",
        },
        stop={
            "binding": "path label stop side from the governed label specification",
        },
        target={
            "path_outcome": "target_before_stop",
            "binding": "path label target side from the governed label specification",
        },
        hold_time={
            "max_minutes": 120,
            "policy": "close the path read after the declared horizon",
        },
        horizon="120m",
        path_label=path_label,
        allowed_variants=["baseline_fixture"],
        forbidden_post_hoc_changes=[
            "Do not change the context bucket after reading exploratory output.",
            "Do not change target or stop binding after reading exploratory output.",
        ],
        mechanism_id=mechanism.mechanism_id,
    )
    return {
        "schema": "alpha_system.research.strategy_shaped_lane.synthetic_probe.v1",
        "phase_id": "SSRL-P04",
        "evidence_id": "fixture_probe",
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": mechanism.to_dict(),
        "setup_spec": setup.to_dict(),
        "compiled_probe": {
            "setup_spec_id": setup.setup_spec_id,
            "path_label": path_label,
            "stamp": EXPLORATORY_STAMP,
        },
    }


def _gap_by_object(report: dict[str, Any], object_name: str) -> dict[str, Any]:
    for gap in report["required_trusted_objects"]:
        if gap["object_name"] == object_name:
            return gap
    raise AssertionError(f"missing gap for {object_name}")


def test_trusted_handoff_emits_expected_trusted_lane_gaps() -> None:
    report = create_trusted_handoff_gap_report(_synthetic_probe_artifact()).to_dict()

    assert report["schema"] == TRUSTED_HANDOFF_SCHEMA
    assert report["status"] == TRUSTED_HANDOFF_STATUS
    assert report["stamp"] == EXPLORATORY_STAMP
    assert report["promotion_eligible"] is False
    assert report["promotion_evidence"] is False
    assert report["trusted_rerun_required"] is True
    assert report["trusted_handoff_id"].startswith("thgap_")

    expected = {
        "AlphaSpec": ALPHA_SPEC_REQUIRED_FIELDS,
        "StudySpec": STUDY_SPEC_REQUIRED_FIELDS,
        "FeatureRequest": FEATURE_REQUEST_REQUIRED_FIELDS,
        "LabelSpec": LABEL_SPEC_REQUIRED_FIELDS,
    }
    for object_name, required_fields in expected.items():
        gap = _gap_by_object(report, object_name)
        assert gap["object_present"] is False
        assert gap["status"] == "MISSING_FOR_TRUSTED_RERUN"
        assert gap["required_fields"] == list(required_fields)
        assert gap["present_fields"] == []
        assert gap["missing_fields"] == list(required_fields)

    alpha_links = _gap_by_object(report, "AlphaSpec")["source_links"]
    assert {
        "trusted_field": "factor_inputs",
        "probe_field": "setup_spec.entry_context.factor_id",
        "probe_identifier": "synthetic_range_contraction_context",
        "probe_version": "v1_fixture_context",
    } in alpha_links
    assert {
        "trusted_field": "factor_inputs",
        "probe_field": "setup_spec.event_trigger.factor_id",
        "probe_identifier": "synthetic_failed_high_reclaim_trigger",
        "probe_version": "v1_fixture_trigger",
    } in alpha_links
    assert any("AlphaSpec" in item for item in report["checklist"])
    assert any("StudySpec" in item for item in report["checklist"])


def test_trusted_handoff_never_strips_stamp_or_sets_lifecycle_state() -> None:
    artifact = _synthetic_probe_artifact()
    original = deepcopy(artifact)

    report = create_trusted_handoff_gap_report(artifact).to_dict()

    assert artifact == original
    assert report["stamp"] == EXPLORATORY_STAMP
    assert report["source_provenance"]["stamp"] == EXPLORATORY_STAMP
    keys = set(_walk_keys(report))
    assert "previous_state" not in keys
    assert "next_state" not in keys
    assert "promotion_decision" not in keys
    assert "trusted_lifecycle_state" not in keys
    assert "promoted" not in keys
    values = set(_walk_text_values(report))
    assert "CANDIDATE" not in values
    assert "VALIDATED" not in values
    assert "LIVE_APPROVED" not in values


def test_trusted_handoff_artifact_is_refused_by_promotion_path() -> None:
    report = create_trusted_handoff_gap_report(_synthetic_probe_artifact()).to_dict()

    with pytest.raises(GovernanceValidationError) as exc_info:
        reject_exploratory_promotion_artifact(report, field="trusted_handoff")

    assert exc_info.value.issues[0].code == EXPLORATORY_PROMOTION_REFUSAL_CODE
    assert exc_info.value.issues[0].field == "trusted_handoff.stamp"

    with pytest.raises(GovernanceValidationError) as gate_exc_info:
        assert_promotion_gate(
            PromotionLifecycleState.REVIEWED,
            PromotionLifecycleState.CANDIDATE,
            PromotionGateContext(promotion_artifacts=(report,)),
        )

    assert gate_exc_info.value.issues[0].code == EXPLORATORY_PROMOTION_REFUSAL_CODE
    assert gate_exc_info.value.issues[0].field == "promotion_artifacts[0].stamp"


def test_trusted_handoff_reports_partial_candidate_spec_fields() -> None:
    artifact = _synthetic_probe_artifact()
    artifact["trusted_lane_specs"] = {
        "alpha_spec": {
            "alpha_spec_id": "aspec_placeholder",
            "hypothesis_id": "hyp_placeholder",
        }
    }

    report = create_trusted_handoff_gap_report(artifact).to_dict()

    alpha_gap = _gap_by_object(report, "AlphaSpec")
    assert alpha_gap["object_present"] is True
    assert alpha_gap["status"] == "PARTIAL_FOR_TRUSTED_RERUN"
    assert alpha_gap["present_fields"] == ["alpha_spec_id", "hypothesis_id"]
    assert "target_instruments" in alpha_gap["missing_fields"]


def test_trusted_handoff_requires_exploratory_input() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        create_trusted_handoff_gap_report(
            {
                "schema": "alpha_system.research.strategy_shaped_lane.synthetic_probe.v1",
                "phase_id": "SSRL-P04",
            }
        )

    assert exc_info.value.issues[0].code == "missing_exploratory_stamp"
    assert exc_info.value.issues[0].field == "probe_artifact.stamp"


def _walk_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_walk_keys(item))
        return tuple(keys)
    return ()


def _walk_text_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_walk_text_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_text_values(item))
        return tuple(values)
    return ()
