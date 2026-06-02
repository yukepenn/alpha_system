from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.store import LabelStoreError, LocalLabelStore
from tests.fixtures.labels.synthetic_bars import regular_bars


REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_files(path: Path) -> set[Path]:
    if not path.exists():
        return set()
    return {item.relative_to(REPO_ROOT) for item in path.rglob("*") if item.is_file()}


def test_default_label_store_writes_only_to_temp_root() -> None:
    before_labels = _repo_files(REPO_ROOT / "data" / "labels")
    before_metadata = _repo_files(REPO_ROOT / "metadata")
    labels = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))

    store = LocalLabelStore()
    output_path = store.write_labels("forward_return_fixture", labels)
    loaded = store.read_labels("forward_return_fixture")

    assert output_path.exists()
    assert REPO_ROOT not in output_path.resolve().parents
    assert len(loaded) == len(labels)
    assert _repo_files(REPO_ROOT / "data" / "labels") == before_labels
    assert _repo_files(REPO_ROOT / "metadata") == before_metadata


def test_label_store_rejects_repo_output_paths() -> None:
    with pytest.raises(LabelStoreError, match="not local-only"):
        LocalLabelStore(REPO_ROOT / "data" / "labels" / "generated")
