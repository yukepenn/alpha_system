from __future__ import annotations

from tools.frontier.verdict import parse_done_check_text, parse_review_text


def test_verdict_parser_pass() -> None:
    parsed = parse_review_text("# Review\n\n- Looks good.\n\nVERDICT: PASS\n")

    assert parsed.verdict == "PASS"
    assert parsed.severity == "none"


def test_verdict_parser_pass_with_warnings() -> None:
    parsed = parse_review_text("- Warning: minor issue.\n\nVERDICT: PASS_WITH_WARNINGS\n")

    assert parsed.verdict == "PASS_WITH_WARNINGS"
    assert parsed.warnings


def test_verdict_parser_rework_repairs() -> None:
    parsed = parse_review_text("## Required repairs\n\n- Must fix validation failure.\n\nVERDICT: REWORK\n")

    assert parsed.verdict == "REWORK"
    assert parsed.required_repairs


def test_ambiguous_review_blocks() -> None:
    parsed = parse_review_text("VERDICT: PASS\nVERDICT: BLOCKED\n")

    assert parsed.verdict == "BLOCKED"
    assert parsed.severity == "critical"


def test_required_repairs_ignore_positive_findings() -> None:
    parsed = parse_review_text(
        "# Review\n\n"
        "## What I verified\n\n"
        "- Generated scaffold passes canaries.\n"
        "- Clean validation output.\n"
        "- ✓ Artifact tests passed.\n\n"
        "## Blocking findings\n\n"
        "- artifact_guard blocks data/raw placeholders before honoring placeholder exceptions.\n\n"
        "## Required next step\n\n"
        "- Apply placeholder exceptions before broad raw/cache forbidden globs.\n\n"
        "VERDICT: BLOCKED\n"
    )

    assert parsed.verdict == "BLOCKED"
    assert parsed.required_repairs == [
        "artifact_guard blocks data/raw placeholders before honoring placeholder exceptions.",
        "Apply placeholder exceptions before broad raw/cache forbidden globs.",
    ]
    repairs = "\n".join(parsed.required_repairs)
    assert "Generated scaffold passes" not in repairs
    assert "Clean validation" not in repairs
    assert "✓" not in repairs


def test_required_repairs_from_structured_json_block() -> None:
    parsed = parse_review_text(
        "```json\n"
        '{"required_repairs": ["Fix the placeholder policy."], '
        '"blocking_findings": ["Raw data guard contradicts config."]}\n'
        "```\n\n"
        "VERDICT: BLOCKED\n"
    )

    assert parsed.required_repairs == [
        "Fix the placeholder policy.",
        "Raw data guard contradicts config.",
    ]


def test_done_check_parser_pass() -> None:
    parsed = parse_done_check_text("# Done\n\nDONE_CHECK: PASS\n")

    assert parsed.verdict == "PASS"
    assert parsed.passing


def test_done_check_parser_blocked() -> None:
    parsed = parse_done_check_text("- Missing acceptance evidence.\n\nDONE_CHECK: BLOCKED\n")

    assert parsed.verdict == "BLOCKED"
    assert not parsed.passing


def test_ambiguous_done_check_blocks() -> None:
    parsed = parse_done_check_text("DONE_CHECK: PASS\nDONE_CHECK: REWORK\n")

    assert parsed.verdict == "BLOCKED"
