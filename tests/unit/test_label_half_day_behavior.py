from __future__ import annotations

from datetime import datetime, timezone

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import make_bars


def test_half_day_forward_horizon_is_clamped_to_short_session_close() -> None:
    half_day_bars = make_bars(
        [100, 101, 102],
        session_id="XNYS:2026-11-27:regular",
        quality_flags=("synthetic", "correctness_only", "half_day"),
        start=datetime(2026, 11, 27, 17, 57, tzinfo=timezone.utc),
    )

    labels = generate_forward_return_labels(half_day_bars, horizons_minutes=(5,))
    first = labels[0]

    assert first.value is None
    assert first.path_metadata["insufficient_future"] is True
    assert first.path_metadata["clamped_to_session_close"] is True
    assert first.path_metadata["horizon_end_ts"] == "2026-11-27T18:00:00Z"
    assert first.label_available_ts == half_day_bars[-1]["available_ts"]
    validate_label_record(first)
