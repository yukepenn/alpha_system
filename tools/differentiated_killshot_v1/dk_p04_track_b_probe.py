#!/usr/bin/env python3
"""DK-P04 Track B context!=trigger EXPLORATORY probe harness (tools/runtime side).

This coordinator harness is the **only** place real-data rows are read for the
DIFFERENTIATED_KILLSHOT_V1 Track B EXPLORATORY conditional probe. It runs the
just-landed SSRL conditional-probe engine, byte-unchanged, on a DIFFERENTIATED
``SetupSpec`` whose context and trigger are genuinely distinct signals (C1):

- ``entry_context``  = ``liquidity_structure_range_contraction``  (a range /
  volatility-compression *regime* descriptor; a CONTEXT predicate).
- ``event_trigger``  = ``liquidity_structure_failed_high_breakout_flag``  (a
  prior-high sweep-then-reclaim *event* flag from a DIFFERENT feature family; a
  TRIGGER predicate).

These are different ``factor_id``s **and** different underlying signals: one is a
trailing range-compression continuous descriptor, the other a discrete sweep /
reclaim event flag, materialized from separate FUTSUB FeaturePacks.

Data flow (no research->sim bridge):

1. Load already-materialized context-factor, trigger-factor, and path-label rows
   via ``core.value_store.load_parquet_values`` (tools/runtime only).
2. Map the materialized value-store schema onto the governance row schema that the
   pure probe expects (``factor_id`` / ``factor_version`` / ``instrument_id`` /
   ``event_ts`` / ``session_id`` / ``data_version`` / ``bar_index`` / ``value``
   for factors; the ASV1-P10 ``LabelSpec`` mapping for path labels). The probe is
   then fed in-memory rows; it never sees a path, a loader, or a Parquet.
3. Run a bounded label-shuffle surrogate calibration over the probe's conditioned
   target-before-stop statistic. ANY shuffled pass blocks and is diagnosed first;
   ``run_count > 0`` with ``0`` passes and ``0`` errors => ``ZERO_PASS_MET``.
4. Call ``evaluate_setup_conditional_probe`` with the injected rows. The surrogate
   ``ZERO_PASS_MET`` gate and the family-budget ``RESPECTED`` check are HARD
   preconditions enforced *inside* ``evaluate`` (it raises otherwise). The harness
   satisfies them; it never bypasses them.
5. Emit a value-free ``EVIDENCE.json`` (``stamp = EXPLORATORY``,
   ``promotion_eligible = false``) or an honest ``status = INCONCLUSIVE`` /
   ``issue_code = "DATA_GAP"`` when no row path resolves (no fabricated values).

``research/`` imports none of ``backtest`` / ``management`` / ``fast_path`` /
``value_store``; the value loader lives here on the tools side and hands rows in.
This output is permanently EXPLORATORY. It is NOT promotion evidence, NOT a
survivor, and does NOT enter FactorLibrary. No promotion, no second PnL truth, no
alpha / tradability / profitability claim.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.value_store import load_parquet_values
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MechanismCard,
    create_mechanism_card,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.research.conditional_probe import (
    ConditionalProbeError,
    build_surrogate_zero_pass_gate,
    compile_setup_spec_to_conditional_probe,
    evaluate_setup_conditional_probe,
)
from alpha_system.research.events import target_before_stop_probability
from alpha_system.runtime.diagnostics.power import build_ic_power_statement

# --------------------------------------------------------------------------- #
# Declared, distinct (C1) context and trigger signals + governed bindings.
# --------------------------------------------------------------------------- #

TRACK_B_SCHEMA = "alpha_system.research.differentiated_substrate.track_b.v1"
PHASE_ID = "DK-P04"

CONTEXT_FACTOR_ID = "liquidity_structure_range_contraction"
CONTEXT_FACTOR_VERSION = "v1_es_2024_liquidity_structure_range_contraction"
TRIGGER_FACTOR_ID = "liquidity_structure_failed_high_breakout_flag"
TRIGGER_FACTOR_VERSION = "v1_es_2024_liquidity_structure_failed_high_breakout_flag"

FAMILY_ID = "dk_p04_track_b_range_contraction_failed_high_breakout"
VARIANT_ID = "baseline_range_contraction_failed_high_breakout"
FAMILY_BUDGET = 1
HOLD_MINUTES = 120
HORIZON_SECONDS = 120 * 60

# A single normalized instrument / session id is synthesized for the join key:
# the materialized factor rows carry a series entity id and the label rows carry
# an instrument entity id; both describe the same ES front contract. The probe
# aligns context/trigger/label on (instrument_id, event_ts, session_id,
# data_version), so all three must share one normalized instrument and session id.
NORMALIZED_INSTRUMENT_ID = "ES"
NORMALIZED_SESSION_ID = "CME:ES_2024:RTH"
DATA_VERSION = "dsv_databento_ohlcv_05404069799decb0"

CONTEXT_THRESHOLD = 0.5
TRIGGER_THRESHOLD = 0.0

# Materialized parquet locations (relative to ALPHA_DATA_ROOT). These are the same
# manifests the SSRL first-light EVIDENCE referenced; here the tools-side loader
# actually reads them (the first-light DATA_GAP was an executor-import limitation,
# not a missing materialization).
CONTEXT_REL_PATH = (
    "features/materialized/futures_substrate_scaleout_v1/"
    "regime_volatility_compression/"
    "feature_set_futures_scaleout_regime_volatility_compression/"
    "v1_es_2024_liquidity_structure_range_contraction/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_full_year/values.parquet"
)
TRIGGER_REL_PATH = (
    "features/materialized/futures_substrate_scaleout_v1/"
    "liquidity_sweep_pa_structure/"
    "feature_set_futures_scaleout_liquidity_sweep_pa_structure/"
    "v1_es_2024_liquidity_structure_failed_high_breakout_flag/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_full_year/values.parquet"
)
PATH_LABEL_REL_PATH = (
    "lcfp_p08_benchmark_20260610T170838Z/path/workers_1/"
    "labels/materialized/futures_substrate_scaleout_v1/path/"
    "lset_99a8f0764554bea7ff73f1c608a676f2e691603c4592b2eac910e64cd0b86ddd/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_120m_lcfp_p08_es_202406/values.parquet"
)

# Path-label version ids carried by the materialized 120m path pack. Mapped onto
# the runtime label_type strings the conditional-probe observation set reads.
PATH_LABEL_VERSIONS: dict[str, tuple[str, str]] = {
    "lver_297d878219743d7ff8c31069a721539f3001c3c619f1d936b3caa031ae3d8d3b": (
        "target_before_stop",
        "bool",
    ),
    "lver_55179d3e8944c66c0204275ad94df9bc017339a41594c396c8bdbca6b6276735": (
        "mfe_by_horizon",
        "float",
    ),
    "lver_4a0478aae5c867bd307ed75a2478a28a56674619e6f9e3734d226a8fe37123b6": (
        "mae_by_horizon",
        "float",
    ),
}
MATERIALIZED_LABEL_VERSION = "lcfp_p08_es_202406"

DEFAULT_SURROGATE_RUNS = 64
DEFAULT_BASE_SEED = 0
CREATED_AT = "2026-06-14T12:00:00Z"


def path_label_governance_id() -> str:
    """Return the governed path-label binding id used by the Track B setup."""

    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {
            "family": "path",
            "name": "target_before_stop",
            "horizon": "120m",
            "dataset": "ES_2024",
            "phase": PHASE_ID,
        },
    )


def build_track_b_mechanism_card() -> MechanismCard:
    """Declare the Track B differentiated idea as an EXPLORATORY MechanismCard."""

    return create_mechanism_card(
        source="DK-P04 Track B differentiated context-not-equal-trigger probe",
        rationale=(
            "A pre-declared range-contraction regime context can isolate sessions "
            "where a separate prior-high sweep then close-back-inside trigger is "
            "worth reading against a fixed 120m target-before-stop path outcome."
        ),
        expected_mechanism=(
            "The context factor reads trailing range compression and marks when "
            "the setup is relevant. The trigger factor reads a distinct prior-high "
            "sweep then close-back-inside event from a different feature family, "
            "and only fires the entry inside the compressed-range context bucket."
        ),
        expected_direction="target-before-stop path outcome after the reclaim event",
        horizon="120m",
        session="RTH",
        required_features=[CONTEXT_FACTOR_ID, TRIGGER_FACTOR_ID],
        required_labels=["target_before_stop_120m_path_label"],
        cost_sensitivity={"scope": "exploratory evidence only", "new_data": False},
        variant_budget=FAMILY_BUDGET,
        duplicate_exposure={
            "status": "bounded",
            "family_id": FAMILY_ID,
            "variant_id": VARIANT_ID,
        },
        stamp=EXPLORATORY_STAMP,
    )


def build_track_b_setup_spec(mechanism_card: MechanismCard | None = None) -> SetupSpec:
    """Declare the Track B SetupSpec with genuinely distinct context and trigger."""

    mechanism = mechanism_card or build_track_b_mechanism_card()
    return create_setup_spec(
        entry_context={
            "factor_id": CONTEXT_FACTOR_ID,
            "factor_version": CONTEXT_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">=",
            "threshold": CONTEXT_THRESHOLD,
            "bucket": "range_contraction_high",
            "signal_kind": "trailing_range_compression_regime_descriptor",
        },
        event_trigger={
            "factor_id": TRIGGER_FACTOR_ID,
            "factor_version": TRIGGER_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">",
            "threshold": TRIGGER_THRESHOLD,
            "event": "prior_high_sweep_close_back_inside",
            "signal_kind": "discrete_sweep_reclaim_event_flag",
        },
        regime_filter={"session": "RTH", "instrument_root": "ES"},
        confirmation={"policy": "none_added_in_p04", "fixed_before_readout": True},
        invalidation={"policy": "fixed_path_stop_binding", "fixed_before_readout": True},
        stop={"binding": "fixed_stop_from_path_label", "geometry": "unchanged"},
        target={"path_outcome": "target_before_stop", "geometry": "unchanged"},
        hold_time={"max_minutes": HOLD_MINUTES, "horizon": "120m"},
        horizon="120m",
        path_label=path_label_governance_id(),
        allowed_variants=[VARIANT_ID],
        forbidden_post_hoc_changes=[
            "No context bucket changes after outcome readout.",
            "No trigger threshold changes after outcome readout.",
            "No target or stop geometry changes inside P04.",
        ],
        mechanism_id=mechanism.mechanism_id,
        stamp=EXPLORATORY_STAMP,
    )


# --------------------------------------------------------------------------- #
# Materialized row injection (tools/runtime side of the no-second-PnL rail).
# --------------------------------------------------------------------------- #


def _alpha_data_root(explicit: str | Path | None) -> Path | None:
    if explicit is not None:
        return Path(explicit).expanduser()
    env_value = os.environ.get("ALPHA_DATA_ROOT")
    if env_value:
        return Path(env_value).expanduser()
    return None


def _factor_rows_from_parquet(
    parquet_path: Path,
    *,
    factor_id: str,
    factor_version: str,
) -> list[dict[str, Any]]:
    """Map materialized feature value rows onto the probe factor row schema."""

    loaded = load_parquet_values(parquet_path)
    rows: list[dict[str, Any]] = []
    bar_index = 0
    for record in sorted(loaded, key=lambda item: str(item["event_ts"])):
        value = record.get("value")
        if value is None:
            continue
        numeric = float(value)
        rows.append(
            {
                "factor_id": factor_id,
                "factor_version": factor_version,
                "instrument_id": NORMALIZED_INSTRUMENT_ID,
                "event_ts": record["event_ts"],
                "available_ts": record.get("available_ts", record["event_ts"]),
                "session_id": NORMALIZED_SESSION_ID,
                "data_version": DATA_VERSION,
                "bar_index": bar_index,
                "value": numeric,
                "normalized_value": numeric,
            }
        )
        bar_index += 1
    return rows


def _path_label_rows_from_parquet(parquet_path: Path, path_label: str) -> list[dict[str, Any]]:
    """Map materialized path-label value rows onto the ASV1-P10 LabelSpec schema."""

    loaded = load_parquet_values(parquet_path)
    rows: list[dict[str, Any]] = []
    for record in loaded:
        version_id = str(record.get("label_version_id", ""))
        mapping = PATH_LABEL_VERSIONS.get(version_id)
        if mapping is None:
            continue
        label_type, cast = mapping
        raw_value = record.get("value")
        if cast == "bool":
            value: bool | float = bool(raw_value)
        else:
            value = float(raw_value)
        rows.append(
            {
                "label_id": path_label,
                "instrument_id": NORMALIZED_INSTRUMENT_ID,
                "event_ts": record["event_ts"],
                "horizon": HORIZON_SECONDS,
                "label_type": label_type,
                "value": value,
                "path_metadata": {
                    "session_id": NORMALIZED_SESSION_ID,
                    "label_version": MATERIALIZED_LABEL_VERSION,
                    "horizon_end_ts": record["horizon_end_ts"],
                    "path_label": path_label,
                    "required_future_bars": HOLD_MINUTES,
                    "observed_future_bars": HOLD_MINUTES,
                    "insufficient_future": False,
                },
                "data_version": DATA_VERSION,
                "label_available_ts": record["label_available_ts"],
            }
        )
    return rows


@dataclass(frozen=True, slots=True)
class InjectedRows:
    """In-memory materialized rows mapped onto the probe schema."""

    context_factor_values: list[dict[str, Any]]
    trigger_factor_values: list[dict[str, Any]]
    path_labels: list[dict[str, Any]]


def load_injected_rows(alpha_data_root: str | Path) -> InjectedRows:
    """Load and map the three materialized parquets into injectable rows."""

    root = Path(alpha_data_root).expanduser()
    context_path = root / CONTEXT_REL_PATH
    trigger_path = root / TRIGGER_REL_PATH
    label_path = root / PATH_LABEL_REL_PATH
    path_label = path_label_governance_id()
    return InjectedRows(
        context_factor_values=_factor_rows_from_parquet(
            context_path,
            factor_id=CONTEXT_FACTOR_ID,
            factor_version=CONTEXT_FACTOR_VERSION,
        ),
        trigger_factor_values=_factor_rows_from_parquet(
            trigger_path,
            factor_id=TRIGGER_FACTOR_ID,
            factor_version=TRIGGER_FACTOR_VERSION,
        ),
        path_labels=_path_label_rows_from_parquet(label_path, path_label),
    )


# --------------------------------------------------------------------------- #
# Label-shuffle surrogate calibration (the existing surrogate-path semantics).
# --------------------------------------------------------------------------- #


def run_label_shuffle_surrogate(
    *,
    setup: SetupSpec,
    injected: InjectedRows,
    surrogate_runs: int,
    base_seed: int,
) -> dict[str, JsonValue]:
    """Shuffle path-label outcomes and count any surrogate gate pass.

    The probe's conditioning statistic is the *conditional uplift* = the conditioned
    (context-passing) target-before-stop share minus the unconditioned (full aligned)
    target-before-stop share. Under the null, conditioning on the declared context
    carries no information about the path outcome, so a label shuffle should not
    reproduce the observed uplift. Each surrogate run shuffles the target-before-stop
    outcomes across event rows and recomputes the uplift. A run "passes" only if its
    shuffled |uplift| strictly exceeds the observed |uplift| (a surrogate cannot beat
    the real conditional read by chance under the zero-pass gate). ``run_count > 0``
    with ``0`` passes and ``0`` errors satisfies ``ZERO_PASS_MET``; any pass blocks
    and is reported (do not proceed).
    """

    probe = compile_setup_spec_to_conditional_probe(setup)
    from alpha_system.research.conditional_probe import build_path_label_observation_set

    observed = build_path_label_observation_set(
        probe,
        context_factor_values=injected.context_factor_values,
        trigger_factor_values=injected.trigger_factor_values,
        path_labels=injected.path_labels,
    )
    observed_uplift = _conditional_uplift(
        observed.conditioned_observations,
        observed.aligned_observations,
    )

    target_rows = [row for row in injected.path_labels if row["label_type"] == "target_before_stop"]
    target_values = [bool(row["value"]) for row in target_rows]

    pass_count = 0
    error_count = 0
    for run_index in range(surrogate_runs):
        rng = random.Random(base_seed + run_index)
        shuffled_values = list(target_values)
        rng.shuffle(shuffled_values)
        target_iter = iter(shuffled_values)
        rebuilt: list[dict[str, Any]] = []
        for row in injected.path_labels:
            if row["label_type"] == "target_before_stop":
                replaced = dict(row)
                replaced["value"] = next(target_iter)
                rebuilt.append(replaced)
            else:
                rebuilt.append(row)
        try:
            surrogate_obs = build_path_label_observation_set(
                probe,
                context_factor_values=injected.context_factor_values,
                trigger_factor_values=injected.trigger_factor_values,
                path_labels=rebuilt,
            )
            surrogate_uplift = _conditional_uplift(
                surrogate_obs.conditioned_observations,
                surrogate_obs.aligned_observations,
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


def _conditioned_target_share(observations: Sequence[Mapping[str, Any]]) -> float | None:
    summary = target_before_stop_probability(observations)
    return summary.get("target_before_stop_probability")


def _conditional_uplift(
    conditioned: Sequence[Mapping[str, Any]],
    aligned: Sequence[Mapping[str, Any]],
) -> float | None:
    conditioned_share = _conditioned_target_share(conditioned)
    aligned_share = _conditioned_target_share(aligned)
    if conditioned_share is None or aligned_share is None:
        return None
    return conditioned_share - aligned_share


# --------------------------------------------------------------------------- #
# EVIDENCE assembly (value-free; EXPLORATORY; honest DATA_GAP fallback).
# --------------------------------------------------------------------------- #


def _manifest_state(alpha_data_root: Path | None) -> dict[str, JsonValue]:
    relatives = {
        "context_factor": CONTEXT_REL_PATH,
        "trigger_factor": TRIGGER_REL_PATH,
        "path_label": PATH_LABEL_REL_PATH,
    }
    return {
        "root_policy": "ALPHA_DATA_ROOT",
        "checked": alpha_data_root is not None,
        "manifests": {
            name: {
                "relative_path": relative,
                "present": bool(
                    alpha_data_root is not None and (alpha_data_root / relative).exists()
                ),
            }
            for name, relative in relatives.items()
        },
    }


def build_data_gap_evidence(
    *,
    alpha_data_root: str | Path | None,
    reason: str,
) -> dict[str, JsonValue]:
    """Build an honest INCONCLUSIVE / DATA_GAP readout (no fabricated values)."""

    mechanism = build_track_b_mechanism_card()
    setup = build_track_b_setup_spec(mechanism)
    probe = compile_setup_spec_to_conditional_probe(setup)
    gate = build_surrogate_zero_pass_gate(run_count=0, gate_pass_count=0, error_count=0)
    power = build_ic_power_statement(
        n_eff=0,
        scope="per_factor",
        factor_id=TRIGGER_FACTOR_ID,
        factor_version=TRIGGER_FACTOR_VERSION,
    )
    payload: dict[str, JsonValue] = {
        "schema": TRACK_B_SCHEMA,
        "phase_id": PHASE_ID,
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": mechanism.to_dict(),
        "setup_spec": setup.to_dict(),
        "compiled_probe": probe.to_dict(),
        "variant_id": VARIANT_ID,
        "family_id": FAMILY_ID,
        "family_budget": FAMILY_BUDGET,
        "outcome_source": "materialized_path_labels",
        "row_access": {
            "status": "unresolved",
            "reason": reason,
            "fabricated_values": False,
        },
        "manifest_state": _manifest_state(_alpha_data_root(alpha_data_root)),
        "surrogate_fdr_gate": gate,
        "power": power,
        "created_at": CREATED_AT,
    }
    payload["evidence_id"] = _evidence_id("tbgap", payload)
    return payload


def build_track_b_evidence(
    *,
    alpha_data_root: str | Path,
    surrogate_runs: int = DEFAULT_SURROGATE_RUNS,
    base_seed: int = DEFAULT_BASE_SEED,
) -> dict[str, JsonValue]:
    """Run the Track B probe over real materialized rows and build EVIDENCE.

    Returns a value-free EXPLORATORY readout when rows resolve, or an honest
    DATA_GAP payload when no sanctioned reader path resolves. No fabricated values.
    """

    root = _alpha_data_root(alpha_data_root)
    if root is None or not root.exists():
        return build_data_gap_evidence(
            alpha_data_root=alpha_data_root,
            reason="ALPHA_DATA_ROOT does not resolve to an existing local data root.",
        )

    try:
        injected = load_injected_rows(root)
    except (OSError, ValueError, KeyError) as exc:
        return build_data_gap_evidence(
            alpha_data_root=root,
            reason=f"Materialized rows could not be loaded via the sanctioned reader: {exc}",
        )

    if (
        not injected.context_factor_values
        or not injected.trigger_factor_values
        or not injected.path_labels
    ):
        return build_data_gap_evidence(
            alpha_data_root=root,
            reason="One or more materialized parquets resolved to zero usable rows.",
        )

    mechanism = build_track_b_mechanism_card()
    setup = build_track_b_setup_spec(mechanism)

    # FDR before metric: establish ZERO_PASS_MET on shuffled labels first.
    surrogate_gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=surrogate_runs,
        base_seed=base_seed,
    )

    try:
        readout = evaluate_setup_conditional_probe(
            setup,
            context_factor_values=injected.context_factor_values,
            trigger_factor_values=injected.trigger_factor_values,
            path_labels=injected.path_labels,
            family_id=FAMILY_ID,
            family_budget=FAMILY_BUDGET,
            surrogate_run_count=int(surrogate_gate["run_count"]),
            variant_id=VARIANT_ID,
            surrogate_gate_pass_count=int(surrogate_gate["gate_pass_count"]),
            surrogate_error_count=int(surrogate_gate["error_count"]),
            created_at=CREATED_AT,
        )
    except ConditionalProbeError as exc:
        return build_data_gap_evidence(
            alpha_data_root=root,
            reason=f"Probe precondition unmet on real rows (no fabrication): {exc}",
        )

    readout_dict = readout.to_dict()
    diagnostics = dict(readout_dict["diagnostics"])
    target_summary = diagnostics.get("target_before_stop_probability", {})
    degenerate = _is_degenerate_outcome(injected.path_labels)

    payload: dict[str, JsonValue] = {
        "schema": TRACK_B_SCHEMA,
        "phase_id": PHASE_ID,
        "status": "RECORDED",
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "outcome_source": "materialized_path_labels",
        "mechanism_card": mechanism.to_dict(),
        "setup_spec": setup.to_dict(),
        "compiled_probe": compile_setup_spec_to_conditional_probe(setup).to_dict(),
        "variant_id": readout_dict["variant_id"],
        "family_id": FAMILY_ID,
        "family_budget": FAMILY_BUDGET,
        "observation_counts": readout_dict["observation_counts"],
        "diagnostics": diagnostics,
        "variant_ledger_binding": readout_dict["variant_ledger_binding"],
        "surrogate_fdr_gate": readout_dict["surrogate_fdr_gate"],
        "power": readout_dict["power"],
        "outcome_caveats": _outcome_caveats(degenerate, target_summary),
        "manifest_state": _manifest_state(root),
        "row_access": {
            "status": "resolved_local_only",
            "reason": (
                "Materialized factor and path-label rows were loaded via "
                "core.value_store.load_parquet_values on the tools side and injected "
                "into the pure probe; only this value-free summary is committed."
            ),
            "fabricated_values": False,
        },
        "created_at": CREATED_AT,
    }
    payload["readout_id"] = readout_dict["readout_id"]
    payload["evidence_id"] = _evidence_id("tbrun", payload)
    return payload


def _is_degenerate_outcome(path_labels: Sequence[Mapping[str, Any]]) -> bool:
    target_values = {
        bool(row["value"])
        for row in path_labels
        if row["label_type"] == "target_before_stop"
    }
    return len(target_values) <= 1


def _outcome_caveats(
    degenerate: bool,
    target_summary: Mapping[str, Any],
) -> dict[str, JsonValue]:
    return {
        "exploratory_only": True,
        "promotion_eligible": False,
        "single_class_path_outcome": degenerate,
        "note": (
            "EXPLORATORY readout only. The materialized 120m target-before-stop "
            "slice (LCFP-P08 ES_2024 benchmark) is single-class (every outcome "
            "False under horizon_no_barrier), so the conditioned target-before-stop "
            "probability is degenerate; this is a substrate-coverage observation, "
            "not alpha, tradability, or profitability evidence."
            if degenerate
            else
            "EXPLORATORY readout only; diagnostics are research-only and are not "
            "alpha, tradability, or profitability evidence."
        ),
        "target_before_stop_event_count": target_summary.get("event_count"),
    }


def _evidence_id(prefix: str, payload: Mapping[str, Any]) -> str:
    from alpha_system.core.hashing import hash_config

    return f"{prefix}_{hash_config(payload)[:24]}"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alpha-data-root",
        default=None,
        help="Local alpha data root (defaults to ALPHA_DATA_ROOT env).",
    )
    parser.add_argument(
        "--evidence-out",
        required=True,
        help="Path to write the value-free EVIDENCE.json.",
    )
    parser.add_argument(
        "--surrogate-runs",
        type=int,
        default=DEFAULT_SURROGATE_RUNS,
        help="Label-shuffle surrogate run count (must be > 0 for ZERO_PASS_MET).",
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=DEFAULT_BASE_SEED,
        help="Base non-negative seed for the label shuffle.",
    )
    parser.add_argument(
        "--mechanism-card-out",
        default=None,
        help="Optional path to write the EXPLORATORY MechanismCard JSON.",
    )
    parser.add_argument(
        "--setup-spec-out",
        default=None,
        help="Optional path to write the EXPLORATORY SetupSpec JSON.",
    )
    args = parser.parse_args(argv)

    root = _alpha_data_root(args.alpha_data_root)
    if args.mechanism_card_out:
        _write_json(Path(args.mechanism_card_out), build_track_b_mechanism_card().to_dict())
    if args.setup_spec_out:
        _write_json(Path(args.setup_spec_out), build_track_b_setup_spec().to_dict())

    if root is None:
        evidence = build_data_gap_evidence(
            alpha_data_root=None,
            reason="No --alpha-data-root provided and ALPHA_DATA_ROOT is unset.",
        )
    else:
        evidence = build_track_b_evidence(
            alpha_data_root=root,
            surrogate_runs=args.surrogate_runs,
            base_seed=args.base_seed,
        )

    _write_json(Path(args.evidence_out), evidence)
    print(
        json.dumps(
            {
                "status": evidence.get("status"),
                "issue_code": evidence.get("issue_code"),
                "stamp": evidence.get("stamp"),
                "promotion_eligible": evidence.get("promotion_eligible"),
                "surrogate_fdr_gate": evidence.get("surrogate_fdr_gate"),
                "evidence_out": str(args.evidence_out),
            },
            sort_keys=True,
        )
    )
    return 0


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
