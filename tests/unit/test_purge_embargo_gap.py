from __future__ import annotations

from alpha_system.experiments.splits import apply_purge_embargo


def test_purge_embargo_removes_training_indices_around_validation_window() -> None:
    train = tuple(range(10))
    validation = (5, 6)

    filtered = apply_purge_embargo(train, validation, purge_gap=2, embargo_gap=1)

    assert filtered == (0, 1, 2, 8, 9)
