from __future__ import annotations

import pytest

from alpha_system.research.events import false_breakout_rate


def test_false_breakout_rate_counts_non_positive_event_returns() -> None:
    rows = [
        {"event_trigger": True, "forward_return": 0.01},
        {"event_trigger": True, "forward_return": -0.02},
        {"event_trigger": True, "forward_return": 0.00},
        {"event_trigger": False, "forward_return": -0.01},
    ]

    result = false_breakout_rate(rows)

    assert result["event_count"] == 3
    assert result["false_breakout_rate"] == pytest.approx(2 / 3)
