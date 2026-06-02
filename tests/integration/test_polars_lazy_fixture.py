from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.data.query import polars_fixture_close_summary
from alpha_system.data.storage import DataDependencyError, dependency_available


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "data"
    / "synthetic_1min_bars.csv"
)


def test_polars_lazy_transformation_over_tiny_fixture() -> None:
    if not dependency_available("polars"):
        with pytest.raises(DataDependencyError, match="polars is required"):
            polars_fixture_close_summary(FIXTURE)
        return

    rows = polars_fixture_close_summary(FIXTURE)

    assert rows == [
        {
            "instrument_id": "SYNTH-1",
            "bar_count": 3,
            "mean_close": pytest.approx(100.75),
        }
    ]
