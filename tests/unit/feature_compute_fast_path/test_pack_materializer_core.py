from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializer,
    SymbolYearFrameRequest,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.input_views import build_ohlcv_input_view
from tests.fixtures.feature_label.synthetic import (
    EmptyRegistryReader,
    accepted_version,
    approved_feature_request,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    FeatureParityTolerance,
    assert_feature_records_match,
)

DATASET_ID = "dsv_fast_path_synthetic_v1"
PARTITION_ID = "development_partition"


def test_pack_materializer_matches_reference_returns_on_synthetic_fixture() -> None:
    pl = pytest.importorskip("polars")
    rows = _fixture_rows()
    accepted = accepted_version(DATASET_ID)
    request = approved_feature_request("fast_path_synthetic_returns")
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_parity",
    )
    reference_records = compute_ohlcv_feature(definition, reference_view)
    materializer = PackMaterializer()
    frame = materializer.frame_from_rows(rows)
    pack = _returns_pack(definition.spec, pl)

    fast_records = materializer.compute_values(frame, pack)

    assert definition.version.feature_version_id == pack.declarations[0].feature_version_id
    assert_feature_records_match(
        reference_records,
        fast_records,
        expected_feature_version_id=definition.version.feature_version_id,
        tolerance=FeatureParityTolerance(abs=1e-12, reason="float division parity"),
    )


def test_compute_values_derives_identity_once_per_declaration_not_per_row(monkeypatch) -> None:
    """Regression: the content-addressed identity must be derived once per
    declaration, never per output row. `feature_version_id` is an uncached property
    that runs JSON-canonicalize + SHA-256 on every access; referencing it inside the
    per-row loop re-hashed identity O(rows) times and made full-window
    materialization pathologically slow (the FCFP P13 benchmark hang)."""
    pl = pytest.importorskip("polars")
    rows = _fixture_rows()
    assert len(rows) >= 2, "fixture must have multiple rows for the per-row bug to be visible"
    request = approved_feature_request("fast_path_synthetic_returns")
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    materializer = PackMaterializer()
    frame = materializer.frame_from_rows(rows)
    pack = _returns_pack(definition.spec, pl)

    from alpha_system.features import contracts as _contracts

    original = _contracts.FeatureVersion.derive.__func__
    calls = {"n": 0}

    def _counting_derive(cls: Any, spec: Any) -> Any:
        calls["n"] += 1
        return original(cls, spec)

    monkeypatch.setattr(_contracts.FeatureVersion, "derive", classmethod(_counting_derive))

    records = materializer.compute_values(frame, pack)

    assert len(records) >= 2
    assert calls["n"] == len(pack.declarations), (
        f"identity derived {calls['n']}x for {len(pack.declarations)} declaration(s) over "
        f"{len(records)} rows; feature_version_id must be hoisted out of the per-row loop"
    )


def test_constant_window_mask_flags_residual_constant_window() -> None:
    """Regression: zero-variance detection must use a constant-window (max==min)
    check, not `rolling_std == 0.0`. Polars' SLIDING rolling_std carries a floating
    residual after a value leaves the window, so a genuinely-constant window that
    follows a changed value gets a tiny non-zero std (~1e-9) and an exact `== 0`
    check misses it -- while the per-row reference flags zero_variance. This was the
    FCFP-P13 real-data parity break on bbo_tradability_spread_zscore (24k rows)."""
    pl = pytest.importorskip("polars")
    from alpha_system.features.fast import constant_window_mask

    # Window [0.1, 0.1, 0.1] at index 4 is constant, but the sliding rolling_std
    # leaves a residual from the prior 0.2 -- so `std == 0` would NOT flag it.
    series = [0.1, 0.2, 0.1, 0.1, 0.1, 0.1]
    frame = pl.DataFrame({"x": series})

    std = frame.select(
        pl.col("x").rolling_std(window_size=3, min_samples=3, ddof=0).alias("s")
    ).to_series().to_list()
    assert std[4] is not None and std[4] != 0.0, (
        "fixture must exercise the residual: sliding rolling_std should be non-zero "
        f"on the constant window (got {std[4]!r}); the exact std==0 check would miss it"
    )

    mask = frame.select(
        constant_window_mask(pl.col("x"), window=3).alias("zero_var")
    ).to_series().to_list()
    # window at index i = positions [i-2, i-1, i]
    assert mask[4] is True, "constant window [0.1,0.1,0.1] must be detected as zero-variance"
    assert mask[5] is True, "constant window [0.1,0.1,0.1] must be detected as zero-variance"
    assert mask[2] is False, "window [0.1,0.2,0.1] varies -> not zero-variance"
    assert mask[3] is False, "window [0.2,0.1,0.1] varies -> not zero-variance"


def test_constant_window_mask_distinguishes_constant_and_varying() -> None:
    pl = pytest.importorskip("polars")
    from alpha_system.features.fast import constant_window_mask

    frame = pl.DataFrame(
        {
            "seg": ["a", "a", "a", "a", "b", "b", "b"],
            "x": [5.0, 5.0, 5.0, 7.0, 3.0, 3.0, 3.0],
        }
    )
    mask = frame.select(
        constant_window_mask(pl.col("x"), window=3, group="seg").alias("z")
    ).to_series().to_list()
    # per-segment, window=3: first two rows of each segment are null (insufficient)
    assert mask[2] is True  # [5,5,5] constant
    assert mask[3] is False  # [5,5,7] varies
    assert mask[6] is True  # [3,3,3] constant; segment reset prevents bleed from 'a'


def test_pack_materializer_persists_and_registers_through_feature_store(
    tmp_path: Path,
) -> None:
    pl = pytest.importorskip("polars")
    rows = _fixture_rows()
    accepted = accepted_version(DATASET_ID)
    request = approved_feature_request("fast_path_synthetic_registry_returns")
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    checked_request = definition.request_gate_decision.checked_feature_request or request
    materializer = PackMaterializer()
    pack = _returns_pack(definition.spec, pl)

    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.DUAL,
    )
    records = materializer.register_pack(
        result,
        pack,
        feature_requests={definition.spec.feature_id: checked_request},
    )

    assert result.value_store_handle is not None
    assert result.value_store_handle.format is ValueStoreFormat.DUAL
    assert result.value_store_handle.schema_version == FAST_VALUE_SCHEMA_VERSION
    assert Path(result.value_store_handle.jsonl_path or "").exists()
    assert Path(result.value_store_handle.parquet_path or "").exists()
    assert len(records) == 1
    record = records[0]
    assert record.feature_version_id == definition.version.feature_version_id
    assert record.value_store_format == "dual"
    assert record.producer_engine_id == FAST_PRODUCER_ENGINE_ID
    assert record.value_schema_version == FAST_VALUE_SCHEMA_VERSION
    assert record.registry_metadata.to_dict()["producer_engine_id"] == FAST_PRODUCER_ENGINE_ID
    assert record.registry_metadata.to_dict()["value_schema_version"] == FAST_VALUE_SCHEMA_VERSION
    assert record.lineage.contract_provenance.to_dict()["producer_engine_id"] == (
        FAST_PRODUCER_ENGINE_ID
    )


def test_symbol_year_loader_caches_one_frame_per_request() -> None:
    pytest.importorskip("polars")
    rows = _fixture_rows()
    calls: list[dict[str, Any]] = []

    def loader(**kwargs: Any) -> tuple[dict[str, Any], ...]:
        calls.append(dict(kwargs))
        return tuple(rows)

    materializer = PackMaterializer(canonical_ohlcv_loader=loader)
    request = SymbolYearFrameRequest(
        canonical_root="/tmp/alpha_system_synthetic",
        dataset_version_id=DATASET_ID,
        symbol="es",
        year=2024,
    )

    first = materializer.load_symbol_year_ohlcv_frame(request)
    second = materializer.load_symbol_year_ohlcv_frame(request)

    assert first is second
    assert len(calls) == 1
    assert calls[0]["symbol"] == "ES"
    assert calls[0]["start_ts"] == "2024-01-01T00:00:00+00:00"
    assert calls[0]["end_ts"] == "2025-01-01T00:00:00+00:00"


def _returns_pack(feature_spec: Any, pl: Any) -> FastFeaturePack:
    close = pl.col("close").cast(pl.Float64)
    prior_close = close.shift(1)
    current_no_trade = pl.col("quality_flags").list.contains("no_trade").fill_null(False)
    prior_no_trade = current_no_trade.shift(1).fill_null(False)
    insufficient_window = prior_close.is_null()
    input_gap = current_no_trade | prior_no_trade
    empty_flags = pl.lit([], dtype=pl.List(pl.Utf8))
    insufficient_flags = pl.lit(
        ["insufficient_window", "primitive_gap"],
        dtype=pl.List(pl.Utf8),
    )
    input_gap_flags = pl.lit(
        ["input_gap", "no_trade", "primitive_gap"],
        dtype=pl.List(pl.Utf8),
    )
    value_expr = (
        pl.when(insufficient_window | input_gap | (prior_close == 0.0))
        .then(None)
        .otherwise(close / prior_close - 1.0)
    )
    flags_expr = (
        pl.when(insufficient_window)
        .then(insufficient_flags)
        .when(input_gap)
        .then(input_gap_flags)
        .when(prior_close == 0.0)
        .then(pl.lit(["primitive_gap", "zero_denominator"], dtype=pl.List(pl.Utf8)))
        .otherwise(empty_flags)
    )
    return FastFeaturePack(
        feature_set=FeatureSetSpec(
            feature_set_id="feature_set_fast_path_demo",
            feature_set_version="v1",
            features=(feature_spec,),
            description="Synthetic fast-path parity demonstrator.",
        ),
        declarations=(
            FastFeatureDeclaration(
                feature_spec=feature_spec,
                value_expr=value_expr,
                quality_flags_expr=flags_expr,
            ),
        ),
    )


def _fixture_rows() -> tuple[dict[str, Any], ...]:
    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "feature_compute_fast_path"
        / "canonical_ohlcv_rows.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["dataset_version_id"] == DATASET_ID
    return tuple(dict(row) for row in payload["rows"])
