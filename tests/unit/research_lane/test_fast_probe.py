from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from alpha_system.data.storage import DataDependencyError
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP, create_mechanism_card
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.governance.surrogate_run import ZERO_PASS_MET
from alpha_system.research_lane import fast_probe as fast_probe_module
from alpha_system.research_lane.fast_probe import (
    InjectedRows,
    fast_probe,
    run_label_shuffle_surrogate,
)


def test_fast_probe_routes_main_effect_to_factor_diagnostics(monkeypatch, tmp_path) -> None:
    card = _mechanism_card()
    payload = _main_effect_slice(tmp_path)
    resolver = _Resolver()
    calls: dict[str, Any] = {}

    def fake_loader(path):
        text = path.as_posix()
        if text.endswith("factor.parquet"):
            return _feature_value_records((1.0, 2.0, 3.0, 4.0))
        if text.endswith("label.parquet"):
            return _main_label_value_records((0.01, 0.02, 0.03, 0.04))
        raise AssertionError(path)

    def fake_factor_run(**kwargs):
        calls["factor_kwargs"] = kwargs
        observations = list(kwargs["observations"])
        assert [row["factor_value"] for row in observations] == [1.0, 2.0, 3.0, 4.0]
        assert [row["label_value"] for row in observations] == [0.01, 0.02, 0.03, 0.04]
        return SimpleNamespace(
            report=SimpleNamespace(to_dict=lambda: {"report_type": "FactorDiagnosticsReport"}),
            record=SimpleNamespace(to_dict=lambda: {"status": "DIAGNOSTICS_COMPLETE"}),
        )

    monkeypatch.setattr(fast_probe_module, "load_parquet_values", fake_loader)
    monkeypatch.setattr(fast_probe_module, "build_factor_diagnostics_run", fake_factor_run)

    result = fast_probe(card, None, payload, resolver=resolver, env={})

    assert result["status"] == "RECORDED"
    assert result["study_kind"] == "main_effect"
    assert result["promotion_eligible"] is False
    assert result["engine"] == "build_factor_diagnostics_run"
    assert result["readout"]["factor_diagnostics_report"]["report_type"] == (
        "FactorDiagnosticsReport"
    )
    assert result["row_access"]["fabricated_values"] is False
    assert calls["factor_kwargs"]["lineage_refs"]["factor_id"] == "main_factor"
    assert resolver.feature_calls == [
        {
            "refs": ("fver_main",),
            "dataset": "dsv_fixture",
            "feature_request_ids": ("freq_main",),
            "partition_id": "partition_fixture",
            # exploratory lane opts in to horizon-agnostic feature partitions
            "allow_horizon_agnostic_partition": True,
        }
    ]
    assert resolver.label_calls == [
        {
            "refs": ("lver_main",),
            "dataset": "dsv_fixture",
            "label_spec_ids": ("lspec_main",),
            "partition_id": "partition_fixture",
        }
    ]


def test_fast_probe_routes_context_probe_and_exercises_surrogate_gate(
    monkeypatch,
    tmp_path,
) -> None:
    card = _mechanism_card()
    setup = _setup_spec(card)
    payload = _context_slice(tmp_path, setup)
    resolver = _Resolver()
    calls: dict[str, Any] = {}
    original_evaluate = fast_probe_module.evaluate_setup_conditional_probe

    def wrapped_evaluate(*args, **kwargs):
        calls["evaluate_kwargs"] = kwargs
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(fast_probe_module, "load_parquet_values", _context_loader(setup))
    monkeypatch.setattr(fast_probe_module, "evaluate_setup_conditional_probe", wrapped_evaluate)

    result = fast_probe(card, setup, payload, resolver=resolver, env={})

    assert result["status"] == "RECORDED"
    assert result["study_kind"] == "context_not_equal_trigger"
    assert result["promotion_eligible"] is False
    assert result["readout"]["promotion_eligible"] is False
    assert result["engine"] == "evaluate_setup_conditional_probe"
    assert result["surrogate_fdr_gate"]["run_count"] == 8
    assert result["surrogate_fdr_gate"]["gate_pass_count"] == 0
    assert result["surrogate_fdr_gate"]["error_count"] == 0
    assert result["surrogate_fdr_gate"]["threshold_verdict"] == "zero-pass-met"
    assert result["variant_ledger_binding"]["family_budget_check"]["status"] == "RESPECTED"
    assert calls["evaluate_kwargs"]["surrogate_run_count"] == 8
    assert calls["evaluate_kwargs"]["surrogate_gate_pass_count"] == 0
    assert calls["evaluate_kwargs"]["surrogate_error_count"] == 0
    assert calls["evaluate_kwargs"]["family_budget"] == 2
    assert result["row_access"]["fabricated_values"] is False
    assert resolver.feature_calls
    assert resolver.label_calls


def test_fast_probe_context_probe_uses_continuous_outcome_when_binary_is_degenerate(
    monkeypatch,
    tmp_path,
) -> None:
    # The bool target_before_stop path is degenerate (single class), which the
    # binary class-balance guard rejects. Selecting the continuous mfe_by_horizon
    # outcome unblocks fair setup testing: the lane runs through the surrogate +
    # conditional probe to a RECORDED, non-DATA_GAP, non-CALIBRATION_BLOCKED readout.
    card = _mechanism_card()
    setup = _setup_spec(card)
    payload = _context_slice(tmp_path, setup)
    payload["outcome_label_type"] = "mfe_by_horizon"
    resolver = _Resolver()
    calls: dict[str, Any] = {}
    original_evaluate = fast_probe_module.evaluate_setup_conditional_probe

    def wrapped_evaluate(*args, **kwargs):
        calls["evaluate_kwargs"] = kwargs
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        fast_probe_module,
        "load_parquet_values",
        _context_loader(setup, degenerate_binary=True),
    )
    monkeypatch.setattr(fast_probe_module, "evaluate_setup_conditional_probe", wrapped_evaluate)

    result = fast_probe(card, setup, payload, resolver=resolver, env={})

    assert result["status"] == "RECORDED"
    assert result.get("issue_code") != "DATA_GAP"
    assert result["surrogate_fdr_gate"]["threshold_verdict"] == "zero-pass-met"
    assert result["engine"] == "evaluate_setup_conditional_probe"
    # The selector was threaded into both engines.
    assert calls["evaluate_kwargs"]["outcome_label_type"] == "mfe_by_horizon"
    # The continuous conditioned-mean lift diagnostic is present.
    assert (
        result["readout"]["diagnostics"]["continuous_outcome_mean_lift"]["outcome_label_type"]
        == "mfe_by_horizon"
    )


def test_fast_probe_data_gap_on_missing_polars_never_calls_scoring(monkeypatch, tmp_path) -> None:
    card = _mechanism_card()
    payload = _main_effect_slice(tmp_path)

    def unavailable_loader(path):
        raise DataDependencyError("polars unavailable")

    def forbidden_scoring(**kwargs):
        raise AssertionError("scoring path should not be called on DATA_GAP")

    monkeypatch.setattr(fast_probe_module, "load_parquet_values", unavailable_loader)
    monkeypatch.setattr(fast_probe_module, "build_factor_diagnostics_run", forbidden_scoring)

    result = fast_probe(card, None, payload, resolver=_Resolver(), env={})

    assert result["status"] == "INCONCLUSIVE"
    assert result["issue_code"] == "DATA_GAP"
    assert result["promotion_eligible"] is False
    assert result["row_access"]["fabricated_values"] is False
    assert result["surrogate_fdr_gate"]["gate_status"] == "BLOCKED"
    assert result["power"]["n_eff"] == 0


def test_fast_probe_data_gap_on_missing_data_root_never_calls_loader(monkeypatch, tmp_path) -> None:
    card = _mechanism_card()
    payload = _main_effect_slice(tmp_path / "missing-root")

    def forbidden_loader(path):
        raise AssertionError("loader should not be called when root is missing")

    monkeypatch.setattr(fast_probe_module, "load_parquet_values", forbidden_loader)

    result = fast_probe(card, None, payload, resolver=_Resolver(), env={})

    assert result["status"] == "INCONCLUSIVE"
    assert result["issue_code"] == "DATA_GAP"
    assert "does not resolve" in result["row_access"]["reason"]
    assert result["row_access"]["fabricated_values"] is False


def test_fast_probe_does_not_bypass_nonzero_surrogate_pass(monkeypatch, tmp_path) -> None:
    card = _mechanism_card()
    setup = _setup_spec(card)
    payload = _context_slice(tmp_path, setup)

    monkeypatch.setattr(fast_probe_module, "load_parquet_values", _context_loader(setup))
    monkeypatch.setattr(
        fast_probe_module,
        "run_label_shuffle_surrogate",
        lambda **kwargs: fast_probe_module.build_surrogate_zero_pass_gate(
            run_count=3,
            gate_pass_count=1,
            error_count=0,
        ),
    )

    # A non-met surrogate-FDR gate (nonzero shuffled-label passes) is an HONEST null,
    # not an error: fast_probe records INCONCLUSIVE and routes to memory, and never
    # produces a tradable readout (promotion stays False, no conditional-probe metric).
    result = fast_probe(card, setup, payload, resolver=_Resolver(), env={})
    assert result["status"] == "INCONCLUSIVE"
    assert result["promotion_eligible"] is False
    assert result["issue_code"] != ZERO_PASS_MET
    # the gate is NOT bypassed: the real surrogate gate is carried; no metric produced
    assert result["surrogate_fdr_gate"]["gate_pass_count"] == 1
    assert "readout" not in result


def test_fast_probe_source_has_no_materialization_or_scaleout_driver_call() -> None:
    source = inspect.getsource(fast_probe_module)

    assert "scaleout" not in source
    assert "materialize_values" not in source
    assert "write_parquet_values" not in source
    assert "registry.write" not in source
    assert "pandas" not in source
    assert "numpy" not in source


def test_main_effect_overlap_metadata_uses_label_horizon_bars() -> None:
    meta = fast_probe_module._main_effect_overlap_metadata(
        SimpleNamespace(required_future_bars=60, label_version_bindings=())
    )

    assert meta == {
        "horizon_bars": 60,
        "sampling_cadence_bars": 1,
        "discount_factor": 60,
        "metadata_source": "fast_probe_main_effect_label_horizon",
    }


def test_main_effect_overlap_metadata_single_bar_label_has_no_discount() -> None:
    # A genuinely single-bar-ahead forward label has no overlap to discount, so
    # block size 1 / discount_factor 1 is honest -- but the metadata is still
    # supplied (never None / raw rows): the discount path is exercised, the
    # discount just happens to be 1.
    meta = fast_probe_module._main_effect_overlap_metadata(
        SimpleNamespace(required_future_bars=1, label_version_bindings=())
    )

    assert meta == {
        "horizon_bars": 1,
        "sampling_cadence_bars": 1,
        "discount_factor": 1,
        "metadata_source": "fast_probe_main_effect_label_horizon",
    }


def test_main_effect_overlap_metadata_fails_closed_when_horizon_unknown() -> None:
    # The main-effect outcome is forward-overlapping by construction. When the
    # forward horizon cannot be derived (required_future_bars unset) the helper
    # MUST fail closed rather than silently fall back to raw rows / discount 1
    # (the ratified #474 law) -- the latent silent-raw regression.
    import pytest

    from alpha_system.runtime.diagnostics.splits.n_eff import NEffSampleReportingError

    with pytest.raises(NEffSampleReportingError):
        fast_probe_module._main_effect_overlap_metadata(
            SimpleNamespace(required_future_bars=None, label_version_bindings=())
        )


def _autocorrelated_overlap_injected(setup: SetupSpec, *, n_bars: int, horizon_bars: int):
    """Inject a strongly forward-autocorrelated continuous path outcome.

    The path outcome is a slow ramp (consecutive bar-spaced values overlap and
    move together, mimicking a forward-overlapping horizon label) and the context
    selects a single CONTIGUOUS upper-mid window of length ``horizon_bars``. The
    observed conditioned-mean lift is therefore moderate. A ROW-level shuffle
    scatters the ramp so the conditioned mean regresses to the global mean and the
    observed lift is almost never exceeded (spurious ZERO_PASS_MET); a fixed-block
    shuffle keeps whole rising blocks intact, restoring the null's tail.
    """

    window_start = 4 * horizon_bars
    base_ts = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
    context_rows: list[dict[str, Any]] = []
    trigger_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    for index in range(n_bars):
        event_ts = _text(base_ts + timedelta(minutes=index))
        in_window = window_start <= index < window_start + horizon_bars
        context_value = 0.9 if in_window else 0.1
        context_rows.append(
            {
                "factor_id": "context_factor",
                "factor_version": "ctx:v1",
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "available_ts": event_ts,
                "session_id": "TEST:SYNTH:RTH",
                "data_version": "dsv_fixture",
                "value": context_value,
                "normalized_value": context_value,
                "bar_index": index + 1,
            }
        )
        trigger_rows.append(
            {
                "factor_id": "trigger_factor",
                "factor_version": "trg:v1",
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "available_ts": event_ts,
                "session_id": "TEST:SYNTH:RTH",
                "data_version": "dsv_fixture",
                "value": 1.0,
                "normalized_value": 1.0,
                "bar_index": index + 1,
            }
        )
        path_rows.append(
            {
                "label_id": setup.path_label,
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "horizon": 7200,
                "label_type": "mfe_by_horizon",
                "value": float(index),
                "path_metadata": {
                    "session_id": "TEST:SYNTH:RTH",
                    "label_version": "fixture_labels_v1",
                    "horizon_end_ts": event_ts,
                    "required_future_bars": horizon_bars,
                    "observed_future_bars": horizon_bars,
                    "path_label_binding": setup.path_label,
                },
                "data_version": "dsv_fixture",
                "label_available_ts": event_ts,
            }
        )
    return InjectedRows(
        feature_rows_by_role={
            "context": tuple(context_rows),
            "trigger": tuple(trigger_rows),
        },
        label_rows_by_role={"path": tuple(path_rows)},
    )


def test_block_shuffle_restores_null_variance_for_overlapping_outcome() -> None:
    # On a strongly forward-autocorrelated path outcome a ROW-level shuffle destroys
    # the overlap autocorrelation, collapses the null tail, and trivially passes the
    # ZERO_PASS gate (spurious significance). A fixed non-overlapping BLOCK shuffle
    # keeps whole rising blocks intact, so the surrogate produces strictly more
    # exceedances and no longer trivially passes — the load-bearing validity proof.
    card = _mechanism_card()
    setup = _setup_spec(card)
    horizon_bars = 20
    injected = _autocorrelated_overlap_injected(setup, n_bars=120, horizon_bars=horizon_bars)

    row_gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=300,
        base_seed=0,
        outcome_label_type="mfe_by_horizon",
        block_size=1,
    )
    block_gate = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=300,
        base_seed=0,
        outcome_label_type="mfe_by_horizon",
        block_size=horizon_bars,
    )

    # Row shuffle falsely finds zero shuffled exceedances (spurious ZERO_PASS_MET).
    assert row_gate["gate_pass_count"] == 0
    assert row_gate["threshold_verdict"] == ZERO_PASS_MET
    # Block shuffle restores the null variance: strictly more exceedances, and the
    # gate is no longer trivially met.
    assert block_gate["gate_pass_count"] > row_gate["gate_pass_count"]
    assert block_gate["threshold_verdict"] != ZERO_PASS_MET


def test_label_shuffle_surrogate_block_size_one_matches_row_level_shuffle() -> None:
    # block_size <= 1 must be identical to the historical row-level shuffle: the
    # non-overlapping path is unchanged. Explicit block_size=1 and the default
    # (no block_size) must agree exactly.
    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _autocorrelated_overlap_injected(setup, n_bars=120, horizon_bars=20)

    explicit_one = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=64,
        base_seed=3,
        outcome_label_type="mfe_by_horizon",
        block_size=1,
    )
    default_block = run_label_shuffle_surrogate(
        setup=setup,
        injected=injected,
        surrogate_runs=64,
        base_seed=3,
        outcome_label_type="mfe_by_horizon",
    )
    assert explicit_one == default_block


def _net_excursion_injected(
    setup: SetupSpec,
    *,
    n_bars: int,
    horizon_bars: int,
    signed_drift: bool,
) -> InjectedRows:
    """Build a context!=trigger slice carrying mfe + mae rows per event.

    The first half of the bars is context-selected (context_factor >= 0.5); the
    rest is excluded. ``signed_drift=False`` makes each event volatility-only: a
    rising-magnitude excursion with mae = -mfe so the per-event net sum is ~0 and
    the conditioned net mean matches the base (no signed asymmetry, no net signal).
    ``signed_drift=True`` adds a positive directional drift ONLY to the
    context-selected rows, so the conditioned net mean is clearly positive while
    each excursion magnitude still varies (a genuine signed net edge).
    """

    import random as _random

    noise_rng = _random.Random(20260615)
    base_ts = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
    # Condition on a MINORITY of bars so the unconditioned base mean is dominated by
    # the non-selected events: a strong positive drift on the small conditioned set
    # then yields a positive lift whose magnitude no block-shuffle (which can only
    # move near-zero non-selected blocks into the conditioned window) can exceed.
    selected_cutoff = max(n_bars // 4, 1)
    context_rows: list[dict[str, Any]] = []
    trigger_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    for index in range(n_bars):
        event_ts = _text(base_ts + timedelta(minutes=index))
        selected = index < selected_cutoff
        context_value = 0.9 if selected else 0.1
        # A varying excursion magnitude keeps the conditioned outcome non-degenerate.
        # A zero-centered noisy wobble on the adverse leg makes the net sum vary
        # genuinely around ~0 (volatility-only: no signed drift), so a block-shuffle
        # null can produce conditioned means that exceed the ~zero observed lift.
        magnitude = 0.01 + 0.001 * (index % 7)
        wobble = noise_rng.uniform(-0.02, 0.02)
        mfe_value = magnitude
        mae_value = -magnitude + wobble
        if signed_drift and selected:
            # Signed directional edge confined to context: the favorable leg gets a
            # large positive drift ONLY on the minority conditioned set. Because the
            # base mean is set by the near-zero majority, the observed positive lift
            # has a wide margin no block-shuffle can exceed (a shuffle can only move
            # near-zero non-selected blocks into the small conditioned window). The
            # drift varies event-to-event, keeping the conditioned outcome non-degenerate.
            mfe_value += 0.3 + 0.01 * (index % 5)
        context_rows.append(
            {
                "factor_id": "context_factor",
                "factor_version": "ctx:v1",
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "available_ts": event_ts,
                "session_id": "TEST:SYNTH:RTH",
                "data_version": "dsv_fixture",
                "value": context_value,
                "normalized_value": context_value,
                "bar_index": index + 1,
            }
        )
        trigger_rows.append(
            {
                "factor_id": "trigger_factor",
                "factor_version": "trg:v1",
                "instrument_id": "SYNTH",
                "event_ts": event_ts,
                "available_ts": event_ts,
                "session_id": "TEST:SYNTH:RTH",
                "data_version": "dsv_fixture",
                "value": 1.0,
                "normalized_value": 1.0,
                "bar_index": index + 1,
            }
        )
        for label_type, value in (
            ("mfe_by_horizon", mfe_value),
            ("mae_by_horizon", mae_value),
        ):
            path_rows.append(
                {
                    "label_id": setup.path_label,
                    "instrument_id": "SYNTH",
                    "event_ts": event_ts,
                    "horizon": 7200,
                    "label_type": label_type,
                    "value": value,
                    "path_metadata": {
                        "session_id": "TEST:SYNTH:RTH",
                        "label_version": "fixture_labels_v1",
                        "horizon_end_ts": event_ts,
                        "required_future_bars": horizon_bars,
                        "observed_future_bars": horizon_bars,
                        "path_label_binding": setup.path_label,
                    },
                    "data_version": "dsv_fixture",
                    "label_available_ts": event_ts,
                }
            )
    return InjectedRows(
        feature_rows_by_role={
            "context": tuple(context_rows),
            "trigger": tuple(trigger_rows),
        },
        label_rows_by_role={"path": tuple(path_rows)},
    )


def test_net_excursion_surrogate_distinguishes_signed_drift_from_volatility() -> None:
    # A volatility-only fixture (mae = -mfe, net ~ 0) carries no signed asymmetry, so
    # the joint block-shuffle null is indistinguishable from the observed net lift and
    # the gate is NOT met. A fixture with a real positive signed net drift on the
    # conditioned set produces a robust observed lift the shuffled null cannot beat,
    # so the gate IS met. Same engine, same seed — only the signed structure differs.
    card = _mechanism_card()
    setup = _setup_spec(card)
    horizon_bars = 10

    flat = _net_excursion_injected(
        setup, n_bars=80, horizon_bars=horizon_bars, signed_drift=False
    )
    drifted = _net_excursion_injected(
        setup, n_bars=80, horizon_bars=horizon_bars, signed_drift=True
    )

    common = {
        "surrogate_runs": 200,
        "base_seed": 0,
        "outcome_label_type": "net_excursion",
        "block_size": horizon_bars,
    }
    flat_gate = run_label_shuffle_surrogate(setup=setup, injected=flat, **common)
    drift_gate = run_label_shuffle_surrogate(setup=setup, injected=drifted, **common)

    # Volatility-only net excursion: shuffled nulls exceed the ~zero observed lift, so
    # the gate is not trivially met (no distinguishable signed effect).
    assert flat_gate["gate_pass_count"] > 0
    assert flat_gate["threshold_verdict"] != ZERO_PASS_MET
    # Signed drift: the surrogate cannot beat the robust observed lift, gate is met.
    assert drift_gate["gate_pass_count"] == 0
    assert drift_gate["threshold_verdict"] == ZERO_PASS_MET


def test_net_excursion_joint_shuffle_preserves_mfe_mae_pairing() -> None:
    # The joint block-shuffle must apply ONE permutation order to BOTH the mfe and
    # mae rows in their own event-time order, so a given event's (mfe, mae) pair
    # always relocates to the SAME destination event together. We assert the rebuilt
    # rows reconstruct a coherent per-event pair for every event.
    import random as _random

    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _net_excursion_injected(
        setup, n_bars=40, horizon_bars=5, signed_drift=True
    )
    path_rows = list(injected.label_rows_by_role["path"])

    # Capture the original per-event (mfe, mae) pair set: the net surrogate must be a
    # permutation of WHOLE pairs, so the multiset of (mfe, mae) tuples is invariant.
    def _pairs(rows: list[dict[str, Any]]) -> list[tuple[float, float]]:
        by_ts: dict[str, dict[str, float]] = {}
        for row in rows:
            by_ts.setdefault(row["event_ts"], {})[row["label_type"]] = row["value"]
        return sorted(
            (vals["mfe_by_horizon"], vals["mae_by_horizon"]) for vals in by_ts.values()
        )

    target_rows_by_type = {
        "mfe_by_horizon": fast_probe_module._time_ordered_label_rows(
            path_rows, "mfe_by_horizon"
        ),
        "mae_by_horizon": fast_probe_module._time_ordered_label_rows(
            path_rows, "mae_by_horizon"
        ),
    }
    shared = fast_probe_module._shared_event_count(target_rows_by_type)
    rebuilt = fast_probe_module._rebuild_surrogate_path_rows(
        path_rows,
        target_rows_by_type=target_rows_by_type,
        shared_event_count=shared,
        block_size=5,
        rng=_random.Random(7),
    )

    # The set of whole (mfe, mae) pairs is preserved exactly: nothing is split,
    # dropped, or recombined across events.
    assert _pairs(rebuilt) == _pairs(path_rows)


def test_label_shuffle_surrogate_block_path_is_deterministic() -> None:
    # Same base_seed + same block_size must reproduce the surrogate gate exactly.
    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _autocorrelated_overlap_injected(setup, n_bars=120, horizon_bars=20)

    kwargs = {
        "setup": setup,
        "injected": injected,
        "surrogate_runs": 80,
        "base_seed": 11,
        "outcome_label_type": "mfe_by_horizon",
        "block_size": 20,
    }
    assert run_label_shuffle_surrogate(**kwargs) == run_label_shuffle_surrogate(**kwargs)


def test_label_shuffle_surrogate_parallel_matches_serial_block_path() -> None:
    # CORRECTNESS GUARD for the parallel refactor: the block-path surrogate gate
    # must be byte-identical whether the per-surrogate units run serially
    # (workers=1) or across a process pool (workers>1). Each surrogate reseeds
    # from base_seed + run_index, so the aggregate is order/worker independent.
    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _autocorrelated_overlap_injected(setup, n_bars=120, horizon_bars=20)

    common = {
        "setup": setup,
        "injected": injected,
        "surrogate_runs": 120,
        "base_seed": 7,
        "outcome_label_type": "mfe_by_horizon",
        "block_size": 20,
    }
    serial = run_label_shuffle_surrogate(**common, workers=1)
    parallel = run_label_shuffle_surrogate(**common, workers=4)
    assert serial == parallel
    # The gate fields the verdict consumes are present and identical.
    for field in ("gate_pass_count", "run_count", "error_count", "threshold_verdict"):
        assert serial[field] == parallel[field]


def test_label_shuffle_surrogate_parallel_matches_serial_legacy_row_path() -> None:
    # The legacy single-label row-shuffle path (block_size=1) must also be
    # byte-identical under parallel execution.
    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _autocorrelated_overlap_injected(setup, n_bars=120, horizon_bars=20)

    common = {
        "setup": setup,
        "injected": injected,
        "surrogate_runs": 96,
        "base_seed": 5,
        "outcome_label_type": "mfe_by_horizon",
        "block_size": 1,
    }
    assert run_label_shuffle_surrogate(**common, workers=1) == run_label_shuffle_surrogate(
        **common, workers=3
    )


def test_label_shuffle_surrogate_parallel_matches_serial_net_excursion() -> None:
    # The joint net_excursion path (two label_types, one shared permutation) must
    # be byte-identical under parallel execution.
    card = _mechanism_card()
    setup = _setup_spec(card)
    injected = _net_excursion_injected(
        setup, n_bars=120, horizon_bars=20, signed_drift=True
    )

    common = {
        "setup": setup,
        "injected": injected,
        "surrogate_runs": 100,
        "base_seed": 9,
        "outcome_label_type": "net_excursion",
        "block_size": 20,
    }
    assert run_label_shuffle_surrogate(**common, workers=1) == run_label_shuffle_surrogate(
        **common, workers=4
    )


class _Handle:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, Any]:
        return dict(self._payload)


class _Resolver:
    def __init__(self) -> None:
        self.feature_calls: list[dict[str, Any]] = []
        self.label_calls: list[dict[str, Any]] = []

    def resolve_feature_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_feature_request_ids,
        partition_id,
        allow_horizon_agnostic_partition=False,
    ):
        self.feature_calls.append(
            {
                "refs": tuple(refs),
                "dataset": expected_dataset_version_id,
                "feature_request_ids": tuple(expected_feature_request_ids),
                "partition_id": partition_id,
                "allow_horizon_agnostic_partition": allow_horizon_agnostic_partition,
            }
        )
        return tuple(_Handle({"feature_version_id": ref}) for ref in refs)

    def resolve_label_packs(
        self,
        refs,
        *,
        expected_dataset_version_id,
        expected_label_spec_ids,
        partition_id,
    ):
        self.label_calls.append(
            {
                "refs": tuple(refs),
                "dataset": expected_dataset_version_id,
                "label_spec_ids": tuple(expected_label_spec_ids),
                "partition_id": partition_id,
            }
        )
        return tuple(_Handle({"label_version_id": ref}) for ref in refs)


def _mechanism_card():
    return create_mechanism_card(
        source="IVL-P03 fast probe unit fixture",
        rationale=(
            "A declared exploratory setup can be read on a bounded existing "
            "slice without changing probe engines."
        ),
        expected_mechanism=(
            "The context gates when the setup is relevant and the separate "
            "trigger marks an event inside that bounded slice."
        ),
        expected_direction="research-only diagnostic readout",
        horizon="120m",
        session="RTH",
        required_features=["main_factor", "context_factor", "trigger_factor"],
        required_labels=["path_label_fixture"],
        cost_sensitivity={"scope": "exploratory only", "new_data": False},
        variant_budget=2,
        duplicate_exposure={
            "status": "bounded",
            "family_id": "fixture_family",
            "variant_id": "baseline",
        },
        stamp=EXPLORATORY_STAMP,
    )


def _setup_spec(card) -> SetupSpec:
    path_label = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC,
        {"family": "path", "name": "target_before_stop", "version": 1},
    )
    return create_setup_spec(
        entry_context={
            "factor_id": "context_factor",
            "factor_version": "ctx:v1",
            "value_field": "normalized_value",
            "operator": ">=",
            "threshold": 0.5,
        },
        event_trigger={
            "factor_id": "trigger_factor",
            "factor_version": "trg:v1",
            "value_field": "normalized_value",
            "operator": ">",
            "threshold": 0.0,
        },
        regime_filter={"session": "RTH", "policy": "unit fixture"},
        confirmation={"policy": "no additional confirmation beyond declared trigger"},
        invalidation={"policy": "fixed path"},
        stop={"binding": "fixed stop"},
        target={"binding": "fixed target"},
        hold_time={"max_minutes": 120, "horizon": "120m"},
        horizon="120m",
        path_label=path_label,
        allowed_variants=["baseline"],
        forbidden_post_hoc_changes=["No changes after readout."],
        mechanism_id=card.mechanism_id,
        stamp=EXPLORATORY_STAMP,
    )


def _main_effect_slice(tmp_path) -> dict[str, Any]:
    return {
        "slice_id": "main_fixture",
        "study_kind": "main_effect",
        "data_root": tmp_path.as_posix(),
        "dataset_version_id": "dsv_fixture",
        "partition_id": "partition_fixture",
        "instrument_id": "SYNTH",
        "session_id": "TEST:SYNTH:RTH",
        "data_version": "dsv_fixture",
        "features": [
            {
                "role": "factor",
                "factor_id": "main_factor",
                "factor_version": "main:v1",
                "relative_path": "features/factor.parquet",
                "pack_ref": "fver_main",
                "feature_request_id": "freq_main",
            }
        ],
        "labels": [
            {
                "role": "label",
                "label_id": "main_label",
                "relative_path": "labels/label.parquet",
                "pack_ref": "lver_main",
                "label_spec_id": "lspec_main",
            }
        ],
        "horizon_seconds": 60,
        "required_future_bars": 1,
    }


def _context_slice(tmp_path, setup: SetupSpec) -> dict[str, Any]:
    return {
        "slice_id": "context_fixture",
        "study_kind": "context_not_equal_trigger",
        "data_root": tmp_path.as_posix(),
        "dataset_version_id": "dsv_fixture",
        "partition_id": "partition_fixture",
        "instrument_id": "SYNTH",
        "session_id": "TEST:SYNTH:RTH",
        "data_version": "dsv_fixture",
        "features": [
            {
                "role": "context",
                "factor_id": "context_factor",
                "factor_version": "ctx:v1",
                "relative_path": "features/context.parquet",
                "pack_ref": "fver_context",
                "feature_request_id": "freq_context",
            },
            {
                "role": "trigger",
                "factor_id": "trigger_factor",
                "factor_version": "trg:v1",
                "relative_path": "features/trigger.parquet",
                "pack_ref": "fver_trigger",
                "feature_request_id": "freq_trigger",
            },
        ],
        "labels": [
            {
                "role": "path",
                "label_id": setup.path_label,
                "relative_path": "labels/path.parquet",
                "pack_ref": "lver_path",
                "label_spec_id": setup.path_label,
            }
        ],
        "label_version_map": {
            "lver_target": ("target_before_stop", "bool"),
            "lver_mfe": ("mfe_by_horizon", "float"),
            "lver_mae": ("mae_by_horizon", "float"),
        },
        "horizon_seconds": 7200,
        "required_future_bars": 120,
        "materialized_label_version": "fixture_labels_v1",
        "surrogate_run_count": 8,
        "surrogate_base_seed": 0,
        "family_id": "fixture_family",
        "family_budget": 2,
        "variant_id": "baseline",
        "created_at": "2026-01-02T15:00:00Z",
    }


def _context_loader(setup: SetupSpec, *, degenerate_binary: bool = False):
    def load(path):
        text = path.as_posix()
        if text.endswith("context.parquet"):
            return _feature_value_records((0.8, 0.9, 0.2, 0.7))
        if text.endswith("trigger.parquet"):
            return _feature_value_records((1.0, 1.0, 1.0, 1.0))
        if text.endswith("path.parquet"):
            return _path_label_value_records(degenerate_binary=degenerate_binary)
        raise AssertionError(path)

    return load


def _feature_value_records(values: tuple[float, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        rows.append(
            {
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=1)),
                "value": value,
            }
        )
    return rows


def _main_label_value_records(values: tuple[float, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        event_ts = _event_ts(index)
        horizon_end = event_ts + timedelta(seconds=60)
        rows.append(
            {
                "event_ts": _text(event_ts),
                "horizon_seconds": 60,
                "horizon_end_ts": _text(horizon_end),
                "label_available_ts": _text(horizon_end + timedelta(seconds=1)),
                "required_future_bars": 1,
                "value": value,
                "label_type": "forward_return_1m",
            }
        )
    return rows


def _path_label_value_records(*, degenerate_binary: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # A degenerate binary path (all True) trips the binary class-balance guard but
    # leaves the continuous mfe outcome non-degenerate.
    targets = (True, True, True, True) if degenerate_binary else (True, False, True, False)
    # For the degenerate-binary continuous case, give the context-selected rows
    # (slots 0, 1, 3) a clearly higher mfe than the excluded slot 2 so the observed
    # conditioned-mean lift is robust to all label shuffles (gate stays ZERO_PASS).
    mfes = (0.5, 0.4, -0.9, 0.6) if degenerate_binary else (0.05, 0.02, 0.01, 0.03)
    maes = (-0.01, -0.03, -0.02, -0.04)
    for index, target in enumerate(targets):
        event_ts = _event_ts(index)
        horizon_end = event_ts + timedelta(seconds=7200)
        common = {
            "event_ts": _text(event_ts),
            "horizon_end_ts": _text(horizon_end),
            "label_available_ts": _text(horizon_end + timedelta(seconds=1)),
            "required_future_bars": 120,
            "observed_future_bars": 120,
        }
        rows.append({**common, "label_version_id": "lver_target", "value": target})
        rows.append({**common, "label_version_id": "lver_mfe", "value": mfes[index]})
        rows.append({**common, "label_version_id": "lver_mae", "value": maes[index]})
    return rows


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
