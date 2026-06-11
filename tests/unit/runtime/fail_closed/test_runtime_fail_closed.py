from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.runtime.artifact_policy import classify_runtime_artifact
from alpha_system.runtime.audit import NoLookaheadRuntimeAudit
from alpha_system.runtime.contracts.run_record import (
    StudyRunRecord,
    StudyRunRecordContractError,
    StudyRunResultState,
)
from alpha_system.runtime.cost import (
    CostModelVersion,
    CostStressFill,
    CostStressProfile,
    CostStressSpec,
    CostStressSpecError,
    build_cost_sensitivity_report,
)
from alpha_system.runtime.decisions import (
    RejectionReasonCode,
    RejectionReasonRecord,
    RuntimeDecision,
    RuntimeDecisionStage,
    RuntimeDecisionState,
    RuntimeDecisionStateError,
    coerce_runtime_decision_state,
    is_prohibited_mvp_state_value,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpecRef
from alpha_system.runtime.entry_contract import (
    RuntimeEntryReason,
    RuntimeEntryRequest,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.grid import (
    BoundedGridOutcome,
    VariantBudget,
    validate_bounded_grid_request,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
    resolve_runtime_input_pack,
)
from alpha_system.runtime.probe import (
    DirectionPolicy,
    FillPolicy,
    FillTiming,
    SignalFeatureRef,
    SignalLabelRef,
    SignalProbeContractError,
    SignalProbeSpec,
)

FIXTURE_PATH = (
    Path(__file__).parents[3] / "fixtures" / "runtime" / "fail_closed" / "invalid_shortcuts.json"
)
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_entry_contract_blocks_requests_without_alpha_or_study_spec() -> None:
    fixture = _fixture()

    missing_alpha = evaluate_runtime_entry_request(
        replace(_entry_request(fixture), alpha_spec_ref=None)
    )
    missing_study = evaluate_runtime_entry_request(
        replace(_entry_request(fixture), study_spec_ref=None)
    )

    assert missing_alpha.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert missing_study.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "missing_alpha_spec_ref" in _reason_codes(missing_alpha)
    assert "missing_study_spec_ref" in _reason_codes(missing_study)


def test_inadmissible_dataset_version_lifecycle_blocks_resolution() -> None:
    fixture = _fixture()
    calls: list[tuple[object, object]] = []

    def resolver(registry_path: object, dataset_version_id: object) -> DatasetVersion:
        calls.append((registry_path, dataset_version_id))
        return _dataset_version(fixture)

    result = resolve_runtime_input_pack(
        _entry_result(fixture),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state=fixture["dataset_lifecycle"]["inadmissible"],
        feature_pack_refs=(_ids(fixture)["feature_version_id"],),
        label_pack_refs=(_ids(fixture)["label_version_id"],),
        partition_scope=fixture["partition_scope"]["development"],
        session_scope=fixture["session_scope"],
        feature_label_resolver=_resolver(fixture),
        dataset_version_resolver=resolver,
    )

    assert calls == [("/tmp/alpha_registry/datasets.sqlite", _ids(fixture)["dataset_version_id"])]
    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert result.input_pack is None
    assert "inadmissible_dataset_lifecycle_state" in _reason_codes(result)

    with pytest.raises(ValueError, match="not admissible"):
        _input_pack(fixture, dataset_lifecycle_state=fixture["dataset_lifecycle"]["inadmissible"])


def test_missing_available_ts_or_label_available_ts_blocks_runtime_inputs() -> None:
    fixture = _fixture()
    feature_missing = replace(_feature_record(fixture), first_available_ts=None)
    label_missing = replace(_label_record(fixture), first_label_available_ts=None)

    feature_result = _resolve(fixture, feature_record=feature_missing)
    label_result = _resolve(fixture, label_record=label_missing)

    assert feature_result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert label_result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_available_ts_missing" in _reason_codes(feature_result)
    assert "label_available_ts_missing" in _reason_codes(label_result)


def test_label_value_cannot_be_exposed_as_live_feature() -> None:
    fixture = _fixture()
    label_ref_result = resolve_runtime_input_pack(
        _entry_result(fixture),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state=fixture["dataset_lifecycle"]["admissible"],
        feature_pack_refs=(_ids(fixture)["label_version_id"],),
        label_pack_refs=(_ids(fixture)["label_version_id"],),
        partition_scope=fixture["partition_scope"]["development"],
        session_scope=fixture["session_scope"],
        feature_label_resolver=_resolver(fixture),
        dataset_version_resolver=lambda _path, _id: _dataset_version(fixture),
    )

    live_label_field = _resolve(
        fixture,
        feature_record=replace(
            _feature_record(fixture),
            feature_spec=_FeatureSpec(
                feature_request_id=_ids(fixture)["feature_request_ref"],
                inputs=_Inputs(fields=("close", "label_value")),
            ),
        ),
    )

    audit = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=_input_pack(fixture),
        decision_ts="2026-01-02T14:36:00+00:00",
        feature_inputs=(fixture["feature_inputs"]["label_value_as_live_feature"],),
    )

    assert label_ref_result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert live_label_field.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert audit.rejected
    assert "label_as_feature_input" in _reason_codes(label_ref_result)
    assert "label_as_feature_input" in _reason_codes(live_label_field)
    assert "label_as_feature_input" in _reason_codes(audit)


def test_same_bar_probe_fill_policy_is_hard_rejected() -> None:
    fixture = _fixture()
    policy = fixture["probe"]["same_bar_policy"]

    with pytest.raises(SignalProbeContractError, match="same-bar"):
        FillPolicy(
            timing=FillTiming(policy["timing"]),
            delay_bars=policy["delay_bars"],
            allow_same_bar_fill=policy["allow_same_bar_fill"],
        )

    audit = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=_input_pack(fixture),
        decision_ts="2026-01-02T14:36:00+00:00",
        signal_probe_report=fixture["probe"]["same_bar_report"],
        probe_fill_records=(fixture["probe"]["same_bar_fill_record"],),
    )

    assert audit.rejected
    assert "same_bar_optimistic_fill" in _reason_codes(audit)


def test_unbounded_grid_and_variant_budget_overage_record_visible_rejections() -> None:
    fixture = _fixture()
    grid_fixture = fixture["grid"]["variant_budget_exceeded"]

    unbounded = validate_bounded_grid_request(
        run_id="run_rt_p20_unbounded_grid",
        binding_ref=_grid_binding(fixture),
        parameter_axes=fixture["grid"]["unbounded_parameter_axes"],
        variant_budget=VariantBudget(max_variants=3),
    )
    budget_exceeded = validate_bounded_grid_request(
        run_id="run_rt_p20_budget_exceeded",
        binding_ref=_grid_binding(fixture),
        parameter_axes=grid_fixture["parameter_axes"],
        variant_budget=VariantBudget(max_variants=grid_fixture["max_variants"]),
    )

    assert unbounded.rejected
    assert budget_exceeded.rejected
    assert unbounded.record.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
    assert budget_exceeded.record.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
    assert "unbounded_grid" in _grid_reason_codes(unbounded.record)
    assert "variant_budget_exceeded" in _grid_reason_codes(budget_exceeded.record)


def test_locked_test_without_metadata_or_selection_is_blocked() -> None:
    fixture = _fixture()

    missing_metadata = resolve_runtime_input_pack(
        _entry_result(fixture),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state=fixture["dataset_lifecycle"]["admissible"],
        feature_pack_refs=(_ids(fixture)["feature_version_id"],),
        label_pack_refs=(_ids(fixture)["label_version_id"],),
        partition_scope=fixture["partition_scope"]["locked_test_without_metadata"],
        session_scope=fixture["session_scope"],
        feature_label_resolver=_resolver(fixture, partition_id="locked_test_candidate"),
        dataset_version_resolver=lambda _path, _id: _dataset_version(fixture),
    )
    selection = resolve_runtime_input_pack(
        _entry_result(fixture),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state=fixture["dataset_lifecycle"]["admissible"],
        feature_pack_refs=(_ids(fixture)["feature_version_id"],),
        label_pack_refs=(_ids(fixture)["label_version_id"],),
        partition_scope=fixture["partition_scope"]["locked_test_selection"],
        session_scope=fixture["session_scope"],
        governance_metadata={"contamination_review_ref": "rt_p20_synthetic_fixture"},
        partition_purpose="locked_test_selection",
        feature_label_resolver=_resolver(fixture, partition_id="locked_test_candidate"),
        dataset_version_resolver=lambda _path, _id: _dataset_version(fixture),
    )

    assert missing_metadata.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE
    assert selection.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "locked_partition_governance_metadata_missing" in _reason_codes(missing_metadata)
    assert "locked_test_selection_forbidden" in _reason_codes(selection)


def test_probe_requires_cost_stress_double_cost_and_slippage_proxy_label() -> None:
    fixture = _fixture()

    with pytest.raises(SignalProbeContractError, match="CostStressSpec"):
        SignalProbeSpec(
            alpha_spec_ref=_ids(fixture)["alpha_spec_ref"],
            study_spec_ref=_ids(fixture)["study_spec_ref"],
            runtime_input_pack=_input_pack(fixture),
            feature_ref=SignalFeatureRef.from_feature_pack(
                _input_pack(fixture).feature_packs[0],
                signal_name="zscore",
            ),
            label_ref=SignalLabelRef.from_label_pack(
                _input_pack(fixture).label_packs[0],
                label_name="forward_return",
                horizon="5m",
            ),
            direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
            thresholds=("0.5",),
            cost_stress_spec=None,
        )

    with pytest.raises(CostStressSpecError, match="double_cost"):
        CostStressSpec(
            cost_model_version=_cost_model_version(),
            profiles=tuple(
                CostStressProfile.from_mapping(profile)
                for profile in fixture["probe"]["cost_profiles_missing_double_cost"]
            ),
        )

    report = build_cost_sensitivity_report(
        diagnostics_run_spec=_cost_diagnostics_ref(),
        fills=(CostStressFill(price=Decimal("1"), quantity=Decimal("1"), side="buy"),),
        lineage_refs={"run_id": "run_rt_p20_cost_proxy"},
        cost_stress_spec=CostStressSpec(cost_model_version=_cost_model_version()),
    )

    assert report.slippage_labeled_proxy is True
    assert report.to_dict()["slippage_labeled_proxy"] is True
    assert report.double_cost_summary.profile_name == "double_cost"


def test_failed_or_inconclusive_records_cannot_hide_rejection_reasons() -> None:
    with pytest.raises(StudyRunRecordContractError, match="visible rejection reason"):
        StudyRunRecord(
            run_id="run_rt_p20_hidden_failure",
            study_run_spec_ref=_study_run_spec_ref(),
            result_state=StudyRunResultState.REJECTED,
            manifest_ref=_manifest_ref(),
        )

    reason = RuntimeEntryReason(
        code="synthetic_rejection",
        message="Synthetic RT-P20 rejection reason.",
        field="request",
        decision_state=RuntimeEntryStatus.INPUTS_BLOCKED,
        expected="blocked fixture",
        actual="invalid shortcut",
    )
    record = StudyRunRecord(
        run_id="run_rt_p20_visible_failure",
        study_run_spec_ref=_study_run_spec_ref(),
        result_state=StudyRunResultState.REJECTED,
        manifest_ref=_manifest_ref(),
        rejection_reasons=(reason,),
    )
    decision_reason = RejectionReasonRecord(
        code=RejectionReasonCode.INCONCLUSIVE,
        message="Synthetic inconclusive runtime result.",
        decision_state=RuntimeDecisionState.INCONCLUSIVE,
        stage=RuntimeDecisionStage.DIAGNOSTICS,
        source_code="synthetic_inconclusive",
    )

    with pytest.raises(RuntimeDecisionStateError, match="visible reasons"):
        RuntimeDecision(state=RuntimeDecisionState.INCONCLUSIVE)

    decision = RuntimeDecision(
        state=RuntimeDecisionState.INCONCLUSIVE,
        reasons=(decision_reason,),
    )

    assert record.to_dict()["result_state"] == "REJECTED"
    assert record.to_dict()["rejection_reasons"][0]["code"] == "synthetic_rejection"
    assert decision.to_dict()["state"] == "INCONCLUSIVE"
    assert decision.to_dict()["reasons"][0]["source_code"] == "synthetic_inconclusive"


def test_prohibited_mvp_states_are_unreachable() -> None:
    for state in _fixture()["prohibited_mvp_states"]:
        assert is_prohibited_mvp_state_value(state)
        assert state not in {item.value for item in RuntimeDecisionState}
        with pytest.raises(RuntimeDecisionStateError, match="prohibited MVP state"):
            coerce_runtime_decision_state(state)


def test_runtime_artifact_policy_blocks_raw_or_heavy_tool_payload_shapes() -> None:
    fixture = _fixture()

    raw_values = classify_runtime_artifact(fixture["artifact_descriptors"]["raw_runtime_values"])
    summary = classify_runtime_artifact(fixture["artifact_descriptors"]["curated_summary"])

    assert raw_values.local_only is True
    assert raw_values.commit_allowed is False
    assert "contains_runtime_values" in raw_values.reasons
    assert "heavy_artifact" in raw_values.forbidden_classes
    assert summary.commit_allowed is True
    assert summary.local_only is False


def _fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["synthetic_attestation"]["market_data"] is False
    return payload


def _ids(fixture: Mapping[str, Any]) -> Mapping[str, str]:
    return fixture["ids"]


def _entry_request(fixture: Mapping[str, Any]) -> RuntimeEntryRequest:
    ids = _ids(fixture)
    return RuntimeEntryRequest(
        alpha_spec_ref=ids["alpha_spec_ref"],
        study_spec_ref=ids["study_spec_ref"],
        study_input_pack=StudyInputPack(
            feature_request_ids=[ids["feature_request_ref"]],
            label_spec_ids=[ids["label_spec_ref"]],
            alpha_spec_id=ids["alpha_spec_ref"],
            dataset_scope=fixture["dataset_scope"],
        ),
        target_dataset_version_id=ids["dataset_version_id"],
        dataset_scope=fixture["dataset_scope"],
        partition_scope=fixture["partition_scope"]["development"],
        expected_dataset_lifecycle_state=fixture["dataset_lifecycle"]["admissible"],
        dataset_version_source_family="synthetic",
    )


def _entry_result(fixture: Mapping[str, Any]) -> Any:
    result = evaluate_runtime_entry_request(_entry_request(fixture))
    assert result.resolved
    return result


def _resolve(
    fixture: Mapping[str, Any],
    *,
    feature_record: Any | None = None,
    label_record: Any | None = None,
) -> Any:
    return resolve_runtime_input_pack(
        _entry_result(fixture),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state=fixture["dataset_lifecycle"]["admissible"],
        feature_pack_refs=(_ids(fixture)["feature_version_id"],),
        label_pack_refs=(_ids(fixture)["label_version_id"],),
        partition_scope=fixture["partition_scope"]["development"],
        session_scope=fixture["session_scope"],
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=_FeatureStore(
                {_ids(fixture)["feature_version_id"]: feature_record or _feature_record(fixture)}
            ),
            label_registry=_LabelRegistry(
                {_ids(fixture)["label_version_id"]: label_record or _label_record(fixture)}
            ),
        ),
        dataset_version_resolver=lambda _path, _id: _dataset_version(fixture),
    )


def _dataset_version(fixture: Mapping[str, Any]) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=_ids(fixture)["dataset_version_id"],
        source="synthetic",
        symbol_universe=("SYNTH",),
        bar_size="1m",
        what_to_show="TRADES",
        start_ts=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end_ts=datetime(2026, 1, 2, 14, 40, tzinfo=UTC),
        contract_universe=("SYNTHM6",),
        roll_policy_id="synthetic_roll_policy_rt_p20",
        manifest_hash="0" * 64,
        code_hash="1" * 64,
        config_hash="2" * 64,
        quality_report_hash="3" * 64,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("close", "volume")
    input_views: tuple[str, ...] = ("canonical_ohlcv",)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str
    feature_request_id: str
    feature_set_id: str
    feature_set_version: str
    dataset_version_id: str
    partition_id: str
    materialization_plan_id: str
    first_event_ts: datetime
    last_event_ts: datetime
    first_available_ts: datetime | None
    last_available_ts: datetime | None
    lifecycle_state: str
    feature_spec: _FeatureSpec


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str
    label_spec_id: str
    label_id: str
    dataset_version_id: str
    partition_id: str
    materialization_plan_id: str
    first_event_ts: datetime
    last_event_ts: datetime
    first_label_available_ts: datetime | None
    last_label_available_ts: datetime | None
    lifecycle_state: str


class _FeatureStore:
    def __init__(self, records: Mapping[str, _FeatureRecord]) -> None:
        self.records = dict(records)

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        return self.records.get(feature_version_id)


class _LabelRegistry:
    def __init__(self, records: Mapping[str, _LabelRecord]) -> None:
        self.records = dict(records)

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        return self.records.get(label_version_id)


def _feature_record(
    fixture: Mapping[str, Any],
    *,
    partition_id: str = "development_partition",
) -> _FeatureRecord:
    ids = _ids(fixture)
    return _FeatureRecord(
        feature_version_id=ids["feature_version_id"],
        feature_request_id=ids["feature_request_ref"],
        feature_set_id="fset_rt_p20_synthetic",
        feature_set_version="1",
        dataset_version_id=ids["dataset_version_id"],
        partition_id=partition_id,
        materialization_plan_id="feature_plan_rt_p20_synthetic",
        first_event_ts=BASE_TS,
        last_event_ts=BASE_TS + timedelta(minutes=2),
        first_available_ts=BASE_TS,
        last_available_ts=BASE_TS + timedelta(minutes=2),
        lifecycle_state="REGISTERED",
        feature_spec=_FeatureSpec(feature_request_id=ids["feature_request_ref"]),
    )


def _label_record(
    fixture: Mapping[str, Any],
    *,
    partition_id: str = "development_partition",
) -> _LabelRecord:
    ids = _ids(fixture)
    return _LabelRecord(
        label_version_id=ids["label_version_id"],
        label_spec_id=ids["label_spec_ref"],
        label_id="forward_return_5m",
        dataset_version_id=ids["dataset_version_id"],
        partition_id=partition_id,
        materialization_plan_id="label_plan_rt_p20_synthetic",
        first_event_ts=BASE_TS,
        last_event_ts=BASE_TS + timedelta(minutes=2),
        first_label_available_ts=BASE_TS + timedelta(minutes=5),
        last_label_available_ts=BASE_TS + timedelta(minutes=7),
        lifecycle_state="REGISTERED",
    )


def _resolver(
    fixture: Mapping[str, Any],
    *,
    partition_id: str = "development_partition",
) -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore(
            {
                _ids(fixture)["feature_version_id"]: _feature_record(
                    fixture, partition_id=partition_id
                )
            }
        ),
        label_registry=_LabelRegistry(
            {_ids(fixture)["label_version_id"]: _label_record(fixture, partition_id=partition_id)}
        ),
    )


def _input_pack(
    fixture: Mapping[str, Any],
    *,
    dataset_lifecycle_state: str = "VERSIONED",
    partition_id: str = "development_partition",
    governance_metadata: Mapping[str, Any] | None = None,
) -> RuntimeInputPack:
    ids = _ids(fixture)
    return RuntimeInputPack(
        alpha_spec_ref=ids["alpha_spec_ref"],
        study_spec_ref=ids["study_spec_ref"],
        study_input_pack={
            "alpha_spec_id": ids["alpha_spec_ref"],
            "feature_request_ids": [ids["feature_request_ref"]],
            "label_spec_ids": [ids["label_spec_ref"]],
            "dataset_scope": fixture["dataset_scope"],
        },
        dataset_version_id=ids["dataset_version_id"],
        dataset_lifecycle_state=dataset_lifecycle_state,
        dataset_source="synthetic",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(
            FeaturePackHandle(
                feature_version_id=ids["feature_version_id"],
                feature_request_id=ids["feature_request_ref"],
                feature_set_id="fset_rt_p20_synthetic",
                feature_set_version="1",
                dataset_version_id=ids["dataset_version_id"],
                partition_id=partition_id,
                materialization_plan_id="feature_plan_rt_p20_synthetic",
                first_event_ts="2026-01-02T14:30:00+00:00",
                last_event_ts="2026-01-02T14:35:00+00:00",
                first_available_ts="2026-01-02T14:30:05+00:00",
                last_available_ts="2026-01-02T14:35:05+00:00",
                lifecycle_state="REGISTERED",
            ),
        ),
        label_packs=(
            LabelPackHandle(
                label_version_id=ids["label_version_id"],
                label_spec_id=ids["label_spec_ref"],
                label_id="forward_return_5m",
                dataset_version_id=ids["dataset_version_id"],
                partition_id=partition_id,
                materialization_plan_id="label_plan_rt_p20_synthetic",
                first_event_ts="2026-01-02T14:30:00+00:00",
                last_event_ts="2026-01-02T14:35:00+00:00",
                first_label_available_ts="2026-01-02T14:35:00+00:00",
                last_label_available_ts="2026-01-02T14:40:00+00:00",
                lifecycle_state="REGISTERED",
            ),
        ),
        dataset_scope=fixture["dataset_scope"],
        partition_scope={"partition_id": partition_id},
        session_scope=fixture["session_scope"],
        governance_metadata=governance_metadata,
    )


def _cost_model_version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "1.0"},
        slippage_model_descriptor={"model": "bps", "bps": "0.5"},
        bbo_available=False,
    )


def _cost_diagnostics_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _grid_binding(fixture: Mapping[str, Any]) -> dict[str, str]:
    ids = _ids(fixture)
    return {
        "alpha_spec_ref": ids["alpha_spec_ref"],
        "study_spec_ref": ids["study_spec_ref"],
        "study_run_spec_id": "srun_0123456789abcdef01234567",
        "study_run_spec_content_hash": "a" * 64,
        "signal_probe_spec_id": "sprobe_0123456789abcdef012345",
        "signal_probe_spec_content_hash": "b" * 64,
    }


def _study_run_spec_ref() -> dict[str, str]:
    return {
        "study_run_spec_id": "srun_rt_p20_synthetic_ref",
        "content_hash": "4" * 64,
    }


def _manifest_ref() -> dict[str, str]:
    return {
        "manifest_id": "manifest_rt_p20_synthetic",
        "manifest_hash": "5" * 64,
    }


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}


def _grid_reason_codes(record: Any) -> set[str]:
    return {reason.code for reason in record.rejection_reasons}
