from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP, create_mechanism_card
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.research.conditional_probe import (
    ConditionalProbeError,
    build_probe_variant_ledger_record,
    compile_setup_spec_to_conditional_probe,
    evaluate_setup_conditional_probe,
)


def test_setup_probe_scores_trigger_inside_separate_context_over_path_labels() -> None:
    setup = _setup_spec()

    readout = evaluate_setup_conditional_probe(
        setup,
        context_factor_values=_factor_rows("range_context", "ctx:v1", (0.8, 0.9, 0.2, 0.7)),
        trigger_factor_values=_factor_rows("sweep_trigger", "trg:v1", (1.0, -0.2, 1.0, 0.6)),
        path_labels=_path_label_rows(setup.path_label),
        family_id="strategy-shaped-fixture-family",
        family_budget=2,
        surrogate_run_count=3,
        variant_id="baseline",
        created_at="2026-01-02T15:00:00Z",
    )

    assert readout.stamp == EXPLORATORY_STAMP
    assert readout.promotion_eligible is False
    assert readout.outcome_source == "materialized_path_labels"
    assert readout.context_factor_id == "range_context"
    assert readout.trigger_factor_id == "sweep_trigger"
    assert readout.observation_counts["aligned_observation_count"] == 4
    assert readout.observation_counts["conditioned_observation_count"] == 3
    assert (
        readout.diagnostics["target_before_stop_probability"][
            "target_before_stop_probability"
        ]
        == pytest.approx(0.5)
    )
    assert readout.diagnostics["post_event_mfe_mae"]["event_count"] == 2
    assert readout.diagnostics["post_event_mfe_mae"]["mean_mfe"] == pytest.approx(0.04)
    assert readout.variant_ledger_binding["family_budget_check"]["status"] == "RESPECTED"
    assert readout.surrogate_fdr_gate["threshold_verdict"] == "zero-pass-met"
    assert readout.power["scope"] == "per_factor"
    assert readout.power["factor_id"] == "sweep_trigger"
    assert readout.power["minimum_detectable_abs_ic"] is not None


def test_setup_probe_discounts_power_n_eff_for_overlapping_outcome() -> None:
    # A forward-overlapping path outcome at horizon H makes consecutive conditioned
    # observations overlap ~H bars, so the IC-power N_eff must be the overlap-aware
    # estimate_n_eff discount (~conditioned/H), strictly less than the raw count.
    from alpha_system.runtime.diagnostics.splits.n_eff import estimate_n_eff

    setup = _setup_spec()
    common = {
        "context_factor_values": _factor_rows("range_context", "ctx:v1", (0.8, 0.9, 0.2, 0.7)),
        "trigger_factor_values": _factor_rows("sweep_trigger", "trg:v1", (1.0, -0.2, 1.0, 0.6)),
        "path_labels": _path_label_rows(setup.path_label),
        "family_id": "strategy-shaped-fixture-family",
        "family_budget": 2,
        "surrogate_run_count": 3,
        "variant_id": "baseline",
        "created_at": "2026-01-02T15:00:00Z",
    }

    raw = evaluate_setup_conditional_probe(setup, **common)
    conditioned = raw.observation_counts["conditioned_observation_count"]
    assert raw.power["n_eff"] == conditioned

    horizon_bars = 3
    discounted = evaluate_setup_conditional_probe(
        setup, outcome_overlap_bars=horizon_bars, **common
    )
    expected = estimate_n_eff(
        conditioned,
        {
            "horizon_bars": horizon_bars,
            "sampling_cadence_bars": 1,
            "discount_factor": horizon_bars,
        },
        purge_gap=0,
        embargo_gap=0,
    ).n_eff
    assert discounted.power["n_eff"] == expected
    assert discounted.power["n_eff"] < conditioned
    # A single-bar (non-overlapping) horizon has nothing to discount.
    no_overlap = evaluate_setup_conditional_probe(setup, outcome_overlap_bars=1, **common)
    assert no_overlap.power["n_eff"] == conditioned


def test_setup_probe_compiler_rejects_context_equal_trigger() -> None:
    setup = _setup_spec(
        entry_context={
            "factor_id": "same_factor",
            "factor_version": "v1",
            "operator": ">=",
            "threshold": 0.5,
        },
        event_trigger={
            "factor_id": "same_factor",
            "factor_version": "v1",
            "operator": ">=",
            "threshold": 0.5,
            "variant_note": "syntactically different but same factor",
        },
    )

    with pytest.raises(ConditionalProbeError, match="separate factors"):
        compile_setup_spec_to_conditional_probe(setup)


def test_setup_probe_fails_closed_on_family_budget_overrun() -> None:
    setup = _setup_spec()
    existing = build_probe_variant_ledger_record(
        setup,
        variant_id="strict-confirmation",
        family_id="strategy-shaped-fixture-family",
        created_at="2026-01-02T14:59:00Z",
    )

    with pytest.raises(ConditionalProbeError, match="family budget"):
        evaluate_setup_conditional_probe(
            setup,
            context_factor_values=_factor_rows("range_context", "ctx:v1", (0.8,)),
            trigger_factor_values=_factor_rows("sweep_trigger", "trg:v1", (1.0,)),
            path_labels=_path_label_rows(setup.path_label, count=1),
            family_id="strategy-shaped-fixture-family",
            family_budget=1,
            surrogate_run_count=3,
            variant_id="baseline",
            existing_variant_records=(existing,),
            created_at="2026-01-02T15:00:00Z",
        )


def test_setup_probe_fails_closed_without_surrogate_zero_pass() -> None:
    setup = _setup_spec()

    with pytest.raises(ConditionalProbeError, match="ZERO_PASS_MET"):
        evaluate_setup_conditional_probe(
            setup,
            context_factor_values=_factor_rows("range_context", "ctx:v1", (0.8,)),
            trigger_factor_values=_factor_rows("sweep_trigger", "trg:v1", (1.0,)),
            path_labels=_path_label_rows(setup.path_label, count=1),
            family_id="strategy-shaped-fixture-family",
            family_budget=2,
            surrogate_run_count=3,
            surrogate_gate_pass_count=1,
            variant_id="baseline",
            created_at="2026-01-02T15:00:00Z",
        )


# Reference simulation / value-accounting engines that the research package must
# never import — directly or by-name. Guards the "no second PnL/value truth" rail
# (AGENTS.md Hard Constraints): value/accounting math lives only in the sanctioned
# reference engine, and research/ imports zero backtest/management/fast_path engines
# nor the sanctioned value sink (core.value_store). Matched on dotted module-path
# *components* and imported *names*, so dotted submodules
# (`import alpha_system.backtest.fast_path`), the value sink
# (`from alpha_system.core import value_store`), aliased, and parenthesized
# multi-line import forms are all caught.
_FORBIDDEN_ENGINE_MODULES = frozenset(
    {"backtest", "management", "fast_path", "value_store"}
)


def _forbidden_engine_imports(source: str) -> list[str]:
    """Return import statements in ``source`` that pull in a reference sim/value engine.

    AST-based rather than line-regex based: a regex over import lines silently
    misses dotted submodules (``import alpha_system.backtest.fast_path``),
    parent-imports of the engine name (``from alpha_system.core import value_store``),
    ``as`` aliases, and parenthesized multi-line imports. Parsing the module catches
    every import syntax by construction.
    """
    offenders: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if set(alias.name.split(".")) & _FORBIDDEN_ENGINE_MODULES:
                    offenders.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported = {alias.name for alias in node.names}
            if (set(module.split(".")) & _FORBIDDEN_ENGINE_MODULES) or (
                imported & _FORBIDDEN_ENGINE_MODULES
            ):
                offenders.append(f"from {module} import {', '.join(sorted(imported))}")
    return offenders


def test_research_package_has_no_sim_bridge_imports() -> None:
    offenders: list[str] = []
    for path in Path("src/alpha_system/research").rglob("*.py"):
        for statement in _forbidden_engine_imports(path.read_text(encoding="utf-8")):
            offenders.append(f"{path}: {statement}")

    assert offenders == []


# Regression pins for the guard itself: a future edit must not silently narrow it
# back to the line-regex coverage gap that let dotted submodules and the value sink
# evade detection (the V0-(A) rail gap found auditing the strategy-shaped lane).
@pytest.mark.parametrize(
    "snippet",
    [
        "import alpha_system.backtest.fast_path",
        "import alpha_system.backtest",
        "import alpha_system.management",
        "import alpha_system.fast_path",
        "import alpha_system.value_store",
        "import alpha_system.core.value_store",
        "import alpha_system.backtest as bt",
        "from alpha_system import backtest",
        "from alpha_system import value_store",
        "from alpha_system.core import value_store",
        "from alpha_system.backtest import management",
        "from alpha_system.backtest.fast_path import run_engine",
        "from alpha_system.research import (\n    foo,\n    value_store,\n)",
    ],
)
def test_sim_bridge_guard_catches_reference_engine_imports(snippet: str) -> None:
    assert _forbidden_engine_imports(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from alpha_system.research.conditional_probe import "
        "compile_setup_spec_to_conditional_probe",
        "from alpha_system.governance.setup_spec import SetupSpec",
        "import alpha_system.research.first_light",
        # forbidden token only as a substring of a legitimately-named symbol/module
        "from alpha_system.research import backtest_summary",
        "import alpha_system.core.value_store_helpers",
        "x = 'this module does not import the backtest engine'",
    ],
)
def test_sim_bridge_guard_ignores_legitimate_imports(snippet: str) -> None:
    assert _forbidden_engine_imports(snippet) == [], snippet


def _setup_spec(
    *,
    entry_context: dict[str, object] | None = None,
    event_trigger: dict[str, object] | None = None,
) -> SetupSpec:
    path_label_id = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "path", "name": "target_before_stop", "version": 1},
    )
    mechanism_id = create_mechanism_card(
        source="SSRL-P02 synthetic conditional probe fixture",
        rationale=(
            "A compressed context can make a later reclaim event informative "
            "without using the same factor for both conditions."
        ),
        expected_mechanism=(
            "The context gates when the setup is relevant and the trigger "
            "marks the separate entry event inside that bucket."
        ),
        expected_direction="long path outcome after reclaim trigger",
        horizon="120m",
        session="RTH",
        required_features=["range_context", "sweep_trigger"],
        required_labels=["path_target_before_stop"],
        cost_sensitivity={"policy": "exploratory only; no promotion evidence"},
        variant_budget=2,
        duplicate_exposure={"status": "checked", "note": "fixture unique"},
    ).mechanism_id
    return create_setup_spec(
        entry_context=entry_context
        or {
            "factor_id": "range_context",
            "factor_version": "ctx:v1",
            "value_field": "normalized_value",
            "operator": ">=",
            "threshold": 0.5,
        },
        event_trigger=event_trigger
        or {
            "factor_id": "sweep_trigger",
            "factor_version": "trg:v1",
            "value_field": "normalized_value",
            "operator": ">",
            "threshold": 0.0,
        },
        regime_filter={"session": "RTH", "policy": "regular session fixture only"},
        confirmation={"rule": "fixture confirmation declared before readout"},
        invalidation={"rule": "fixture invalidation declared before readout"},
        stop={"binding": "fixed stop from governed path label"},
        target={"binding": "fixed target from governed path label"},
        hold_time={"max_minutes": 120, "policy": "fixed path-label horizon"},
        horizon="120m",
        path_label=path_label_id,
        allowed_variants=["baseline", "strict-confirmation"],
        forbidden_post_hoc_changes=[
            "Do not change context buckets after reading outcomes.",
            "Do not change target or stop binding after reading outcomes.",
        ],
        mechanism_id=mechanism_id,
    )


def _factor_rows(
    factor_id: str,
    factor_version: str,
    values: tuple[float, ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        rows.append(
            {
                "factor_id": factor_id,
                "factor_version": factor_version,
                "instrument_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": "XNYS:2026-01-02:regular",
                "bar_index": index + 1,
                "value": value,
                "normalized_value": value,
                "quality_flags": ["synthetic"],
                "data_version": "data:v1",
                "compute_version": "test",
            }
        )
    return tuple(rows)


def _path_label_rows(path_label: str, *, count: int = 4) -> tuple[dict[str, object], ...]:
    target_values = (True, False, True, False)
    mfe_values = (0.05, 0.02, 0.01, 0.03)
    mae_values = (-0.01, -0.03, -0.02, -0.04)
    rows: list[dict[str, object]] = []
    for index in range(count):
        event_ts = _event_ts(index)
        rows.extend(
            [
                _label_row(path_label, event_ts, "target_before_stop", target_values[index]),
                _label_row(path_label, event_ts, "mfe_by_horizon", mfe_values[index]),
                _label_row(path_label, event_ts, "mae_by_horizon", mae_values[index]),
            ]
        )
    return tuple(rows)


def _label_row(
    path_label: str,
    event_ts: datetime,
    label_type: str,
    value: bool | float,
) -> dict[str, object]:
    horizon_end = event_ts + timedelta(minutes=30)
    return {
        "label_id": path_label,
        "instrument_id": "SYNTH",
        "event_ts": _text(event_ts),
        "horizon": 1800,
        "label_type": label_type,
        "value": value,
        "path_metadata": {
            "session_id": "XNYS:2026-01-02:regular",
            "label_version": "labels:v1",
            "horizon_end_ts": _text(horizon_end),
            "required_future_bars": 30,
            "observed_future_bars": 30,
            "entry_bar_index": 1,
            "target_hit_bar_index": 3,
            "path_label_binding": path_label,
        },
        "data_version": "data:v1",
        "label_available_ts": _text(horizon_end + timedelta(seconds=1)),
    }


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
