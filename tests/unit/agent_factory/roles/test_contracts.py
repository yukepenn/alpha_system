from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from alpha_system.agent_factory.roles.contracts import AgentRole


def test_valid_agent_role_round_trips_every_field() -> None:
    role = valid_role()

    assert role.role_id == "synthetic_reviewer"
    assert role.name == "Synthetic Reviewer"
    assert role.purpose == "Review one bounded synthetic handoff."
    assert role.readable_inputs == ("handoff_ref", "evidence_summary_ref")
    assert role.callable_tools == ("review.checklist",)
    assert role.producible_outputs == ("review_verdict_ref",)
    assert role.allowed_decisions == ("request_revision", "reject_handoff")
    assert role.forbidden_decisions == (
        "self_approval",
        "self_promotion",
        "raw_provider_access",
        "alpha_tradability_claim",
    )
    assert role.handoff_format == ("summary", "decision", "rejection_modes")
    assert role.reviewer_independence == ("drafter != approver",)
    assert role.failure_modes == ("malformed_handoff", "missing_independence")


def test_agent_role_is_immutable() -> None:
    role = valid_role()

    with pytest.raises(FrozenInstanceError):
        role.name = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("role_id", ""),
        ("name", ""),
        ("purpose", ""),
        ("readable_inputs", ()),
        ("callable_tools", ()),
        ("producible_outputs", ()),
        ("allowed_decisions", ()),
        ("forbidden_decisions", ()),
        ("handoff_format", ()),
        ("reviewer_independence", ()),
        ("failure_modes", ()),
    ],
)
def test_agent_role_required_fields_fail_closed(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(valid_role(), **{field_name: bad_value})


def test_agent_role_rejects_mutable_collection_fields() -> None:
    with pytest.raises(TypeError):
        AgentRole(
            role_id="mutable_role",
            name="Mutable Role",
            purpose="Demonstrate fail-closed collection validation.",
            readable_inputs=["handoff_ref"],  # type: ignore[arg-type]
            callable_tools=("review.checklist",),
            producible_outputs=("review_verdict_ref",),
            allowed_decisions=("request_revision",),
            forbidden_decisions=("self_approval",),
            handoff_format=("summary",),
            reviewer_independence=("drafter != approver",),
            failure_modes=("malformed_contract",),
        )


@pytest.mark.parametrize(
    "bad_value",
    [
        "raw_payload",
        "provider_payload",
        "db_rows",
        "data/raw/es_ticks.parquet",
        "metadata/roles.sqlite",
        "artifacts/report.arrow",
    ],
)
def test_agent_role_rejects_raw_heavy_payload_references(bad_value: str) -> None:
    with pytest.raises(ValueError):
        replace(valid_role(), readable_inputs=(bad_value,))


def test_agent_role_rejects_multiline_or_oversized_payload_text() -> None:
    with pytest.raises(ValueError):
        replace(valid_role(), purpose="line one\nline two")

    with pytest.raises(ValueError):
        replace(valid_role(), purpose="x" * 513)


def valid_role() -> AgentRole:
    return AgentRole(
        role_id="synthetic_reviewer",
        name="Synthetic Reviewer",
        purpose="Review one bounded synthetic handoff.",
        readable_inputs=("handoff_ref", "evidence_summary_ref"),
        callable_tools=("review.checklist",),
        producible_outputs=("review_verdict_ref",),
        allowed_decisions=("request_revision", "reject_handoff"),
        forbidden_decisions=(
            "self_approval",
            "self_promotion",
            "raw_provider_access",
            "alpha_tradability_claim",
        ),
        handoff_format=("summary", "decision", "rejection_modes"),
        reviewer_independence=("drafter != approver",),
        failure_modes=("malformed_handoff", "missing_independence"),
    )
