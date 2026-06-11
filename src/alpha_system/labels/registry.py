"""Local-only LabelRegistry persistence for materialized label metadata.

The registry stores label metadata, lineage, duplicate/equivalent exposure
reports, and deprecation records. It deliberately does not store label values.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from alpha_system.core.registry import is_local_only_registry_path, resolve_registry_path
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import WindowSpec
from alpha_system.governance.serialization import JsonValue, canonical_serialize
from alpha_system.labels.engine import (
    LABEL_MATERIALIZATION_ALLOWED,
    LabelMaterializationPlan,
    LabelMaterializationResult,
)
from alpha_system.labels.version import (
    LABEL_VERSION_PATTERN,
    BarrierSpec,
    CostAdjustmentSpec,
    FrozenJsonMapping,
    LabelAvailabilityConsumer,
    LabelAvailabilityPolicy,
    LabelContractError,
    LabelContractSpec,
    LabelHorizonSpec,
    LabelInputSpec,
    LabelLineageRecord,
    LabelPathSpec,
    LabelValueRecord,
    LabelVersion,
)

LABEL_REGISTRY_SCHEMA = "alpha_system.labels.registry.v1"
LABEL_DEPRECATION_SCHEMA = "alpha_system.labels.deprecation.v1"
DEFAULT_LABEL_REGISTRY_RELATIVE_PATH = Path("registry") / "labels.sqlite"
PROHIBITED_LABEL_REGISTRY_STATES: frozenset[str] = frozenset(
    {
        "ALPHA_VALIDATED",
        "STRATEGY_READY",
        "LIVE_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
    }
)


class LabelRegistryError(ValueError):
    """Raised when label registry operations fail closed."""


class LabelRegistryLifecycleState(StrEnum):
    """Narrow lifecycle states for registry discoverability only."""

    REGISTERED = "REGISTERED"
    READY_FOR_STUDY = "READY_FOR_STUDY"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class LabelExposureReport:
    """Duplicate/equivalent label exposure metadata recorded at registration."""

    registry_entries_checked: int
    duplicate_label_version_ids: Sequence[str] = ()
    equivalent_label_version_ids: Sequence[str] = ()
    rationale: str = "label registry exposure check"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "registry_entries_checked",
            _require_nonnegative_int(
                self.registry_entries_checked,
                "registry_entries_checked",
            ),
        )
        object.__setattr__(
            self,
            "duplicate_label_version_ids",
            _label_version_id_tuple(
                self.duplicate_label_version_ids,
                "duplicate_label_version_ids",
            ),
        )
        object.__setattr__(
            self,
            "equivalent_label_version_ids",
            _label_version_id_tuple(
                self.equivalent_label_version_ids,
                "equivalent_label_version_ids",
            ),
        )
        object.__setattr__(self, "rationale", _require_text(self.rationale, "rationale"))

    @property
    def has_findings(self) -> bool:
        """Return whether any duplicate or equivalent exposure was recorded."""

        return bool(self.duplicate_label_version_ids or self.equivalent_label_version_ids)

    @property
    def status(self) -> str:
        """Return a compact registry exposure status."""

        if self.duplicate_label_version_ids:
            return "DUPLICATE_RECORDED"
        if self.equivalent_label_version_ids:
            return "EQUIVALENCE_RECORDED"
        return "NO_FINDINGS"

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible report payload."""

        return {
            "registry_entries_checked": self.registry_entries_checked,
            "duplicate_label_version_ids": list(self.duplicate_label_version_ids),
            "equivalent_label_version_ids": list(self.equivalent_label_version_ids),
            "status": self.status,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class LabelRegistryRecord:
    """Versioned registry metadata for one governed materialized label."""

    label_version: LabelVersion
    label_contract: LabelContractSpec
    lineage: LabelLineageRecord
    exposure_report: LabelExposureReport
    materialization_plan_id: str
    dataset_version_id: str
    partition_id: str
    materialization_output_path: str
    value_record_count: int
    first_event_ts: datetime
    last_event_ts: datetime
    first_label_available_ts: datetime
    last_label_available_ts: datetime
    registered_at: datetime
    value_store_format: str = ValueStoreFormat.JSONL.value
    parquet_path: str | None = None
    value_content_hash: str | None = None
    value_schema_version: str | None = None
    lifecycle_state: LabelRegistryLifecycleState | str = (
        LabelRegistryLifecycleState.REGISTERED
    )
    registry_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.label_version, LabelVersion):
            raise LabelRegistryError("label_version must be a LabelVersion")
        if not isinstance(self.label_contract, LabelContractSpec):
            raise LabelRegistryError("label_contract must be a LabelContractSpec")
        if not isinstance(self.lineage, LabelLineageRecord):
            raise LabelRegistryError("lineage must be a LabelLineageRecord")
        if self.label_version != self.label_contract.derive_label_version():
            raise LabelRegistryError("label_version must match LabelContractSpec content")
        if self.lineage.label_version != self.label_version:
            raise LabelRegistryError("lineage must bind the same LabelVersion")
        if self.lineage.label_contract != self.label_contract:
            raise LabelRegistryError("lineage must bind the same LabelContractSpec")
        if self.lineage.label_spec_id != self.label_contract.label_spec_id:
            raise LabelRegistryError("lineage label_spec_id must match LabelContractSpec")
        if not isinstance(self.exposure_report, LabelExposureReport):
            raise LabelRegistryError("exposure_report must be a LabelExposureReport")

        state = _coerce_lifecycle_state(self.lifecycle_state)
        value_record_count = _require_positive_int(
            self.value_record_count,
            "value_record_count",
        )
        first_event_ts = _require_aware_datetime(self.first_event_ts, "first_event_ts")
        last_event_ts = _require_aware_datetime(self.last_event_ts, "last_event_ts")
        first_available_ts = _require_aware_datetime(
            self.first_label_available_ts,
            "first_label_available_ts",
        )
        last_available_ts = _require_aware_datetime(
            self.last_label_available_ts,
            "last_label_available_ts",
        )
        if first_event_ts > last_event_ts:
            raise LabelRegistryError("first_event_ts must not be after last_event_ts")
        if first_available_ts > last_available_ts:
            raise LabelRegistryError(
                "first_label_available_ts must not be after last_label_available_ts"
            )

        object.__setattr__(
            self,
            "materialization_plan_id",
            _require_text(self.materialization_plan_id, "materialization_plan_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _require_text(self.dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(self, "partition_id", _require_text(self.partition_id, "partition_id"))
        object.__setattr__(
            self,
            "materialization_output_path",
            _require_text(self.materialization_output_path, "materialization_output_path"),
        )
        object.__setattr__(
            self,
            "value_store_format",
            _coerce_value_store_format(self.value_store_format).value,
        )
        object.__setattr__(
            self,
            "parquet_path",
            _optional_text_or_none(self.parquet_path, "parquet_path"),
        )
        object.__setattr__(
            self,
            "value_content_hash",
            _optional_text_or_none(self.value_content_hash, "value_content_hash"),
        )
        object.__setattr__(
            self,
            "value_schema_version",
            _optional_text_or_none(self.value_schema_version, "value_schema_version"),
        )
        object.__setattr__(self, "value_record_count", value_record_count)
        object.__setattr__(self, "first_event_ts", first_event_ts)
        object.__setattr__(self, "last_event_ts", last_event_ts)
        object.__setattr__(self, "first_label_available_ts", first_available_ts)
        object.__setattr__(self, "last_label_available_ts", last_available_ts)
        object.__setattr__(
            self,
            "registered_at",
            _require_aware_datetime(self.registered_at, "registered_at"),
        )
        object.__setattr__(self, "lifecycle_state", state)
        object.__setattr__(
            self,
            "registry_metadata",
            _freeze_json_mapping(self.registry_metadata, "registry_metadata"),
        )

    @property
    def label_version_id(self) -> str:
        """Return the deterministic LabelVersion id."""

        return self.label_version.label_version_id

    @property
    def label_id(self) -> str:
        """Return the label contract id."""

        return self.label_contract.label_id

    @property
    def label_spec_id(self) -> str:
        """Return the governed LabelSpec id."""

        return self.label_contract.label_spec_id

    @property
    def exposure_status(self) -> str:
        """Return the compact duplicate/equivalent exposure status."""

        return self.exposure_report.status

    @property
    def producer_engine_id(self) -> str | None:
        """Return producer provenance recorded with this materialization."""

        metadata = self.registry_metadata.to_dict()
        value = metadata.get("producer_engine_id")
        if isinstance(value, str) and value.strip():
            return value
        lineage = self.lineage.contract_provenance.to_dict()
        value = lineage.get("producer_engine_id")
        return value if isinstance(value, str) and value.strip() else None

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible registry payload."""

        return {
            "schema": LABEL_REGISTRY_SCHEMA,
            "label_version": self.label_version.to_dict(),
            "label_contract": self.label_contract.to_contract_dict(),
            "label_id": self.label_id,
            "label_spec_id": self.label_spec_id,
            "lineage": self.lineage.to_dict(),
            "lifecycle_state": self.lifecycle_state.value,
            "exposure_status": self.exposure_status,
            "exposure_report": self.exposure_report.to_dict(),
            "materialization": {
                "plan_id": self.materialization_plan_id,
                "dataset_version_id": self.dataset_version_id,
                "partition_id": self.partition_id,
                "output_path": self.materialization_output_path,
                "value_store_format": self.value_store_format,
                "parquet_path": self.parquet_path,
                "value_content_hash": self.value_content_hash,
                "value_schema_version": self.value_schema_version,
                "value_record_count": self.value_record_count,
                "first_event_ts": self.first_event_ts.isoformat(),
                "last_event_ts": self.last_event_ts.isoformat(),
                "first_label_available_ts": self.first_label_available_ts.isoformat(),
                "last_label_available_ts": self.last_label_available_ts.isoformat(),
            },
            "registered_at": self.registered_at.isoformat(),
            "registry_metadata": self.registry_metadata.to_dict(),
        }

    def __hash__(self) -> int:
        return hash((self.label_version_id, self.lifecycle_state))


@dataclass(frozen=True, slots=True)
class LabelDeprecationRecord:
    """Retirement metadata for a registered label version."""

    label_version_id: str
    deprecated_at: datetime
    deprecated_by: str
    reason: str
    replacement_label_version_id: str = ""
    deprecation_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label_version_id",
            _require_label_version_id(self.label_version_id),
        )
        object.__setattr__(
            self,
            "deprecated_at",
            _require_aware_datetime(self.deprecated_at, "deprecated_at"),
        )
        object.__setattr__(
            self,
            "deprecated_by",
            _require_text(self.deprecated_by, "deprecated_by"),
        )
        object.__setattr__(self, "reason", _require_text(self.reason, "reason"))
        replacement = _optional_label_version_id(self.replacement_label_version_id)
        if replacement == self.label_version_id:
            raise LabelRegistryError("replacement_label_version_id must differ")
        object.__setattr__(self, "replacement_label_version_id", replacement)
        object.__setattr__(
            self,
            "deprecation_metadata",
            _freeze_json_mapping(self.deprecation_metadata, "deprecation_metadata"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible deprecation payload."""

        return {
            "schema": LABEL_DEPRECATION_SCHEMA,
            "label_version_id": self.label_version_id,
            "deprecated_at": self.deprecated_at.isoformat(),
            "deprecated_by": self.deprecated_by,
            "reason": self.reason,
            "replacement_label_version_id": self.replacement_label_version_id,
            "deprecation_metadata": self.deprecation_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class _ValueSummary:
    count: int
    first_event_ts: datetime
    last_event_ts: datetime
    first_label_available_ts: datetime
    last_label_available_ts: datetime


class LabelRegistry:
    """SQLite-backed local registry for label metadata and lineage."""

    def __init__(
        self,
        registry_path: str | Path | None = None,
        *,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if registry_path is None:
            registry_path = default_label_registry_path(
                alpha_data_root=alpha_data_root,
                env=env,
            )
        self.registry_path = _require_registry_path(registry_path)
        with self._connect() as connection:
            _ensure_schema(connection)

    @classmethod
    def from_alpha_data_root(
        cls,
        alpha_data_root: str | Path | None = None,
        *,
        env: Mapping[str, str] | None = None,
    ) -> LabelRegistry:
        """Build a registry at ``$ALPHA_DATA_ROOT/registry/labels.sqlite``."""

        return cls(alpha_data_root=alpha_data_root, env=env)

    def register_materialized_label(
        self,
        materialization_result: LabelMaterializationResult,
        *,
        label_contract: LabelContractSpec,
        label_version: LabelVersion,
        lineage: LabelLineageRecord | None = None,
        registry_metadata: Mapping[str, Any] | None = None,
    ) -> LabelRegistryRecord:
        """Register one materialized label version after fail-closed checks."""

        result = _require_materialization_result(materialization_result)
        contract = _require_validated_label_contract(label_contract)
        version = _require_matching_label_version(label_version, contract)
        lineage_record = _bind_lineage(contract, version, lineage)
        existing = self.resolve_label(version.label_version_id)
        if existing is not None:
            _require_existing_record_matches(existing, contract, version, lineage_record)
            summary = _summarize_materialized_values(result, contract, version)
            output_path = _materialization_output_path(result)
            value_store = _value_store_metadata(result)
            return self._persist_label(
                LabelRegistryRecord(
                    label_version=version,
                    label_contract=contract,
                    lineage=lineage_record,
                    exposure_report=existing.exposure_report,
                    materialization_plan_id=result.plan.plan_id,
                    dataset_version_id=result.plan.dataset_version_id,
                    partition_id=result.plan.partition_id,
                    materialization_output_path=output_path.as_posix(),
                    value_store_format=value_store["value_store_format"],
                    parquet_path=value_store["parquet_path"],
                    value_content_hash=value_store["value_content_hash"],
                    value_schema_version=value_store["value_schema_version"],
                    value_record_count=summary.count,
                    first_event_ts=summary.first_event_ts,
                    last_event_ts=summary.last_event_ts,
                    first_label_available_ts=summary.first_label_available_ts,
                    last_label_available_ts=summary.last_label_available_ts,
                    registered_at=existing.registered_at,
                    lifecycle_state=existing.lifecycle_state,
                    registry_metadata=existing.registry_metadata,
                )
            )

        summary = _summarize_materialized_values(result, contract, version)
        output_path = _materialization_output_path(result)
        value_store = _value_store_metadata(result)
        record = LabelRegistryRecord(
            label_version=version,
            label_contract=contract,
            lineage=lineage_record,
            exposure_report=self.build_exposure_report(contract, version),
            materialization_plan_id=result.plan.plan_id,
            dataset_version_id=result.plan.dataset_version_id,
            partition_id=result.plan.partition_id,
            materialization_output_path=output_path.as_posix(),
            value_store_format=value_store["value_store_format"],
            parquet_path=value_store["parquet_path"],
            value_content_hash=value_store["value_content_hash"],
            value_schema_version=value_store["value_schema_version"],
            value_record_count=summary.count,
            first_event_ts=summary.first_event_ts,
            last_event_ts=summary.last_event_ts,
            first_label_available_ts=summary.first_label_available_ts,
            last_label_available_ts=summary.last_label_available_ts,
            registered_at=datetime.now(UTC),
            registry_metadata=registry_metadata or {},
        )
        return self._persist_label(record)

    def _persist_label(self, record: LabelRegistryRecord) -> LabelRegistryRecord:
        """Persist one label registry record idempotently."""

        if not isinstance(record, LabelRegistryRecord):
            raise LabelRegistryError("_persist_label requires a LabelRegistryRecord")
        payload = _record_json(record)
        with self._connect() as connection:
            _ensure_schema(connection)
            existing = _fetch_record_row(connection, record.label_version_id)
            if existing is not None:
                return _record_from_row(existing)
            connection.execute(
                """
                INSERT INTO label_registry_records (
                    label_version_id,
                    label_id,
                    label_spec_id,
                    lifecycle_state,
                    materialization_plan_id,
                    dataset_version_id,
                    partition_id,
                    materialization_output_path,
                    value_store_format,
                    parquet_path,
                    value_content_hash,
                    value_schema_version,
                    value_record_count,
                    first_event_ts,
                    last_event_ts,
                    first_label_available_ts,
                    last_label_available_ts,
                    exposure_status,
                    registered_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.label_version_id,
                    record.label_id,
                    record.label_spec_id,
                    record.lifecycle_state.value,
                    record.materialization_plan_id,
                    record.dataset_version_id,
                    record.partition_id,
                    record.materialization_output_path,
                    record.value_store_format,
                    record.parquet_path,
                    record.value_content_hash,
                    record.value_schema_version,
                    record.value_record_count,
                    record.first_event_ts.isoformat(),
                    record.last_event_ts.isoformat(),
                    record.first_label_available_ts.isoformat(),
                    record.last_label_available_ts.isoformat(),
                    record.exposure_status,
                    record.registered_at.isoformat(),
                    payload,
                ),
            )
            connection.execute(
                """
                INSERT INTO label_lineage_records (
                    label_version_id,
                    label_spec_id,
                    metadata_json
                )
                VALUES (?, ?, ?)
                ON CONFLICT(label_version_id) DO UPDATE SET
                    label_spec_id = excluded.label_spec_id,
                    metadata_json = excluded.metadata_json
                """,
                (
                    record.label_version_id,
                    record.label_spec_id,
                    _lineage_json(record.lineage),
                ),
            )
        return record

    def resolve_label(
        self,
        label_version_id: object,
        *,
        include_deprecated: bool = True,
    ) -> LabelRegistryRecord | None:
        """Resolve one label by deterministic LabelVersion id.

        By default this is the raw by-id audit/deprecation-tooling path and
        returns deprecated rows. Runtime code should use the explicit
        registered/active resolver or enforce the returned lifecycle state.
        """

        version_id = _require_label_version_id(label_version_id)
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = _fetch_record_row(connection, version_id)
        if row is None:
            return None
        record = _record_from_row(row)
        if (
            not include_deprecated
            and record.lifecycle_state is not LabelRegistryLifecycleState.REGISTERED
        ):
            return None
        return record

    def resolve_label_by_version(
        self,
        label_version_id: object,
        *,
        include_deprecated: bool = True,
    ) -> LabelRegistryRecord | None:
        """Resolve one label by deterministic LabelVersion id."""

        return self.resolve_label(
            label_version_id,
            include_deprecated=include_deprecated,
        )

    def resolve_registered_label(
        self,
        label_version_id: object,
    ) -> LabelRegistryRecord | None:
        """Resolve a runtime-admissible REGISTERED label by id."""

        return self.resolve_label(label_version_id, include_deprecated=False)

    def resolve_active_label(self, label_version_id: object) -> LabelRegistryRecord | None:
        """Alias for REGISTERED-only label resolution."""

        return self.resolve_registered_label(label_version_id)

    def resolve_lineage(self, label_version_id: object) -> LabelLineageRecord | None:
        """Resolve lineage for one registered label version."""

        version_id = _require_label_version_id(label_version_id)
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = connection.execute(
                """
                SELECT metadata_json
                FROM label_lineage_records
                WHERE label_version_id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return _lineage_from_json(str(row["metadata_json"]))

    def deprecate_label(
        self,
        label_version_id: object,
        *,
        reason: object,
        deprecated_by: object,
        replacement_label_version_id: object = "",
        deprecated_at: datetime | None = None,
        deprecation_metadata: Mapping[str, Any] | None = None,
    ) -> LabelDeprecationRecord:
        """Mark a label version deprecated without deleting lineage."""

        version_id = _require_label_version_id(label_version_id)
        deprecation = LabelDeprecationRecord(
            label_version_id=version_id,
            deprecated_at=deprecated_at or datetime.now(UTC),
            deprecated_by=_require_text(deprecated_by, "deprecated_by"),
            reason=_require_text(reason, "reason"),
            replacement_label_version_id=_optional_label_version_id(
                replacement_label_version_id
            ),
            deprecation_metadata=deprecation_metadata or {},
        )
        payload = _deprecation_json(deprecation)
        with self._connect() as connection:
            _ensure_schema(connection)
            row = _fetch_record_row(connection, version_id)
            if row is None:
                raise LabelRegistryError(
                    f"cannot deprecate unregistered label version: {version_id}"
                )
            existing_deprecation = connection.execute(
                """
                SELECT metadata_json
                FROM label_deprecation_records
                WHERE label_version_id = ?
                """,
                (version_id,),
            ).fetchone()
            if existing_deprecation is not None:
                return _deprecation_from_json(str(existing_deprecation["metadata_json"]))
            record = _record_from_row(row)
            deprecated_record = replace(
                record,
                lifecycle_state=LabelRegistryLifecycleState.DEPRECATED,
            )
            connection.execute(
                """
                UPDATE label_registry_records
                SET lifecycle_state = ?,
                    metadata_json = ?
                WHERE label_version_id = ?
                """,
                (
                    LabelRegistryLifecycleState.DEPRECATED.value,
                    _record_json(deprecated_record),
                    version_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO label_deprecation_records (
                    label_version_id,
                    deprecated_at,
                    reason,
                    replacement_label_version_id,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    deprecation.deprecated_at.isoformat(),
                    deprecation.reason,
                    deprecation.replacement_label_version_id,
                    payload,
                ),
            )
        return deprecation

    def resolve_deprecation(
        self,
        label_version_id: object,
    ) -> LabelDeprecationRecord | None:
        """Resolve a deprecation record by label version id."""

        version_id = _require_label_version_id(label_version_id)
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = connection.execute(
                """
                SELECT metadata_json
                FROM label_deprecation_records
                WHERE label_version_id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return _deprecation_from_json(str(row["metadata_json"]))

    def is_deprecated(self, label_version_id: object) -> bool:
        """Return whether a registered label version has been deprecated."""

        record = self.resolve_label(label_version_id)
        return (
            record is not None
            and record.lifecycle_state is LabelRegistryLifecycleState.DEPRECATED
        )

    def build_exposure_report(
        self,
        label_contract: LabelContractSpec,
        label_version: LabelVersion,
    ) -> LabelExposureReport:
        """Build duplicate/equivalent label exposure metadata from registry rows."""

        contract = _require_validated_label_contract(label_contract)
        version = _require_matching_label_version(label_version, contract)
        existing_records = self.read_label_records()
        duplicate_ids: list[str] = []
        equivalent_ids: list[str] = []
        incoming_key = _equivalence_key(contract)
        for existing in existing_records:
            if existing.label_version_id == version.label_version_id:
                continue
            if existing.label_id == contract.label_id:
                duplicate_ids.append(existing.label_version_id)
                continue
            if _equivalence_key(existing.label_contract) == incoming_key:
                equivalent_ids.append(existing.label_version_id)
        return LabelExposureReport(
            registry_entries_checked=len(existing_records),
            duplicate_label_version_ids=tuple(sorted(duplicate_ids)),
            equivalent_label_version_ids=tuple(sorted(equivalent_ids)),
            rationale=(
                "label_id duplicates and equivalent label contract exposure are recorded "
                "for registry audit; label values are not copied into SQLite"
            ),
        )

    def read_label_versions(self) -> list[dict[str, object]]:
        """Expose a read-only duplicate/equivalent guard view over labels."""

        return [_label_registry_entry(record) for record in self.read_label_records()]

    def read_label_records(self) -> tuple[LabelRegistryRecord, ...]:
        """Return registered label metadata records ordered by label id and version."""

        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT metadata_json
                FROM label_registry_records
                ORDER BY label_id, label_version_id
                """
            ).fetchall()
        return tuple(_record_from_json(str(row["metadata_json"])) for row in rows)

    def count_label_records(self) -> int:
        """Return the number of persisted label registry rows."""

        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = connection.execute(
                "SELECT count(*) AS count FROM label_registry_records"
            ).fetchone()
        return int(row["count"])

    def _connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        if read_only and self.registry_path.exists():
            connection = sqlite3.connect(
                f"file:{self.registry_path.as_posix()}?mode=ro",
                uri=True,
            )
        else:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.registry_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def default_label_registry_path(
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Return the default local-only label registry path."""

    source = os.environ if env is None else env
    root_value = alpha_data_root if alpha_data_root is not None else source.get("ALPHA_DATA_ROOT")
    if root_value is None:
        raise LabelRegistryError("ALPHA_DATA_ROOT is required for LabelRegistry")
    root = _require_path(root_value, "ALPHA_DATA_ROOT")
    _require_outside_repo(root, "ALPHA_DATA_ROOT")
    return root / DEFAULT_LABEL_REGISTRY_RELATIVE_PATH


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS label_registry_records (
            label_version_id TEXT PRIMARY KEY,
            label_id TEXT NOT NULL,
            label_spec_id TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            materialization_plan_id TEXT NOT NULL,
            dataset_version_id TEXT NOT NULL,
            partition_id TEXT NOT NULL,
            materialization_output_path TEXT NOT NULL,
            value_store_format TEXT NOT NULL DEFAULT 'jsonl',
            parquet_path TEXT,
            value_content_hash TEXT,
            value_schema_version TEXT,
            value_record_count INTEGER NOT NULL,
            first_event_ts TEXT NOT NULL,
            last_event_ts TEXT NOT NULL,
            first_label_available_ts TEXT NOT NULL,
            last_label_available_ts TEXT NOT NULL,
            exposure_status TEXT NOT NULL,
            registered_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        )
        """
    )
    _backfill_columns(
        connection,
        "label_registry_records",
        {
            "value_store_format": "TEXT NOT NULL DEFAULT 'jsonl'",
            "parquet_path": "TEXT",
            "value_content_hash": "TEXT",
            "value_schema_version": "TEXT",
        },
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS label_lineage_records (
            label_version_id TEXT PRIMARY KEY,
            label_spec_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            FOREIGN KEY(label_version_id)
                REFERENCES label_registry_records(label_version_id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS label_deprecation_records (
            label_version_id TEXT PRIMARY KEY,
            deprecated_at TEXT NOT NULL,
            reason TEXT NOT NULL,
            replacement_label_version_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            FOREIGN KEY(label_version_id)
                REFERENCES label_registry_records(label_version_id)
                ON DELETE RESTRICT
        )
        """
    )


def _backfill_columns(
    connection: sqlite3.Connection,
    table_name: str,
    columns: Mapping[str, str],
) -> None:
    existing = {
        str(row["name"] if isinstance(row, sqlite3.Row) else row[1])
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_spec in columns.items():
        if column_name not in existing:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}")


def _fetch_record_row(
    connection: sqlite3.Connection,
    label_version_id: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM label_registry_records
        WHERE label_version_id = ?
        """,
        (label_version_id,),
    ).fetchone()


def _record_json(record: LabelRegistryRecord) -> str:
    return canonical_serialize(record.to_dict())


def _lineage_json(lineage: LabelLineageRecord) -> str:
    return canonical_serialize({"schema": LABEL_REGISTRY_SCHEMA, "lineage": lineage.to_dict()})


def _deprecation_json(record: LabelDeprecationRecord) -> str:
    return canonical_serialize(record.to_dict())


def _record_from_row(row: sqlite3.Row) -> LabelRegistryRecord:
    record = _record_from_json(str(row["metadata_json"]))
    keys = set(row.keys())
    return replace(
        record,
        value_store_format=(
            row["value_store_format"]
            if "value_store_format" in keys and row["value_store_format"] is not None
            else record.value_store_format
        ),
        parquet_path=(
            row["parquet_path"]
            if "parquet_path" in keys and row["parquet_path"] is not None
            else record.parquet_path
        ),
        value_content_hash=(
            row["value_content_hash"]
            if "value_content_hash" in keys and row["value_content_hash"] is not None
            else record.value_content_hash
        ),
        value_schema_version=(
            row["value_schema_version"]
            if "value_schema_version" in keys and row["value_schema_version"] is not None
            else record.value_schema_version
        ),
    )


def _record_from_json(text: str) -> LabelRegistryRecord:
    payload = _loads_mapping(text, "LabelRegistryRecord")
    if payload.get("schema") != LABEL_REGISTRY_SCHEMA:
        raise LabelRegistryError("label registry record schema is unsupported")
    label_contract = _label_contract_from_payload(
        _mapping_payload(payload.get("label_contract"), "label_contract")
    )
    label_version = _label_version_from_payload(
        _mapping_payload(payload.get("label_version"), "label_version")
    )
    lineage_payload = _mapping_payload(payload.get("lineage"), "lineage")
    materialization = _mapping_payload(payload.get("materialization"), "materialization")
    return LabelRegistryRecord(
        label_version=label_version,
        label_contract=label_contract,
        lineage=LabelLineageRecord(
            label_version=label_version,
            label_contract=label_contract,
            label_spec_id=_require_text(
                lineage_payload.get("label_spec_id"),
                "lineage.label_spec_id",
            ),
            contract_provenance=_mapping_payload(
                lineage_payload.get("contract_provenance", {}),
                "lineage.contract_provenance",
            ),
        ),
        exposure_report=_exposure_report_from_payload(
            _mapping_payload(payload.get("exposure_report"), "exposure_report")
        ),
        materialization_plan_id=_require_text(
            materialization.get("plan_id"),
            "materialization.plan_id",
        ),
        dataset_version_id=_require_text(
            materialization.get("dataset_version_id"),
            "materialization.dataset_version_id",
        ),
        partition_id=_require_text(
            materialization.get("partition_id"),
            "materialization.partition_id",
        ),
        materialization_output_path=_require_text(
            materialization.get("output_path"),
            "materialization.output_path",
        ),
        value_store_format=_coerce_value_store_format(
            materialization.get("value_store_format", ValueStoreFormat.JSONL.value)
        ).value,
        parquet_path=_optional_text_or_none(
            materialization.get("parquet_path"),
            "materialization.parquet_path",
        ),
        value_content_hash=_optional_text_or_none(
            materialization.get("value_content_hash"),
            "materialization.value_content_hash",
        ),
        value_schema_version=_optional_text_or_none(
            materialization.get("value_schema_version"),
            "materialization.value_schema_version",
        ),
        value_record_count=_require_positive_int(
            materialization.get("value_record_count"),
            "materialization.value_record_count",
        ),
        first_event_ts=_datetime_from_payload(
            materialization.get("first_event_ts"),
            "materialization.first_event_ts",
        ),
        last_event_ts=_datetime_from_payload(
            materialization.get("last_event_ts"),
            "materialization.last_event_ts",
        ),
        first_label_available_ts=_datetime_from_payload(
            materialization.get("first_label_available_ts"),
            "materialization.first_label_available_ts",
        ),
        last_label_available_ts=_datetime_from_payload(
            materialization.get("last_label_available_ts"),
            "materialization.last_label_available_ts",
        ),
        registered_at=_datetime_from_payload(payload.get("registered_at"), "registered_at"),
        lifecycle_state=_require_text(payload.get("lifecycle_state"), "lifecycle_state"),
        registry_metadata=_mapping_payload(
            payload.get("registry_metadata", {}),
            "registry_metadata",
        ),
    )


def _lineage_from_json(text: str) -> LabelLineageRecord:
    payload = _loads_mapping(text, "LabelLineageRecord")
    if payload.get("schema") != LABEL_REGISTRY_SCHEMA:
        raise LabelRegistryError("label lineage schema is unsupported")
    lineage_payload = _mapping_payload(payload.get("lineage"), "lineage")
    label_contract = _label_contract_from_payload(
        _mapping_payload(lineage_payload.get("label_contract"), "lineage.label_contract")
    )
    label_version = _label_version_from_payload(
        _mapping_payload(lineage_payload.get("label_version"), "lineage.label_version")
    )
    return LabelLineageRecord(
        label_version=label_version,
        label_contract=label_contract,
        label_spec_id=_require_text(lineage_payload.get("label_spec_id"), "lineage.label_spec_id"),
        contract_provenance=_mapping_payload(
            lineage_payload.get("contract_provenance", {}),
            "lineage.contract_provenance",
        ),
    )


def _deprecation_from_json(text: str) -> LabelDeprecationRecord:
    payload = _loads_mapping(text, "LabelDeprecationRecord")
    if payload.get("schema") != LABEL_DEPRECATION_SCHEMA:
        raise LabelRegistryError("label deprecation schema is unsupported")
    return LabelDeprecationRecord(
        label_version_id=_require_text(payload.get("label_version_id"), "label_version_id"),
        deprecated_at=_datetime_from_payload(payload.get("deprecated_at"), "deprecated_at"),
        deprecated_by=_require_text(payload.get("deprecated_by"), "deprecated_by"),
        reason=_require_text(payload.get("reason"), "reason"),
        replacement_label_version_id=_optional_label_version_id(
            payload.get("replacement_label_version_id", "")
        ),
        deprecation_metadata=_mapping_payload(
            payload.get("deprecation_metadata", {}),
            "deprecation_metadata",
        ),
    )


def _label_contract_from_payload(payload: Mapping[str, object]) -> LabelContractSpec:
    inputs = _mapping_payload(payload.get("inputs"), "label_contract.inputs")
    horizon = _mapping_payload(payload.get("horizon"), "label_contract.horizon")
    path = _mapping_payload(payload.get("path"), "label_contract.path")
    barriers = _mapping_payload(payload.get("barriers"), "label_contract.barriers")
    cost = _mapping_payload(payload.get("cost_adjustment"), "label_contract.cost_adjustment")
    availability = _mapping_payload(
        payload.get("availability_policy"),
        "label_contract.availability_policy",
    )
    return LabelContractSpec(
        label_id=_require_text(payload.get("label_id"), "label_contract.label_id"),
        family=_require_text(payload.get("family"), "label_contract.family"),
        governance_label_spec=_mapping_payload(
            payload.get("governance_label_spec"),
            "label_contract.governance_label_spec",
        ),
        inputs=LabelInputSpec(
            input_views=_text_tuple_payload(
                _sequence_payload(inputs.get("input_views"), "inputs.input_views")
            ),
            fields=_text_tuple_payload(_sequence_payload(inputs.get("fields"), "inputs.fields")),
            dataset_version_ids=_text_tuple_payload(
                _sequence_payload(
                    inputs.get("dataset_version_ids", ()),
                    "inputs.dataset_version_ids",
                )
            ),
            input_metadata=_mapping_payload(
                inputs.get("input_metadata", {}),
                "inputs.input_metadata",
            ),
        ),
        horizon=LabelHorizonSpec(
            horizon=_require_text(horizon.get("horizon"), "horizon.horizon"),
            horizon_end_rule=_require_text(
                horizon.get("horizon_end_rule"),
                "horizon.horizon_end_rule",
            ),
            parameters=_mapping_payload(horizon.get("parameters", {}), "horizon.parameters"),
        ),
        path=LabelPathSpec(
            path_rules=_mapping_payload(path.get("path_rules"), "path.path_rules"),
            uses_forward_data=_require_bool(
                path.get("uses_forward_data"),
                "path.uses_forward_data",
            ),
            window=_window_from_payload(path.get("window")),
            parameters=_mapping_payload(path.get("parameters", {}), "path.parameters"),
        ),
        barriers=BarrierSpec(
            target_stop_rules=_mapping_payload(
                barriers.get("target_stop_rules"),
                "barriers.target_stop_rules",
            )
        ),
        cost_adjustment=CostAdjustmentSpec(
            cost_model=_mapping_payload(cost.get("cost_model"), "cost_adjustment.cost_model")
        ),
        availability_policy=LabelAvailabilityPolicy(
            availability_time=_require_text(
                availability.get("availability_time"),
                "availability.availability_time",
            ),
            label_available_ts_derivation_rule=_require_text(
                availability.get("label_available_ts_derivation_rule"),
                "availability.label_available_ts_derivation_rule",
            ),
            forbidden_feature_overlap=_mapping_payload(
                availability.get("forbidden_feature_overlap"),
                "availability.forbidden_feature_overlap",
            ),
            leakage_checks=_text_tuple_payload(
                _sequence_payload(availability.get("leakage_checks"), "availability.leakage_checks")
            ),
            forward_data_allowed=_require_bool(
                availability.get("forward_data_allowed"),
                "availability.forward_data_allowed",
            ),
            legal_consumer=_require_text(
                availability.get("legal_consumer"),
                "availability.legal_consumer",
            ),
        ),
        contract_metadata=_mapping_payload(
            payload.get("contract_metadata", {}),
            "label_contract.contract_metadata",
        ),
    )


def _window_from_payload(value: object) -> WindowSpec | None:
    if value is None:
        return None
    payload = _mapping_payload(value, "path.window")
    return WindowSpec(
        kind=_require_text(payload.get("kind"), "path.window.kind"),
        length=_require_positive_int(payload.get("length"), "path.window.length"),
        causality=_require_text(payload.get("causality"), "path.window.causality"),
        offline_only=_require_bool(payload.get("offline_only"), "path.window.offline_only"),
        anchor=_require_text(payload.get("anchor", "available_ts"), "path.window.anchor"),
        parameters=_mapping_payload(payload.get("parameters", {}), "path.window.parameters"),
    )


def _label_version_from_payload(payload: Mapping[str, object]) -> LabelVersion:
    return LabelVersion(
        label_version_id=_require_text(payload.get("label_version_id"), "label_version_id"),
        content_hash=_require_text(payload.get("content_hash"), "content_hash"),
        algorithm=_require_text(payload.get("algorithm"), "algorithm"),
    )


def _exposure_report_from_payload(payload: Mapping[str, object]) -> LabelExposureReport:
    return LabelExposureReport(
        registry_entries_checked=_require_nonnegative_int(
            payload.get("registry_entries_checked"),
            "registry_entries_checked",
        ),
        duplicate_label_version_ids=_text_tuple_payload(
            _sequence_payload(
                payload.get("duplicate_label_version_ids", ()),
                "duplicate_label_version_ids",
            )
        ),
        equivalent_label_version_ids=_text_tuple_payload(
            _sequence_payload(
                payload.get("equivalent_label_version_ids", ()),
                "equivalent_label_version_ids",
            )
        ),
        rationale=_require_text(payload.get("rationale"), "rationale"),
    )


def _label_registry_entry(record: LabelRegistryRecord) -> dict[str, object]:
    key = _equivalence_key(record.label_contract)
    return {
        "label_id": record.label_id,
        "label_version": record.label_version_id,
        "label_spec_id": record.label_spec_id,
        "name": record.label_id,
        "metadata": {
            "label_version_id": record.label_version_id,
            "lifecycle_state": record.lifecycle_state.value,
            "dataset_version_id": record.dataset_version_id,
            "partition_id": record.partition_id,
            "exposure_status": record.exposure_status,
            "family": record.label_contract.family.value,
            "horizon": key["horizon"],
        },
        "parameters": key,
    }


def _require_validated_label_contract(label_contract: LabelContractSpec) -> LabelContractSpec:
    if not isinstance(label_contract, LabelContractSpec):
        raise LabelRegistryError("registration requires a LabelContractSpec")
    if not label_contract.label_spec_id.startswith("lspec_"):
        raise LabelRegistryError("LabelContractSpec must carry a governed lspec_ binding")
    if not label_contract.availability_policy.future_data_legal_only_for_labels:
        raise LabelRegistryError("future-looking data is legal only for labels")
    if (
        label_contract.availability_policy.legal_consumer
        is not LabelAvailabilityConsumer.LABELS_ONLY
    ):
        raise LabelRegistryError("labels cannot be exposed as live feature inputs")
    if "label_available_ts" not in (
        label_contract.availability_policy.label_available_ts_derivation_rule.lower()
    ):
        raise LabelRegistryError("label_available_ts derivation rule is required")
    return label_contract


def _require_matching_label_version(
    label_version: LabelVersion,
    label_contract: LabelContractSpec,
) -> LabelVersion:
    if not isinstance(label_version, LabelVersion):
        raise LabelRegistryError("registration requires a LabelVersion")
    if label_version != label_contract.derive_label_version():
        raise LabelRegistryError("LabelVersion must match LabelContractSpec content")
    return label_version


def _bind_lineage(
    label_contract: LabelContractSpec,
    label_version: LabelVersion,
    lineage: LabelLineageRecord | None,
) -> LabelLineageRecord:
    if lineage is None:
        return LabelLineageRecord(
            label_version=label_version,
            label_contract=label_contract,
            label_spec_id=label_contract.label_spec_id,
            contract_provenance={"bound_by": "LabelRegistry"},
        )
    if not isinstance(lineage, LabelLineageRecord):
        raise LabelRegistryError("lineage must be a LabelLineageRecord")
    if lineage.label_version != label_version:
        raise LabelRegistryError("lineage LabelVersion does not match registration")
    if lineage.label_contract != label_contract:
        raise LabelRegistryError("lineage LabelContractSpec does not match registration")
    if lineage.label_spec_id != label_contract.label_spec_id:
        raise LabelRegistryError("lineage LabelSpec id does not match registration")
    return lineage


def _require_existing_record_matches(
    existing: LabelRegistryRecord,
    label_contract: LabelContractSpec,
    label_version: LabelVersion,
    lineage: LabelLineageRecord,
) -> None:
    if existing.label_version != label_version:
        raise LabelRegistryError("existing registry record has a mismatched LabelVersion")
    if existing.label_contract != label_contract:
        raise LabelRegistryError("existing registry record has a mismatched LabelContractSpec")
    if existing.lineage != lineage:
        raise LabelRegistryError("existing registry record has a mismatched lineage")


def _summarize_materialized_values(
    materialization_result: LabelMaterializationResult,
    label_contract: LabelContractSpec,
    label_version: LabelVersion,
) -> _ValueSummary:
    result = _require_materialization_result(materialization_result)
    _require_materialization_plan(result.plan)
    if result.dry_run:
        raise LabelRegistryError("dry-run materialization results cannot be registered")
    if result.plan.label_lifecycle_state != LABEL_MATERIALIZATION_ALLOWED:
        raise LabelRegistryError("LabelSpec lifecycle gate must be MATERIALIZATION_ALLOWED")
    if result.plan.legal_consumer != LabelAvailabilityConsumer.LABELS_ONLY.value:
        raise LabelRegistryError("labels cannot be exposed as live feature inputs")
    if label_version.label_version_id not in result.plan.label_version_ids:
        raise LabelRegistryError("LabelVersion is not in the materialization plan")
    plan_contracts = {
        contract.derive_label_version().label_version_id: contract
        for contract in result.plan.label_contracts
    }
    if plan_contracts.get(label_version.label_version_id) != label_contract:
        raise LabelRegistryError("materialization plan contract does not match registration")
    if label_contract.label_spec_id not in result.plan.label_spec_ids:
        raise LabelRegistryError("LabelSpec lspec_ binding is not in the materialization plan")
    records = tuple(
        record
        for record in result.records
        if getattr(record, "label_version_id", None) == label_version.label_version_id
    )
    if not records:
        raise LabelRegistryError("registration requires materialized LabelValueRecords")
    for record in records:
        if not isinstance(record, LabelValueRecord):
            raise LabelRegistryError("materialization result contains a non-LabelValueRecord")
        event_ts = _require_aware_datetime(record.event_ts, "LabelValueRecord.event_ts")
        horizon_end_ts = _require_aware_datetime(
            record.horizon_end_ts,
            "LabelValueRecord.horizon_end_ts",
        )
        label_available_ts = _require_aware_datetime(
            record.label_available_ts,
            "LabelValueRecord.label_available_ts",
        )
        if record.label_spec_id != label_contract.label_spec_id:
            raise LabelRegistryError("LabelValueRecord label_spec_id must match LabelContractSpec")
        if horizon_end_ts < event_ts:
            raise LabelRegistryError("LabelValueRecord.horizon_end_ts must not precede event_ts")
        if label_available_ts < horizon_end_ts:
            raise LabelRegistryError(
                "LabelValueRecord.label_available_ts must be at or after horizon_end_ts"
            )
        if label_available_ts < label_contract.availability_policy.availability_time:
            raise LabelRegistryError(
                "LabelValueRecord.label_available_ts must not precede LabelSpec.availability_time"
            )
    event_ts_values = tuple(record.event_ts for record in records)
    available_ts_values = tuple(record.label_available_ts for record in records)
    return _ValueSummary(
        count=len(records),
        first_event_ts=min(event_ts_values),
        last_event_ts=max(event_ts_values),
        first_label_available_ts=min(available_ts_values),
        last_label_available_ts=max(available_ts_values),
    )


def _materialization_output_path(materialization_result: LabelMaterializationResult) -> Path:
    result = _require_materialization_result(materialization_result)
    output_path = result.output_path or result.plan.output_path
    if output_path is None:
        raise LabelRegistryError("materialization result must expose an output path")
    path = Path(output_path).expanduser().resolve(strict=False)
    root = result.plan.alpha_data_root.expanduser().resolve(strict=False)
    if not path.is_relative_to(root):
        raise LabelRegistryError("materialization output path must stay under ALPHA_DATA_ROOT")
    return path


def _value_store_metadata(
    materialization_result: LabelMaterializationResult,
) -> dict[str, str | None]:
    handle = _require_materialization_result(materialization_result).value_store_handle
    if handle is None:
        return {
            "value_store_format": ValueStoreFormat.JSONL.value,
            "parquet_path": None,
            "value_content_hash": None,
            "value_schema_version": None,
        }
    return {
        "value_store_format": handle.format.value,
        "parquet_path": handle.parquet_path,
        "value_content_hash": handle.content_hash,
        "value_schema_version": handle.schema_version,
    }


def _require_materialization_result(
    materialization_result: LabelMaterializationResult,
) -> LabelMaterializationResult:
    if not isinstance(materialization_result, LabelMaterializationResult):
        raise LabelRegistryError(
            "registration requires a LabelMaterializationResult from the label engine"
        )
    return materialization_result


def _require_materialization_plan(plan: LabelMaterializationPlan) -> LabelMaterializationPlan:
    if not isinstance(plan, LabelMaterializationPlan):
        raise LabelRegistryError("registration requires a LabelMaterializationPlan")
    return plan


def _equivalence_key(label_contract: LabelContractSpec) -> dict[str, JsonValue]:
    """Return a label exposure signature that ignores version-only metadata."""

    return {
        "family": label_contract.family.value,
        "inputs": label_contract.inputs.to_dict(),
        "horizon": label_contract.horizon.to_dict(),
        "path": label_contract.path.to_dict(),
        "barriers": label_contract.barriers.to_dict(),
        "cost_adjustment": label_contract.cost_adjustment.to_dict(),
        "availability_policy": label_contract.availability_policy.to_dict(),
    }


def _loads_mapping(text: str, field_name: str) -> Mapping[str, object]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LabelRegistryError(f"{field_name} must be valid JSON") from exc
    return _mapping_payload(payload, field_name)


def _mapping_payload(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise LabelRegistryError(f"{field_name} must be a mapping")
    return value


def _sequence_payload(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, str) or not isinstance(value, list | tuple):
        raise LabelRegistryError(f"{field_name} must be a sequence")
    return tuple(value)


def _text_tuple_payload(values: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(_require_text(value, "sequence item") for value in values)


def _label_version_id_tuple(value: object, field_name: str) -> tuple[str, ...]:
    values = _sequence_payload(value, field_name)
    return tuple(_require_label_version_id(item) for item in values)


def _require_registry_path(path: str | Path) -> Path:
    resolved = resolve_registry_path(path)
    if not is_local_only_registry_path(resolved):
        raise LabelRegistryError("LabelRegistry path must be a local SQLite path")
    _require_outside_repo(resolved, "LabelRegistry path")
    return resolved


def _require_outside_repo(path: Path, field_name: str) -> None:
    repo_root = Path.cwd().resolve(strict=False)
    resolved = path.resolve(strict=False)
    if resolved == repo_root or resolved.is_relative_to(repo_root):
        raise LabelRegistryError(f"{field_name} must be outside the repository tree")


def _require_path(value: str | Path, field_name: str) -> Path:
    if not isinstance(value, str | Path):
        raise LabelRegistryError(f"{field_name} must be a path")
    try:
        return Path(value).expanduser().resolve(strict=False)
    except RuntimeError as exc:
        raise LabelRegistryError(f"{field_name} could not be resolved") from exc


def _coerce_lifecycle_state(
    value: LabelRegistryLifecycleState | str,
) -> LabelRegistryLifecycleState:
    text = _require_text(value, "lifecycle_state").upper()
    if text in PROHIBITED_LABEL_REGISTRY_STATES:
        raise LabelRegistryError(f"prohibited label lifecycle state: {text}")
    try:
        return LabelRegistryLifecycleState(text)
    except ValueError as exc:
        allowed = ", ".join(state.value for state in LabelRegistryLifecycleState)
        raise LabelRegistryError(f"lifecycle_state must be one of: {allowed}") from exc


def _coerce_value_store_format(value: object) -> ValueStoreFormat:
    try:
        if isinstance(value, ValueStoreFormat):
            return value
        return ValueStoreFormat(_require_text(value, "value_store_format"))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ValueStoreFormat)
        raise LabelRegistryError(f"value_store_format must be one of: {allowed}") from exc


def _freeze_json_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    if isinstance(value, FrozenJsonMapping):
        return value
    try:
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    except LabelContractError as exc:
        raise LabelRegistryError(str(exc)) from exc


def _require_text(value: object, field_name: str) -> str:
    if isinstance(value, StrEnum):
        value = value.value
    if not isinstance(value, str):
        raise LabelRegistryError(f"{field_name} must be a string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise LabelRegistryError(f"{field_name} must be a non-empty single-line string")
    return text


def _optional_text_or_none(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise LabelRegistryError(f"{field_name} must be a positive integer")
    return value


def _require_nonnegative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LabelRegistryError(f"{field_name} must be a non-negative integer")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise LabelRegistryError(f"{field_name} must be a bool")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LabelRegistryError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise LabelRegistryError(f"{field_name} must be timezone-aware")
    return value


def _datetime_from_payload(value: object, field_name: str) -> datetime:
    try:
        return _require_aware_datetime(
            datetime.fromisoformat(_require_text(value, field_name)),
            field_name,
        )
    except ValueError as exc:
        raise LabelRegistryError(f"{field_name} must be an ISO datetime") from exc


def _require_label_version_id(value: object) -> str:
    text = _require_text(value, "label_version_id")
    if LABEL_VERSION_PATTERN.fullmatch(text) is None:
        raise LabelRegistryError("label_version_id must be lver_<64-hex-content-hash>")
    return text


def _optional_label_version_id(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return _require_label_version_id(text)


__all__ = [
    "DEFAULT_LABEL_REGISTRY_RELATIVE_PATH",
    "LABEL_DEPRECATION_SCHEMA",
    "LABEL_REGISTRY_SCHEMA",
    "PROHIBITED_LABEL_REGISTRY_STATES",
    "LabelDeprecationRecord",
    "LabelExposureReport",
    "LabelRegistry",
    "LabelRegistryError",
    "LabelRegistryLifecycleState",
    "LabelRegistryRecord",
    "default_label_registry_path",
]
