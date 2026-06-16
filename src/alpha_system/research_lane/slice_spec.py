"""Bounded fast-probe slice descriptors.

This module is deliberately pure metadata: it validates the already-materialized
slice inputs that a fast exploratory probe may read, but it performs no I/O and
does not load values.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.sources import (
    DEFAULT_ALPHA_DATA_ROOT as _DEFAULT_ALPHA_DATA_ROOT_PATH,
)
from alpha_system.data.foundation.sources import resolve_alpha_data_root
from alpha_system.governance.idea_draft import (
    CONTEXT_NOT_EQUAL_TRIGGER,
    MAIN_EFFECT,
)
from alpha_system.governance.serialization import JsonValue

FAST_PROBE_SLICE_SCHEMA = "alpha_system.research_lane.fast_probe.slice_spec.v1"
# Single source of truth for the literal lives in data.foundation.sources; this
# module re-exports it as a string for its public surface / back-compat.
DEFAULT_ALPHA_DATA_ROOT = _DEFAULT_ALPHA_DATA_ROOT_PATH.as_posix()
ALLOWED_STUDY_KINDS = frozenset({MAIN_EFFECT, CONTEXT_NOT_EQUAL_TRIGGER})
ALLOWED_LABEL_VALUE_TYPES = frozenset({"bool", "float", "int"})


class SliceSpecError(ValueError):
    """Raised when a fast-probe slice descriptor is malformed."""


@dataclass(frozen=True, slots=True)
class SliceFeatureInput:
    """One materialized feature input for a bounded slice."""

    role: str
    factor_id: str
    factor_version: str
    relative_path: str | None = None
    pack_ref: str | None = None
    feature_request_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SliceFeatureInput:
        mapping = dict(payload)
        role = _text(mapping.get("role") or mapping.get("name"), "feature.role")
        factor_id = _text(mapping.get("factor_id"), "feature.factor_id")
        factor_version = _text(mapping.get("factor_version"), "feature.factor_version")
        relative_path = _optional_text(
            mapping.get("relative_path") or mapping.get("path") or mapping.get("parquet_path"),
            "feature.relative_path",
        )
        pack_ref = _optional_text(
            mapping.get("pack_ref")
            or mapping.get("feature_pack_ref")
            or mapping.get("feature_version_id"),
            "feature.pack_ref",
        )
        if relative_path is None and pack_ref is None:
            raise SliceSpecError("feature input must declare relative_path or pack_ref")
        return cls(
            role=role,
            factor_id=factor_id,
            factor_version=factor_version,
            relative_path=relative_path,
            pack_ref=pack_ref,
            feature_request_id=_optional_text(
                mapping.get("feature_request_id"),
                "feature.feature_request_id",
            ),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "role": self.role,
            "factor_id": self.factor_id,
            "factor_version": self.factor_version,
            "relative_path": self.relative_path,
            "pack_ref": self.pack_ref,
            "feature_request_id": self.feature_request_id,
        }


@dataclass(frozen=True, slots=True)
class SliceLabelInput:
    """One materialized label or path-label input for a bounded slice."""

    role: str
    label_id: str
    relative_path: str | None = None
    pack_ref: str | None = None
    label_spec_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SliceLabelInput:
        mapping = dict(payload)
        role = _text(mapping.get("role") or mapping.get("name"), "label.role")
        label_id = _text(
            mapping.get("label_id")
            or mapping.get("path_label")
            or mapping.get("label_spec_id"),
            "label.label_id",
        )
        relative_path = _optional_text(
            mapping.get("relative_path") or mapping.get("path") or mapping.get("parquet_path"),
            "label.relative_path",
        )
        pack_ref = _optional_text(
            mapping.get("pack_ref")
            or mapping.get("label_pack_ref")
            or mapping.get("label_version_id"),
            "label.pack_ref",
        )
        if relative_path is None and pack_ref is None:
            raise SliceSpecError("label input must declare relative_path or pack_ref")
        return cls(
            role=role,
            label_id=label_id,
            relative_path=relative_path,
            pack_ref=pack_ref,
            label_spec_id=_optional_text(mapping.get("label_spec_id"), "label.label_spec_id"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "role": self.role,
            "label_id": self.label_id,
            "relative_path": self.relative_path,
            "pack_ref": self.pack_ref,
            "label_spec_id": self.label_spec_id,
        }


@dataclass(frozen=True, slots=True)
class LabelVersionBinding:
    """Mapping from materialized label version id to probe label field semantics."""

    label_version_id: str
    label_type: str
    value_type: str

    @classmethod
    def from_pair(
        cls,
        version_id: str,
        payload: Mapping[str, Any] | Sequence[Any],
    ) -> LabelVersionBinding:
        if isinstance(payload, Mapping):
            label_type = _text(payload.get("label_type") or payload.get("type"), "label_type")
            value_type = _text(
                payload.get("value_type") or payload.get("cast") or payload.get("dtype"),
                "value_type",
            )
        elif isinstance(payload, Sequence) and not isinstance(payload, str | bytes):
            if len(payload) != 2:
                raise SliceSpecError("label version tuple bindings must have two values")
            label_type = _text(payload[0], "label_type")
            value_type = _text(payload[1], "value_type")
        else:
            raise SliceSpecError("label version binding must be a mapping or two-item sequence")
        if value_type not in ALLOWED_LABEL_VALUE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_LABEL_VALUE_TYPES))
            raise SliceSpecError(f"label version value_type must be one of: {allowed}")
        return cls(
            label_version_id=_text(version_id, "label_version_id"),
            label_type=label_type,
            value_type=value_type,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "label_type": self.label_type,
            "value_type": self.value_type,
        }


@dataclass(frozen=True, slots=True)
class SliceSpec:
    """Immutable descriptor for one already-materialized fast-probe slice."""

    slice_id: str
    study_kind: str
    dataset_version_id: str
    partition_id: str
    instrument_id: str
    session_id: str
    data_version: str
    feature_inputs: tuple[SliceFeatureInput, ...]
    label_inputs: tuple[SliceLabelInput, ...]
    label_version_bindings: tuple[LabelVersionBinding, ...] = ()
    data_root: str | None = None
    materialized_label_version: str | None = None
    horizon_seconds: int | None = None
    required_future_bars: int | None = None
    surrogate_run_count: int = 1
    surrogate_base_seed: int = 0
    family_id: str | None = None
    family_budget: int | None = None
    variant_id: str | None = None
    outcome_label_type: str | None = None
    created_at: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SliceSpec:
        """Build and validate a bounded fast-probe slice descriptor."""

        mapping = dict(payload)
        study_kind = _text(mapping.get("study_kind"), "study_kind")
        if study_kind not in ALLOWED_STUDY_KINDS:
            allowed = ", ".join(sorted(ALLOWED_STUDY_KINDS))
            raise SliceSpecError(f"study_kind must be one of: {allowed}")
        feature_inputs = _feature_inputs(mapping.get("feature_inputs") or mapping.get("features"))
        label_inputs = _label_inputs(mapping.get("label_inputs") or mapping.get("labels"))
        label_versions = _label_version_bindings(
            mapping.get("label_version_map")
            or mapping.get("label_versions")
            or mapping.get("path_label_versions")
            or {}
        )
        surrogate_run_count = _positive_int(
            mapping.get("surrogate_run_count", mapping.get("surrogate_runs", 1)),
            "surrogate_run_count",
        )
        surrogate_base_seed = _non_negative_int(
            mapping.get("surrogate_base_seed", mapping.get("base_seed", 0)),
            "surrogate_base_seed",
        )
        return cls(
            slice_id=_text(mapping.get("slice_id") or mapping.get("id"), "slice_id"),
            study_kind=study_kind,
            dataset_version_id=_text(mapping.get("dataset_version_id"), "dataset_version_id"),
            partition_id=_text(
                mapping.get("partition_id") or mapping.get("partition"),
                "partition_id",
            ),
            instrument_id=_text(mapping.get("instrument_id"), "instrument_id"),
            session_id=_text(mapping.get("session_id"), "session_id"),
            data_version=_text(
                mapping.get("data_version") or mapping.get("dataset_version_id"),
                "data_version",
            ),
            feature_inputs=feature_inputs,
            label_inputs=label_inputs,
            label_version_bindings=label_versions,
            data_root=_optional_text(
                mapping.get("data_root") or mapping.get("alpha_data_root"),
                "data_root",
            ),
            materialized_label_version=_optional_text(
                mapping.get("materialized_label_version") or mapping.get("label_version"),
                "materialized_label_version",
            ),
            horizon_seconds=_optional_int(
                mapping.get("horizon_seconds"),
                "horizon_seconds",
            ),
            required_future_bars=_optional_int(
                mapping.get("required_future_bars"),
                "required_future_bars",
            ),
            surrogate_run_count=surrogate_run_count,
            surrogate_base_seed=surrogate_base_seed,
            family_id=_optional_text(mapping.get("family_id"), "family_id"),
            family_budget=_optional_int(mapping.get("family_budget"), "family_budget"),
            variant_id=_optional_text(mapping.get("variant_id"), "variant_id"),
            outcome_label_type=_optional_text(
                mapping.get("outcome_label_type"),
                "outcome_label_type",
            ),
            created_at=_optional_text(mapping.get("created_at"), "created_at"),
        )

    @classmethod
    def from_idea_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        slice_id: str | None = None,
    ) -> SliceSpec:
        """Extract a fast-probe slice descriptor from an idea payload."""

        selected = _select_slice_payload(payload, slice_id=slice_id)
        if selected is None:
            if slice_id:
                raise SliceSpecError(f"slice {slice_id!r} was not found in idea payload")
            raise SliceSpecError("idea payload does not contain a fast-probe slice descriptor")
        return cls.from_mapping(selected)

    @property
    def feature_pack_refs(self) -> tuple[str, ...]:
        return tuple(item.pack_ref for item in self.feature_inputs if item.pack_ref is not None)

    @property
    def label_pack_refs(self) -> tuple[str, ...]:
        return tuple(item.pack_ref for item in self.label_inputs if item.pack_ref is not None)

    @property
    def feature_request_ids(self) -> tuple[str, ...]:
        return tuple(
            item.feature_request_id
            for item in self.feature_inputs
            if item.feature_request_id is not None
        )

    @property
    def label_spec_ids(self) -> tuple[str, ...]:
        return tuple(
            item.label_spec_id for item in self.label_inputs if item.label_spec_id is not None
        )

    @property
    def label_version_map(self) -> dict[str, LabelVersionBinding]:
        return {binding.label_version_id: binding for binding in self.label_version_bindings}

    def resolve_data_root(self, env: Mapping[str, str] | None = None) -> Path:
        """Resolve the local data root path without checking the filesystem.

        Order is env (ALPHA_DATA_ROOT) -> this slice's ``data_root`` -> the
        canonical default. The env tier wins first (so an explicit
        ``ALPHA_DATA_ROOT`` overrides a slice-pinned root); the canonical
        default literal is owned by ``data.foundation.sources``.
        """

        active_env = os.environ if env is None else env
        env_value = _optional_text(active_env.get("ALPHA_DATA_ROOT"), "ALPHA_DATA_ROOT")
        # env wins; otherwise prefer this slice's pinned root over the default.
        explicit = env_value or self.data_root
        return resolve_alpha_data_root(explicit=explicit, env=active_env)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema": FAST_PROBE_SLICE_SCHEMA,
            "slice_id": self.slice_id,
            "study_kind": self.study_kind,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "instrument_id": self.instrument_id,
            "session_id": self.session_id,
            "data_version": self.data_version,
            "feature_inputs": [item.to_dict() for item in self.feature_inputs],
            "label_inputs": [item.to_dict() for item in self.label_inputs],
            "label_version_map": {
                binding.label_version_id: binding.to_dict()
                for binding in self.label_version_bindings
            },
            "data_root": self.data_root,
            "materialized_label_version": self.materialized_label_version,
            "horizon_seconds": self.horizon_seconds,
            "required_future_bars": self.required_future_bars,
            "surrogate_run_count": self.surrogate_run_count,
            "surrogate_base_seed": self.surrogate_base_seed,
            "family_id": self.family_id,
            "family_budget": self.family_budget,
            "variant_id": self.variant_id,
            "outcome_label_type": self.outcome_label_type,
            "created_at": self.created_at,
        }


def from_idea_payload(
    payload: Mapping[str, Any],
    *,
    slice_id: str | None = None,
) -> SliceSpec:
    """Convenience wrapper for `SliceSpec.from_idea_payload`."""

    return SliceSpec.from_idea_payload(payload, slice_id=slice_id)


def _select_slice_payload(
    payload: Mapping[str, Any],
    *,
    slice_id: str | None,
) -> Mapping[str, Any] | None:
    direct = (
        payload.get("slice_spec")
        or payload.get("fast_probe_slice")
        or payload.get("fast_probe_slice_spec")
        or payload.get("slice")
    )
    if isinstance(direct, Mapping):
        if slice_id is None or str(direct.get("slice_id") or direct.get("id")) == slice_id:
            return direct
    if "slice_id" in payload and (slice_id is None or str(payload.get("slice_id")) == slice_id):
        return payload
    slices = payload.get("slices") or payload.get("slice_specs")
    if isinstance(slices, Mapping):
        if slice_id is None and len(slices) == 1:
            value = next(iter(slices.values()))
            return value if isinstance(value, Mapping) else None
        value = slices.get(slice_id or "")
        return value if isinstance(value, Mapping) else None
    if isinstance(slices, Sequence) and not isinstance(slices, str | bytes):
        for value in slices:
            if not isinstance(value, Mapping):
                continue
            candidate_id = str(value.get("slice_id") or value.get("id"))
            if slice_id is None or candidate_id == slice_id:
                return value
    return None


def _feature_inputs(value: Any) -> tuple[SliceFeatureInput, ...]:
    rows = _mapping_sequence(value, "feature_inputs")
    if not rows:
        raise SliceSpecError("feature_inputs must contain at least one feature input")
    return tuple(SliceFeatureInput.from_mapping(row) for row in rows)


def _label_inputs(value: Any) -> tuple[SliceLabelInput, ...]:
    rows = _mapping_sequence(value, "label_inputs")
    if not rows:
        raise SliceSpecError("label_inputs must contain at least one label input")
    return tuple(SliceLabelInput.from_mapping(row) for row in rows)


def _label_version_bindings(value: Any) -> tuple[LabelVersionBinding, ...]:
    if value in (None, {}):
        return ()
    if not isinstance(value, Mapping):
        raise SliceSpecError("label_version_map must be a mapping")
    return tuple(
        LabelVersionBinding.from_pair(str(version_id), binding)
        for version_id, binding in sorted(value.items(), key=lambda item: str(item[0]))
    )


def _mapping_sequence(value: Any, field: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        raise SliceSpecError(f"{field} must be a sequence of mappings")
    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise SliceSpecError(f"{field}[{index}] must be a mapping")
        rows.append(item)
    return tuple(rows)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SliceSpecError(f"{field} must be non-empty text")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _optional_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    return _int(value, field)


def _positive_int(value: Any, field: str) -> int:
    number = _int(value, field)
    if number <= 0:
        raise SliceSpecError(f"{field} must be positive")
    return number


def _non_negative_int(value: Any, field: str) -> int:
    number = _int(value, field)
    if number < 0:
        raise SliceSpecError(f"{field} must be non-negative")
    return number


def _int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise SliceSpecError(f"{field} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SliceSpecError(f"{field} must be an integer") from exc


__all__ = [
    "DEFAULT_ALPHA_DATA_ROOT",
    "FAST_PROBE_SLICE_SCHEMA",
    "LabelVersionBinding",
    "SliceFeatureInput",
    "SliceLabelInput",
    "SliceSpec",
    "SliceSpecError",
    "from_idea_payload",
]
