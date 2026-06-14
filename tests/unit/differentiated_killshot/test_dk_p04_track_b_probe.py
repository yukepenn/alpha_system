"""DK-P04 Track B context!=trigger EXPLORATORY probe harness tests.

Covers:
- the SetupSpec compiles with genuinely distinct context vs trigger (C1);
- ``context.factor_id == trigger.factor_id`` is rejected at compile time;
- the tools-side harness injects rows and the probe returns an EXPLORATORY
  readout with ``promotion_eligible = False``, ``ZERO_PASS_MET`` surrogate gate,
  a ``RESPECTED`` family-budget binding, and a per-factor power statement;
- the label-shuffle surrogate yields ``ZERO_PASS_MET`` on a clean fixture;
- ``reject_exploratory_promotion_artifact`` refuses the EVIDENCE artifact;
- the DATA_GAP fallback yields ``status = INCONCLUSIVE`` / ``issue_code = DATA_GAP``
  with no fabricated values;
- the committed EVIDENCE / SetupSpec / MechanismCard JSON are EXPLORATORY,
  promotion_eligible false, and declare genuinely distinct context and trigger;
- ``research/`` imports none of backtest/management/fast_path/value_store and the
  harness does not define a second PnL/value truth.
"""

from __future__ import annotations

import ast
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.setup_spec import create_setup_spec
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.research.conditional_probe import (
    ConditionalProbeError,
    compile_setup_spec_to_conditional_probe,
)
from tools.differentiated_killshot_v1.dk_p04_track_b_probe import (
    CONTEXT_FACTOR_ID,
    CONTEXT_FACTOR_VERSION,
    HORIZON_SECONDS,
    NORMALIZED_INSTRUMENT_ID,
    NORMALIZED_SESSION_ID,
    TRIGGER_FACTOR_ID,
    TRIGGER_FACTOR_VERSION,
    InjectedRows,
    build_data_gap_evidence,
    build_track_b_evidence,
    build_track_b_mechanism_card,
    build_track_b_setup_spec,
    path_label_governance_id,
    run_label_shuffle_surrogate,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TRACK_B_DIR = _REPO_ROOT / "research" / "differentiated_substrate_v1" / "track_b"
_HARNESS = (
    _REPO_ROOT / "tools" / "differentiated_killshot_v1" / "dk_p04_track_b_probe.py"
)


# --------------------------------------------------------------------------- #
# C1: genuinely distinct context vs trigger.
# --------------------------------------------------------------------------- #


def test_setup_spec_compiles_with_distinct_context_and_trigger() -> None:
    setup = build_track_b_setup_spec()
    probe = compile_setup_spec_to_conditional_probe(setup)
    assert probe.context.factor_id == CONTEXT_FACTOR_ID
    assert probe.trigger.factor_id == TRIGGER_FACTOR_ID
    assert probe.context.factor_id != probe.trigger.factor_id
    # Different underlying signals, not just different names.
    assert setup.entry_context["signal_kind"] != setup.event_trigger["signal_kind"]
    assert setup.stamp == EXPLORATORY_STAMP


def test_compiler_rejects_context_equal_trigger() -> None:
    # A SetupSpec that declares distinct *content* but the SAME underlying factor
    # for context and trigger passes the SetupSpec validator (which only checks
    # declared distinctness) yet must fail closed at compile time: the compiler
    # enforces ``context.factor_id == trigger.factor_id`` numeric identity.
    mechanism = build_track_b_mechanism_card()
    same_factor_setup = create_setup_spec(
        entry_context={
            "factor_id": CONTEXT_FACTOR_ID,
            "factor_version": CONTEXT_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">=",
            "threshold": 0.5,
            "bucket": "context_bucket",
        },
        event_trigger={
            "factor_id": CONTEXT_FACTOR_ID,
            "factor_version": CONTEXT_FACTOR_VERSION,
            "value_field": "normalized_value",
            "operator": ">",
            "threshold": 0.0,
            "event": "syntactically_distinct_same_factor",
        },
        regime_filter={"session": "RTH", "instrument_root": "ES"},
        confirmation={"policy": "none_added", "fixed_before_readout": True},
        invalidation={"policy": "fixed", "fixed_before_readout": True},
        stop={"binding": "fixed_stop_from_path_label", "geometry": "unchanged"},
        target={"path_outcome": "target_before_stop", "geometry": "unchanged"},
        hold_time={"max_minutes": 120, "horizon": "120m"},
        horizon="120m",
        path_label=path_label_governance_id(),
        allowed_variants=["same_factor_variant"],
        forbidden_post_hoc_changes=["No changes after readout."],
        mechanism_id=mechanism.mechanism_id,
        stamp=EXPLORATORY_STAMP,
    )
    with pytest.raises(ConditionalProbeError, match="separate factors"):
        compile_setup_spec_to_conditional_probe(same_factor_setup)


# --------------------------------------------------------------------------- #
# Injected-row probe readout (EXPLORATORY, ZERO_PASS_MET, RESPECTED, power).
# --------------------------------------------------------------------------- #


def _event_ts(index: int) -> datetime:
    return datetime(2024, 6, 3, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _factor_rows(factor_id: str, factor_version: str, values: tuple[float, ...]) -> list[dict]:
    rows: list[dict] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        rows.append(
            {
                "factor_id": factor_id,
                "factor_version": factor_version,
                "instrument_id": NORMALIZED_INSTRUMENT_ID,
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "session_id": NORMALIZED_SESSION_ID,
                "data_version": "dsv_fixture",
                "bar_index": index,
                "value": value,
                "normalized_value": value,
            }
        )
    return rows


def _label_rows(
    path_label: str,
    target_values: tuple[bool, ...],
    mfe_values: tuple[float, ...],
    mae_values: tuple[float, ...],
) -> list[dict]:
    rows: list[dict] = []
    for index, target in enumerate(target_values):
        event_ts = _event_ts(index)
        horizon_end = event_ts + timedelta(seconds=HORIZON_SECONDS)
        common = {
            "instrument_id": NORMALIZED_INSTRUMENT_ID,
            "event_ts": _text(event_ts),
            "horizon": HORIZON_SECONDS,
            "data_version": "dsv_fixture",
            "label_available_ts": _text(horizon_end + timedelta(seconds=1)),
            "path_metadata": {
                "session_id": NORMALIZED_SESSION_ID,
                "label_version": "fixture_v1",
                "horizon_end_ts": _text(horizon_end),
                "path_label": path_label,
                "required_future_bars": 120,
                "observed_future_bars": 120,
                "insufficient_future": False,
            },
            "label_id": path_label,
        }
        rows.append({**common, "label_type": "target_before_stop", "value": target})
        rows.append({**common, "label_type": "mfe_by_horizon", "value": mfe_values[index]})
        rows.append({**common, "label_type": "mae_by_horizon", "value": mae_values[index]})
    return rows


def _injected_with_variance() -> InjectedRows:
    # The context (>= 0.5) perfectly predicts the target outcome among events, so
    # the observed conditional uplift is maximal and no label shuffle can strictly
    # exceed it -> 0 surrogate passes -> ZERO_PASS_MET. All rows fire the trigger.
    path_label = path_label_governance_id()
    return InjectedRows(
        context_factor_values=_factor_rows(
            CONTEXT_FACTOR_ID, CONTEXT_FACTOR_VERSION, (0.8, 0.9, 0.2, 0.7)
        ),
        trigger_factor_values=_factor_rows(
            TRIGGER_FACTOR_ID, TRIGGER_FACTOR_VERSION, (1.0, 1.0, 1.0, 1.0)
        ),
        path_labels=_label_rows(
            path_label,
            target_values=(True, True, False, True),
            mfe_values=(0.05, 0.02, 0.01, 0.03),
            mae_values=(-0.01, -0.03, -0.02, -0.04),
        ),
    )


def test_label_shuffle_surrogate_yields_zero_pass_met() -> None:
    setup = build_track_b_setup_spec()
    gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=_injected_with_variance(),
        surrogate_runs=32,
        base_seed=0,
    )
    assert gate["run_count"] == 32
    assert gate["gate_pass_count"] == 0
    assert gate["error_count"] == 0
    assert gate["threshold_verdict"] == "zero-pass-met"
    assert gate["promotion_evidence"] is False


def test_build_evidence_emits_exploratory_readout(monkeypatch, tmp_path) -> None:
    injected = _injected_with_variance()

    monkeypatch.setattr(
        "tools.differentiated_killshot_v1.dk_p04_track_b_probe.load_injected_rows",
        lambda root: injected,
    )
    # ALPHA_DATA_ROOT must resolve to an existing dir so the gate is reached.
    evidence = build_track_b_evidence(alpha_data_root=tmp_path, surrogate_runs=16, base_seed=0)

    assert evidence["status"] == "RECORDED"
    assert evidence["stamp"] == EXPLORATORY_STAMP
    assert evidence["promotion_eligible"] is False
    assert evidence["outcome_source"] == "materialized_path_labels"
    assert evidence["surrogate_fdr_gate"]["threshold_verdict"] == "zero-pass-met"
    assert evidence["variant_ledger_binding"]["family_budget_check"]["status"] == "RESPECTED"
    assert evidence["power"]["scope"] == "per_factor"
    assert evidence["power"]["factor_id"] == TRIGGER_FACTOR_ID
    assert evidence["power"]["minimum_detectable_abs_ic"] is not None
    diagnostics = evidence["diagnostics"]
    assert "target_before_stop_probability" in diagnostics
    assert "post_event_mfe_mae" in diagnostics
    assert evidence["row_access"]["fabricated_values"] is False


def test_build_evidence_data_gap_when_root_missing() -> None:
    evidence = build_track_b_evidence(
        alpha_data_root="/nonexistent/dk_p04/data/root",
        surrogate_runs=8,
        base_seed=0,
    )
    assert evidence["status"] == "INCONCLUSIVE"
    assert evidence["issue_code"] == "DATA_GAP"
    assert evidence["stamp"] == EXPLORATORY_STAMP
    assert evidence["promotion_eligible"] is False
    assert evidence["surrogate_fdr_gate"]["gate_status"] == "BLOCKED"
    assert evidence["power"]["n_eff"] == 0
    assert evidence["row_access"]["fabricated_values"] is False


def test_data_gap_evidence_has_no_fabricated_values() -> None:
    evidence = build_data_gap_evidence(alpha_data_root=None, reason="unit fixture")
    assert evidence["status"] == "INCONCLUSIVE"
    assert evidence["issue_code"] == "DATA_GAP"
    assert evidence["power"]["n_eff"] == 0
    assert evidence["power"]["se_ic"] is None
    assert evidence["power"]["mde_abs_ic"] is None
    assert evidence["row_access"]["fabricated_values"] is False


# --------------------------------------------------------------------------- #
# EXPLORATORY quarantine.
# --------------------------------------------------------------------------- #


def test_evidence_is_refused_by_promotion_path(monkeypatch, tmp_path) -> None:
    injected = _injected_with_variance()
    monkeypatch.setattr(
        "tools.differentiated_killshot_v1.dk_p04_track_b_probe.load_injected_rows",
        lambda root: injected,
    )
    evidence = build_track_b_evidence(alpha_data_root=tmp_path, surrogate_runs=8, base_seed=0)
    with pytest.raises(GovernanceValidationError) as excinfo:
        reject_exploratory_promotion_artifact(evidence, field="promotion_artifact")
    codes = {issue.code for issue in excinfo.value.issues}
    assert EXPLORATORY_PROMOTION_REFUSAL_CODE in codes


def test_data_gap_evidence_is_refused_by_promotion_path() -> None:
    evidence = build_data_gap_evidence(alpha_data_root=None, reason="unit fixture")
    with pytest.raises(GovernanceValidationError):
        reject_exploratory_promotion_artifact(evidence, field="promotion_artifact")


# --------------------------------------------------------------------------- #
# Committed artifacts.
# --------------------------------------------------------------------------- #


def test_committed_evidence_is_exploratory_and_not_promotable() -> None:
    evidence = json.loads((_TRACK_B_DIR / "EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["stamp"] == EXPLORATORY_STAMP
    assert evidence["promotion_eligible"] is False
    assert evidence["setup_spec"]["entry_context"]["factor_id"] != (
        evidence["setup_spec"]["event_trigger"]["factor_id"]
    )
    with pytest.raises(GovernanceValidationError):
        reject_exploratory_promotion_artifact(evidence, field="promotion_artifact")


def test_committed_setup_and_mechanism_match_builders() -> None:
    setup = json.loads((_TRACK_B_DIR / "setup_spec.json").read_text(encoding="utf-8"))
    mechanism = json.loads((_TRACK_B_DIR / "mechanism_card.json").read_text(encoding="utf-8"))
    assert setup == build_track_b_setup_spec().to_dict()
    assert mechanism == build_track_b_mechanism_card().to_dict()
    assert setup["stamp"] == EXPLORATORY_STAMP
    assert mechanism["stamp"] == EXPLORATORY_STAMP


def test_committed_evidence_is_value_free() -> None:
    blob = (_TRACK_B_DIR / "EVIDENCE.json").read_text(encoding="utf-8")
    # No raw value-store rows, no absolute data root, no DB / parquet payloads.
    for forbidden in ("value_json", "entity_id", "series_databento", ".sqlite", "/home/"):
        assert forbidden not in blob, forbidden


# --------------------------------------------------------------------------- #
# No-second-PnL rail: research/ clean; harness defines no PnL truth.
# --------------------------------------------------------------------------- #


_FORBIDDEN_ENGINE_MODULES = frozenset({"backtest", "management", "fast_path"})


def _imported_modules(source: str) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_harness_does_not_import_reference_sim_engines() -> None:
    modules = _imported_modules(_HARNESS.read_text(encoding="utf-8"))
    for module in modules:
        components = set(module.split("."))
        assert not (components & _FORBIDDEN_ENGINE_MODULES), module


def test_harness_defines_no_second_pnl_truth() -> None:
    source = _HARNESS.read_text(encoding="utf-8")
    assert "def compute_pnl" not in source
    assert "def build_equity_curve" not in source
    assert "realized_pnl" not in source


def test_research_track_b_dir_has_no_python_modules() -> None:
    # The pure research package must gain no .py (only value-free JSON here); the
    # value loader lives on the tools side.
    py_files = list(_TRACK_B_DIR.rglob("*.py"))
    assert py_files == [], py_files
