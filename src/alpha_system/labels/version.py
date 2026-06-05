"""Immutable label-layer contract objects.

This module defines label contract metadata only. It does not calculate labels,
materialize values, persist registries, read raw provider files, call external
providers, or expose labels as live features.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from alpha_system.features.contracts import (
    CANONICAL_INPUT_VIEW_NAMES,
    WindowCausality,
    WindowSpec,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    validate_governance_id,
)
from alpha_system.governance.label_leakage_guard import (
    FeatureReferences,
    LabelLeakageResult,
    check_label_leakage,
)
from alpha_system.governance.label_spec import (
    REQUIRED_LEAKAGE_CHECKS,
    validate_label_spec,
)
from alpha_system.governance.label_spec import (
    LabelSpec as GovernanceLabelSpec,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    content_hash,
)

LABEL_VERSION_ALGORITHM = "label_version_sha256_v1"
LABEL_VERSION_PATTERN = re.compile(r"^lver_[a-f0-9]{64}$")
LABEL_CONTRACT_NAMESPACE = "labels"


class LabelContractError(ValueError):
    """Raised when a label contract fails closed."""


class LabelFamily(StrEnum):
    """Label families planned by the Feature/Label foundation campaign."""

    FIXED_HORIZON = "fixed_horizon"
    MIDPRICE_FORWARD = "midprice_forward"
    COST_ADJUSTED = "cost_adjusted"
    PATH = "path"
    EVENT = "event"


class LabelAvailabilityConsumer(StrEnum):
    """Consumer boundary for forward-looking label data."""

    LABELS_ONLY = "labels_only"


@dataclass(frozen=True, slots=True)
class FrozenJsonMapping:
    """Hashable, deterministic representation of JSON-compatible metadata."""

    items: tuple[tuple[str, object], ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, field_name: str) -> FrozenJsonMapping:
        if isinstance(value, FrozenJsonMapping):
            return value
        if not isinstance(value, Mapping):
            raise LabelContractError(f"{field_name} must be a mapping")
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise LabelContractError(f"{field_name} keys must be non-empty strings")
            items.append((key, _freeze_json_value(item, f"{field_name}.{key}")))
        frozen = cls(tuple(sorted(items, key=lambda pair: pair[0])))
        _canonical_json(frozen.to_dict(), field_name)
        return frozen

    def __bool__(self) -> bool:
        return bool(self.items)

    def to_dict(self) -> dict[str, JsonValue]:
        return {key: _thaw_json_value(value) for key, value in self.items}


@dataclass(frozen=True, slots=True)
class LabelInputSpec:
    """Canonical input views and fields a label family may read."""

    input_views: Sequence[str]
    fields: Sequence[str]
    dataset_version_ids: Sequence[str] = ()
    input_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        input_views = _require_text_tuple(self.input_views, "LabelInputSpec.input_views")
        fields = _require_text_tuple(self.fields, "LabelInputSpec.fields")
        dataset_version_ids = _require_text_tuple(
            self.dataset_version_ids,
            "LabelInputSpec.dataset_version_ids",
            allow_empty=True,
        )
        unknown_views = tuple(
            input_view for input_view in input_views if input_view not in CANONICAL_INPUT_VIEW_NAMES
        )
        if unknown_views:
            raise LabelContractError(
                "LabelInputSpec.input_views must name canonical feature input views; "
                f"got {', '.join(unknown_views)}"
            )
        if _duplicates(input_views):
            raise LabelContractError("LabelInputSpec.input_views must not contain duplicates")
        if _duplicates(fields):
            raise LabelContractError("LabelInputSpec.fields must not contain duplicates")
        object.__setattr__(self, "input_views", input_views)
        object.__setattr__(self, "fields", fields)
        object.__setattr__(self, "dataset_version_ids", dataset_version_ids)
        object.__setattr__(
            self,
            "input_metadata",
            _freeze_json_mapping(self.input_metadata, "LabelInputSpec.input_metadata"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "input_views": list(self.input_views),
            "fields": list(self.fields),
            "dataset_version_ids": list(self.dataset_version_ids),
            "input_metadata": self.input_metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class LabelHorizonSpec:
    """Label horizon metadata consumed from governance `LabelSpec.horizon`."""

    horizon: str
    horizon_end_rule: str
    parameters: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "horizon",
            _require_text(self.horizon, "LabelHorizonSpec.horizon"),
        )
        object.__setattr__(
            self,
            "horizon_end_rule",
            _require_text(self.horizon_end_rule, "LabelHorizonSpec.horizon_end_rule"),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "LabelHorizonSpec.parameters"),
        )

    @classmethod
    def from_label_spec(
        cls,
        label_spec: GovernanceLabelSpec | Mapping[str, Any],
    ) -> LabelHorizonSpec:
        spec = _coerce_governance_label_spec(label_spec)
        return cls(
            horizon=spec.horizon,
            horizon_end_rule="label.horizon_end_ts is derived from LabelSpec.horizon",
            parameters={"governance_horizon": spec.horizon},
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "horizon": self.horizon,
            "horizon_end_rule": self.horizon_end_rule,
            "parameters": self.parameters.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class LabelPathSpec:
    """Forward path metadata consumed from governance `LabelSpec.path_rules`."""

    path_rules: Mapping[str, Any] | FrozenJsonMapping
    uses_forward_data: bool
    window: WindowSpec | None = None
    parameters: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        path_rules = _freeze_json_mapping(self.path_rules, "LabelPathSpec.path_rules")
        if not path_rules:
            raise LabelContractError("LabelPathSpec.path_rules must be non-empty")
        uses_forward_data = _require_bool(
            self.uses_forward_data,
            "LabelPathSpec.uses_forward_data",
        )
        if self.window is not None and not isinstance(self.window, WindowSpec):
            raise LabelContractError("LabelPathSpec.window must be an FLF-P06 WindowSpec")
        if self.window is not None and self.window.causality is WindowCausality.FUTURE:
            if not uses_forward_data:
                raise LabelContractError(
                    "LabelPathSpec future windows require uses_forward_data=True"
                )
            if not self.window.offline_only:
                raise LabelContractError("LabelPathSpec future windows must be offline_only")
        object.__setattr__(self, "path_rules", path_rules)
        object.__setattr__(self, "uses_forward_data", uses_forward_data)
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "LabelPathSpec.parameters"),
        )

    @classmethod
    def from_label_spec(
        cls,
        label_spec: GovernanceLabelSpec | Mapping[str, Any],
        *,
        window: WindowSpec | None = None,
    ) -> LabelPathSpec:
        spec = _coerce_governance_label_spec(label_spec)
        return cls(path_rules=spec.path_rules, uses_forward_data=True, window=window)

    def to_dict(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "path_rules": self.path_rules.to_dict(),
            "uses_forward_data": self.uses_forward_data,
            "parameters": self.parameters.to_dict(),
        }
        if self.window is not None:
            payload["window"] = self.window.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class BarrierSpec:
    """Target and stop metadata consumed from governance `LabelSpec.target_stop_rules`."""

    target_stop_rules: Mapping[str, Any] | FrozenJsonMapping

    def __post_init__(self) -> None:
        rules = _freeze_json_mapping(self.target_stop_rules, "BarrierSpec.target_stop_rules")
        if not rules:
            raise LabelContractError("BarrierSpec.target_stop_rules must be non-empty")
        object.__setattr__(self, "target_stop_rules", rules)

    @classmethod
    def from_label_spec(cls, label_spec: GovernanceLabelSpec | Mapping[str, Any]) -> BarrierSpec:
        spec = _coerce_governance_label_spec(label_spec)
        return cls(target_stop_rules=spec.target_stop_rules)

    def to_dict(self) -> dict[str, JsonValue]:
        return {"target_stop_rules": self.target_stop_rules.to_dict()}


@dataclass(frozen=True, slots=True)
class CostAdjustmentSpec:
    """Cost metadata consumed from governance `LabelSpec.cost_model`."""

    cost_model: Mapping[str, Any] | FrozenJsonMapping

    def __post_init__(self) -> None:
        cost_model = _freeze_json_mapping(self.cost_model, "CostAdjustmentSpec.cost_model")
        if not cost_model:
            raise LabelContractError("CostAdjustmentSpec.cost_model must be non-empty")
        object.__setattr__(self, "cost_model", cost_model)

    @classmethod
    def from_label_spec(
        cls,
        label_spec: GovernanceLabelSpec | Mapping[str, Any],
    ) -> CostAdjustmentSpec:
        spec = _coerce_governance_label_spec(label_spec)
        return cls(cost_model=spec.cost_model)

    def to_dict(self) -> dict[str, JsonValue]:
        return {"cost_model": self.cost_model.to_dict()}


@dataclass(frozen=True, slots=True)
class LabelAvailabilityPolicy:
    """Availability and feature-exclusion policy for label-only future data."""

    availability_time: datetime | str
    label_available_ts_derivation_rule: str
    forbidden_feature_overlap: Mapping[str, Any] | FrozenJsonMapping
    leakage_checks: Sequence[str]
    forward_data_allowed: bool = True
    legal_consumer: LabelAvailabilityConsumer | str = LabelAvailabilityConsumer.LABELS_ONLY

    def __post_init__(self) -> None:
        availability_time = _require_aware_datetime_or_iso(
            self.availability_time,
            "LabelAvailabilityPolicy.availability_time",
        )
        rule = _require_text(
            self.label_available_ts_derivation_rule,
            "LabelAvailabilityPolicy.label_available_ts_derivation_rule",
        )
        forbidden = _freeze_json_mapping(
            self.forbidden_feature_overlap,
            "LabelAvailabilityPolicy.forbidden_feature_overlap",
        )
        if not forbidden:
            raise LabelContractError(
                "LabelAvailabilityPolicy.forbidden_feature_overlap must be non-empty"
            )
        leakage_checks = _require_leakage_checks(self.leakage_checks)
        forward_data_allowed = _require_bool(
            self.forward_data_allowed,
            "LabelAvailabilityPolicy.forward_data_allowed",
        )
        legal_consumer = _coerce_str_enum(
            self.legal_consumer,
            LabelAvailabilityConsumer,
            "LabelAvailabilityPolicy.legal_consumer",
        )
        if forward_data_allowed and legal_consumer is not LabelAvailabilityConsumer.LABELS_ONLY:
            raise LabelContractError("forward-looking data is legal only for labels")
        object.__setattr__(self, "availability_time", availability_time)
        object.__setattr__(self, "label_available_ts_derivation_rule", rule)
        object.__setattr__(self, "forbidden_feature_overlap", forbidden)
        object.__setattr__(self, "leakage_checks", leakage_checks)
        object.__setattr__(self, "forward_data_allowed", forward_data_allowed)
        object.__setattr__(self, "legal_consumer", legal_consumer)

    @classmethod
    def from_label_spec(
        cls,
        label_spec: GovernanceLabelSpec | Mapping[str, Any],
    ) -> LabelAvailabilityPolicy:
        spec = _coerce_governance_label_spec(label_spec)
        return cls(
            availability_time=spec.availability_time,
            label_available_ts_derivation_rule=(
                "label.label_available_ts = max(horizon_end_ts, path_rules terminal "
                "availability, LabelSpec.availability_time)"
            ),
            forbidden_feature_overlap=spec.forbidden_feature_overlap,
            leakage_checks=spec.leakage_checks,
            forward_data_allowed=True,
            legal_consumer=LabelAvailabilityConsumer.LABELS_ONLY,
        )

    @property
    def future_data_legal_only_for_labels(self) -> bool:
        """Return true when forward-looking data is confined to labels."""

        return (
            self.forward_data_allowed
            and self.legal_consumer is LabelAvailabilityConsumer.LABELS_ONLY
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "availability_time": self.availability_time.isoformat(),
            "label_available_ts_derivation_rule": self.label_available_ts_derivation_rule,
            "forbidden_feature_overlap": self.forbidden_feature_overlap.to_dict(),
            "leakage_checks": list(self.leakage_checks),
            "forward_data_allowed": self.forward_data_allowed,
            "legal_consumer": self.legal_consumer.value,
        }


@dataclass(frozen=True, slots=True)
class LabelContractSpec:
    """Central immutable label contract bound to a governed `lspec_` LabelSpec."""

    label_id: str
    family: LabelFamily | str
    governance_label_spec: InitVar[GovernanceLabelSpec | Mapping[str, Any] | None]
    inputs: LabelInputSpec
    horizon: LabelHorizonSpec
    path: LabelPathSpec
    barriers: BarrierSpec
    cost_adjustment: CostAdjustmentSpec
    availability_policy: LabelAvailabilityPolicy
    contract_metadata: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)
    label_spec_id: str = field(init=False)
    governance_label_spec_snapshot: FrozenJsonMapping = field(init=False)
    namespace: str = field(default=LABEL_CONTRACT_NAMESPACE, init=False)

    def __post_init__(
        self,
        governance_label_spec: GovernanceLabelSpec | Mapping[str, Any] | None,
    ) -> None:
        spec = _coerce_governance_label_spec(governance_label_spec)
        object.__setattr__(self, "label_id", _require_text(self.label_id, "label_id"))
        object.__setattr__(
            self,
            "family",
            _coerce_str_enum(self.family, LabelFamily, "LabelContractSpec.family"),
        )
        _require_component(self.inputs, LabelInputSpec, "LabelContractSpec.inputs")
        _require_component(self.horizon, LabelHorizonSpec, "LabelContractSpec.horizon")
        _require_component(self.path, LabelPathSpec, "LabelContractSpec.path")
        _require_component(self.barriers, BarrierSpec, "LabelContractSpec.barriers")
        _require_component(
            self.cost_adjustment,
            CostAdjustmentSpec,
            "LabelContractSpec.cost_adjustment",
        )
        _require_component(
            self.availability_policy,
            LabelAvailabilityPolicy,
            "LabelContractSpec.availability_policy",
        )
        _validate_components_match_governance(
            spec,
            self.horizon,
            self.path,
            self.barriers,
            self.cost_adjustment,
            self.availability_policy,
        )
        object.__setattr__(self, "label_spec_id", spec.label_spec_id)
        object.__setattr__(
            self,
            "governance_label_spec_snapshot",
            FrozenJsonMapping.from_mapping(
                spec.to_dict(),
                field_name="LabelContractSpec.governance_label_spec_snapshot",
            ),
        )
        object.__setattr__(
            self,
            "contract_metadata",
            _freeze_json_mapping(
                self.contract_metadata,
                "LabelContractSpec.contract_metadata",
            ),
        )

    @classmethod
    def from_label_spec(
        cls,
        *,
        label_id: str,
        family: LabelFamily | str,
        governance_label_spec: GovernanceLabelSpec | Mapping[str, Any],
        inputs: LabelInputSpec,
        window: WindowSpec | None = None,
        contract_metadata: Mapping[str, Any] | FrozenJsonMapping | None = None,
    ) -> LabelContractSpec:
        """Build a label contract by adapting the governed `LabelSpec` fields."""

        spec = _coerce_governance_label_spec(governance_label_spec)
        return cls(
            label_id=label_id,
            family=family,
            governance_label_spec=spec,
            inputs=inputs,
            horizon=LabelHorizonSpec.from_label_spec(spec),
            path=LabelPathSpec.from_label_spec(spec, window=window),
            barriers=BarrierSpec.from_label_spec(spec),
            cost_adjustment=CostAdjustmentSpec.from_label_spec(spec),
            availability_policy=LabelAvailabilityPolicy.from_label_spec(spec),
            contract_metadata=contract_metadata or {},
        )

    def to_contract_dict(self) -> dict[str, JsonValue]:
        """Return the canonical versioned contract payload."""

        return {
            "namespace": self.namespace,
            "label_id": self.label_id,
            "family": self.family.value,
            "label_spec_id": self.label_spec_id,
            "governance_label_spec": self.governance_label_spec_snapshot.to_dict(),
            "inputs": self.inputs.to_dict(),
            "horizon": self.horizon.to_dict(),
            "path": self.path.to_dict(),
            "barriers": self.barriers.to_dict(),
            "cost_adjustment": self.cost_adjustment.to_dict(),
            "availability_policy": self.availability_policy.to_dict(),
            "contract_metadata": self.contract_metadata.to_dict(),
        }

    def derive_label_version(self) -> LabelVersion:
        """Derive the deterministic content-addressed version for this contract."""

        return LabelVersion.derive(self)

    def validate_live_feature_references(
        self,
        feature_references: FeatureReferences,
    ) -> LabelLeakageResult:
        """Reject label-as-feature or lookahead feature references via governance guard."""

        result = check_label_leakage(
            self.governance_label_spec_snapshot.to_dict(),
            feature_references,
        )
        if result.is_blocked:
            raise LabelContractError(
                "LabelContractSpec cannot be exposed as a live feature input"
            )
        return result


@dataclass(frozen=True, slots=True)
class LabelVersion:
    """Deterministic content-addressed identity for one full label contract."""

    label_version_id: str
    content_hash: str
    algorithm: str = LABEL_VERSION_ALGORITHM

    def __post_init__(self) -> None:
        content_hash_value = _require_hex_hash(self.content_hash, "LabelVersion.content_hash")
        algorithm = _require_text(self.algorithm, "LabelVersion.algorithm")
        if algorithm != LABEL_VERSION_ALGORITHM:
            raise LabelContractError(f"unsupported LabelVersion algorithm: {algorithm}")
        label_version_id = _require_text(self.label_version_id, "LabelVersion.label_version_id")
        expected = f"lver_{content_hash_value}"
        pattern_matches = LABEL_VERSION_PATTERN.fullmatch(label_version_id) is not None
        if label_version_id != expected or not pattern_matches:
            raise LabelContractError(
                "LabelVersion.label_version_id must be lver_<64-hex-content-hash>"
            )
        object.__setattr__(self, "content_hash", content_hash_value)
        object.__setattr__(self, "algorithm", algorithm)
        object.__setattr__(self, "label_version_id", label_version_id)

    @classmethod
    def derive(cls, spec: LabelContractSpec) -> LabelVersion:
        """Derive a stable LabelVersion from a LabelContractSpec."""

        if not isinstance(spec, LabelContractSpec):
            raise LabelContractError("LabelVersion.derive requires a LabelContractSpec")
        payload: dict[str, JsonValue] = {
            "algorithm": LABEL_VERSION_ALGORITHM,
            "label_contract": spec.to_contract_dict(),
        }
        digest = content_hash(payload)
        return cls(label_version_id=f"lver_{digest}", content_hash=digest)

    def to_dict(self) -> dict[str, str]:
        return {
            "label_version_id": self.label_version_id,
            "content_hash": self.content_hash,
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True, slots=True)
class LabelValueRecord:
    """Label value contract requiring an explicit label availability timestamp."""

    label_version_id: str
    entity_id: str
    event_ts: datetime
    horizon_end_ts: datetime
    label_available_ts: datetime
    value: Any
    label_contract: InitVar[LabelContractSpec]
    quality_flags: Sequence[str] = ()
    label_spec_id: str = field(init=False)

    def __post_init__(self, label_contract: LabelContractSpec) -> None:
        if not isinstance(label_contract, LabelContractSpec):
            raise LabelContractError("LabelValueRecord requires a bound LabelContractSpec")
        expected_version = LabelVersion.derive(label_contract)
        label_version_id = _require_label_version_id(self.label_version_id)
        if label_version_id != expected_version.label_version_id:
            raise LabelContractError(
                "LabelValueRecord.label_version_id must match LabelContractSpec content"
            )
        event_ts = _require_aware_datetime(self.event_ts, "LabelValueRecord.event_ts")
        horizon_end_ts = _require_aware_datetime(
            self.horizon_end_ts,
            "LabelValueRecord.horizon_end_ts",
        )
        label_available_ts = _require_aware_datetime(
            self.label_available_ts,
            "LabelValueRecord.label_available_ts",
        )
        if horizon_end_ts < event_ts:
            raise LabelContractError("LabelValueRecord.horizon_end_ts must be at or after event_ts")
        if label_available_ts < event_ts:
            raise LabelContractError("LabelValueRecord.label_available_ts must be after event_ts")
        if label_available_ts < horizon_end_ts:
            raise LabelContractError(
                "LabelValueRecord.label_available_ts must be at or after horizon_end_ts"
            )
        if label_available_ts < label_contract.availability_policy.availability_time:
            raise LabelContractError(
                "LabelValueRecord.label_available_ts must not precede LabelSpec.availability_time"
            )
        object.__setattr__(self, "label_version_id", label_version_id)
        object.__setattr__(
            self,
            "entity_id",
            _require_text(self.entity_id, "LabelValueRecord.entity_id"),
        )
        object.__setattr__(self, "event_ts", event_ts)
        object.__setattr__(self, "horizon_end_ts", horizon_end_ts)
        object.__setattr__(self, "label_available_ts", label_available_ts)
        object.__setattr__(self, "value", _freeze_json_value(self.value, "LabelValueRecord.value"))
        object.__setattr__(
            self,
            "quality_flags",
            _require_text_tuple(
                self.quality_flags,
                "LabelValueRecord.quality_flags",
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "label_spec_id", label_contract.label_spec_id)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "label_version_id": self.label_version_id,
            "label_spec_id": self.label_spec_id,
            "entity_id": self.entity_id,
            "event_ts": self.event_ts.isoformat(),
            "horizon_end_ts": self.horizon_end_ts.isoformat(),
            "label_available_ts": self.label_available_ts.isoformat(),
            "value": _thaw_json_value(self.value),
            "quality_flags": list(self.quality_flags),
        }


@dataclass(frozen=True, slots=True)
class LabelLineageRecord:
    """Lineage link from a LabelVersion to its governed contract provenance."""

    label_version: LabelVersion
    label_contract: LabelContractSpec
    label_spec_id: str
    contract_provenance: Mapping[str, Any] | FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.label_version, LabelVersion):
            raise LabelContractError("LabelLineageRecord.label_version must be a LabelVersion")
        if not isinstance(self.label_contract, LabelContractSpec):
            raise LabelContractError(
                "LabelLineageRecord.label_contract must be a LabelContractSpec"
            )
        label_spec_id = _require_label_spec_id(self.label_spec_id)
        if label_spec_id != self.label_contract.label_spec_id:
            raise LabelContractError(
                "LabelLineageRecord.label_spec_id must match LabelContractSpec.label_spec_id"
            )
        expected_version = LabelVersion.derive(self.label_contract)
        if self.label_version != expected_version:
            raise LabelContractError(
                "LabelLineageRecord.label_version must match LabelContractSpec content"
            )
        object.__setattr__(self, "label_spec_id", label_spec_id)
        object.__setattr__(
            self,
            "contract_provenance",
            _freeze_json_mapping(
                self.contract_provenance,
                "LabelLineageRecord.contract_provenance",
            ),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "label_version": self.label_version.to_dict(),
            "label_contract": self.label_contract.to_contract_dict(),
            "label_spec_id": self.label_spec_id,
            "contract_provenance": self.contract_provenance.to_dict(),
        }


def _coerce_governance_label_spec(
    value: GovernanceLabelSpec | Mapping[str, Any] | None,
) -> GovernanceLabelSpec:
    if value is None:
        raise LabelContractError("governance LabelSpec lspec_ binding is required")
    try:
        if isinstance(value, GovernanceLabelSpec):
            return validate_label_spec(value.to_dict())
        return validate_label_spec(value)
    except ValueError as exc:
        raise LabelContractError("governance LabelSpec lspec_ binding is invalid") from exc


def _validate_components_match_governance(
    spec: GovernanceLabelSpec,
    horizon: LabelHorizonSpec,
    path: LabelPathSpec,
    barriers: BarrierSpec,
    cost_adjustment: CostAdjustmentSpec,
    availability_policy: LabelAvailabilityPolicy,
) -> None:
    if horizon.horizon != spec.horizon:
        raise LabelContractError("LabelHorizonSpec.horizon must match LabelSpec.horizon")
    if path.path_rules.to_dict() != spec.path_rules:
        raise LabelContractError("LabelPathSpec.path_rules must match LabelSpec.path_rules")
    if barriers.target_stop_rules.to_dict() != spec.target_stop_rules:
        raise LabelContractError(
            "BarrierSpec.target_stop_rules must match LabelSpec.target_stop_rules"
        )
    if cost_adjustment.cost_model.to_dict() != spec.cost_model:
        raise LabelContractError("CostAdjustmentSpec.cost_model must match LabelSpec.cost_model")
    if availability_policy.availability_time != _require_aware_datetime_or_iso(
        spec.availability_time,
        "LabelSpec.availability_time",
    ):
        raise LabelContractError(
            "LabelAvailabilityPolicy.availability_time must match "
            "LabelSpec.availability_time"
        )
    if availability_policy.forbidden_feature_overlap.to_dict() != spec.forbidden_feature_overlap:
        raise LabelContractError(
            "LabelAvailabilityPolicy.forbidden_feature_overlap must match "
            "LabelSpec.forbidden_feature_overlap"
        )
    if tuple(availability_policy.leakage_checks) != tuple(spec.leakage_checks):
        raise LabelContractError(
            "LabelAvailabilityPolicy.leakage_checks must match LabelSpec.leakage_checks"
        )


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
            raise LabelContractError(f"{field_name} must be a finite JSON number")
        return value
    if isinstance(value, Mapping):
        return FrozenJsonMapping.from_mapping(value, field_name=field_name)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return tuple(
            _freeze_json_value(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        )
    raise LabelContractError(f"{field_name} must be JSON-compatible")


def _thaw_json_value(value: object) -> JsonValue:
    if isinstance(value, FrozenJsonMapping):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise LabelContractError(f"unsupported frozen JSON value type: {type(value).__name__}")


def _canonical_json(value: JsonValue, field_name: str) -> str:
    try:
        return canonical_serialize(value)
    except GovernanceSerializationError as exc:
        raise LabelContractError(f"{field_name} must be canonically serializable") from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise LabelContractError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise LabelContractError(f"{field_name} must be non-empty")
    return normalized


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LabelContractError(f"{field_name} must be a sequence of strings")
    normalized = tuple(_require_text(item, f"{field_name}[]") for item in value)
    if not allow_empty and not normalized:
        raise LabelContractError(f"{field_name} must contain at least one item")
    return normalized


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise LabelContractError(f"{field_name} must be a bool")
    return value


def _coerce_str_enum(value: object, enum_type: type[StrEnum], field_name: str) -> StrEnum:
    try:
        if isinstance(value, enum_type):
            return value
        return enum_type(_require_text(value, field_name))
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise LabelContractError(f"{field_name} must be one of: {allowed}") from exc


def _require_component(value: object, expected_type: type[object], field_name: str) -> None:
    if not isinstance(value, expected_type):
        raise LabelContractError(f"{field_name} must be a {expected_type.__name__}")


def _require_label_spec_id(value: object) -> str:
    label_spec_id = _require_text(value, "label_spec_id")
    try:
        return validate_governance_id(
            label_spec_id,
            expected_kind=GovernanceIdKind.LABEL_SPEC,
        )
    except GovernanceIdError as exc:
        raise LabelContractError("label_spec_id must be a governed LabelSpec lspec_ id") from exc


def _require_leakage_checks(value: object) -> tuple[str, ...]:
    checks = _require_text_tuple(value, "LabelAvailabilityPolicy.leakage_checks")
    normalized = frozenset(check.strip().lower() for check in checks)
    missing = REQUIRED_LEAKAGE_CHECKS - normalized
    if missing:
        raise LabelContractError(
            "LabelAvailabilityPolicy.leakage_checks must include "
            f"{', '.join(sorted(REQUIRED_LEAKAGE_CHECKS))}"
        )
    return checks


def _require_hex_hash(value: object, field_name: str) -> str:
    text = _require_text(value, field_name)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise LabelContractError(f"{field_name} must be a 64-character lowercase hex hash")
    return text


def _require_label_version_id(value: object) -> str:
    text = _require_text(value, "LabelValueRecord.label_version_id")
    if LABEL_VERSION_PATTERN.fullmatch(text) is None:
        raise LabelContractError("label_version_id must be lver_<64-hex-content-hash>")
    return text


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LabelContractError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise LabelContractError(f"{field_name} must be timezone-aware")
    return value


def _require_aware_datetime_or_iso(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _require_aware_datetime(value, field_name)
    text = _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LabelContractError(f"{field_name} must be ISO-8601") from exc
    return _require_aware_datetime(parsed, field_name)


def _duplicates(values: Sequence[str] | Any) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(duplicates)


__all__ = [
    "LABEL_CONTRACT_NAMESPACE",
    "LABEL_VERSION_ALGORITHM",
    "BarrierSpec",
    "CostAdjustmentSpec",
    "FrozenJsonMapping",
    "LabelAvailabilityConsumer",
    "LabelAvailabilityPolicy",
    "LabelContractError",
    "LabelContractSpec",
    "LabelFamily",
    "LabelHorizonSpec",
    "LabelInputSpec",
    "LabelLineageRecord",
    "LabelPathSpec",
    "LabelValueRecord",
    "LabelVersion",
]
