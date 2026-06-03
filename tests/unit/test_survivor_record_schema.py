from __future__ import annotations

import pytest

from alpha_system.experiments.survivors import (
    SURVIVOR_REQUIRED_FIELDS,
    SurvivorRecord,
    SurvivorSchemaError,
)


def test_survivor_record_schema_contains_required_fields() -> None:
    assert SurvivorRecord.required_fields() == SURVIVOR_REQUIRED_FIELDS


def test_survivor_record_accepts_spec_field_aliases() -> None:
    record = SurvivorRecord.from_mapping(
        {
            "candidate id": "candidate:aliases",
            "source run id": "grid_source",
            "factor versions": {"fixture_factor": "v1"},
            "label versions": {},
            "strategy version": "strategy:v1",
            "baseline management config": {
                "management_id": "management:baseline",
                "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
            },
            "baseline portfolio config": {"portfolio_id": "portfolio:baseline"},
            "source grid config hash": "hash-alias",
            "reason for survivor eligibility": "passed diagnostics and baseline review",
            "warnings": ["review sample size"],
            "review status": "PASS",
            "allowed management grid scope": {
                "management_parameters": ["management.fixed_stop.stop_pct"],
                "max_combinations": 1,
            },
        }
    )

    assert record.candidate_id == "candidate:aliases"
    assert record.label_versions == {}
    assert record.warnings == ("review sample size",)


def test_survivor_record_requires_review_status() -> None:
    payload = {
        "candidate_id": "candidate:missing-review",
        "source_run_id": "grid_source",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {},
        "strategy_version": "strategy:v1",
        "baseline_management_config": {"fixed_stop": {"enabled": True, "stop_pct": "0.02"}},
        "baseline_portfolio_config": {"portfolio_id": "portfolio:baseline"},
        "source_grid_config_hash": "hash-missing-review",
        "survivor_eligibility_reason": "passed diagnostics and baseline review",
        "warnings": [],
        "allowed_management_grid_scope": {
            "management_parameters": ["management.fixed_stop.stop_pct"],
            "max_combinations": 1,
        },
    }

    with pytest.raises(SurvivorSchemaError, match="review_status"):
        SurvivorRecord.from_mapping(payload)
