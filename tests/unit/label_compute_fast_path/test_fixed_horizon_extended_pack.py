from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import build_ohlcv_input_view
from alpha_system.labels.fast import FastLabelMaterializer, build_fixed_horizon_label_pack
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelValueRecord
from tests.fixtures.feature_compute_fast_path.fixed_horizon_label import (
    DATASET_ID,
    PARTITION_ID,
    fixed_horizon_ohlcv_rows,
    governed_fixed_horizon_label_specs,
)
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.unit.feature_compute_fast_path.parity_harness import assert_label_records_match


_TRADE_MINUTE_LABELS = (
    FixedHorizonLabelName.FWD_RET_1M,
    FixedHorizonLabelName.FWD_RET_3M,
    FixedHorizonLabelName.FWD_RET_5M,
    FixedHorizonLabelName.FWD_RET_10M,
    FixedHorizonLabelName.FWD_RET_15M,
    FixedHorizonLabelName.FWD_RET_30M,
    FixedHorizonLabelName.FWD_RET_60M,
    FixedHorizonLabelName.FWD_RET_120M,
    FixedHorizonLabelName.FWD_RET_240M,
)


def test_extended_trade_horizon_pack_matches_reference_for_all_nine_horizons() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _definitions(_TRADE_MINUTE_LABELS)
    ohlcv_rows = fixed_horizon_ohlcv_rows()
    reference_records = compute_fixed_horizon_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose="lcfp_p03_extended_fixed_horizon_reference",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_fixed_horizon_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)

    for definition in definitions:
        assert reference_records[definition.name]
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
        )


@pytest.mark.parametrize(
    ("label_name", "source_ts"),
    (
        (
            FixedHorizonLabelName.FWD_RET_240M,
            datetime(2024, 3, 7, 23, 45, tzinfo=UTC),
        ),
        (
            FixedHorizonLabelName.FWD_RET_240M,
            datetime(2024, 1, 2, 21, 45, tzinfo=UTC),
        ),
    ),
)
def test_extended_horizon_roll_and_maintenance_crossings_drop_like_reference(
    label_name: FixedHorizonLabelName,
    source_ts: datetime,
) -> None:
    pytest.importorskip("polars")
    definition = _definitions((label_name,))[0]
    rows = (
        _row(source_ts, close=Decimal("100")),
        _row(source_ts + timedelta(minutes=definition.horizon_minutes), close=Decimal("101")),
    )
    accepted = accepted_version(DATASET_ID)
    reference_records = compute_fixed_horizon_labels(
        (definition,),
        build_ohlcv_input_view(
            accepted,
            rows,
            partition_id=PARTITION_ID,
            purpose="lcfp_p03_extended_fixed_horizon_guard_reference",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=rows, bbo_rows=()),
        build_fixed_horizon_label_pack((definition,)),
    )

    assert reference_records[label_name] == ()
    assert computation.records == ()


def _definitions(
    names: tuple[FixedHorizonLabelName, ...],
) -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = governed_fixed_horizon_label_specs()
    return tuple(
        build_fixed_horizon_label_definition(
            name,
            specs[name],
            dataset_version_ids=(DATASET_ID,),
        )
        for name in names
    )


def _records_by_label_version(
    records: tuple[LabelValueRecord, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {label_version_id: tuple(values) for label_version_id, values in grouped.items()}


def _row(event_ts: datetime, *, close: Decimal) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESH4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": close,
        "high": close + Decimal("0.25"),
        "low": close - Decimal("0.25"),
        "close": close,
        "volume": Decimal("10"),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p03_guard_case",
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": "RTH",
    }
