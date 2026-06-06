from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from alpha_system.experiments.limits import CombinationLimit
from alpha_system.governance.alpha_spec import AlphaSpec, generate_alpha_spec_id
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.governance.study_spec import StudySpec, generate_study_spec_id
from alpha_system.runtime.contracts.plan import RuntimePlan, validate_runtime_plan
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState, RuntimeRequest
from alpha_system.runtime.entry_contract import RuntimeEntryStatus
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
LOCKED_SCOPE = {
    "partition_id": "locked_test_candidate",
    "start": "2025-01-01",
    "end": "as_of_run",
}
SESSION_SCOPE = {"session": "rth_and_eth"}


def test_signal_probe_plan_reaches_plan_validated_with_budget_and_double_cost() -> None:
    request = _runtime_request()

    result = validate_runtime_plan(
        runtime_request=request,
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        include_signal_probe=True,
        variant_grid_ref="bounded_probe_grid_fixture",
        variant_budget=CombinationLimit(4),
        cost_stress_profiles=("base", "double_cost"),
    )

    assert result.status is RuntimeLifecycleState.PLAN_VALIDATED
    assert result.validated
    assert result.plan is not None
    assert result.plan.status is RuntimeLifecycleState.PLAN_VALIDATED
    assert hash(result.plan)
    assert result.plan.to_dict()["execution_outcome"] is None


def test_runtime_plan_constructor_produces_validated_plan_object() -> None:
    request = _runtime_request()

    plan = RuntimePlan(
        runtime_request=request,
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
    )

    assert plan.status is RuntimeLifecycleState.PLAN_VALIDATED
    assert plan.request_content_hash == request.content_hash


def test_unbounded_plan_is_rejected() -> None:
    result = validate_runtime_plan(
        runtime_request=_runtime_request(),
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        bounded=False,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "unbounded_runtime_plan" in _reason_codes(result.reasons)


def test_partition_scope_must_match_campaign_partitions() -> None:
    bad_scope = {
        "partition_id": "development",
        "start": "2018-01-01",
        "end": "2023-01-01",
    }

    result = validate_runtime_plan(
        runtime_request=_runtime_request(partition_scope=bad_scope),
        partition_scope=bad_scope,
        session_scope=SESSION_SCOPE,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "partition_scope_not_campaign_bound" in _reason_codes(result.reasons)


def test_probe_plan_requires_variant_grid_budget_and_double_cost_stress() -> None:
    missing_grid = validate_runtime_plan(
        runtime_request=_runtime_request(),
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        include_signal_probe=True,
        variant_budget=CombinationLimit(4),
        cost_stress_profiles=("double_cost",),
    )
    missing_budget = validate_runtime_plan(
        runtime_request=_runtime_request(),
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        include_signal_probe=True,
        variant_grid_ref="bounded_probe_grid_fixture",
        cost_stress_profiles=("double_cost",),
    )
    missing_cost = validate_runtime_plan(
        runtime_request=_runtime_request(),
        partition_scope=DEVELOPMENT_SCOPE,
        session_scope=SESSION_SCOPE,
        include_signal_probe=True,
        variant_grid_ref="bounded_probe_grid_fixture",
        variant_budget=CombinationLimit(4),
        cost_stress_profiles=("base",),
    )

    assert "missing_variant_grid_ref" in _reason_codes(missing_grid.reasons)
    assert "missing_variant_budget" in _reason_codes(missing_budget.reasons)
    assert "missing_double_cost_stress" in _reason_codes(missing_cost.reasons)


def test_locked_partition_requires_contamination_metadata() -> None:
    result = validate_runtime_plan(
        runtime_request=_runtime_request(partition_scope=LOCKED_SCOPE),
        partition_scope=LOCKED_SCOPE,
        session_scope=SESSION_SCOPE,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE
    assert result.inconclusive
    assert "locked_partition_governance_metadata_missing" in _reason_codes(result.reasons)


def test_locked_partition_with_metadata_can_validate_but_selection_is_rejected() -> None:
    metadata = {"contamination_review_id": "synthetic_contamination_review_rt_p04"}
    valid = validate_runtime_plan(
        runtime_request=_runtime_request(
            partition_scope=LOCKED_SCOPE, governance_metadata=metadata
        ),
        partition_scope=LOCKED_SCOPE,
        session_scope=SESSION_SCOPE,
        governance_metadata=metadata,
    )
    selection = validate_runtime_plan(
        runtime_request=_runtime_request(
            partition_scope=LOCKED_SCOPE, governance_metadata=metadata
        ),
        partition_scope=LOCKED_SCOPE,
        session_scope=SESSION_SCOPE,
        governance_metadata=metadata,
        partition_purpose="locked_test_selection",
    )

    assert valid.status is RuntimeLifecycleState.PLAN_VALIDATED
    assert selection.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "locked_test_selection_forbidden" in _reason_codes(selection.reasons)


def _runtime_request(
    *,
    partition_scope: dict[str, str] | None = None,
    governance_metadata: dict[str, str] | None = None,
) -> RuntimeRequest:
    alpha_spec = _alpha_spec()
    study_spec = _study_spec(alpha_spec.alpha_spec_id)
    pack = _study_input_pack(alpha_spec.alpha_spec_id)
    runtime_pack = _runtime_input_pack(
        alpha_spec=alpha_spec,
        study_spec=study_spec,
        study_input_pack=pack,
        partition_scope=partition_scope or DEVELOPMENT_SCOPE,
        governance_metadata=governance_metadata or {},
    )
    return RuntimeRequest(
        alpha_spec=alpha_spec,
        study_spec=study_spec,
        study_input_pack=pack,
        target_dataset_version_id=DATASET_VERSION_ID,
        runtime_input_pack=runtime_pack,
    )


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
    partition_scope: dict[str, str],
    governance_metadata: dict[str, str],
) -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=alpha_spec.alpha_spec_id,
        study_spec_ref=study_spec.study_spec_id,
        study_input_pack=study_input_pack.to_dict(),
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="databento",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(),
        label_packs=(),
        dataset_scope=DATASET_SCOPE,
        partition_scope=partition_scope,
        session_scope=SESSION_SCOPE,
        governance_metadata=governance_metadata,
    )


def _reason_codes(reasons: tuple[object, ...]) -> set[str]:
    return {reason.code for reason in reasons}  # type: ignore[attr-defined]
