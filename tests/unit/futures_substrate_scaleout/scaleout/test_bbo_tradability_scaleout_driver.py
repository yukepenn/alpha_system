from __future__ import annotations

from alpha_system.features.scaleout import load_scaleout_config, render_scaleout_summary_markdown
from alpha_system.features.scaleout.driver import (
    _unit_executor_for_family,
    materialize_v1_feature_unit,
    materialize_bbo_tradability_top_book_unit,
    run_scaleout,
)

CONFIG_PATH = "configs/features/scaleout/bbo_tradability_top_book.json"


def test_bbo_tradability_scaleout_driver_defaults_to_v1_with_reference_fallback() -> None:
    assert _unit_executor_for_family("bbo_tradability_top_book") is materialize_v1_feature_unit
    assert (
        _unit_executor_for_family("bbo_tradability_top_book", engine="reference")
        is materialize_bbo_tradability_top_book_unit
    )


def test_bbo_tradability_scaleout_full_window_preview_has_proxy_guardrails() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="full-window")
    rendered = render_scaleout_summary_markdown(summary)

    assert summary.accepted_unit_count == 24
    assert summary.planned_count == 24
    assert summary.failed_count == 0
    assert {record.unit.year for record in summary.records} == set(range(2019, 2027))
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    assert all(record.unit.schema_id == "bbo_1m" for record in summary.records)
    assert all(record.unit.dataset_version_id.startswith("dsv_databento_bbo_") for record in summary.records)
    assert all(record.feature_version_ids for record in summary.records)
    assert "time-sampled and forward-filled" in rendered
    assert "Passive-fill" in rendered
    assert "Missing, quarantined, wide-spread, and low-depth" in rendered
