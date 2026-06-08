from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.families.bbo import (
    BBOFeatureName,
    build_bbo_feature_definition,
    compute_bbo_feature,
)
from alpha_system.features.input_views import BBOInputRow, BBOInputView
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
CONFIG_PATH = "configs/features/scaleout/bbo_tradability_top_book.json"
DATASET_VERSION_ID = "dsv_databento_bbo_f9e1d70a04d9dae4"

P12_BBO_PRIMITIVES = (
    BBOFeatureName.MID,
    BBOFeatureName.SPREAD,
    BBOFeatureName.SPREAD_TICKS,
    BBOFeatureName.SPREAD_ZSCORE,
    BBOFeatureName.TOP_BOOK_DEPTH,
    BBOFeatureName.TOP_BOOK_IMBALANCE,
    BBOFeatureName.MISSING_BBO_FLAG,
    BBOFeatureName.BAD_QUOTE_FLAG,
    BBOFeatureName.WIDE_SPREAD_FLAG,
    BBOFeatureName.LOW_DEPTH_FLAG,
    BBOFeatureName.MICROPRICE,
)


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_bbo_top_book_scaleout_preview_maps_existing_bbo_primitives() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "bbo_tradability_top_book"
    assert config.feature_names == (
        "mid",
        "spread",
        "spread_ticks",
        "spread_zscore",
        "top_book_depth",
        "top_book_imbalance",
        "missing_bbo_flag",
        "bad_quote_flag",
        "wide_spread_flag",
        "low_depth_flag",
        "microprice_proxy",
    )
    assert summary.accepted_unit_count == 24
    assert summary.bounded_unit_count == 3
    assert summary.failed_count == 0
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    version_sets = [set(record.feature_version_ids) for record in summary.records]
    assert len(set.union(*version_sets)) == len(P12_BBO_PRIMITIVES) * len(summary.records)
    for record in summary.records:
        assert len(record.feature_version_ids) == len(P12_BBO_PRIMITIVES)
        assert record.unit.schema_id == "bbo_1m"
        assert record.unit.dataset_version_id.startswith("dsv_databento_bbo_")
        assert all(version_id.startswith("fver_") for version_id in record.feature_version_ids)


def test_bbo_top_book_primitives_preserve_available_ts_and_surface_missingness() -> None:
    view = BBOInputView(_rows())
    definitions = tuple(
        build_bbo_feature_definition(
            name,
            _approved_request(name),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=2,
            wide_spread_bps_threshold=100.0,
            low_depth_threshold=1.0,
            reset_on_session=False,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        )
        for name in P12_BBO_PRIMITIVES
    )

    results = {
        definition.name: compute_bbo_feature(definition, view)
        for definition in definitions
    }

    expected_available_ts = [row.available_ts for row in view.rows]
    for records in results.values():
        assert [record.available_ts for record in records] == expected_available_ts
        assert all(record.available_ts >= record.event_ts for record in records)
        assert all(record.feature_version_id.startswith("fver_") for record in records)

    assert results[BBOFeatureName.MID][0].value == pytest.approx(100.0)
    assert results[BBOFeatureName.SPREAD_ZSCORE][2].value == pytest.approx(1.0)
    assert results[BBOFeatureName.TOP_BOOK_DEPTH][0].value == pytest.approx(40.0)
    assert results[BBOFeatureName.TOP_BOOK_IMBALANCE][0].value == pytest.approx(-0.5)
    assert results[BBOFeatureName.MICROPRICE][0].value == pytest.approx(99.5)
    assert results[BBOFeatureName.WIDE_SPREAD_FLAG][2].value == 1
    assert results[BBOFeatureName.LOW_DEPTH_FLAG][5].value == 1
    assert results[BBOFeatureName.MISSING_BBO_FLAG][3].value == 1
    assert results[BBOFeatureName.BAD_QUOTE_FLAG][4].value == 1

    for name in (
        BBOFeatureName.MID,
        BBOFeatureName.SPREAD,
        BBOFeatureName.TOP_BOOK_DEPTH,
        BBOFeatureName.TOP_BOOK_IMBALANCE,
        BBOFeatureName.MICROPRICE,
    ):
        assert results[name][3].value is None
        assert "missing_bbo" in results[name][3].quality_flags
        assert results[name][4].value is None
        assert "bbo_quarantined" in results[name][4].quality_flags


def _rows() -> tuple[BBOInputRow, ...]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    return (
        _row(start, bid="99", ask="101", bid_size="10", ask_size="30", spread_ticks="8"),
        _row(
            start + timedelta(minutes=1),
            bid="100",
            ask="102",
            bid_size="30",
            ask_size="10",
            spread_ticks="8",
        ),
        _row(
            start + timedelta(minutes=2),
            bid="100",
            ask="104",
            bid_size="20",
            ask_size="20",
            spread_ticks="16",
        ),
        _row(
            start + timedelta(minutes=3),
            bid="0",
            ask="0",
            bid_size="0",
            ask_size="0",
            quality_flags=("missing_bbo",),
        ),
        _row(
            start + timedelta(minutes=4),
            bid="105",
            ask="104",
            bid_size="10",
            ask_size="10",
            mid="104.5",
            spread="-1",
            quality_flags=("bbo_quarantined",),
        ),
        _row(
            start + timedelta(minutes=5),
            bid="101",
            ask="102",
            bid_size="0",
            ask_size="0",
            spread_ticks="4",
        ),
    )


def _row(
    bar_start_ts: datetime,
    *,
    bid: str,
    ask: str,
    bid_size: str,
    ask_size: str,
    mid: str | None = None,
    spread: str | None = None,
    spread_ticks: str | None = None,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    bid_size_decimal = Decimal(bid_size)
    ask_size_decimal = Decimal(ask_size)
    mid_decimal = Decimal(mid) if mid is not None else (bid_decimal + ask_decimal) / Decimal("2")
    spread_decimal = Decimal(spread) if spread is not None else ask_decimal - bid_decimal
    microprice = None
    if bid_size_decimal > 0 and ask_size_decimal > 0 and ask_decimal >= bid_decimal:
        microprice = (
            ask_decimal * bid_size_decimal + bid_decimal * ask_size_decimal
        ) / (bid_size_decimal + ask_size_decimal)
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid_decimal,
        ask=ask_decimal,
        bid_size=bid_size_decimal,
        ask_size=ask_size_decimal,
        mid=mid_decimal,
        spread=spread_decimal,
        data_version=DATASET_VERSION_ID,
        quality_flags=quality_flags,
        session_label="RTH",
        spread_ticks=Decimal(spread_ticks) if spread_ticks is not None else None,
        microprice=microprice,
    )


def _approved_request(feature: BBOFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"bbo_top_book_{feature.value}"],
        formula_sketch={
            "exposure_family": f"bbo_top_book_{feature.value}",
            "inputs": ["canonical_bbo"],
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": "BBO feature value is emitted at the current row available_ts",
            "proxy": "BBO-1m is a time-sampled tradability proxy, not execution truth",
            "missingness": "missing and quarantined quotes are surfaced, not imputed",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["bid", "ask", "bid_size", "ask_size", "quality_flags", "available_ts"],
            "source": "tiny synthetic canonical BBO fixture only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
