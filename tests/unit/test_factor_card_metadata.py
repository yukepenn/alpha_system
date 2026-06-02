from __future__ import annotations

from alpha_system.reports.factor_card import build_factor_card, render_factor_card_markdown
from tests.fixtures.reports.synthetic import diagnostic_summary, report_metadata


def test_factor_card_preserves_reproducibility_metadata() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )

    metadata = card.to_dict()["metadata"]
    assert metadata["data_version"] == "data:v1"
    assert metadata["factor_version"] == "factor:v1"
    assert metadata["label_version"] == "label:v1"
    assert metadata["code_hash_ref"] == "code:abc123"
    assert metadata["config_hash_ref"] == "config:def456"
    assert metadata["run_manifest_path"] == "artifacts/factor_studies/run_manifest.json"
    assert metadata["factor_label_alignment_status"] == "matched"


def test_factor_card_metadata_renders_required_fields() -> None:
    card = build_factor_card(
        diagnostic_summary(),
        reproducibility_metadata=report_metadata(),
    )
    rendered = render_factor_card_markdown(card)

    for value in (
        "data:v1",
        "factor:v1",
        "label:v1",
        "code:abc123",
        "config:def456",
        "artifacts/factor_studies/run_manifest.json",
        "passed",
        "review_pending",
    ):
        assert value in rendered
