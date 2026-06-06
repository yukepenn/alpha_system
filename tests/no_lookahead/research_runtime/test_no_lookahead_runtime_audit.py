from __future__ import annotations

from dataclasses import replace
from typing import Any

from alpha_system.runtime.audit import NoLookaheadRuntimeAudit
from alpha_system.runtime.input_resolver import (
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
FEATURE_VERSION_ID = "fver_" + "1" * 64
LABEL_VERSION_ID = "lver_" + "2" * 64
DATASET_VERSION_ID = "dsv_no_lookahead_audit_synthetic_fixture_v1"
DECISION_TS = "2026-01-02T14:36:00+00:00"


def test_audit_rejects_feature_input_missing_available_ts() -> None:
    feature = replace(_feature_pack(), first_available_ts=None)

    result = _audit(_input_pack(feature_pack=feature))

    assert result.rejected
    assert "feature_available_ts_missing" in _reason_codes(result)


def test_audit_rejects_label_input_missing_label_available_ts() -> None:
    label = replace(_label_pack(), first_label_available_ts=None)

    result = _audit(_input_pack(label_pack=label))

    assert result.rejected
    assert "label_available_ts_missing" in _reason_codes(result)


def test_audit_rejects_label_as_live_feature_input() -> None:
    result = _audit(
        _input_pack(),
        feature_inputs=(
            {
                "event_ts": "2026-01-02T14:35:00+00:00",
                "available_ts": "2026-01-02T14:35:05+00:00",
                "fields": ("close", "label_value"),
            },
        ),
    )

    assert result.rejected
    assert "label_as_feature_input" in _reason_codes(result)


def test_audit_rejects_centered_or_future_live_feature_window() -> None:
    result = _audit(
        _input_pack(),
        live_feature_windows=(
            {
                "role": "live_feature",
                "window_type": "centered",
                "centered": True,
                "forward_horizon_bars": 2,
            },
        ),
    )

    assert result.rejected
    assert {
        "live_feature_centered_window",
        "live_feature_future_window",
    }.issubset(_reason_codes(result))


def test_audit_rejects_same_bar_probe_fill_metadata() -> None:
    result = _audit(
        _input_pack(),
        signal_probe_report={
            "position_summary": {"same_bar_fill_count": 1},
            "trade_summary": {"fill_delay_bars": 0},
            "report_metadata": {"same_bar_optimistic_fill_forbidden": False},
        },
        probe_fill_records=({"fill_index": 3, "origin_signal_index": 3, "same_bar_fill": True},),
    )

    assert result.rejected
    assert "same_bar_optimistic_fill" in _reason_codes(result)


def test_audit_rejects_locked_test_use_without_contamination_metadata() -> None:
    result = _audit(_input_pack(partition_id="locked_test_candidate"))

    assert result.rejected
    assert "locked_partition_governance_metadata_missing" in _reason_codes(result)


def _audit(runtime_input_pack: RuntimeInputPack, **kwargs: Any) -> Any:
    options: dict[str, Any] = {
        "runtime_input_pack": runtime_input_pack,
        "decision_ts": DECISION_TS,
        "signal_probe_report": {
            "position_summary": {"same_bar_fill_count": 0},
            "trade_summary": {"fill_delay_bars": 1},
            "report_metadata": {"same_bar_optimistic_fill_forbidden": True},
        },
    }
    options.update(kwargs)
    return NoLookaheadRuntimeAudit().evaluate(**options)


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


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}
