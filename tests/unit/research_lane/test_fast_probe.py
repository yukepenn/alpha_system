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
        SimpleNamespace(required_future_bars=60)
    )

    assert meta == {
        "horizon_bars": 60,
        "sampling_cadence_bars": 1,
        "discount_factor": 60,
        "metadata_source": "fast_probe_main_effect_label_horizon",
    }


def test_main_effect_overlap_metadata_none_when_no_forward_overlap() -> None:
    # No forward horizon, or a single-bar horizon, means no overlap to discount.
    assert (
        fast_probe_module._main_effect_overlap_metadata(
            SimpleNamespace(required_future_bars=None)
        )
        is None
    )
    assert (
        fast_probe_module._main_effect_overlap_metadata(
            SimpleNamespace(required_future_bars=1)
        )
        is None
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
