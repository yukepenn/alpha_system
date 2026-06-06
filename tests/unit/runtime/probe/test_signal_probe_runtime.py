from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.cost import CostModelVersion, CostStressSpec
from alpha_system.runtime.diagnostics.contracts import DiagnosticsRunSpecRef
from alpha_system.runtime.input_resolver import (
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
)
from alpha_system.runtime.probe import (
    DirectionPolicy,
    FillPolicy,
    FillTiming,
    SignalFeatureRef,
    SignalLabelRef,
    SignalProbeContractError,
    SignalProbeReport,
    SignalProbeSpec,
    build_next_bar_position_series,
    run_signal_probe,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
FEATURE_VERSION_ID = "fver_" + "c" * 64
LABEL_VERSION_ID = "lver_" + "d" * 64
DATASET_VERSION_ID = "dsv_signal_probe_synthetic_fixture_v1"


def test_signal_probe_import_surface_is_lazy_and_report_is_non_promotional() -> None:
    spec = _spec()

    report = run_signal_probe(
        signal_probe_spec=spec,
        observations=_observations(),
        cost_diagnostics_run_spec=_cost_diagnostics_ref(),
        lineage_refs={"run_id": "synthetic_signal_probe_unit"},
    )

    assert isinstance(report, SignalProbeReport)
    assert report.status is StudyRunResultState.SIGNAL_PROBE_COMPLETE
    assert report.fast_path is True
    assert report.not_strategy_validation is True
    assert report.not_a_candidate is True
    assert report.cost_stress_evidence_state == "COST_STRESS_COMPLETE"
    assert report.trade_summary["trade_count"] > 0
    assert report.position_summary["same_bar_fill_count"] == 0
    assert "double_cost_expectancy_proxy" in report.cost_aware_expectancy_proxy
    assert report.to_dict()["promotion_basis_allowed"] is False
    assert report.to_dict()["not_a_backtest"] is True


def test_spec_is_immutable_hashable_and_requires_bounded_no_same_bar_inputs() -> None:
    spec = _spec()

    assert hash(spec)
    with pytest.raises(SignalProbeContractError, match="same-bar"):
        FillPolicy(timing=FillTiming.EXPLICIT_DELAY, delay_bars=0)
    with pytest.raises(SignalProbeContractError, match="bounded"):
        _spec(thresholds=tuple(str(index + 1) for index in range(10)))
    with pytest.raises(SignalProbeContractError, match="alpha_spec_ref"):
        _spec(alpha_spec_ref=None)
    with pytest.raises(SignalProbeContractError, match="label fields"):
        _spec(feature_ref=SignalFeatureRef(FEATURE_VERSION_ID, FEATURE_REQUEST_REF, "label_value"))


def test_locked_partition_requires_contamination_metadata() -> None:
    with pytest.raises(SignalProbeContractError, match="contamination"):
        _spec(runtime_input_pack=_input_pack(partition_id="locked_test_candidate"))

    spec = _spec(
        runtime_input_pack=_input_pack(
            partition_id="locked_test_candidate",
            governance_metadata={"contamination_review": "documented synthetic fixture"},
        )
    )

    assert spec.runtime_input_pack.partition_scope["partition_id"] == "locked_test_candidate"


def test_next_bar_fill_rule_builds_positions_without_same_bar_execution() -> None:
    series = build_next_bar_position_series(
        _observations(),
        threshold=Decimal("0.5"),
        direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
        fill_policy=FillPolicy(),
    )

    assert series.positions[0] == 0
    assert series.positions[1] == 1
    assert series.origin_signal_indices[1] == 0
    assert all(fill.fill_index > fill.origin_signal_index for fill in series.fills)
    assert series.to_summary()["same_bar_fill_count"] == 0


def test_runner_returns_visible_blocked_report_for_missing_availability() -> None:
    bad_rows = list(_observations())
    bad_rows[0] = {key: value for key, value in bad_rows[0].items() if key != "available_ts"}

    report = run_signal_probe(
        signal_probe_spec=_spec(),
        observations=bad_rows,
        cost_diagnostics_run_spec=_cost_diagnostics_ref(),
        lineage_refs={"run_id": "synthetic_signal_probe_blocked"},
    )

    assert report.status is StudyRunResultState.BLOCKED
    assert report.rejection_reason is not None
    assert report.rejection_reason.code == "probe_observation_contract_invalid"
    assert report.cost_sensitivity_report_ref.report_kind == "cost_sensitivity_report"


def _spec(
    *,
    alpha_spec_ref: str | None = ALPHA_SPEC_REF,
    runtime_input_pack: RuntimeInputPack | None = None,
    feature_ref: SignalFeatureRef | None = None,
    thresholds: tuple[str, ...] = ("0.5", "0.55"),
) -> SignalProbeSpec:
    input_pack = runtime_input_pack or _input_pack()
    return SignalProbeSpec(
        alpha_spec_ref=alpha_spec_ref,
        study_spec_ref=STUDY_SPEC_REF,
        runtime_input_pack=input_pack,
        feature_ref=feature_ref
        or SignalFeatureRef.from_feature_pack(input_pack.feature_packs[0], signal_name="zscore"),
        label_ref=SignalLabelRef.from_label_pack(
            input_pack.label_packs[0],
            label_name="forward_return",
            horizon="5m",
        ),
        direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
        thresholds=thresholds,
        primary_threshold=thresholds[0],
        fill_policy=FillPolicy(),
        cost_stress_spec=CostStressSpec(cost_model_version=_cost_model_version()),
        spec_metadata={"fixture": "synthetic signal probe unit only"},
    )


def _input_pack(
    *,
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
            "dataset_scope": {"source": "synthetic fixture metadata only"},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="synthetic",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(
            FeaturePackHandle(
                feature_version_id=FEATURE_VERSION_ID,
                feature_request_id=FEATURE_REQUEST_REF,
                feature_set_id="fset_signal_probe_synthetic",
                feature_set_version="1",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id=partition_id,
                materialization_plan_id="feature_plan_signal_probe_synthetic",
                first_event_ts="2026-01-02T14:30:00+00:00",
                last_event_ts="2026-01-02T14:35:00+00:00",
                first_available_ts="2026-01-02T14:30:05+00:00",
                last_available_ts="2026-01-02T14:35:05+00:00",
                lifecycle_state="REGISTERED",
            ),
        ),
        label_packs=(
            LabelPackHandle(
                label_version_id=LABEL_VERSION_ID,
                label_spec_id=LABEL_SPEC_REF,
                label_id="forward_return_5m",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id=partition_id,
                materialization_plan_id="label_plan_signal_probe_synthetic",
                first_event_ts="2026-01-02T14:30:00+00:00",
                last_event_ts="2026-01-02T14:35:00+00:00",
                first_label_available_ts="2026-01-02T14:35:00+00:00",
                last_label_available_ts="2026-01-02T14:40:00+00:00",
                lifecycle_state="READY_FOR_STUDY",
            ),
        ),
        dataset_scope={"source": "synthetic fixture metadata only"},
        partition_scope={"partition_id": partition_id},
        session_scope={"session": "rth_only"},
        governance_metadata=governance_metadata,
    )


def _cost_model_version() -> CostModelVersion:
    return CostModelVersion.from_mappings(
        cost_model_descriptor={"model": "bps_cost", "bps": "0.1"},
        slippage_model_descriptor={"model": "bps", "bps": "0.1"},
        bbo_available=False,
    )


def _cost_diagnostics_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _observations() -> tuple[dict[str, object], ...]:
    return (
        _row(0, "0.6", "0.0"),
        _row(1, "0.6", "0.3"),
        _row(2, "-0.6", "0.25"),
        _row(3, "-0.6", "-0.3"),
        _row(4, "0.0", "-0.25"),
        _row(5, "0.7", "0.0"),
    )


def _row(index: int, feature: str, label: str) -> dict[str, object]:
    minute = 30 + index
    return {
        "row_id": f"row-{index}",
        "event_ts": f"2026-01-02T14:{minute:02d}:00+00:00",
        "available_ts": f"2026-01-02T14:{minute:02d}:05+00:00",
        "label_available_ts": f"2026-01-02T14:{minute + 5:02d}:00+00:00",
        "feature_value": feature,
        "label_value": label,
        "price": "1",
        "session_label": "RTH",
    }
