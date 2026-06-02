from __future__ import annotations

from datetime import datetime, timezone

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import make_bars


def test_forward_horizon_does_not_cross_session_boundary() -> None:
    first_session = make_bars([100, 101], session_id="XNYS:2026-01-02:regular")
    second_session = make_bars(
        [200, 201, 202],
        session_id="XNYS:2026-01-05:regular",
        start=datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc),
    )

    labels = generate_forward_return_labels(first_session + second_session, horizons_minutes=(3,))
    first = next(label for label in labels if label.event_ts == first_session[0]["event_ts"])

    assert first.value is None
    assert first.path_metadata["session_id"] == "XNYS:2026-01-02:regular"
    assert first.path_metadata["observed_future_bars"] == 1
    assert first.path_metadata["clamped_to_session_close"] is True
    assert first.label_available_ts == first_session[-1]["available_ts"]
    validate_label_record(first)
