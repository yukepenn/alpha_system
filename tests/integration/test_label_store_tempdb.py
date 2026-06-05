from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.store import (
    LabelStoreError,
    get_label_version,
    register_label_version,
)
from tests.fixtures.labels.synthetic_bars import regular_bars


def test_label_versions_are_recorded_in_temp_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    label = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))[0]

    register_label_version(
        registry_path,
        label,
        label_version="v1",
        parameters={"horizon_minutes": 1},
        decision_status="draft",
    )
    record = get_label_version(registry_path, label.label_id, "v1")

    assert record is not None
    assert record.label_id == "forward_return_1m"
    assert record.label_version == "v1"
    assert record.label_type == "forward_return_1m"
    assert record.data_version == "data:synthetic-labels:v1"
    assert record.parameters == {"horizon_minutes": 1}
    assert len(record.code_hash) == 64
    assert len(record.config_hash) == 64


def test_duplicate_label_versions_are_rejected_in_temp_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    label = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))[0]
    register_label_version(registry_path, label, label_version="v1")

    with pytest.raises(LabelStoreError, match="already exists"):
        register_label_version(registry_path, label, label_version="v1")
