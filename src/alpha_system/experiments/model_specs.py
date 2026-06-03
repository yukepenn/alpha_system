"""Model specification registry for the ML/factor-combination MVP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


ML_ENGINE_VERSION = "ml_factor_combination_mvp_v1"


class ModelSpecError(ValueError):
    """Raised when a model spec is invalid or intentionally deferred."""


@dataclass(frozen=True, slots=True)
class ModelTypeRegistration:
    """Metadata for an ML model type."""

    model_type: str
    implemented: bool
    description: str
    allowed_parameters: tuple[str, ...] = ()
    placeholder_reason: str = ""

    @property
    def design_only(self) -> bool:
        return not self.implemented

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MODEL_TYPE_REGISTRY: dict[str, ModelTypeRegistration] = {}


def register_model_type(registration: ModelTypeRegistration) -> None:
    """Register one model type for validation and discovery."""
    model_type = _text(registration.model_type, "model_type")
    if model_type in MODEL_TYPE_REGISTRY:
        raise ModelSpecError(f"model type already registered: {model_type}")
    MODEL_TYPE_REGISTRY[model_type] = registration


def registered_model_types() -> dict[str, ModelTypeRegistration]:
    """Return a copy of the model type registry."""
    return dict(MODEL_TYPE_REGISTRY)


def get_model_type(model_type: str) -> ModelTypeRegistration:
    """Return a registered model type or raise a validation error."""
    key = _text(model_type, "model_type")
    try:
        return MODEL_TYPE_REGISTRY[key]
    except KeyError as exc:
        raise ModelSpecError(f"unsupported model type: {key}") from exc


def require_executable_model(model_type: str) -> ModelTypeRegistration:
    """Require a model type that has an executable MVP training path."""
    registration = get_model_type(model_type)
    if not registration.implemented:
        reason = registration.placeholder_reason or "model type is design-only in this MVP"
        raise ModelSpecError(f"{registration.model_type} is deferred: {reason}")
    return registration


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Deterministic ML model declaration."""

    model_id: str
    model_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    fit_intercept: bool = True
    random_seed: int | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ModelSpec":
        if not isinstance(payload, Mapping):
            raise ModelSpecError("model_spec must be a mapping")
        required = ("model_id", "model_type")
        missing = tuple(field_name for field_name in required if _missing(payload.get(field_name)))
        if missing:
            raise ModelSpecError(f"model_spec missing required fields: {', '.join(missing)}")
        return cls(
            model_id=_text(payload["model_id"], "model_id"),
            model_type=_text(payload["model_type"], "model_type"),
            parameters=_parameters(payload.get("parameters", {})),
            fit_intercept=_bool(payload.get("fit_intercept", True), "fit_intercept"),
            random_seed=_optional_int(payload.get("random_seed"), "random_seed"),
        )

    def __post_init__(self) -> None:
        registration = get_model_type(self.model_type)
        object.__setattr__(self, "model_id", _text(self.model_id, "model_id"))
        object.__setattr__(self, "parameters", _parameters(self.parameters))
        unknown = tuple(
            sorted(set(self.parameters).difference(registration.allowed_parameters))
        )
        if unknown:
            raise ModelSpecError(
                f"unsupported parameter(s) for {self.model_type}: {', '.join(unknown)}",
            )
        if self.model_type in {"linear_baseline", "ridge_baseline", "ic_weighted_score"}:
            _non_negative_float(self.parameters.get("ridge_l2", 0.0), "ridge_l2")

    @property
    def registration(self) -> ModelTypeRegistration:
        return get_model_type(self.model_type)

    @property
    def executable(self) -> bool:
        return self.registration.implemented

    @property
    def ridge_l2(self) -> float:
        return _non_negative_float(self.parameters.get("ridge_l2", 0.0), "ridge_l2")

    def require_executable(self) -> None:
        require_executable_model(self.model_type)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _register_defaults() -> None:
    defaults = (
        ModelTypeRegistration(
            model_type="linear_baseline",
            implemented=True,
            description="Deterministic covariance-weighted linear baseline for fixture research.",
            allowed_parameters=("ridge_l2",),
        ),
        ModelTypeRegistration(
            model_type="ridge_baseline",
            implemented=True,
            description="Deterministic ridge-style shrinkage baseline for fixture research.",
            allowed_parameters=("ridge_l2",),
        ),
        ModelTypeRegistration(
            model_type="ic_weighted_score",
            implemented=True,
            description="Deterministic IC-weighted factor score baseline.",
            allowed_parameters=("ridge_l2",),
        ),
        ModelTypeRegistration(
            model_type="orthogonalized_score",
            implemented=False,
            description="Reserved score-combination design placeholder.",
            allowed_parameters=(),
            placeholder_reason="orthogonalization rules require a later reviewed phase",
        ),
        ModelTypeRegistration(
            model_type="lightgbm",
            implemented=False,
            description="Reserved gradient-boosted tree design placeholder.",
            allowed_parameters=(),
            placeholder_reason="no heavy or server-style dependency is introduced",
        ),
        ModelTypeRegistration(
            model_type="xgboost",
            implemented=False,
            description="Reserved gradient-boosted tree design placeholder.",
            allowed_parameters=(),
            placeholder_reason="no heavy or server-style dependency is introduced",
        ),
        ModelTypeRegistration(
            model_type="random_forest",
            implemented=False,
            description="Reserved tree ensemble design placeholder.",
            allowed_parameters=(),
            placeholder_reason="not part of the deterministic MVP training path",
        ),
        ModelTypeRegistration(
            model_type="meta_labeling",
            implemented=False,
            description="Reserved meta-labeling design placeholder.",
            allowed_parameters=(),
            placeholder_reason="requires additional leakage controls in a later phase",
        ),
        ModelTypeRegistration(
            model_type="ensemble",
            implemented=False,
            description="Reserved ensemble design placeholder.",
            allowed_parameters=(),
            placeholder_reason="promotion and selection controls are deferred",
        ),
        ModelTypeRegistration(
            model_type="regime_conditioned_model",
            implemented=False,
            description="Reserved regime-conditioned design placeholder.",
            allowed_parameters=(),
            placeholder_reason="requires reviewed regime-feature contracts",
        ),
    )
    for registration in defaults:
        MODEL_TYPE_REGISTRY.setdefault(registration.model_type, registration)


def _parameters(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ModelSpecError("model parameters must be a mapping")
    return dict(value)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelSpecError(f"{field_name} must be a non-empty string")
    return value.strip()


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise ModelSpecError(f"{field_name} must be boolean")


def _optional_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ModelSpecError(f"{field_name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ModelSpecError(f"{field_name} must be an integer") from exc


def _non_negative_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise ModelSpecError(f"{field_name} must be non-negative")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ModelSpecError(f"{field_name} must be non-negative") from exc
    if number < 0:
        raise ModelSpecError(f"{field_name} must be non-negative")
    return number


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return len(value) == 0
    return False


_register_defaults()
