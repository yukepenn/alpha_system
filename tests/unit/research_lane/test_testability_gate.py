from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.surrogate_run import ZERO_PASS_MET
from alpha_system.research_lane.testability_gate import (
    CHECK_FEATURES_MATERIALIZED,
    CHECK_LABELS_EXIST,
    CHECK_N_EFF_MDE_DEDUP,
    CHECK_NO_LOOKAHEAD_SURROGATE,
    CHECK_PATH_LABEL_TWO_CLASS,
    GateStatus,
    evaluate_testability_gate,
)
from alpha_system.research_lane.testability_gate import (
    TestabilitySlice as GateSlice,
)
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")
DATASET_VERSION_ID = "dsv_testability_gate_fixture_v1"
PARTITION_ID = "development_partition"
FEATURE_VERSION_ID = "fver_" + "a" * 64
LABEL_VERSION_ID = "lver_" + "b" * 64
FEATURE_REQUEST_ID = "freq_" + "c" * 24
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_testability_gate_passes_resolved_two_class_slice_without_probe_call() -> None:
    bundle = _bundle()
    resolver = _resolver(label_spec_id=bundle.alpha_spec.label_references[0])
    probe_calls: list[str] = []

    result = evaluate_testability_gate(
        bundle.idea_draft,
        alpha_spec=bundle.alpha_spec,
        mechanism_card=bundle.mechanism_card,
        slice_spec=_slice(bundle.alpha_spec.label_references[0]),
        resolver=resolver,
        probe_runner=lambda: probe_calls.append("called"),
    )

    assert result.overall_status is GateStatus.PASS
    assert _statuses(result) == {
        CHECK_FEATURES_MATERIALIZED: GateStatus.PASS,
        CHECK_LABELS_EXIST: GateStatus.PASS,
        CHECK_PATH_LABEL_TWO_CLASS: GateStatus.PASS,
        CHECK_N_EFF_MDE_DEDUP: GateStatus.PASS,
        CHECK_NO_LOOKAHEAD_SURROGATE: GateStatus.PASS,
    }
    assert result.probe_invoked is False
    assert result.to_dict()["shot_spent"] is False
    assert probe_calls == []
    assert resolver.feature_store.calls == [FEATURE_VERSION_ID]
    assert resolver.label_registry.calls == [LABEL_VERSION_ID]


def test_testability_gate_data_gaps_single_class_slice_before_probe_call() -> None:
    bundle = _bundle()
    probe_calls: list[str] = []

    result = evaluate_testability_gate(
        bundle.idea_draft,
        alpha_spec=bundle.alpha_spec,
        mechanism_card=bundle.mechanism_card,
        slice_spec=_slice(
            bundle.alpha_spec.label_references[0],
            path_label_observations=(
                {"label_value": True},
                {"label_value": True},
                {"label_value": True},
            ),
        ),
        resolver=_resolver(label_spec_id=bundle.alpha_spec.label_references[0]),
        probe_runner=lambda: probe_calls.append("called"),
    )

    assert result.overall_status is GateStatus.DATA_GAP
    assert _statuses(result)[CHECK_PATH_LABEL_TWO_CLASS] is GateStatus.DATA_GAP
    assert result.probe_invoked is False
    assert result.to_dict()["shot_spent"] is False
    assert probe_calls == []


@pytest.mark.parametrize(
    ("check_id", "slice_overrides"),
    [
        (CHECK_FEATURES_MATERIALIZED, {"feature_pack_refs": ()}),
        (CHECK_LABELS_EXIST, {"label_pack_refs": ()}),
        (
            CHECK_PATH_LABEL_TWO_CLASS,
            {"path_label_observations": (), "path_label_class_counts": None},
        ),
        (CHECK_N_EFF_MDE_DEDUP, {"n_eff": None}),
        (CHECK_NO_LOOKAHEAD_SURROGATE, {"surrogate_fdr_requirement": None}),
    ],
)
def test_each_gate_check_can_return_data_gap_independently(
    check_id: str,
    slice_overrides: dict[str, object],
) -> None:
    bundle = _bundle()

    result = evaluate_testability_gate(
        bundle.idea_draft,
        alpha_spec=bundle.alpha_spec,
        mechanism_card=bundle.mechanism_card,
        slice_spec=_slice(bundle.alpha_spec.label_references[0], **slice_overrides),
        resolver=_resolver(label_spec_id=bundle.alpha_spec.label_references[0]),
    )

    assert _statuses(result)[check_id] is GateStatus.DATA_GAP
    assert result.overall_status is GateStatus.DATA_GAP


@pytest.mark.parametrize(
    ("check_id", "slice_overrides"),
    [
        (CHECK_N_EFF_MDE_DEDUP, {"minimum_detectable_effect": 1.5}),
        (CHECK_NO_LOOKAHEAD_SURROGATE, {"available_ts_satisfiable": False}),
        (CHECK_NO_LOOKAHEAD_SURROGATE, {"surrogate_fdr_requirement": "CALIBRATION_BLOCKED"}),
    ],
)
def test_gate_checks_fail_on_definite_untestable_metadata(
    check_id: str,
    slice_overrides: dict[str, object],
) -> None:
    bundle = _bundle()

    result = evaluate_testability_gate(
        bundle.idea_draft,
        alpha_spec=bundle.alpha_spec,
        mechanism_card=bundle.mechanism_card,
        slice_spec=_slice(bundle.alpha_spec.label_references[0], **slice_overrides),
        resolver=_resolver(label_spec_id=bundle.alpha_spec.label_references[0]),
    )

    assert _statuses(result)[check_id] is GateStatus.FAIL
    assert result.overall_status is GateStatus.FAIL


def test_gate_can_use_precomputed_path_label_class_counts() -> None:
    bundle = _bundle()

    result = evaluate_testability_gate(
        bundle.idea_draft,
        alpha_spec=bundle.alpha_spec,
        mechanism_card=bundle.mechanism_card,
        slice_spec=_slice(
            bundle.alpha_spec.label_references[0],
            path_label_observations=(),
            path_label_class_counts={"true": 3, "false": 1},
        ),
        resolver=_resolver(label_spec_id=bundle.alpha_spec.label_references[0]),
    )

    class_detail = next(
        check.detail
        for check in result.checks
        if check.check_id == CHECK_PATH_LABEL_TWO_CLASS
    )
    assert result.overall_status is GateStatus.PASS
    assert class_detail["class_balance"]["class_count"] == 2
    assert class_detail["class_balance"]["minority_class_count"] == 1


def _bundle():
    return build_idea_validation_bundle(
        json.loads(FIXTURE_IDEA.read_text(encoding="utf-8")),
        source=FIXTURE_IDEA.as_posix(),
    )


def _slice(label_spec_id: str, **overrides: object) -> GateSlice:
    payload = {
        "slice_id": "unit-slice",
        "dataset_version_id": DATASET_VERSION_ID,
        "partition_id": PARTITION_ID,
        "feature_pack_refs": (FEATURE_VERSION_ID,),
        "label_pack_refs": (LABEL_VERSION_ID,),
        "feature_request_ids": (),
        "label_spec_ids": (label_spec_id,),
        "path_label_observations": (
            {"label_value": True},
            {"label_value": False},
            {"label_value": True},
        ),
        "path_label_class_counts": None,
        "n_eff": 24,
        "minimum_detectable_effect": 0.25,
        "available_ts_satisfiable": True,
        "surrogate_fdr_requirement": ZERO_PASS_MET,
    }
    payload.update(overrides)
    return GateSlice(**payload)


def _resolver(label_spec_id: str) -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: _feature_record()}),
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _label_record(label_spec_id)}),
    )


def _statuses(result) -> dict[str, GateStatus]:
    return {check.check_id: check.status for check in result.checks}


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("known_ahead_context",)
    input_views: tuple[str, ...] = ("canonical_ohlcv",)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str = FEATURE_REQUEST_ID
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_ID
    feature_set_id: str = "fset_testability_gate"
    feature_set_version: str = "1"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "feature_plan_testability_gate"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=10)
    first_available_ts: datetime = BASE_TS + timedelta(seconds=1)
    last_available_ts: datetime = BASE_TS + timedelta(minutes=10, seconds=1)
    lifecycle_state: str = "REGISTERED"
    replacement_feature_version_id: str = ""
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_spec_id: str
    label_version_id: str = LABEL_VERSION_ID
    label_id: str = "path_target_before_stop"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "label_plan_testability_gate"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=10)
    first_label_available_ts: datetime = BASE_TS + timedelta(minutes=30)
    last_label_available_ts: datetime = BASE_TS + timedelta(minutes=40)
    lifecycle_state: str = "REGISTERED"


class _FeatureStore:
    def __init__(self, records: dict[str, _FeatureRecord]) -> None:
        self.records = records
        self.calls: list[str] = []

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        self.calls.append(feature_version_id)
        return self.records.get(feature_version_id)


class _LabelRegistry:
    def __init__(self, records: dict[str, _LabelRecord]) -> None:
        self.records = records
        self.calls: list[str] = []

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        self.calls.append(label_version_id)
        return self.records.get(label_version_id)


def _feature_record() -> _FeatureRecord:
    return _FeatureRecord()


def _label_record(label_spec_id: str) -> _LabelRecord:
    return _LabelRecord(label_spec_id=label_spec_id)
