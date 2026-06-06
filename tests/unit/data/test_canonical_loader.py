from __future__ import annotations

from pathlib import Path

import pytest

pl = pytest.importorskip("polars")

from alpha_system.data.foundation.canonical_loader import (  # noqa: E402
    CanonicalLoaderError,
    canonical_partition_path,
    load_canonical_ohlcv_rows,
)

DATASET_VERSION_ID = "dsv_canonical_loader_fixture_v1"
SYMBOL = "ES"


def _write_partition(tmp_path: Path) -> Path:
    canonical_root = tmp_path / "canonical"
    partition_path = canonical_partition_path(
        canonical_root,
        dataset_version_id=DATASET_VERSION_ID,
        symbol=SYMBOL,
    )
    partition_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "instrument_id": "ES",
            "contract_id": "ESM4",
            "series_id": "ES_c_0",
            "bar_start_ts": "2024-01-03T14:32:00+00:00",
            "bar_end_ts": "2024-01-03T14:33:00+00:00",
            "event_ts": "2024-01-03T14:33:00+00:00",
            "available_ts": "2024-01-03T14:33:01+00:00",
            "ingested_at": "2024-01-03T14:33:02+00:00",
            "open": "102.00",
            "high": "102.00",
            "low": "102.00",
            "close": "102.00",
            "volume": "10",
            "source": "dsrc_databento_historical",
            "source_request_id": "req_fixture_1",
            "data_version": DATASET_VERSION_ID,
            "quality_flags": [None],
            "session_label": "RTH",
        },
        {
            "instrument_id": "ES",
            "contract_id": "ESM4",
            "series_id": "ES_c_0",
            "bar_start_ts": "2024-01-03T14:30:00+00:00",
            "bar_end_ts": "2024-01-03T14:31:00+00:00",
            "event_ts": "2024-01-03T14:31:00+00:00",
            "available_ts": "2024-01-03T14:31:01+00:00",
            "ingested_at": "2024-01-03T14:31:02+00:00",
            "open": "100.00",
            "high": "100.00",
            "low": "100.00",
            "close": "100.00",
            "volume": "10",
            "source": "dsrc_databento_historical",
            "source_request_id": "req_fixture_1",
            "data_version": DATASET_VERSION_ID,
            "quality_flags": ["no_trade"],
            "session_label": "RTH",
        },
        {
            "instrument_id": "ES",
            "contract_id": "ESM4",
            "series_id": "ES_c_0",
            "bar_start_ts": "2024-01-04T14:30:00+00:00",
            "bar_end_ts": "2024-01-04T14:31:00+00:00",
            "event_ts": "2024-01-04T14:31:00+00:00",
            "available_ts": "2024-01-04T14:31:01+00:00",
            "ingested_at": "2024-01-04T14:31:02+00:00",
            "open": "104.00",
            "high": "104.00",
            "low": "104.00",
            "close": "104.00",
            "volume": "10",
            "source": "dsrc_databento_historical",
            "source_request_id": "req_fixture_1",
            "data_version": DATASET_VERSION_ID,
            "quality_flags": None,
            "session_label": "RTH",
        },
    ]
    pl.DataFrame(rows).write_parquet(partition_path.as_posix())
    return canonical_root


def test_loader_returns_normalized_canonical_dicts(tmp_path: Path) -> None:
    canonical_root = _write_partition(tmp_path)

    rows = load_canonical_ohlcv_rows(
        canonical_root=canonical_root,
        dataset_version_id=DATASET_VERSION_ID,
        symbol=SYMBOL,
    )

    assert len(rows) == 3
    # Sorted by event_ts ascending.
    assert [row["event_ts"] for row in rows] == [
        "2024-01-03T14:31:00+00:00",
        "2024-01-03T14:33:00+00:00",
        "2024-01-04T14:31:00+00:00",
    ]
    # quality_flags normalized to tuples; None/[None] -> ().
    flags_by_event = {row["event_ts"]: row["quality_flags"] for row in rows}
    assert flags_by_event["2024-01-03T14:31:00+00:00"] == ("no_trade",)
    assert flags_by_event["2024-01-03T14:33:00+00:00"] == ()
    assert flags_by_event["2024-01-04T14:31:00+00:00"] == ()
    assert all(isinstance(row["quality_flags"], tuple) for row in rows)
    assert set(rows[0]).issuperset(
        {"instrument_id", "close", "available_ts", "session_label"}
    )


def test_loader_filters_by_window(tmp_path: Path) -> None:
    canonical_root = _write_partition(tmp_path)

    rows = load_canonical_ohlcv_rows(
        canonical_root=canonical_root,
        dataset_version_id=DATASET_VERSION_ID,
        symbol=SYMBOL,
        start_ts="2024-01-03T00:00:00+00:00",
        end_ts="2024-01-04T00:00:00+00:00",
    )

    assert len(rows) == 2
    assert all(row["bar_start_ts"].startswith("2024-01-03") for row in rows)


def test_loader_fails_closed_when_partition_missing(tmp_path: Path) -> None:
    with pytest.raises(CanonicalLoaderError, match="does not exist"):
        load_canonical_ohlcv_rows(
            canonical_root=tmp_path / "canonical",
            dataset_version_id=DATASET_VERSION_ID,
            symbol=SYMBOL,
        )
