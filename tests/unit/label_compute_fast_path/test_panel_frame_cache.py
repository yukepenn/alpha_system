"""LCFP-P08 panel-cache regression tests.

The process-local panel-frame cache must be semantically invisible: executing
the same unit set through the cached path (one shared materializer, repeated
requests) must yield exactly the record sets and registry-eligible payloads
the uncached path (a fresh materializer per unit) produces. The cache must be
bounded, must never alias across dataset versions, and must reset for
benchmark cold starts.
"""

from __future__ import annotations

from typing import Any

import pytest

from alpha_system.core.value_store import compute_value_content_hash
from alpha_system.labels.fast import (
    FastLabelMaterializer,
    LabelPanelFrameRequest,
    build_cost_adjusted_label_pack,
    build_session_maintenance_label_pack,
)
from alpha_system.labels.fast.materializer import _canonical_record_dicts
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from tests.fixtures.label_compute_fast_path.session_cost_labels import (
    DATASET_ID,
    cost_adjusted_bbo_rows,
    cost_adjusted_label_specs,
    cost_adjusted_ohlcv_rows,
    session_maintenance_label_specs,
    session_maintenance_ohlcv_rows,
)

OHLCV_DATASET_VERSION_ID = "dsv_lcfp_p08_cache_ohlcv_a"
BBO_DATASET_VERSION_ID = "dsv_lcfp_p08_cache_bbo_a"


class _CountingLoader:
    """Fake canonical loader that records every (dataset_version_id) call."""

    def __init__(self, rows: tuple[dict[str, Any], ...]) -> None:
        self.rows = rows
        self.calls: list[str] = []

    def __call__(self, **kwargs: Any) -> tuple[dict[str, Any], ...]:
        self.calls.append(str(kwargs["dataset_version_id"]))
        return self.rows


def _cost_pack() -> Any:
    specs = cost_adjusted_label_specs()
    return build_cost_adjusted_label_pack(
        tuple(
            build_cost_adjusted_label_definition(
                label_name,
                specs[label_name],
                dataset_version_ids=(DATASET_ID,),
            )
            for label_name in (
                CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
                CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            )
        )
    )


def _close_out_pack() -> Any:
    specs = session_maintenance_label_specs()
    return build_session_maintenance_label_pack(
        tuple(
            build_fixed_horizon_label_definition(
                label_name,
                specs[label_name],
                dataset_version_ids=(DATASET_ID,),
            )
            for label_name in (
                FixedHorizonLabelName.SESSION_CLOSE,
                FixedHorizonLabelName.MAINTENANCE_FLAT,
            )
        )
    )


def _request(
    *,
    ohlcv_dataset_version_id: str = OHLCV_DATASET_VERSION_ID,
    bbo_dataset_version_id: str = BBO_DATASET_VERSION_ID,
) -> LabelPanelFrameRequest:
    return LabelPanelFrameRequest(
        canonical_root="unused_by_counting_loaders",
        dataset_version_id=ohlcv_dataset_version_id,
        symbol="ES",
        year=2024,
        bbo_dataset_version_id=bbo_dataset_version_id,
    )


def _materializer(
    ohlcv_loader: _CountingLoader,
    bbo_loader: _CountingLoader,
) -> FastLabelMaterializer:
    return FastLabelMaterializer(
        canonical_ohlcv_loader=ohlcv_loader,
        canonical_bbo_loader=bbo_loader,
    )


def _registry_eligible_payload(computation: Any) -> tuple[str, dict[str, Any]]:
    """Return the registry-eligible payload identity for one computation."""

    return (
        compute_value_content_hash(_canonical_record_dicts(computation.records)),
        computation.metadata.to_dict(),
    )


def test_cached_cost_pack_is_semantically_invisible_and_loads_once() -> None:
    pytest.importorskip("polars")
    pack = _cost_pack()
    ohlcv_rows = cost_adjusted_ohlcv_rows()
    bbo_rows = cost_adjusted_bbo_rows()

    # Cached path: ONE shared materializer executes the same unit set twice.
    ohlcv_loader = _CountingLoader(ohlcv_rows)
    bbo_loader = _CountingLoader(bbo_rows)
    shared = _materializer(ohlcv_loader, bbo_loader)
    first = shared.compute_values_with_metadata(
        shared.load_symbol_year_price_frame(_request()), pack
    )
    second = shared.compute_values_with_metadata(
        shared.load_symbol_year_price_frame(_request()), pack
    )
    assert ohlcv_loader.calls == [OHLCV_DATASET_VERSION_ID]
    assert bbo_loader.calls == [BBO_DATASET_VERSION_ID]

    # Uncached path: a fresh materializer per unit (cold caches every time).
    uncached_runs = []
    for _ in range(2):
        cold = _materializer(_CountingLoader(ohlcv_rows), _CountingLoader(bbo_rows))
        uncached_runs.append(
            cold.compute_values_with_metadata(
                cold.load_symbol_year_price_frame(_request()), pack
            )
        )

    assert first.records == second.records
    assert first.records == uncached_runs[0].records == uncached_runs[1].records
    assert len(first.records) > 0
    assert (
        _registry_eligible_payload(first)
        == _registry_eligible_payload(second)
        == _registry_eligible_payload(uncached_runs[0])
        == _registry_eligible_payload(uncached_runs[1])
    )


def test_cached_close_out_pack_reuses_terminal_models_invisibly() -> None:
    pytest.importorskip("polars")
    pack = _close_out_pack()
    ohlcv_rows = session_maintenance_ohlcv_rows()

    ohlcv_loader = _CountingLoader(ohlcv_rows)
    bbo_loader = _CountingLoader(())
    shared = _materializer(ohlcv_loader, bbo_loader)
    first = shared.compute_values_with_metadata(
        shared.load_symbol_year_price_frame(_request()), pack
    )
    second = shared.compute_values_with_metadata(
        shared.load_symbol_year_price_frame(_request()), pack
    )
    assert len(ohlcv_loader.calls) == 1

    cold = _materializer(_CountingLoader(ohlcv_rows), _CountingLoader(()))
    uncached = cold.compute_values_with_metadata(
        cold.load_symbol_year_price_frame(_request()), pack
    )

    assert first.records == second.records == uncached.records
    assert len(first.records) > 0
    assert (
        _registry_eligible_payload(first)
        == _registry_eligible_payload(second)
        == _registry_eligible_payload(uncached)
    )


def test_frame_cache_never_aliases_across_dataset_versions() -> None:
    pytest.importorskip("polars")
    ohlcv_rows = cost_adjusted_ohlcv_rows()
    bbo_rows = cost_adjusted_bbo_rows()
    ohlcv_loader = _CountingLoader(ohlcv_rows)
    bbo_loader = _CountingLoader(bbo_rows)
    shared = _materializer(ohlcv_loader, bbo_loader)

    shared.load_symbol_year_price_frame(_request())
    shared.load_symbol_year_price_frame(
        _request(bbo_dataset_version_id="dsv_lcfp_p08_cache_bbo_b")
    )
    shared.load_symbol_year_price_frame(
        _request(ohlcv_dataset_version_id="dsv_lcfp_p08_cache_ohlcv_b")
    )

    # Every distinct (OHLCV, BBO) DatasetVersion pair re-loads: a stale frame
    # is never served for a different dataset version identity.
    assert ohlcv_loader.calls == [
        OHLCV_DATASET_VERSION_ID,
        OHLCV_DATASET_VERSION_ID,
        "dsv_lcfp_p08_cache_ohlcv_b",
    ]
    assert bbo_loader.calls == [
        BBO_DATASET_VERSION_ID,
        "dsv_lcfp_p08_cache_bbo_b",
        BBO_DATASET_VERSION_ID,
    ]


def test_frame_cache_is_bounded_with_fifo_eviction() -> None:
    pytest.importorskip("polars")
    ohlcv_rows = cost_adjusted_ohlcv_rows()
    bbo_rows = cost_adjusted_bbo_rows()
    ohlcv_loader = _CountingLoader(ohlcv_rows)
    bbo_loader = _CountingLoader(bbo_rows)
    shared = _materializer(ohlcv_loader, bbo_loader)
    bound = FastLabelMaterializer._FRAME_CACHE_MAX_ENTRIES
    assert bound >= 1

    requests = [
        _request(ohlcv_dataset_version_id=f"dsv_lcfp_p08_cache_ohlcv_{index}")
        for index in range(bound + 1)
    ]
    pack = _cost_pack()
    for request in requests:
        # Drive the full cached path so derived panel state is populated too.
        shared.compute_values_with_metadata(
            shared.load_symbol_year_price_frame(request), pack
        )

    assert len(shared._frame_cache) <= bound
    assert len(shared._panel_cache) <= FastLabelMaterializer._PANEL_CACHE_MAX_ENTRIES
    assert len(shared._terminal_model_cache) <= FastLabelMaterializer._PANEL_CACHE_MAX_ENTRIES

    # The oldest request was evicted (FIFO), so revisiting it loads again.
    calls_before = len(ohlcv_loader.calls)
    shared.load_symbol_year_price_frame(requests[0])
    assert len(ohlcv_loader.calls) == calls_before + 1
    # The most recent request is still cached.
    shared.load_symbol_year_price_frame(requests[-1])
    assert len(ohlcv_loader.calls) == calls_before + 1


def test_driver_shared_materializer_is_process_local_and_cold_start_resettable() -> None:
    pytest.importorskip("polars")
    from alpha_system.features.scaleout.driver import (
        _shared_fast_label_materializer,
        reset_fast_label_materializer_caches,
    )

    reset_fast_label_materializer_caches()
    try:
        with_bbo = _shared_fast_label_materializer(requires_bbo=True)
        without_bbo = _shared_fast_label_materializer(requires_bbo=False)
        assert with_bbo is _shared_fast_label_materializer(requires_bbo=True)
        assert without_bbo is _shared_fast_label_materializer(requires_bbo=False)
        assert with_bbo is not without_bbo

        # Benchmark cells call this to start cold: a fresh materializer (and
        # therefore an empty panel-frame cache) must be returned afterwards.
        reset_fast_label_materializer_caches()
        assert _shared_fast_label_materializer(requires_bbo=True) is not with_bbo
    finally:
        reset_fast_label_materializer_caches()
