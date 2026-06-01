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
    parsed = parse_review_text("- Must fix validation failure.\n\nVERDICT: REWORK\n")

    assert parsed.verdict == "REWORK"
    assert parsed.required_repairs


def test_ambiguous_review_blocks() -> None:
    parsed = parse_review_text("VERDICT: PASS\nVERDICT: BLOCKED\n")

    assert parsed.verdict == "BLOCKED"
    assert parsed.severity == "critical"


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
