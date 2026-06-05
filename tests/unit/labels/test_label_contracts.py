from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureSpec,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.version import (
    BarrierSpec,
    CostAdjustmentSpec,
    LabelAvailabilityPolicy,
    LabelContractError,
    LabelContractSpec,
    LabelFamily,
    LabelHorizonSpec,
    LabelInputSpec,
    LabelLineageRecord,
    LabelPathSpec,
    LabelValueRecord,
)


def test_label_contract_objects_are_immutable_hashable_and_governance_bound() -> None:
    governance_spec = _governance_label_spec()
    contract = _label_contract(governance_spec)
    version = contract.derive_label_version()
    lineage = LabelLineageRecord(
        label_version=version,
        label_contract=contract,
        label_spec_id=contract.label_spec_id,
        contract_provenance={"phase": "FLF-P16"},
    )
    value = LabelValueRecord(
        label_version_id=version.label_version_id,
        entity_id="ES",
        event_ts=_dt("2024-01-02T14:30:00+00:00"),
        horizon_end_ts=_dt("2024-01-02T14:35:00+00:00"),
        label_available_ts=_dt("2024-01-02T14:37:00+00:00"),
        value=0.25,
        label_contract=contract,
    )

    assert contract.label_spec_id == governance_spec.label_spec_id
    assert contract.label_spec_id.startswith("lspec_")
    assert contract.horizon.horizon == governance_spec.horizon
    assert contract.path.path_rules.to_dict() == governance_spec.path_rules
    assert contract.cost_adjustment.cost_model.to_dict() == governance_spec.cost_model
    assert contract.barriers.target_stop_rules.to_dict() == governance_spec.target_stop_rules
    assert (
        contract.availability_policy.forbidden_feature_overlap.to_dict()
        == governance_spec.forbidden_feature_overlap
    )
    assert tuple(contract.availability_policy.leakage_checks) == tuple(
        governance_spec.leakage_checks
    )
    assert version.label_version_id.startswith("lver_")
    assert len(version.content_hash) == 64
    assert lineage.label_version == version
    assert value.label_spec_id == contract.label_spec_id

    for item in (
        contract.inputs,
        contract.horizon,
        contract.path,
        contract.barriers,
        contract.cost_adjustment,
        contract.availability_policy,
        contract,
        version,
        lineage,
        value,
    ):
        assert isinstance(hash(item), int)

    with pytest.raises(FrozenInstanceError):
        contract.label_id = "mutated"  # type: ignore[misc]


def test_label_version_is_deterministic_and_collision_sensitive() -> None:
    first = _label_contract(contract_metadata={"purpose": "fixture"}).derive_label_version()
    second = _label_contract(contract_metadata={"purpose": "fixture"}).derive_label_version()
    changed = _label_contract(contract_metadata={"purpose": "changed"}).derive_label_version()

    assert first == second
    assert changed != first
    assert changed.content_hash != first.content_hash


def test_missing_lspec_binding_fails_closed() -> None:
    governance_spec = _governance_label_spec()

    with pytest.raises(LabelContractError, match="lspec_ binding"):
        LabelContractSpec(
            label_id="fixed_horizon_midprice_forward_5m",
            family=LabelFamily.FIXED_HORIZON,
            governance_label_spec=None,
            inputs=_label_inputs(),
            horizon=LabelHorizonSpec.from_label_spec(governance_spec),
            path=LabelPathSpec.from_label_spec(governance_spec),
            barriers=BarrierSpec.from_label_spec(governance_spec),
            cost_adjustment=CostAdjustmentSpec.from_label_spec(governance_spec),
            availability_policy=LabelAvailabilityPolicy.from_label_spec(governance_spec),
        )


def test_component_mismatch_with_governance_lspec_fails_closed() -> None:
    governance_spec = _governance_label_spec()

    with pytest.raises(LabelContractError, match="LabelSpec.horizon"):
        LabelContractSpec(
            label_id="fixed_horizon_midprice_forward_5m",
            family=LabelFamily.FIXED_HORIZON,
            governance_label_spec=governance_spec,
            inputs=_label_inputs(),
            horizon=LabelHorizonSpec(
                horizon="10m",
                horizon_end_rule="label.horizon_end_ts is derived from LabelSpec.horizon",
            ),
            path=LabelPathSpec.from_label_spec(governance_spec),
            barriers=BarrierSpec.from_label_spec(governance_spec),
            cost_adjustment=CostAdjustmentSpec.from_label_spec(governance_spec),
            availability_policy=LabelAvailabilityPolicy.from_label_spec(governance_spec),
        )


def test_label_value_record_requires_label_available_ts() -> None:
    contract = _label_contract()
    version = contract.derive_label_version()

    with pytest.raises(TypeError):
        LabelValueRecord(  # type: ignore[call-arg]
            label_version_id=version.label_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:30:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:35:00+00:00"),
            value=0.25,
            label_contract=contract,
        )
    with pytest.raises(LabelContractError, match="label_available_ts"):
        LabelValueRecord(
            label_version_id=version.label_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:30:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:35:00+00:00"),
            label_available_ts=None,  # type: ignore[arg-type]
            value=0.25,
            label_contract=contract,
        )


def test_label_value_record_rejects_pre_availability_timestamp() -> None:
    contract = _label_contract()
    version = contract.derive_label_version()

    with pytest.raises(LabelContractError, match="LabelSpec.availability_time"):
        LabelValueRecord(
            label_version_id=version.label_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:30:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:35:00+00:00"),
            label_available_ts=_dt("2024-01-02T14:36:00+00:00"),
            value=0.25,
            label_contract=contract,
        )


def test_label_cannot_be_reached_as_live_feature() -> None:
    contract = _label_contract()

    with pytest.raises(LabelContractError, match="live feature"):
        contract.validate_live_feature_references(
            [
                {
                    "feature_id": "fixed_horizon_midprice_forward_5m",
                    "available_at": "2024-01-02T14:31:00+00:00",
                }
            ]
        )

    result = contract.validate_live_feature_references(
        [
            {
                "feature_id": "causal_close_return_1m",
                "available_at": "2024-01-02T14:31:00+00:00",
            }
        ]
    )
    assert result.is_clean


def test_future_windows_are_rejected_for_live_features_but_allowed_for_labels() -> None:
    future_window = WindowSpec(
        kind=WindowKind.FUTURE,
        length=5,
        causality=WindowCausality.FUTURE,
        offline_only=True,
    )

    with pytest.raises(ValueError, match="live FeatureSpec"):
        FeatureSpec(
            feature_id="illegal_future_feature",
            family=FeatureFamily.BASE_OHLCV,
            feature_request_id="freq_aaaaaaaaaaaaaaaaaaaaaaaa",
            inputs=FeatureInputSpec(
                input_views=("canonical_ohlcv",),
                fields=("close", "available_ts"),
                dataset_version_ids=("dsv_synthetic_accepted",),
            ),
            transform=TransformSpec(transform_id="future_mean"),
            window=future_window,
            normalization=NormalizationSpec(normalization_id="identity"),
            availability_assumptions={"source": "synthetic accepted DatasetVersion"},
            available_ts_derivation_rule="feature.available_ts = max(input.available_ts)",
            live=True,
        )

    contract = _label_contract(window=future_window)
    assert contract.path.window == future_window
    assert contract.path.uses_forward_data is True
    assert contract.availability_policy.future_data_legal_only_for_labels is True


def _label_contract(
    governance_spec: LabelSpec | None = None,
    *,
    window: WindowSpec | None = None,
    contract_metadata: dict[str, object] | None = None,
) -> LabelContractSpec:
    return LabelContractSpec.from_label_spec(
        label_id="fixed_horizon_midprice_forward_5m",
        family=LabelFamily.FIXED_HORIZON,
        governance_label_spec=governance_spec or _governance_label_spec(),
        inputs=_label_inputs(),
        window=window,
        contract_metadata=contract_metadata,
    )


def _label_inputs() -> LabelInputSpec:
    return LabelInputSpec(
        input_views=("canonical_bbo",),
        fields=("bid", "ask", "available_ts"),
        dataset_version_ids=("dsv_synthetic_accepted",),
        input_metadata={"source": "accepted synthetic DatasetVersion fixture"},
    )


def _governance_label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="5m",
        path_rules={
            "path": "midprice_forward_return",
            "terminal_rule": "first valid BBO mid at horizon end",
            "horizon_steps": 5,
        },
        cost_model={
            "model": "gross_midprice",
            "spread_adjustment": "not_applied_in_fixed_horizon_fixture",
        },
        target_stop_rules={
            "target_rule": "disabled_for_fixed_horizon_fixture",
            "stop_rule": "disabled_for_fixed_horizon_fixture",
        },
        availability_time="2024-01-02T14:37:00+00:00",
        forbidden_feature_overlap={
            "label_ids": ["fixed_horizon_midprice_forward_5m"],
            "aliases": ["midprice_forward_5m"],
            "transforms": ["label(fixed_horizon_midprice_forward_5m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
