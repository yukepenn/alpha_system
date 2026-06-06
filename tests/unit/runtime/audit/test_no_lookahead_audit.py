from __future__ import annotations

from dataclasses import replace

from alpha_system.runtime.audit import (
    NoLookaheadAuditOutcome,
    NoLookaheadRejectionCategory,
    NoLookaheadRuntimeAudit,
)
from alpha_system.runtime.cost import CostModelVersion, CostStressSpec
from alpha_system.runtime.input_resolver import (
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
)
from alpha_system.runtime.probe.spec import (
    FillPolicy,
    SignalFeatureRef,
    SignalLabelRef,
    SignalProbeSpec,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
FEATURE_VERSION_ID = "fver_" + "e" * 64
LABEL_VERSION_ID = "lver_" + "f" * 64
DATASET_VERSION_ID = "dsv_no_lookahead_audit_unit_fixture_v1"
DECISION_TS = "2026-01-02T14:36:00+00:00"


def test_audit_accepts_resolved_point_in_time_safe_runtime_metadata() -> None:
    pack = _input_pack()
    spec = _signal_probe_spec(pack)

    result = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=pack,
        decision_ts=DECISION_TS,
        signal_probe_spec=spec,
        signal_probe_report=_probe_report(same_bar_fill_count=0),
        probe_fill_records=({"fill_index": 1, "origin_signal_index": 0, "same_bar_fill": False},),
        live_feature_windows=(
            {"role": "live_feature", "window_type": "trailing", "lookback_bars": 3},
        ),
    )

    assert result.outcome is NoLookaheadAuditOutcome.POINT_IN_TIME_SAFE
    assert result.accepted is True
    assert result.rejected is False
    assert result.runtime_entry_reasons == ()
    payload = result.to_dict()
    assert payload["integrity_only"] is True
    assert payload["not_alpha_validation"] is True
    assert payload["raw_or_heavy_data_embedded"] is False


def test_failed_audit_carries_recordable_rejection_reason() -> None:
    pack = _input_pack(
        feature_pack=replace(
            _feature_pack(),
            first_available_ts="2026-01-02T14:37:00+00:00",
        )
    )

    result = NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=pack,
        decision_ts=DECISION_TS,
        signal_probe_report=_probe_report(same_bar_fill_count=0),
    )

    assert result.rejected is True
    assert result.rejection_reason is not None
    assert result.rejection_reason.code == "feature_available_ts_after_decision_ts"
    assert result.rejection_reason.category is NoLookaheadRejectionCategory.LEAKAGE_RISK
    runtime_reason = result.runtime_entry_reasons[0]
    assert runtime_reason.code == "feature_available_ts_after_decision_ts"
    assert runtime_reason.decision_state.value == "INPUTS_BLOCKED"


def _signal_probe_spec(runtime_input_pack: RuntimeInputPack) -> SignalProbeSpec:
    return SignalProbeSpec(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        runtime_input_pack=runtime_input_pack,
        feature_ref=SignalFeatureRef.from_feature_pack(
            runtime_input_pack.feature_packs[0],
            signal_name="zscore",
        ),
        label_ref=SignalLabelRef.from_label_pack(
            runtime_input_pack.label_packs[0],
            label_name="forward_return",
            horizon="5m",
        ),
        thresholds=("0.5", "0.55"),
        primary_threshold="0.5",
        fill_policy=FillPolicy(),
        cost_stress_spec=CostStressSpec(cost_model_version=_cost_model_version()),
        spec_metadata={"fixture": "synthetic no-lookahead audit unit"},
    )


def _input_pack(
    *,
    feature_pack: FeaturePackHandle | None = None,
    label_pack: LabelPackHandle | None = None,
    partition_id: str = "development_partition",
    governance_metadata: dict[str, object] | None = None,
) -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack={
            "alpha_spec_id": ALPHA_SPEC_REF,
            "feature_request_ids": [FEATURE_REQUEST_REF],
            "label_spec_ids": [LABEL_SPEC_REF],
            "dataset_scope": {"source": "synthetic audit fixture metadata only"},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="synthetic",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(feature_pack or _feature_pack(partition_id=partition_id),),
        label_packs=(label_pack or _label_pack(partition_id=partition_id),),
        dataset_scope={"source": "synthetic audit fixture metadata only"},
        partition_scope={"partition_id": partition_id},
        session_scope={"session": "rth_only"},
        governance_metadata=governance_metadata,
    )


def _feature_pack(*, partition_id: str = "development_partition") -> FeaturePackHandle:
    return FeaturePackHandle(
        feature_version_id=FEATURE_VERSION_ID,
        feature_request_id=FEATURE_REQUEST_REF,
        feature_set_id="fset_no_lookahead_audit",
        feature_set_version="1",
        dataset_version_id=DATASET_VERSION_ID,
        partition_id=partition_id,
        materialization_plan_id="feature_plan_no_lookahead_audit",
        first_event_ts="2026-01-02T14:30:00+00:00",
        last_event_ts="2026-01-02T14:35:00+00:00",
        first_available_ts="2026-01-02T14:30:05+00:00",
        last_available_ts="2026-01-02T14:35:05+00:00",
        lifecycle_state="REGISTERED",
    )


def _label_pack(*, partition_id: str = "development_partition") -> LabelPackHandle:
    return LabelPackHandle(
        label_version_id=LABEL_VERSION_ID,
        label_spec_id=LABEL_SPEC_REF,
        label_id="forward_return_5m",
        dataset_version_id=DATASET_VERSION_ID,
        partition_id=partition_id,
        materialization_plan_id="label_plan_no_lookahead_audit",
        first_event_ts="2026-01-02T14:30:00+00:00",
        last_event_ts="2026-01-02T14:35:00+00:00",
        first_label_available_ts="2026-01-02T14:35:00+00:00",
        last_label_available_ts="2026-01-02T14:40:00+00:00",
        lifecycle_state="READY_FOR_STUDY",
    )


def _cost_model_version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "0.1"},
        slippage_model_descriptor={"model": "bps", "bps": "0.1"},
        bbo_available=False,
    )


def _probe_report(*, same_bar_fill_count: int) -> dict[str, object]:
    return {
        "position_summary": {"same_bar_fill_count": same_bar_fill_count},
        "trade_summary": {"fill_delay_bars": 1},
        "report_metadata": {"same_bar_optimistic_fill_forbidden": True},
    }
