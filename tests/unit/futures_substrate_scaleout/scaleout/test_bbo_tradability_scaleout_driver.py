from __future__ import annotations

from types import SimpleNamespace

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.features.scaleout import load_scaleout_config, render_scaleout_summary_markdown
from alpha_system.features.scaleout.driver import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
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


def test_serial_v1_force_recompute_uses_force_helper(monkeypatch, tmp_path) -> None:
    config = load_scaleout_config(CONFIG_PATH)
    calls: list[str] = []

    def _acceptance_lock_noop(*_args, **_kwargs) -> None:
        return None

    def _fake_force_helper(config, unit, alpha_data_root, dataset_registry_path, canonical_root):
        calls.append(unit.unit_id)
        return MaterializedUnitEvidence(
            parquet_path=(tmp_path / "values.parquet").as_posix(),
            content_hash="sha256:test",
            row_count=1,
            feature_version_ids=("fver_test",),
        )

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        _acceptance_lock_noop,
    )
    monkeypatch.setattr(
        scaleout_driver,
        "materialize_v1_feature_unit_force_recompute",
        _fake_force_helper,
    )

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path,
        dataset_registry_path=tmp_path / "datasets.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="full-window",
        execute=True,
        target=ScaleoutTarget(symbols=("ES",), years=(2019,)),
        force_recompute=True,
        workers=1,
    )

    assert calls == ["mbu_cff63bcd382b1b68cd745ce3"]
    assert summary.completed_count == 1
    assert summary.records[0].feature_version_ids == ("fver_test",)


def test_force_recompute_context_allows_mixed_existing_and_missing_fvids(
    monkeypatch,
    tmp_path,
) -> None:
    config = load_scaleout_config(CONFIG_PATH)
    unit = scaleout_driver.build_scaleout_units(
        config,
        target=ScaleoutTarget(symbols=("ES",), years=(2019,)),
    )[0]
    existing_spec = SimpleNamespace(feature_id="bbo_existing")
    missing_spec = SimpleNamespace(feature_id="bbo_missing")
    existing_request = {"feature_request_id": "freq_existing"}
    fresh_request = {"feature_request_id": "freq_missing"}

    class _FakeStore:
        def resolve_feature(self, feature_version_id: str):
            if feature_version_id != "fver_existing":
                return None
            return SimpleNamespace(
                feature_spec=existing_spec,
                feature_request_payload=existing_request,
            )

    monkeypatch.setattr(
        scaleout_driver,
        "_preview_feature_version_ids",
        lambda _config, _unit: ("fver_existing", "fver_missing"),
    )
    monkeypatch.setattr(
        scaleout_driver,
        "_require_existing_v1_materialization",
        lambda _record, _feature_version_id: None,
    )

    def _fresh_for_missing(_config, _unit, *, expected_version_id, alpha_data_root):
        assert expected_version_id == "fver_missing"
        assert alpha_data_root == tmp_path
        fresh = SimpleNamespace(feature_request_payloads={"bbo_missing": fresh_request})
        declaration = SimpleNamespace(feature_spec=missing_spec)
        return fresh, object(), declaration

    monkeypatch.setattr(
        scaleout_driver,
        "_fresh_v1_declaration_for_version",
        _fresh_for_missing,
    )

    feature_specs, feature_requests = (
        scaleout_driver._existing_v1_feature_context_for_force_recompute(
            config,
            unit,
            _FakeStore(),
            alpha_data_root=tmp_path,
        )
    )

    assert feature_specs == (existing_spec, missing_spec)
    assert feature_requests == {
        "bbo_existing": existing_request,
        "bbo_missing": fresh_request,
    }
