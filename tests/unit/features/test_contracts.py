from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from alpha_system.experiments import feature_sets as experiment_feature_sets
from alpha_system.features.contracts import (
    FEATURE_SET_NAMESPACE,
    FeatureContractError,
    FeatureFamily,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
    FitPartitionPolicy,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.request_gate import evaluate_feature_request_gate
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_contract_objects_are_immutable_and_hashable() -> None:
    spec = _feature_spec()
    version = spec.derive_feature_version()
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
        contract_provenance={"phase": "FLF-P06"},
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_contract_fixture",
        feature_set_version="v1",
        features=(spec,),
    )
    value_record = FeatureValueRecord(
        feature_version_id=version.feature_version_id,
        entity_id="ES",
        event_ts=_dt("2024-01-02T14:32:00+00:00"),
        available_ts=_dt("2024-01-02T14:32:05+00:00"),
        value=1.25,
    )

    for item in (
        spec.inputs,
        spec.transform,
        spec.window,
        spec.normalization,
        spec,
        version,
        lineage,
        feature_set,
        value_record,
    ):
        assert isinstance(hash(item), int)

    with pytest.raises(FrozenInstanceError):
        spec.feature_id = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        spec.transform.parameters.items = ()  # type: ignore[misc]


@pytest.mark.parametrize("field_name", ["inputs", "transform", "window", "normalization"])
def test_feature_spec_missing_required_component_fails_closed(field_name: str) -> None:
    kwargs = _feature_spec_kwargs()
    kwargs[field_name] = None

    with pytest.raises(FeatureContractError, match=f"FeatureSpec.{field_name}"):
        FeatureSpec(**kwargs)


def test_feature_spec_requires_available_ts_derivation_rule() -> None:
    kwargs = _feature_spec_kwargs()
    kwargs["available_ts_derivation_rule"] = " "

    with pytest.raises(FeatureContractError, match="available_ts_derivation_rule"):
        FeatureSpec(**kwargs)


def test_feature_spec_implementation_eligibility_consumes_request_gate() -> None:
    decision = _approved_gate_decision()
    kwargs = _feature_spec_kwargs(feature_request_id=decision.feature_request_id)
    kwargs["implementation_eligible"] = True

    with pytest.raises(FeatureContractError, match="FeatureRequestGateDecision"):
        FeatureSpec(**kwargs)

    spec = FeatureSpec(**kwargs, request_gate_decision=decision)
    assert spec.implementation_eligible is True

    pending_decision = evaluate_feature_request_gate(
        _feature_request(FeatureRequestApprovalStatus.PENDING),
        EmptyRegistryReader(),
    )
    pending_kwargs = _feature_spec_kwargs(feature_request_id=pending_decision.feature_request_id)
    pending_kwargs["implementation_eligible"] = True
    with pytest.raises(FeatureContractError, match="did not admit implementation"):
        FeatureSpec(**pending_kwargs, request_gate_decision=pending_decision)


def test_live_feature_spec_rejects_offline_only_centered_and_future_windows() -> None:
    with pytest.raises(FeatureContractError, match="offline_only"):
        WindowSpec(
            kind=WindowKind.CENTERED,
            length=5,
            causality=WindowCausality.CENTERED,
            offline_only=False,
        )

    centered_window = WindowSpec(
        kind=WindowKind.CENTERED,
        length=5,
        causality=WindowCausality.CENTERED,
        offline_only=True,
    )
    with pytest.raises(FeatureContractError, match="live FeatureSpec"):
        FeatureSpec(**_feature_spec_kwargs(window=centered_window, live=True))

    offline_spec = FeatureSpec(**_feature_spec_kwargs(window=centered_window, live=False))
    assert offline_spec.live is False
    assert offline_spec.window.is_live_compatible is False

    future_window = WindowSpec(
        kind=WindowKind.FUTURE,
        length=2,
        causality=WindowCausality.FUTURE,
        offline_only=True,
    )
    with pytest.raises(FeatureContractError, match="live FeatureSpec"):
        FeatureSpec(**_feature_spec_kwargs(window=future_window, live=True))


def test_feature_value_record_requires_available_ts() -> None:
    version = _feature_spec().derive_feature_version()
    with pytest.raises(TypeError):
        FeatureValueRecord(  # type: ignore[call-arg]
            feature_version_id=version.feature_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:32:00+00:00"),
            value=1.0,
        )
    with pytest.raises(FeatureContractError, match="available_ts"):
        FeatureValueRecord(
            feature_version_id=version.feature_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:32:00+00:00"),
            available_ts=None,  # type: ignore[arg-type]
            value=1.0,
        )


def test_feature_version_is_deterministic_and_collision_sensitive() -> None:
    first = _feature_spec(transform_parameters={"lag": 1, "scale": "log"}).derive_feature_version()
    second = _feature_spec(
        transform_parameters={"scale": "log", "lag": 1}
    ).derive_feature_version()
    changed = _feature_spec(
        transform_parameters={"lag": 2, "scale": "log"}
    ).derive_feature_version()

    assert first == second
    assert first.feature_version_id.startswith("fver_")
    assert len(first.content_hash) == 64
    assert changed != first
    assert changed.content_hash != first.content_hash


def test_feature_lineage_requires_matching_version_and_request() -> None:
    spec = _feature_spec()
    version = FeatureVersion.derive(spec)
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
    )

    assert lineage.feature_version == version

    changed_spec = _feature_spec(transform_parameters={"lag": 2})
    with pytest.raises(FeatureContractError, match="contract content"):
        FeatureLineageRecord(
            feature_version=version,
            feature_spec=changed_spec,
            feature_request_id=changed_spec.feature_request_id,
        )


def test_feature_set_spec_is_namespaced_and_not_experiment_feature_set_spec() -> None:
    spec = _feature_spec()
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_contract_fixture",
        feature_set_version="v1",
        features=(spec,),
    )

    assert feature_set.namespace == FEATURE_SET_NAMESPACE
    assert FeatureSetSpec.__module__ == "alpha_system.features.contracts"
    assert FeatureSetSpec is not experiment_feature_sets.FeatureSetSpec
    assert feature_set.feature_versions == (spec.derive_feature_version(),)

    with pytest.raises(FeatureContractError, match="namespace"):
        FeatureSetSpec(
            namespace="experiments",
            feature_set_id="feature_set_contract_fixture",
            feature_set_version="v1",
            features=(spec,),
        )


def test_locked_test_normalization_requires_governance_metadata() -> None:
    with pytest.raises(FeatureContractError, match="contamination metadata"):
        NormalizationSpec(
            normalization_id="zscore",
            fit_partition_policy=FitPartitionPolicy.LOCKED_TEST,
        )

    spec = NormalizationSpec(
        normalization_id="zscore",
        fit_partition_policy=FitPartitionPolicy.LOCKED_TEST,
        contamination_metadata={"study_spec_id": "sspec_fixture", "rationale": "synthetic audit"},
    )
    assert spec.fit_partition_policy is FitPartitionPolicy.LOCKED_TEST


def _feature_spec(
    *,
    transform_parameters: dict[str, object] | None = None,
    **overrides: object,
) -> FeatureSpec:
    kwargs = _feature_spec_kwargs(transform_parameters=transform_parameters, **overrides)
    return FeatureSpec(**kwargs)


def _feature_spec_kwargs(
    *,
    feature_request_id: str | None = None,
    transform_parameters: dict[str, object] | None = None,
    window: WindowSpec | None = None,
    live: bool = True,
) -> dict[str, object]:
    request_id = feature_request_id or _approved_gate_decision().feature_request_id
    return {
        "feature_id": "base_ohlcv_close_return_1m",
        "family": FeatureFamily.BASE_OHLCV,
        "feature_request_id": request_id,
        "inputs": FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("close", "available_ts"),
            dataset_version_ids=("dsv_fixture",),
        ),
        "transform": TransformSpec(
            transform_id="close_return",
            parameters=transform_parameters or {"lag": 1},
        ),
        "window": window
        or WindowSpec(
            kind=WindowKind.ROLLING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        "normalization": NormalizationSpec(normalization_id="identity"),
        "availability_assumptions": {
            "source": "canonical OHLCV available_ts from accepted DatasetVersion"
        },
        "available_ts_derivation_rule": "feature.available_ts = max(input.available_ts)",
        "live": live,
    }


def _approved_gate_decision():
    return evaluate_feature_request_gate(
        _feature_request(FeatureRequestApprovalStatus.APPROVED),
        EmptyRegistryReader(),
    )


def _feature_request(approval_status: FeatureRequestApprovalStatus) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=["synthetic_close_return_1m"],
        formula_sketch={
            "exposure_family": "synthetic_close_return_1m",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic feature inputs are available after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["synthetic_close"],
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
