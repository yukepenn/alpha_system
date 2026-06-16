"""Canary for the SCHEMA-AWARE label accepted-context preflight.

This guards the engine-seam fix that lets a BBO-dsv-primary cost_adjusted config
(``configs/labels/scaleout/bbo_microstructure_cost_adjusted.json``) actually
materialize under ``--execute``.

Before the fix, ``_label_accepted_context`` was hardwired to the OHLCV preflight
(``_session_bar_row_loader`` -> ``load_canonical_ohlcv_rows`` and
``_scaleout_quality_coverage_builder`` -> ``_canonical_ohlcv_mapping`` projecting
to ``CANONICAL_OHLCV_FIELDS``). A BBO-primary unit (``schema_id == "bbo_1m"``)
has no OHLCV columns on its canonical surface, so the projection raised
``canonical OHLCV row missing required fields: open, high, low, close, volume``
on every unit.

The fix dispatches on the unit's RESOLVED primary schema:

* ``schema_id`` startswith ``bbo`` -> the BBO-aware preflight
  (``_build_bbo_accepted_context``: BBO canonical loader + BBO-appropriate
  quality/coverage) with an EMPTY OHLCV trade-row overlay (``bar_rows == ()``).
* ``schema_id == "ohlcv_1m"`` (every existing config) -> the UNCHANGED OHLCV
  preflight (byte-identical routing: OHLCV loader + OHLCV quality/coverage).

These canaries are hermetic: they monkeypatch the leaf loaders to assert the
routing decision and the fail-on-old / pass-on-new behaviour without touching
``ALPHA_DATA_ROOT``. The actual BBO value math is unchanged and lives only in the
sanctioned reference engine (``alpha_system.labels.families.cost_adjusted``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.features.scaleout import (
    ScaleoutTarget,
    load_scaleout_config,
    run_scaleout,
)

BBO_CONFIG_PATH = "configs/labels/scaleout/bbo_microstructure_cost_adjusted.json"
OHLCV_CONFIG_PATH = "configs/labels/scaleout/cost_adjusted.json"


def _first_unit(config_path: str):
    config = load_scaleout_config(config_path)
    summary = run_scaleout(
        config,
        rollout="full-window",
        execute=False,
        engine="reference",
        target=ScaleoutTarget(symbols=("ES",), years=(2024,)),
    )
    assert summary.records, f"expected planned label units for {config_path}"
    return config, summary.records[0].unit


def test_bbo_primary_unit_is_detected_and_ohlcv_primary_is_not() -> None:
    """The dispatch predicate keys on the resolved primary schema, not a flag."""

    _bbo_config, bbo_unit = _first_unit(BBO_CONFIG_PATH)
    _ohlcv_config, ohlcv_unit = _first_unit(OHLCV_CONFIG_PATH)

    assert bbo_unit.schema_id == "bbo_1m"
    assert ohlcv_unit.schema_id == "ohlcv_1m"
    assert scaleout_driver._unit_primary_schema_is_bbo(bbo_unit) is True
    assert scaleout_driver._unit_primary_schema_is_bbo(ohlcv_unit) is False


def test_bbo_primary_preflight_routes_bbo_context_not_ohlcv_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PASS-ON-NEW: a bbo_1m-primary unit builds its accepted-context + quality-
    coverage via the BBO path and never invokes the OHLCV loader/projection.
    """

    scaleout_driver._LABEL_ACCEPTED_CONTEXT_CACHE.clear()
    bbo_config, bbo_unit = _first_unit(BBO_CONFIG_PATH)

    calls: list[str] = []

    def _spy_bbo(unit, *, dataset_registry_path, canonical_root):
        calls.append("bbo")
        # Minimal stand-in for the real BBO accepted context; the routing, not
        # the canonical load, is what this canary locks.
        return scaleout_driver._BBOAcceptedContext(
            accepted=object(),
            bbo_rows=(),
            quality_status="PASSING",
            coverage_status="PASSING",
        )

    def _explode_ohlcv(**_kwargs):
        calls.append("ohlcv_loader")
        raise AssertionError("BBO-primary preflight must not load OHLCV rows")

    monkeypatch.setattr(scaleout_driver, "_build_bbo_accepted_context", _spy_bbo)
    monkeypatch.setattr(scaleout_driver, "_session_bar_row_loader", _explode_ohlcv)

    context = scaleout_driver._label_accepted_context(
        bbo_config,
        bbo_unit,
        dataset_registry_path=tmp_path / "registry.sqlite",
        canonical_root=tmp_path / "canonical",
    )

    assert calls == ["bbo"], f"expected BBO routing only, got {calls}"
    # The OHLCV trade-row overlay must be EMPTY for a single-(BBO)-dsv unit:
    # no second value truth, no OHLCV-missing-fields projection.
    assert context.bar_rows == ()
    assert context.quality_status == "PASSING"


def test_ohlcv_primary_preflight_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NO REGRESSION: an ohlcv_1m-primary unit still routes the OHLCV loader +
    OHLCV quality/coverage builder, and never the BBO path.
    """

    scaleout_driver._LABEL_ACCEPTED_CONTEXT_CACHE.clear()
    ohlcv_config, ohlcv_unit = _first_unit(OHLCV_CONFIG_PATH)

    calls: list[str] = []

    def _spy_ohlcv_loader(**_kwargs):
        calls.append("ohlcv_loader")
        # One synthetic canonical OHLCV row so the downstream builder/projection
        # has a real OHLCV surface to validate, exactly as today.
        return (
            {
                "open": 1.0,
                "high": 1.0,
                "low": 1.0,
                "close": 1.0,
                "volume": 1.0,
            },
        )

    def _spy_quality_coverage(_config, rows, *, repo_root):
        calls.append("ohlcv_quality_coverage")
        # The OHLCV quality/coverage builder is the seam where the OLD code
        # projected every row to CANONICAL_OHLCV_FIELDS. We only need to observe
        # that this OHLCV builder (not the BBO path) was routed; halt here.
        raise _StopBuild

    def _explode_bbo(*_args, **_kwargs):
        calls.append("bbo")
        raise AssertionError("OHLCV-primary preflight must not build a BBO context")

    monkeypatch.setattr(scaleout_driver, "_session_bar_row_loader", _spy_ohlcv_loader)
    monkeypatch.setattr(
        scaleout_driver, "_scaleout_quality_coverage_builder", _spy_quality_coverage
    )
    monkeypatch.setattr(scaleout_driver, "_build_bbo_accepted_context", _explode_bbo)

    with pytest.raises(_StopBuild):
        scaleout_driver._label_accepted_context(
            ohlcv_config,
            ohlcv_unit,
            dataset_registry_path=tmp_path / "registry.sqlite",
            canonical_root=tmp_path / "canonical",
        )

    # The OHLCV loader and the OHLCV quality/coverage builder both ran; the BBO
    # path was never touched.
    assert calls == ["ohlcv_loader", "ohlcv_quality_coverage"]


def test_ohlcv_projection_raises_on_a_bbo_only_row() -> None:
    """FAIL-ON-OLD signature: the OHLCV projection that the OLD preflight applied
    unconditionally raises the exact 'missing required fields' error on a BBO row
    (bid/ask/mid only). The fix avoids this by routing BBO-primary units away
    from this projection entirely.
    """

    from alpha_system.data.foundation.canonical_loader import CANONICAL_OHLCV_FIELDS

    bbo_only_row = {
        "bid": 100.0,
        "ask": 100.25,
        "mid": 100.125,
        "spread": 0.25,
        "bid_size": 10.0,
        "ask_size": 10.0,
    }
    with pytest.raises(scaleout_driver.ScaleoutError) as exc:
        scaleout_driver._canonical_ohlcv_mapping(
            bbo_only_row, fields=CANONICAL_OHLCV_FIELDS
        )
    assert "missing required fields" in str(exc.value)
    assert "open" in str(exc.value)


class _StopBuild(Exception):
    """Sentinel to halt the OHLCV preflight after the routing is observed."""
