from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureName,
    CrossMarketInputBundle,
    align_cross_market_rows,
    build_cross_market_feature_definition,
    compute_cross_market_feature,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
CONFIG_PATH = "configs/features/scaleout/cross_market_alignment.json"
DATASET_VERSION_ID = "dsv_synthetic_cross_market_p13"
P13_PRIMITIVE_COUNT = 11


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_cross_market_scaleout_preview_maps_existing_primitives() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "cross_market_alignment"
    assert config.feature_names == (
        "aligned_returns",
        "beta_residual",
        "basket_residual",
        "relative_strength_rank",
        "catch_up_rotation",
        "divergence_agreement",
        "lead_lag",
    )
    assert summary.accepted_unit_count == 8
    assert summary.bounded_unit_count == 1
    assert summary.failed_count == 0
    assert {record.unit.symbol for record in summary.records} == {"ES_NQ_RTY"}
    for record in summary.records:
        assert len(record.feature_version_ids) == P13_PRIMITIVE_COUNT
        assert all(version_id.startswith("fver_") for version_id in record.feature_version_ids)
        assert {dataset.schema_id for dataset in record.unit.input_datasets} == {
            "ohlcv_1m",
            "ohlcv_dense_research_grid",
        }
    bounded_versions = {
        record.unit.year: tuple(record.feature_version_ids)
        for record in summary.records
        if record.unit.year == summary.bounded_year
    }
    assert len(set(bounded_versions.values())) == 1


def test_strict_intersection_preserves_latest_contributing_available_ts() -> None:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    delayed_nq_available = datetime(2024, 1, 2, 14, 40, tzinfo=UTC)
    bundle = CrossMarketInputBundle(
        {
            "ES": OHLCVInputView(
                (
                    _row("ES", start, close="100"),
                    _row("ES", start + timedelta(minutes=1), close="102"),
                )
            ),
            "NQ": OHLCVInputView(
                (
                    _row("NQ", start, close="200"),
                    _row(
                        "NQ",
                        start + timedelta(minutes=1),
                        close="206",
                        available_ts=delayed_nq_available,
                    ),
                )
            ),
            "RTY": OHLCVInputView(
                (
                    _row("RTY", start, close="50"),
                    _row("RTY", start + timedelta(minutes=1), close="51"),
                )
            ),
        }
    )
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        _approved_request(CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        reset_on_session=False,
        alignment_policy="strict_intersection",
    )

    snapshots = align_cross_market_rows(
        bundle,
        reset_on_session=False,
        alignment_policy="strict_intersection",
    )
    records = compute_cross_market_feature(definition, bundle)

    assert [snapshot.event_ts for snapshot in snapshots] == [
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
    ]
    assert snapshots[1].available_ts == delayed_nq_available
    assert records[1].available_ts == delayed_nq_available
    assert records[1].value == pytest.approx(0.01)
    assert all(
        source_ts <= snapshots[1].available_ts
        for timestamps in snapshots[1].source_available_ts.values()
        for source_ts in timestamps
    )


def test_strict_intersection_does_not_impute_missing_instrument_event() -> None:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    bundle = CrossMarketInputBundle(
        {
            "ES": OHLCVInputView(
                (
                    _row("ES", start, close="100"),
                    _row("ES", start + timedelta(minutes=1), close="102"),
                )
            ),
            "NQ": OHLCVInputView(
                (
                    _row("NQ", start, close="200"),
                    _row("NQ", start + timedelta(minutes=1), close="206"),
                )
            ),
            "RTY": OHLCVInputView((_row("RTY", start, close="50"),)),
        }
    )

    snapshots = align_cross_market_rows(
        bundle,
        reset_on_session=False,
        alignment_policy="strict_intersection",
    )

    assert [snapshot.event_ts for snapshot in snapshots] == [start + timedelta(minutes=1)]


def test_cross_market_scaleout_guard_rejects_asof_alignment_policy() -> None:
    config = load_scaleout_config(CONFIG_PATH)
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        _approved_request(CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        alignment_policy="asof",
    )

    with pytest.raises(scaleout_driver.ScaleoutError, match="strict_intersection"):
        scaleout_driver._require_trusted_scaleout_feature_specs(
            config,
            (definition.spec.feature_spec,),
        )


def _row(
    market: str,
    bar_start_ts: datetime,
    *,
    close: str,
    available_ts: datetime | None = None,
) -> OHLCVInputRow:
    close_decimal = Decimal(close)
    available = available_ts or bar_start_ts + timedelta(minutes=1, seconds=1)
    return OHLCVInputRow(
        instrument_id=market,
        contract_id=f"{market}M4",
        series_id=f"{market}.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=close_decimal,
        high=close_decimal,
        low=close_decimal,
        close=close_decimal,
        volume=Decimal("10"),
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label="RTH",
    )


def _approved_request(feature: CrossMarketFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"cross_market_{feature.value}"],
        formula_sketch={
            "exposure_family": f"cross_market_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "markets": ["ES", "NQ", "RTY"],
            "operation": feature.value,
            "alignment_policy": "strict_intersection",
        },
        availability_assumptions={
            "timing": "output waits for all same-event contributing instrument rows",
            "forbidden": "no cross-instrument forward-fill or missing-instrument imputation",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "event_ts", "available_ts", "quality_flags"],
            "source": "tiny synthetic ES/NQ/RTY fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
