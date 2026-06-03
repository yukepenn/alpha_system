from __future__ import annotations

from alpha_system.experiments.splits import assert_chronological_split, train_validation_split


def test_train_validation_split_is_chronological() -> None:
    window = train_validation_split(10, validation_fraction=0.3)

    assert window.train_indices == tuple(range(7))
    assert window.validation_indices == (7, 8, 9)
    assert_chronological_split(window)


def test_train_validation_split_applies_purge_gap() -> None:
    window = train_validation_split(10, validation_fraction=0.3, purge_gap=2)

    assert window.validation_indices == (7, 8, 9)
    assert window.train_indices == (0, 1, 2, 3, 4)
