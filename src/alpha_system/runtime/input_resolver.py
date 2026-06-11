"""Fail-closed runtime input resolver for accepted Feature/Label studies.

This module turns an admitted runtime entry result into value-free handles for
one accepted DatasetVersion and its registered FeatureStore/LabelStore packs.
It resolves metadata only; it does not read provider files, materialize feature
or label values, or call external providers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import DatasetPartitionPlan
from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.features import consumption as feature_consumption
from alpha_system.features.contracts import FEATURE_VERSION_PATTERN
from alpha_system.features.registry import FeatureRegistryError
from alpha_system.features.store import FeatureStore, FeatureStoreError
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.labels.registry import LabelRegistry, LabelRegistryError
from alpha_system.labels.version import LABEL_VERSION_PATTERN
from alpha_system.runtime.entry_contract import (
    ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES,
    RAW_PROVIDER_FILE_SUFFIXES,
    RAW_PROVIDER_METADATA_KEYS,
    RuntimeEntryReason,
    RuntimeEntryResult,
    RuntimeEntryStatus,
)

RejectionReasonRecord = RuntimeEntryReason

DatasetVersionResolver = Callable[[str | Path, object], object | None]

LOCKED_PARTITION_IDS: frozenset[str] = frozenset(
    {"locked_test_candidate", "latest_shadow_candidate"}
)
FORBIDDEN_PROVIDER_METADATA_KEYS: frozenset[str] = frozenset(
    set(RAW_PROVIDER_METADATA_KEYS)
    | {
        "databento_client",
        "external_provider",
        "external_provider_request",
        "ibkr_client",
        "provider_import",
        "provider_reader",
        "provider_reader_import",
        "raw_provider_import",
    }
)
LABEL_AS_FEATURE_FIELDS: frozenset[str] = frozenset(
    {
        "label",
        "label_available_ts",
        "label_value",
        "horizon_end_ts",
        "target",
    }
)
RUNTIME_PACK_LIFECYCLE_STATE = "REGISTERED"


class FieldRole(StrEnum):
    """Declared role for a feature input field."""

    FEATURE = "FEATURE"
    LABEL_TARGET = "LABEL_TARGET"
    SESSION_METADATA = "SESSION_METADATA"
    QUALITY_FLAG = "QUALITY_FLAG"
    PROVIDER_METADATA = "PROVIDER_METADATA"
    COST_METADATA = "COST_METADATA"


SESSION_METADATA_FIELDS: frozenset[str] = frozenset(
    {
        "session_label",
        "session_segment",
        "rth_flag",
        "eth_flag",
        "session_minute",
        "minutes_from_rth_open",
    }
)
SESSION_METADATA_ROLE_MARKER = "SESSION_METADATA_POINT_IN_TIME"
FORBIDDEN_FUTURE_FIELDS: frozenset[str] = frozenset(
    {
        "forward_return",
        "triple_barrier",
        "target_before_stop",
        "future_liquidity_quality",
        "final_session_high",
        "final_session_low",
        "final_session_vwap",
        "label_value",
        "label_outcome",
        "label_available_ts",
        "horizon_end_ts",
        "y_true",
        "target",
    }
)


@dataclass(frozen=True, slots=True)
class CanonicalInputViewHandle:
    """Reference to a canonical record type usable by downstream runtime phases."""

    view_name: str
    record_type: str
    dataset_version_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "view_name": self.view_name,
            "record_type": self.record_type,
            "dataset_version_id": self.dataset_version_id,
        }


@dataclass(frozen=True, slots=True)
class FeaturePackHandle:
    """Value-free handle for one registered feature pack member."""

    feature_version_id: str
    feature_request_id: str
    feature_set_id: str
    feature_set_version: str
    dataset_version_id: str
    partition_id: str
    materialization_plan_id: str
    first_event_ts: str
    last_event_ts: str
    first_available_ts: str
    last_available_ts: str
    lifecycle_state: str

    @property
    def available_ts(self) -> tuple[str, str]:
        """Return the feature availability window carried by this handle."""

        return (self.first_available_ts, self.last_available_ts)

    def to_dict(self) -> dict[str, object]:
        return {
            "feature_version_id": self.feature_version_id,
            "feature_request_id": self.feature_request_id,
            "feature_set_id": self.feature_set_id,
            "feature_set_version": self.feature_set_version,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "materialization_plan_id": self.materialization_plan_id,
            "event_ts": {
                "first": self.first_event_ts,
                "last": self.last_event_ts,
            },
            "available_ts": {
                "first": self.first_available_ts,
                "last": self.last_available_ts,
            },
            "lifecycle_state": self.lifecycle_state,
        }


@dataclass(frozen=True, slots=True)
class LabelPackHandle:
    """Value-free handle for one registered label pack member."""

    label_version_id: str
    label_spec_id: str
    label_id: str
    dataset_version_id: str
    partition_id: str
    materialization_plan_id: str
    first_event_ts: str
    last_event_ts: str
    first_label_available_ts: str
    last_label_available_ts: str
    lifecycle_state: str

    @property
    def label_available_ts(self) -> tuple[str, str]:
        """Return the label availability window carried by this handle."""

        return (self.first_label_available_ts, self.last_label_available_ts)

    def to_dict(self) -> dict[str, object]:
        return {
            "label_version_id": self.label_version_id,
            "label_spec_id": self.label_spec_id,
            "label_id": self.label_id,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "materialization_plan_id": self.materialization_plan_id,
            "event_ts": {
                "first": self.first_event_ts,
                "last": self.last_event_ts,
            },
            "label_available_ts": {
                "first": self.first_label_available_ts,
                "last": self.last_label_available_ts,
            },
            "lifecycle_state": self.lifecycle_state,
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeInputPack:
    """Immutable, hashable, value-free resolved input bundle."""

    alpha_spec_ref: str
    study_spec_ref: str
    study_input_pack_json: str
    dataset_version_id: str
    dataset_lifecycle_state: str
    dataset_source: str
    dataset_reproducibility_hashes: tuple[tuple[str, str], ...]
    canonical_input_views: tuple[CanonicalInputViewHandle, ...]
    feature_packs: tuple[FeaturePackHandle, ...]
    label_packs: tuple[LabelPackHandle, ...]
    dataset_scope_json: str
    partition_scope_json: str
    session_scope_json: str
    governance_metadata_json: str

    def __init__(
        self,
        *,
        alpha_spec_ref: str,
        study_spec_ref: str,
        study_input_pack: Mapping[str, Any],
        dataset_version_id: str,
        dataset_lifecycle_state: str,
        dataset_source: str,
        dataset_reproducibility_hashes: Mapping[str, object],
        canonical_input_views: Sequence[CanonicalInputViewHandle],
        feature_packs: Sequence[FeaturePackHandle],
        label_packs: Sequence[LabelPackHandle],
        dataset_scope: Mapping[str, Any],
        partition_scope: Mapping[str, Any],
        session_scope: Mapping[str, Any],
        governance_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "alpha_spec_ref", _require_text(alpha_spec_ref, "alpha_spec_ref"))
        object.__setattr__(self, "study_spec_ref", _require_text(study_spec_ref, "study_spec_ref"))
        object.__setattr__(
            self,
            "study_input_pack_json",
            _canonical_json(study_input_pack, "study_input_pack"),
        )
        object.__setattr__(
            self,
            "dataset_version_id",
            _require_text(dataset_version_id, "dataset_version_id"),
        )
        object.__setattr__(
            self,
            "dataset_lifecycle_state",
            _require_accepted_lifecycle_state(dataset_lifecycle_state),
        )
        object.__setattr__(self, "dataset_source", _require_text(dataset_source, "dataset_source"))
        object.__setattr__(
            self,
            "dataset_reproducibility_hashes",
            _freeze_string_mapping(dataset_reproducibility_hashes),
        )
        object.__setattr__(self, "canonical_input_views", tuple(canonical_input_views))
        object.__setattr__(self, "feature_packs", tuple(feature_packs))
        object.__setattr__(self, "label_packs", tuple(label_packs))
        object.__setattr__(
            self,
            "dataset_scope_json",
            _canonical_json(dataset_scope, "dataset_scope"),
        )
        object.__setattr__(
            self,
            "partition_scope_json",
            _canonical_json(partition_scope, "partition_scope"),
        )
        object.__setattr__(
            self,
            "session_scope_json",
            _canonical_json(session_scope, "session_scope"),
        )
        object.__setattr__(
            self,
            "governance_metadata_json",
            _canonical_json(governance_metadata or {}, "governance_metadata"),
        )

    @property
    def study_input_pack(self) -> dict[str, JsonValue]:
        """Return the governed StudyInputPack payload as a defensive copy."""

        return _json_dict(self.study_input_pack_json)

    @property
    def dataset_scope(self) -> dict[str, JsonValue]:
        """Return the resolved dataset scope as a defensive copy."""

        return _json_dict(self.dataset_scope_json)

    @property
    def partition_scope(self) -> dict[str, JsonValue]:
        """Return the resolved partition scope as a defensive copy."""

        return _json_dict(self.partition_scope_json)

    @property
    def session_scope(self) -> dict[str, JsonValue]:
        """Return the resolved session scope as a defensive copy."""

        return _json_dict(self.session_scope_json)

    @property
    def governance_metadata(self) -> dict[str, JsonValue]:
        """Return governance contamination metadata as a defensive copy."""

        return _json_dict(self.governance_metadata_json)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible, value-free mapping."""

        return {
            "schema": "alpha_system.runtime.input_pack.v1",
            "alpha_spec_ref": self.alpha_spec_ref,
            "study_spec_ref": self.study_spec_ref,
            "study_input_pack": self.study_input_pack,
            "dataset_version": {
                "dataset_version_id": self.dataset_version_id,
                "lifecycle_state": self.dataset_lifecycle_state,
                "source": self.dataset_source,
                "reproducibility_hashes": dict(self.dataset_reproducibility_hashes),
            },
            "canonical_input_views": [view.to_dict() for view in self.canonical_input_views],
            "feature_packs": [pack.to_dict() for pack in self.feature_packs],
            "label_packs": [pack.to_dict() for pack in self.label_packs],
            "dataset_scope": self.dataset_scope,
            "partition_scope": self.partition_scope,
            "session_scope": self.session_scope,
            "governance_metadata": self.governance_metadata,
            "value_free": True,
        }


@dataclass(frozen=True, slots=True)
class RuntimeInputResolutionResult:
    """Resolved input pack or visible fail-closed rejection reasons."""

    status: RuntimeEntryStatus
    reasons: tuple[RejectionReasonRecord, ...]
    input_pack: RuntimeInputPack | None = None

    @property
    def resolved(self) -> bool:
        return self.status is RuntimeEntryStatus.INPUTS_RESOLVED

    @property
    def blocked(self) -> bool:
        return self.status is RuntimeEntryStatus.INPUTS_BLOCKED

    @property
    def inconclusive(self) -> bool:
        return self.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
            "input_pack": None if self.input_pack is None else self.input_pack.to_dict(),
        }


class RuntimeInputResolverError(ValueError):
    """Internal fail-closed error carrying a rejection-shaped reason."""

    def __init__(self, reason: RejectionReasonRecord):
        self.reason = reason
        super().__init__(reason.message)


class FeatureLabelPackResolver:
    """Resolve FeatureStore and LabelStore handles without materializing values."""

    def __init__(
        self,
        *,
        feature_store: object | None = None,
        label_registry: object | None = None,
        alpha_data_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._feature_store = feature_store
        self._label_registry = label_registry
        self._alpha_data_root = alpha_data_root
        self._env = env

    @property
    def feature_store(self) -> object:
        """Return the FeatureStore facade, constructing it lazily when needed."""

        if self._feature_store is None:
            self._feature_store = FeatureStore.from_alpha_data_root(
                self._alpha_data_root,
                env=self._env,
            )
        return self._feature_store

    @property
    def label_registry(self) -> object:
        """Return the LabelRegistry facade, constructing it lazily when needed."""

        if self._label_registry is None:
            self._label_registry = LabelRegistry.from_alpha_data_root(
                self._alpha_data_root,
                env=self._env,
            )
        return self._label_registry

    def resolve_feature_packs(
        self,
        feature_pack_refs: Sequence[str],
        *,
        expected_dataset_version_id: str,
        expected_feature_request_ids: Sequence[str],
        partition_id: str,
    ) -> tuple[FeaturePackHandle, ...]:
        """Resolve feature pack handles through the FeatureStore/FeatureRegistry."""

        if not feature_pack_refs and expected_feature_request_ids:
            raise RuntimeInputResolverError(
                _reason(
                    code="missing_feature_pack_refs",
                    message="StudyInputPack feature requests require versioned feature pack refs",
                    field="feature_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="feature version handles",
                    actual="missing",
                )
            )
        expected_ids = set(expected_feature_request_ids)
        handles: list[FeaturePackHandle] = []
        for index, ref in enumerate(feature_pack_refs):
            ref_value = _normalize_feature_pack_ref(ref, field=f"feature_pack_refs[{index}]")
            record = self._resolve_feature_record(ref_value)
            if record is None:
                raise RuntimeInputResolverError(
                    _reason(
                        code="feature_pack_not_found",
                        message="FeatureStore did not resolve the requested feature pack",
                        field=f"feature_pack_refs[{index}]",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected="registered feature version",
                        actual=ref_value,
                    )
                )
            _require_registered_pack_lifecycle(
                record,
                pack_kind="feature_pack",
                field=f"feature_pack_refs[{index}].lifecycle_state",
                replacement_field="replacement_feature_version_id",
                replacement_id=self._feature_replacement_id(ref_value, record),
            )
            handle = _feature_handle_from_record(record)
            _require_pack_dataset_match(
                handle.dataset_version_id,
                expected_dataset_version_id,
                field=f"feature_pack_refs[{index}].dataset_version_id",
                code="feature_pack_dataset_version_mismatch",
                message="feature packs must be bound to the accepted DatasetVersion",
            )
            _require_partition_match(
                handle.partition_id,
                partition_id,
                field=f"feature_pack_refs[{index}].partition_id",
                code="feature_pack_partition_mismatch",
                message="feature pack partition must match the runtime partition scope",
            )
            if expected_ids and handle.feature_request_id not in expected_ids:
                raise RuntimeInputResolverError(
                    _reason(
                        code="feature_pack_not_governed_by_study_input_pack",
                        message="feature pack must trace to a StudyInputPack FeatureRequest",
                        field=f"feature_pack_refs[{index}].feature_request_id",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected=",".join(sorted(expected_ids)),
                        actual=handle.feature_request_id,
                    )
                )
            _reject_label_as_live_feature(record, field=f"feature_pack_refs[{index}]")
            handles.append(handle)
        return tuple(handles)

    def resolve_label_packs(
        self,
        label_pack_refs: Sequence[str],
        *,
        expected_dataset_version_id: str,
        expected_label_spec_ids: Sequence[str],
        partition_id: str,
    ) -> tuple[LabelPackHandle, ...]:
        """Resolve label pack handles through the LabelRegistry."""

        if not label_pack_refs and expected_label_spec_ids:
            raise RuntimeInputResolverError(
                _reason(
                    code="missing_label_pack_refs",
                    message="StudyInputPack label specs require versioned label pack refs",
                    field="label_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="label version handles",
                    actual="missing",
                )
            )
        expected_ids = set(expected_label_spec_ids)
        handles: list[LabelPackHandle] = []
        for index, ref in enumerate(label_pack_refs):
            ref_value = _normalize_label_pack_ref(ref, field=f"label_pack_refs[{index}]")
            record = self._resolve_label_record(ref_value)
            if record is None:
                raise RuntimeInputResolverError(
                    _reason(
                        code="label_pack_not_found",
                        message="LabelRegistry did not resolve the requested label pack",
                        field=f"label_pack_refs[{index}]",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected="registered label version",
                        actual=ref_value,
                    )
                )
            _require_registered_pack_lifecycle(
                record,
                pack_kind="label_pack",
                field=f"label_pack_refs[{index}].lifecycle_state",
                replacement_field="replacement_label_version_id",
                replacement_id=self._label_replacement_id(ref_value, record),
            )
            handle = _label_handle_from_record(record)
            _require_pack_dataset_match(
                handle.dataset_version_id,
                expected_dataset_version_id,
                field=f"label_pack_refs[{index}].dataset_version_id",
                code="label_pack_dataset_version_mismatch",
                message="label packs must be bound to the accepted DatasetVersion",
            )
            _require_partition_match(
                handle.partition_id,
                partition_id,
                field=f"label_pack_refs[{index}].partition_id",
                code="label_pack_partition_mismatch",
                message="label pack partition must match the runtime partition scope",
            )
            if expected_ids and handle.label_spec_id not in expected_ids:
                raise RuntimeInputResolverError(
                    _reason(
                        code="label_pack_not_governed_by_study_input_pack",
                        message="label pack must trace to a StudyInputPack LabelSpec",
                        field=f"label_pack_refs[{index}].label_spec_id",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected=",".join(sorted(expected_ids)),
                        actual=handle.label_spec_id,
                    )
                )
            handles.append(handle)
        return tuple(handles)

    def _resolve_feature_record(self, feature_version_id: str) -> object | None:
        try:
            store = self.feature_store
            active_resolver = getattr(store, "resolve_active_feature", None)
            if active_resolver is None:
                active_resolver = getattr(store, "resolve_registered_feature", None)
            if active_resolver is not None:
                active_record = active_resolver(feature_version_id)
                if active_record is not None:
                    return active_record
            resolver = getattr(store, "resolve_feature_by_version", None)
            if resolver is None:
                resolver = getattr(store, "resolve_feature", None)
            if resolver is None:
                raise RuntimeInputResolverError(
                    _reason(
                        code="feature_store_resolver_missing",
                        message="FeatureStore must expose resolve_feature_by_version",
                        field="feature_store",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected="FeatureStore resolver method",
                        actual=type(store).__name__,
                    )
                )
            return resolver(feature_version_id)
        except (FeatureRegistryError, FeatureStoreError) as exc:
            raise RuntimeInputResolverError(
                _reason(
                    code="feature_store_resolution_failed",
                    message="FeatureStore failed closed while resolving a feature pack",
                    field="feature_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="registered feature version",
                    actual=str(exc),
                )
            ) from exc

    def _feature_replacement_id(self, feature_version_id: str, record: object) -> str:
        replacement = _replacement_id_from_record(record, "replacement_feature_version_id")
        if replacement:
            return replacement
        try:
            store = self.feature_store
            resolver = getattr(store, "resolve_deprecation", None)
            if resolver is None:
                registry = getattr(store, "registry", None)
                resolver = getattr(registry, "resolve_deprecation", None)
            if resolver is None:
                return ""
            deprecation = resolver(feature_version_id)
        except (FeatureRegistryError, FeatureStoreError) as exc:
            raise RuntimeInputResolverError(
                _reason(
                    code="feature_store_resolution_failed",
                    message="FeatureStore failed closed while resolving feature deprecation metadata",
                    field="feature_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="feature deprecation metadata",
                    actual=str(exc),
                )
            ) from exc
        return _replacement_id_from_record(deprecation, "replacement_feature_version_id")

    def _resolve_label_record(self, label_version_id: str) -> object | None:
        try:
            registry = self.label_registry
            active_resolver = getattr(registry, "resolve_active_label", None)
            if active_resolver is None:
                active_resolver = getattr(registry, "resolve_registered_label", None)
            if active_resolver is not None:
                active_record = active_resolver(label_version_id)
                if active_record is not None:
                    return active_record
            resolver = getattr(registry, "resolve_label_by_version", None)
            if resolver is None:
                resolver = getattr(registry, "resolve_label", None)
            if resolver is None:
                raise RuntimeInputResolverError(
                    _reason(
                        code="label_registry_resolver_missing",
                        message="LabelRegistry must expose resolve_label_by_version",
                        field="label_registry",
                        state=RuntimeEntryStatus.INPUTS_BLOCKED,
                        expected="LabelRegistry resolver method",
                        actual=type(registry).__name__,
                    )
                )
            return resolver(label_version_id)
        except LabelRegistryError as exc:
            raise RuntimeInputResolverError(
                _reason(
                    code="label_registry_resolution_failed",
                    message="LabelRegistry failed closed while resolving a label pack",
                    field="label_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="registered label version",
                    actual=str(exc),
                )
            ) from exc

    def _label_replacement_id(self, label_version_id: str, record: object) -> str:
        replacement = _replacement_id_from_record(record, "replacement_label_version_id")
        if replacement:
            return replacement
        try:
            registry = self.label_registry
            resolver = getattr(registry, "resolve_deprecation", None)
            if resolver is None:
                return ""
            deprecation = resolver(label_version_id)
        except LabelRegistryError as exc:
            raise RuntimeInputResolverError(
                _reason(
                    code="label_registry_resolution_failed",
                    message="LabelRegistry failed closed while resolving label deprecation metadata",
                    field="label_pack_refs",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="label deprecation metadata",
                    actual=str(exc),
                )
            ) from exc
        return _replacement_id_from_record(deprecation, "replacement_label_version_id")


def resolve_runtime_input_pack(
    entry_result: RuntimeEntryResult,
    *,
    registry_path: str | Path,
    dataset_lifecycle_state: str | None = None,
    feature_pack_refs: Sequence[str] = (),
    label_pack_refs: Sequence[str] = (),
    partition_scope: Mapping[str, Any] | None = None,
    session_scope: Mapping[str, Any] | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
    partition_purpose: str = "research_runtime_resolution",
    partition_plan: DatasetPartitionPlan | Mapping[str, object] | None = None,
    feature_label_resolver: FeatureLabelPackResolver | None = None,
    dataset_version_resolver: DatasetVersionResolver = resolve_dataset_version,
) -> RuntimeInputResolutionResult:
    """Resolve an admitted entry result into a value-free RuntimeInputPack."""

    preflight = _preflight_entry_result(entry_result)
    if preflight is not None:
        return preflight

    assert entry_result.study_input_pack is not None
    assert entry_result.target_dataset_version_id is not None
    assert entry_result.dataset_scope is not None

    blocked_reasons: list[RejectionReasonRecord] = []
    inconclusive_reasons: list[RejectionReasonRecord] = []

    blocked_reasons.extend(
        _forbidden_reference_reasons(
            {
                "registry_path": registry_path,
                "dataset_scope": entry_result.dataset_scope,
                "partition_scope": partition_scope,
                "session_scope": session_scope,
                "governance_metadata": governance_metadata,
                "feature_pack_refs": list(feature_pack_refs),
                "label_pack_refs": list(label_pack_refs),
            }
        )
    )

    if partition_scope is None:
        inconclusive_reasons.append(
            _reason(
                code="missing_partition_scope",
                message="runtime input resolution requires an explicit partition scope",
                field="partition_scope",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                expected="partition scope mapping with partition_id",
                actual="missing",
            )
        )
    if session_scope is None:
        inconclusive_reasons.append(
            _reason(
                code="missing_session_scope",
                message="runtime input resolution requires an explicit session scope",
                field="session_scope",
                state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                expected="session scope mapping",
                actual="missing",
            )
        )
    if blocked_reasons or inconclusive_reasons:
        return _reject(blocked_reasons, inconclusive_reasons)

    assert partition_scope is not None
    assert session_scope is not None

    partition_id, partition_reason = _partition_id_from_scope(partition_scope)
    if partition_reason is not None:
        return _reject([], [partition_reason])

    dataset_version = _resolve_dataset_version(
        dataset_version_resolver,
        registry_path=registry_path,
        dataset_version_id=entry_result.target_dataset_version_id,
    )
    if isinstance(dataset_version, RuntimeInputResolutionResult):
        return dataset_version

    fallback_state = getattr(dataset_version, "lifecycle_state", None)
    lifecycle_state, lifecycle_reason = _coerce_lifecycle_state(
        dataset_lifecycle_state,
        fallback_state,
    )
    if lifecycle_reason is not None:
        return _reject([], [lifecycle_reason])

    if lifecycle_state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
        return _reject(
            [
                _reason(
                    code="inadmissible_dataset_lifecycle_state",
                    message="DatasetVersion lifecycle state is not admissible for runtime input",
                    field="dataset_lifecycle_state",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=", ".join(sorted(ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES)),
                    actual=lifecycle_state,
                )
            ],
            [],
        )

    partition_gate = _evaluate_partition_gate(
        partition_id=partition_id,
        partition_scope=partition_scope,
        governance_metadata=governance_metadata,
        partition_purpose=partition_purpose,
        partition_plan=partition_plan,
    )
    if partition_gate is not None:
        return partition_gate

    resolver = feature_label_resolver or FeatureLabelPackResolver()
    try:
        feature_handles = resolver.resolve_feature_packs(
            feature_pack_refs,
            expected_dataset_version_id=entry_result.target_dataset_version_id,
            expected_feature_request_ids=entry_result.study_input_pack.feature_request_ids,
            partition_id=partition_id,
        )
        label_handles = resolver.resolve_label_packs(
            label_pack_refs,
            expected_dataset_version_id=entry_result.target_dataset_version_id,
            expected_label_spec_ids=entry_result.study_input_pack.label_spec_ids,
            partition_id=partition_id,
        )
    except RuntimeInputResolverError as exc:
        return _reject([exc.reason], [])

    dataset_source = _require_text(getattr(dataset_version, "source", ""), "dataset_version.source")
    if _source_family_merge_requested(dataset_source, entry_result.dataset_scope):
        return _reject(
            [
                _reason(
                    code="merged_dataset_version_sources_requested",
                    message="Databento and IBKR DatasetVersions must not be merged",
                    field="dataset_scope",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="one DatasetVersion provenance family",
                    actual="databento,ibkr",
                )
            ],
            [],
        )

    try:
        input_pack = RuntimeInputPack(
            alpha_spec_ref=_require_text(entry_result.alpha_spec_ref, "alpha_spec_ref"),
            study_spec_ref=_require_text(entry_result.study_spec_ref, "study_spec_ref"),
            study_input_pack=entry_result.study_input_pack.to_dict(),
            dataset_version_id=entry_result.target_dataset_version_id,
            dataset_lifecycle_state=lifecycle_state,
            dataset_source=dataset_source,
            dataset_reproducibility_hashes=_dataset_hashes(dataset_version),
            canonical_input_views=_canonical_input_views(entry_result.target_dataset_version_id),
            feature_packs=feature_handles,
            label_packs=label_handles,
            dataset_scope=entry_result.dataset_scope,
            partition_scope=partition_scope,
            session_scope=session_scope,
            governance_metadata=governance_metadata,
        )
    except (GovernanceSerializationError, RuntimeInputResolverError, ValueError) as exc:
        return _reject(
            [
                _reason(
                    code="runtime_input_pack_contract_invalid",
                    message="RuntimeInputPack failed contract construction",
                    field="RuntimeInputPack",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="value-free JSON-compatible input pack",
                    actual=str(exc),
                )
            ],
            [],
        )

    return RuntimeInputResolutionResult(
        status=RuntimeEntryStatus.INPUTS_RESOLVED,
        input_pack=input_pack,
        reasons=(
            _reason(
                code="runtime_input_pack_resolved",
                message="runtime input pack resolved accepted DatasetVersion and pack handles",
                field="RuntimeInputPack",
                state=RuntimeEntryStatus.INPUTS_RESOLVED,
                expected="value-free input handles",
                actual="value-free input handles",
            ),
        ),
    )


def _preflight_entry_result(
    entry_result: RuntimeEntryResult,
) -> RuntimeInputResolutionResult | None:
    if not isinstance(entry_result, RuntimeEntryResult):
        return RuntimeInputResolutionResult(
            status=RuntimeEntryStatus.INPUTS_BLOCKED,
            reasons=(
                _reason(
                    code="invalid_runtime_entry_result",
                    message="runtime input resolution requires a RuntimeEntryResult",
                    field="entry_result",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="RuntimeEntryResult",
                    actual=type(entry_result).__name__,
                ),
            ),
        )
    if entry_result.status is RuntimeEntryStatus.INPUTS_BLOCKED:
        return RuntimeInputResolutionResult(
            status=RuntimeEntryStatus.INPUTS_BLOCKED,
            reasons=entry_result.reasons
            + (
                _reason(
                    code="runtime_entry_blocked",
                    message="runtime input resolution refuses a blocked entry result",
                    field="entry_result.status",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected=RuntimeEntryStatus.INPUTS_RESOLVED.value,
                    actual=entry_result.status.value,
                ),
            ),
        )
    if entry_result.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE:
        return RuntimeInputResolutionResult(
            status=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            reasons=entry_result.reasons
            + (
                _reason(
                    code="runtime_entry_inconclusive",
                    message="runtime input resolution requires conclusive entry metadata",
                    field="entry_result.status",
                    state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                    expected=RuntimeEntryStatus.INPUTS_RESOLVED.value,
                    actual=entry_result.status.value,
                ),
            ),
        )
    if (
        entry_result.study_input_pack is None
        or entry_result.target_dataset_version_id is None
        or entry_result.dataset_scope is None
    ):
        return RuntimeInputResolutionResult(
            status=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            reasons=(
                _reason(
                    code="runtime_entry_result_missing_resolved_inputs",
                    message=(
                        "resolved entry result is missing StudyInputPack or DatasetVersion refs"
                    ),
                    field="entry_result",
                    state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
                    expected="StudyInputPack, DatasetVersion id, dataset scope",
                    actual="missing",
                ),
            ),
        )
    return None


def _resolve_dataset_version(
    resolver: DatasetVersionResolver,
    *,
    registry_path: str | Path,
    dataset_version_id: str,
) -> object | RuntimeInputResolutionResult:
    try:
        dataset_version = resolver(registry_path, dataset_version_id)
    except (DataFoundationValidationError, OSError, ValueError) as exc:
        return _reject(
            [
                _reason(
                    code="dataset_version_resolution_failed",
                    message="DatasetVersion resolution failed through resolve_dataset_version",
                    field="target_dataset_version_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="accepted DatasetVersion registry record",
                    actual=str(exc),
                )
            ],
            [],
        )
    if dataset_version is None:
        return _reject(
            [
                _reason(
                    code="dataset_version_not_found",
                    message="DatasetVersion was not found in the sanctioned registry",
                    field="target_dataset_version_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="accepted DatasetVersion registry record",
                    actual=dataset_version_id,
                )
            ],
            [],
        )
    return dataset_version


def _evaluate_partition_gate(
    *,
    partition_id: str,
    partition_scope: Mapping[str, Any],
    governance_metadata: Mapping[str, Any] | None,
    partition_purpose: str,
    partition_plan: DatasetPartitionPlan | Mapping[str, object] | None,
) -> RuntimeInputResolutionResult | None:
    try:
        plan = _coerce_partition_plan(partition_plan)
    except DataFoundationValidationError as exc:
        return _reject(
            [
                _reason(
                    code="invalid_partition_plan",
                    message="partition plan failed the data-foundation partition contract",
                    field="partition_plan",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="DatasetPartitionPlan",
                    actual=str(exc),
                )
            ],
            [],
        )
    normalized_purpose = _normalize_token(partition_purpose)
    if partition_id == "locked_test_candidate" and "selection" in normalized_purpose:
        return _reject(
            [
                _reason(
                    code="locked_test_selection_forbidden",
                    message="runtime input resolution refuses selection on the locked test",
                    field="partition_scope.partition_id",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="development or validation selection partition",
                    actual=partition_id,
                )
            ],
            [],
        )

    if partition_id in LOCKED_PARTITION_IDS:
        try:
            feature_consumption.require_partition_access(
                partition_id=partition_id,
                purpose=partition_purpose,
                governance_metadata=governance_metadata,
                partition_plan=plan,
            )
        except DataFoundationValidationError as exc:
            state = RuntimeEntryStatus.INPUTS_INCONCLUSIVE
            return _reject(
                [],
                [
                    _reason(
                        code="locked_partition_governance_metadata_missing",
                        message="locked or shadow partition use requires governance metadata",
                        field="governance_metadata",
                        state=state,
                        expected="substantive governance contamination metadata",
                        actual=str(exc),
                    )
                ],
            )

    if _selection_on_locked_marker(partition_scope):
        return _reject(
            [
                _reason(
                    code="locked_test_selection_forbidden",
                    message="partition scope must not request selection on locked-test data",
                    field="partition_scope",
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="no locked-test selection",
                    actual=str(partition_scope),
                )
            ],
            [],
        )
    return None


def _feature_handle_from_record(record: object) -> FeaturePackHandle:
    feature_spec = getattr(record, "feature_spec", None)
    handle = FeaturePackHandle(
        feature_version_id=_require_text(
            _first_present(
                getattr(record, "feature_version_id", None),
                getattr(getattr(record, "feature_version", None), "feature_version_id", None),
            ),
            "feature_version_id",
        ),
        feature_request_id=_require_text(
            _first_present(
                getattr(record, "feature_request_id", None),
                getattr(feature_spec, "feature_request_id", None),
            ),
            "feature_request_id",
        ),
        feature_set_id=_require_text(getattr(record, "feature_set_id", None), "feature_set_id"),
        feature_set_version=_require_text(
            getattr(record, "feature_set_version", None),
            "feature_set_version",
        ),
        dataset_version_id=_require_text(
            getattr(record, "dataset_version_id", None),
            "dataset_version_id",
        ),
        partition_id=_require_text(getattr(record, "partition_id", None), "partition_id"),
        materialization_plan_id=_require_text(
            getattr(record, "materialization_plan_id", None),
            "materialization_plan_id",
        ),
        first_event_ts=_aware_iso(getattr(record, "first_event_ts", None), "first_event_ts"),
        last_event_ts=_aware_iso(getattr(record, "last_event_ts", None), "last_event_ts"),
        first_available_ts=_aware_iso(
            getattr(record, "first_available_ts", None),
            "first_available_ts",
            missing_code="feature_available_ts_missing",
        ),
        last_available_ts=_aware_iso(
            getattr(record, "last_available_ts", None),
            "last_available_ts",
            missing_code="feature_available_ts_missing",
        ),
        lifecycle_state=_pack_lifecycle_state(
            record,
            field="feature_pack.lifecycle_state",
            missing_code="feature_pack_lifecycle_state_missing",
        ),
    )
    _require_availability_not_before_event(
        first_available_ts=handle.first_available_ts,
        first_event_ts=handle.first_event_ts,
        last_available_ts=handle.last_available_ts,
        last_event_ts=handle.last_event_ts,
        code="feature_available_ts_precedes_event_ts",
        field="feature_pack.available_ts",
        message="feature available_ts must not precede feature event_ts",
    )
    return handle


def _label_handle_from_record(record: object) -> LabelPackHandle:
    label_contract = getattr(record, "label_contract", None)
    handle = LabelPackHandle(
        label_version_id=_require_text(
            _first_present(
                getattr(record, "label_version_id", None),
                getattr(getattr(record, "label_version", None), "label_version_id", None),
            ),
            "label_version_id",
        ),
        label_spec_id=_require_text(
            _first_present(
                getattr(record, "label_spec_id", None),
                getattr(label_contract, "label_spec_id", None),
            ),
            "label_spec_id",
        ),
        label_id=_require_text(
            _first_present(
                getattr(record, "label_id", None),
                getattr(label_contract, "label_id", None),
            ),
            "label_id",
        ),
        dataset_version_id=_require_text(
            getattr(record, "dataset_version_id", None),
            "dataset_version_id",
        ),
        partition_id=_require_text(getattr(record, "partition_id", None), "partition_id"),
        materialization_plan_id=_require_text(
            getattr(record, "materialization_plan_id", None),
            "materialization_plan_id",
        ),
        first_event_ts=_aware_iso(getattr(record, "first_event_ts", None), "first_event_ts"),
        last_event_ts=_aware_iso(getattr(record, "last_event_ts", None), "last_event_ts"),
        first_label_available_ts=_aware_iso(
            getattr(record, "first_label_available_ts", None),
            "first_label_available_ts",
            missing_code="label_available_ts_missing",
        ),
        last_label_available_ts=_aware_iso(
            getattr(record, "last_label_available_ts", None),
            "last_label_available_ts",
            missing_code="label_available_ts_missing",
        ),
        lifecycle_state=_pack_lifecycle_state(
            record,
            field="label_pack.lifecycle_state",
            missing_code="label_pack_lifecycle_state_missing",
        ),
    )
    _require_availability_not_before_event(
        first_available_ts=handle.first_label_available_ts,
        first_event_ts=handle.first_event_ts,
        last_available_ts=handle.last_label_available_ts,
        last_event_ts=handle.last_event_ts,
        code="label_available_ts_precedes_event_ts",
        field="label_pack.label_available_ts",
        message="label_available_ts must not precede label event_ts",
    )
    return handle


def _reject_label_as_live_feature(record: object, *, field: str) -> None:
    feature_spec = getattr(record, "feature_spec", None)
    if feature_spec is None:
        return
    live = bool(getattr(feature_spec, "live", True))
    inputs = getattr(feature_spec, "inputs", None)
    fields = tuple(str(item) for item in getattr(inputs, "fields", ()))
    input_views = tuple(str(item) for item in getattr(inputs, "input_views", ()))
    field_roles = _field_roles_from_record(record, inputs)
    suspicious_fields = tuple(
        item for item in fields if _looks_like_label_feature_field(item, field_roles)
    )
    suspicious_views = tuple(
        item
        for item in input_views
        if _is_forbidden_future_field(item)
        or (
            "label" in _normalize_token(item)
            and not _is_exempt_session_field(item, field_roles)
        )
    )
    if live and (suspicious_fields or suspicious_views):
        actual = ",".join(suspicious_fields + suspicious_views)
        raise RuntimeInputResolverError(
            _reason(
                code="label_as_feature_input",
                message="labels must not be exposed as live feature inputs",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="canonical feature inputs only",
                actual=actual,
            )
        )


def _normalize_feature_pack_ref(value: object, *, field: str) -> str:
    text = _require_text(value, field)
    if LABEL_VERSION_PATTERN.fullmatch(text) or text.startswith("lspec_"):
        raise RuntimeInputResolverError(
            _reason(
                code="label_as_feature_input",
                message="label refs must not be supplied as feature pack refs",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="feature version handle",
                actual=text,
            )
        )
    if not FEATURE_VERSION_PATTERN.fullmatch(text):
        raise RuntimeInputResolverError(
            _reason(
                code="invalid_feature_pack_ref",
                message="feature pack refs must be FeatureVersion ids",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="fver_<64-hex-content-hash>",
                actual=text,
            )
        )
    return text


def _normalize_label_pack_ref(value: object, *, field: str) -> str:
    text = _require_text(value, field)
    if not LABEL_VERSION_PATTERN.fullmatch(text):
        raise RuntimeInputResolverError(
            _reason(
                code="invalid_label_pack_ref",
                message="label pack refs must be LabelVersion ids",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="lver_<64-hex-content-hash>",
                actual=text,
            )
        )
    return text


def _require_pack_dataset_match(
    actual_dataset_version_id: str,
    expected_dataset_version_id: str,
    *,
    field: str,
    code: str,
    message: str,
) -> None:
    if actual_dataset_version_id != expected_dataset_version_id:
        raise RuntimeInputResolverError(
            _reason(
                code=code,
                message=message,
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=expected_dataset_version_id,
                actual=actual_dataset_version_id,
            )
        )


def _require_partition_match(
    actual_partition_id: str,
    expected_partition_id: str,
    *,
    field: str,
    code: str,
    message: str,
) -> None:
    if actual_partition_id != expected_partition_id:
        raise RuntimeInputResolverError(
            _reason(
                code=code,
                message=message,
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=expected_partition_id,
                actual=actual_partition_id,
            )
        )


def _require_registered_pack_lifecycle(
    record: object,
    *,
    pack_kind: str,
    field: str,
    replacement_field: str,
    replacement_id: str,
) -> None:
    state = _pack_lifecycle_state(
        record,
        field=field,
        missing_code=f"{pack_kind}_lifecycle_state_missing",
    )
    if state == RUNTIME_PACK_LIFECYCLE_STATE:
        return
    is_deprecated = state == "DEPRECATED"
    actual = state
    if replacement_id:
        actual = f"{state}; {replacement_field}={replacement_id}"
    raise RuntimeInputResolverError(
        _reason(
            code=f"{pack_kind}_deprecated" if is_deprecated else f"{pack_kind}_not_registered",
            message=f"{pack_kind} lifecycle_state must be REGISTERED for runtime resolution",
            field=field,
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected=RUNTIME_PACK_LIFECYCLE_STATE,
            actual=actual,
        )
    )


def _pack_lifecycle_state(record: object, *, field: str, missing_code: str) -> str:
    raw_state = getattr(record, "lifecycle_state", None)
    if raw_state is None:
        raise RuntimeInputResolverError(
            _reason(
                code=missing_code,
                message="runtime pack resolution requires an explicit lifecycle_state",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=RUNTIME_PACK_LIFECYCLE_STATE,
                actual="missing",
            )
        )
    return _enum_value(raw_state).strip().upper()


def _replacement_id_from_record(record: object | None, field: str) -> str:
    if record is None:
        return ""
    raw = getattr(record, field, "")
    if raw is None:
        return ""
    return str(raw).strip()


def _require_availability_not_before_event(
    *,
    first_available_ts: str,
    first_event_ts: str,
    last_available_ts: str,
    last_event_ts: str,
    code: str,
    field: str,
    message: str,
) -> None:
    if _parse_iso(first_available_ts) < _parse_iso(first_event_ts):
        raise RuntimeInputResolverError(
            _reason(
                code=code,
                message=message,
                field=f"{field}.first",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=f">= {first_event_ts}",
                actual=first_available_ts,
            )
        )
    if _parse_iso(last_available_ts) < _parse_iso(last_event_ts):
        raise RuntimeInputResolverError(
            _reason(
                code=code,
                message=message,
                field=f"{field}.last",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected=f">= {last_event_ts}",
                actual=last_available_ts,
            )
        )


def _coerce_lifecycle_state(
    explicit_state: object,
    fallback_state: object,
) -> tuple[str, RejectionReasonRecord | None]:
    state = explicit_state if explicit_state is not None else fallback_state
    if state is None or (isinstance(state, str) and not state.strip()):
        return "", _reason(
            code="missing_dataset_lifecycle_state",
            message="runtime input resolution requires a DatasetVersion lifecycle state",
            field="dataset_lifecycle_state",
            state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            expected=", ".join(sorted(ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES)),
            actual="missing",
        )
    return str(state).strip().upper(), None


def _require_accepted_lifecycle_state(value: str) -> str:
    state = _require_text(value, "dataset_lifecycle_state").upper()
    if state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
        raise ValueError("DatasetVersion lifecycle state is not admissible")
    return state


def _partition_id_from_scope(
    partition_scope: Mapping[str, Any],
) -> tuple[str, RejectionReasonRecord | None]:
    if not isinstance(partition_scope, Mapping):
        return "", _reason(
            code="invalid_partition_scope",
            message="partition scope must be a mapping",
            field="partition_scope",
            state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            expected="partition scope mapping",
            actual=type(partition_scope).__name__,
        )
    value = partition_scope.get("partition_id")
    if value is None:
        value = partition_scope.get("id")
    if value is None:
        return "", _reason(
            code="missing_partition_id",
            message="partition scope must include partition_id",
            field="partition_scope.partition_id",
            state=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
            expected="partition_id",
            actual="missing",
        )
    try:
        return _require_text(value, "partition_scope.partition_id"), None
    except RuntimeInputResolverError as exc:
        return "", exc.reason


def _forbidden_reference_reasons(values: Mapping[str, object]) -> list[RejectionReasonRecord]:
    reasons: list[RejectionReasonRecord] = []
    raw_file = _first_raw_file_reference(values)
    if raw_file is not None:
        field, value = raw_file
        reasons.append(
            _reason(
                code="raw_provider_file_requested",
                message="runtime input resolution must not name raw or heavy data files",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="accepted DatasetVersion and registry handles",
                actual=value,
            )
        )

    provider_metadata = _first_forbidden_provider_metadata(values)
    if provider_metadata is not None:
        field, value = provider_metadata
        reasons.append(
            _reason(
                code="provider_metadata_requested",
                message="runtime input resolution must not request provider-reader access",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="local accepted DatasetVersion handles",
                actual=value,
            )
        )
    return reasons


def _first_raw_file_reference(value: object, *, field: str = "request") -> tuple[str, str] | None:
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized.endswith(RAW_PROVIDER_FILE_SUFFIXES):
            return field, value
        return None
    if isinstance(value, Path):
        return _first_raw_file_reference(value.as_posix(), field=field)
    if isinstance(value, Mapping):
        for key, item in value.items():
            found = _first_raw_file_reference(item, field=f"{field}.{key}")
            if found is not None:
                return found
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for index, item in enumerate(value):
            found = _first_raw_file_reference(item, field=f"{field}[{index}]")
            if found is not None:
                return found
    return None


def _first_forbidden_provider_metadata(
    value: object,
    *,
    field: str = "request",
) -> tuple[str, str] | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if normalized_key in FORBIDDEN_PROVIDER_METADATA_KEYS and _truthy(item):
                return f"{field}.{key}", str(item)
            nested = _first_forbidden_provider_metadata(item, field=f"{field}.{key}")
            if nested is not None:
                return nested
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for index, item in enumerate(value):
            nested = _first_forbidden_provider_metadata(item, field=f"{field}[{index}]")
            if nested is not None:
                return nested
    return None


def _source_family_merge_requested(dataset_source: str, dataset_scope: Mapping[str, Any]) -> bool:
    families = {_normalize_source_family(dataset_source)}
    families.update(_source_families_in_value(dataset_scope))
    return {"databento", "ibkr"}.issubset({family for family in families if family})


def _source_families_in_value(value: object) -> set[str]:
    families: set[str] = set()
    if isinstance(value, str):
        normalized = _normalize_source_family(value)
        if normalized in {"databento", "ibkr"}:
            families.add(normalized)
        return families
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_token = _normalize_token(str(key))
            if key_token in {"source", "source_family", "provider", "provider_family"}:
                families.update(_source_families_in_value(item))
            elif isinstance(item, Mapping | Sequence) and not isinstance(item, str | bytes):
                families.update(_source_families_in_value(item))
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            families.update(_source_families_in_value(item))
    return families


def _normalize_source_family(value: object) -> str:
    token = _normalize_token(str(value))
    if token in {"interactive_brokers", "ib", "ibkr"}:
        return "ibkr"
    if token == "databento":
        return "databento"
    return token


def _selection_on_locked_marker(value: object) -> bool:
    if isinstance(value, str):
        token = _normalize_token(value)
        return "selection" in token and ("locked_test" in token or "locked" in token)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _selection_on_locked_marker(str(key)) or _selection_on_locked_marker(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return any(_selection_on_locked_marker(item) for item in value)
    return False


def _coerce_partition_plan(
    value: DatasetPartitionPlan | Mapping[str, object] | None,
) -> DatasetPartitionPlan | None:
    if value is None or isinstance(value, DatasetPartitionPlan):
        return value
    return DatasetPartitionPlan.from_mapping(value)


def _canonical_input_views(dataset_version_id: str) -> tuple[CanonicalInputViewHandle, ...]:
    return (
        CanonicalInputViewHandle(
            view_name="canonical_ohlcv",
            record_type=_qualified_name(CanonicalBarRecord),
            dataset_version_id=dataset_version_id,
        ),
        CanonicalInputViewHandle(
            view_name="canonical_bbo",
            record_type=_qualified_name(CanonicalBBORecord),
            dataset_version_id=dataset_version_id,
        ),
        CanonicalInputViewHandle(
            view_name="dense_grid_ohlcv",
            record_type=_qualified_name(DenseGridBarRecord),
            dataset_version_id=dataset_version_id,
        ),
    )


def _dataset_hashes(dataset_version: object) -> dict[str, object]:
    hashes = getattr(dataset_version, "reproducibility_hashes", None)
    if isinstance(hashes, Mapping):
        return dict(hashes)
    return {
        key: getattr(dataset_version, key, "")
        for key in (
            "manifest_hash",
            "code_hash",
            "config_hash",
            "quality_report_hash",
        )
        if getattr(dataset_version, key, "")
    }


def _aware_iso(value: object, field: str, *, missing_code: str | None = None) -> str:
    if value is None:
        raise RuntimeInputResolverError(
            _reason(
                code=missing_code or f"missing_{field}",
                message=f"{field} is required for runtime input resolution",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="timezone-aware timestamp",
                actual="missing",
            )
        )
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise RuntimeInputResolverError(
                _reason(
                    code=f"{field}_timezone_missing",
                    message=f"{field} must be timezone-aware",
                    field=field,
                    state=RuntimeEntryStatus.INPUTS_BLOCKED,
                    expected="timezone-aware timestamp",
                    actual=value.isoformat(),
                )
            )
        return value.isoformat()
    if isinstance(value, str):
        parsed = _parse_iso(value)
        return parsed.isoformat()
    raise RuntimeInputResolverError(
        _reason(
            code=f"invalid_{field}",
            message=f"{field} must be a timezone-aware timestamp",
            field=field,
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected="datetime or ISO timestamp",
            actual=type(value).__name__,
        )
    )


def _parse_iso(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeInputResolverError(
            _reason(
                code="timestamp_timezone_missing",
                message="runtime timestamps must be timezone-aware",
                field="timestamp",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="timezone-aware timestamp",
                actual=value,
            )
        )
    return parsed


def _canonical_json(value: object, field_name: str) -> str:
    try:
        return canonical_serialize(_to_json_value(value, field_name=field_name))
    except GovernanceSerializationError:
        raise
    except (TypeError, ValueError) as exc:
        raise RuntimeInputResolverError(
            _reason(
                code="invalid_json_metadata",
                message=f"{field_name} must be JSON-compatible metadata",
                field=field_name,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="JSON-compatible mapping",
                actual=str(exc),
            )
        ) from exc


def _to_json_value(value: object, *, field_name: str) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_name} mapping keys must be strings")
            result[key] = _to_json_value(item, field_name=f"{field_name}.{key}")
        return result
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_to_json_value(item, field_name=f"{field_name}[]") for item in value]
    raise ValueError(f"{field_name} contains unsupported {type(value).__name__}")


def _json_dict(text: str) -> dict[str, JsonValue]:
    value = deserialize(text)
    if not isinstance(value, dict):
        raise RuntimeInputResolverError(
            _reason(
                code="invalid_json_mapping",
                message="RuntimeInputPack stored metadata must be a JSON mapping",
                field="RuntimeInputPack",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="JSON mapping",
                actual=type(value).__name__,
            )
        )
    return dict(value)


def _freeze_string_mapping(value: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(key), str(item)) for key, item in value.items()))


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeInputResolverError(
            _reason(
                code=f"invalid_{field}",
                message=f"{field} must be a non-empty string",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="non-empty string",
                actual=type(value).__name__,
            )
        )
    text = value.strip()
    if not text:
        raise RuntimeInputResolverError(
            _reason(
                code=f"missing_{field}",
                message=f"{field} must be a non-empty string",
                field=field,
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="non-empty string",
                actual="blank",
            )
        )
    return text


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def _looks_like_label_feature_field(
    value: str,
    field_roles: Mapping[str, object] | None = None,
) -> bool:
    if _is_forbidden_future_field(value):
        return True
    if _is_exempt_session_field(value, field_roles):
        return False
    token = _normalize_token(value)
    return (
        token in LABEL_AS_FEATURE_FIELDS
        or token.startswith("label_")
        or token.endswith("_label")
        or token.startswith("future_label")
    )


def _field_roles_from_record(record: object, inputs: object) -> Mapping[str, object]:
    input_metadata = _plain_mapping(getattr(inputs, "input_metadata", {}))
    roles = _field_roles_from_metadata(input_metadata)
    _add_session_metadata_roles(roles, input_metadata, inputs)

    registry_metadata = _plain_mapping(getattr(record, "registry_metadata", {}))
    for key, role in _field_roles_from_metadata(registry_metadata).items():
        roles.setdefault(key, role)
    _add_session_metadata_roles(roles, registry_metadata, inputs)

    return roles


def _field_roles_from_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    field_roles = metadata.get("field_roles")
    if isinstance(field_roles, Mapping):
        return {str(key): role for key, role in field_roles.items()}
    return {}


def _add_session_metadata_roles(
    roles: dict[str, object],
    metadata: Mapping[str, object],
    inputs: object,
) -> None:
    if not _declares_session_metadata_role(metadata):
        return
    fields = tuple(str(item) for item in getattr(inputs, "fields", ()))
    input_views = tuple(str(item) for item in getattr(inputs, "input_views", ()))
    for field in (*fields, *input_views):
        if _normalize_token(field) in SESSION_METADATA_FIELDS:
            roles.setdefault(field, FieldRole.SESSION_METADATA.value)


def _declares_session_metadata_role(metadata: Mapping[str, object]) -> bool:
    role = metadata.get("session_metadata_role")
    return _normalize_role(role) in {
        _normalize_role(SESSION_METADATA_ROLE_MARKER),
        _normalize_role(FieldRole.SESSION_METADATA),
    }


def _plain_mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _normalize_role(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value
    return str(value).strip().lower()


def _is_exempt_session_field(
    field: str,
    field_roles: Mapping[str, object] | None,
) -> bool:
    token = _normalize_token(field)
    if token not in SESSION_METADATA_FIELDS or _is_forbidden_future_field(field):
        return False
    if not isinstance(field_roles, Mapping):
        return False
    role = field_roles.get(field)
    if role is None:
        role = next(
            (
                item
                for key, item in field_roles.items()
                if _normalize_token(str(key)) == token
            ),
            None,
        )
    return _normalize_role(role) == _normalize_role(FieldRole.SESSION_METADATA)


def _is_forbidden_future_field(field: str) -> bool:
    token = _normalize_token(field)
    return (
        token in FORBIDDEN_FUTURE_FIELDS
        or token == "fwd_ret"
        or token.startswith("fwd_ret_")
    )


def _normalize_token(value: str) -> str:
    return "_".join(value.strip().casefold().replace("-", "_").split())


def _truthy(value: object) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, Sequence) and not isinstance(value, str | bytes) and not value:
        return False
    if isinstance(value, Mapping) and not value:
        return False
    return True


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _qualified_name(value: type[object]) -> str:
    return f"{value.__module__}.{value.__qualname__}"


def _reject(
    blocked_reasons: Sequence[RejectionReasonRecord],
    inconclusive_reasons: Sequence[RejectionReasonRecord],
) -> RuntimeInputResolutionResult:
    if blocked_reasons:
        return RuntimeInputResolutionResult(
            status=RuntimeEntryStatus.INPUTS_BLOCKED,
            reasons=tuple(blocked_reasons),
        )
    return RuntimeInputResolutionResult(
        status=RuntimeEntryStatus.INPUTS_INCONCLUSIVE,
        reasons=tuple(inconclusive_reasons),
    )


def _reason(
    *,
    code: str,
    message: str,
    field: str,
    state: RuntimeEntryStatus,
    expected: str,
    actual: str,
) -> RejectionReasonRecord:
    return RuntimeEntryReason(
        code=code,
        message=message,
        field=field,
        decision_state=state,
        expected=expected,
        actual=actual,
    )


__all__ = [
    "CanonicalInputViewHandle",
    "FeatureLabelPackResolver",
    "FeaturePackHandle",
    "LabelPackHandle",
    "RejectionReasonRecord",
    "RuntimeInputPack",
    "RuntimeInputResolutionResult",
    "resolve_runtime_input_pack",
]
