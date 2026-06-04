from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from alpha_system.data.foundation.batches import (
    CANONICAL_MICRO_SECONDARY_ROOTS,
    CANONICAL_MINI_MAIN_ROOTS,
    CANONICAL_REQUEST_PACING_POLICY_ID,
    HISTORICAL_REQUEST_MANIFEST_CONTRACT,
    MINI_MAIN_BATCH_PULL_PLAN,
    MINI_MAIN_SYMBOL_BATCH_PLAN,
    SymbolBatchPlan,
)
from alpha_system.data.foundation.requests import HistoricalRequestManifest
from alpha_system.data.foundation.sources import DataFoundationValidationError

ROOT = Path(__file__).resolve().parents[3]
MINI_MANIFEST_PATH = ROOT / "templates" / "data" / "synthetic_mini_batch_manifest.json"


def _plan_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "plan_id": "sbp_mini_main_es_nq_rty_v1",
        "mini_main": ["ES", "NQ", "RTY"],
        "micro_secondary": ["MES", "MNQ", "M2K"],
        "max_concurrent_roots": 3,
        "do_not_mix_mini_and_micro_batches": True,
    }
    values.update(overrides)
    return values


def _load_mini_manifest_payload() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(MINI_MANIFEST_PATH.read_text(encoding="utf-8")),
    )


def test_symbol_batch_plan_validates_required_fields_and_no_authorization() -> None:
    plan = SymbolBatchPlan.from_mapping(_plan_values())

    assert plan.plan_id == "sbp_mini_main_es_nq_rty_v1"
    assert plan.mini_main == CANONICAL_MINI_MAIN_ROOTS
    assert plan.micro_secondary == CANONICAL_MICRO_SECONDARY_ROOTS
    assert plan.max_concurrent_roots == 3
    assert plan.do_not_mix_mini_and_micro_batches is True
    assert plan.implies_pull_authorization is False
    assert "pull_authorization" not in plan.to_mapping()

    missing = _plan_values()
    missing.pop("plan_id")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        SymbolBatchPlan.from_mapping(missing)


def test_symbol_batch_plan_enforces_exact_root_sets_and_disjointness() -> None:
    with pytest.raises(DataFoundationValidationError, match="disjoint"):
        SymbolBatchPlan.from_mapping(
            _plan_values(micro_secondary=["RTY", "MNQ", "M2K"])
        )

    with pytest.raises(DataFoundationValidationError, match="mini_main must equal ES/NQ/RTY"):
        SymbolBatchPlan.from_mapping(_plan_values(mini_main=["ES", "NQ"]))

    with pytest.raises(
        DataFoundationValidationError,
        match="micro_secondary must equal MES/MNQ/M2K",
    ):
        SymbolBatchPlan.from_mapping(_plan_values(micro_secondary=["MNQ", "M2K"]))

    with pytest.raises(
        DataFoundationValidationError,
        match="do_not_mix_mini_and_micro_batches must be true",
    ):
        SymbolBatchPlan.from_mapping(
            _plan_values(do_not_mix_mini_and_micro_batches=False)
        )


def test_symbol_batch_plan_enforces_concurrency_bound_and_mix_rejection() -> None:
    plan = MINI_MAIN_SYMBOL_BATCH_PLAN

    assert plan.validate_batch_roots(["ES", "NQ", "RTY"]) == CANONICAL_MINI_MAIN_ROOTS

    with pytest.raises(DataFoundationValidationError, match="must equal 3"):
        SymbolBatchPlan.from_mapping(_plan_values(max_concurrent_roots=4))

    with pytest.raises(DataFoundationValidationError, match="must equal 3"):
        SymbolBatchPlan.from_mapping(_plan_values(max_concurrent_roots=2))

    with pytest.raises(DataFoundationValidationError, match="mixes mini and micro roots"):
        plan.validate_batch_roots(["ES", "MNQ"], batch_name="mixed_negative_case")

    with pytest.raises(DataFoundationValidationError, match="duplicate roots"):
        plan.validate_batch_roots(["ES", "ES"], batch_name="duplicate_negative_case")


def test_mini_main_batch_pull_plan_defines_primary_and_labeled_secondary_panels() -> None:
    primary = cast(Mapping[str, object], MINI_MAIN_BATCH_PULL_PLAN["primary_common_panel"])

    assert primary["roots"] == CANONICAL_MINI_MAIN_ROOTS
    assert primary["start_date"] == "2018-01-01"
    assert primary["end_date"] == "present_as_of_run"
    assert primary["bar_size"] == "1 min"
    assert primary["what_to_show"] == "TRADES"
    assert primary["session_views"] == ("ETH_canonical", "RTH_derived")
    assert primary["manifest_contract"] == HISTORICAL_REQUEST_MANIFEST_CONTRACT
    assert primary["pacing_policy_id"] == CANONICAL_REQUEST_PACING_POLICY_ID

    optional_panels = cast(
        tuple[Mapping[str, object], ...],
        MINI_MAIN_BATCH_PULL_PLAN["optional_secondary_panels"],
    )
    panels_by_id = {cast(str, panel["panel_id"]): panel for panel in optional_panels}

    assert set(panels_by_id) == {
        "mini_optional_es_nq_long_qa_panel",
        "mini_optional_rty_transition_qa_panel",
        "mini_optional_contract_truth_diagnostic_panel",
    }
    assert panels_by_id["mini_optional_es_nq_long_qa_panel"]["start_date"] == "2015-01-01"
    assert panels_by_id["mini_optional_rty_transition_qa_panel"]["start_date"] == (
        "2017-07-10"
    )
    assert panels_by_id["mini_optional_rty_transition_qa_panel"]["end_date"] == (
        "2017-12-31"
    )
    assert panels_by_id["mini_optional_contract_truth_diagnostic_panel"]["start_date"] == (
        "rolling_available_expired_window"
    )
    assert panels_by_id["mini_optional_contract_truth_diagnostic_panel"]["end_date"] == (
        "availability_discovered_not_assumed"
    )

    micro_roots = set(CANONICAL_MICRO_SECONDARY_ROOTS)
    for panel in optional_panels:
        roots = set(cast(tuple[str, ...], panel["roots"]))
        assert roots.isdisjoint(micro_roots)
        assert cast(str, panel["panel_role"]).startswith("optional_secondary")
        assert panel["qa_or_diagnostic_label"]
        assert panel["merge_into_primary_common_panel"] is False
        assert panel["manifest_contract"] == HISTORICAL_REQUEST_MANIFEST_CONTRACT
        assert panel["pacing_policy_id"] == CANONICAL_REQUEST_PACING_POLICY_ID

    assert MINI_MAIN_BATCH_PULL_PLAN["pull_authorization"] is False
    assert MINI_MAIN_BATCH_PULL_PLAN["external_provider_call"] is False
    assert MINI_MAIN_BATCH_PULL_PLAN["data_exists_claim"] is False


def test_synthetic_mini_batch_manifest_is_valid_mini_only_and_no_authorization() -> None:
    payload = _load_mini_manifest_payload()
    expected_coverage = cast(Mapping[str, object], payload["expected_coverage"])

    assert expected_coverage["synthetic"] is True
    assert expected_coverage["sample_manifest"] is True
    assert expected_coverage["coverage_status"] == "planned_only_not_requested"
    assert expected_coverage["roots"] == list(CANONICAL_MINI_MAIN_ROOTS)
    assert expected_coverage["micro_roots_included"] == []
    assert expected_coverage["mini_micro_mixed"] is False
    assert expected_coverage["real_coverage_claim"] is False
    assert expected_coverage["authorization_claim"] is False
    assert expected_coverage["pull_authorization"] is False
    assert expected_coverage["data_exists_claim"] is False

    manifest = HistoricalRequestManifest.from_mapping(payload)

    assert manifest.manifest_hash == payload["manifest_hash"]
    assert MINI_MAIN_SYMBOL_BATCH_PLAN.validate_manifest_roots(manifest) == (
        CANONICAL_MINI_MAIN_ROOTS
    )
    assert {request.symbol_root for request in manifest.request_specs} == set(
        CANONICAL_MINI_MAIN_ROOTS
    )
    assert all(request.bar_size == "1 min" for request in manifest.request_specs)
    assert all(request.what_to_show == "TRADES" for request in manifest.request_specs)


def test_manifest_root_validation_rejects_mini_micro_mix() -> None:
    payload = _load_mini_manifest_payload()
    mixed_request = dict(cast(list[Mapping[str, object]], payload["request_specs"])[0])
    mixed_request["request_spec_id"] = "hrs_synthetic_negative_mnq_mix_v1"
    mixed_request["symbol_root"] = "MNQ"
    payload["request_specs"] = list(payload["request_specs"]) + [mixed_request]

    with pytest.raises(DataFoundationValidationError, match="mixes mini and micro roots"):
        MINI_MAIN_SYMBOL_BATCH_PLAN.validate_manifest_roots(payload)
