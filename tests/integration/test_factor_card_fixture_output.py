from __future__ import annotations

from alpha_system.reports.factor_card import (
    build_factor_card,
    render_factor_card_csv,
    render_factor_card_markdown,
    write_factor_card,
)
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_factor_card_fixture_markdown_output_is_tiny_and_deterministic(tmp_path) -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    output_path = tmp_path / "factor_card.md"

    written = write_factor_card(card, output_path)
    rendered = render_factor_card_markdown(card)

    assert written == output_path
    assert output_path.read_text(encoding="utf-8") == rendered
    assert output_path.stat().st_size < 20_000
    assert rendered.startswith("# Factor Card: fixture_close_delta\n")
    assert "candidate_for_review" in rendered
    assert "fixture_momentum" in rendered


def test_factor_card_fixture_csv_output_is_tiny_and_deterministic() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    rendered = render_factor_card_csv(card)

    assert rendered.splitlines()[0] == "section,field,value"
    assert "correlation_to_existing_factors,values" in rendered
    assert len(rendered.encode("utf-8")) < 20_000
