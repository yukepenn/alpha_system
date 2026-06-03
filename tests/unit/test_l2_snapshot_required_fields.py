from __future__ import annotations

from alpha_system.core.schema import contract_field_names
from alpha_system.l2.schemas import (
    L2_SNAPSHOT_SCHEMA,
    L2SnapshotSchemaRecord,
    REQUIRED_L2_SNAPSHOT_FIELDS,
    l2_snapshot_columns,
    missing_l2_snapshot_fields,
)


def test_l2_snapshot_required_fields_are_declared_in_order() -> None:
    assert l2_snapshot_columns() == REQUIRED_L2_SNAPSHOT_FIELDS
    assert tuple(L2_SNAPSHOT_SCHEMA) == REQUIRED_L2_SNAPSHOT_FIELDS


def test_l2_snapshot_schema_record_contains_required_fields() -> None:
    assert contract_field_names(L2SnapshotSchemaRecord) == REQUIRED_L2_SNAPSHOT_FIELDS


def test_l2_snapshot_missing_required_fields_are_reported() -> None:
    missing = missing_l2_snapshot_fields({"instrument_id": "SYNTH-L2-1"})

    assert "available_ts" in missing
    assert "quality_flags" in missing
