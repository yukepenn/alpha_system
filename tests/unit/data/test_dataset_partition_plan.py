from __future__ import annotations

from dataclasses import fields

import pytest

from alpha_system.data.foundation import (
    REQUIRED_DATASET_PARTITION_PLAN_FIELDS as EXPORTED_PARTITION_PLAN_FIELDS,
)
from alpha_system.data.foundation.datasets import (
    REQUIRED_DATASET_PARTITION_PLAN_FIELDS,
    DatasetPartitionPlan,
    require_governance_metadata_for_locked_partition_use,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _canonical_values(**overrides: object) -> dict[str, object]:
    values = dict(DatasetPartitionPlan.canonical().to_mapping())
    values.update(overrides)
    return values


def _partition_values(field_name: str, **overrides: object) -> dict[str, object]:
    partition = dict(DatasetPartitionPlan.canonical().to_mapping()[field_name])
    partition.update(overrides)
    return partition


def test_partition_plan_exposes_exact_required_fields_and_canonical_dates() -> None:
    plan = DatasetPartitionPlan.canonical()

    assert tuple(field.name for field in fields(DatasetPartitionPlan)) == (
        REQUIRED_DATASET_PARTITION_PLAN_FIELDS
    )
    assert EXPORTED_PARTITION_PLAN_FIELDS == REQUIRED_DATASET_PARTITION_PLAN_FIELDS
    assert set(plan.to_mapping()) == set(REQUIRED_DATASET_PARTITION_PLAN_FIELDS)
    assert plan.development_partition == {
        "partition_id": "development_partition",
        "start_date": "2018-01-01",
        "end_date": "2022-12-31",
        "role": "development_partition",
    }
    assert plan.validation_partition["start_date"] == "2023-01-01"
    assert plan.validation_partition["end_date"] == "2024-12-31"
    assert plan.locked_test_candidate["start_date"] == "2025-01-01"
    assert plan.locked_test_candidate["end_date"] == "as_of_run"
    assert plan.latest_shadow_candidate is None
    assert plan.contamination_metadata_rules["implies_research_approval"] is False


def test_partition_plan_from_mapping_fails_closed_on_missing_extra_or_blank_id() -> None:
    values = _canonical_values()

    missing = dict(values)
    missing.pop("locked_test_candidate")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        DatasetPartitionPlan.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        DatasetPartitionPlan.from_mapping({**values, "dataset_version_id": "dsv_loose"})

    with pytest.raises(DataFoundationValidationError, match="non-empty string"):
        DatasetPartitionPlan.from_mapping({**values, "plan_id": "   "})


def test_partition_plan_rejects_malformed_or_noncanonical_partition_bounds() -> None:
    with pytest.raises(DataFoundationValidationError, match="ISO-8601 date"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                development_partition=_partition_values(
                    "development_partition",
                    start_date="2018/01/01",
                )
            )
        )

    with pytest.raises(DataFoundationValidationError, match="start_date"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                validation_partition=_partition_values(
                    "validation_partition",
                    start_date="2022-12-31",
                )
            )
        )

    with pytest.raises(DataFoundationValidationError, match="end_date"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                locked_test_candidate=_partition_values(
                    "locked_test_candidate",
                    end_date="2025-12-31",
                )
            )
        )


def test_partition_plan_rejects_loose_partition_fields_and_bad_latest_shadow() -> None:
    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                development_partition={
                    **_partition_values("development_partition"),
                    "notes": "loose",
                }
            )
        )

    with pytest.raises(DataFoundationValidationError, match="end_date"):
        DatasetPartitionPlan.canonical(
            latest_shadow_candidate={
                "partition_id": "latest_shadow_candidate",
                "start_date": "2026-01-02",
                "end_date": "2026-01-01",
                "role": "latest_shadow_candidate",
                "rolling": True,
                "optional": True,
            }
        )

    plan = DatasetPartitionPlan.canonical(
        latest_shadow_candidate={
            "partition_id": "latest_shadow_candidate",
            "start_date": "rolling_recent",
            "end_date": "as_of_run",
            "role": "latest_shadow_candidate",
            "rolling": True,
            "optional": True,
        }
    )
    assert plan.latest_shadow_candidate == {
        "partition_id": "latest_shadow_candidate",
        "start_date": "rolling_recent",
        "end_date": "as_of_run",
        "role": "latest_shadow_candidate",
        "rolling": True,
        "optional": True,
    }


def test_partition_plan_rejects_non_enforcing_contamination_rules() -> None:
    rules = dict(DatasetPartitionPlan.canonical().contamination_metadata_rules)

    with pytest.raises(DataFoundationValidationError, match="coverage inspection"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                contamination_metadata_rules={
                    **rules,
                    "data_qa_coverage_inspection_allowed": False,
                }
            )
        )

    with pytest.raises(DataFoundationValidationError, match="Governance contamination"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                contamination_metadata_rules={
                    **rules,
                    "locked_partition_use_requires_governance_metadata": False,
                }
            )
        )

    with pytest.raises(DataFoundationValidationError, match="research approval"):
        DatasetPartitionPlan.from_mapping(
            _canonical_values(
                contamination_metadata_rules={
                    **rules,
                    "implies_research_approval": True,
                }
            )
        )


def test_data_qa_coverage_is_allowed_across_all_partitions() -> None:
    plan = DatasetPartitionPlan.canonical(
        latest_shadow_candidate={
            "partition_id": "latest_shadow_candidate",
            "start_date": "rolling_recent",
            "end_date": "as_of_run",
            "role": "latest_shadow_candidate",
            "rolling": True,
            "optional": True,
        }
    )

    for partition_id in plan.partition_ids:
        assert plan.permits_coverage_qa(partition_id) is True
        assert (
            require_governance_metadata_for_locked_partition_use(
                partition_id=partition_id,
                purpose="data_qa_coverage",
                plan=plan,
            )
            is True
        )


def test_locked_partition_use_without_governance_metadata_is_rejected() -> None:
    plan = DatasetPartitionPlan.canonical()

    assert (
        require_governance_metadata_for_locked_partition_use(
            partition_id="development_partition",
            purpose="alpha_research",
            plan=plan,
        )
        is True
    )

    with pytest.raises(DataFoundationValidationError, match="Governance contamination"):
        require_governance_metadata_for_locked_partition_use(
            partition_id="locked_test_candidate",
            purpose="alpha_research",
            plan=plan,
        )

    with pytest.raises(DataFoundationValidationError, match="Governance contamination"):
        require_governance_metadata_for_locked_partition_use(
            partition_id="locked_test_candidate",
            purpose="alpha_research",
            governance_metadata={},
            plan=plan,
        )
