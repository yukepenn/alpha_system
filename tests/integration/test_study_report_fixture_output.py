from __future__ import annotations

from alpha_system.reports.study_report import (
    build_study_report,
    render_study_report_markdown,
    write_study_report,
)
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_study_report_fixture_markdown_output_is_tiny_and_deterministic(tmp_path) -> None:
    metadata = {
        "factors": {
            "fixture_close_delta": report_metadata(),
            "fixture_volume_delta": report_metadata(),
        }
    }
    report = build_study_report(
        [
            diagnostic_summary(),
            diagnostic_summary(factor_id="fixture_volume_delta", factor_version="factor:v2"),
        ],
        study_id="synthetic_study_report",
        reproducibility_metadata=metadata,
    )
    output_path = tmp_path / "study_report.md"

    written = write_study_report(report, output_path)
    rendered = render_study_report_markdown(report)

    assert written == output_path
    assert output_path.read_text(encoding="utf-8") == rendered
    assert output_path.stat().st_size < 40_000
    assert rendered.startswith("# Study Report: synthetic_study_report\n")
    assert "fixture_close_delta" in rendered
    assert "fixture_volume_delta" in rendered
    assert "candidate_for_review" in rendered
