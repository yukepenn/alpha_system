from __future__ import annotations

import pytest

from alpha_system.governance.ids import (
    GOVERNANCE_ID_PREFIXES,
    TOKEN_LENGTH,
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    object_for_prefix,
    parse_governance_id,
    prefix_for_kind,
    validate_governance_id,
)

EXPECTED_PREFIXES = {
    "HypothesisCard": "hyp",
    "AlphaSpec": "aspec",
    "FeatureRequest": "freq",
    "LabelSpec": "lspec",
    "StudySpec": "sspec",
    "TrialLedgerRecord": "trial",
    "EvidenceBundle": "evb",
    "RejectedIdeaRecord": "rej",
    "PromotionDecision": "prom",
    "ReviewerVerdict": "rver",
    "NegativeControlResult": "nctrl",
    "AlphaBookRecord": "abook",
    "BudgetAmendmentRecord": "bamend",
    "SealedHoldoutWindow": "holdwin",
    "HoldoutAccessLog": "haccess",
    "SurrogateStudyRun": "surrun",
    "PooledHypothesisRecord": "poolhyp",
}


def test_governance_id_prefixes_match_naming_contract() -> None:
    assert dict(GOVERNANCE_ID_PREFIXES) == EXPECTED_PREFIXES
    assert prefix_for_kind(GovernanceIdKind.ALPHA_SPEC) == "aspec"
    assert object_for_prefix("aspec") == "AlphaSpec"


def test_generate_governance_id_is_deterministic_for_same_logical_content() -> None:
    first = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"version": 1, "title": "synthetic governance primitive"},
    )
    second = generate_governance_id(
        "AlphaSpec",
        {"title": "synthetic governance primitive", "version": 1},
    )

    assert first == second
    assert first.startswith("aspec_")
    assert len(first.split("_", maxsplit=1)[1]) == TOKEN_LENGTH


def test_generate_governance_id_changes_when_logical_content_changes() -> None:
    original = generate_governance_id("StudySpec", {"title": "fixture", "version": 1})
    changed = generate_governance_id("StudySpec", {"title": "fixture", "version": 2})

    assert original != changed


def test_parse_and_validate_governance_id_return_typed_parts() -> None:
    governance_id = generate_governance_id(
        GovernanceIdKind.FEATURE_REQUEST,
        {"feature": "synthetic-input", "version": 1},
    )

    parsed = parse_governance_id(governance_id, expected_kind="FeatureRequest")

    assert parsed.value == governance_id
    assert parsed.kind is GovernanceIdKind.FEATURE_REQUEST
    assert parsed.object_name == "FeatureRequest"
    assert parsed.prefix == "freq"
    assert validate_governance_id(governance_id, expected_prefix="freq") == governance_id


@pytest.mark.parametrize(
    ("value", "code"),
    (
        ("missingseparator", "malformed_id"),
        ("aspec_nothex", "malformed_id"),
        ("unknown_0123456789abcdef01234567", "unknown_prefix"),
    ),
)
def test_parse_governance_id_rejects_malformed_ids(value: str, code: str) -> None:
    with pytest.raises(GovernanceIdError) as exc_info:
        parse_governance_id(value)

    assert exc_info.value.issue.code == code


def test_parse_governance_id_rejects_wrong_expected_kind() -> None:
    governance_id = generate_governance_id("AlphaSpec", {"title": "synthetic", "version": 1})

    with pytest.raises(GovernanceIdError) as exc_info:
        parse_governance_id(governance_id, expected_kind="StudySpec")

    assert exc_info.value.issue.code == "unexpected_kind"


def test_generate_governance_id_rejects_non_mapping_components() -> None:
    with pytest.raises(GovernanceIdError) as exc_info:
        generate_governance_id("AlphaSpec", ["not", "a", "mapping"])  # type: ignore[arg-type]

    assert exc_info.value.issue.code == "invalid_components"


def test_generate_governance_id_rejects_unknown_kind() -> None:
    with pytest.raises(GovernanceIdError) as exc_info:
        generate_governance_id("UnknownObject", {"version": 1})

    assert exc_info.value.issue.code == "unknown_kind"
