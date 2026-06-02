from __future__ import annotations

import pytest

from alpha_system.research.execution_filters import (
    adverse_selection_proxy,
    execution_filter_summary,
    sensitivity_by_field,
)


def test_execution_filter_sensitivity_summarizes_spread_buckets() -> None:
    rows = [
        {"spread": 0.01, "forward_return": 0.03, "factor_value": 1},
        {"spread": 0.02, "forward_return": 0.02, "factor_value": 1},
        {"spread": 0.05, "forward_return": -0.01, "factor_value": -1},
        {"spread": 0.08, "forward_return": -0.02, "factor_value": -1},
    ]

    spread = sensitivity_by_field(rows, field="spread", bucket_count=2)
    summary = execution_filter_summary(
        [
            {
                **row,
                "liquidity": 1000 - index * 100,
                "slippage": row["spread"],
                "volume_participation": 0.01 + index * 0.01,
            }
            for index, row in enumerate(rows)
        ]
    )
    adverse = adverse_selection_proxy(rows)

    assert spread["correlation"] < 0
    assert spread["buckets"][0]["mean_forward_return"] == pytest.approx(0.025)
    assert summary["liquidity_sensitivity"]["n"] == 4
    assert adverse["n"] == 4
