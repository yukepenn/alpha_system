from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.governance.claims import (
    PERMITTED_NON_ASSERTING_LANGUAGE,
    PROHIBITED_CLAIM_TAXONOMY,
    STANDARD_NO_CLAIMS_LANGUAGE,
    UnsupportedClaimError,
    find_unsupported_claims,
    validate_no_unsupported_claims,
)

EXPECTED_CATEGORIES = {
    "alpha_validity",
    "profitability",
    "tradability",
    "robustness",
    "production_readiness",
    "paper_readiness",
    "live_readiness",
    "broker_readiness",
    "real_data_readiness",
}


@pytest.mark.parametrize(
    ("category", "text"),
    (
        ("alpha_validity", "This report proves alpha validity."),
        ("profitability", "This report says the output is profitable."),
        ("tradability", "This report says the output is tradable."),
        ("robustness", "This report says the output is robust."),
        ("production_readiness", "This report says production-readiness is confirmed."),
        ("paper_readiness", "This report says the output is paper-ready."),
        ("live_readiness", "This report says the output is live-ready."),
        ("broker_readiness", "This report says the output is broker-ready."),
        ("real_data_readiness", "This report says the output is ready for real data."),
    ),
)
def test_prohibited_claim_phrases_are_detected_and_blocking(
    category: str,
    text: str,
) -> None:
    violations = find_unsupported_claims(text)

    assert [violation.category for violation in violations] == [category]

    with pytest.raises(UnsupportedClaimError) as exc_info:
        validate_no_unsupported_claims(text, context="synthetic governance report")

    assert exc_info.value.violations[0].category == category
    assert exc_info.value.issues[0].code == f"unsupported_claim:{category}"
    assert exc_info.value.to_dict()["violations"][0]["category"] == category


def test_taxonomy_covers_full_required_category_set() -> None:
    assert {rule.category for rule in PROHIBITED_CLAIM_TAXONOMY} == EXPECTED_CATEGORIES
    assert all(rule.patterns for rule in PROHIBITED_CLAIM_TAXONOMY)


@pytest.mark.parametrize(
    "payload",
    (
        None,
        b"This report says the output is profitable.",
        "",
        " \n\t ",
        "decoded text with \ufffd replacement character",
        "decoded text with \x00 NUL",
    ),
)
def test_malformed_or_undecidable_input_fails_closed(payload: object) -> None:
    with pytest.raises(UnsupportedClaimError) as exc_info:
        validate_no_unsupported_claims(payload, context="synthetic governance report")

    assert exc_info.value.issues
    assert exc_info.value.violations == ()


@pytest.mark.parametrize(
    "text",
    (
        STANDARD_NO_CLAIMS_LANGUAGE,
        "This template is not an alpha/profitability/tradability/production-ready claim.",
        "Blocked-language taxonomy category profitability lists the blocked phrase profitable.",
        "The guard blocks robust when it is used as a research-output assertion.",
        "AlphaSpec and alpha_spec_id are governance identifiers, not market evidence.",
    ),
)
def test_permitted_non_asserting_language_passes(text: str) -> None:
    assert find_unsupported_claims(text) == ()
    validate_no_unsupported_claims(text)


@pytest.mark.parametrize(
    ("text", "expected_categories"),
    (
        (
            "The alpha_system pipeline produced profitable, tradable results.",
            {"profitability", "tradability"},
        ),
        (
            "The alpha_id record is profitable.",
            {"profitability"},
        ),
        (
            "This validation requires profitable returns.",
            {"profitability"},
        ),
        (
            "The template requires the strategy to be tradable.",
            {"tradability"},
        ),
    ),
)
def test_allowlist_does_not_bypass_report_claims(
    text: str,
    expected_categories: set[str],
) -> None:
    violations = find_unsupported_claims(text)

    assert {violation.category for violation in violations} == expected_categories


def test_guard_documentation_records_taxonomy_and_allowlist() -> None:
    text = Path("docs/governance/UNSUPPORTED_CLAIM_GUARD.md").read_text(encoding="utf-8")

    for rule in PROHIBITED_CLAIM_TAXONOMY:
        assert rule.category in text
    for allowed_language in PERMITTED_NON_ASSERTING_LANGUAGE:
        assert allowed_language in text
    validate_no_unsupported_claims(text, context="unsupported-claim guard doc")


def test_governance_templates_do_not_contain_unsupported_claims() -> None:
    template_paths = sorted(
        path
        for path in Path("templates/governance").iterdir()
        if path.is_file() and path.suffix in {".md", ".yaml"}
    )

    assert template_paths
    for path in template_paths:
        validate_no_unsupported_claims(path.read_text(encoding="utf-8"), context=str(path))


def test_evidence_governance_report_template_requires_core_sections() -> None:
    text = Path("templates/governance/evidence_governance_report.template.md").read_text(
        encoding="utf-8"
    )
    compact_text = " ".join(text.split())

    assert "## Evidence References" in text
    assert "## Limitations" in text
    assert "## No-Claims Language" in text
    assert "## Required Checks" in text
    assert " ".join(STANDARD_NO_CLAIMS_LANGUAGE.split()) in compact_text
