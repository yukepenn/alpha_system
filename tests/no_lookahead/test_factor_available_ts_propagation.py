from __future__ import annotations

from datetime import timedelta

from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_factor_available_ts_propagates_late_input_availability() -> None:
    spec = factor_spec(availability_lag=30)
    bars = make_bars(["100", "101"], available_delay=timedelta(minutes=5))

    values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        bars,
        data_version=DATA_VERSION,
    )

    assert values[1].available_ts == bars[1]["available_ts"] + timedelta(seconds=30)
    assert values[1].available_ts > bars[1]["event_ts"] + timedelta(minutes=5)
