"""FeatureStore facade for governed feature registration and resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import (
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
)
from alpha_system.features.engine import FeatureMaterializationResult
from alpha_system.features.registry import (
    FeatureDeprecationRecord,
    FeatureRegistry,
    FeatureRegistryError,
    FeatureRegistryRecord,
    REFERENCE_FEATURE_PRODUCER_ENGINE_ID,
)
from alpha_system.features.request_gate import evaluate_feature_request_gate
from alpha_system.governance.feature_request import FeatureRequest


class FeatureStoreError(ValueError):
    """Raised when FeatureStore registration fails closed."""


@dataclass(frozen=True, slots=True)
class _ValueSummary:
    count: int
    first_event_ts: datetime
    last_event_ts: datetime
    first_available_ts: datetime
    last_available_ts: datetime


class FeatureStore:
    """Governed facade over the local-only FeatureRegistry."""

    def __init__(
        self,
        registry: FeatureRegistry | str | Path | None = None,
        *,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if isinstance(registry, FeatureRegistry):
            self.registry = registry
        else:
            self.registry = FeatureRegistry(
                registry_path=registry,
                alpha_data_root=alpha_data_root,
                env=env,
            )

    @classmethod
    def from_alpha_data_root(
        cls,
        alpha_data_root: str | Path | None = None,
        *,
        env: Mapping[str, str] | None = None,
    ) -> FeatureStore:
        """Build a FeatureStore backed by ``$ALPHA_DATA_ROOT/registry/features.sqlite``."""

        return cls(alpha_data_root=alpha_data_root, env=env)

    def register_materialized_feature(
        self,
        materialization_result: FeatureMaterializationResult,
        *,
        feature_spec: FeatureSpec,
        feature_version: FeatureVersion,
        feature_request: FeatureRequest | Mapping[str, Any] | None,
        lineage: FeatureLineageRecord | None = None,
        producer_engine_id: str | None = None,
        registry_metadata: Mapping[str, Any] | None = None,
    ) -> FeatureRegistryRecord:
        """Register one materialized feature version after governance checks."""

        spec = _require_validated_feature_spec(feature_spec)
        version = _require_matching_feature_version(feature_version, spec)
        lineage_record = _bind_lineage(spec, version, lineage)
        producer_id = _producer_engine_id(
            producer_engine_id,
            lineage=lineage_record,
            registry_metadata=registry_metadata,
        )
        existing = self.registry.resolve_feature(version.feature_version_id)
        if (
            existing is not None
            and _approved_request_handle_id(feature_request) == spec.feature_request_id
        ):
            _require_existing_record_matches(existing, spec, version, lineage_record)
            feature_set, ordinal = _feature_set_membership(materialization_result, spec, version)
            summary = _summarize_materialized_values(materialization_result, version)
            output_path = _materialization_output_path(materialization_result)
            value_store = _value_store_metadata(materialization_result)
            return self.registry.persist_feature(
                FeatureRegistryRecord(
                    feature_version=version,
                    feature_spec=spec,
                    lineage=lineage_record,
                    feature_request_payload=existing.feature_request_payload,
                    duplicate_exposure_report=existing.duplicate_exposure_report,
                    feature_set_id=feature_set.feature_set_id,
                    feature_set_version=feature_set.feature_set_version,
                    feature_set_ordinal=ordinal,
                    materialization_plan_id=materialization_result.plan.plan_id,
                    dataset_version_id=materialization_result.plan.dataset_version_id,
                    partition_id=materialization_result.plan.partition_id,
                    materialization_output_path=output_path.as_posix(),
                    value_store_format=value_store["value_store_format"],
                    parquet_path=value_store["parquet_path"],
                    value_content_hash=value_store["value_content_hash"],
                    producer_engine_id=producer_id,
                    value_schema_version=value_store["value_schema_version"],
                    value_record_count=summary.count,
                    first_event_ts=summary.first_event_ts,
                    last_event_ts=summary.last_event_ts,
                    first_available_ts=summary.first_available_ts,
                    last_available_ts=summary.last_available_ts,
                    registered_at=existing.registered_at,
                    lifecycle_state=existing.lifecycle_state,
                    registry_metadata=existing.registry_metadata,
                )
        )
        decision = evaluate_feature_request_gate(feature_request, self.registry)
        if not decision.implementation_allowed:
            raise FeatureStoreError(
                f"FeatureRequest gate rejected registration: {decision.message}"
            )
        if decision.checked_feature_request is None:
            raise FeatureStoreError("FeatureRequest gate did not return a checked request")
        if decision.duplicate_exposure_report is None:
            raise FeatureStoreError("FeatureRequest gate did not return a duplicate report")
        if decision.feature_request_id != spec.feature_request_id:
            raise FeatureStoreError(
                "checked FeatureRequest id must match FeatureSpec.feature_request_id"
            )
        feature_set, ordinal = _feature_set_membership(materialization_result, spec, version)
        summary = _summarize_materialized_values(materialization_result, version)
        output_path = _materialization_output_path(materialization_result)
        value_store = _value_store_metadata(materialization_result)
        record = FeatureRegistryRecord(
            feature_version=version,
            feature_spec=spec,
            lineage=lineage_record,
            feature_request_payload=decision.checked_feature_request.to_dict(),
            duplicate_exposure_report=decision.duplicate_exposure_report,
            feature_set_id=feature_set.feature_set_id,
            feature_set_version=feature_set.feature_set_version,
            feature_set_ordinal=ordinal,
            materialization_plan_id=materialization_result.plan.plan_id,
            dataset_version_id=materialization_result.plan.dataset_version_id,
            partition_id=materialization_result.plan.partition_id,
            materialization_output_path=output_path.as_posix(),
            value_store_format=value_store["value_store_format"],
            parquet_path=value_store["parquet_path"],
            value_content_hash=value_store["value_content_hash"],
            producer_engine_id=producer_id,
            value_schema_version=value_store["value_schema_version"],
            value_record_count=summary.count,
            first_event_ts=summary.first_event_ts,
            last_event_ts=summary.last_event_ts,
            first_available_ts=summary.first_available_ts,
            last_available_ts=summary.last_available_ts,
            registered_at=datetime.now(UTC),
            registry_metadata=registry_metadata or {},
        )
        try:
            return self.registry.persist_feature(record)
        except FeatureRegistryError as exc:
            raise FeatureStoreError(str(exc)) from exc

    def register_feature(
        self,
        materialization_result: FeatureMaterializationResult,
        *,
        feature_spec: FeatureSpec,
        feature_version: FeatureVersion,
        feature_request: FeatureRequest | Mapping[str, Any] | None,
        lineage: FeatureLineageRecord | None = None,
        producer_engine_id: str | None = None,
        registry_metadata: Mapping[str, Any] | None = None,
    ) -> FeatureRegistryRecord:
        """Alias for ``register_materialized_feature``."""

        return self.register_materialized_feature(
            materialization_result,
            feature_spec=feature_spec,
            feature_version=feature_version,
            feature_request=feature_request,
            lineage=lineage,
            producer_engine_id=producer_engine_id,
            registry_metadata=registry_metadata,
        )

    def resolve_feature(self, feature_version_id: object) -> FeatureRegistryRecord | None:
        """Resolve one feature by deterministic FeatureVersion id."""

        return self.registry.resolve_feature(feature_version_id)

    def resolve_feature_by_version(
        self,
        feature_version_id: object,
    ) -> FeatureRegistryRecord | None:
        """Resolve one feature by deterministic FeatureVersion id."""

        return self.resolve_feature(feature_version_id)

    def resolve_feature_set(self, feature_set: FeatureSetSpec) -> tuple[FeatureRegistryRecord, ...]:
        """Resolve every registered feature in a FeatureSetSpec."""

        return self.registry.resolve_feature_set(feature_set)

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
        """Mark a feature deprecated without deleting its lineage."""

        return self.registry.deprecate_feature(
            feature_version_id,
            reason=reason,
            deprecated_by=deprecated_by,
            replacement_feature_version_id=replacement_feature_version_id,
            deprecated_at=deprecated_at,
            deprecation_metadata=deprecation_metadata,
        )


def _require_validated_feature_spec(feature_spec: FeatureSpec) -> FeatureSpec:
    if not isinstance(feature_spec, FeatureSpec):
        raise FeatureStoreError("registration requires a FeatureSpec")
    if not feature_spec.implementation_eligible:
        raise FeatureStoreError(
            "FeatureSpec must be implementation eligible before registration"
        )
    return feature_spec


def _require_matching_feature_version(
    feature_version: FeatureVersion,
    feature_spec: FeatureSpec,
) -> FeatureVersion:
    if not isinstance(feature_version, FeatureVersion):
        raise FeatureStoreError("registration requires a FeatureVersion")
    if feature_version != FeatureVersion.derive(feature_spec):
        raise FeatureStoreError("FeatureVersion must match FeatureSpec content")
    return feature_version


def _bind_lineage(
    feature_spec: FeatureSpec,
    feature_version: FeatureVersion,
    lineage: FeatureLineageRecord | None,
) -> FeatureLineageRecord:
    if lineage is None:
        return FeatureLineageRecord(
            feature_version=feature_version,
            feature_spec=feature_spec,
            feature_request_id=feature_spec.feature_request_id,
            contract_provenance={"bound_by": "FeatureStore"},
        )
    if not isinstance(lineage, FeatureLineageRecord):
        raise FeatureStoreError("lineage must be a FeatureLineageRecord")
    if lineage.feature_version != feature_version:
        raise FeatureStoreError("lineage FeatureVersion does not match registration")
    if lineage.feature_spec != feature_spec:
        raise FeatureStoreError("lineage FeatureSpec does not match registration")
    if lineage.feature_request_id != feature_spec.feature_request_id:
        raise FeatureStoreError("lineage FeatureRequest id does not match registration")
    return lineage


def _producer_engine_id(
    value: str | None,
    *,
    lineage: FeatureLineageRecord,
    registry_metadata: Mapping[str, Any] | None,
) -> str:
    explicit = _optional_text(value, "producer_engine_id")
    if explicit is not None:
        return explicit
    if registry_metadata is not None:
        metadata_payload = (
            registry_metadata.to_dict()
            if hasattr(registry_metadata, "to_dict")
            else registry_metadata
        )
        metadata_value = _optional_text(
            metadata_payload.get("producer_engine_id"),
            "registry_metadata.producer_engine_id",
        )
        if metadata_value is not None:
            return metadata_value
    lineage_value = _optional_text(
        lineage.contract_provenance.to_dict().get("producer_engine_id"),
        "lineage.contract_provenance.producer_engine_id",
    )
    if lineage_value is not None:
        return lineage_value
    return REFERENCE_FEATURE_PRODUCER_ENGINE_ID


def _approved_request_handle_id(
    feature_request: FeatureRequest | Mapping[str, Any] | None,
) -> str | None:
    if isinstance(feature_request, FeatureRequest):
        if feature_request.approval_status == "APPROVED":
            return feature_request.feature_request_id
        return None
    if isinstance(feature_request, Mapping):
        if str(feature_request.get("approval_status", "")) == "APPROVED":
            value = feature_request.get("feature_request_id")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _require_existing_record_matches(
    existing: FeatureRegistryRecord,
    feature_spec: FeatureSpec,
    feature_version: FeatureVersion,
    lineage: FeatureLineageRecord,
) -> None:
    if existing.feature_version != feature_version:
        raise FeatureStoreError("existing registry record has a mismatched FeatureVersion")
    if existing.feature_spec != feature_spec:
        raise FeatureStoreError("existing registry record has a mismatched FeatureSpec")
    if existing.lineage != lineage:
        raise FeatureStoreError("existing registry record has a mismatched lineage")


def _feature_set_membership(
    materialization_result: FeatureMaterializationResult,
    feature_spec: FeatureSpec,
    feature_version: FeatureVersion,
) -> tuple[FeatureSetSpec, int]:
    result = _require_materialization_result(materialization_result)
    feature_set = result.plan.feature_set
    if not isinstance(feature_set, FeatureSetSpec):
        raise FeatureStoreError("materialization result plan must carry a FeatureSetSpec")
    for ordinal, member in enumerate(feature_set.features):
        if member.feature_id != feature_spec.feature_id:
            continue
        if member != feature_spec:
            raise FeatureStoreError("FeatureSetSpec member does not match FeatureSpec")
        if feature_set.feature_versions[ordinal] != feature_version:
            raise FeatureStoreError("FeatureSetSpec member does not match FeatureVersion")
        return feature_set, ordinal
    raise FeatureStoreError("FeatureSpec is not a member of the materialized FeatureSetSpec")


def _summarize_materialized_values(
    materialization_result: FeatureMaterializationResult,
    feature_version: FeatureVersion,
) -> _ValueSummary:
    result = _require_materialization_result(materialization_result)
    if result.dry_run:
        raise FeatureStoreError("dry-run materialization results cannot be registered")
    if feature_version.feature_version_id not in result.plan.feature_version_ids:
        raise FeatureStoreError("FeatureVersion is not in the materialization plan")
    records = tuple(
        record
        for record in result.records
        if record.feature_version_id == feature_version.feature_version_id
    )
    if not records:
        raise FeatureStoreError("registration requires materialized FeatureValueRecords")
    for record in records:
        if not isinstance(record, FeatureValueRecord):
            raise FeatureStoreError("materialization result contains a non-FeatureValueRecord")
        if record.available_ts < record.event_ts:
            raise FeatureStoreError("FeatureValueRecord.available_ts must not precede event_ts")
    event_ts_values = tuple(record.event_ts for record in records)
    available_ts_values = tuple(record.available_ts for record in records)
    return _ValueSummary(
        count=len(records),
        first_event_ts=min(event_ts_values),
        last_event_ts=max(event_ts_values),
        first_available_ts=min(available_ts_values),
        last_available_ts=max(available_ts_values),
    )


def _materialization_output_path(materialization_result: FeatureMaterializationResult) -> Path:
    result = _require_materialization_result(materialization_result)
    output_path = result.output_path or result.plan.output_path
    if output_path is None:
        raise FeatureStoreError("materialization result must expose an output path")
    path = Path(output_path).expanduser().resolve(strict=False)
    root = result.plan.alpha_data_root.expanduser().resolve(strict=False)
    if not path.is_relative_to(root):
        raise FeatureStoreError("materialization output path must stay under ALPHA_DATA_ROOT")
    return path


def _value_store_metadata(
    materialization_result: FeatureMaterializationResult,
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
    materialization_result: FeatureMaterializationResult,
) -> FeatureMaterializationResult:
    if not isinstance(materialization_result, FeatureMaterializationResult):
        raise FeatureStoreError("registration requires a FeatureMaterializationResult")
    return materialization_result


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FeatureStoreError(f"{field_name} must be a string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FeatureStoreError(f"{field_name} must be a non-empty single-line string")
    return text


__all__ = [
    "FeatureStore",
    "FeatureStoreError",
]
