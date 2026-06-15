"""Generic fast exploratory probe bridge over already-materialized slices."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.core.value_store import load_parquet_values
from alpha_system.data.storage import DataDependencyError
from alpha_system.governance.idea_draft import CONTEXT_NOT_EQUAL_TRIGGER, MAIN_EFFECT
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MechanismCard,
    validate_mechanism_card,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec, validate_setup_spec
from alpha_system.governance.surrogate_run import ZERO_PASS_MET
from alpha_system.research.conditional_probe import (
    ConditionalProbeError,
    build_path_label_observation_set,
    build_surrogate_zero_pass_gate,
    compile_setup_spec_to_conditional_probe,
    evaluate_setup_conditional_probe,
)
from alpha_system.research.events import target_before_stop_probability
from alpha_system.research_lane.slice_spec import (
    SliceFeatureInput,
    SliceLabelInput,
    SliceSpec,
    SliceSpecError,
)
from alpha_system.runtime.diagnostics.factor.runtime import build_factor_diagnostics_run
from alpha_system.runtime.diagnostics.power import build_ic_power_statement
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

FAST_PROBE_SCHEMA = "alpha_system.research_lane.fast_probe.v1"


class FastProbeError(ValueError):
    """Raised when fast-probe inputs are malformed."""


@dataclass(frozen=True, slots=True)
class ResolvedSliceHandles:
    """Value-free resolver output for the requested bounded slice."""

    feature_handles: tuple[Mapping[str, object], ...]
    label_handles: tuple[Mapping[str, object], ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "feature_handles": [dict(handle) for handle in self.feature_handles],
            "label_handles": [dict(handle) for handle in self.label_handles],
        }


@dataclass(frozen=True, slots=True)
class InjectedRows:
    """Mapped in-memory rows for the unchanged probe engines."""

    feature_rows_by_role: Mapping[str, tuple[dict[str, Any], ...]]
    label_rows_by_role: Mapping[str, tuple[dict[str, Any], ...]]

    def row_counts(self) -> dict[str, JsonValue]:
        return {
            "feature_rows": {
                role: len(rows) for role, rows in sorted(self.feature_rows_by_role.items())
            },
            "label_rows": {
                role: len(rows) for role, rows in sorted(self.label_rows_by_role.items())
            },
        }


def fast_probe(
    card: MechanismCard | Mapping[str, Any],
    setup: SetupSpec | Mapping[str, Any] | None,
    slice_spec: SliceSpec | Mapping[str, Any],
    *,
    resolver: FeatureLabelPackResolver | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, JsonValue]:
    """Load one bounded existing slice and run the configured exploratory probe."""

    active_card = _coerce_card(card)
    active_slice = _coerce_slice(slice_spec)
    root = active_slice.resolve_data_root(env=env)
    active_setup = _coerce_setup(setup) if setup is not None else None

    if not root.exists():
        return build_fast_probe_data_gap(
            active_card,
            active_setup,
            active_slice,
            reason=f"ALPHA_DATA_ROOT/data root does not resolve: {root}",
        )
    try:
        active_resolver = resolver or FeatureLabelPackResolver(alpha_data_root=root, env=env)
        handles = _resolve_slice_handles(active_slice, active_resolver)
        injected = _load_injected_rows(root, active_slice)
        _require_non_empty_rows(injected)
    except _DATA_GAP_EXCEPTIONS as exc:
        return build_fast_probe_data_gap(
            active_card,
            active_setup,
            active_slice,
            reason=f"bounded slice rows could not be resolved via sanctioned loader: {exc}",
        )

    if active_slice.study_kind == MAIN_EFFECT:
        return _run_main_effect(
            active_card,
            active_slice,
            injected,
            handles=handles,
        )
    if active_slice.study_kind == CONTEXT_NOT_EQUAL_TRIGGER:
        if active_setup is None:
            raise FastProbeError("setup is required for context_not_equal_trigger fast probes")
        return _run_context_not_equal_trigger(
            active_card,
            active_setup,
            active_slice,
            injected,
            handles=handles,
        )
    raise FastProbeError(f"unsupported study_kind: {active_slice.study_kind}")


def build_fast_probe_data_gap(
    card: MechanismCard | Mapping[str, Any],
    setup: SetupSpec | Mapping[str, Any] | None,
    slice_spec: SliceSpec | Mapping[str, Any],
    *,
    reason: str,
) -> dict[str, JsonValue]:
    """Build an honest DATA_GAP readout without fabricated values."""

    active_card = _coerce_card(card)
    active_slice = _coerce_slice(slice_spec)
    active_setup = _coerce_setup(setup) if setup is not None else None
    factor_id, factor_version = _power_factor(active_slice, active_setup)
    gate = build_surrogate_zero_pass_gate(run_count=0, gate_pass_count=0, error_count=0)
    power = build_ic_power_statement(
        n_eff=0,
        scope="per_factor",
        factor_id=factor_id,
        factor_version=factor_version,
    )
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "study_kind": active_slice.study_kind,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": active_card.to_dict(),
        "setup_spec": active_setup.to_dict() if active_setup is not None else None,
        "slice_spec": active_slice.to_dict(),
        "row_access": {
            "status": "unresolved",
            "reason": reason,
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": gate,
        "power": power,
        "created_at": active_slice.created_at,
    }
    payload["readout_id"] = _readout_id("fpgap", payload)
    return payload


def run_label_shuffle_surrogate(
    *,
    setup: SetupSpec | Mapping[str, Any],
    injected: InjectedRows,
    surrogate_runs: int,
    base_seed: int,
) -> dict[str, JsonValue]:
    """Run the bounded label-shuffle ZERO_PASS surrogate calibration."""

    active_setup = _coerce_setup(setup)
    probe = compile_setup_spec_to_conditional_probe(active_setup)
    context_rows = _feature_rows(injected, "context")
    trigger_rows = _feature_rows(injected, "trigger")
    path_rows = _label_rows(injected, "path")

    observed = build_path_label_observation_set(
        probe,
        context_factor_values=context_rows,
        trigger_factor_values=trigger_rows,
        path_labels=path_rows,
    )
    observed_uplift = _conditional_uplift(
        observed.conditioned_observations,
        observed.aligned_observations,
    )
    target_rows = [row for row in path_rows if row.get("label_type") == "target_before_stop"]
    target_values = [bool(row.get("value")) for row in target_rows]

    pass_count = 0
    error_count = 0
    for run_index in range(surrogate_runs):
        rng = random.Random(base_seed + run_index)
        shuffled_values = list(target_values)
        rng.shuffle(shuffled_values)
        target_iter = iter(shuffled_values)
        rebuilt: list[dict[str, Any]] = []
        for row in path_rows:
            if row.get("label_type") == "target_before_stop":
                replaced = dict(row)
                replaced["value"] = next(target_iter)
                rebuilt.append(replaced)
            else:
                rebuilt.append(dict(row))
        try:
            surrogate_observations = build_path_label_observation_set(
                probe,
                context_factor_values=context_rows,
                trigger_factor_values=trigger_rows,
                path_labels=rebuilt,
            )
            surrogate_uplift = _conditional_uplift(
                surrogate_observations.conditioned_observations,
                surrogate_observations.aligned_observations,
            )
        except ConditionalProbeError:
            error_count += 1
            continue
        if (
            surrogate_uplift is not None
            and observed_uplift is not None
            and abs(surrogate_uplift) > abs(observed_uplift)
        ):
            pass_count += 1

    return build_surrogate_zero_pass_gate(
        run_count=surrogate_runs,
        gate_pass_count=pass_count,
        error_count=error_count,
    )


def _run_main_effect(
    card: MechanismCard,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
) -> dict[str, JsonValue]:
    feature_rows = _feature_rows(injected, "factor", fallback_first=True)
    label_rows = _label_rows(injected, "label", fallback_first=True)
    observations = _align_main_effect_rows(feature_rows, label_rows)
    feature = _first_feature(slice_spec, roles=("factor",))
    spec = {
        "diagnostics_run_spec_id": f"fast_probe_{card.mechanism_id}",
        "content_hash": hash_config(
            {
                "mechanism_id": card.mechanism_id,
                "slice_id": slice_spec.slice_id,
                "study_kind": slice_spec.study_kind,
            }
        ),
    }
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=spec,
        observations=observations,
        lineage_refs={
            "mechanism_id": card.mechanism_id,
            "factor_id": feature.factor_id,
            "slice_id": slice_spec.slice_id,
        },
    )
    report_payload = result.report.to_dict()
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "RECORDED",
        "study_kind": MAIN_EFFECT,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": None,
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "build_factor_diagnostics_run",
        "readout": {
            "factor_diagnostics_report": report_payload,
            "diagnostics_run_record": result.record.to_dict(),
        },
    }
    payload["readout_id"] = _readout_id("fpmain", payload)
    return payload


def _run_context_not_equal_trigger(
    card: MechanismCard,
    setup: SetupSpec,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
) -> dict[str, JsonValue]:
    surrogate_gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=slice_spec.surrogate_run_count,
        base_seed=slice_spec.surrogate_base_seed,
    )
    if str(surrogate_gate.get("threshold_verdict")) != ZERO_PASS_MET:
        # The label-shuffle surrogate-FDR gate is NOT met: the conditioned effect is
        # indistinguishable from shuffled-label noise (or calibration was insufficient).
        # That is an HONEST exploratory outcome, not an error — return INCONCLUSIVE so the
        # loop records a verdict + routes to memory (requeue), never a tradable readout.
        return _build_surrogate_blocked_readout(
            card,
            setup,
            slice_spec,
            injected,
            handles=handles,
            surrogate_gate=surrogate_gate,
        )
    readout = evaluate_setup_conditional_probe(
        setup,
        context_factor_values=_feature_rows(injected, "context"),
        trigger_factor_values=_feature_rows(injected, "trigger"),
        path_labels=_label_rows(injected, "path"),
        family_id=_family_id(card, slice_spec),
        family_budget=_family_budget(card, slice_spec),
        surrogate_run_count=int(surrogate_gate["run_count"]),
        variant_id=_variant_id(card, setup, slice_spec),
        surrogate_gate_pass_count=int(surrogate_gate["gate_pass_count"]),
        surrogate_error_count=int(surrogate_gate["error_count"]),
        label_version=slice_spec.materialized_label_version,
        data_version=slice_spec.data_version,
        created_at=slice_spec.created_at,
    )
    readout_payload = readout.to_dict()
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "RECORDED",
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": setup.to_dict(),
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "evaluate_setup_conditional_probe",
        "readout": readout_payload,
        "surrogate_fdr_gate": readout_payload["surrogate_fdr_gate"],
        "variant_ledger_binding": readout_payload["variant_ledger_binding"],
        "power": readout_payload["power"],
    }
    payload["readout_id"] = readout_payload["readout_id"]
    return payload


def _build_surrogate_blocked_readout(
    card: MechanismCard,
    setup: SetupSpec,
    slice_spec: SliceSpec,
    injected: InjectedRows,
    *,
    handles: ResolvedSliceHandles,
    surrogate_gate: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Honest INCONCLUSIVE readout when the surrogate-FDR gate is not ZERO_PASS_MET.

    The label-shuffle surrogate found the conditioned effect indistinguishable from
    shuffled-label noise (or calibration was insufficient): a legitimate research null,
    not an error. Return INCONCLUSIVE carrying the real surrogate gate so the loop routes
    it to memory (requeue); promotion_eligible stays False and no tradable metric is read.
    """

    factor_id, factor_version = _power_factor(slice_spec, setup)
    power = build_ic_power_statement(
        n_eff=0,
        scope="per_factor",
        factor_id=factor_id,
        factor_version=factor_version,
    )
    issue_code = str(surrogate_gate.get("threshold_verdict") or "surrogate_fdr_not_met")
    payload: dict[str, JsonValue] = {
        "schema": FAST_PROBE_SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": issue_code,
        "study_kind": CONTEXT_NOT_EQUAL_TRIGGER,
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": card.to_dict(),
        "setup_spec": setup.to_dict(),
        "slice_spec": slice_spec.to_dict(),
        "row_access": _resolved_row_access(injected),
        "resolved_handles": handles.to_dict(),
        "engine": "run_label_shuffle_surrogate",
        "surrogate_fdr_gate": surrogate_gate,
        "power": power,
        "created_at": slice_spec.created_at,
    }
    payload["readout_id"] = _readout_id("fpsg", payload)
    return payload


def _resolve_slice_handles(
    slice_spec: SliceSpec,
    resolver: FeatureLabelPackResolver,
) -> ResolvedSliceHandles:
    feature_handles = ()
    label_handles = ()
    if slice_spec.feature_pack_refs:
        feature_handles = tuple(
            handle.to_dict()
            for handle in resolver.resolve_feature_packs(
                slice_spec.feature_pack_refs,
                expected_dataset_version_id=slice_spec.dataset_version_id,
                expected_feature_request_ids=slice_spec.feature_request_ids,
                partition_id=slice_spec.partition_id,
                # Exploratory lane: horizon-agnostic features (<instr>_<year>_full_year)
                # legitimately serve a horizon-specific runtime; join is no-lookahead on
                # event_ts/available_ts. Labels below stay strict.
                allow_horizon_agnostic_partition=True,
            )
        )
    if slice_spec.label_pack_refs:
        label_handles = tuple(
            handle.to_dict()
            for handle in resolver.resolve_label_packs(
                slice_spec.label_pack_refs,
                expected_dataset_version_id=slice_spec.dataset_version_id,
                expected_label_spec_ids=slice_spec.label_spec_ids,
                partition_id=slice_spec.partition_id,
            )
        )
    return ResolvedSliceHandles(feature_handles=feature_handles, label_handles=label_handles)


def _load_injected_rows(root: Path, slice_spec: SliceSpec) -> InjectedRows:
    feature_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    label_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    for feature in slice_spec.feature_inputs:
        path = _input_path(root, feature.relative_path, field=f"feature[{feature.role}]")
        rows = tuple(
            _factor_rows_from_records(
                load_parquet_values(path),
                feature,
                slice_spec=slice_spec,
            )
        )
        feature_rows[feature.role] = rows
    for label in slice_spec.label_inputs:
        path = _input_path(root, label.relative_path, field=f"label[{label.role}]")
        rows = tuple(
            _label_rows_from_records(
                load_parquet_values(path),
                label,
                slice_spec=slice_spec,
            )
        )
        label_rows[label.role] = rows
    return InjectedRows(feature_rows_by_role=feature_rows, label_rows_by_role=label_rows)


def _factor_rows_from_records(
    records: Sequence[Mapping[str, Any]],
    feature: SliceFeatureInput,
    *,
    slice_spec: SliceSpec,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bar_index, record in enumerate(sorted(records, key=lambda item: str(item.get("event_ts")))):
        # A feature SET pack holds multiple feature_version_ids; select only the one
        # this role's factor targets (feature.pack_ref == the feature_version_id), so a
        # single factor never gets duplicate rows per (instrument, event_ts) key. Labels
        # already filter by label_version_id symmetrically. Only skip records that
        # actually CARRY a differing feature_version_id; records without the column
        # (single-feature packs, in-memory fixtures) are kept (backward compatible).
        record_fver = record.get("feature_version_id")
        if feature.pack_ref and record_fver and str(record_fver) != feature.pack_ref:
            continue
        numeric = _optional_numeric(record.get("value"))
        if numeric is None:
            continue
        rows.append(
            {
                "factor_id": feature.factor_id,
                "factor_version": feature.factor_version,
                "instrument_id": slice_spec.instrument_id,
                "event_ts": _required(record, "event_ts"),
                "available_ts": record.get("available_ts") or record.get("event_ts"),
                "session_id": slice_spec.session_id,
                "data_version": slice_spec.data_version,
                "bar_index": int(record.get("bar_index", bar_index)),
                "value": numeric,
                "normalized_value": numeric,
                "factor_value": numeric,
                "feature_value": numeric,
            }
        )
    return rows


def _label_rows_from_records(
    records: Sequence[Mapping[str, Any]],
    label: SliceLabelInput,
    *,
    slice_spec: SliceSpec,
) -> list[dict[str, Any]]:
    bindings = slice_spec.label_version_map
    rows: list[dict[str, Any]] = []
    for record in records:
        version_id = str(record.get("label_version_id", ""))
        binding = bindings.get(version_id)
        if binding is None and bindings:
            continue
        label_type = (
            binding.label_type
            if binding is not None
            else str(record.get("label_type") or "forward_return_1m")
        )
        value_type = (
            binding.value_type
            if binding is not None
            else ("bool" if label_type in {"target_before_stop", "stop_before_target"} else "float")
        )
        value = _cast_label_value(record.get("value"), value_type)
        event_ts = _required(record, "event_ts")
        horizon_end_ts = str(
            record.get("horizon_end_ts") or record.get("label_available_ts") or event_ts
        )
        rows.append(
            {
                "label_id": label.label_id,
                "instrument_id": slice_spec.instrument_id,
                "event_ts": event_ts,
                "horizon": _horizon_seconds(slice_spec, record),
                "label_type": label_type,
                "value": value,
                "path_metadata": {
                    "session_id": slice_spec.session_id,
                    "label_version": (
                        slice_spec.materialized_label_version
                        or record.get("materialized_label_version")
                        or version_id
                        or "unversioned"
                    ),
                    "horizon_end_ts": horizon_end_ts,
                    "path_label": label.label_id,
                    "path_label_id": label.label_id,
                    "label_spec_id": label.label_spec_id or label.label_id,
                    "required_future_bars": _required_future_bars(slice_spec, record),
                    "observed_future_bars": _observed_future_bars(slice_spec, record),
                    "insufficient_future": bool(record.get("insufficient_future", False)),
                },
                "data_version": slice_spec.data_version,
                "label_available_ts": _required(record, "label_available_ts"),
            }
        )
    return rows


def _align_main_effect_rows(
    feature_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    label_index: dict[tuple[str, str, str, str], Mapping[str, Any]] = {}
    for label in label_rows:
        key = _alignment_key(label)
        if key not in label_index:
            label_index[key] = label
    observations: list[dict[str, Any]] = []
    for feature in feature_rows:
        label = label_index.get(_alignment_key(feature))
        if label is None:
            continue
        observations.append(
            {
                "instrument_id": feature["instrument_id"],
                "event_ts": feature["event_ts"],
                "session_id": feature["session_id"],
                "data_version": feature["data_version"],
                "available_ts": feature["available_ts"],
                "label_available_ts": label["label_available_ts"],
                "factor_id": feature["factor_id"],
                "factor_version": feature["factor_version"],
                "factor_value": feature["value"],
                "feature_value": feature["value"],
                "value": feature["value"],
                "label_value": _label_numeric_value(label["value"]),
                "forward_return": _label_numeric_value(label["value"]),
                "horizon_seconds": int(label["horizon"]),
            }
        )
    if not observations:
        raise ValueError("main_effect fast probe found no aligned feature/label rows")
    return observations


def _require_non_empty_rows(injected: InjectedRows) -> None:
    for role, rows in injected.feature_rows_by_role.items():
        if not rows:
            raise ValueError(f"feature input {role!r} resolved to zero usable rows")
    for role, rows in injected.label_rows_by_role.items():
        if not rows:
            raise ValueError(f"label input {role!r} resolved to zero usable rows")


def _resolved_row_access(injected: InjectedRows) -> dict[str, JsonValue]:
    return {
        "status": "resolved_local_only",
        "reason": (
            "Rows were loaded via core.value_store.load_parquet_values in "
            "research_lane and injected in-memory into unchanged probe engines."
        ),
        "fabricated_values": False,
        "row_counts": injected.row_counts(),
    }


def _input_path(root: Path, relative_path: str | None, *, field: str) -> Path:
    if relative_path is None:
        raise ValueError(f"{field} lacks a relative_path; resolver handles are value-free")
    path = Path(relative_path).expanduser()
    return path if path.is_absolute() else root / path


def _feature_rows(
    injected: InjectedRows,
    role: str,
    *,
    fallback_first: bool = False,
) -> tuple[dict[str, Any], ...]:
    rows = injected.feature_rows_by_role.get(role)
    if rows is None and fallback_first and injected.feature_rows_by_role:
        rows = next(iter(injected.feature_rows_by_role.values()))
    if rows is None:
        raise FastProbeError(f"slice is missing feature role {role!r}")
    return tuple(dict(row) for row in rows)


def _label_rows(
    injected: InjectedRows,
    role: str,
    *,
    fallback_first: bool = False,
) -> tuple[dict[str, Any], ...]:
    rows = injected.label_rows_by_role.get(role)
    if rows is None and fallback_first and injected.label_rows_by_role:
        rows = next(iter(injected.label_rows_by_role.values()))
    if rows is None:
        raise FastProbeError(f"slice is missing label role {role!r}")
    return tuple(dict(row) for row in rows)


def _first_feature(slice_spec: SliceSpec, *, roles: Sequence[str]) -> SliceFeatureInput:
    for role in roles:
        for feature in slice_spec.feature_inputs:
            if feature.role == role:
                return feature
    return slice_spec.feature_inputs[0]


def _alignment_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["instrument_id"]),
        str(row["event_ts"]),
        str(row.get("session_id") or row.get("path_metadata", {}).get("session_id")),
        str(row["data_version"]),
    )


def _conditional_uplift(
    conditioned: Sequence[Mapping[str, Any]],
    aligned: Sequence[Mapping[str, Any]],
) -> float | None:
    conditioned_share = target_before_stop_probability(conditioned).get(
        "target_before_stop_probability"
    )
    aligned_share = target_before_stop_probability(aligned).get("target_before_stop_probability")
    if conditioned_share is None or aligned_share is None:
        return None
    return float(conditioned_share) - float(aligned_share)


def _family_id(card: MechanismCard, slice_spec: SliceSpec) -> str:
    if slice_spec.family_id:
        return slice_spec.family_id
    value = card.duplicate_exposure.get("family_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return card.mechanism_id


def _family_budget(card: MechanismCard, slice_spec: SliceSpec) -> int:
    return int(
        slice_spec.family_budget if slice_spec.family_budget is not None else card.variant_budget
    )


def _variant_id(card: MechanismCard, setup: SetupSpec, slice_spec: SliceSpec) -> str | None:
    if slice_spec.variant_id:
        return slice_spec.variant_id
    value = card.duplicate_exposure.get("variant_id")
    if isinstance(value, str) and value.strip() and value.strip() in setup.allowed_variants:
        return value.strip()
    return None


def _power_factor(slice_spec: SliceSpec, setup: SetupSpec | None) -> tuple[str, str]:
    if setup is not None:
        trigger = dict(setup.event_trigger)
        factor_id = str(trigger.get("factor_id") or "")
        factor_version = str(trigger.get("factor_version") or "")
        if factor_id and factor_version:
            return factor_id, factor_version
    feature = slice_spec.feature_inputs[0]
    return feature.factor_id, feature.factor_version


def _horizon_seconds(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("horizon") or record.get("horizon_seconds") or slice_spec.horizon_seconds
    if value is None:
        raise ValueError("label rows require horizon_seconds or slice_spec.horizon_seconds")
    if isinstance(value, str):
        text = value.strip().lower()
        if text.endswith("m"):
            return int(float(text[:-1]) * 60)
        if text.endswith("s"):
            return int(float(text[:-1]))
    return int(value)


def _required_future_bars(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("required_future_bars") or slice_spec.required_future_bars
    if value is None:
        raise ValueError("label rows require required_future_bars")
    return int(value)


def _observed_future_bars(slice_spec: SliceSpec, record: Mapping[str, Any]) -> int:
    value = record.get("observed_future_bars") or _required_future_bars(slice_spec, record)
    return int(value)


def _cast_label_value(value: Any, value_type: str) -> bool | int | float | None:
    if value is None:
        return None
    if value_type == "bool":
        return bool(value)
    if value_type == "int":
        return int(value)
    if value_type == "float":
        return float(value)
    raise ValueError(f"unsupported label value_type: {value_type}")


def _label_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def _optional_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        for key in ("normalized_value", "value"):
            if key in value:
                return _optional_numeric(value[key])
        return None
    return float(value)


def _required(record: Mapping[str, Any], field: str) -> Any:
    value = record.get(field)
    if value is None:
        raise ValueError(f"value row is missing {field}")
    return value


def _coerce_card(value: MechanismCard | Mapping[str, Any]) -> MechanismCard:
    if isinstance(value, MechanismCard):
        return validate_mechanism_card(value.to_dict())
    return validate_mechanism_card(value)


def _coerce_setup(value: SetupSpec | Mapping[str, Any]) -> SetupSpec:
    if isinstance(value, SetupSpec):
        return validate_setup_spec(value.to_dict())
    return validate_setup_spec(value)


def _coerce_slice(value: SliceSpec | Mapping[str, Any]) -> SliceSpec:
    if isinstance(value, SliceSpec):
        return SliceSpec.from_mapping(value.to_dict())
    return SliceSpec.from_mapping(value)


def _readout_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{hash_config(payload)[:24]}"


_DATA_GAP_EXCEPTIONS = (
    DataDependencyError,
    RuntimeInputResolverError,
    OSError,
    ValueError,
    KeyError,
    SliceSpecError,
)


__all__ = [
    "FAST_PROBE_SCHEMA",
    "FastProbeError",
    "InjectedRows",
    "ResolvedSliceHandles",
    "build_fast_probe_data_gap",
    "fast_probe",
    "run_label_shuffle_surrogate",
]
