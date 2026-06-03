from __future__ import annotations

from alpha_system.experiments.splits import walk_forward_splits


def test_walk_forward_split_windows_are_ordered() -> None:
    windows = walk_forward_splits(
        12,
        train_window=4,
        validation_window=2,
        step_size=2,
    )

    assert [window.train_indices for window in windows] == [
        (0, 1, 2, 3),
        (2, 3, 4, 5),
        (4, 5, 6, 7),
        (6, 7, 8, 9),
    ]
    assert [window.validation_indices for window in windows] == [
        (4, 5),
        (6, 7),
        (8, 9),
        (10, 11),
    ]
