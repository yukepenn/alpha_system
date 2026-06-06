from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from typing import Any

import pytest

import alpha_system.runtime.contracts as runtime_contracts
from alpha_system.governance.alpha_spec import (
    IMPLEMENTATION_ALLOWED_STATE,
    AlphaSpec,
    generate_alpha_spec_id,
)
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.governance.study_spec import (
    DIAGNOSTICS_ALLOWED_STATE,
    StudySpec,
    generate_study_spec_id,
)
from alpha_system.runtime.contracts.plan import RuntimePlan
from alpha_system.runtime.contracts.run_spec import (
    RuntimeContractError,
    RuntimeLifecycleState,
    RuntimeRequest,
    StudyRunSpec,
)
from alpha_system.runtime.input_resolver import RuntimeInputPack

FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
DATASET_VERSION_ID = "dsv_synthetic_feature_label_fixture_v1"
DATASET_SCOPE = {
    "instrument_universe": "SYNTH_US_EQUITY_LARGE_CAP fixture universe only",
    "source": "tiny synthetic governance fixture metadata, not real market data",
    "time_range": "2018-01-01 through as_of_run synthetic timestamps",
}
DEVELOPMENT_SCOPE = {
    "partition_id": "development",
    "start": "2018-01-01",
    "end": "2022-12-31",
}
SESSION_SCOPE = {"session": "rth_and_eth"}


def test_contract_package_surface_exposes_rt_p04_symbols() -> None:
    assert runtime_contracts.RuntimeRequest is RuntimeRequest
    assert runtime_contracts.StudyRunSpec is StudyRunSpec
    assert runtime_contracts.RuntimePlan is RuntimePlan


def test_runtime_request_is_immutable_hashable_and_deterministic() -> None:
    request = _runtime_request()
    same_request = _runtime_request()

    assert request.lifecycle_state is RuntimeLifecycleState.RUNTIME_REQUESTED
    assert request.content_hash == same_request.content_hash
    assert request.request_id == same_request.request_id
    assert hash(request)
    with pytest.raises(FrozenInstanceError):
        request.alpha_spec_ref = "aspec_" + "0" * 24  # type: ignore[misc]


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"alpha_spec": None}, "missing_alpha_spec"),
        ({"study_spec": None}, "missing_study_spec"),
        ({"study_input_pack": None}, "missing_study_input_pack"),
        ({"target_dataset_version_id": None}, "missing_target_dataset_version_id"),
        ({"runtime_input_pack": None}, "missing_runtime_input_pack"),
    ],
)
def test_runtime_request_missing_required_reference_fails_closed(
    overrides: dict[str, object],
    expected_code: str,
) -> None:
    with pytest.raises(RuntimeContractError) as exc_info:
        _runtime_request(**overrides)

    assert expected_code in _reason_codes(exc_info.value.reasons)


def test_runtime_request_requires_approved_governance_states() -> None:
    with pytest.raises(RuntimeContractError) as exc_info:
        _runtime_request(study_spec_state="IMPLEMENTED")

    assert "study_spec_not_approved" in _reason_codes(exc_info.value.reasons)


def test_runtime_request_rejects_runtime_input_pack_mismatch() -> None:
    alpha_spec = _alpha_spec()
    study_spec = _study_spec(alpha_spec.alpha_spec_id)
    pack = _study_input_pack(alpha_spec.alpha_spec_id)
    runtime_pack = _runtime_input_pack(
        alpha_spec=alpha_spec,
        study_spec=study_spec,
        study_input_pack=pack,
        dataset_version_id="dsv_other_fixture_v1",
    )

    with pytest.raises(RuntimeContractError) as exc_info:
        RuntimeRequest(
            alpha_spec=alpha_spec,
            study_spec=study_spec,
            study_input_pack=pack,
            target_dataset_version_id=DATASET_VERSION_ID,
            runtime_input_pack=runtime_pack,
        )

    assert "runtime_input_dataset_version_mismatch" in _reason_codes(exc_info.value.reasons)


def test_study_run_spec_binds_validated_plan_without_execution_outcome() -> None:
    request = _runtime_request()
    plan = RuntimePlan(
        runtime_request=request,
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
    )

    run_spec = StudyRunSpec(runtime_request=request, runtime_plan=plan)

    assert run_spec.lifecycle_state is RuntimeLifecycleState.PLAN_VALIDATED
    assert hash(run_spec)
    payload = run_spec.to_dict()
    assert payload["execution_outcome"] is None
    assert payload["runtime_plan"]["status"] == "PLAN_VALIDATED"


def test_study_run_spec_rejects_unvalidated_plan() -> None:
    request = _runtime_request()

    with pytest.raises(RuntimeContractError) as exc_info:
        StudyRunSpec(runtime_request=request, runtime_plan=object())  # type: ignore[arg-type]

    assert "runtime_plan_not_validated" in _reason_codes(exc_info.value.reasons)


def _runtime_request(**overrides: object) -> RuntimeRequest:
    alpha_spec = _alpha_spec()
    study_spec = _study_spec(alpha_spec.alpha_spec_id)
    pack = _study_input_pack(alpha_spec.alpha_spec_id)
    runtime_pack = _runtime_input_pack(
        alpha_spec=alpha_spec,
        study_spec=study_spec,
        study_input_pack=pack,
    )
    values: dict[str, object] = {
        "alpha_spec": alpha_spec,
        "study_spec": study_spec,
        "study_input_pack": pack,
        "target_dataset_version_id": DATASET_VERSION_ID,
        "runtime_input_pack": runtime_pack,
        "alpha_spec_state": IMPLEMENTATION_ALLOWED_STATE,
        "study_spec_state": DIAGNOSTICS_ALLOWED_STATE,
    }
    values.update(overrides)
    return RuntimeRequest(**values)  # type: ignore[arg-type]


def _alpha_spec() -> AlphaSpec:
    payload: dict[str, Any] = {
        "hypothesis_id": "hyp_" + "a" * 24,
        "target_instruments": ["ES synthetic fixture"],
        "data_assumptions": {"dataset": "accepted DatasetVersion fixture metadata only"},
        "factor_inputs": ["registered feature request fixture"],
        "label_references": [LABEL_SPEC_REF],
        "exclusion_rules": ["Exclude any raw provider or live trading behavior."],
        "timestamp_assumptions": {"availability": "available_ts precedes feature use."},
        "cost_assumptions": {"stress": "double_cost profile must be declared."},
        "expected_failure_modes": ["Synthetic plan may fail closed before execution."],
        "promotion_criteria": ["No promotion claim is made by this runtime request."],
        "created_by": "runtime-contract-test",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }
    payload["alpha_spec_id"] = generate_alpha_spec_id(payload)
    return AlphaSpec.from_mapping(payload)


def _study_spec(alpha_spec_id: str) -> StudySpec:
    payload: dict[str, Any] = {
        "alpha_spec_id": alpha_spec_id,
        "label_spec_id": LABEL_SPEC_REF,
        "dataset_scope": DATASET_SCOPE,
        "split_protocol": {"method": "campaign partitions are fixed by RT-P04."},
        "metrics": ["information_coefficient_fixture"],
        "cost_assumptions": {"profile": "base plus double_cost stress required for probes."},
        "variant_budget": 4,
        "locked_test_policy": {"policy": "locked_test_candidate requires contamination metadata."},
        "negative_controls": ["synthetic no-lookahead guard"],
        "stopping_rules": ["stop before execution when contract validation fails"],
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return StudySpec.from_mapping(payload)


def _study_input_pack(alpha_spec_id: str) -> StudyInputPack:
    return StudyInputPack(
        feature_request_ids=[FEATURE_REQUEST_REF],
        label_spec_ids=[LABEL_SPEC_REF],
        alpha_spec_id=alpha_spec_id,
        dataset_scope=DATASET_SCOPE,
    )


def _runtime_input_pack(
    *,
    alpha_spec: AlphaSpec,
    study_spec: StudySpec,
    study_input_pack: StudyInputPack,
    dataset_version_id: str = DATASET_VERSION_ID,
    partition_scope: dict[str, str] | None = None,
) -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=alpha_spec.alpha_spec_id,
        study_spec_ref=study_spec.study_spec_id,
        study_input_pack=study_input_pack.to_dict(),
        dataset_version_id=dataset_version_id,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="databento",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(),
        label_packs=(),
        dataset_scope=DATASET_SCOPE,
        partition_scope=partition_scope or DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        governance_metadata={},
    )


def _reason_codes(reasons: tuple[object, ...]) -> set[str]:
    return {reason.code for reason in reasons}  # type: ignore[attr-defined]
