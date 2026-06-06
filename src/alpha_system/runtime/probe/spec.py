"""Immutable Signal Probe specification contracts.

Signal probes bind one approved AlphaSpec / StudySpec reference pair to one
resolved RuntimeInputPack and one bounded threshold neighborhood. They are a
descriptive fast path only: not strategy validation, not a candidate, and not a
promotion decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, cast

from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)
from alpha_system.runtime.cost import CostStressSpec
from alpha_system.runtime.input_resolver import (
    LOCKED_PARTITION_IDS,
    FeaturePackHandle,
    LabelPackHandle,
    RuntimeInputPack,
)

SIGNAL_PROBE_SPEC_SCHEMA = "alpha_system.runtime.probe.spec.v1"
SIGNAL_PROBE_SPEC_ID_PREFIX = "sprobe"
MAX_THRESHOLD_COUNT = 9
LABEL_AS_FEATURE_TOKENS: frozenset[str] = frozenset(
    {
        "horizon_end_ts",
        "label",
        "label_available_ts",
        "label_outcome",
        "label_value",
        "target",
    }
)


class SignalProbeContractError(ValueError):
    """Raised when a SignalProbeSpec would violate fail-closed invariants."""


class DirectionPolicy(StrEnum):
    """Allowed long/short/flat direction policies for a simple threshold probe."""

    LONG_SHORT_FLAT = "long_short_flat"
    LONG_FLAT = "long_flat"
    SHORT_FLAT = "short_flat"


class FillTiming(StrEnum):
    """Fill timing policies that forbid same-bar optimistic execution."""

    NEXT_BAR = "next_bar"
    EXPLICIT_DELAY = "explicit_delay"


@dataclass(frozen=True, slots=True)
class FillPolicy:
    """Probe-local fill policy; same-bar fills are forbidden."""

    timing: FillTiming | str = FillTiming.NEXT_BAR
    delay_bars: int = 1
    allow_same_bar_fill: bool = False

    def __post_init__(self) -> None:
        timing = _coerce_fill_timing(self.timing)
        object.__setattr__(self, "timing", timing)
        if isinstance(self.delay_bars, bool) or not isinstance(self.delay_bars, int):
            raise SignalProbeContractError("fill delay_bars must be an integer")
        if self.delay_bars < 1:
            raise SignalProbeContractError("same-bar optimistic fill is forbidden")
        if self.allow_same_bar_fill is not False:
            raise SignalProbeContractError("allow_same_bar_fill must be false")
        if timing is FillTiming.NEXT_BAR and self.delay_bars != 1:
            raise SignalProbeContractError("next_bar fill timing requires delay_bars=1")

    def to_dict(self) -> dict[str, object]:
        """Return a stable fill-policy payload."""

        return {
            "timing": self.timing.value,
            "delay_bars": self.delay_bars,
            "allow_same_bar_fill": False,
            "same_bar_optimistic_fill_forbidden": True,
        }


@dataclass(frozen=True, slots=True)
class SignalFeatureRef:
    """Reference to the already-approved feature/signal input used by a probe."""

    feature_version_id: str
    feature_request_id: str
    signal_name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_version_id",
            _required_text(self.feature_version_id, field="feature_version_id"),
        )
        object.__setattr__(
            self,
            "feature_request_id",
            _required_text(self.feature_request_id, field="feature_request_id"),
        )
        signal_name = _required_text(self.signal_name, field="signal_name")
        if _contains_label_token(signal_name):
            raise SignalProbeContractError("probe signal_name must not reference label fields")
        object.__setattr__(self, "signal_name", signal_name)

    @classmethod
    def from_feature_pack(
        cls,
        feature_pack: FeaturePackHandle,
        *,
        signal_name: str,
    ) -> SignalFeatureRef:
        """Build a probe feature reference from a RuntimeInputPack handle."""

        return cls(
            feature_version_id=feature_pack.feature_version_id,
            feature_request_id=feature_pack.feature_request_id,
            signal_name=signal_name,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> SignalFeatureRef:
        """Build a feature reference from a JSON-compatible mapping."""

        _reject_extra_keys(
            value,
            allowed={"feature_version_id", "feature_request_id", "signal_name"},
            field="feature_ref",
        )
        return cls(
            feature_version_id=value.get("feature_version_id"),
            feature_request_id=value.get("feature_request_id"),
            signal_name=value.get("signal_name"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable feature reference payload."""

        return {
            "feature_version_id": self.feature_version_id,
            "feature_request_id": self.feature_request_id,
            "signal_name": self.signal_name,
        }


@dataclass(frozen=True, slots=True)
class SignalLabelRef:
    """Reference to the approved label/horizon used only for offline evaluation."""

    label_version_id: str
    label_spec_id: str
    label_name: str
    horizon: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label_version_id",
            _required_text(self.label_version_id, field="label_version_id"),
        )
        object.__setattr__(
            self,
            "label_spec_id",
            _required_text(self.label_spec_id, field="label_spec_id"),
        )
        object.__setattr__(self, "label_name", _required_text(self.label_name, field="label_name"))
        object.__setattr__(self, "horizon", _required_text(self.horizon, field="horizon"))

    @classmethod
    def from_label_pack(
        cls,
        label_pack: LabelPackHandle,
        *,
        label_name: str | None = None,
        horizon: str,
    ) -> SignalLabelRef:
        """Build a probe label reference from a RuntimeInputPack handle."""

        return cls(
            label_version_id=label_pack.label_version_id,
            label_spec_id=label_pack.label_spec_id,
            label_name=label_name or label_pack.label_id,
            horizon=horizon,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> SignalLabelRef:
        """Build a label reference from a JSON-compatible mapping."""

        _reject_extra_keys(
            value,
            allowed={"label_version_id", "label_spec_id", "label_name", "horizon"},
            field="label_ref",
        )
        return cls(
            label_version_id=value.get("label_version_id"),
            label_spec_id=value.get("label_spec_id"),
            label_name=value.get("label_name"),
            horizon=value.get("horizon"),
        )

    def to_dict(self) -> dict[str, str]:
        """Return a stable label reference payload."""

        return {
            "label_version_id": self.label_version_id,
            "label_spec_id": self.label_spec_id,
            "label_name": self.label_name,
            "horizon": self.horizon,
        }


@dataclass(frozen=True, slots=True)
class SignalProbeSpecRef:
    """Compact reference to a SignalProbeSpec."""

    signal_probe_spec_id: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signal_probe_spec_id",
            _required_text(self.signal_probe_spec_id, field="signal_probe_spec_id"),
        )
        object.__setattr__(self, "content_hash", _required_text(self.content_hash, field="hash"))

    def to_dict(self) -> dict[str, str]:
        """Return a stable spec reference."""

        return {
            "signal_probe_spec_id": self.signal_probe_spec_id,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True, init=False)
class SignalProbeSpec:
    """Immutable contract for one simple long/short/flat signal probe."""

    signal_probe_spec_id: str
    alpha_spec_ref: str
    study_spec_ref: str
    runtime_input_pack: RuntimeInputPack
    runtime_input_pack_content_hash: str
    feature_ref: SignalFeatureRef
    label_ref: SignalLabelRef
    direction_policy: DirectionPolicy
    thresholds: tuple[Decimal, ...]
    primary_threshold: Decimal
    fill_policy: FillPolicy
    cost_stress_spec: CostStressSpec
    spec_metadata_json: str
    content_hash: str

    def __init__(
        self,
        *,
        alpha_spec_ref: str | None,
        study_spec_ref: str | None,
        runtime_input_pack: RuntimeInputPack | None,
        feature_ref: SignalFeatureRef | Mapping[str, Any],
        label_ref: SignalLabelRef | Mapping[str, Any],
        direction_policy: DirectionPolicy | str = DirectionPolicy.LONG_SHORT_FLAT,
        thresholds: Sequence[Decimal | int | float | str] = (),
        primary_threshold: Decimal | int | float | str | None = None,
        fill_policy: FillPolicy | Mapping[str, Any] | None = None,
        cost_stress_spec: CostStressSpec | None = None,
        spec_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        normalized_alpha_ref = _required_text(alpha_spec_ref, field="alpha_spec_ref")
        normalized_study_ref = _required_text(study_spec_ref, field="study_spec_ref")
        if not isinstance(runtime_input_pack, RuntimeInputPack):
            raise SignalProbeContractError("SignalProbeSpec requires a resolved RuntimeInputPack")
        if runtime_input_pack.alpha_spec_ref != normalized_alpha_ref:
            raise SignalProbeContractError(
                "alpha_spec_ref must match the resolved RuntimeInputPack"
            )
        if runtime_input_pack.study_spec_ref != normalized_study_ref:
            raise SignalProbeContractError(
                "study_spec_ref must match the resolved RuntimeInputPack"
            )
        normalized_feature = _coerce_feature_ref(feature_ref)
        normalized_label = _coerce_label_ref(label_ref)
        normalized_direction = _coerce_direction(direction_policy)
        normalized_thresholds = _coerce_thresholds(thresholds)
        normalized_primary = _coerce_primary_threshold(primary_threshold, normalized_thresholds)
        normalized_fill = _coerce_fill_policy(fill_policy)
        if not isinstance(cost_stress_spec, CostStressSpec):
            raise SignalProbeContractError("SignalProbeSpec requires a CostStressSpec")
        if "double_cost" not in cost_stress_spec.profile_names:
            raise SignalProbeContractError("cost stress with double_cost is required")

        _validate_runtime_input_pack(runtime_input_pack)
        _validate_feature_binding(runtime_input_pack, normalized_feature)
        _validate_label_binding(runtime_input_pack, normalized_label)
        _validate_locked_partition_use(runtime_input_pack)

        metadata_json = _canonical_mapping(spec_metadata or {}, field="spec_metadata")
        input_pack_hash = governance_content_hash(cast(JsonValue, runtime_input_pack.to_dict()))
        payload = {
            "schema": SIGNAL_PROBE_SPEC_SCHEMA,
            "alpha_spec_ref": normalized_alpha_ref,
            "study_spec_ref": normalized_study_ref,
            "runtime_input_pack_content_hash": input_pack_hash,
            "dataset_version_id": runtime_input_pack.dataset_version_id,
            "feature_ref": normalized_feature.to_dict(),
            "label_ref": normalized_label.to_dict(),
            "direction_policy": normalized_direction.value,
            "thresholds": [_decimal_text(item) for item in normalized_thresholds],
            "primary_threshold": _decimal_text(normalized_primary),
            "fill_policy": normalized_fill.to_dict(),
            "cost_stress_spec": cost_stress_spec.to_dict(),
            "spec_metadata": _json_dict(metadata_json, field="spec_metadata"),
            "fast_path": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "not_a_backtest": True,
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "signal_probe_spec_id",
            f"{SIGNAL_PROBE_SPEC_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "alpha_spec_ref", normalized_alpha_ref)
        object.__setattr__(self, "study_spec_ref", normalized_study_ref)
        object.__setattr__(self, "runtime_input_pack", runtime_input_pack)
        object.__setattr__(self, "runtime_input_pack_content_hash", input_pack_hash)
        object.__setattr__(self, "feature_ref", normalized_feature)
        object.__setattr__(self, "label_ref", normalized_label)
        object.__setattr__(self, "direction_policy", normalized_direction)
        object.__setattr__(self, "thresholds", normalized_thresholds)
        object.__setattr__(self, "primary_threshold", normalized_primary)
        object.__setattr__(self, "fill_policy", normalized_fill)
        object.__setattr__(self, "cost_stress_spec", cost_stress_spec)
        object.__setattr__(self, "spec_metadata_json", metadata_json)
        object.__setattr__(self, "content_hash", digest)

    @property
    def spec_metadata(self) -> dict[str, JsonValue]:
        """Return spec metadata as a defensive JSON-compatible copy."""

        return _json_dict(self.spec_metadata_json, field="spec_metadata")

    def to_ref(self) -> SignalProbeSpecRef:
        """Return the compact spec reference used by reports."""

        return SignalProbeSpecRef(
            signal_probe_spec_id=self.signal_probe_spec_id,
            content_hash=self.content_hash,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable reference-only signal probe spec payload."""

        return {
            "schema": SIGNAL_PROBE_SPEC_SCHEMA,
            "signal_probe_spec_id": self.signal_probe_spec_id,
            "alpha_spec_ref": self.alpha_spec_ref,
            "study_spec_ref": self.study_spec_ref,
            "runtime_input_pack_ref": {
                "dataset_version_id": self.runtime_input_pack.dataset_version_id,
                "content_hash": self.runtime_input_pack_content_hash,
            },
            "feature_ref": self.feature_ref.to_dict(),
            "label_ref": self.label_ref.to_dict(),
            "direction_policy": self.direction_policy.value,
            "thresholds": [_decimal_text(item) for item in self.thresholds],
            "primary_threshold": _decimal_text(self.primary_threshold),
            "fill_policy": self.fill_policy.to_dict(),
            "cost_stress_spec": self.cost_stress_spec.to_dict(),
            "spec_metadata": self.spec_metadata,
            "content_hash": self.content_hash,
            "fast_path": True,
            "not_strategy_validation": True,
            "not_a_candidate": True,
            "not_a_backtest": True,
            "promotion_basis_allowed": False,
        }


def _coerce_feature_ref(value: SignalFeatureRef | Mapping[str, Any]) -> SignalFeatureRef:
    if isinstance(value, SignalFeatureRef):
        return value
    if isinstance(value, Mapping):
        return SignalFeatureRef.from_mapping(value)
    raise SignalProbeContractError("feature_ref must be SignalFeatureRef or mapping")


def _coerce_label_ref(value: SignalLabelRef | Mapping[str, Any]) -> SignalLabelRef:
    if isinstance(value, SignalLabelRef):
        return value
    if isinstance(value, Mapping):
        return SignalLabelRef.from_mapping(value)
    raise SignalProbeContractError("label_ref must be SignalLabelRef or mapping")


def _coerce_fill_policy(value: FillPolicy | Mapping[str, Any] | None) -> FillPolicy:
    if value is None:
        return FillPolicy()
    if isinstance(value, FillPolicy):
        return value
    if isinstance(value, Mapping):
        _reject_extra_keys(
            value,
            allowed={"timing", "delay_bars", "allow_same_bar_fill"},
            field="fill_policy",
        )
        return FillPolicy(
            timing=value.get("timing", FillTiming.NEXT_BAR),
            delay_bars=int(value.get("delay_bars", 1)),
            allow_same_bar_fill=bool(value.get("allow_same_bar_fill", False)),
        )
    raise SignalProbeContractError("fill_policy must be FillPolicy, mapping, or None")


def _coerce_direction(value: DirectionPolicy | str) -> DirectionPolicy:
    if isinstance(value, DirectionPolicy):
        return value
    if isinstance(value, str):
        try:
            return DirectionPolicy(value)
        except ValueError as exc:
            raise SignalProbeContractError(f"unsupported direction_policy: {value}") from exc
    raise SignalProbeContractError("direction_policy must be DirectionPolicy or str")


def _coerce_fill_timing(value: FillTiming | str) -> FillTiming:
    if isinstance(value, FillTiming):
        return value
    if isinstance(value, str):
        try:
            return FillTiming(value)
        except ValueError as exc:
            raise SignalProbeContractError(f"unsupported fill timing: {value}") from exc
    raise SignalProbeContractError("fill timing must be FillTiming or str")


def _coerce_thresholds(
    values: Sequence[Decimal | int | float | str],
) -> tuple[Decimal, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise SignalProbeContractError("thresholds must be a finite declared sequence")
    if not values:
        raise SignalProbeContractError("thresholds must not be empty")
    if len(values) > MAX_THRESHOLD_COUNT:
        raise SignalProbeContractError("threshold neighborhood exceeds the bounded maximum")
    thresholds = tuple(_positive_decimal(value, field="threshold") for value in values)
    if len(set(thresholds)) != len(thresholds):
        raise SignalProbeContractError("thresholds must not contain duplicates")
    return thresholds


def _coerce_primary_threshold(
    value: Decimal | int | float | str | None,
    thresholds: tuple[Decimal, ...],
) -> Decimal:
    if value is None:
        return thresholds[0]
    primary = _positive_decimal(value, field="primary_threshold")
    if primary not in thresholds:
        raise SignalProbeContractError("primary_threshold must be in the threshold neighborhood")
    return primary


def _validate_runtime_input_pack(runtime_input_pack: RuntimeInputPack) -> None:
    if not runtime_input_pack.feature_packs:
        raise SignalProbeContractError("SignalProbeSpec requires at least one feature pack handle")
    if not runtime_input_pack.label_packs:
        raise SignalProbeContractError("SignalProbeSpec requires at least one label pack handle")
    for index, feature in enumerate(runtime_input_pack.feature_packs):
        if _missing(getattr(feature, "first_available_ts", None)):
            raise SignalProbeContractError(
                f"feature_packs[{index}] lacks required available_ts metadata"
            )
    for index, label in enumerate(runtime_input_pack.label_packs):
        if _missing(getattr(label, "first_label_available_ts", None)):
            raise SignalProbeContractError(
                f"label_packs[{index}] lacks required label_available_ts metadata"
            )


def _validate_feature_binding(
    runtime_input_pack: RuntimeInputPack,
    feature_ref: SignalFeatureRef,
) -> None:
    for feature in runtime_input_pack.feature_packs:
        if (
            feature.feature_version_id == feature_ref.feature_version_id
            and feature.feature_request_id == feature_ref.feature_request_id
        ):
            return
    raise SignalProbeContractError("feature_ref must match a RuntimeInputPack feature pack")


def _validate_label_binding(
    runtime_input_pack: RuntimeInputPack,
    label_ref: SignalLabelRef,
) -> None:
    for label in runtime_input_pack.label_packs:
        if (
            label.label_version_id == label_ref.label_version_id
            and label.label_spec_id == label_ref.label_spec_id
        ):
            return
    raise SignalProbeContractError("label_ref must match a RuntimeInputPack label pack")


def _validate_locked_partition_use(runtime_input_pack: RuntimeInputPack) -> None:
    partition_scope = runtime_input_pack.partition_scope
    partition_id = str(partition_scope.get("partition_id", ""))
    if _selection_on_locked_marker(partition_scope):
        raise SignalProbeContractError("locked-test selection is forbidden for signal probes")
    if partition_id in LOCKED_PARTITION_IDS and not _contains_contamination_metadata(
        runtime_input_pack.governance_metadata
    ):
        raise SignalProbeContractError(
            "locked or shadow partition use requires governance contamination metadata"
        )


def _contains_contamination_metadata(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if "contamination" in normalized_key and not _missing(item):
                return True
            if normalized_key == "governance_metadata" and not _missing(item):
                return True
            if _contains_contamination_metadata(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_contamination_metadata(item) for item in value)
    return False


def _selection_on_locked_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_token(str(key))
            if "selection" in normalized_key and _contains_locked_partition_marker(item):
                return True
            if _selection_on_locked_marker(item):
                return True
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_selection_on_locked_marker(item) for item in value)
    return False


def _contains_locked_partition_marker(value: object) -> bool:
    if isinstance(value, str):
        normalized = _normalize_token(value)
        return any(_normalize_token(partition) in normalized for partition in LOCKED_PARTITION_IDS)
    if isinstance(value, Mapping):
        return any(
            _contains_locked_partition_marker(key) or _contains_locked_partition_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_locked_partition_marker(item) for item in value)
    return False


def _contains_label_token(value: str) -> bool:
    normalized = _normalize_token(value)
    return any(_normalize_token(token) in normalized for token in LABEL_AS_FEATURE_TOKENS)


def _normalize_token(value: object) -> str:
    text = str(value).strip().lower()
    return "".join(char if char.isalnum() else "_" for char in text)


def _canonical_mapping(value: Mapping[str, Any], *, field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise SignalProbeContractError(f"{field} must be JSON-compatible: {exc}") from exc


def _json_dict(text: str, *, field: str) -> dict[str, JsonValue]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise SignalProbeContractError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SignalProbeContractError(f"{field} must serialize to a mapping")
    return dict(value)


def _reject_extra_keys(value: Mapping[str, Any], *, allowed: set[str], field: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise SignalProbeContractError(
            f"{field} contains unsupported fields: {', '.join(sorted(extra))}"
        )


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SignalProbeContractError(f"{field} is required")
    return value.strip()


def _positive_decimal(value: object, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise SignalProbeContractError(f"{field} must be a positive finite number")
    try:
        active = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SignalProbeContractError(f"{field} must be numeric") from exc
    if not active.is_finite() or active <= Decimal("0"):
        raise SignalProbeContractError(f"{field} must be a positive finite number")
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


__all__ = [
    "DirectionPolicy",
    "FillPolicy",
    "FillTiming",
    "MAX_THRESHOLD_COUNT",
    "SIGNAL_PROBE_SPEC_SCHEMA",
    "SignalFeatureRef",
    "SignalLabelRef",
    "SignalProbeContractError",
    "SignalProbeSpec",
    "SignalProbeSpecRef",
]
