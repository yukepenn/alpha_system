"""Bounded local execution for strategy grid MVP runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from alpha_system.backtest.engine_config import (
    ReferenceEngineConfig,
    load_reference_engine_config,
)
from alpha_system.backtest.fast_path import FAST_PATH_MODE_ACCELERATED, run_fast_path_backtest
from alpha_system.backtest.fixtures import (
    SYNTH_INSTRUMENT_MULTIPLIERS,
    falling_bars,
    no_trade_signals,
    signal_record,
    synthetic_bars,
)
from alpha_system.backtest.parity import (
    FastPathGridGateError,
    assert_grid_fast_path_allowed,
    certify_parity,
)
from alpha_system.backtest.reference import ReferenceBacktestError, run_reference_backtest
from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.core.run_ids import generate_run_id
from alpha_system.data.fixture_policy import FixturePolicyError, assert_registry_path_allowed
from alpha_system.experiments.grid import (
    GridConfiguration,
    RejectedGridConfig,
    expand_grid,
)
from alpha_system.experiments.grid_config import GridSpec
from alpha_system.experiments.grid_manifest import build_grid_manifest
from alpha_system.experiments.grid_outputs import (
    CostSensitivityRow,
    GridOutputPaths,
    MonthlyBreakdownRow,
    resolve_grid_output_paths,
    write_grid_outputs,
)
from alpha_system.experiments.leaderboard import LeaderboardRow, build_leaderboard
from alpha_system.experiments.registry import RunRecord, insert_run_record


class GridRunError(ValueError):
    """Raised when a grid run cannot complete safely."""


@dataclass(frozen=True, slots=True)
class CompletedGridConfig:
    """Completed configuration result used for output assembly."""

    config: GridConfiguration
    engine_requested: str
    engine_used: str
    result: Any
    execution_config: ReferenceEngineConfig
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GridRunResult:
    """Result of one bounded local strategy-grid run."""

    grid_id: str
    run_id: str
    combination_count: int
    completed_count: int
    rejected_count: int
    output_paths: GridOutputPaths
    registry_path: str | None
    registry_written: bool
    manifest: Mapping[str, Any]
    warnings: tuple[str, ...]
    failed_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_id": self.grid_id,
            "run_id": self.run_id,
            "combination_count": self.combination_count,
            "completed_count": self.completed_count,
            "rejected_count": self.rejected_count,
            "output_paths": self.output_paths.to_dict(),
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
            "manifest": dict(self.manifest),
            "warnings": list(self.warnings),
            "failed_steps": list(self.failed_steps),
        }


def run_grid(spec: GridSpec, *, repo_root: str | Path | None = None) -> GridRunResult:
    """Run a bounded local strategy grid and write schema-defined outputs."""
    root = Path(repo_root).resolve(strict=False) if repo_root is not None else Path.cwd()
    config_payload = spec.to_dict()
    config_hash = hash_config(config_payload)
    expansion = expand_grid(
        grid_id=spec.grid_id,
        parameter_space=spec.parameter_space,
        max_combinations=spec.max_combinations,
    )
    run_id = spec.run_id or generate_run_id(
        "grid",
        seed=spec.grid_id,
        components={
            "grid_id": spec.grid_id,
            "data_version": spec.data_version,
            "factor_versions": dict(spec.factor_versions),
            "label_versions": dict(spec.label_versions),
            "config_hash": config_hash,
        },
    )
    output_paths = resolve_grid_output_paths(spec.output_dir, manifest_path=spec.manifest_path)
    base_execution_config = _base_execution_config(spec)

    completed: list[CompletedGridConfig] = []
    rejected: list[RejectedGridConfig] = []
    warnings: list[str] = []
    failed_steps: list[str] = []

    for config in expansion.configurations:
        rule_reason = _rejection_reason(spec, config)
        if rule_reason is not None:
            rejected.append(
                RejectedGridConfig(
                    config_id=config.config_id,
                    reason=rule_reason,
                    parameters=dict(config.parameters),
                )
            )
            continue

        try:
            execution_config = _execution_config_for_parameters(base_execution_config, config.parameters)
            _assert_cost_config_allowed(spec, execution_config)
            completed.append(
                _run_single_config(
                    spec,
                    config,
                    grid_run_id=run_id,
                    execution_config=execution_config,
                )
            )
        except GridRunError as exc:
            rejected.append(
                RejectedGridConfig(
                    config_id=config.config_id,
                    reason=str(exc),
                    parameters=dict(config.parameters),
                )
            )
            failed_steps.append(f"{config.config_id}: {exc}")
        except (ReferenceBacktestError, ValueError) as exc:
            rejected.append(
                RejectedGridConfig(
                    config_id=config.config_id,
                    reason=f"execution failed: {exc}",
                    parameters=dict(config.parameters),
                )
            )
            failed_steps.append(f"{config.config_id}: {exc}")

    leaderboard = build_leaderboard(_leaderboard_rows(run_id, completed))
    monthly_rows = _monthly_breakdown_rows(run_id, completed)
    cost_rows = _cost_sensitivity_rows(run_id, completed)
    warnings.extend(_run_warnings(completed, rejected))
    manifest_parameters = {
        "grid_id": spec.grid_id,
        "combination_count": expansion.combination_count,
        "completed_count": len(completed),
        "rejected_count": len(rejected),
        "parameter_paths": list(expansion.parameter_paths),
        "engine_requested": spec.engine,
        "fast_path_features": list(spec.fast_path_features),
        "discipline": list(spec.discipline),
    }
    manifest = build_grid_manifest(
        run_id=run_id,
        grid_id=spec.grid_id,
        engine_version=spec.engine_version,
        config_hash=config_hash,
        config_payload=config_payload,
        data_version=spec.data_version,
        factor_versions=spec.factor_versions,
        label_versions=spec.label_versions,
        parameters=manifest_parameters,
        artifact_paths=output_paths.to_dict(),
        decision_status="research_evidence_only",
        warnings=tuple(dict.fromkeys(warnings)),
        failed_steps=tuple(dict.fromkeys(failed_steps)),
        repo_root=root,
    )
    write_grid_outputs(
        paths=output_paths,
        grid_id=spec.grid_id,
        grid_run_id=run_id,
        leaderboard=leaderboard,
        monthly_breakdown=monthly_rows,
        cost_sensitivity=cost_rows,
        rejected_configs=tuple(rejected),
        manifest=manifest,
        top_config_count=spec.top_config_count,
    )

    registry_written = False
    registry_path = None
    if spec.registry_path:
        registry_path = _record_grid_run(
            spec,
            run_id=run_id,
            config_hash=config_hash,
            artifact_paths=output_paths.to_dict(),
            parameters=manifest_parameters,
            warnings=tuple(dict.fromkeys(warnings)),
            repo_root=root,
        )
        registry_written = True

    return GridRunResult(
        grid_id=spec.grid_id,
        run_id=run_id,
        combination_count=expansion.combination_count,
        completed_count=len(completed),
        rejected_count=len(rejected),
        output_paths=output_paths,
        registry_path=registry_path,
        registry_written=registry_written,
        manifest=manifest,
        warnings=tuple(dict.fromkeys(warnings)),
        failed_steps=tuple(dict.fromkeys(failed_steps)),
    )


def _run_single_config(
    spec: GridSpec,
    config: GridConfiguration,
    *,
    grid_run_id: str,
    execution_config: ReferenceEngineConfig,
) -> CompletedGridConfig:
    bars, signals = _fixture_inputs(spec, config.parameters)
    requested_features = spec.fast_path_features or _features_for_parameters(config.parameters)
    warnings: list[str] = []
    # The grid runner operates on synthetic ``SYNTH`` fixtures (see _fixture_inputs);
    # supply the unit multiplier so engine multiplier resolution stays fail-loud.
    grid_instrument_multipliers = SYNTH_INSTRUMENT_MULTIPLIERS

    if spec.engine == "reference":
        result = run_reference_backtest(
            bars=bars,
            signals=signals,
            config=execution_config,
            strategy_id=spec.strategy_id,
            strategy_version=spec.strategy_version,
            data_version=spec.data_version,
            factor_versions=spec.factor_versions,
            initial_cash=spec.initial_cash,
            instrument_multipliers=grid_instrument_multipliers,
            run_id=f"{grid_run_id}-{config.config_id}",
            write_outputs=False,
        )
        return CompletedGridConfig(
            config=config,
            engine_requested=spec.engine,
            engine_used="reference",
            result=result,
            execution_config=execution_config,
            warnings=tuple(result.summary.warnings),
        )

    try:
        certification = certify_parity()
        assert_grid_fast_path_allowed(certification, requested_features)
    except FastPathGridGateError as exc:
        if not spec.reference_fallback:
            raise GridRunError(f"fast path parity gate failed closed: {exc}") from exc
        warnings.append(f"fast path parity gate routed to reference fallback: {exc}")
        result = run_reference_backtest(
            bars=bars,
            signals=signals,
            config=execution_config,
            strategy_id=spec.strategy_id,
            strategy_version=spec.strategy_version,
            data_version=spec.data_version,
            factor_versions=spec.factor_versions,
            initial_cash=spec.initial_cash,
            instrument_multipliers=grid_instrument_multipliers,
            run_id=f"{grid_run_id}-{config.config_id}",
            write_outputs=False,
        )
        warnings.extend(result.summary.warnings)
        return CompletedGridConfig(
            config=config,
            engine_requested=spec.engine,
            engine_used="reference_fallback",
            result=result,
            execution_config=execution_config,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    fast_run = run_fast_path_backtest(
        bars=bars,
        signals=signals,
        config=execution_config,
        requested_features=requested_features,
        strategy_id=spec.strategy_id,
        strategy_version=spec.strategy_version,
        data_version=spec.data_version,
        factor_versions=spec.factor_versions,
        initial_cash=spec.initial_cash,
        instrument_multipliers=grid_instrument_multipliers,
        run_id=f"{grid_run_id}-{config.config_id}",
        allow_reference_fallback=False,
    )
    if fast_run.mode != FAST_PATH_MODE_ACCELERATED:
        msg = f"fast path returned non-accelerated mode {fast_run.mode!r}"
        raise GridRunError(msg)
    return CompletedGridConfig(
        config=config,
        engine_requested=spec.engine,
        engine_used="fast",
        result=fast_run.result,
        execution_config=execution_config,
        warnings=tuple(fast_run.result.summary.warnings),
    )


def _base_execution_config(spec: GridSpec) -> ReferenceEngineConfig:
    if spec.execution_config is None:
        return ReferenceEngineConfig()
    return load_reference_engine_config(spec.execution_config)


def _execution_config_for_parameters(
    base_config: ReferenceEngineConfig,
    parameters: Mapping[str, Any],
) -> ReferenceEngineConfig:
    cost_model = base_config.cost_model
    if "execution.fixed_bps" in parameters:
        cost_model = replace(cost_model, fixed_bps=_decimal(parameters["execution.fixed_bps"], "execution.fixed_bps"))
    if "execution.minimum_cost" in parameters:
        cost_model = replace(
            cost_model,
            minimum_cost=_decimal(parameters["execution.minimum_cost"], "execution.minimum_cost"),
        )
    updates: dict[str, Any] = {"cost_model": cost_model}
    if "risk.default_quantity" in parameters:
        updates["default_quantity"] = _decimal(parameters["risk.default_quantity"], "risk.default_quantity")
    if "management.eod_flat" in parameters:
        updates["eod_flat"] = _bool(parameters["management.eod_flat"], "management.eod_flat")
    if "management.stop_loss_pct" in parameters:
        updates["stop_loss_pct"] = _optional_decimal(
            parameters["management.stop_loss_pct"],
            "management.stop_loss_pct",
        )
    if "management.target_profit_pct" in parameters:
        updates["target_profit_pct"] = _optional_decimal(
            parameters["management.target_profit_pct"],
            "management.target_profit_pct",
        )
    return replace(base_config, **updates)


def _assert_cost_config_allowed(spec: GridSpec, config: ReferenceEngineConfig) -> None:
    if spec.allow_fixture_zero_cost:
        return
    if config.cost_model.fixed_bps == 0 and config.cost_model.minimum_cost == 0:
        msg = "zero execution cost requires allow_fixture_zero_cost=true"
        raise GridRunError(msg)


def _fixture_inputs(
    spec: GridSpec,
    parameters: Mapping[str, Any],
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    pattern = str(parameters.get("strategy.signal_pattern", "entry_exit"))
    direction = str(parameters.get("strategy.direction", "long"))
    if direction not in {"long", "short"}:
        msg = f"unsupported strategy.direction {direction!r}"
        raise GridRunError(msg)
    bars = falling_bars(4, start_price=100) if direction == "short" else synthetic_bars(4)
    if pattern == "no_trade":
        signals = no_trade_signals()
    elif pattern == "entry_exit":
        signals = (
            signal_record(0, "entry", signal_id=f"{direction}-entry", direction=direction),
            signal_record(2, "exit", signal_id=f"{direction}-exit", direction=direction),
        )
    else:
        msg = f"unsupported strategy.signal_pattern {pattern!r}"
        raise GridRunError(msg)
    return (
        tuple(_with_versions(bar, spec) for bar in bars),
        tuple(_with_versions(signal, spec) for signal in signals),
    )


def _with_versions(row: Mapping[str, Any], spec: GridSpec) -> dict[str, Any]:
    payload = dict(row)
    payload["data_version"] = spec.data_version
    if "strategy_id" in payload:
        payload["strategy_id"] = spec.strategy_id
        payload["strategy_version"] = spec.strategy_version
        payload["factor_versions"] = dict(spec.factor_versions)
    return payload


def _features_for_parameters(parameters: Mapping[str, Any]) -> tuple[str, ...]:
    features: set[str] = {"trade_summary", "equity_curve"}
    pattern = str(parameters.get("strategy.signal_pattern", "entry_exit"))
    direction = str(parameters.get("strategy.direction", "long"))
    if pattern == "no_trade":
        features.add("no_trade")
    elif direction == "short":
        features.add("simple_short")
    else:
        features.add("simple_long")
    if _has_positive(parameters.get("execution.fixed_bps")):
        features.add("costs")
    if _has_positive(parameters.get("management.stop_loss_pct")):
        features.add("fixed_stop")
    if _has_positive(parameters.get("management.target_profit_pct")):
        features.add("target")
    if _bool_or_false(parameters.get("management.eod_flat")):
        features.add("eod_exit")
    return tuple(sorted(features))


def _rejection_reason(spec: GridSpec, config: GridConfiguration) -> str | None:
    for rule in spec.rejection_rules:
        if rule.matches(config.parameters):
            return rule.reason
    return None


def _leaderboard_rows(
    grid_run_id: str,
    completed: Sequence[CompletedGridConfig],
) -> tuple[LeaderboardRow, ...]:
    rows: list[LeaderboardRow] = []
    for item in completed:
        summary = item.result.summary
        rows.append(
            LeaderboardRow(
                rank=0,
                grid_run_id=grid_run_id,
                config_id=item.config.config_id,
                engine_requested=item.engine_requested,
                engine_used=item.engine_used,
                total_trades=summary.total_trades,
                open_positions=summary.open_positions,
                gross_pnl=summary.gross_pnl,
                costs=summary.costs,
                net_pnl=summary.net_pnl,
                final_equity=summary.final_equity,
                warning_count=len(item.warnings),
                parameters=dict(item.config.parameters),
            )
        )
    return tuple(rows)


def _monthly_breakdown_rows(
    grid_run_id: str,
    completed: Sequence[CompletedGridConfig],
) -> tuple[MonthlyBreakdownRow, ...]:
    rows = []
    for item in sorted(completed, key=lambda entry: entry.config.config_id):
        summary = item.result.summary
        month = _result_month(item)
        rows.append(
            MonthlyBreakdownRow(
                grid_run_id=grid_run_id,
                config_id=item.config.config_id,
                month=month,
                total_trades=summary.total_trades,
                net_pnl=_decimal_text(summary.net_pnl),
                final_equity=_decimal_text(summary.final_equity),
                warning_count=len(item.warnings),
            )
        )
    return tuple(rows)


def _cost_sensitivity_rows(
    grid_run_id: str,
    completed: Sequence[CompletedGridConfig],
) -> tuple[CostSensitivityRow, ...]:
    rows = []
    for item in sorted(completed, key=lambda entry: entry.config.config_id):
        summary = item.result.summary
        cost_model = item.execution_config.cost_model
        rows.append(
            CostSensitivityRow(
                grid_run_id=grid_run_id,
                config_id=item.config.config_id,
                cost_model=cost_model.model,
                fixed_bps=_decimal_text(cost_model.fixed_bps),
                minimum_cost=_decimal_text(cost_model.minimum_cost),
                total_trades=summary.total_trades,
                costs=_decimal_text(summary.costs),
                net_pnl=_decimal_text(summary.net_pnl),
            )
        )
    return tuple(rows)


def _record_grid_run(
    spec: GridSpec,
    *,
    run_id: str,
    config_hash: str,
    artifact_paths: Mapping[str, str],
    parameters: Mapping[str, Any],
    warnings: Sequence[str],
    repo_root: Path,
) -> str:
    try:
        registry_path = assert_registry_path_allowed(spec.registry_path or "", repo_root=repo_root)
    except FixturePolicyError as exc:
        raise GridRunError(str(exc)) from exc
    status = init_registry(registry_path)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise GridRunError(msg)
    git_info = capture_git_info(repo_root)
    record = RunRecord(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=hash_config({"engine_version": spec.engine_version, "module": __name__}),
        config_hash=config_hash,
        data_version=spec.data_version,
        factor_versions=dict(spec.factor_versions),
        label_versions=dict(spec.label_versions),
        engine_version=spec.engine_version,
        parameters=parameters,
        artifact_paths=artifact_paths,
        decision_status="grid_recorded",
        warnings=tuple(warnings),
        status_message="Strategy grid research evidence only; no promotion decision.",
    )
    with connect_registry(registry_path) as connection:
        insert_run_record(connection, "grid_runs", record)
    return registry_path.as_posix()


def _run_warnings(
    completed: Sequence[CompletedGridConfig],
    rejected: Sequence[RejectedGridConfig],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if rejected:
        warnings.append("one or more grid configurations were rejected with visible reasons")
    for item in completed:
        warnings.extend(item.warnings)
    return tuple(dict.fromkeys(warnings))


def _result_month(item: CompletedGridConfig) -> str:
    if item.result.equity_curve:
        return item.result.equity_curve[-1].bar_end_ts.strftime("%Y-%m")
    return "unknown"


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise GridRunError(msg)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise GridRunError(msg) from exc


def _optional_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    active = _decimal(value, field_name)
    if active <= 0:
        msg = f"{field_name} must be positive when provided"
        raise GridRunError(msg)
    return active


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    msg = f"{field_name} must be boolean"
    raise GridRunError(msg)


def _bool_or_false(value: Any) -> bool:
    if value in (None, ""):
        return False
    return _bool(value, "value")


def _has_positive(value: Any) -> bool:
    if value in (None, ""):
        return False
    return _decimal(value, "value") > 0


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
