from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pytest

from alpha_system.data.foundation.batches import (
    CANONICAL_MAX_CONCURRENT_ROOTS,
    CANONICAL_MICRO_BATCH_POLICY_ID,
    CANONICAL_MICRO_BATCH_START_DATE,
    CANONICAL_MICRO_SECONDARY_ROOTS,
    CANONICAL_MINI_MICRO_PARITY_TARGETS,
    DATA_P05_INSTRUMENT_ECONOMICS_REFERENCE,
    DATA_P10_SEPARATION_CONTRACT_REFERENCE,
    INSTRUMENT_MASTER_RECORD_CONTRACT,
    MICRO_BATCH_PLAN,
    MICRO_BATCH_POLICY,
    MICRO_BATCH_START_DATE_STATUS,
    MINI_MAIN_SYMBOL_BATCH_PLAN,
    REQUIRED_MICRO_BATCH_POLICY_FIELDS,
    MicroBatchPolicy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _policy_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "batch_id": CANONICAL_MICRO_BATCH_POLICY_ID,
        "symbols": ["MES", "MNQ", "M2K"],
        "start_date": CANONICAL_MICRO_BATCH_START_DATE,
        "separate_batch": True,
        "parity_check_targets": [
            {"mini_root": "ES", "micro_root": "MES"},
            {"mini_root": "NQ", "micro_root": "MNQ"},
            {"mini_root": "RTY", "micro_root": "M2K"},
        ],
    }
    values.update(overrides)
    return values


def test_micro_batch_policy_validates_required_fields_and_no_authorization() -> None:
    policy = MicroBatchPolicy.from_mapping(_policy_values())

    assert set(REQUIRED_MICRO_BATCH_POLICY_FIELDS) == {
        "batch_id",
        "symbols",
        "start_date",
        "separate_batch",
        "parity_check_targets",
    }
    assert policy.batch_id == CANONICAL_MICRO_BATCH_POLICY_ID
    assert policy.symbols == CANONICAL_MICRO_SECONDARY_ROOTS
    assert policy.start_date == "2020-01-01"
    assert policy.separate_batch is True
    assert policy.parity_check_targets == CANONICAL_MINI_MICRO_PARITY_TARGETS
    assert policy.implies_pull_authorization is False
    assert policy.secondary_path is True
    assert policy.instrument_economics_contract == INSTRUMENT_MASTER_RECORD_CONTRACT
    assert policy.instrument_economics_roots == CANONICAL_MICRO_SECONDARY_ROOTS
    assert "pull_authorization" not in policy.to_mapping()

    missing = _policy_values()
    missing.pop("batch_id")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        MicroBatchPolicy.from_mapping(missing)


def test_micro_batch_policy_enforces_exact_micro_roots_and_separation_flag() -> None:
    with pytest.raises(DataFoundationValidationError, match="disjoint from mini roots"):
        MicroBatchPolicy.from_mapping(_policy_values(symbols=["MES", "MNQ", "ES"]))

    with pytest.raises(DataFoundationValidationError, match="symbols must equal MES/MNQ/M2K"):
        MicroBatchPolicy.from_mapping(_policy_values(symbols=["MES", "MNQ"]))

    with pytest.raises(DataFoundationValidationError, match="duplicate roots"):
        MicroBatchPolicy.from_mapping(_policy_values(symbols=["MES", "MES", "M2K"]))

    with pytest.raises(DataFoundationValidationError, match="separate_batch must be true"):
        MicroBatchPolicy.from_mapping(_policy_values(separate_batch=False))


def test_micro_batch_policy_validates_micro_batch_roots_without_mini_mixing() -> None:
    policy = MICRO_BATCH_POLICY

    assert policy.validate_batch_roots(["MES", "MNQ", "M2K"]) == (
        CANONICAL_MICRO_SECONDARY_ROOTS
    )

    with pytest.raises(DataFoundationValidationError, match="must not include mini roots"):
        policy.validate_batch_roots(["MES", "NQ", "M2K"])

    with pytest.raises(
        DataFoundationValidationError,
        match="micro batch must equal MES/MNQ/M2K",
    ):
        policy.validate_batch_roots(["MES", "MNQ"])

    manifest_payload = {
        "request_specs": [
            {"symbol_root": "MES"},
            {"symbol_root": "MNQ"},
            {"symbol_root": "M2K"},
        ]
    }
    assert policy.validate_manifest_roots(manifest_payload) == CANONICAL_MICRO_SECONDARY_ROOTS

    mixed_manifest_payload = {
        "request_specs": [
            {"symbol_root": "MES"},
            {"symbol_root": "NQ"},
            {"symbol_root": "M2K"},
        ]
    }
    with pytest.raises(DataFoundationValidationError, match="must not include mini roots"):
        policy.validate_manifest_roots(mixed_manifest_payload)


def test_micro_batch_policy_enforces_declaration_only_parity_targets() -> None:
    policy = MicroBatchPolicy.from_mapping(
        _policy_values(
            parity_check_targets={
                "ES": "MES",
                "NQ": "MNQ",
                "RTY": "M2K",
            }
        )
    )
    assert policy.parity_check_targets == CANONICAL_MINI_MICRO_PARITY_TARGETS

    with pytest.raises(DataFoundationValidationError, match="canonical ES-MES"):
        MicroBatchPolicy.from_mapping(
            _policy_values(
                parity_check_targets=[
                    ("ES", "MNQ"),
                    ("NQ", "MES"),
                    ("RTY", "M2K"),
                ]
            )
        )

    with pytest.raises(DataFoundationValidationError, match="mini_root must be"):
        MicroBatchPolicy.from_mapping(
            _policy_values(
                parity_check_targets=[
                    ("MES", "ES"),
                    ("NQ", "MNQ"),
                    ("RTY", "M2K"),
                ]
            )
        )

    with pytest.raises(DataFoundationValidationError, match="declarations only"):
        MicroBatchPolicy.from_mapping(
            _policy_values(
                parity_check_targets=[
                    {"mini_root": "ES", "micro_root": "MES", "result": "pass"},
                    {"mini_root": "NQ", "micro_root": "MNQ"},
                    {"mini_root": "RTY", "micro_root": "M2K"},
                ]
            )
        )

    with pytest.raises(DataFoundationValidationError, match="must equal ES<->MES"):
        MicroBatchPolicy.from_mapping(
            _policy_values(parity_check_targets=[("ES", "MES"), ("NQ", "MNQ")])
        )


def test_micro_batch_plan_references_p05_p10_contracts_without_economic_duplication() -> None:
    policy_mapping = cast(Mapping[str, object], MICRO_BATCH_PLAN["policy"])
    separation_contract = cast(Mapping[str, object], MICRO_BATCH_PLAN["separation_contract"])

    assert policy_mapping["batch_id"] == CANONICAL_MICRO_BATCH_POLICY_ID
    assert policy_mapping["symbols"] == CANONICAL_MICRO_SECONDARY_ROOTS
    assert policy_mapping["start_date"] == CANONICAL_MICRO_BATCH_START_DATE
    assert policy_mapping["separate_batch"] is True
    assert policy_mapping["parity_check_targets"] == CANONICAL_MINI_MICRO_PARITY_TARGETS

    assert MICRO_BATCH_PLAN["secondary_path"] is True
    assert MICRO_BATCH_PLAN["v1_source_role"] == "secondary_path_not_primary_alpha_source"
    assert MICRO_BATCH_PLAN["start_date_status"] == MICRO_BATCH_START_DATE_STATUS
    assert (
        MICRO_BATCH_PLAN["instrument_economics_reference"]
        == DATA_P05_INSTRUMENT_ECONOMICS_REFERENCE
    )
    assert MICRO_BATCH_PLAN["instrument_economics_contract"] == (
        INSTRUMENT_MASTER_RECORD_CONTRACT
    )
    assert MICRO_BATCH_PLAN["instrument_economics_roots"] == CANONICAL_MICRO_SECONDARY_ROOTS
    assert separation_contract["contract_reference"] == DATA_P10_SEPARATION_CONTRACT_REFERENCE
    assert separation_contract["symbol_batch_plan_id"] == MINI_MAIN_SYMBOL_BATCH_PLAN.plan_id
    assert separation_contract["do_not_mix_mini_and_micro_batches"] is True
    assert separation_contract["max_concurrent_roots"] == CANONICAL_MAX_CONCURRENT_ROOTS
    assert MICRO_BATCH_PLAN["parity_check_declaration_only"] is True
    assert MICRO_BATCH_PLAN["external_provider_call"] is False
    assert MICRO_BATCH_PLAN["pull_authorization"] is False
    assert MICRO_BATCH_PLAN["data_exists_claim"] is False

    duplicated_economics_fields = {"point_value", "tick_size", "tick_value", "multiplier"}
    assert duplicated_economics_fields.isdisjoint(MICRO_BATCH_PLAN)
    assert duplicated_economics_fields.isdisjoint(policy_mapping)
