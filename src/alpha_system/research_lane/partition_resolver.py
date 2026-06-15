"""Cross-partition SliceSpec resolution for OOS fan-out (PARTITION_RESOLVER_V0).

An idea declares its slice for the partition it was authored against (e.g.
``ES_2020_120m``). To mine that idea across other partitions (cross-year /
cross-instrument OOS), the driver needs a COMPLETE ``SliceSpec`` for each TARGET
partition -- one whose feature/label pack refs point at the *target* partition's
materialized versions, not the declared partition's.

The decisive resolution fact (see ``runtime/input_resolver.FeatureLabelPackResolver``):
``fast_probe`` resolves a feature/label pack **by its deterministic version-id
hash** (``fver_...`` / ``lver_...``) against the local registry, then asserts the
resolved record's ``dataset_version_id`` and ``partition_id`` match what the
SliceSpec declares. So fanning ES_2020 -> ES_2021 cannot copy ES_2020's hashes:
it must discover the ES_2021 materialized ``feature_version_id`` /
``label_version_id`` for the SAME factor identity.

This module resolves, per target partition, the REGISTERED materialized version
for each factor role -- by ``(feature_id, partition_id)`` for features and
``(label_id, partition_id)`` for path labels -- and synthesizes a complete
``SliceSpec`` carrying the target partition's resolved versions + dataset_version
+ partition_id. It REUSES the idea's declared slice purely as a TEMPLATE for the
factor roles, study_kind, session, horizon, surrogate config, and outcome type.

FAIL CLOSED: if a required factor/label is not materialized (REGISTERED) for the
target partition -- or if more than one REGISTERED candidate matches the factor
identity at that partition -- resolution raises a typed
``PartitionResolutionError`` so the driver records an honest DATA_GAP. It NEVER
falls back to a different partition's data and NEVER fabricates a version id.

Partition convention: ``<INSTRUMENT>_<YEAR>_<horizon>`` (e.g. ``ES_2021_120m``).
Features are partitioned horizon-AGNOSTICALLY as ``<INSTRUMENT>_<YEAR>_full_year``
(features are computed once per (instrument, year) at the base bar grid and serve
every label horizon; the join stays no-lookahead on event_ts/available_ts). Path
labels are partitioned horizon-SPECIFICALLY as ``<INSTRUMENT>_<YEAR>_<horizon>``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.research_lane.slice_spec import (
    SliceSpec,
    SliceSpecError,
    _select_slice_payload,
)

# Partition id convention shared with tools/frontier/data_inventory.py.
_PARTITION_RE = re.compile(
    r"^(?P<instrument>[A-Za-z0-9]+)_(?P<year>\d{4})_(?P<horizon>.+)$"
)

# Features materialize once per (instrument, year) at the base bar grid; this is
# the horizon-agnostic partition the feature registry records carry.
_FEATURE_HORIZON = "full_year"


class PartitionResolutionError(ValueError):
    """Fail-closed: a target partition could not be resolved to materialized data.

    Carries a machine-stable ``code`` so the driver can record an honest DATA_GAP
    reason without string-spelunking the message.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class TargetPartition:
    """A parsed target partition identity for one OOS fan-out member."""

    instrument: str
    year: int
    horizon: str

    @property
    def slice_id(self) -> str:
        return f"{self.instrument}_{self.year}_{self.horizon}"

    @property
    def label_partition_id(self) -> str:
        """Horizon-specific partition the path label registry records carry."""

        return self.slice_id

    @property
    def feature_partition_id(self) -> str:
        """Horizon-agnostic partition the feature registry records carry."""

        return f"{self.instrument}_{self.year}_{_FEATURE_HORIZON}"

    @classmethod
    def from_slice_id(cls, slice_id: str) -> TargetPartition:
        match = _PARTITION_RE.match(str(slice_id).strip())
        if match is None:
            raise PartitionResolutionError(
                "malformed_target_partition",
                f"target partition {slice_id!r} is not <INSTRUMENT>_<YEAR>_<horizon>",
            )
        return cls(
            instrument=match.group("instrument"),
            year=int(match.group("year")),
            horizon=match.group("horizon"),
        )

    @classmethod
    def from_fields(cls, *, instrument: str, year: int, horizon: str) -> TargetPartition:
        instrument = str(instrument).strip()
        horizon = str(horizon).strip()
        if not instrument or not horizon:
            raise PartitionResolutionError(
                "malformed_target_partition",
                "target partition requires non-empty instrument and horizon",
            )
        return cls(instrument=instrument, year=int(year), horizon=horizon)

    @classmethod
    def coerce(cls, target: Any) -> TargetPartition:
        if isinstance(target, TargetPartition):
            return target
        if isinstance(target, str):
            return cls.from_slice_id(target)
        if isinstance(target, Mapping):
            slice_id = target.get("slice_id") or target.get("partition_id")
            if slice_id:
                return cls.from_slice_id(str(slice_id))
            return cls.from_fields(
                instrument=str(target["instrument"]),
                year=int(target["year"]),
                horizon=str(target["horizon"]),
            )
        raise PartitionResolutionError(
            "malformed_target_partition",
            f"unsupported target partition spec: {type(target).__name__}",
        )


class _RegistryIndex:
    """In-memory (factor identity, partition) -> REGISTERED record index.

    Built once from the registries' public REGISTERED-record read methods and
    reused across every target partition in a fan-out, so the SQLite registries
    are read at most once per fan-out batch rather than once per partition.
    """

    def __init__(
        self,
        *,
        alpha_data_root: str | Path | None,
        env: Mapping[str, str] | None,
        feature_store: object | None = None,
        label_registry: object | None = None,
    ) -> None:
        self._alpha_data_root = alpha_data_root
        self._env = env
        self._feature_store = feature_store
        self._label_registry = label_registry
        self._feature_index: dict[tuple[str, str], list[Any]] | None = None
        self._label_index: dict[tuple[str, str], list[Any]] | None = None

    def _build_feature_index(self) -> dict[tuple[str, str], list[Any]]:
        if self._feature_index is not None:
            return self._feature_index
        store = self._feature_store
        if store is None:
            from alpha_system.features.store import FeatureStore

            store = FeatureStore.from_alpha_data_root(
                self._alpha_data_root, env=self._env
            )
        registry = getattr(store, "registry", store)
        records = registry.read_registered_parquet_features()
        index: dict[tuple[str, str], list[Any]] = {}
        for record in records:
            feature_id = record.feature_spec.feature_id
            key = (feature_id, record.partition_id)
            index.setdefault(key, []).append(record)
        self._feature_index = index
        return index

    def _build_label_index(self) -> dict[tuple[str, str], list[Any]]:
        if self._label_index is not None:
            return self._label_index
        registry = self._label_registry
        if registry is None:
            from alpha_system.labels.registry import LabelRegistry

            registry = LabelRegistry.from_alpha_data_root(
                self._alpha_data_root, env=self._env
            )
        index: dict[tuple[str, str], list[Any]] = {}
        for record in registry.read_label_records():
            state = getattr(record, "lifecycle_state", None)
            if getattr(state, "value", state) != "REGISTERED":
                continue
            if getattr(record, "parquet_path", None) is None:
                continue
            key = (record.label_id, record.partition_id)
            index.setdefault(key, []).append(record)
        self._label_index = index
        return index

    def resolve_feature(self, feature_id: str, partition_id: str) -> Any:
        return _unique(
            self._build_feature_index().get((feature_id, partition_id), []),
            kind="feature",
            factor_id=feature_id,
            partition_id=partition_id,
        )

    def resolve_label(self, label_id: str, partition_id: str) -> Any:
        return _unique(
            self._build_label_index().get((label_id, partition_id), []),
            kind="label",
            factor_id=label_id,
            partition_id=partition_id,
        )


def _unique(candidates: Sequence[Any], *, kind: str, factor_id: str, partition_id: str) -> Any:
    if not candidates:
        raise PartitionResolutionError(
            f"{kind}_not_materialized_for_partition",
            (
                f"no REGISTERED {kind} materialized for "
                f"{factor_id!r} at partition {partition_id!r}"
            ),
        )
    if len(candidates) > 1:
        raise PartitionResolutionError(
            f"ambiguous_{kind}_for_partition",
            (
                f"{len(candidates)} REGISTERED {kind} candidates for "
                f"{factor_id!r} at partition {partition_id!r}; refusing to guess"
            ),
        )
    return candidates[0]


def _relative_path(parquet_path: str, root: Path) -> str:
    absolute = Path(parquet_path)
    try:
        return absolute.relative_to(root).as_posix()
    except ValueError:
        # Path is outside the resolved root; keep absolute so the loader still
        # resolves it (fast_probe joins root / relative_path only when relative).
        return absolute.as_posix()


def _template_slice_payload(
    idea_payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    """The idea's declared slice, used purely as the role/config template."""

    template = _select_slice_payload(idea_payload, slice_id=None)
    if template is None:
        raise PartitionResolutionError(
            "idea_declares_no_slice_template",
            "idea payload declares no slice to use as a resolution template",
        )
    return template


def _retarget_session(session_id: str | None, target: TargetPartition) -> str:
    """Retarget an ``<INSTR>:<SESSION>`` session id to the target instrument."""

    if not session_id:
        return f"{target.instrument}:RTH"
    if ":" in session_id:
        _, _, suffix = session_id.partition(":")
        return f"{target.instrument}:{suffix}"
    return session_id


def resolve_partition_slice(
    idea_payload: Mapping[str, Any],
    *,
    target_partition: Any,
    env: Mapping[str, str] | None = None,
    alpha_data_root: str | Path | None = None,
    feature_store: object | None = None,
    label_registry: object | None = None,
    _index: _RegistryIndex | None = None,
) -> SliceSpec:
    """Synthesize a complete ``SliceSpec`` for ``target_partition``.

    Resolves each declared factor role to the target partition's REGISTERED
    materialized version and builds a SliceSpec whose pack refs, dataset_version,
    and partition_id all describe the TARGET partition. Fails closed
    (``PartitionResolutionError``) if any required factor/label is not
    materialized for the target -- never falls back to another partition.
    """

    target = TargetPartition.coerce(target_partition)
    template = _template_slice_payload(idea_payload)

    # The data root the resolved relative_paths are taken relative to. fast_probe
    # resolves the root from ALPHA_DATA_ROOT / data_root at probe time; mirror that
    # here so the synthesized relative_path lines up with the loader.
    template_spec = SliceSpec.from_mapping(template)
    root = template_spec.resolve_data_root(env=env)
    if alpha_data_root is None:
        alpha_data_root = str(root)

    index = _index or _RegistryIndex(
        alpha_data_root=alpha_data_root,
        env=env,
        feature_store=feature_store,
        label_registry=label_registry,
    )

    # --- path labels (horizon-specific partition) ---------------------------
    # Resolve labels first so the target dataset_version_id is known before the
    # feature dataset-version cross-check below.
    label_inputs: list[dict[str, Any]] = []
    label_version_map: dict[str, list[str]] = {}
    target_dsv: str | None = None
    template_bindings = template_spec.label_version_map
    # Carry the binding SEMANTICS (mfe_by_horizon/mae_by_horizon, value_type) of
    # each declared label onto the resolved target label_version_id, keyed by the
    # declaring label's label_id (NOT role: net_excursion declares two path labels
    # path_mfe/path_mae that share role "path" but carry distinct mfe/mae bindings).
    declared_binding_by_label_id: dict[str, tuple[str, str]] = {}
    for declared_label in template_spec.label_inputs:
        binding = template_bindings.get(declared_label.pack_ref or "")
        if binding is not None:
            declared_binding_by_label_id[declared_label.label_id] = (
                binding.label_type,
                binding.value_type,
            )

    for label in template_spec.label_inputs:
        record = index.resolve_label(label.label_id, target.label_partition_id)
        if record.parquet_path is None:
            raise PartitionResolutionError(
                "label_not_materialized_for_partition",
                (
                    f"REGISTERED label {label.label_id!r} at "
                    f"{target.label_partition_id!r} has no parquet value store"
                ),
            )
        record_dsv = record.dataset_version_id
        if target_dsv is None:
            target_dsv = record_dsv
        elif target_dsv != record_dsv:
            raise PartitionResolutionError(
                "inconsistent_target_dataset_version",
                (
                    f"target partition {target.slice_id!r} resolved to multiple "
                    f"dataset_version_ids ({target_dsv!r} vs {record_dsv!r}); "
                    "refusing to synthesize a mixed-dataset slice"
                ),
            )
        resolved_lver = record.label_version_id
        label_inputs.append(
            {
                "role": label.role,
                "label_id": label.label_id,
                "relative_path": _relative_path(record.parquet_path, root),
                "pack_ref": resolved_lver,
                "label_spec_id": record.label_spec_id,
            }
        )
        binding = declared_binding_by_label_id.get(label.label_id)
        if binding is not None:
            label_version_map[resolved_lver] = [binding[0], binding[1]]

    if target_dsv is None:
        raise PartitionResolutionError(
            "target_has_no_path_label",
            f"target partition {target.slice_id!r} resolved no path label",
        )

    # --- features (horizon-agnostic full_year partition) --------------------
    feature_inputs: list[dict[str, Any]] = []
    for feature in template_spec.feature_inputs:
        record = index.resolve_feature(feature.factor_id, target.feature_partition_id)
        if record.parquet_path is None:
            raise PartitionResolutionError(
                "feature_not_materialized_for_partition",
                (
                    f"REGISTERED feature {feature.factor_id!r} at "
                    f"{target.feature_partition_id!r} has no parquet value store"
                ),
            )
        # A feature pack bound to a DIFFERENT DatasetVersion than the labels would
        # be rejected by the runtime resolver -- fail closed here with a clear reason.
        if record.dataset_version_id != target_dsv:
            raise PartitionResolutionError(
                "feature_label_dataset_version_mismatch",
                (
                    f"feature {feature.factor_id!r} at {target.feature_partition_id!r} "
                    f"is bound to {record.dataset_version_id!r} but the target labels "
                    f"are bound to {target_dsv!r}; refusing a mixed-dataset slice"
                ),
            )
        feature_inputs.append(
            {
                "role": feature.role,
                "factor_id": feature.factor_id,
                # Keep the TEMPLATE factor_version verbatim: it is an opaque join
                # key that must stay consistent between the slice's feature rows
                # and the (unchanged) SetupSpec context/trigger predicates. Data
                # resolution is by ``pack_ref`` (the target version-id hash), never
                # by this descriptor, so the target's data is loaded correctly.
                "factor_version": feature.factor_version,
                "relative_path": _relative_path(record.parquet_path, root),
                "pack_ref": record.feature_version_id,
                "feature_request_id": record.feature_request_id,
            }
        )

    label_spec_ids = sorted(
        {str(item["label_spec_id"]) for item in label_inputs if item["label_spec_id"]}
    )
    synthesized: dict[str, Any] = {
        "slice_id": target.slice_id,
        "study_kind": template_spec.study_kind,
        "dataset_version_id": target_dsv,
        "data_version": target_dsv,
        "partition_id": target.slice_id,
        "instrument_id": target.instrument,
        "session_id": _retarget_session(template_spec.session_id, target),
        "feature_inputs": feature_inputs,
        "label_inputs": label_inputs,
        "label_version_map": label_version_map,
        "label_spec_ids": label_spec_ids,
        "data_root": template_spec.data_root,
        "materialized_label_version": label_inputs[0]["pack_ref"],
        "horizon_seconds": template_spec.horizon_seconds,
        "required_future_bars": template_spec.required_future_bars,
        "surrogate_run_count": template_spec.surrogate_run_count,
        "surrogate_base_seed": template_spec.surrogate_base_seed,
        "family_id": template_spec.family_id,
        "family_budget": template_spec.family_budget,
        "variant_id": template_spec.variant_id,
        "outcome_label_type": template_spec.outcome_label_type,
        "created_at": template_spec.created_at,
    }
    try:
        return SliceSpec.from_mapping(synthesized)
    except SliceSpecError as exc:  # pragma: no cover - defensive
        raise PartitionResolutionError(
            "synthesized_slice_invalid",
            f"synthesized SliceSpec for {target.slice_id!r} is invalid: {exc}",
        ) from exc


def resolve_partition_setup(setup_spec: Any, target_slice: SliceSpec) -> Any:
    """Retarget a SetupSpec's ``path_label`` to ``target_slice``'s label spec.

    The path-label outcome binding in the conditional probe matches
    ``SetupSpec.path_label`` against each materialized label row's spec id /
    label_id (see ``research/conditional_probe._label_bound_to_path``). A label
    spec is content-hashed per ``(instrument, year, horizon)``, so the declared
    ES_2020 ``path_label`` (``lspec_...``) will not bind ES_2021's labels. This
    clones the SetupSpec with the TARGET partition's resolved label spec id so the
    SAME setup shape binds the target partition's labels, then re-validates +
    re-derives the deterministic ``setup_spec_id``.

    The context/trigger ``factor_version`` predicates are left UNCHANGED: the
    resolver keeps the slice's feature ``factor_version`` equal to the template,
    so the predicate/slice join key already agrees on the target partition. Only
    the path_label (a per-partition content hash) needs retargeting.

    Returns the input unchanged when it is ``None`` or already bound to the target
    label spec.
    """

    if setup_spec is None:
        return None
    target_label_spec_id = _setup_target_label_spec_id(target_slice)
    if target_label_spec_id is None:
        return setup_spec
    payload = dict(setup_spec.to_dict())
    if payload.get("path_label") == target_label_spec_id:
        return setup_spec
    payload["path_label"] = target_label_spec_id

    from alpha_system.governance.setup_spec import (
        SetupSpec,
        generate_setup_spec_id,
    )

    payload["setup_spec_id"] = generate_setup_spec_id(payload)
    return SetupSpec.from_mapping(payload)


def _setup_target_label_spec_id(target_slice: SliceSpec) -> str | None:
    """The single path-label spec id the target slice's path labels resolve to."""

    spec_ids = {
        label.label_spec_id
        for label in target_slice.label_inputs
        if label.label_spec_id
    }
    if len(spec_ids) == 1:
        return next(iter(spec_ids))
    # Zero or mixed spec ids: leave the setup unchanged and let the probe's own
    # binding/validation decide (fail-closed in the probe, never fabricated here).
    return None


def resolve_partition_slices(
    idea_payload: Mapping[str, Any],
    targets: Sequence[Any],
    *,
    env: Mapping[str, str] | None = None,
    alpha_data_root: str | Path | None = None,
    feature_store: object | None = None,
    label_registry: object | None = None,
) -> list[SliceSpec]:
    """Resolve a batch of target partitions, sharing one registry index.

    Each target is resolved independently; a per-target failure raises
    ``PartitionResolutionError`` for THAT target. Callers that want the
    coverage-honest "record DATA_GAP and keep going" behaviour should catch the
    typed error per target (the mining driver does exactly this).
    """

    template = _template_slice_payload(idea_payload)
    root = SliceSpec.from_mapping(template).resolve_data_root(env=env)
    resolved_root = str(root) if alpha_data_root is None else alpha_data_root
    index = _RegistryIndex(
        alpha_data_root=resolved_root,
        env=env,
        feature_store=feature_store,
        label_registry=label_registry,
    )
    return [
        resolve_partition_slice(
            idea_payload,
            target_partition=target,
            env=env,
            alpha_data_root=resolved_root,
            _index=index,
        )
        for target in targets
    ]


__all__ = [
    "PartitionResolutionError",
    "TargetPartition",
    "resolve_partition_setup",
    "resolve_partition_slice",
    "resolve_partition_slices",
]
