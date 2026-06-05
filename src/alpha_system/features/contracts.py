"""Immutable feature contract objects for the Feature/Label substrate.

The objects in this module define contract metadata only. They do not implement
feature calculations, materialize feature values, persist registries, read data
files, or call external providers.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.features.request_gate import FeatureRequestGateDecision
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    validate_governance_id,
)
from alpha_system.governance.serialization import (
    JsonValue,
    canonical_serialize,
    content_hash,
)

FEATURE_VERSION_ALGORITHM = "feature_version_sha256_v1"
FEATURE_VERSION_PATTERN = re.compile(r"^fver_[a-f0-9]{64}$")
FEATURE_SET_NAMESPACE = "features"
CANONICAL_INPUT_VIEW_NAMES: frozenset[str] = frozenset(
    {
        "canonical_ohlcv",
        "canonical_bbo",
        "canonical_input_views",
        "dense_grid_ohlcv",
    }
)


class FeatureContractError(ValueError):
    """Raised when a feature contract fails closed."""


class FeatureFamily(StrEnum):
    """Feature families planned by the Feature/Label foundation campaign."""

    BASE_OHLCV = "base_ohlcv"
    BBO_TRADABILITY = "bbo_tradability"
    SESSION_CALENDAR_ROLL = "session_calendar_roll"
    CROSS_MARKET = "cross_market"
    LIQUIDITY_STRUCTURE = "liquidity_structure"


class WindowKind(StrEnum):
    """Declarative window shape for a feature contract."""

    POINT_IN_TIME = "point_in_time"
    ROLLING = "rolling"
    EXPANDING = "expanding"
    CENTERED = "centered"
    FUTURE = "future"


class WindowCausality(StrEnum):
    """Whether a window is usable for live features or offline-only work."""

    CAUSAL = "causal"
    CENTERED = "centered"
    FUTURE = "future"


class FitPartitionPolicy(StrEnum):
    """Partition policy used to fit normalization state."""

    DEVELOPMENT_VALIDATION = "development_validation"
    DEVELOPMENT_ONLY = "development_only"
    LOCKED_TEST = "locked_test"


@dataclass(frozen=True, slots=True)
class FrozenJsonMapping:
    """Hashable, deterministic representation of JSON-compatible metadata."""

    items: tuple[tuple[str, object], ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, field_name: str) -> FrozenJsonMapping:
        if isinstance(value, FrozenJsonMapping):
            return value
        if not isinstance(value, Mapping):
            raise FeatureContractError(f"{field_name} must be a mapping")
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise FeatureContractError(f"{field_name} keys must be non-empty strings")
            items.append((key, _freeze_json_value(item, f"{field_name}.{key}")))
        frozen = cls(tuple(sorted(items, key=lambda pair: pair[0])))
        _canonical_json(frozen.to_dict(), field_name)
        return frozen

    def __bool__(self) -> bool:
        return bool(self.items)

    def to_dict(self) -> dict[str, JsonValue]:
        return {key: _thaw_json_value(value) for key, value in self.items}


@dataclass(frozen=True, slots=True)
class FeatureInputSpec:
    """Canonical input views and fields a feature is allowed to read."""

    input_views: Sequence[str]
    fields: Sequence[str]
    dataset_version_ids: Sequence[str] = ()
    input_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        input_views = _require_text_tuple(self.input_views, "FeatureInputSpec.input_views")
        fields = _require_text_tuple(self.fields, "FeatureInputSpec.fields")
        dataset_version_ids = _require_text_tuple(
            self.dataset_version_ids,
            "FeatureInputSpec.dataset_version_ids",
            allow_empty=True,
        )
        unknown_views = tuple(
            input_view for input_view in input_views if input_view not in CANONICAL_INPUT_VIEW_NAMES
        )
        if unknown_views:
            raise FeatureContractError(
                "FeatureInputSpec.input_views must name canonical feature input views; "
                f"got {', '.join(unknown_views)}"
            )
        if _duplicates(input_views):
            raise FeatureContractError("FeatureInputSpec.input_views must not contain duplicates")
        if _duplicates(fields):
            raise FeatureContractError("FeatureInputSpec.fields must not contain duplicates")
        object.__setattr__(self, "input_views", input_views)
        object.__setattr__(self, "fields", fields)
        object.__setattr__(self, "dataset_version_ids", dataset_version_ids)
        object.__setattr__(
            self,
            "input_metadata",
            _freeze_json_mapping(self.input_metadata, "FeatureInputSpec.input_metadata"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "input_views": list(self.input_views),
            "fields": list(self.fields),
            "dataset_version_ids": list(self.dataset_version_ids),
            "input_metadata": self.input_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class TransformSpec:
    """Declarative transform identity and JSON-compatible parameters."""

    transform_id: str
    parameters: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "transform_id",
            _require_text(self.transform_id, "TransformSpec.transform_id"),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "TransformSpec.parameters"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "transform_id": self.transform_id,
            "parameters": self.parameters.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class WindowSpec:
    """Declarative feature window, including live/offline causality."""

    kind: WindowKind | str
    length: int
    causality: WindowCausality | str
    offline_only: bool
    anchor: str = "available_ts"
    parameters: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = _coerce_str_enum(self.kind, WindowKind, "WindowSpec.kind")
        causality = _coerce_str_enum(
            self.causality,
            WindowCausality,
            "WindowSpec.causality",
        )
        length = _require_positive_int(self.length, "WindowSpec.length")
        offline_only = _require_bool(self.offline_only, "WindowSpec.offline_only")
        anchor = _require_text(self.anchor, "WindowSpec.anchor")
        if kind is WindowKind.CENTERED and causality is not WindowCausality.CENTERED:
            raise FeatureContractError("WindowSpec.kind=centered requires causality=centered")
        if kind is WindowKind.FUTURE and causality is not WindowCausality.FUTURE:
            raise FeatureContractError("WindowSpec.kind=future requires causality=future")
        if causality in {WindowCausality.CENTERED, WindowCausality.FUTURE} and not offline_only:
            raise FeatureContractError(
                "centered and future windows must be explicitly flagged offline_only"
            )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "causality", causality)
        object.__setattr__(self, "offline_only", offline_only)
        object.__setattr__(self, "anchor", anchor)
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "WindowSpec.parameters"),
        )

    @property
    def is_live_compatible(self) -> bool:
        """Return whether this window can be used in a live feature contract."""

        return self.causality is WindowCausality.CAUSAL and not self.offline_only

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind.value,
            "length": self.length,
            "causality": self.causality.value,
            "offline_only": self.offline_only,
            "anchor": self.anchor,
            "parameters": self.parameters.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class NormalizationSpec:
    """Declarative normalization identity, parameters, and fit partition policy."""

    normalization_id: str
    parameters: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)
    fit_partition_policy: FitPartitionPolicy | str = FitPartitionPolicy.DEVELOPMENT_VALIDATION
    contamination_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        policy = _coerce_str_enum(
            self.fit_partition_policy,
            FitPartitionPolicy,
            "NormalizationSpec.fit_partition_policy",
        )
        contamination_metadata = _freeze_json_mapping(
            self.contamination_metadata,
            "NormalizationSpec.contamination_metadata",
        )
        if policy is FitPartitionPolicy.LOCKED_TEST and not contamination_metadata:
            raise FeatureContractError(
                "NormalizationSpec locked_test fit policy requires governance "
                "contamination metadata"
            )
        object.__setattr__(
            self,
            "normalization_id",
            _require_text(self.normalization_id, "NormalizationSpec.normalization_id"),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "NormalizationSpec.parameters"),
        )
        object.__setattr__(self, "fit_partition_policy", policy)
        object.__setattr__(self, "contamination_metadata", contamination_metadata)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "normalization_id": self.normalization_id,
            "parameters": self.parameters.to_dict(),
            "fit_partition_policy": self.fit_partition_policy.value,
            "contamination_metadata": self.contamination_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Central immutable feature contract bound to a governed FeatureRequest."""

    feature_id: str
    family: FeatureFamily | str
    feature_request_id: str
    inputs: FeatureInputSpec
    transform: TransformSpec
    window: WindowSpec
    normalization: NormalizationSpec
    availability_assumptions: Mapping[str, Any] | FrozenJsonMapping
    available_ts_derivation_rule: str
    live: bool = True
    implementation_eligible: bool = False
    contract_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)
    request_gate_decision: InitVar[FeatureRequestGateDecision | None] = None

    def __post_init__(self, request_gate_decision: FeatureRequestGateDecision | None) -> None:
        object.__setattr__(
            self,
            "feature_id",
            _require_text(self.feature_id, "FeatureSpec.feature_id"),
        )
        object.__setattr__(
            self,
            "family",
            _coerce_str_enum(self.family, FeatureFamily, "FeatureSpec.family"),
        )
        object.__setattr__(
            self,
            "feature_request_id",
            _require_feature_request_id(self.feature_request_id),
        )
        if not isinstance(self.inputs, FeatureInputSpec):
            raise FeatureContractError("FeatureSpec.inputs must be a FeatureInputSpec")
        if not isinstance(self.transform, TransformSpec):
            raise FeatureContractError("FeatureSpec.transform must be a TransformSpec")
        if not isinstance(self.window, WindowSpec):
            raise FeatureContractError("FeatureSpec.window must be a WindowSpec")
        if not isinstance(self.normalization, NormalizationSpec):
            raise FeatureContractError("FeatureSpec.normalization must be a NormalizationSpec")
        live = _require_bool(self.live, "FeatureSpec.live")
        implementation_eligible = _require_bool(
            self.implementation_eligible,
            "FeatureSpec.implementation_eligible",
        )
        available_ts_rule = _require_text(
            self.available_ts_derivation_rule,
            "FeatureSpec.available_ts_derivation_rule",
        )
        availability_assumptions = _freeze_json_mapping(
            self.availability_assumptions,
            "FeatureSpec.availability_assumptions",
        )
        if not availability_assumptions:
            raise FeatureContractError("FeatureSpec.availability_assumptions must be non-empty")
        if live and not self.window.is_live_compatible:
            raise FeatureContractError(
                "live FeatureSpec contracts cannot use centered, future, or offline-only windows"
            )
        if implementation_eligible:
            _require_approved_gate_decision(request_gate_decision, self.feature_request_id)
        object.__setattr__(self, "live", live)
        object.__setattr__(self, "implementation_eligible", implementation_eligible)
        object.__setattr__(self, "available_ts_derivation_rule", available_ts_rule)
        object.__setattr__(self, "availability_assumptions", availability_assumptions)
        object.__setattr__(
            self,
            "contract_metadata",
            _freeze_json_mapping(self.contract_metadata, "FeatureSpec.contract_metadata"),
        )

    def to_contract_dict(self) -> dict[str, JsonValue]:
        """Return the canonical versioned contract payload."""

        return {
            "feature_id": self.feature_id,
            "family": self.family.value,
            "feature_request_id": self.feature_request_id,
            "inputs": self.inputs.to_dict(),
            "transform": self.transform.to_dict(),
            "window": self.window.to_dict(),
            "normalization": self.normalization.to_dict(),
            "availability_assumptions": self.availability_assumptions.to_dict(),
            "available_ts_derivation_rule": self.available_ts_derivation_rule,
            "live": self.live,
            "implementation_eligible": self.implementation_eligible,
            "contract_metadata": self.contract_metadata.to_dict(),
        }

    def derive_feature_version(self) -> FeatureVersion:
        """Derive the deterministic content-addressed version for this contract."""

        return FeatureVersion.derive(self)


@dataclass(frozen=True, slots=True)
class FeatureVersion:
    """Deterministic content-addressed identity for one full feature contract."""

    feature_version_id: str
    content_hash: str
    algorithm: str = FEATURE_VERSION_ALGORITHM

    def __post_init__(self) -> None:
        content_hash_value = _require_hex_hash(self.content_hash, "FeatureVersion.content_hash")
        algorithm = _require_text(self.algorithm, "FeatureVersion.algorithm")
        if algorithm != FEATURE_VERSION_ALGORITHM:
            raise FeatureContractError(f"unsupported FeatureVersion algorithm: {algorithm}")
        feature_version_id = _require_text(
            self.feature_version_id,
            "FeatureVersion.feature_version_id",
        )
        expected = f"fver_{content_hash_value}"
        pattern_matches = FEATURE_VERSION_PATTERN.fullmatch(feature_version_id) is not None
        if feature_version_id != expected or not pattern_matches:
            raise FeatureContractError(
                "FeatureVersion.feature_version_id must be fver_<64-hex-content-hash>"
            )
        object.__setattr__(self, "content_hash", content_hash_value)
        object.__setattr__(self, "algorithm", algorithm)
        object.__setattr__(self, "feature_version_id", feature_version_id)

    @classmethod
    def derive(cls, spec: FeatureSpec) -> FeatureVersion:
        """Derive a stable FeatureVersion from a FeatureSpec."""

        if not isinstance(spec, FeatureSpec):
            raise FeatureContractError("FeatureVersion.derive requires a FeatureSpec")
        payload: dict[str, JsonValue] = {
            "algorithm": FEATURE_VERSION_ALGORITHM,
            "feature_contract": spec.to_contract_dict(),
        }
        digest = content_hash(payload)
        return cls(feature_version_id=f"fver_{digest}", content_hash=digest)

    def to_dict(self) -> dict[str, str]:
        return {
            "feature_version_id": self.feature_version_id,
            "content_hash": self.content_hash,
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True, slots=True)
class FeatureSetSpec:
    """Namespaced, versioned bundle of feature contracts."""

    feature_set_id: str
    feature_set_version: str
    features: Sequence[FeatureSpec]
    namespace: str = FEATURE_SET_NAMESPACE
    description: str = ""
    metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        namespace = _require_text(self.namespace, "FeatureSetSpec.namespace")
        if namespace != FEATURE_SET_NAMESPACE:
            raise FeatureContractError("FeatureSetSpec.namespace must be 'features'")
        features = tuple(self.features)
        if not features:
            raise FeatureContractError(
                "FeatureSetSpec.features must contain at least one FeatureSpec"
            )
        for feature in features:
            if not isinstance(feature, FeatureSpec):
                raise FeatureContractError(
                    "FeatureSetSpec.features must contain FeatureSpec objects"
                )
        duplicate_ids = _duplicates(feature.feature_id for feature in features)
        if duplicate_ids:
            raise FeatureContractError(
                f"FeatureSetSpec.features duplicate feature_id values: {', '.join(duplicate_ids)}"
            )
        object.__setattr__(
            self,
            "feature_set_id",
            _require_text(self.feature_set_id, "FeatureSetSpec.feature_set_id"),
        )
        object.__setattr__(
            self,
            "feature_set_version",
            _require_text(self.feature_set_version, "FeatureSetSpec.feature_set_version"),
        )
        object.__setattr__(self, "features", features)
        object.__setattr__(self, "namespace", namespace)
        object.__setattr__(self, "description", _optional_text(self.description))
        object.__setattr__(
            self,
            "metadata",
            _freeze_json_mapping(self.metadata, "FeatureSetSpec.metadata"),
        )

    @property
    def feature_versions(self) -> tuple[FeatureVersion, ...]:
        """Return deterministic versions for all bundled FeatureSpecs."""

        return tuple(feature.derive_feature_version() for feature in self.features)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "namespace": self.namespace,
            "feature_set_id": self.feature_set_id,
            "feature_set_version": self.feature_set_version,
            "features": [feature.to_contract_dict() for feature in self.features],
            "feature_versions": [version.to_dict() for version in self.feature_versions],
            "description": self.description,
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FeatureValueRecord:
    """Feature value contract requiring an explicit availability timestamp."""

    feature_version_id: str
    entity_id: str
    event_ts: datetime
    available_ts: datetime
    value: Any
    quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_version_id",
            _require_feature_version_id(self.feature_version_id),
        )
        object.__setattr__(
            self,
            "entity_id",
            _require_text(self.entity_id, "FeatureValueRecord.entity_id"),
        )
        object.__setattr__(
            self,
            "event_ts",
            _require_aware_datetime(self.event_ts, "FeatureValueRecord.event_ts"),
        )
        object.__setattr__(
            self,
            "available_ts",
            _require_aware_datetime(self.available_ts, "FeatureValueRecord.available_ts"),
        )
        object.__setattr__(
            self,
            "value",
            _freeze_json_value(self.value, "FeatureValueRecord.value"),
        )
        object.__setattr__(
            self,
            "quality_flags",
            _require_text_tuple(
                self.quality_flags,
                "FeatureValueRecord.quality_flags",
                allow_empty=True,
            ),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "feature_version_id": self.feature_version_id,
            "entity_id": self.entity_id,
            "event_ts": self.event_ts.isoformat(),
            "available_ts": self.available_ts.isoformat(),
            "value": _thaw_json_value(self.value),
            "quality_flags": list(self.quality_flags),
        }


@dataclass(frozen=True, slots=True)
class FeatureLineageRecord:
    """Lineage link from a FeatureVersion to its contract and request provenance."""

    feature_version: FeatureVersion
    feature_spec: FeatureSpec
    feature_request_id: str
    contract_provenance: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.feature_version, FeatureVersion):
            raise FeatureContractError(
                "FeatureLineageRecord.feature_version must be a FeatureVersion"
            )
        if not isinstance(self.feature_spec, FeatureSpec):
            raise FeatureContractError("FeatureLineageRecord.feature_spec must be a FeatureSpec")
        feature_request_id = _require_feature_request_id(self.feature_request_id)
        if feature_request_id != self.feature_spec.feature_request_id:
            raise FeatureContractError(
                "FeatureLineageRecord.feature_request_id must match FeatureSpec.feature_request_id"
            )
        expected_version = FeatureVersion.derive(self.feature_spec)
        if self.feature_version != expected_version:
            raise FeatureContractError(
                "FeatureLineageRecord.feature_version must match FeatureSpec contract content"
            )
        object.__setattr__(self, "feature_request_id", feature_request_id)
        object.__setattr__(
            self,
            "contract_provenance",
            _freeze_json_mapping(
                self.contract_provenance,
                "FeatureLineageRecord.contract_provenance",
            ),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "feature_version": self.feature_version.to_dict(),
            "feature_spec": self.feature_spec.to_contract_dict(),
            "feature_request_id": self.feature_request_id,
            "contract_provenance": self.contract_provenance.to_dict(),
        }


def _freeze_json_mapping(
    value: Mapping[str, Any] | FrozenJsonMapping,
    field_name: str,
) -> FrozenJsonMapping:
    if isinstance(value, FrozenJsonMapping):
        return value
    return FrozenJsonMapping.from_mapping(value, field_name=field_name)


def _freeze_json_value(value: Any, field_name: str) -> object:
    if isinstance(value, FrozenJsonMapping):
        return value
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FeatureContractError(f"{field_name} must be a finite JSON number")
        return value
    if isinstance(value, Mapping):
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return tuple(
            _freeze_json_value(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        )
    raise FeatureContractError(f"{field_name} must be JSON-compatible")


def _thaw_json_value(value: object) -> JsonValue:
    if isinstance(value, FrozenJsonMapping):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise FeatureContractError(f"unsupported frozen JSON value type: {type(value).__name__}")


def _canonical_json(value: JsonValue, field_name: str) -> str:
    try:
        return canonical_serialize(value)
    except ValueError as exc:
        raise FeatureContractError(f"{field_name} must be canonically serializable") from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise FeatureContractError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise FeatureContractError(f"{field_name} must be non-empty")
    return normalized


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise FeatureContractError("optional text must be a string")
    return value.strip()


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise FeatureContractError(f"{field_name} must be a sequence of strings")
    normalized = tuple(_require_text(item, f"{field_name}[]") for item in value)
    if not allow_empty and not normalized:
        raise FeatureContractError(f"{field_name} must contain at least one item")
    return normalized


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise FeatureContractError(f"{field_name} must be a positive integer")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise FeatureContractError(f"{field_name} must be a bool")
    return value


def _coerce_str_enum(value: object, enum_type: type[StrEnum], field_name: str) -> StrEnum:
    try:
        if isinstance(value, enum_type):
            return value
        return enum_type(_require_text(value, field_name))
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise FeatureContractError(f"{field_name} must be one of: {allowed}") from exc


def _require_feature_request_id(value: object) -> str:
    feature_request_id = _require_text(value, "feature_request_id")
    try:
        return validate_governance_id(
            feature_request_id,
            expected_kind=GovernanceIdKind.FEATURE_REQUEST,
        )
    except GovernanceIdError as exc:
        raise FeatureContractError(
            "FeatureSpec.feature_request_id must be a governed FeatureRequest freq_ id"
        ) from exc


def _require_approved_gate_decision(
    decision: FeatureRequestGateDecision | None,
    feature_request_id: str,
) -> None:
    if not isinstance(decision, FeatureRequestGateDecision):
        raise FeatureContractError(
            "implementation_eligible FeatureSpec requires an FLF-P05 "
            "FeatureRequestGateDecision"
        )
    if not decision.implementation_allowed:
        raise FeatureContractError("FeatureRequest gate did not admit implementation")
    if decision.feature_request_id != feature_request_id:
        raise FeatureContractError(
            "FeatureRequest gate decision must match FeatureSpec.feature_request_id"
        )


def _require_hex_hash(value: object, field_name: str) -> str:
    text = _require_text(value, field_name)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise FeatureContractError(f"{field_name} must be a 64-character lowercase hex hash")
    return text


def _require_feature_version_id(value: object) -> str:
    text = _require_text(value, "FeatureValueRecord.feature_version_id")
    if FEATURE_VERSION_PATTERN.fullmatch(text) is None:
        raise FeatureContractError("feature_version_id must be fver_<64-hex-content-hash>")
    return text


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FeatureContractError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise FeatureContractError(f"{field_name} must be timezone-aware")
    return value


def _duplicates(values: Sequence[str] | Any) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(duplicates)


__all__ = [
    "CANONICAL_INPUT_VIEW_NAMES",
    "FEATURE_SET_NAMESPACE",
    "FEATURE_VERSION_ALGORITHM",
    "FeatureContractError",
    "FeatureFamily",
    "FeatureInputSpec",
    "FeatureLineageRecord",
    "FeatureSetSpec",
    "FeatureSpec",
    "FeatureValueRecord",
    "FeatureVersion",
    "FitPartitionPolicy",
    "FrozenJsonMapping",
    "NormalizationSpec",
    "TransformSpec",
    "WindowCausality",
    "WindowKind",
    "WindowSpec",
]
