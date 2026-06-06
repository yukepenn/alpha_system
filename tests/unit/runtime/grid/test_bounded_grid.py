from __future__ import annotations

import pytest

from alpha_system.runtime.grid import (
    BoundedGridContractError,
    BoundedGridOutcome,
    BoundedGridRunRecord,
    BoundedGridSpec,
    ParameterAxis,
    VariantBudget,
    guard_bounded_grid,
    validate_bounded_grid_request,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"


def test_spec_is_immutable_hashable_and_records_realized_count() -> None:
    spec = _spec()

    assert hash(spec)
    assert spec.realized_variant_count == 6
    assert spec.variant_budget.effective_max_combinations == 6
    assert spec.partition_scope_ids == ("development", "validation")
    assert spec.to_dict()["promotion_basis_allowed"] is False

    with pytest.raises(BoundedGridContractError, match="VariantBudget"):
        BoundedGridSpec(
            binding_ref=_binding(),
            parameter_axes={"threshold": ["0.5"]},
            variant_budget=None,
        )


def test_budget_exceeded_fails_closed_with_visible_record() -> None:
    result = validate_bounded_grid_request(
        run_id="run_grid_budget_exceeded",
        binding_ref=_binding(),
        parameter_axes={"threshold": ["0.5", "0.6"], "direction_policy": ["long", "short"]},
        variant_budget=VariantBudget(max_variants=3),
    )

    assert result.spec is None
    assert result.rejected is True
    assert result.record.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
    assert result.record.realized_variant_count == 4
    assert _reason_codes(result.record) == {"variant_budget_exceeded"}
    assert result.record.to_dict()["variant_budget"]["limit_primitive"].endswith(
        "CombinationLimit"
    )


def test_guard_refuses_locked_test_selection_with_recorded_reason() -> None:
    spec = _spec(partition_scope=["development", "locked_test_candidate"])

    record = guard_bounded_grid(spec, run_id="run_grid_locked_selection")

    assert record.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
    assert record.realized_variant_count == 6
    assert "locked_test_selection" in _reason_codes(record)
    assert "locked_partition_governance_metadata_missing" in _reason_codes(record)
    assert record.to_dict()["value_free"] is True


def test_locked_partition_non_selection_requires_contamination_metadata() -> None:
    no_metadata = _spec(
        partition_scope=["locked_test_candidate"],
        partition_purpose="descriptive_locked_partition_audit",
    )

    blocked = guard_bounded_grid(no_metadata, run_id="run_grid_locked_no_metadata")

    assert blocked.guard_outcome is BoundedGridOutcome.GUARD_REJECTED
    assert _reason_codes(blocked) == {"locked_partition_governance_metadata_missing"}

    with_metadata = _spec(
        partition_scope=["locked_test_candidate"],
        partition_purpose="descriptive_locked_partition_audit",
        governance_metadata={"contamination_review_ref": "gov_review_synthetic_unit"},
    )

    accepted = guard_bounded_grid(with_metadata, run_id="run_grid_locked_with_metadata")

    assert accepted.guard_outcome is BoundedGridOutcome.GUARD_PASSED
    assert accepted.rejection_reasons == ()


def test_guard_consumes_overfit_controls_and_keeps_repeated_run_refs() -> None:
    spec = _spec()

    first = guard_bounded_grid(spec, run_id="run_grid_repeat", repeated_run_index=1)
    second = guard_bounded_grid(
        spec,
        run_id="run_grid_repeat",
        repeated_run_index=2,
        previous_run_record_ids=(first.record_id,),
    )

    assert isinstance(first, BoundedGridRunRecord)
    assert first.guard_outcome is BoundedGridOutcome.GUARD_PASSED
    assert first.overfit_warning_count >= 1
    assert "combination_count" in first.overfit_control_keys
    assert first.record_id != second.record_id
    assert second.previous_run_record_ids == (first.record_id,)


def test_empty_axis_is_unbounded_grid_rejection() -> None:
    result = validate_bounded_grid_request(
        run_id="run_grid_empty_axis",
        binding_ref=_binding(),
        parameter_axes=(),
        variant_budget=VariantBudget(max_variants=3),
    )

    assert result.rejected is True
    assert result.record.realized_variant_count == 0
    assert _reason_codes(result.record) == {"unbounded_grid"}


def test_invalid_partition_scope_returns_visible_rejection() -> None:
    result = validate_bounded_grid_request(
        run_id="run_grid_bad_partition",
        binding_ref=_binding(),
        parameter_axes={"threshold": ["0.5"]},
        variant_budget=VariantBudget(max_variants=1),
        partition_scope=[""],
    )

    assert result.rejected is True
    assert _reason_codes(result.record) == {"invalid_partition_scope"}


def _spec(
    *,
    partition_scope: list[str] | None = None,
    partition_purpose: str = "grid_selection",
    governance_metadata: dict[str, object] | None = None,
) -> BoundedGridSpec:
    return BoundedGridSpec(
        binding_ref=_binding(),
        parameter_axes=(
            ParameterAxis("threshold", ["0.5", "0.6", "0.7"]),
            ParameterAxis("direction_policy", ["long_flat", "short_flat"]),
        ),
        variant_budget=VariantBudget(max_variants=8, max_grid_points=6),
        partition_scope=partition_scope,
        partition_purpose=partition_purpose,
        governance_metadata=governance_metadata,
    )


def _binding() -> dict[str, str]:
    return {
        "alpha_spec_ref": ALPHA_SPEC_REF,
        "study_spec_ref": STUDY_SPEC_REF,
        "study_run_spec_id": "srun_0123456789abcdef01234567",
        "study_run_spec_content_hash": "a" * 64,
        "signal_probe_spec_id": "sprobe_0123456789abcdef012345",
        "signal_probe_spec_content_hash": "b" * 64,
    }


def _reason_codes(record: BoundedGridRunRecord) -> set[str]:
    return {reason.code for reason in record.rejection_reasons}
