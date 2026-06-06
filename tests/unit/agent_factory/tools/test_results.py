from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from alpha_system.agent_factory.tools.results import (
    AGENT_TOOL_RESULT_FIELDS,
    AgentToolResult,
    AgentToolStatus,
)

EXPECTED_RESULT_FIELDS = (
    "status",
    "role",
    "request_id",
    "alpha_spec_id",
    "study_spec_id",
    "dataset_version_id",
    "feature_pack_refs",
    "label_pack_refs",
    "runtime_run_id",
    "diagnostics_summary",
    "cost_summary",
    "rejection_reasons",
    "blocking_findings",
    "next_required_gate",
    "artifacts",
    "limitations",
)


def test_agent_tool_result_carries_exact_structured_fields() -> None:
    assert tuple(field.name for field in fields(AgentToolResult)) == EXPECTED_RESULT_FIELDS
    assert AGENT_TOOL_RESULT_FIELDS == EXPECTED_RESULT_FIELDS


def test_agent_tool_result_accepts_value_free_summary() -> None:
    result = valid_result(status="OK")

    assert result.status is AgentToolStatus.OK
    assert result.role == "diagnostics_runner"
    assert result.dataset_version_id == "dataset_version:es_2024_seed"
    assert result.feature_pack_refs == ("feature_pack:seed_ohlcv",)
    assert result.label_pack_refs == ("label_pack:fixed_horizon_seed",)
    assert result.artifacts == ("artifact_ref:diagnostics_summary",)


def test_agent_tool_result_is_immutable() -> None:
    result = valid_result()

    with pytest.raises(FrozenInstanceError):
        result.role = "statistical_reviewer"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("dataset_version_id", "data/raw/es_ticks.parquet"),
        ("runtime_run_id", b"binary-runtime-payload"),
        ("diagnostics_summary", "embedded_file_contents=provider bytes"),
        ("cost_summary", "pandas dataframe with rows"),
        ("feature_pack_refs", ("feature_pack:seed", "feature_pack:seed")),
        ("label_pack_refs", ["label_pack:mutable"]),  # type: ignore[list-item]
        ("rejection_reasons", ("raw quotes included",)),
        ("blocking_findings", ("numpy ndarray payload",)),
        ("artifacts", ("local_bundle.arrow",)),
        ("limitations", ("base64 encoded provider payload",)),
    ],
)
def test_agent_tool_result_rejects_raw_or_heavy_payloads(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(valid_result(), **{field_name: bad_value})


@pytest.mark.parametrize("bad_status", ["PASS", "ok", "", " OK "])
def test_agent_tool_result_rejects_unknown_or_malformed_status(
    bad_status: str,
) -> None:
    with pytest.raises(ValueError):
        valid_result(status=bad_status)


def test_agent_tool_result_rejects_unstructured_collections() -> None:
    with pytest.raises(TypeError):
        replace(valid_result(), diagnostics_summary={"rows": [1, 2, 3]})


def valid_result(status: AgentToolStatus | str = AgentToolStatus.OK) -> AgentToolResult:
    return AgentToolResult(
        status=status,
        role="diagnostics_runner",
        request_id="request:diagnostics_seed",
        alpha_spec_id="alpha_spec:seed",
        study_spec_id="study_spec:seed",
        dataset_version_id="dataset_version:es_2024_seed",
        feature_pack_refs=("feature_pack:seed_ohlcv",),
        label_pack_refs=("label_pack:fixed_horizon_seed",),
        runtime_run_id="runtime_run:dry_contract",
        diagnostics_summary="status counts and blocking findings only",
        cost_summary="cost stress summary without values",
        rejection_reasons=(),
        blocking_findings=("runtime bridge not implemented until AGENT-P21",),
        next_required_gate="statistical_review",
        artifacts=("artifact_ref:diagnostics_summary",),
        limitations=("contract only",),
    )
