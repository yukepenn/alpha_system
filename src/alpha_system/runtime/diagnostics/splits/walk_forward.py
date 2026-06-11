"""Purged and embargoed walk-forward split wiring for runtime diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.experiments.splits import (
    SplitError,
    SplitWindow,
    apply_purge_embargo,
    assert_chronological_split,
    walk_forward_splits,
)
from alpha_system.runtime.diagnostics.contracts import DiagnosticsHalfLifeProtocol

JsonScalar = None | bool | int | float | str

_PROTOCOL_DEFAULTS: dict[DiagnosticsHalfLifeProtocol, dict[str, int]] = {
    DiagnosticsHalfLifeProtocol.STRUCTURAL: {
        "train_window": 960,
        "validation_window": 240,
        "step_size": 240,
        "purge_gap": 120,
        "embargo_gap": 120,
        "min_fold_count": 2,
    },
    DiagnosticsHalfLifeProtocol.MEDIUM: {
        "train_window": 320,
        "validation_window": 80,
        "step_size": 80,
        "purge_gap": 40,
        "embargo_gap": 40,
        "min_fold_count": 2,
    },
    DiagnosticsHalfLifeProtocol.FAST: {
        "train_window": 80,
        "validation_window": 20,
        "step_size": 20,
        "purge_gap": 10,
        "embargo_gap": 10,
        "min_fold_count": 2,
    },
}


class WalkForwardSplitError(ValueError):
    """Raised when runtime walk-forward splits cannot be built safely."""


@dataclass(frozen=True, slots=True)
class WalkForwardSplitConfig:
    """Bounded, overridable walk-forward split configuration."""

    half_life_protocol: DiagnosticsHalfLifeProtocol
    train_window: int
    validation_window: int
    step_size: int
    purge_gap: int
    embargo_gap: int
    min_fold_count: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "half_life_protocol",
            coerce_half_life_protocol(self.half_life_protocol),
        )
        object.__setattr__(self, "train_window", _positive_int(self.train_window, "train_window"))
        object.__setattr__(
            self,
            "validation_window",
            _positive_int(self.validation_window, "validation_window"),
        )
        object.__setattr__(self, "step_size", _positive_int(self.step_size, "step_size"))
        object.__setattr__(self, "purge_gap", _non_negative_int(self.purge_gap, "purge_gap"))
        object.__setattr__(
            self,
            "embargo_gap",
            _non_negative_int(self.embargo_gap, "embargo_gap"),
        )
        object.__setattr__(
            self,
            "min_fold_count",
            _positive_int(self.min_fold_count, "min_fold_count"),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> WalkForwardSplitConfig:
        """Build a config from a JSON-compatible mapping."""

        allowed = {
            "half_life_protocol",
            "protocol",
            "train_window",
            "validation_window",
            "step_size",
            "purge_gap",
            "embargo_gap",
            "min_fold_count",
        }
        extra = set(value) - allowed
        if extra:
            raise WalkForwardSplitError(
                f"unsupported walk-forward config fields: {', '.join(sorted(extra))}"
            )
        protocol = coerce_half_life_protocol(
            value.get(
                "half_life_protocol", value.get("protocol", DiagnosticsHalfLifeProtocol.MEDIUM)
            )
        )
        defaults = default_walk_forward_split_config(protocol)
        return cls(
            half_life_protocol=protocol,
            train_window=value.get("train_window", defaults.train_window),
            validation_window=value.get("validation_window", defaults.validation_window),
            step_size=value.get("step_size", defaults.step_size),
            purge_gap=value.get("purge_gap", defaults.purge_gap),
            embargo_gap=value.get("embargo_gap", defaults.embargo_gap),
            min_fold_count=value.get("min_fold_count", defaults.min_fold_count),
        )

    def to_dict(self) -> dict[str, JsonScalar]:
        """Return scalar configuration metadata."""

        return {
            "half_life_protocol": self.half_life_protocol.value,
            "train_window": self.train_window,
            "validation_window": self.validation_window,
            "step_size": self.step_size,
            "purge_gap": self.purge_gap,
            "embargo_gap": self.embargo_gap,
            "min_fold_count": self.min_fold_count,
        }


@dataclass(frozen=True, slots=True)
class WalkForwardSplitPlan:
    """Value-free walk-forward fold metadata for runtime diagnostics."""

    config: WalkForwardSplitConfig
    sample_count: int
    folds: tuple[SplitWindow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_count", _positive_int(self.sample_count, "sample_count"))
        if not self.folds:
            raise WalkForwardSplitError("walk-forward plan requires at least one fold")
        if len(self.folds) < self.config.min_fold_count:
            raise WalkForwardSplitError(
                "walk-forward plan produced "
                f"{len(self.folds)} folds below the configured minimum of "
                f"{self.config.min_fold_count}"
            )

    @property
    def fold_count(self) -> int:
        """Return the number of generated folds."""

        return len(self.folds)

    def scalar_summary(self) -> dict[str, JsonScalar]:
        """Return scalar-only metadata suitable for shared diagnostics reports."""

        return {
            "walk_forward_enabled": True,
            "walk_forward_fold_count": len(self.folds),
            "walk_forward_sample_count": self.sample_count,
            "walk_forward_half_life_protocol": self.config.half_life_protocol.value,
            "walk_forward_train_window": self.config.train_window,
            "walk_forward_validation_window": self.config.validation_window,
            "walk_forward_step_size": self.config.step_size,
            "walk_forward_purge_gap": self.config.purge_gap,
            "walk_forward_embargo_gap": self.config.embargo_gap,
            "walk_forward_min_fold_count": self.config.min_fold_count,
        }

    def to_dict(self) -> dict[str, object]:
        """Return value-free fold metadata using the canonical SplitWindow shape."""

        return {
            "config": self.config.to_dict(),
            "sample_count": self.sample_count,
            "fold_count": len(self.folds),
            "folds": [fold.to_dict() for fold in self.folds],
        }


def default_walk_forward_split_config(
    protocol: DiagnosticsHalfLifeProtocol | str = DiagnosticsHalfLifeProtocol.MEDIUM,
) -> WalkForwardSplitConfig:
    """Return the bounded default config for one half-life protocol."""

    normalized = coerce_half_life_protocol(protocol)
    defaults = _PROTOCOL_DEFAULTS[normalized]
    return WalkForwardSplitConfig(half_life_protocol=normalized, **defaults)


def coerce_walk_forward_split_config(
    value: WalkForwardSplitConfig | Mapping[str, Any] | None,
) -> WalkForwardSplitConfig | None:
    """Coerce an optional caller-supplied walk-forward config."""

    if value is None:
        return None
    if isinstance(value, WalkForwardSplitConfig):
        return value
    if isinstance(value, Mapping):
        return WalkForwardSplitConfig.from_mapping(value)
    raise WalkForwardSplitError(
        "walk_forward_config must be WalkForwardSplitConfig, mapping, or None"
    )


def coerce_half_life_protocol(
    value: DiagnosticsHalfLifeProtocol | str,
) -> DiagnosticsHalfLifeProtocol:
    """Coerce protocol names while accepting lower-case operator input."""

    if isinstance(value, DiagnosticsHalfLifeProtocol):
        return value
    if isinstance(value, str):
        text = value.strip()
        try:
            return DiagnosticsHalfLifeProtocol(text)
        except ValueError:
            try:
                return DiagnosticsHalfLifeProtocol[text.upper()]
            except KeyError as exc:
                allowed = ", ".join(protocol.value for protocol in DiagnosticsHalfLifeProtocol)
                raise WalkForwardSplitError(
                    f"unsupported half-life protocol {value!r}; expected one of {allowed}"
                ) from exc
    raise WalkForwardSplitError(
        f"half_life_protocol must be DiagnosticsHalfLifeProtocol or str, got {type(value).__name__}"
    )


def build_walk_forward_split_plan(
    sample_count: int,
    *,
    config: WalkForwardSplitConfig | Mapping[str, Any] | None = None,
    half_life_protocol: DiagnosticsHalfLifeProtocol | str = DiagnosticsHalfLifeProtocol.MEDIUM,
    train_window: int | None = None,
    validation_window: int | None = None,
    step_size: int | None = None,
    purge_gap: int | None = None,
    embargo_gap: int | None = None,
    min_fold_count: int | None = None,
) -> WalkForwardSplitPlan:
    """Build a purged/embargoed runtime walk-forward split plan.

    This function delegates split generation to
    :func:`alpha_system.experiments.splits.walk_forward_splits` and verifies the
    purge/embargo projection with :func:`apply_purge_embargo`.
    """

    resolved_config = _resolve_config(
        config=config,
        half_life_protocol=half_life_protocol,
        train_window=train_window,
        validation_window=validation_window,
        step_size=step_size,
        purge_gap=purge_gap,
        embargo_gap=embargo_gap,
        min_fold_count=min_fold_count,
    )
    total = _positive_int(sample_count, "sample_count")
    try:
        folds = walk_forward_splits(
            total,
            train_window=resolved_config.train_window,
            validation_window=resolved_config.validation_window,
            step_size=resolved_config.step_size,
            purge_gap=resolved_config.purge_gap,
            embargo_gap=resolved_config.embargo_gap,
        )
        for fold in folds:
            assert_chronological_split(fold)
            _assert_purge_embargo_projection(fold, resolved_config)
    except SplitError as exc:
        raise WalkForwardSplitError(f"walk-forward split failed closed: {exc}") from exc

    return WalkForwardSplitPlan(
        config=resolved_config,
        sample_count=total,
        folds=folds,
    )


def build_walk_forward_split_plan_for_observations(
    observations: Iterable[Mapping[str, Any]],
    *,
    config: WalkForwardSplitConfig | Mapping[str, Any] | None = None,
    half_life_protocol: DiagnosticsHalfLifeProtocol | str = DiagnosticsHalfLifeProtocol.MEDIUM,
    train_window: int | None = None,
    validation_window: int | None = None,
    step_size: int | None = None,
    purge_gap: int | None = None,
    embargo_gap: int | None = None,
    min_fold_count: int | None = None,
) -> WalkForwardSplitPlan:
    """Build a split plan from an already-resolved in-memory observation view."""

    cached = tuple(observations)
    return build_walk_forward_split_plan(
        len(cached),
        config=config,
        half_life_protocol=half_life_protocol,
        train_window=train_window,
        validation_window=validation_window,
        step_size=step_size,
        purge_gap=purge_gap,
        embargo_gap=embargo_gap,
        min_fold_count=min_fold_count,
    )


def _resolve_config(
    *,
    config: WalkForwardSplitConfig | Mapping[str, Any] | None,
    half_life_protocol: DiagnosticsHalfLifeProtocol | str,
    train_window: int | None,
    validation_window: int | None,
    step_size: int | None,
    purge_gap: int | None,
    embargo_gap: int | None,
    min_fold_count: int | None,
) -> WalkForwardSplitConfig:
    base = coerce_walk_forward_split_config(config)
    if base is None:
        base = default_walk_forward_split_config(half_life_protocol)
    overrides = {
        key: value
        for key, value in {
            "train_window": train_window,
            "validation_window": validation_window,
            "step_size": step_size,
            "purge_gap": purge_gap,
            "embargo_gap": embargo_gap,
            "min_fold_count": min_fold_count,
        }.items()
        if value is not None
    }
    if not overrides:
        return base
    return WalkForwardSplitConfig(
        half_life_protocol=base.half_life_protocol,
        train_window=overrides.get("train_window", base.train_window),
        validation_window=overrides.get("validation_window", base.validation_window),
        step_size=overrides.get("step_size", base.step_size),
        purge_gap=overrides.get("purge_gap", base.purge_gap),
        embargo_gap=overrides.get("embargo_gap", base.embargo_gap),
        min_fold_count=overrides.get("min_fold_count", base.min_fold_count),
    )


def _assert_purge_embargo_projection(
    fold: SplitWindow,
    config: WalkForwardSplitConfig,
) -> None:
    validation_start = min(fold.validation_indices)
    raw_train_start = validation_start - config.train_window
    if raw_train_start < 0:
        raise WalkForwardSplitError("walk-forward fold has invalid train/validation geometry")
    raw_train = tuple(range(raw_train_start, validation_start))
    expected = apply_purge_embargo(
        raw_train,
        fold.validation_indices,
        purge_gap=config.purge_gap,
        embargo_gap=config.embargo_gap,
    )
    if expected != fold.train_indices:
        raise WalkForwardSplitError("walk-forward fold failed purge/embargo projection check")


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise WalkForwardSplitError(f"{field} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise WalkForwardSplitError(f"{field} must be a positive integer") from exc
    if number <= 0:
        raise WalkForwardSplitError(f"{field} must be positive")
    return number


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise WalkForwardSplitError(f"{field} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise WalkForwardSplitError(f"{field} must be a non-negative integer") from exc
    if number < 0:
        raise WalkForwardSplitError(f"{field} must be non-negative")
    return number


__all__ = [
    "WalkForwardSplitConfig",
    "WalkForwardSplitError",
    "WalkForwardSplitPlan",
    "build_walk_forward_split_plan",
    "build_walk_forward_split_plan_for_observations",
    "coerce_half_life_protocol",
    "coerce_walk_forward_split_config",
    "default_walk_forward_split_config",
]
