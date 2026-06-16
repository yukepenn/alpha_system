from __future__ import annotations

import csv
import json
import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from alpha_system.backtest.execution_config import ExecutionConfig
from alpha_system.backtest.costs import BpsCost, CompositeCostModel
from alpha_system.backtest.parity import certify_parity
from alpha_system.backtest.reference import run_reference_backtest
from alpha_system.backtest.slippage import BpsSlippageModel, CompositeSlippageModel
from alpha_system.core.enums import Direction
from alpha_system.core.registry import init_registry, inspect_registry_status
from alpha_system.data.calendar import TradingCalendar
from alpha_system.data.universe import MISSING_DATA_FLAG, load_universe_config
from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.management_grid import ManagementGridSpec, run_management_grid
from alpha_system.experiments.ml import MLRunSpec, run_ml_experiment
from alpha_system.experiments.runner import run_grid
from alpha_system.experiments.universe_runner import UniverseRunnerSpec, run_universe_fixture
from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from alpha_system.factors.validation import validate_factor_spec_mapping
from alpha_system.l2.features import compute_top_of_book_spread
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows
from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.store import LocalLabelStore
from alpha_system.labels.validation import validate_label_record
from alpha_system.management.integration import run_reference_backtest_with_management
from alpha_system.management.spec import ManagementSpec
from alpha_system.portfolio.integration import (
    reference_default_quantity_from_targets,
    signals_to_portfolio_targets,
)
from alpha_system.portfolio.spec import PortfolioSpec
from alpha_system.reports.factor_card import build_factor_card, write_factor_card
from alpha_system.reports.review_bundle import build_review_bundle, write_review_bundle
from alpha_system.research.diagnostics import run_study
from alpha_system.research.study_config import StudyConfig
from alpha_system.signals.store import LocalSignalStore
from alpha_system.strategies.templates import (
    build_single_factor_threshold_spec,
    evaluate_single_factor_threshold,
)
from tests.fixtures.backtest_reference import (
    INSTRUMENT_ID,
    SYNTH_INSTRUMENT_MULTIPLIERS,
    signal_record,
    synthetic_bar,
    synthetic_bars,
    zero_cost_config,
)
from tests.fixtures.factors.synthetic import (
    DATA_VERSION as FACTOR_DATA_VERSION,
    factor_payload,
    factor_spec,
    make_bars as factor_bars,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
DATA_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "data" / "synthetic_1min_bars.csv"
DATA_VALIDATION_CONFIG = REPO_ROOT / "configs" / "data" / "validation_example.yaml"
UNIVERSE_CONFIG = REPO_ROOT / "configs" / "universes" / "examples" / "tiny_multi_symbol.json"


def test_end_to_end_v0_1_fixture_workflow_is_local_only(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.sqlite3"
    init_registry(registry_path)

    validation_summary = _validate_data_fixture(tmp_path)
    canonical_rows = _build_canonical_fixture_bars(tmp_path)
    assert validation_summary["valid"] is True
    assert canonical_rows[0]["session_id"] == "SYNTH_E2E:2026-01-02:regular"
    assert canonical_rows[0]["bar_index"] == "0"

    factor_validation = validate_factor_spec_mapping(
        factor_payload(),
        used_fields=("close_price",),
    )
    assert factor_validation.valid is True

    spec = factor_spec()
    computed_factor_values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        factor_bars(["100", "101", "103", "102", "104", "105"]),
        data_version=FACTOR_DATA_VERSION,
    )
    assert [value.value for value in computed_factor_values[:3]] == [None, 1.0, 2.0]
    assert computed_factor_values[1].available_ts > computed_factor_values[1].event_ts

    labels = generate_forward_return_labels(
        factor_bars(["100", "101", "103", "102", "104", "105"]),
        horizons_minutes=(1,),
        label_version="v1",
    )
    assert labels
    assert all(validate_label_record(label) for label in labels)
    assert all(label.label_available_ts >= label.event_ts for label in labels)

    label_store = LocalLabelStore(tmp_path / "labels", repo_root=REPO_ROOT)
    label_path = label_store.write_labels("forward_return_1m", labels)
    factor_value_path = _write_jsonl(
        tmp_path / "factor_values.jsonl",
        [value.to_dict() for value in computed_factor_values[:-1]],
    )

    study = run_study(
        StudyConfig.from_mapping(
            {
                "study_id": "e2e-v0-1-study",
                "factor_id": spec.factor_id,
                "factor_version": spec.version,
                "label_id": "forward_return_1m",
                "label_version": "v1",
                "data_version": FACTOR_DATA_VERSION,
                "factor_values_path": factor_value_path.as_posix(),
                "labels_path": label_path.as_posix(),
                "horizon_seconds": 60,
                "output_dir": (tmp_path / "study").as_posix(),
                "registry_path": registry_path.as_posix(),
                "sample_size_thresholds": {"min_total": 1},
                "bucket_count": 2,
            }
        )
    )
    assert study.registry_written is True
    assert study.summary.engine_version == "intraday_factor_diagnostics_v1"
    assert "directional" in study.summary.diagnostics

    factor_card = build_factor_card(
        study.summary.to_dict(),
        reproducibility_metadata={
            "run_manifest_path": study.output_paths.manifest_path,
            "code_hash_ref": "code:e2e-fixture",
            "config_hash_ref": "config:e2e-fixture",
            "no_lookahead_validation_status": "passed",
            "review_status": "review_pending",
            "factor_label_alignment_status": "matched",
        },
    )
    factor_card_path = write_factor_card(factor_card, tmp_path / "factor_card.md")
    assert factor_card_path.is_file()
    assert "correctness validation" not in factor_card_path.read_text(encoding="utf-8").lower()

    strategy_spec = build_single_factor_threshold_spec(
        strategy_id="threshold_strategy",
        version="v1",
        owner="research",
        factor_id=spec.factor_id,
        factor_version=spec.version,
        entry_threshold=0.5,
        exit_threshold=-0.1,
        direction=Direction.LONG,
        confidence_score=0.6,
        desired_exposure=0.25,
    )
    signal = evaluate_single_factor_threshold(
        strategy_spec,
        {spec.factor_id: computed_factor_values[2].to_dict()},
    )
    signal_store = LocalSignalStore(tmp_path / "signals", repo_root=REPO_ROOT)
    signal_write = signal_store.write_signals("threshold_signals", [signal.to_dict()])
    assert signal_write.record_count == 1
    assert signal_write.signals_path.is_relative_to(tmp_path)

    portfolio_spec = PortfolioSpec.from_mapping(
        {
            "position_sizing": {"method": "fixed_notional", "fixed_notional": "100"},
            "capital_allocation": {"starting_equity": "100000"},
            "risk_limits": {"max_position_percent": "0.1", "max_gross_exposure": "1.0"},
        }
    )
    entry_signal = signal_record(0, "entry", signal_id="entry")
    targets = signals_to_portfolio_targets(
        signals=[entry_signal],
        prices={INSTRUMENT_ID: Decimal("100")},
        portfolio_spec=portfolio_spec,
    )
    quantity = reference_default_quantity_from_targets(targets, instrument_id=INSTRUMENT_ID)

    reference_result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[entry_signal, signal_record(1, "exit", signal_id="exit")],
        config=zero_cost_config(default_quantity=quantity),
        output_dir=tmp_path / "backtest",
        registry_path=registry_path,
        run_id="e2e-reference",
        repo_root=REPO_ROOT,
        write_outputs=True,
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )
    assert reference_result.summary.total_trades == 1
    assert reference_result.manifest["engine_version"] == "reference_1min_v1"
    assert reference_result.registry_written is True
    assert reference_result.output_paths is not None
    assert Path(reference_result.output_paths.trades_path).is_relative_to(tmp_path)

    costly_result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[entry_signal, signal_record(1, "exit", signal_id="cost-exit")],
        config=ExecutionConfig(cost_model=CompositeCostModel(models=(BpsCost(Decimal("100")),))),
        run_id="e2e-costs",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )
    slippage_result = run_reference_backtest(
        bars=synthetic_bars(4),
        signals=[entry_signal, signal_record(1, "exit", signal_id="slippage-exit")],
        config=ExecutionConfig(
            slippage_model=CompositeSlippageModel(models=(BpsSlippageModel(Decimal("25")),))
        ),
        run_id="e2e-slippage",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )
    assert costly_result.summary.costs > reference_result.summary.costs
    assert slippage_result.manifest["parameters"]["slippage_model"]["components"][0]["bps"] == "25"

    managed_result = run_reference_backtest_with_management(
        bars=[
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="102.5", low="99", close="101"),
            synthetic_bar(2, open_price="102", high="103", low="101", close="102"),
        ],
        signals=[entry_signal],
        config=zero_cost_config(default_quantity=Decimal("1")),
        management_spec=ManagementSpec.from_mapping(
            {
                "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
                "laddered_partial_take_profit": {
                    "enabled": True,
                    "steps": [
                        {"label": "half_at_1r", "threshold_r": "1", "exit_fraction": "0.5"}
                    ],
                },
                "eod_exit": True,
            }
        ),
        run_id="e2e-management",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )
    assert managed_result.summary.total_trades == 2
    assert managed_result.summary.open_positions == 0

    parity = certify_parity()
    assert parity.certified is True
    assert parity.accelerated_features
    assert parity.failed_cases == ()

    grid = run_grid(GridSpec.from_mapping(_grid_payload(tmp_path)))
    assert grid.completed_count == 2
    assert grid.rejected_count == 0
    assert Path(grid.output_paths.leaderboard_path).is_relative_to(tmp_path)

    management_grid = run_management_grid(ManagementGridSpec.from_mapping(_management_grid_payload(tmp_path)))
    assert management_grid.completed_count == 2
    assert management_grid.rejected_count == 0
    assert Path(management_grid.output_paths.leaderboard_path).is_relative_to(tmp_path)

    ml = run_ml_experiment(MLRunSpec.from_mapping(_ml_payload(tmp_path, registry_path)))
    assert ml.registry_written is True
    with sqlite3.connect(registry_path) as connection:
        assert connection.execute("SELECT count(*) FROM ml_runs").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM backtest_runs").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM study_runs").fetchone()[0] == 1

    universe = run_universe_fixture(
        UniverseRunnerSpec(
            run_id="e2e-multi-symbol",
            universe=load_universe_config(UNIVERSE_CONFIG),
            calendars=_calendars(),
            trading_dates=(date(2026, 1, 2),),
            bars=(
                _universe_bar(
                    "EQ_US_SYNTH_A",
                    datetime(2026, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York")),
                ),
                _universe_bar(
                    "EQ_US_SYNTH_A",
                    datetime(2026, 1, 2, 9, 31, tzinfo=ZoneInfo("America/New_York")),
                ),
                _universe_bar(
                    "EQ_US_SYNTH_B",
                    datetime(2026, 1, 2, 8, 30, tzinfo=ZoneInfo("America/Chicago")),
                ),
            ),
            output_dir=(tmp_path / "universe").as_posix(),
        )
    )
    assert universe.missing_data_flags == {"EQ_US_SYNTH_B": (MISSING_DATA_FLAG,)}

    l2_feature = compute_top_of_book_spread(synthetic_l2_snapshot_rows())
    assert l2_feature.value == 0.05
    assert "l2_feature_fixture_only" in l2_feature.quality_flags

    bundle = build_review_bundle(
        run_id="e2e-review-bundle",
        artifact_manifest=_write_artifact_manifest(tmp_path),
        run_manifest=_write_run_manifest(tmp_path),
        source_root=REPO_ROOT,
    )
    bundle_write = write_review_bundle(bundle, tmp_path / "review_bundle")
    assert Path(bundle_write.files["review_bundle_summary.json"]).is_file()
    assert Path(bundle_write.output_dir).is_relative_to(tmp_path)

    registry_status = inspect_registry_status(registry_path)
    assert registry_status.valid is True
    assert registry_status.local_only is True


def _env_with_src_path() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_ROOT) if not pythonpath else os.pathsep.join([str(SRC_ROOT), pythonpath])
    )
    return env


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", *args],
        cwd=cwd,
        env=_env_with_src_path(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _validate_data_fixture(tmp_path: Path) -> dict[str, object]:
    summary_path = tmp_path / "data_validation_summary.json"
    result = _run_cli(
        [
            "data",
            "validate",
            "--config",
            DATA_VALIDATION_CONFIG.as_posix(),
            "--input",
            DATA_FIXTURE.as_posix(),
            "--schema-id",
            "canonical_1min_bars_v1",
            "--summary-out",
            summary_path.as_posix(),
            "--json",
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert summary_path.is_file()
    return json.loads(result.stdout)


def _build_canonical_fixture_bars(tmp_path: Path) -> list[dict[str, str]]:
    instrument_config = tmp_path / "instrument.yaml"
    instrument_config.write_text(
        "instrument_id: SYNTH-1\nfixture_policy: synthetic_correctness_only\n",
        encoding="utf-8",
    )
    calendar_config = tmp_path / "calendar.json"
    calendar_config.write_text(
        json.dumps(
            {
                "calendar_id": "SYNTH_E2E",
                "timezone": "America/New_York",
                "regular_session": {
                    "open": "09:30",
                    "close": "09:33",
                    "session_type": "regular",
                },
                "sessions": [{"trading_date": "2026-01-02", "session_type": "regular"}],
                "metadata": {"fixture_scope": "synthetic e2e test"},
            }
        ),
        encoding="utf-8",
    )
    validation_config = tmp_path / "validation.yaml"
    validation_config.write_text("available_latency_seconds: 5\n", encoding="utf-8")
    output_path = tmp_path / "data" / "canonical" / "bars.csv"

    result = _run_cli(
        [
            "data",
            "build-bars",
            "--input",
            DATA_FIXTURE.as_posix(),
            "--instrument-config",
            instrument_config.as_posix(),
            "--calendar-config",
            calendar_config.as_posix(),
            "--output",
            output_path.as_posix(),
            "--data-version",
            "data:synthetic-e2e:v1",
            "--validation-config",
            validation_config.as_posix(),
            "--json",
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _grid_payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "e2e_tiny_grid",
        "run_id": "e2e_tiny_grid",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "factor_versions": {"fixture_factor": "v1"},
        "label_versions": {"fixture_label": "v1"},
        "output_dir": (tmp_path / "grid").as_posix(),
        "max_combinations": 2,
        "parameter_space": {
            "factor": {"lookback": [2]},
            "strategy": {"direction": ["long", "short"]},
            "risk": {"default_quantity": ["1"]},
            "management": {"eod_flat": [True]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _management_grid_payload(tmp_path: Path) -> dict[str, object]:
    return {
        "grid_id": "e2e_management_grid",
        "run_id": "e2e_management_grid",
        "strategy_version": "strategy:v1",
        "data_version": "data:v1",
        "output_dir": (tmp_path / "management_grid").as_posix(),
        "max_combinations": 2,
        "survivors": [
            {
                "candidate_id": "candidate:e2e-fixture",
                "source_run_id": "grid_source",
                "factor_versions": {"fixture_factor": "v1"},
                "label_versions": {"fixture_label": "v1"},
                "strategy_version": "strategy:v1",
                "baseline_management_config": {
                    "management_id": "management:baseline",
                    "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
                    "eod_exit": True,
                },
                "baseline_portfolio_config": {"portfolio_id": "portfolio:baseline"},
                "source_grid_config_hash": "hash-e2e-fixture",
                "survivor_eligibility_reason": "passed diagnostics and baseline review",
                "warnings": [],
                "review_status": "PASS",
                "allowed_management_grid_scope": {
                    "management_parameters": ["management.fixed_stop.stop_pct"],
                    "execution_parameters": ["execution.fixed_bps"],
                    "max_combinations": 2,
                },
            }
        ],
        "parameter_space": {
            "management": {"fixed_stop.stop_pct": ["0.01", "0.02"]},
            "execution": {"fixed_bps": ["1"]},
        },
    }


def _ml_payload(tmp_path: Path, registry_path: Path) -> dict[str, object]:
    return {
        "run_id": "e2e_ml",
        "output_dir": (tmp_path / "ml").as_posix(),
        "registry_path": registry_path.as_posix(),
        "feature_set": {
            "feature_set_id": "e2e_fixture",
            "data_version": "data:v1",
            "factor_versions": {"momentum_3": "factor:v1", "reversal_2": "factor:v1"},
            "features": [{"factor_id": "momentum_3"}, {"factor_id": "reversal_2"}],
        },
        "label_spec": {"label_id": "forward_return_1", "label_version": "label:v1"},
        "model_spec": {
            "model_id": "ridge",
            "model_type": "ridge_baseline",
            "parameters": {"ridge_l2": 0.1},
        },
        "split": {"split_type": "train_validation", "validation_fraction": 0.34},
        "observations": [
            _ml_observation(index, momentum, reversal, label)
            for index, momentum, reversal, label in (
                (0, 0.1, -0.2, 0.01),
                (1, 0.2, -0.1, 0.02),
                (2, -0.1, 0.2, -0.01),
                (3, 0.3, -0.3, 0.03),
                (4, -0.2, 0.1, -0.02),
                (5, 0.4, -0.4, 0.04),
            )
        ],
    }


def _ml_observation(index: int, momentum: float, reversal: float, label: float) -> dict[str, object]:
    decision_ts = datetime(2026, 1, 2, 10, index, tzinfo=ZoneInfo("UTC"))
    return {
        "instrument": "SYNTH",
        "decision_ts": decision_ts.isoformat().replace("+00:00", "Z"),
        "label_available_ts": (decision_ts - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "momentum_3": momentum,
        "reversal_2": reversal,
        "forward_return_1": label,
    }


def _calendars() -> dict[str, TradingCalendar]:
    return {
        "EQ_US_SYNTH_A": _calendar("XNYS_SYNTH", "America/New_York", "09:30", "09:32"),
        "EQ_US_SYNTH_B": _calendar("XCME_SYNTH", "America/Chicago", "08:30", "08:32"),
    }


def _calendar(calendar_id: str, zone: str, open_time: str, close_time: str) -> TradingCalendar:
    return TradingCalendar.from_config(
        {
            "calendar_id": calendar_id,
            "timezone": zone,
            "regular_session": {"open": open_time, "close": close_time},
            "sessions": [{"trading_date": "2026-01-02"}],
        }
    )


def _universe_bar(instrument_id: str, start: datetime) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "bar_start_ts": start,
        "bar_end_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1),
    }


def _write_run_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "review_run_manifest.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "e2e-review-bundle",
                "data_version": "data:v1",
                "factor_versions": {"fixture_factor": "factor:v1"},
                "label_versions": {"fixture_label": "label:v1"},
                "engine_version": "fixture_engine_v1",
                "config_hash": "config-hash-v1",
                "code_hash": "code-hash-v1",
                "diagnostics_summary": {"sample_size": 12, "warning_count": 1},
                "backtest_summary": {"trade_count": 0},
                "cost_sensitivity": {"not_applicable": True},
                "monthly_breakdown": {"2026-01": {"rows": 2}},
                "rejected_configs": (),
                "failed_steps": (),
                "warnings": ("fixture warning",),
                "promotion_decision_status": "not_recorded",
                "no_lookahead_validation_status": "passed",
                "review_status": "review_pending",
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _write_artifact_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "review_artifact_manifest.json"
    path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "artifact_key": "diagnostics_summary",
                        "artifact_path": "docs/REVIEW_BUNDLES.md",
                        "artifact_role": "tiny_fixture_reference",
                        "content_hash": "",
                        "warnings": (),
                    }
                ]
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
