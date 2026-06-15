from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from alpha_system.governance.idea_draft import CONTEXT_NOT_EQUAL_TRIGGER, MAIN_EFFECT
from alpha_system.research_lane import slice_spec as slice_spec_module
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError


def test_slice_spec_from_mapping_round_trips_de_hardcoded_inputs() -> None:
    spec = SliceSpec.from_mapping(_slice_payload())

    assert spec.slice_id == "fixture_slice"
    assert spec.study_kind == CONTEXT_NOT_EQUAL_TRIGGER
    assert spec.instrument_id == "SYNTH"
    assert spec.session_id == "TEST:SYNTH:RTH"
    assert spec.feature_pack_refs == ("fver_context_v1", "fver_trigger_v1")
    assert spec.label_pack_refs == ("lver_path_pack",)
    assert spec.feature_request_ids == ("freq_context", "freq_trigger")
    assert spec.label_spec_ids == ("lspec_path",)
    assert spec.label_version_map["lver_target"].label_type == "target_before_stop"
    assert spec.label_version_map["lver_target"].value_type == "bool"

    # The outcome selector defaults to None (binary target_before_stop path).
    assert spec.outcome_label_type is None

    payload = spec.to_dict()
    assert payload["instrument_id"] == "SYNTH"
    assert payload["session_id"] == "TEST:SYNTH:RTH"
    assert payload["label_version_map"]["lver_mfe"]["label_type"] == "mfe_by_horizon"
    assert payload["outcome_label_type"] is None


def test_slice_spec_round_trips_continuous_outcome_label_type() -> None:
    spec = SliceSpec.from_mapping({**_slice_payload(), "outcome_label_type": "mfe_by_horizon"})

    assert spec.outcome_label_type == "mfe_by_horizon"
    assert spec.to_dict()["outcome_label_type"] == "mfe_by_horizon"
    # The selector survives a from_mapping(to_dict()) round trip.
    assert SliceSpec.from_mapping(spec.to_dict()).outcome_label_type == "mfe_by_horizon"


def test_slice_spec_is_immutable_and_resolves_root_without_io(tmp_path: Path) -> None:
    spec = SliceSpec.from_mapping({**_slice_payload(), "data_root": tmp_path.as_posix()})

    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.slice_id = "changed"  # type: ignore[misc]

    resolved = spec.resolve_data_root(env={"ALPHA_DATA_ROOT": "/env/root"})
    assert resolved == Path("/env/root")
    assert spec.resolve_data_root(env={}) == tmp_path


def test_slice_spec_from_idea_payload_selects_requested_slice() -> None:
    first = {**_slice_payload(), "slice_id": "first"}
    second = {**_slice_payload(), "slice_id": "second", "study_kind": MAIN_EFFECT}

    spec = SliceSpec.from_idea_payload({"slices": [first, second]}, slice_id="second")

    assert spec.slice_id == "second"
    assert spec.study_kind == MAIN_EFFECT


def test_slice_spec_fails_closed_on_missing_required_fields() -> None:
    payload = _slice_payload()
    payload.pop("instrument_id")

    with pytest.raises(SliceSpecError, match="instrument_id"):
        SliceSpec.from_mapping(payload)


def test_slice_spec_fails_closed_when_input_has_no_pack_ref_or_path() -> None:
    payload = _slice_payload()
    payload["features"] = [
        {
            "role": "context",
            "factor_id": "context_factor",
            "factor_version": "ctx:v1",
        }
    ]

    with pytest.raises(SliceSpecError, match="relative_path or pack_ref"):
        SliceSpec.from_mapping(payload)


def test_slice_spec_defaults_do_not_leak_frozen_es_2024_constants() -> None:
    source = inspect.getsource(slice_spec_module)
    payload = SliceSpec.from_mapping(_slice_payload()).to_dict()

    assert "ES_2024" not in source
    assert "CME:ES_2024:RTH" not in source
    assert "ES_2024" not in str(payload)


def _slice_payload() -> dict:
    return {
        "slice_id": "fixture_slice",
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "dataset_version_id": "dsv_fixture",
        "partition_id": "partition_fixture",
        "instrument_id": "SYNTH",
        "session_id": "TEST:SYNTH:RTH",
        "data_version": "dsv_fixture",
        "features": [
            {
                "role": "context",
                "factor_id": "context_factor",
                "factor_version": "ctx:v1",
                "relative_path": "features/context.parquet",
                "pack_ref": "fver_context_v1",
                "feature_request_id": "freq_context",
            },
            {
                "role": "trigger",
                "factor_id": "trigger_factor",
                "factor_version": "trg:v1",
                "relative_path": "features/trigger.parquet",
                "pack_ref": "fver_trigger_v1",
                "feature_request_id": "freq_trigger",
            },
        ],
        "labels": [
            {
                "role": "path",
                "label_id": "path_label_fixture",
                "relative_path": "labels/path.parquet",
                "pack_ref": "lver_path_pack",
                "label_spec_id": "lspec_path",
            }
        ],
        "label_version_map": {
            "lver_target": ("target_before_stop", "bool"),
            "lver_mfe": {"label_type": "mfe_by_horizon", "value_type": "float"},
            "lver_mae": {"label_type": "mae_by_horizon", "value_type": "float"},
        },
        "horizon_seconds": 7200,
        "required_future_bars": 120,
        "materialized_label_version": "fixture_labels_v1",
        "surrogate_run_count": 8,
        "surrogate_base_seed": 0,
        "family_id": "fixture_family",
        "family_budget": 2,
        "variant_id": "baseline",
        "created_at": "2026-01-02T15:00:00Z",
    }
