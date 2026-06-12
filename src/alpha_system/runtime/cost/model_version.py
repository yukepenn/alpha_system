"""Immutable cost-model identity for descriptive cost stress."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.backtest.futures_fees import (
    active_fee_schedule_cost_component_descriptor,
)
from alpha_system.backtest import costs, slippage
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.serialization import (
    content_hash as governance_content_hash,
)

COST_MODEL_VERSION_SCHEMA = "alpha_system.runtime.cost.model_version.v1"
COST_MODEL_VERSION_ID_PREFIX = "cmv"


class CostModelVersionError(ValueError):
    """Raised when a cost-model version would hide an unsupported cost state."""


@dataclass(frozen=True, slots=True, init=False)
class CostModelVersion:
    """Stable identity for the cost and slippage descriptors used by cost stress."""

    cost_model_version_id: str
    cost_model_descriptor_json: str
    slippage_model_descriptor_json: str
    slippage_is_proxy: bool
    bbo_available: bool
    zero_cost_diagnostic_only: bool
    promotion_basis_allowed: bool
    content_hash: str

    def __init__(
        self,
        *,
        cost_model: Any | None = None,
        slippage_model: Any | None = None,
        cost_model_descriptor: Mapping[str, Any] | None = None,
        slippage_model_descriptor: Mapping[str, Any] | None = None,
        slippage_is_proxy: bool = True,
        bbo_available: bool,
    ) -> None:
        if slippage_is_proxy is not True:
            raise CostModelVersionError("slippage must be explicitly labeled as a proxy")

        cost_descriptor = _resolved_cost_descriptor(
            cost_model=cost_model,
            cost_model_descriptor=cost_model_descriptor,
            bbo_available=bool(bbo_available),
        )
        slippage_descriptor = _resolved_slippage_descriptor(
            slippage_model=slippage_model,
            slippage_model_descriptor=slippage_model_descriptor,
            bbo_available=bool(bbo_available),
        )
        cost_json = _canonical_descriptor(cost_descriptor, field="cost_model_descriptor")
        slippage_json = _canonical_descriptor(
            slippage_descriptor,
            field="slippage_model_descriptor",
        )
        zero_cost_diagnostic_only = _descriptor_has_model(cost_descriptor, "zero_cost")
        payload = {
            "schema": COST_MODEL_VERSION_SCHEMA,
            "cost_model_descriptor": _json_dict(cost_json, field="cost_model_descriptor"),
            "slippage_model_descriptor": _json_dict(
                slippage_json,
                field="slippage_model_descriptor",
            ),
            "slippage_is_proxy": True,
            "bbo_available": bool(bbo_available),
            "zero_cost_diagnostic_only": zero_cost_diagnostic_only,
            "promotion_basis_allowed": False,
        }
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "cost_model_version_id",
            f"{COST_MODEL_VERSION_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "cost_model_descriptor_json", cost_json)
        object.__setattr__(self, "slippage_model_descriptor_json", slippage_json)
        object.__setattr__(self, "slippage_is_proxy", True)
        object.__setattr__(self, "bbo_available", bool(bbo_available))
        object.__setattr__(self, "zero_cost_diagnostic_only", zero_cost_diagnostic_only)
        object.__setattr__(self, "promotion_basis_allowed", False)
        object.__setattr__(self, "content_hash", digest)

    @classmethod
    def from_mappings(
        cls,
        *,
        cost_model_descriptor: Mapping[str, Any] | None = None,
        slippage_model_descriptor: Mapping[str, Any] | None = None,
        slippage_is_proxy: bool = True,
        bbo_available: bool,
    ) -> CostModelVersion:
        """Build a version by parsing mappings through the consumed primitives."""

        return cls(
            cost_model_descriptor=cost_model_descriptor,
            slippage_model_descriptor=slippage_model_descriptor,
            slippage_is_proxy=slippage_is_proxy,
            bbo_available=bbo_available,
        )

    @classmethod
    def from_models(
        cls,
        *,
        cost_model: Any,
        slippage_model: Any,
        slippage_is_proxy: bool = True,
        bbo_available: bool,
    ) -> CostModelVersion:
        """Build a version by serializing already-constructed primitive models."""

        return cls(
            cost_model=cost_model,
            slippage_model=slippage_model,
            slippage_is_proxy=slippage_is_proxy,
            bbo_available=bbo_available,
        )

    @property
    def cost_model_descriptor(self) -> dict[str, JsonValue]:
        """Return the normalized primitive cost-model descriptor."""

        return _json_dict(self.cost_model_descriptor_json, field="cost_model_descriptor")

    @property
    def slippage_model_descriptor(self) -> dict[str, JsonValue]:
        """Return the normalized primitive slippage-model descriptor."""

        return _json_dict(self.slippage_model_descriptor_json, field="slippage_model_descriptor")

    def to_dict(self) -> dict[str, object]:
        """Return a stable, summary-only version payload."""

        return {
            "schema": COST_MODEL_VERSION_SCHEMA,
            "cost_model_version_id": self.cost_model_version_id,
            "cost_model_descriptor": self.cost_model_descriptor,
            "slippage_model_descriptor": self.slippage_model_descriptor,
            "slippage_is_proxy": self.slippage_is_proxy,
            "bbo_available": self.bbo_available,
            "zero_cost_diagnostic_only": self.zero_cost_diagnostic_only,
            "promotion_basis_allowed": self.promotion_basis_allowed,
            "content_hash": self.content_hash,
        }


def _resolved_cost_descriptor(
    *,
    cost_model: Any | None,
    cost_model_descriptor: Mapping[str, Any] | None,
    bbo_available: bool,
) -> dict[str, Any]:
    if cost_model is not None and cost_model_descriptor is not None:
        raise CostModelVersionError("supply either cost_model or cost_model_descriptor, not both")
    if cost_model is None and cost_model_descriptor is None and bbo_available:
        cost_model_descriptor = {
            "model": "composite",
            "components": (
                active_fee_schedule_cost_component_descriptor(default_symbol="ES"),
                {"model": "spread_cost", "assumption": "half_spread"},
            ),
        }
    if cost_model is None and cost_model_descriptor is None and not bbo_available:
        cost_model_descriptor = {
            "model": "composite",
            "components": (
                active_fee_schedule_cost_component_descriptor(default_symbol="ES"),
            ),
        }
    if cost_model is None:
        cost_model = costs.cost_model_from_mapping(cost_model_descriptor)
    return _model_to_dict(cost_model, field="cost_model")


def _resolved_slippage_descriptor(
    *,
    slippage_model: Any | None,
    slippage_model_descriptor: Mapping[str, Any] | None,
    bbo_available: bool,
) -> dict[str, Any]:
    if slippage_model is not None and slippage_model_descriptor is not None:
        raise CostModelVersionError(
            "supply either slippage_model or slippage_model_descriptor, not both"
        )
    if slippage_model is None and slippage_model_descriptor is None and bbo_available:
        slippage_model_descriptor = {
            "model": "composite",
            "components": (
                {
                    "model": "spread_sensitive",
                    "spread_fraction": "0.25",
                    "fallback_bps": "0.5",
                },
            ),
        }
    if slippage_model is None:
        slippage_model = slippage.slippage_model_from_mapping(slippage_model_descriptor)
    return _model_to_dict(slippage_model, field="slippage_model")


def _model_to_dict(model: Any, *, field: str) -> dict[str, Any]:
    to_dict = getattr(model, "to_dict", None)
    if not callable(to_dict):
        raise CostModelVersionError(f"{field} must expose to_dict()")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise CostModelVersionError(f"{field}.to_dict() must return a mapping")
    return dict(payload)


def _canonical_descriptor(value: Mapping[str, Any], *, field: str) -> str:
    try:
        return canonical_serialize(cast(JsonValue, dict(value)))
    except GovernanceSerializationError as exc:
        raise CostModelVersionError(f"{field} must be JSON-compatible: {exc}") from exc


def _json_dict(text: str, *, field: str) -> dict[str, JsonValue]:
    try:
        value = deserialize(text)
    except GovernanceSerializationError as exc:
        raise CostModelVersionError(f"{field} must be serialized JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CostModelVersionError(f"{field} must serialize to a mapping")
    return dict(value)


def _descriptor_has_model(value: Mapping[str, Any], model_name: str) -> bool:
    if value.get("model") == model_name:
        return True
    components = value.get("components", ())
    if not isinstance(components, list | tuple):
        return False
    return any(
        isinstance(component, Mapping) and _descriptor_has_model(component, model_name)
        for component in components
    )


__all__ = [
    "COST_MODEL_VERSION_SCHEMA",
    "CostModelVersion",
    "CostModelVersionError",
]
