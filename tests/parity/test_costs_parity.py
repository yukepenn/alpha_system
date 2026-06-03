from __future__ import annotations

from decimal import Decimal

from tests.parity.helpers import assert_accelerated


def test_costs_parity_matches_reference() -> None:
    result = assert_accelerated("costs")

    assert result.fast_run.summary.costs > Decimal("0")
    assert result.fast_run.summary.costs == result.reference_result.summary.costs
