"""Local-only FeatureRegistry persistence for registered feature metadata.

The registry stores feature metadata, lineage, duplicate-exposure reports, and
deprecation records. It deliberately does not store feature values.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.core.registry import is_local_only_registry_path, resolve_registry_path
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import (
    FEATURE_VERSION_PATTERN,
    FeatureContractError,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    FeatureVersion,
    FrozenJsonMapping,
    NormalizationSpec,
    TransformSpec,
    WindowSpec,
)
from alpha_system.features.request_gate import (
    DuplicateExposureReport,
    EquivalentFeatureGroup,
    FeatureRequestGateDecision,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureFindingKind,
    ExposureFindingSeverity,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import FeatureRequest, validate_feature_request
from alpha_system.governance.serialization import JsonValue, canonical_serialize

FEATURE_REGISTRY_SCHEMA = "alpha_system.features.registry.v1"
FEATURE_DEPRECATION_SCHEMA = "alpha_system.features.deprecation.v1"
DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH = Path("registry") / "features.sqlite"
REFERENCE_FEATURE_PRODUCER_ENGINE_ID = "alpha_system.features.reference.materializer.v1"
PROHIBITED_FEATURE_REGISTRY_STATES: frozenset[str] = frozenset(
    {
        "ALPHA_VALIDATED",
        "STRATEGY_READY",
        "LIVE_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
    }
)


class FeatureRegistryError(ValueError):
    """Raised when feature registry operations fail closed."""


class FeatureRegistryLifecycleState(StrEnum):
    """Narrow lifecycle states for registry discoverability only."""

    REGISTERED = "REGISTERED"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class FeatureRegistryRecord:
    """Versioned registry metadata for one governed feature."""

    feature_version: FeatureVersion
    feature_spec: FeatureSpec
    lineage: FeatureLineageRecord
    feature_request_payload: Mapping[str, Any] | FrozenJsonMapping
    duplicate_exposure_report: DuplicateExposureReport
    feature_set_id: str
    feature_set_version: str
    feature_set_ordinal: int
    materialization_plan_id: str
    dataset_version_id: str
    partition_id: str
    materialization_output_path: str
    value_record_count: int
    first_event_ts: datetime
    last_event_ts: datetime
    first_available_ts: datetime
    last_available_ts: datetime
    registered_at: datetime
    value_store_format: str = ValueStoreFormat.JSONL.value
    parquet_path: str | None = None
    value_content_hash: str | None = None
    producer_engine_id: str | None = None
    value_schema_version: str | None = None
    lifecycle_state: FeatureRegistryLifecycleState | str = (
        FeatureRegistryLifecycleState.REGISTERED
    )
    registry_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.feature_version, FeatureVersion):
            raise FeatureRegistryError("feature_version must be a FeatureVersion")
        if not isinstance(self.feature_spec, FeatureSpec):
            raise FeatureRegistryError("feature_spec must be a FeatureSpec")
        if not isinstance(self.lineage, FeatureLineageRecord):
            raise FeatureRegistryError("lineage must be a FeatureLineageRecord")
        expected_version = FeatureVersion.derive(self.feature_spec)
        if self.feature_version != expected_version:
            raise FeatureRegistryError("feature_version must match FeatureSpec content")
        if self.lineage.feature_version != self.feature_version:
            raise FeatureRegistryError("lineage must bind the same FeatureVersion")
        if self.lineage.feature_spec != self.feature_spec:
            raise FeatureRegistryError("lineage must bind the same FeatureSpec")
        if self.lineage.feature_request_id != self.feature_spec.feature_request_id:
            raise FeatureRegistryError("lineage feature_request_id must match FeatureSpec")
        if not isinstance(self.duplicate_exposure_report, DuplicateExposureReport):
            raise FeatureRegistryError(
                "duplicate_exposure_report must be a DuplicateExposureReport"
            )
        feature_request_payload = _freeze_json_mapping(
            self.feature_request_payload,
            "feature_request_payload",
        )
        feature_request = _feature_request_from_payload(feature_request_payload.to_dict())
        if feature_request.feature_request_id != self.feature_spec.feature_request_id:
            raise FeatureRegistryError(
                "feature_request_payload must match FeatureSpec.feature_request_id"
            )
        state = _coerce_lifecycle_state(self.lifecycle_state)
        value_record_count = _require_positive_int(
            self.value_record_count,
            "value_record_count",
        )
        first_event_ts = _require_aware_datetime(self.first_event_ts, "first_event_ts")
        last_event_ts = _require_aware_datetime(self.last_event_ts, "last_event_ts")
        first_available_ts = _require_aware_datetime(
            self.first_available_ts,
            "first_available_ts",
        )
        last_available_ts = _require_aware_datetime(
            self.last_available_ts,
            "last_available_ts",
        )
        if first_event_ts > last_event_ts:
            raise FeatureRegistryError("first_event_ts must not be after last_event_ts")
        if first_available_ts > last_available_ts:
            raise FeatureRegistryError(
                "first_available_ts must not be after last_available_ts"
            )
        object.__setattr__(self, "feature_request_payload", feature_request_payload)
        object.__setattr__(
            self,
            "feature_set_id",
            _require_text(self.feature_set_id, "feature_set_id"),
        )
        object.__setattr__(
            self,
            "feature_set_version",
            _require_text(self.feature_set_version, "feature_set_version"),
        )
        object.__setattr__(
            self,
            "feature_set_ordinal",
            _require_nonnegative_int(self.feature_set_ordinal, "feature_set_ordinal"),
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
        object.__setattr__(
            self,
            "partition_id",
            _require_text(self.partition_id, "partition_id"),
        )
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
            "producer_engine_id",
            _producer_engine_id_from_provenance(
                self.producer_engine_id,
                registry_metadata=self.registry_metadata,
                lineage_provenance=self.lineage.contract_provenance,
            ),
        )
        object.__setattr__(
            self,
            "value_schema_version",
            _optional_text_or_none(self.value_schema_version, "value_schema_version"),
        )
        object.__setattr__(self, "value_record_count", value_record_count)
        object.__setattr__(self, "first_event_ts", first_event_ts)
        object.__setattr__(self, "last_event_ts", last_event_ts)
        object.__setattr__(self, "first_available_ts", first_available_ts)
        object.__setattr__(self, "last_available_ts", last_available_ts)
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
    def feature_version_id(self) -> str:
        """Return the deterministic FeatureVersion id."""

        return self.feature_version.feature_version_id

    @property
    def feature_request_id(self) -> str:
        """Return the governed FeatureRequest id bound to this record."""

        return self.feature_spec.feature_request_id

    @property
    def duplicate_exposure_status(self) -> str:
        """Return a compact duplicate/equivalent exposure status."""

        if self.duplicate_exposure_report.has_blocking_findings:
            return "BLOCKING_RECORDED"
        if self.duplicate_exposure_report.has_findings:
            return "EQUIVALENCE_RECORDED"
        return "NO_FINDINGS"

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible registry payload."""

        return {
            "schema": FEATURE_REGISTRY_SCHEMA,
            "feature_version": self.feature_version.to_dict(),
            "feature_spec": self.feature_spec.to_contract_dict(),
            "feature_request_id": self.feature_request_id,
            "feature_request": self.feature_request_payload.to_dict(),
            "lineage": self.lineage.to_dict(),
            "lifecycle_state": self.lifecycle_state.value,
            "duplicate_exposure_status": self.duplicate_exposure_status,
            "duplicate_exposure_report": self.duplicate_exposure_report.to_dict(),
            "feature_set_membership": {
                "feature_set_id": self.feature_set_id,
                "feature_set_version": self.feature_set_version,
                "ordinal": self.feature_set_ordinal,
            },
            "materialization": {
                "plan_id": self.materialization_plan_id,
                "dataset_version_id": self.dataset_version_id,
                "partition_id": self.partition_id,
                "output_path": self.materialization_output_path,
                "value_store_format": self.value_store_format,
                "parquet_path": self.parquet_path,
                "value_content_hash": self.value_content_hash,
                "producer_engine_id": self.producer_engine_id,
                "value_schema_version": self.value_schema_version,
                "value_record_count": self.value_record_count,
                "first_event_ts": self.first_event_ts.isoformat(),
                "last_event_ts": self.last_event_ts.isoformat(),
                "first_available_ts": self.first_available_ts.isoformat(),
                "last_available_ts": self.last_available_ts.isoformat(),
            },
            "registered_at": self.registered_at.isoformat(),
            "registry_metadata": self.registry_metadata.to_dict(),
        }

    def __hash__(self) -> int:
        return hash(
            (
                self.feature_version_id,
                self.feature_set_id,
                self.feature_set_version,
                self.lifecycle_state,
            )
        )


@dataclass(frozen=True, slots=True)
class FeatureDeprecationRecord:
    """Retirement metadata for a registered feature version."""

    feature_version_id: str
    deprecated_at: datetime
    deprecated_by: str
    reason: str
    replacement_feature_version_id: str = ""
    deprecation_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_version_id",
            _require_feature_version_id(self.feature_version_id),
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
        replacement = _optional_feature_version_id(self.replacement_feature_version_id)
        if replacement == self.feature_version_id:
            raise FeatureRegistryError("replacement_feature_version_id must differ")
        object.__setattr__(self, "replacement_feature_version_id", replacement)
        object.__setattr__(
            self,
            "deprecation_metadata",
            _freeze_json_mapping(self.deprecation_metadata, "deprecation_metadata"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a canonical JSON-compatible deprecation payload."""

        return {
            "schema": FEATURE_DEPRECATION_SCHEMA,
            "feature_version_id": self.feature_version_id,
            "deprecated_at": self.deprecated_at.isoformat(),
            "deprecated_by": self.deprecated_by,
            "reason": self.reason,
            "replacement_feature_version_id": self.replacement_feature_version_id,
            "deprecation_metadata": self.deprecation_metadata.to_dict(),
        }


class FeatureRegistry:
    """SQLite-backed local registry for feature metadata and lineage."""

    def __init__(
        self,
        registry_path: str | Path | None = None,
        *,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if registry_path is None:
            registry_path = default_feature_registry_path(
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
    ) -> FeatureRegistry:
        """Build a registry at ``$ALPHA_DATA_ROOT/registry/features.sqlite``."""

        return cls(alpha_data_root=alpha_data_root, env=env)

    def persist_feature(self, record: FeatureRegistryRecord) -> FeatureRegistryRecord:
        """Persist one feature registry record idempotently."""

        if not isinstance(record, FeatureRegistryRecord):
            raise FeatureRegistryError("persist_feature requires a FeatureRegistryRecord")
        payload = _record_json(record)
        with self._connect() as connection:
            _ensure_schema(connection)
            existing = _fetch_record_row(connection, record.feature_version_id)
            if existing is not None:
                _insert_feature_set_membership(connection, record)
                return _record_from_row(existing)
            connection.execute(
                """
                INSERT INTO feature_registry_records (
                    feature_version_id,
                    feature_id,
                    feature_request_id,
                    lifecycle_state,
                    materialization_plan_id,
                    dataset_version_id,
                    partition_id,
                    materialization_output_path,
                    value_store_format,
                    parquet_path,
                    value_content_hash,
                    producer_engine_id,
                    value_schema_version,
                    value_record_count,
                    first_event_ts,
                    last_event_ts,
                    first_available_ts,
                    last_available_ts,
                    duplicate_exposure_status,
                    registered_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.feature_version_id,
                    record.feature_spec.feature_id,
                    record.feature_request_id,
                    record.lifecycle_state.value,
                    record.materialization_plan_id,
                    record.dataset_version_id,
                    record.partition_id,
                    record.materialization_output_path,
                    record.value_store_format,
                    record.parquet_path,
                    record.value_content_hash,
                    record.producer_engine_id,
                    record.value_schema_version,
                    record.value_record_count,
                    record.first_event_ts.isoformat(),
                    record.last_event_ts.isoformat(),
                    record.first_available_ts.isoformat(),
                    record.last_available_ts.isoformat(),
                    record.duplicate_exposure_status,
                    record.registered_at.isoformat(),
                    payload,
                ),
            )
            connection.execute(
                """
                INSERT INTO feature_lineage_records (
                    feature_version_id,
                    feature_request_id,
                    metadata_json
                )
                VALUES (?, ?, ?)
                ON CONFLICT(feature_version_id) DO UPDATE SET
                    feature_request_id = excluded.feature_request_id,
                    metadata_json = excluded.metadata_json
                """,
                (
                    record.feature_version_id,
                    record.feature_request_id,
                    _lineage_json(record.lineage),
                ),
            )
            _insert_feature_set_membership(connection, record)
        return record

    def resolve_feature(self, feature_version_id: object) -> FeatureRegistryRecord | None:
        """Resolve one registered feature by deterministic FeatureVersion id."""

        version_id = _require_feature_version_id(feature_version_id)
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = _fetch_record_row(connection, version_id)
        if row is None:
            return None
        return _record_from_row(row)

    def resolve_feature_set(self, feature_set: FeatureSetSpec) -> tuple[FeatureRegistryRecord, ...]:
        """Resolve registered records for every member of a FeatureSetSpec."""

        if not isinstance(feature_set, FeatureSetSpec):
            raise FeatureRegistryError("resolve_feature_set requires a FeatureSetSpec")
        expected_ids = tuple(
            version.feature_version_id for version in feature_set.feature_versions
        )
        records_by_id = {
            record.feature_version_id: record
            for record in self.resolve_feature_set_membership(
                feature_set.feature_set_id,
                feature_set.feature_set_version,
            )
        }
        missing = tuple(
            version_id for version_id in expected_ids if version_id not in records_by_id
        )
        if missing:
            raise FeatureRegistryError(
                "FeatureSetSpec has unregistered feature versions: " + ", ".join(missing)
            )
        return tuple(records_by_id[version_id] for version_id in expected_ids)

    def resolve_feature_set_membership(
        self,
        feature_set_id: object,
        feature_set_version: object,
    ) -> tuple[FeatureRegistryRecord, ...]:
        """Resolve all records recorded for a feature-set id and version."""

        feature_set_id = _require_text(feature_set_id, "feature_set_id")
        feature_set_version = _require_text(feature_set_version, "feature_set_version")
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT r.metadata_json
                FROM feature_set_memberships m
                JOIN feature_registry_records r
                  ON r.feature_version_id = m.feature_version_id
                WHERE m.feature_set_id = ?
                  AND m.feature_set_version = ?
                ORDER BY m.ordinal, m.feature_version_id
                """,
                (feature_set_id, feature_set_version),
            ).fetchall()
        return tuple(_record_from_json(str(row["metadata_json"])) for row in rows)

    def deprecate_feature(
        self,
        feature_version_id: object,
        *,
        reason: object,
        deprecated_by: object,
        replacement_feature_version_id: object = "",
        deprecated_at: datetime | None = None,
        deprecation_metadata: Mapping[str, Any] | None = None,
    ) -> FeatureDeprecationRecord:
        """Mark a feature version deprecated without deleting lineage."""

        version_id = _require_feature_version_id(feature_version_id)
        deprecation = FeatureDeprecationRecord(
            feature_version_id=version_id,
            deprecated_at=deprecated_at or datetime.now(UTC),
            deprecated_by=_require_text(deprecated_by, "deprecated_by"),
            reason=_require_text(reason, "reason"),
            replacement_feature_version_id=_optional_feature_version_id(
                replacement_feature_version_id
            ),
            deprecation_metadata=deprecation_metadata or {},
        )
        payload = _deprecation_json(deprecation)
        with self._connect() as connection:
            _ensure_schema(connection)
            row = _fetch_record_row(connection, version_id)
            if row is None:
                raise FeatureRegistryError(
                    f"cannot deprecate unregistered feature version: {version_id}"
                )
            existing_deprecation = connection.execute(
                """
                SELECT metadata_json
                FROM feature_deprecation_records
                WHERE feature_version_id = ?
                """,
                (version_id,),
            ).fetchone()
            if existing_deprecation is not None:
                return _deprecation_from_json(str(existing_deprecation["metadata_json"]))
            record = _record_from_row(row)
            deprecated_record = replace(
                record,
                lifecycle_state=FeatureRegistryLifecycleState.DEPRECATED,
            )
            connection.execute(
                """
                UPDATE feature_registry_records
                SET lifecycle_state = ?,
                    metadata_json = ?
                WHERE feature_version_id = ?
                """,
                (
                    FeatureRegistryLifecycleState.DEPRECATED.value,
                    _record_json(deprecated_record),
                    version_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO feature_deprecation_records (
                    feature_version_id,
                    deprecated_at,
                    reason,
                    replacement_feature_version_id,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    deprecation.deprecated_at.isoformat(),
                    deprecation.reason,
                    deprecation.replacement_feature_version_id,
                    payload,
                ),
            )
        return deprecation

    def resolve_deprecation(
        self,
        feature_version_id: object,
    ) -> FeatureDeprecationRecord | None:
        """Resolve a deprecation record by feature version id."""

        version_id = _require_feature_version_id(feature_version_id)
        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = connection.execute(
                """
                SELECT metadata_json
                FROM feature_deprecation_records
                WHERE feature_version_id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return _deprecation_from_json(str(row["metadata_json"]))

    def read_factor_versions(self) -> list[dict[str, object]]:
        """Expose a read-only duplicate-exposure guard view over registered features."""

        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT metadata_json
                FROM feature_registry_records
                ORDER BY feature_id, feature_version_id
                """
            ).fetchall()
        return [
            _duplicate_exposure_registry_entry(_record_from_json(str(row["metadata_json"])))
            for row in rows
        ]

    def count_feature_records(self) -> int:
        """Return the number of persisted feature registry rows."""

        with self._connect(read_only=True) as connection:
            _ensure_schema(connection)
            row = connection.execute(
                "SELECT count(*) AS count FROM feature_registry_records"
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
        return connection


def default_feature_registry_path(
    *,
    alpha_data_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Return the default local-only feature registry path."""

    source = os.environ if env is None else env
    root_value = alpha_data_root if alpha_data_root is not None else source.get("ALPHA_DATA_ROOT")
    if root_value is None:
        raise FeatureRegistryError("ALPHA_DATA_ROOT is required for FeatureRegistry")
    root = _require_path(root_value, "ALPHA_DATA_ROOT")
    _require_outside_repo(root, "ALPHA_DATA_ROOT")
    return root / DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_registry_records (
            feature_version_id TEXT PRIMARY KEY,
            feature_id TEXT NOT NULL,
            feature_request_id TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            materialization_plan_id TEXT NOT NULL,
            dataset_version_id TEXT NOT NULL,
            partition_id TEXT NOT NULL,
            materialization_output_path TEXT NOT NULL,
            value_store_format TEXT NOT NULL DEFAULT 'jsonl',
            parquet_path TEXT,
            value_content_hash TEXT,
            producer_engine_id TEXT,
            value_schema_version TEXT,
            value_record_count INTEGER NOT NULL,
            first_event_ts TEXT NOT NULL,
            last_event_ts TEXT NOT NULL,
            first_available_ts TEXT NOT NULL,
            last_available_ts TEXT NOT NULL,
            duplicate_exposure_status TEXT NOT NULL,
            registered_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        )
        """
    )
    _backfill_columns(
        connection,
        "feature_registry_records",
        {
            "value_store_format": "TEXT NOT NULL DEFAULT 'jsonl'",
            "parquet_path": "TEXT",
            "value_content_hash": "TEXT",
            "producer_engine_id": "TEXT",
            "value_schema_version": "TEXT",
        },
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_lineage_records (
            feature_version_id TEXT PRIMARY KEY,
            feature_request_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            FOREIGN KEY(feature_version_id)
                REFERENCES feature_registry_records(feature_version_id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_set_memberships (
            feature_set_id TEXT NOT NULL,
            feature_set_version TEXT NOT NULL,
            feature_version_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            metadata_json TEXT NOT NULL,
            PRIMARY KEY(feature_set_id, feature_set_version, feature_version_id),
            FOREIGN KEY(feature_version_id)
                REFERENCES feature_registry_records(feature_version_id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_deprecation_records (
            feature_version_id TEXT PRIMARY KEY,
            deprecated_at TEXT NOT NULL,
            reason TEXT NOT NULL,
            replacement_feature_version_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            FOREIGN KEY(feature_version_id)
                REFERENCES feature_registry_records(feature_version_id)
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
    feature_version_id: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM feature_registry_records
        WHERE feature_version_id = ?
        """,
        (feature_version_id,),
    ).fetchone()


def _insert_feature_set_membership(
    connection: sqlite3.Connection,
    record: FeatureRegistryRecord,
) -> None:
    connection.execute(
        """
        INSERT INTO feature_set_memberships (
            feature_set_id,
            feature_set_version,
            feature_version_id,
            ordinal,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(feature_set_id, feature_set_version, feature_version_id) DO UPDATE SET
            ordinal = excluded.ordinal,
            metadata_json = excluded.metadata_json
        """,
        (
            record.feature_set_id,
            record.feature_set_version,
            record.feature_version_id,
            record.feature_set_ordinal,
            _membership_json(record),
        ),
    )


def _record_json(record: FeatureRegistryRecord) -> str:
    return canonical_serialize(record.to_dict())


def _lineage_json(lineage: FeatureLineageRecord) -> str:
    return canonical_serialize(
        {
            "schema": FEATURE_REGISTRY_SCHEMA,
            "lineage": lineage.to_dict(),
        }
    )


def _membership_json(record: FeatureRegistryRecord) -> str:
    return canonical_serialize(
        {
            "schema": FEATURE_REGISTRY_SCHEMA,
            "feature_set_id": record.feature_set_id,
            "feature_set_version": record.feature_set_version,
            "feature_version_id": record.feature_version_id,
            "ordinal": record.feature_set_ordinal,
        }
    )


def _deprecation_json(record: FeatureDeprecationRecord) -> str:
    return canonical_serialize(record.to_dict())


def _record_from_row(row: sqlite3.Row) -> FeatureRegistryRecord:
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
        producer_engine_id=(
            row["producer_engine_id"]
            if "producer_engine_id" in keys and row["producer_engine_id"] is not None
            else record.producer_engine_id
        ),
        value_schema_version=(
            row["value_schema_version"]
            if "value_schema_version" in keys and row["value_schema_version"] is not None
            else record.value_schema_version
        ),
    )


def _record_from_json(text: str) -> FeatureRegistryRecord:
    payload = _loads_mapping(text, "FeatureRegistryRecord")
    if payload.get("schema") != FEATURE_REGISTRY_SCHEMA:
        raise FeatureRegistryError("feature registry record schema is unsupported")
    duplicate_report = _duplicate_report_from_payload(
        _mapping_payload(payload.get("duplicate_exposure_report"), "duplicate_exposure_report")
    )
    feature_request_payload = _mapping_payload(payload.get("feature_request"), "feature_request")
    feature_request = _feature_request_from_payload(feature_request_payload)
    decision = FeatureRequestGateDecision(
        implementation_allowed=True,
        feature_request=feature_request,
        checked_feature_request=feature_request,
        duplicate_exposure_report=duplicate_report,
        rejection_reason=None,
        message="FeatureRequest restored from FeatureRegistry",
    )
    feature_spec = _feature_spec_from_payload(
        _mapping_payload(payload.get("feature_spec"), "feature_spec"),
        decision,
    )
    feature_version = _feature_version_from_payload(
        _mapping_payload(payload.get("feature_version"), "feature_version")
    )
    lineage_payload = _mapping_payload(payload.get("lineage"), "lineage")
    materialization = _mapping_payload(payload.get("materialization"), "materialization")
    membership = _mapping_payload(
        payload.get("feature_set_membership"),
        "feature_set_membership",
    )
    return FeatureRegistryRecord(
        feature_version=feature_version,
        feature_spec=feature_spec,
        lineage=FeatureLineageRecord(
            feature_version=feature_version,
            feature_spec=feature_spec,
            feature_request_id=_require_text(
                lineage_payload.get("feature_request_id"),
                "lineage.feature_request_id",
            ),
            contract_provenance=_mapping_payload(
                lineage_payload.get("contract_provenance", {}),
                "lineage.contract_provenance",
            ),
        ),
        feature_request_payload=feature_request_payload,
        duplicate_exposure_report=duplicate_report,
        feature_set_id=_require_text(membership.get("feature_set_id"), "feature_set_id"),
        feature_set_version=_require_text(
            membership.get("feature_set_version"),
            "feature_set_version",
        ),
        feature_set_ordinal=_require_nonnegative_int(membership.get("ordinal"), "ordinal"),
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
        producer_engine_id=_optional_text_or_none(
            materialization.get("producer_engine_id"),
            "materialization.producer_engine_id",
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
        first_available_ts=_datetime_from_payload(
            materialization.get("first_available_ts"),
            "materialization.first_available_ts",
        ),
        last_available_ts=_datetime_from_payload(
            materialization.get("last_available_ts"),
            "materialization.last_available_ts",
        ),
        registered_at=_datetime_from_payload(payload.get("registered_at"), "registered_at"),
        lifecycle_state=_require_text(payload.get("lifecycle_state"), "lifecycle_state"),
        registry_metadata=_mapping_payload(
            payload.get("registry_metadata", {}),
            "registry_metadata",
        ),
    )


def _deprecation_from_json(text: str) -> FeatureDeprecationRecord:
    payload = _loads_mapping(text, "FeatureDeprecationRecord")
    if payload.get("schema") != FEATURE_DEPRECATION_SCHEMA:
        raise FeatureRegistryError("feature deprecation schema is unsupported")
    return FeatureDeprecationRecord(
        feature_version_id=_require_text(payload.get("feature_version_id"), "feature_version_id"),
        deprecated_at=_datetime_from_payload(payload.get("deprecated_at"), "deprecated_at"),
        deprecated_by=_require_text(payload.get("deprecated_by"), "deprecated_by"),
        reason=_require_text(payload.get("reason"), "reason"),
        replacement_feature_version_id=_optional_feature_version_id(
            payload.get("replacement_feature_version_id", "")
        ),
        deprecation_metadata=_mapping_payload(
            payload.get("deprecation_metadata", {}),
            "deprecation_metadata",
        ),
    )


def _feature_spec_from_payload(
    payload: Mapping[str, object],
    decision: FeatureRequestGateDecision,
) -> FeatureSpec:
    kwargs: dict[str, object] = {
        "feature_id": _require_text(payload.get("feature_id"), "feature_id"),
        "family": _require_text(payload.get("family"), "family"),
        "feature_request_id": _require_text(
            payload.get("feature_request_id"),
            "feature_request_id",
        ),
        "inputs": FeatureInputSpec(
            input_views=_text_tuple_payload(
                _sequence_payload(
                    _mapping_payload(payload.get("inputs"), "inputs").get("input_views"),
                    "inputs.input_views",
                )
            ),
            fields=_text_tuple_payload(
                _sequence_payload(
                    _mapping_payload(payload.get("inputs"), "inputs").get("fields"),
                    "inputs.fields",
                )
            ),
            dataset_version_ids=_text_tuple_payload(
                _sequence_payload(
                    _mapping_payload(payload.get("inputs"), "inputs").get(
                        "dataset_version_ids",
                        (),
                    ),
                    "inputs.dataset_version_ids",
                )
            ),
            input_metadata=_mapping_payload(
                _mapping_payload(payload.get("inputs"), "inputs").get("input_metadata", {}),
                "inputs.input_metadata",
            ),
        ),
        "transform": TransformSpec(
            transform_id=_require_text(
                _mapping_payload(payload.get("transform"), "transform").get("transform_id"),
                "transform.transform_id",
            ),
            parameters=_mapping_payload(
                _mapping_payload(payload.get("transform"), "transform").get("parameters", {}),
                "transform.parameters",
            ),
        ),
        "window": WindowSpec(
            kind=_require_text(
                _mapping_payload(payload.get("window"), "window").get("kind"),
                "window.kind",
            ),
            length=_require_positive_int(
                _mapping_payload(payload.get("window"), "window").get("length"),
                "window.length",
            ),
            causality=_require_text(
                _mapping_payload(payload.get("window"), "window").get("causality"),
                "window.causality",
            ),
            offline_only=_require_bool(
                _mapping_payload(payload.get("window"), "window").get("offline_only"),
                "window.offline_only",
            ),
            anchor=_require_text(
                _mapping_payload(payload.get("window"), "window").get("anchor"),
                "window.anchor",
            ),
            parameters=_mapping_payload(
                _mapping_payload(payload.get("window"), "window").get("parameters", {}),
                "window.parameters",
            ),
        ),
        "normalization": NormalizationSpec(
            normalization_id=_require_text(
                _mapping_payload(payload.get("normalization"), "normalization").get(
                    "normalization_id"
                ),
                "normalization.normalization_id",
            ),
            parameters=_mapping_payload(
                _mapping_payload(payload.get("normalization"), "normalization").get(
                    "parameters",
                    {},
                ),
                "normalization.parameters",
            ),
            fit_partition_policy=_require_text(
                _mapping_payload(payload.get("normalization"), "normalization").get(
                    "fit_partition_policy"
                ),
                "normalization.fit_partition_policy",
            ),
            contamination_metadata=_mapping_payload(
                _mapping_payload(payload.get("normalization"), "normalization").get(
                    "contamination_metadata",
                    {},
                ),
                "normalization.contamination_metadata",
            ),
        ),
        "availability_assumptions": _mapping_payload(
            payload.get("availability_assumptions"),
            "availability_assumptions",
        ),
        "available_ts_derivation_rule": _require_text(
            payload.get("available_ts_derivation_rule"),
            "available_ts_derivation_rule",
        ),
        "live": _require_bool(payload.get("live"), "live"),
        "implementation_eligible": _require_bool(
            payload.get("implementation_eligible"),
            "implementation_eligible",
        ),
        "contract_metadata": _mapping_payload(
            payload.get("contract_metadata", {}),
            "contract_metadata",
        ),
    }
    if kwargs["implementation_eligible"]:
        return FeatureSpec(**kwargs, request_gate_decision=decision)
    return FeatureSpec(**kwargs)


def _feature_version_from_payload(payload: Mapping[str, object]) -> FeatureVersion:
    return FeatureVersion(
        feature_version_id=_require_text(payload.get("feature_version_id"), "feature_version_id"),
        content_hash=_require_text(payload.get("content_hash"), "content_hash"),
        algorithm=_require_text(payload.get("algorithm"), "algorithm"),
    )


def _duplicate_report_from_payload(payload: Mapping[str, object]) -> DuplicateExposureReport:
    groups = []
    for item in _sequence_payload(
        payload.get("equivalent_feature_groups", ()),
        "equivalent_feature_groups",
    ):
        group = _mapping_payload(item, "equivalent_feature_group")
        groups.append(
            EquivalentFeatureGroup(
                kind=ExposureFindingKind(
                    _require_text(group.get("kind"), "equivalent_feature_group.kind")
                ),
                severity=ExposureFindingSeverity(
                    _require_text(group.get("severity"), "equivalent_feature_group.severity")
                ),
                matched_registry_reference=MappingProxyType(
                    {
                        str(key): str(value)
                        for key, value in _mapping_payload(
                            group.get("matched_registry_reference"),
                            "matched_registry_reference",
                        ).items()
                    }
                ),
                rationale=_require_text(
                    group.get("rationale"),
                    "equivalent_feature_group.rationale",
                ),
            )
        )
    return DuplicateExposureReport(
        registry_status=ExposureRegistryStatus(
            _require_text(payload.get("registry_status"), "registry_status")
        ),
        registry_entries_checked=_require_nonnegative_int(
            payload.get("registry_entries_checked"),
            "registry_entries_checked",
        ),
        registry_error=str(payload.get("registry_error", "")),
        equivalent_feature_groups=tuple(groups),
    )


def _duplicate_exposure_registry_entry(record: FeatureRegistryRecord) -> dict[str, object]:
    request_payload = record.feature_request_payload.to_dict()
    formula = _mapping_payload(request_payload.get("formula_sketch", {}), "formula_sketch")
    requested_inputs = _string_list(request_payload.get("requested_inputs", ()))
    formula_inputs = _string_list(formula.get("inputs", ()))
    inputs = formula_inputs or requested_inputs or list(record.feature_spec.inputs.fields)
    operation = _first_text(
        formula,
        ("operation", "operator", "transform", "method", "formula"),
        fallback=record.feature_spec.transform.transform_id,
    )
    exposure_family = _first_text(
        formula,
        ("exposure_family", "exposure", "family", "factor_id", "name"),
        fallback=record.feature_spec.feature_id,
    )
    window = formula.get("window", record.feature_spec.window.length)
    metadata = {
        "feature_request_id": record.feature_request_id,
        "feature_version_id": record.feature_version_id,
        "lifecycle_state": record.lifecycle_state.value,
        "exposure_family": exposure_family,
        "operation": operation,
        "inputs": inputs,
        "window": window,
    }
    parameters = record.feature_spec.transform.parameters.to_dict()
    parameters.setdefault("operation", operation)
    parameters.setdefault("inputs", inputs)
    parameters.setdefault("window", window)
    return {
        "factor_id": record.feature_spec.feature_id,
        "factor_version": record.feature_version_id,
        "name": record.feature_spec.feature_id,
        "metadata": metadata,
        "parameters": parameters,
    }


def _feature_request_from_payload(payload: Mapping[str, object]) -> FeatureRequest:
    try:
        return validate_feature_request(payload)
    except Exception as exc:
        raise FeatureRegistryError("feature_request_payload is not a valid FeatureRequest") from exc


def _loads_mapping(text: str, field_name: str) -> Mapping[str, object]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FeatureRegistryError(f"{field_name} must be valid JSON") from exc
    return _mapping_payload(payload, field_name)


def _mapping_payload(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise FeatureRegistryError(f"{field_name} must be a mapping")
    return value


def _sequence_payload(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, str) or not isinstance(value, list | tuple):
        raise FeatureRegistryError(f"{field_name} must be a sequence")
    return tuple(value)


def _text_tuple_payload(values: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(_require_text(value, "sequence item") for value in values)


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return []


def _first_text(
    mapping: Mapping[str, object],
    fields: tuple[str, ...],
    *,
    fallback: object = "",
) -> str:
    for field_name in fields:
        value = mapping.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()
    return str(fallback)


def _require_registry_path(path: str | Path) -> Path:
    resolved = resolve_registry_path(path)
    if not is_local_only_registry_path(resolved):
        raise FeatureRegistryError("FeatureRegistry path must be a local SQLite path")
    _require_outside_repo(resolved, "FeatureRegistry path")
    return resolved


def _require_outside_repo(path: Path, field_name: str) -> None:
    repo_root = Path.cwd().resolve(strict=False)
    resolved = path.resolve(strict=False)
    if resolved == repo_root or resolved.is_relative_to(repo_root):
        raise FeatureRegistryError(f"{field_name} must be outside the repository tree")


def _require_path(value: str | Path, field_name: str) -> Path:
    if not isinstance(value, str | Path):
        raise FeatureRegistryError(f"{field_name} must be a path")
    try:
        return Path(value).expanduser().resolve(strict=False)
    except RuntimeError as exc:
        raise FeatureRegistryError(f"{field_name} could not be resolved") from exc


def _coerce_lifecycle_state(
    value: FeatureRegistryLifecycleState | str,
) -> FeatureRegistryLifecycleState:
    text = _require_text(value, "lifecycle_state")
    if text in PROHIBITED_FEATURE_REGISTRY_STATES:
        raise FeatureRegistryError(f"prohibited feature lifecycle state: {text}")
    try:
        return FeatureRegistryLifecycleState(text)
    except ValueError as exc:
        allowed = ", ".join(state.value for state in FeatureRegistryLifecycleState)
        raise FeatureRegistryError(f"lifecycle_state must be one of: {allowed}") from exc


def _coerce_value_store_format(value: object) -> ValueStoreFormat:
    try:
        if isinstance(value, ValueStoreFormat):
            return value
        return ValueStoreFormat(_require_text(value, "value_store_format"))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ValueStoreFormat)
        raise FeatureRegistryError(f"value_store_format must be one of: {allowed}") from exc


def _producer_engine_id_from_provenance(
    value: object,
    *,
    registry_metadata: Mapping[str, Any] | FrozenJsonMapping,
    lineage_provenance: Mapping[str, Any] | FrozenJsonMapping,
) -> str:
    explicit = _optional_text_or_none(value, "producer_engine_id")
    if explicit is not None:
        return explicit
    for source_name, source in (
        ("registry_metadata.producer_engine_id", registry_metadata),
        ("lineage.contract_provenance.producer_engine_id", lineage_provenance),
    ):
        payload = source.to_dict() if isinstance(source, FrozenJsonMapping) else source
        candidate = _optional_text_or_none(payload.get("producer_engine_id"), source_name)
        if candidate is not None:
            return candidate
    return REFERENCE_FEATURE_PRODUCER_ENGINE_ID


def _freeze_json_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    if isinstance(value, FrozenJsonMapping):
        return value
    try:
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    except FeatureContractError as exc:
        raise FeatureRegistryError(str(exc)) from exc


def _require_text(value: object, field_name: str) -> str:
    if isinstance(value, StrEnum):
        value = value.value
    if not isinstance(value, str):
        raise FeatureRegistryError(f"{field_name} must be a string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FeatureRegistryError(f"{field_name} must be a non-empty single-line string")
    return text


def _optional_text_or_none(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise FeatureRegistryError(f"{field_name} must be a positive integer")
    return value


def _require_nonnegative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FeatureRegistryError(f"{field_name} must be a non-negative integer")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise FeatureRegistryError(f"{field_name} must be a bool")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FeatureRegistryError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise FeatureRegistryError(f"{field_name} must be timezone-aware")
    return value


def _datetime_from_payload(value: object, field_name: str) -> datetime:
    try:
        return _require_aware_datetime(
            datetime.fromisoformat(_require_text(value, field_name)),
            field_name,
        )
    except ValueError as exc:
        raise FeatureRegistryError(f"{field_name} must be an ISO datetime") from exc


def _require_feature_version_id(value: object) -> str:
    text = _require_text(value, "feature_version_id")
    if FEATURE_VERSION_PATTERN.fullmatch(text) is None:
        raise FeatureRegistryError("feature_version_id must be fver_<64-hex-content-hash>")
    return text


def _optional_feature_version_id(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return _require_feature_version_id(text)


__all__ = [
    "DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH",
    "FEATURE_DEPRECATION_SCHEMA",
    "FEATURE_REGISTRY_SCHEMA",
    "PROHIBITED_FEATURE_REGISTRY_STATES",
    "REFERENCE_FEATURE_PRODUCER_ENGINE_ID",
    "FeatureDeprecationRecord",
    "FeatureRegistry",
    "FeatureRegistryError",
    "FeatureRegistryLifecycleState",
    "FeatureRegistryRecord",
    "default_feature_registry_path",
]
