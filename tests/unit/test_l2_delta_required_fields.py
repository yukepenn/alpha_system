from __future__ import annotations

from alpha_system.core.schema import contract_field_names
from alpha_system.l2.schemas import (
    L2_EVENT_DELTA_SCHEMA,
    L2EventDeltaSchemaRecord,
    REQUIRED_L2_EVENT_DELTA_FIELDS,
    l2_event_delta_columns,
    missing_l2_event_delta_fields,
)


def test_l2_delta_required_fields_are_declared_in_order() -> None:
    assert l2_event_delta_columns() == REQUIRED_L2_EVENT_DELTA_FIELDS
    assert tuple(L2_EVENT_DELTA_SCHEMA) == REQUIRED_L2_EVENT_DELTA_FIELDS


def test_l2_delta_schema_record_contains_required_fields() -> None:
    assert contract_field_names(L2EventDeltaSchemaRecord) == REQUIRED_L2_EVENT_DELTA_FIELDS


def test_l2_delta_missing_required_fields_are_reported() -> None:
    missing = missing_l2_event_delta_fields({"instrument_id": "SYNTH-L2-1"})

    assert "sequence_id" in missing
    assert "action" in missing
    assert "available_ts" in missing
