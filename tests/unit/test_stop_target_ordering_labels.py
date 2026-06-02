from __future__ import annotations

from decimal import Decimal

from alpha_system.core.enums import LabelType
from alpha_system.labels.generation import generate_stop_target_ordering_labels
from tests.fixtures.labels.synthetic_bars import make_bars


def _first_pair(bars: list[dict[str, object]]) -> tuple[object, object]:
    labels = generate_stop_target_ordering_labels(
        bars,
        horizons_minutes=(3,),
        target_return=Decimal("0.01"),
        stop_return=Decimal("0.01"),
    )
    first = [label for label in labels if label.event_ts == bars[0]["event_ts"]]
    target = next(label for label in first if label.label_type == LabelType.TARGET_BEFORE_STOP)
    stop = next(label for label in first if label.label_type == LabelType.STOP_BEFORE_TARGET)
    return target, stop


def test_target_before_stop_ordering() -> None:
    target, stop = _first_pair(
        make_bars([100, 100, 100, 100], highs=[100, 101.5, 100.5, 100.5], lows=[100, 99.2, 98.8, 99])
    )

    assert target.value is True
    assert stop.value is False
    assert target.path_metadata["ordering"] == "target_before_stop"


def test_stop_before_target_ordering() -> None:
    target, stop = _first_pair(
        make_bars([100, 100, 100, 100], highs=[100, 100.5, 101.5, 100.5], lows=[100, 98.8, 99.2, 99])
    )

    assert target.value is False
    assert stop.value is True
    assert stop.path_metadata["ordering"] == "stop_before_target"


def test_same_bar_target_and_stop_is_conservative_ambiguous() -> None:
    target, stop = _first_pair(
        make_bars([100, 100, 100, 100], highs=[100, 101.2, 100.5, 100.5], lows=[100, 98.8, 99.2, 99])
    )

    assert target.value is False
    assert stop.value is False
    assert target.path_metadata["ordering"] == "ambiguous_same_bar"
    assert target.path_metadata["ambiguous_same_bar"] is True
