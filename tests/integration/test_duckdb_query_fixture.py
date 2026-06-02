from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.query import query_csv_with_duckdb
from alpha_system.data.storage import DataDependencyError, dependency_available


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "data"
    / "synthetic_1min_bars.csv"
)


def test_duckdb_query_over_tiny_csv_fixture() -> None:
    sql = """
        SELECT
            instrument_id,
            count(*) AS bar_count,
            sum(volume) AS total_volume
        FROM bars
        GROUP BY instrument_id
    """

    if not dependency_available("duckdb"):
        with pytest.raises(DataDependencyError, match="duckdb is required"):
            query_csv_with_duckdb(FIXTURE, sql)
        return

    rows = query_csv_with_duckdb(FIXTURE, sql)

    assert rows == [
        {
            "instrument_id": "SYNTH-1",
            "bar_count": 3,
            "total_volume": pytest.approx(3100),
        }
    ]
