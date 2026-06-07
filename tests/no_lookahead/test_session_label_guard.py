from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from alpha_system.runtime.audit import NoLookaheadRuntimeAudit
from alpha_system.runtime.input_resolver import (
    FeaturePackHandle,
    FieldRole,
    LabelPackHandle,
    RuntimeInputPack,
    RuntimeInputResolverError,
    _reject_label_as_live_feature,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
FEATURE_VERSION_ID = "fver_" + "6" * 64
LABEL_VERSION_ID = "lver_" + "7" * 64
DATASET_VERSION_ID = "dsv_session_label_guard_fixture_v1"
DECISION_TS = "2026-01-02T14:36:00+00:00"
SESSION_METADATA = FieldRole.SESSION_METADATA.value


def test_declared_session_label_passes_resolver_and_audit() -> None:
    field_roles = {"session_label": SESSION_METADATA}

    _assert_resolver_accepts(fields=("close", "session_label"), field_roles=field_roles)
    result = _audit(
        feature_inputs=(
            _live_feature_input(
                fields=("close", "session_label"),
                field_roles=field_roles,
                values={"session_label": "RTH_with_ETH_context"},
            ),
        ),
    )

    assert result.accepted
    assert "label_as_feature_input" not in _reason_codes(result)


def test_session_label_without_role_declaration_is_rejected_by_resolver() -> None:
    _assert_resolver_rejects(fields=("session_label",), field_roles={})


@pytest.mark.parametrize(
    ("session_field", "value"),
    (
        ("rth_flag", True),
        ("eth_flag", False),
        ("session_minute", 12),
        ("session_segment", "pre_RTH"),
        ("session_segment", "post_RTH"),
    ),
)
def test_declared_session_context_fields_pass_resolver_and_audit(
    session_field: str,
    value: object,
) -> None:
    field_roles = {session_field: SESSION_METADATA}

    _assert_resolver_accepts(fields=(session_field,), field_roles=field_roles)
    result = _audit(
        feature_inputs=(
            _live_feature_input(
                fields=(session_field,),
                field_roles=field_roles,
                values={session_field: value},
            ),
        ),
    )

    assert result.accepted
    assert "label_as_feature_input" not in _reason_codes(result)


def test_fwd_return_feature_input_is_rejected_even_with_session_metadata_role() -> None:
    field_roles = {"fwd_ret_5m": SESSION_METADATA}

    _assert_resolver_rejects(fields=("fwd_ret_5m",), field_roles=field_roles)
    result = _audit(
        feature_inputs=(
            _live_feature_input(fields=("fwd_ret_5m",), field_roles=field_roles),
        ),
    )

    assert result.rejected
    assert "label_as_feature_input" in _reason_codes(result)


def test_target_label_feature_input_is_rejected() -> None:
    _assert_resolver_rejects(
        fields=("target_label",),
        field_roles={"target_label": SESSION_METADATA},
    )


@pytest.mark.parametrize("label_handle", (LABEL_VERSION_ID, LABEL_SPEC_REF))
def test_label_value_handles_cannot_be_accepted_as_feature_requests(
    label_handle: str,
) -> None:
    result = _audit(runtime_input_pack=_input_pack(feature_request_ids=(label_handle,)))

    assert result.rejected
    assert "label_as_feature_input" in _reason_codes(result)


@pytest.mark.parametrize(
    "field_name",
    ("final_session_high", "final_session_low", "final_session_vwap"),
)
def test_final_session_fields_are_rejected_even_with_session_metadata_role(
    field_name: str,
) -> None:
    field_roles = {field_name: SESSION_METADATA}

    _assert_resolver_rejects(fields=(field_name,), field_roles=field_roles)
    result = _audit(
        feature_inputs=(
            _live_feature_input(fields=(field_name,), field_roles=field_roles),
        ),
    )

    assert result.rejected
    assert "label_as_feature_input" in _reason_codes(result)


def test_rth_with_eth_context_session_metadata_passes_with_valid_available_ts() -> None:
    field_roles = {
        "session_label": SESSION_METADATA,
        "session_segment": SESSION_METADATA,
        "rth_flag": SESSION_METADATA,
        "eth_flag": SESSION_METADATA,
        "session_minute": SESSION_METADATA,
    }

    _assert_resolver_accepts(
        fields=tuple(field_roles),
        field_roles=field_roles,
    )
    result = _audit(
        feature_inputs=(
            _live_feature_input(
                fields=tuple(field_roles),
                field_roles=field_roles,
                values={
                    "session_label": "RTH_with_ETH_context",
                    "session_segment": "post_RTH",
                    "rth_flag": True,
                    "eth_flag": True,
                    "session_minute": 27,
                },
            ),
        ),
    )

    assert result.accepted
    assert "label_as_feature_input" not in _reason_codes(result)


def _assert_resolver_accepts(
    *,
    fields: tuple[str, ...],
    field_roles: dict[str, object],
) -> None:
    _reject_label_as_live_feature(
        _feature_record(fields, field_roles), field="feature_pack_refs[0]"
    )


def _assert_resolver_rejects(
    *,
    fields: tuple[str, ...],
    field_roles: dict[str, object],
) -> None:
    with pytest.raises(RuntimeInputResolverError) as exc_info:
        _reject_label_as_live_feature(
            _feature_record(fields, field_roles),
            field="feature_pack_refs[0]",
        )
    assert exc_info.value.reason.code == "label_as_feature_input"


def _feature_record(fields: tuple[str, ...], field_roles: dict[str, object]) -> _FeatureRecord:
    return _FeatureRecord(
        feature_spec=_FeatureSpec(
            inputs=_Inputs(
                fields=fields,
                input_metadata={"field_roles": field_roles},
            )
        )
    )


def _audit(
    *,
    runtime_input_pack: RuntimeInputPack | None = None,
    feature_inputs: tuple[dict[str, object], ...] = (),
) -> Any:
    return NoLookaheadRuntimeAudit().evaluate(
        runtime_input_pack=runtime_input_pack or _input_pack(),
        decision_ts=DECISION_TS,
        signal_probe_report={
            "position_summary": {"same_bar_fill_count": 0},
            "trade_summary": {"fill_delay_bars": 1},
            "report_metadata": {"same_bar_optimistic_fill_forbidden": True},
        },
        feature_inputs=feature_inputs,
    )


def _live_feature_input(
    *,
    fields: tuple[str, ...],
    field_roles: dict[str, object],
    values: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_ts": "2026-01-02T14:35:00+00:00",
        "available_ts": "2026-01-02T14:35:05+00:00",
        "fields": fields,
        "field_roles": field_roles,
    }
    payload.update(values or {})
    return payload


def _input_pack(
    *,
    feature_request_ids: tuple[str, ...] = (FEATURE_REQUEST_REF,),
) -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack={
            "alpha_spec_id": ALPHA_SPEC_REF,
            "feature_request_ids": list(feature_request_ids),
            "label_spec_ids": [LABEL_SPEC_REF],
            "dataset_scope": {"source": "synthetic session label guard fixture"},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="synthetic",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(_feature_pack(),),
        label_packs=(_label_pack(),),
        dataset_scope={"source": "synthetic session label guard fixture"},
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "rth_and_eth"},
    )


def _feature_pack() -> FeaturePackHandle:
    return FeaturePackHandle(
        feature_version_id=FEATURE_VERSION_ID,
        feature_request_id=FEATURE_REQUEST_REF,
        feature_set_id="fset_session_label_guard",
        feature_set_version="1",
        dataset_version_id=DATASET_VERSION_ID,
        partition_id="development_partition",
        materialization_plan_id="feature_plan_session_label_guard",
        first_event_ts="2026-01-02T14:30:00+00:00",
        last_event_ts="2026-01-02T14:35:00+00:00",
        first_available_ts="2026-01-02T14:30:05+00:00",
        last_available_ts="2026-01-02T14:35:05+00:00",
        lifecycle_state="REGISTERED",
    )


def _label_pack() -> LabelPackHandle:
    return LabelPackHandle(
        label_version_id=LABEL_VERSION_ID,
        label_spec_id=LABEL_SPEC_REF,
        label_id="forward_return_5m",
        dataset_version_id=DATASET_VERSION_ID,
        partition_id="development_partition",
        materialization_plan_id="label_plan_session_label_guard",
        first_event_ts="2026-01-02T14:30:00+00:00",
        last_event_ts="2026-01-02T14:35:00+00:00",
        first_label_available_ts="2026-01-02T14:35:00+00:00",
        last_label_available_ts="2026-01-02T14:40:00+00:00",
        lifecycle_state="READY_FOR_STUDY",
    )


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...]
    input_views: tuple[str, ...] = ("canonical_ohlcv",)
    input_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    live: bool = True
    inputs: _Inputs = field(default_factory=lambda: _Inputs(fields=("close",)))


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_spec: _FeatureSpec
