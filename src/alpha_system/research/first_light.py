"""First-light evidence helpers for the strategy-shaped research lane."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.core.hashing import hash_config
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    MechanismCard,
    create_mechanism_card,
)
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.labels.spec import LabelSpec
from alpha_system.research.conditional_probe import (
    ConditionalProbeReadout,
    build_surrogate_zero_pass_gate,
    compile_setup_spec_to_conditional_probe,
    evaluate_setup_conditional_probe,
)
from alpha_system.runtime.diagnostics.power import build_ic_power_statement
from alpha_system.strategies.templates import (
    SINGLE_FACTOR_THRESHOLD_TEMPLATE,
    build_single_factor_threshold_spec,
    evaluate_single_factor_threshold,
)

FIRST_LIGHT_SCHEMA = "alpha_system.research.strategy_shaped_lane.first_light.v1"
DE_STACK_SCHEMA = "alpha_system.research.strategy_shaped_lane.de_stack.v1"

FIRST_LIGHT_CONTEXT_FACTOR_ID = "liquidity_structure_range_contraction"
FIRST_LIGHT_CONTEXT_FACTOR_VERSION = "v1_es_2024_liquidity_structure_range_contraction"
FIRST_LIGHT_TRIGGER_FACTOR_ID = "liquidity_structure_failed_high_breakout_flag"
FIRST_LIGHT_TRIGGER_FACTOR_VERSION = (
    "v1_es_2024_liquidity_structure_failed_high_breakout_flag"
)
FIRST_LIGHT_VARIANT_ID = "baseline_range_contraction_failed_high_breakout"
FIRST_LIGHT_FAMILY_ID = "ssrl_p03_first_light_range_contraction_failed_high_breakout"
FIRST_LIGHT_FAMILY_BUDGET = 1
FIRST_LIGHT_HOLD_MINUTES = 120

FIRST_LIGHT_CONTEXT_MANIFEST = (
    "features/materialized/futures_substrate_scaleout_v1/"
    "regime_volatility_compression/"
    "feature_set_futures_scaleout_regime_volatility_compression/"
    "v1_es_2024_liquidity_structure_range_contraction/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_full_year/"
    "values.parquet.manifest.json"
)
FIRST_LIGHT_TRIGGER_MANIFEST = (
    "features/materialized/futures_substrate_scaleout_v1/"
    "liquidity_sweep_pa_structure/"
    "feature_set_futures_scaleout_liquidity_sweep_pa_structure/"
    "v1_es_2024_liquidity_structure_failed_high_breakout_flag/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_full_year/"
    "values.parquet.manifest.json"
)
FIRST_LIGHT_PATH_LABEL_MANIFEST = (
    "lcfp_p08_benchmark_20260610T170838Z/path/workers_1/"
    "labels/materialized/futures_substrate_scaleout_v1/path/"
    "lset_99a8f0764554bea7ff73f1c608a676f2e691603c4592b2eac910e64cd0b86ddd/"
    "dsv_databento_ohlcv_05404069799decb0/ES_2024_120m_lcfp_p08_es_202406/"
    "values.parquet.manifest.json"
)

DE_STACK_FACTOR_FAMILY = "vwap_session"
DE_STACK_FACTOR_ID = "factor_session_minute"
DE_STACK_FACTOR_REFERENCE = f"{DE_STACK_FACTOR_FAMILY}.{DE_STACK_FACTOR_ID}"
DE_STACK_FACTOR_VERSION = "settler_flagged_isolated_v1"
DE_STACK_OBSERVATION_COUNT = 6862
DE_STACK_ISOLATED_IC = 0.068


def first_light_path_label_id() -> str:
    """Return the governed path-label binding used by the first-light setup."""

    return generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {
            "family": "path",
            "name": "target_before_stop",
            "horizon": "120m",
            "dataset": "ES_2024",
            "phase": "SSRL-P03",
        },
    )


def build_first_light_mechanism_card() -> MechanismCard:
    """Declare the first-light strategy-shaped idea as a MechanismCard."""

    return create_mechanism_card(
        source="SSRL-P03 first-light worked example",
        rationale=(
            "A pre-declared range-contraction context can isolate sessions where "
            "a separate failed-high-breakout trigger is worth reading against a "
            "fixed path outcome."
        ),
        expected_mechanism=(
            "The context identifies compressed auction state before the event. "
            "The trigger is a distinct prior-high sweep and close-back-inside "
            "event read from a different factor family."
        ),
        expected_direction="target-before-stop path outcome after reclaim event",
        horizon="120m",
        session="RTH",
        required_features=[
            FIRST_LIGHT_CONTEXT_FACTOR_ID,
            FIRST_LIGHT_TRIGGER_FACTOR_ID,
        ],
        required_labels=["target_before_stop_120m_path_label"],
        cost_sensitivity={"scope": "exploratory evidence only", "new_data": False},
        variant_budget=FIRST_LIGHT_FAMILY_BUDGET,
        duplicate_exposure={
            "status": "bounded",
            "family_id": FIRST_LIGHT_FAMILY_ID,
            "variant_id": FIRST_LIGHT_VARIANT_ID,
        },
        stamp=EXPLORATORY_STAMP,
    )


def build_first_light_setup_spec(
    mechanism_card: MechanismCard | None = None,
) -> SetupSpec:
    """Declare the first-light SetupSpec with separate context and trigger factors."""

    mechanism = mechanism_card or build_first_light_mechanism_card()
    return create_setup_spec(
        entry_context={
            "factor_id": FIRST_LIGHT_CONTEXT_FACTOR_ID,
            "factor_version": FIRST_LIGHT_CONTEXT_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">=",
            "threshold": 0.75,
            "bucket": "range_contraction_high",
        },
        event_trigger={
            "factor_id": FIRST_LIGHT_TRIGGER_FACTOR_ID,
            "factor_version": FIRST_LIGHT_TRIGGER_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">",
            "threshold": 0.0,
            "event": "prior_high_sweep_close_back_inside",
        },
        regime_filter={"session": "RTH", "instrument_root": "ES"},
        confirmation={"policy": "none_added_in_p03", "fixed_before_readout": True},
        invalidation={"policy": "fixed_path_stop_binding", "fixed_before_readout": True},
        stop={"binding": "fixed_stop_from_path_label", "geometry": "unchanged"},
        target={"path_outcome": "target_before_stop", "geometry": "unchanged"},
        hold_time={"max_minutes": FIRST_LIGHT_HOLD_MINUTES, "horizon": "120m"},
        horizon="120m",
        path_label=first_light_path_label_id(),
        allowed_variants=[FIRST_LIGHT_VARIANT_ID],
        forbidden_post_hoc_changes=[
            "No context bucket changes after outcome readout.",
            "No trigger threshold changes after outcome readout.",
            "No target or stop geometry changes inside P03.",
        ],
        mechanism_id=mechanism.mechanism_id,
        stamp=EXPLORATORY_STAMP,
    )


def evaluate_first_light_probe(
    *,
    context_factor_values: Iterable[Mapping[str, Any]],
    trigger_factor_values: Iterable[Mapping[str, Any]],
    path_labels: Iterable[LabelSpec | Mapping[str, Any]],
    surrogate_run_count: int = 1,
    created_at: str = "2026-06-13T22:30:00Z",
) -> ConditionalProbeReadout:
    """Run the first-light idea through the unchanged P02 conditional probe."""

    return evaluate_setup_conditional_probe(
        build_first_light_setup_spec(),
        context_factor_values=context_factor_values,
        trigger_factor_values=trigger_factor_values,
        path_labels=path_labels,
        family_id=FIRST_LIGHT_FAMILY_ID,
        family_budget=FIRST_LIGHT_FAMILY_BUDGET,
        surrogate_run_count=surrogate_run_count,
        variant_id=FIRST_LIGHT_VARIANT_ID,
        created_at=created_at,
    )


def build_first_light_data_gap_evidence(
    *,
    alpha_data_root: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Build an honest first-light readout when row data cannot be loaded."""

    mechanism = build_first_light_mechanism_card()
    setup = build_first_light_setup_spec(mechanism)
    probe = compile_setup_spec_to_conditional_probe(setup)
    manifest_state = _manifest_state(alpha_data_root)
    gate = build_surrogate_zero_pass_gate(
        run_count=0,
        gate_pass_count=0,
        error_count=0,
    )
    power = build_ic_power_statement(
        n_eff=0,
        scope="per_factor",
        factor_id=FIRST_LIGHT_TRIGGER_FACTOR_ID,
        factor_version=FIRST_LIGHT_TRIGGER_FACTOR_VERSION,
    )
    payload: dict[str, JsonValue] = {
        "schema": FIRST_LIGHT_SCHEMA,
        "phase_id": "SSRL-P03",
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "mechanism_card": mechanism.to_dict(),
        "setup_spec": setup.to_dict(),
        "compiled_probe": probe.to_dict(),
        "variant_id": FIRST_LIGHT_VARIANT_ID,
        "family_id": FIRST_LIGHT_FAMILY_ID,
        "family_budget": FIRST_LIGHT_FAMILY_BUDGET,
        "outcome_source": "materialized_path_labels",
        "row_access": {
            "status": "unavailable_in_executor",
            "reason": (
                "Local materializations are Parquet-backed and no sanctioned "
                "Parquet reader module is importable in this executor."
            ),
            "fabricated_values": False,
        },
        "manifest_state": manifest_state,
        "surrogate_fdr_gate": gate,
        "power": power,
        "created_at": "2026-06-13T22:30:00Z",
    }
    payload["evidence_id"] = _evidence_id("flgap", payload)
    return payload


def build_de_stack_single_factor_evidence(
    *,
    sample_factor: Mapping[str, Any] | None = None,
) -> dict[str, JsonValue]:
    """Record the vwap-session de-stack read through the existing single-factor engine."""

    spec = build_single_factor_threshold_spec(
        strategy_id="ssrl_p03_de_stack_factor_session_minute",
        version="v1",
        owner="strategy_shaped_research_lane_v0",
        factor_id=DE_STACK_FACTOR_REFERENCE,
        factor_version=DE_STACK_FACTOR_VERSION,
        entry_threshold=0.0,
        exit_threshold=-1.0,
        direction=Direction.LONG,
    )
    factor = dict(sample_factor or _default_de_stack_sample_factor())
    signal = evaluate_single_factor_threshold(
        spec,
        {DE_STACK_FACTOR_REFERENCE: factor},
    )
    gate = build_surrogate_zero_pass_gate(
        run_count=1,
        gate_pass_count=0,
        error_count=0,
    )
    power = build_ic_power_statement(
        n_eff=DE_STACK_OBSERVATION_COUNT,
        scope="per_factor",
        factor_id=DE_STACK_FACTOR_REFERENCE,
        factor_version=DE_STACK_FACTOR_VERSION,
    )
    payload: dict[str, JsonValue] = {
        "schema": DE_STACK_SCHEMA,
        "phase_id": "SSRL-P03",
        "status": "RECORDED",
        "stamp": EXPLORATORY_STAMP,
        "promotion_eligible": False,
        "factor_family": DE_STACK_FACTOR_FAMILY,
        "factor_id": DE_STACK_FACTOR_ID,
        "factor_reference": DE_STACK_FACTOR_REFERENCE,
        "factor_version": DE_STACK_FACTOR_VERSION,
        "single_factor_engine": {
            "template": SINGLE_FACTOR_THRESHOLD_TEMPLATE,
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
            "sample_signal_type": signal.signal_type.value,
            "engine_changed": False,
        },
        "isolated_read": {
            "ic": DE_STACK_ISOLATED_IC,
            "observation_count": DE_STACK_OBSERVATION_COUNT,
            "stacked_context": "diluted_when_read_with_siblings",
            "source": "SHIP_REFIT settler flag carried into SSRL-P03",
        },
        "surrogate_fdr_gate": gate,
        "power": power,
        "created_at": "2026-06-13T22:30:00Z",
    }
    payload["evidence_id"] = _evidence_id("dstk", payload)
    return payload


def _manifest_state(alpha_data_root: str | Path | None) -> dict[str, JsonValue]:
    root = _alpha_data_root(alpha_data_root)
    manifests = {
        "context_factor": FIRST_LIGHT_CONTEXT_MANIFEST,
        "trigger_factor": FIRST_LIGHT_TRIGGER_MANIFEST,
        "path_label": FIRST_LIGHT_PATH_LABEL_MANIFEST,
    }
    return {
        "root_policy": "ALPHA_DATA_ROOT",
        "checked": root is not None,
        "manifests": {
            name: {
                "relative_path": relative,
                "present": bool(root is not None and (root / relative).exists()),
            }
            for name, relative in manifests.items()
        },
    }


def _alpha_data_root(alpha_data_root: str | Path | None) -> Path | None:
    if alpha_data_root is not None:
        return Path(alpha_data_root)
    env_value = os.environ.get("ALPHA_DATA_ROOT")
    if env_value:
        return Path(env_value)
    return None


def _default_de_stack_sample_factor() -> dict[str, JsonValue]:
    event_ts = datetime(2026, 1, 2, 15, 0, tzinfo=UTC)
    return {
        "factor_id": DE_STACK_FACTOR_REFERENCE,
        "factor_version": DE_STACK_FACTOR_VERSION,
        "instrument_id": "ES",
        "event_ts": _datetime_text(event_ts),
        "available_ts": _datetime_text(event_ts),
        "session_id": "CME:2026-01-02:RTH",
        "bar_index": 90,
        "value": 0.5,
        "normalized_value": 0.5,
        "quality_flags": ["settler_read_shape"],
        "data_version": "ssrl_p03_shape_check",
        "compute_version": "existing_single_factor_template",
    }


def _datetime_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _evidence_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{hash_config(payload)[:24]}"


__all__ = [
    "DE_STACK_FACTOR_ID",
    "DE_STACK_FACTOR_REFERENCE",
    "DE_STACK_FACTOR_VERSION",
    "DE_STACK_ISOLATED_IC",
    "DE_STACK_OBSERVATION_COUNT",
    "DE_STACK_SCHEMA",
    "FIRST_LIGHT_CONTEXT_FACTOR_ID",
    "FIRST_LIGHT_CONTEXT_FACTOR_VERSION",
    "FIRST_LIGHT_FAMILY_BUDGET",
    "FIRST_LIGHT_FAMILY_ID",
    "FIRST_LIGHT_HOLD_MINUTES",
    "FIRST_LIGHT_SCHEMA",
    "FIRST_LIGHT_TRIGGER_FACTOR_ID",
    "FIRST_LIGHT_TRIGGER_FACTOR_VERSION",
    "FIRST_LIGHT_VARIANT_ID",
    "build_de_stack_single_factor_evidence",
    "build_first_light_data_gap_evidence",
    "build_first_light_mechanism_card",
    "build_first_light_setup_spec",
    "evaluate_first_light_probe",
    "first_light_path_label_id",
]
