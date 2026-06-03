"""Survivor-gated bounded management-grid execution."""

from __future__ import annotations

import itertools
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from alpha_system.backtest.engine_config import (
    ReferenceEngineConfig,
    load_reference_engine_config,
)
from alpha_system.backtest.fast_path import FAST_PATH_MODE_ACCELERATED, run_fast_path_backtest
from alpha_system.backtest.fixtures import falling_bars, no_trade_signals, signal_record, synthetic_bar, synthetic_bars
from alpha_system.backtest.parity import FastPathGridGateError, assert_grid_fast_path_allowed, certify_parity
from alpha_system.backtest.reference import ReferenceBacktestError
from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_code_paths, hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.core.run_ids import generate_run_id
from alpha_system.data.fixture_policy import FixturePolicyError, assert_registry_path_allowed
from alpha_system.experiments.candidate_policy import (
    CandidateEligibilityDecision,
    CandidateEligibilityError,
    assert_candidate_eligible,
)
from alpha_system.experiments.limits import CombinationLimit, GridLimitError, product_count
from alpha_system.experiments.management_outputs import (
    BaselineComparisonRow,
    ManagementCostSensitivityRow,
    ManagementLeaderboardRow,
    ManagementMonthlyBreakdownRow,
    ManagementOutputPaths,
    rank_management_leaderboard,
    resolve_management_output_paths,
    write_management_outputs,
)
from alpha_system.experiments.overfit_controls import (
    SURVIVOR_WORKFLOW_STEPS,
    assess_management_overfit_controls,
)
from alpha_system.experiments.registry import RunRecord, insert_run_record
from alpha_system.experiments.survivors import (
    SurvivorRecord,
    SurvivorSchemaError,
    select_survivor,
    survivor_records_from_payload,
)
from alpha_system.management.integration import run_reference_backtest_with_management
from alpha_system.management.spec import ManagementSpec, ManagementSpecError


MANAGEMENT_GRID_ENGINE_VERSION = "management_grid_v1"
MANAGEMENT_GRID_PARAMETER_GROUPS: tuple[str, ...] = ("management", "execution")
MANAGEMENT_PARAMETER_ORDER: tuple[str, ...] = ("management", "execution")
SUPPORTED_MANAGEMENT_PARAMETER_PATHS: tuple[str, ...] = (
    "management.fixed_stop.stop_pct",
    "management.fixed_stop.stop_price",
    "management.target_r_multiple.r_multiple",
    "management.laddered_partial_take_profit.steps",
    "management.trailing_stop.trail_r",
    "management.trailing_stop.trail_pct",
    "management.breakeven_stop.trigger_r",
    "management.breakeven_stop.offset_r",
    "management.max_holding_bars.max_bars",
    "management.cooldown.bars",
    "management.eod_exit.enabled",
    "management.time_exit.max_minutes",
    "management.max_trades_per_day.limit",
    "execution.fixed_bps",
    "execution.minimum_cost",
)
MANAGEMENT_GRID_CODE_MODULES: tuple[str, ...] = (
    "management_grid.py",
    "survivors.py",
    "candidate_policy.py",
    "overfit_controls.py",
    "management_outputs.py",
)


class ManagementGridConfigError(ValueError):
    """Raised when a management-grid spec is incomplete or unsafe."""


class ManagementGridExpansionError(GridLimitError):
    """Raised when management-grid expansion is not finite and bounded."""

    def __init__(
        self,
        message: str,
        *,
        rejected_configs: Sequence["RejectedManagementConfig"] = (),
        count: int | None = None,
        max_combinations: int | None = None,
    ) -> None:
        self.rejected_configs = tuple(rejected_configs)
        super().__init__(message, count=count, max_combinations=max_combinations)


class ManagementGridRunError(ValueError):
    """Raised when a management-grid run cannot complete safely."""


@dataclass(frozen=True, slots=True)
class ManagementGridParameter:
    """One finite management-grid dimension."""

    group: str
    name: str
    values: tuple[Any, ...]

    @property
    def path(self) -> str:
        return f"{self.group}.{self.name}"


@dataclass(frozen=True, slots=True)
class ManagementGridConfiguration:
    """One expanded management-grid configuration."""

    config_id: str
    ordinal: int
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RejectedManagementConfig:
    """A rejected management-grid configuration with visible reason text."""

    management_grid_run_id: str
    candidate_id: str
    config_id: str
    reason: str
    parameters: Mapping[str, Any]
    status: str = "rejected"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManagementGridExpansion:
    """Expanded configurations plus deterministic expansion metadata."""

    grid_id: str
    parameters: tuple[ManagementGridParameter, ...]
    configurations: tuple[ManagementGridConfiguration, ...]
    combination_count: int
    max_combinations: int

    @property
    def parameter_paths(self) -> tuple[str, ...]:
        return tuple(parameter.path for parameter in self.parameters)


@dataclass(frozen=True, slots=True)
class ManagementRejectionRule:
    """Declarative rule for intentionally rejected management configurations."""

    when: Mapping[str, Any]
    reason: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ManagementRejectionRule":
        when = payload.get("when")
        if not isinstance(when, Mapping) or not when:
            raise ManagementGridConfigError("rejection rule requires a non-empty when mapping")
        reason = _text(payload.get("reason"), "rejection rule reason")
        return cls(when=dict(when), reason=reason)

    def matches(self, parameters: Mapping[str, Any]) -> bool:
        return all(parameters.get(str(path)) == expected for path, expected in self.when.items())

    def to_dict(self) -> dict[str, Any]:
        return {"when": dict(self.when), "reason": self.reason}


@dataclass(frozen=True, slots=True)
class ManagementGridSpec:
    """Finite local management-grid experiment declaration."""

    grid_id: str
    survivors: tuple[SurvivorRecord, ...]
    candidate_id: str
    strategy_version: str
    data_version: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    baseline_management_config: Mapping[str, Any]
    baseline_portfolio_config: Mapping[str, Any]
    parameter_space: Mapping[str, Mapping[str, tuple[Any, ...]]]
    max_combinations: int
    strategy_id: str = "management_grid_fixture_strategy"
    run_id: str | None = None
    engine: str = "reference"
    fast_path_features: tuple[str, ...] = ()
    reference_fallback: bool = True
    execution_config: str | None = None
    output_dir: str | None = None
    registry_path: str | None = None
    manifest_path: str | None = None
    top_config_count: int = 3
    rejection_rules: tuple[ManagementRejectionRule, ...] = ()
    allow_fixture_zero_cost: bool = False
    direction: str = "long"
    signal_pattern: str = "entry_only"
    engine_version: str = MANAGEMENT_GRID_ENGINE_VERSION
    initial_cash: Decimal = Decimal("100000")
    workflow_steps: tuple[str, ...] = field(default=SURVIVOR_WORKFLOW_STEPS)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ManagementGridSpec":
        required = ("grid_id", "data_version", "parameter_space", "max_combinations")
        missing = tuple(field_name for field_name in required if _missing(payload.get(field_name)))
        if missing:
            msg = f"management grid spec missing required fields: {', '.join(missing)}"
            raise ManagementGridConfigError(msg)

        survivors_payload = payload.get("survivors", payload.get("survivor_records"))
        if survivors_payload is None:
            raise ManagementGridConfigError("management grid spec requires survivor records")
        try:
            survivors = survivor_records_from_payload(survivors_payload)
        except SurvivorSchemaError as exc:
            raise ManagementGridConfigError(str(exc)) from exc
        candidate_id = _optional_text(payload.get("candidate_id"), "candidate_id")
        survivor = select_survivor(survivors, candidate_id)
        parameter_space = _parameter_space(payload.get("parameter_space"))

        factor_versions = _version_map(
            payload.get("factor_versions", survivor.factor_versions),
            "factor_versions",
            allow_empty=False,
        )
        label_versions = _version_map(
            payload.get("label_versions", survivor.label_versions),
            "label_versions",
            allow_empty=True,
        )
        strategy_version = _optional_text(payload.get("strategy_version"), "strategy_version") or survivor.strategy_version
        if strategy_version != survivor.strategy_version:
            raise ManagementGridConfigError("strategy_version must match the selected survivor record")
        if factor_versions != dict(survivor.factor_versions):
            raise ManagementGridConfigError("factor_versions must match the selected survivor record")
        if label_versions != dict(survivor.label_versions):
            raise ManagementGridConfigError("label_versions must match the selected survivor record")

        engine = _optional_text(payload.get("engine"), "engine") or "reference"
        if engine not in {"reference", "fast"}:
            raise ManagementGridConfigError("engine must be either 'reference' or 'fast'")
        direction = _optional_text(payload.get("direction"), "direction") or "long"
        if direction not in {"long", "short"}:
            raise ManagementGridConfigError("direction must be either 'long' or 'short'")
        signal_pattern = _optional_text(payload.get("signal_pattern"), "signal_pattern") or "entry_only"
        if signal_pattern not in {"entry_only", "entry_exit", "no_trade"}:
            raise ManagementGridConfigError("signal_pattern must be entry_only, entry_exit, or no_trade")

        return cls(
            grid_id=_text(payload["grid_id"], "grid_id"),
            survivors=survivors,
            candidate_id=survivor.candidate_id,
            strategy_id=_optional_text(payload.get("strategy_id"), "strategy_id")
            or "management_grid_fixture_strategy",
            strategy_version=strategy_version,
            data_version=_text(payload["data_version"], "data_version"),
            factor_versions=factor_versions,
            label_versions=label_versions,
            baseline_management_config=dict(
                payload.get("baseline_management_config", survivor.baseline_management_config)
            ),
            baseline_portfolio_config=dict(
                payload.get("baseline_portfolio_config", survivor.baseline_portfolio_config)
            ),
            parameter_space=parameter_space,
            max_combinations=_positive_int(payload.get("max_combinations"), "max_combinations"),
            run_id=_optional_text(payload.get("run_id"), "run_id"),
            engine=engine,
            fast_path_features=_text_tuple(payload.get("fast_path_features", ()), "fast_path_features"),
            reference_fallback=_bool(payload.get("reference_fallback", True), "reference_fallback"),
            execution_config=_optional_text(payload.get("execution_config"), "execution_config"),
            output_dir=_optional_text(payload.get("output_dir"), "output_dir"),
            registry_path=_optional_text(payload.get("registry_path"), "registry_path"),
            manifest_path=_optional_text(payload.get("manifest_path"), "manifest_path"),
            top_config_count=_positive_int(payload.get("top_config_count", 3), "top_config_count"),
            rejection_rules=tuple(
                ManagementRejectionRule.from_mapping(rule) for rule in payload.get("rejection_rules", ())
            ),
            allow_fixture_zero_cost=_bool(
                payload.get("allow_fixture_zero_cost", False),
                "allow_fixture_zero_cost",
            ),
            direction=direction,
            signal_pattern=signal_pattern,
            engine_version=_optional_text(payload.get("engine_version"), "engine_version")
            or MANAGEMENT_GRID_ENGINE_VERSION,
            initial_cash=_positive_decimal(payload.get("initial_cash", "100000"), "initial_cash"),
            workflow_steps=_workflow_steps(payload.get("workflow_steps")),
        )

    @property
    def selected_survivor(self) -> SurvivorRecord:
        return select_survivor(self.survivors, self.candidate_id)

    @property
    def combination_count(self) -> int:
        return count_management_grid_combinations(self.parameter_space)

    def with_overrides(self, **overrides: Any) -> "ManagementGridSpec":
        updates = {key: value for key, value in overrides.items() if value is not None}
        if "engine" in updates and updates["engine"] not in {"reference", "fast"}:
            raise ManagementGridConfigError("engine must be either 'reference' or 'fast'")
        if "reference_fallback" in updates:
            updates["reference_fallback"] = _bool(updates["reference_fallback"], "reference_fallback")
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["survivors"] = [survivor.to_dict() for survivor in self.survivors]
        payload["factor_versions"] = dict(self.factor_versions)
        payload["label_versions"] = dict(self.label_versions)
        payload["baseline_management_config"] = dict(self.baseline_management_config)
        payload["baseline_portfolio_config"] = dict(self.baseline_portfolio_config)
        payload["parameter_space"] = {
            group: {name: list(values) for name, values in dimensions.items()}
            for group, dimensions in self.parameter_space.items()
        }
        payload["fast_path_features"] = list(self.fast_path_features)
        payload["rejection_rules"] = [rule.to_dict() for rule in self.rejection_rules]
        payload["initial_cash"] = str(self.initial_cash)
        payload["workflow_steps"] = list(self.workflow_steps)
        return payload


@dataclass(frozen=True, slots=True)
class CompletedManagementConfig:
    """Completed management configuration result used for output assembly."""

    config: ManagementGridConfiguration
    management_spec: ManagementSpec
    engine_requested: str
    engine_used: str
    result: Any
    execution_config: ReferenceEngineConfig
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManagementGridRunResult:
    """Result of one bounded local survivor management-grid run."""

    grid_id: str
    candidate_id: str
    run_id: str
    combination_count: int
    completed_count: int
    rejected_count: int
    output_paths: ManagementOutputPaths
    registry_path: str | None
    registry_written: bool
    manifest: Mapping[str, Any]
    warnings: tuple[str, ...]
    failed_steps: tuple[str, ...]
    eligibility: CandidateEligibilityDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_id": self.grid_id,
            "candidate_id": self.candidate_id,
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
            "eligibility": self.eligibility.to_dict(),
        }


def load_management_grid_spec(path: str | Path) -> ManagementGridSpec:
    """Load a JSON management-grid spec from disk."""
    config_path = Path(path).expanduser().resolve(strict=False)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ManagementGridConfigError("management grid config root must be a JSON object")
    return ManagementGridSpec.from_mapping(payload)


def ordered_management_parameters(
    parameter_space: Mapping[str, Mapping[str, Sequence[Any]]],
) -> tuple[ManagementGridParameter, ...]:
    """Return management-grid dimensions in deterministic order."""
    unknown_groups = tuple(sorted(set(parameter_space).difference(MANAGEMENT_GRID_PARAMETER_GROUPS)))
    if unknown_groups:
        raise ManagementGridExpansionError(f"unsupported management grid group(s): {', '.join(unknown_groups)}")
    parameters: list[ManagementGridParameter] = []
    for group in MANAGEMENT_PARAMETER_ORDER:
        dimensions = parameter_space.get(group, {})
        if not isinstance(dimensions, Mapping):
            raise ManagementGridExpansionError(f"parameter_space.{group} must be a mapping")
        for name in sorted(dimensions):
            path = f"{group}.{name}"
            if path not in SUPPORTED_MANAGEMENT_PARAMETER_PATHS:
                raise ManagementGridExpansionError(f"unsupported management grid parameter: {path}")
            parameters.append(
                ManagementGridParameter(
                    group=group,
                    name=str(name),
                    values=_finite_values(dimensions[name], path),
                )
            )
    return tuple(parameters)


def count_management_grid_combinations(parameter_space: Mapping[str, Mapping[str, Sequence[Any]]]) -> int:
    """Count finite management-grid combinations without materializing them."""
    return product_count(len(parameter.values) for parameter in ordered_management_parameters(parameter_space))


def expand_management_grid(
    *,
    grid_id: str,
    parameter_space: Mapping[str, Mapping[str, Sequence[Any]]],
    max_combinations: int,
) -> ManagementGridExpansion:
    """Expand a finite management grid and raise before materialization on overflow."""
    parameters = ordered_management_parameters(parameter_space)
    count = product_count(len(parameter.values) for parameter in parameters)
    try:
        CombinationLimit(max_combinations).enforce(count, grid_id=grid_id)
    except GridLimitError as exc:
        rejection = RejectedManagementConfig(
            management_grid_run_id="pending",
            candidate_id="pending",
            config_id="grid",
            reason=str(exc),
            parameters={"combination_count": count, "max_combinations": max_combinations},
        )
        raise ManagementGridExpansionError(
            str(exc),
            rejected_configs=(rejection,),
            count=count,
            max_combinations=max_combinations,
        ) from exc

    paths = tuple(parameter.path for parameter in parameters)
    configurations = []
    value_product = itertools.product(*(parameter.values for parameter in parameters))
    for index, values in enumerate(value_product, start=1):
        configurations.append(
            ManagementGridConfiguration(
                config_id=f"mgmt_{index:06d}",
                ordinal=index,
                parameters=dict(zip(paths, values, strict=True)),
            )
        )
    return ManagementGridExpansion(
        grid_id=grid_id,
        parameters=parameters,
        configurations=tuple(configurations),
        combination_count=count,
        max_combinations=max_combinations,
    )


def run_management_grid(spec: ManagementGridSpec, *, repo_root: str | Path | None = None) -> ManagementGridRunResult:
    """Run a bounded local survivor management grid and write required outputs."""
    root = Path(repo_root).resolve(strict=False) if repo_root is not None else Path.cwd()
    config_payload = spec.to_dict()
    config_hash = hash_config(config_payload)
    expansion = expand_management_grid(
        grid_id=spec.grid_id,
        parameter_space=spec.parameter_space,
        max_combinations=spec.max_combinations,
    )
    survivor = spec.selected_survivor
    try:
        eligibility = assert_candidate_eligible(
            survivor,
            parameter_paths=expansion.parameter_paths,
            max_combinations=spec.max_combinations,
        )
    except CandidateEligibilityError as exc:
        raise ManagementGridRunError(str(exc)) from exc

    run_id = spec.run_id or generate_run_id(
        "management-grid",
        seed=f"{spec.grid_id}:{spec.candidate_id}",
        components={
            "grid_id": spec.grid_id,
            "candidate_id": spec.candidate_id,
            "data_version": spec.data_version,
            "factor_versions": dict(spec.factor_versions),
            "label_versions": dict(spec.label_versions),
            "config_hash": config_hash,
        },
    )
    output_paths = resolve_management_output_paths(spec.output_dir, manifest_path=spec.manifest_path)
    base_execution_config = _base_execution_config(spec)
    _assert_cost_config_allowed(spec, base_execution_config)
    baseline_management = ManagementSpec.from_mapping(spec.baseline_management_config)
    bars, signals = _fixture_inputs(spec)
    baseline_result = run_reference_backtest_with_management(
        bars=bars,
        signals=signals,
        management_spec=baseline_management,
        config=base_execution_config,
        strategy_id=spec.strategy_id,
        strategy_version=spec.strategy_version,
        data_version=spec.data_version,
        factor_versions=spec.factor_versions,
        initial_cash=spec.initial_cash,
        run_id=f"{run_id}-baseline",
    )

    completed: list[CompletedManagementConfig] = []
    rejected: list[RejectedManagementConfig] = []
    failed_steps: list[str] = []

    for config in expansion.configurations:
        rule_reason = _rejection_reason(spec, config)
        if rule_reason is not None:
            rejected.append(_rejected(run_id, spec.candidate_id, config, rule_reason))
            continue
        try:
            completed.append(
                _run_single_config(
                    spec,
                    config,
                    run_id=run_id,
                    base_execution_config=base_execution_config,
                )
            )
        except (ManagementGridRunError, ManagementSpecError, ReferenceBacktestError, ValueError) as exc:
            reason = str(exc)
            rejected.append(_rejected(run_id, spec.candidate_id, config, reason))
            failed_steps.append(f"{config.config_id}: {reason}")

    overfit = assess_management_overfit_controls(
        combination_count=expansion.combination_count,
        max_combinations=spec.max_combinations,
        parameter_paths=expansion.parameter_paths,
        survivor_warning_count=len(survivor.warnings),
        rejected_count=len(rejected),
    )
    warnings = tuple(
        dict.fromkeys(
            (
                *eligibility.warnings,
                *overfit.warnings,
                *_run_warnings(completed),
            )
        )
    )
    leaderboard = rank_management_leaderboard(_leaderboard_rows(run_id, spec, completed))
    baseline_rows = _baseline_comparison_rows(run_id, spec.candidate_id, baseline_result, leaderboard)
    monthly_rows = _monthly_breakdown_rows(run_id, spec.candidate_id, completed)
    cost_rows = _cost_sensitivity_rows(run_id, spec.candidate_id, completed)
    survivor_summary = {
        "candidate_id": spec.candidate_id,
        "eligible": eligibility.eligible,
        "reasons": list(eligibility.reasons),
        "warnings": list(eligibility.warnings),
        "review_status": survivor.review_status,
        "source_run_id": survivor.source_run_id,
        "source_grid_config_hash": survivor.source_grid_config_hash,
        "allowed_management_grid_scope": dict(survivor.allowed_management_grid_scope),
    }
    manifest_parameters = {
        "grid_id": spec.grid_id,
        "candidate_id": spec.candidate_id,
        "source_run_id": survivor.source_run_id,
        "source_grid_config_hash": survivor.source_grid_config_hash,
        "combination_count": expansion.combination_count,
        "completed_count": len(completed),
        "rejected_count": len(rejected),
        "parameter_paths": list(expansion.parameter_paths),
        "engine_requested": spec.engine,
        "fast_path_features": list(spec.fast_path_features),
        "workflow_steps": list(spec.workflow_steps),
        "overfit_controls": overfit.to_dict(),
        "baseline_portfolio_config": dict(spec.baseline_portfolio_config),
    }
    manifest = _build_management_manifest(
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
        warnings=warnings,
        failed_steps=tuple(dict.fromkeys(failed_steps)),
        repo_root=root,
    )
    write_management_outputs(
        paths=output_paths,
        baseline_comparison=baseline_rows,
        leaderboard=leaderboard,
        rejected_configs=tuple(rejected),
        monthly_breakdown=monthly_rows,
        cost_sensitivity=cost_rows,
        manifest=manifest,
        warnings=warnings,
        survivor_eligibility_summary=survivor_summary,
    )

    registry_written = False
    registry_path = None
    if spec.registry_path:
        registry_path = _record_management_grid_run(
            spec,
            run_id=run_id,
            config_hash=config_hash,
            artifact_paths=output_paths.to_dict(),
            parameters=manifest_parameters,
            warnings=warnings,
            repo_root=root,
        )
        registry_written = True

    return ManagementGridRunResult(
        grid_id=spec.grid_id,
        candidate_id=spec.candidate_id,
        run_id=run_id,
        combination_count=expansion.combination_count,
        completed_count=len(completed),
        rejected_count=len(rejected),
        output_paths=output_paths,
        registry_path=registry_path,
        registry_written=registry_written,
        manifest=manifest,
        warnings=warnings,
        failed_steps=tuple(dict.fromkeys(failed_steps)),
        eligibility=eligibility,
    )


def _run_single_config(
    spec: ManagementGridSpec,
    config: ManagementGridConfiguration,
    *,
    run_id: str,
    base_execution_config: ReferenceEngineConfig,
) -> CompletedManagementConfig:
    management_payload = _management_payload_for_parameters(
        spec.baseline_management_config,
        config.parameters,
        config_id=config.config_id,
    )
    management_spec = ManagementSpec.from_mapping(management_payload)
    execution_config = _execution_config_for_parameters(base_execution_config, config.parameters)
    _assert_cost_config_allowed(spec, execution_config)
    bars, signals = _fixture_inputs(spec)
    requested_features = spec.fast_path_features or _features_for_management(spec, management_spec, config.parameters)
    warnings: list[str] = []

    if spec.engine == "reference":
        result = run_reference_backtest_with_management(
            bars=bars,
            signals=signals,
            management_spec=management_spec,
            config=execution_config,
            strategy_id=spec.strategy_id,
            strategy_version=spec.strategy_version,
            data_version=spec.data_version,
            factor_versions=spec.factor_versions,
            initial_cash=spec.initial_cash,
            run_id=f"{run_id}-{config.config_id}",
        )
        return CompletedManagementConfig(
            config=config,
            management_spec=management_spec,
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
            raise ManagementGridRunError(f"fast path parity gate failed closed: {exc}") from exc
        warnings.append(f"fast path parity gate routed to reference fallback: {exc}")
        result = run_reference_backtest_with_management(
            bars=bars,
            signals=signals,
            management_spec=management_spec,
            config=execution_config,
            strategy_id=spec.strategy_id,
            strategy_version=spec.strategy_version,
            data_version=spec.data_version,
            factor_versions=spec.factor_versions,
            initial_cash=spec.initial_cash,
            run_id=f"{run_id}-{config.config_id}",
        )
        warnings.extend(result.summary.warnings)
        return CompletedManagementConfig(
            config=config,
            management_spec=management_spec,
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
        management_spec=management_spec,
        requested_features=requested_features,
        strategy_id=spec.strategy_id,
        strategy_version=spec.strategy_version,
        data_version=spec.data_version,
        factor_versions=spec.factor_versions,
        initial_cash=spec.initial_cash,
        run_id=f"{run_id}-{config.config_id}",
        allow_reference_fallback=False,
    )
    if fast_run.mode != FAST_PATH_MODE_ACCELERATED:
        raise ManagementGridRunError(f"fast path returned non-accelerated mode {fast_run.mode!r}")
    return CompletedManagementConfig(
        config=config,
        management_spec=management_spec,
        engine_requested=spec.engine,
        engine_used="fast",
        result=fast_run.result,
        execution_config=execution_config,
        warnings=tuple(fast_run.result.summary.warnings),
    )


def _base_execution_config(spec: ManagementGridSpec) -> ReferenceEngineConfig:
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
    return replace(base_config, cost_model=cost_model)


def _assert_cost_config_allowed(spec: ManagementGridSpec, config: ReferenceEngineConfig) -> None:
    if spec.allow_fixture_zero_cost:
        return
    if config.cost_model.fixed_bps == 0 and config.cost_model.minimum_cost == 0:
        raise ManagementGridRunError("zero execution cost requires allow_fixture_zero_cost=true")


def _fixture_inputs(spec: ManagementGridSpec) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    if spec.direction == "short":
        bars = falling_bars(5, start_price=100)
    else:
        bars = (
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="102.5", low="99", close="101"),
            synthetic_bar(2, open_price="102", high="103", low="100.5", close="102"),
            synthetic_bar(3, open_price="102", high="103", low="101", close="102"),
            synthetic_bar(4, open_price="102", high="103", low="101", close="102"),
        )
    if spec.signal_pattern == "no_trade":
        signals = no_trade_signals()
    elif spec.signal_pattern == "entry_exit":
        signals = (
            signal_record(0, "entry", signal_id=f"{spec.direction}-entry", direction=spec.direction),
            signal_record(3, "exit", signal_id=f"{spec.direction}-exit", direction=spec.direction),
        )
    else:
        signals = (signal_record(0, "entry", signal_id=f"{spec.direction}-entry", direction=spec.direction),)
    return (
        tuple(_with_versions(bar, spec) for bar in bars),
        tuple(_with_versions(signal, spec) for signal in signals),
    )


def _with_versions(row: Mapping[str, Any], spec: ManagementGridSpec) -> dict[str, Any]:
    payload = dict(row)
    payload["data_version"] = spec.data_version
    if "strategy_id" in payload:
        payload["strategy_id"] = spec.strategy_id
        payload["strategy_version"] = spec.strategy_version
        payload["factor_versions"] = dict(spec.factor_versions)
    return payload


def _management_payload_for_parameters(
    baseline: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    config_id: str,
) -> dict[str, Any]:
    payload = json.loads(json.dumps(dict(baseline), sort_keys=True, default=str))
    payload["management_id"] = f"{payload.get('management_id', 'management:grid')}:{config_id}"
    for path, value in parameters.items():
        if not path.startswith("management."):
            continue
        active = path.removeprefix("management.")
        if active == "fixed_stop.stop_pct":
            _rule_update(payload, "fixed_stop", {"stop_pct": value})
        elif active == "fixed_stop.stop_price":
            _rule_update(payload, "fixed_stop", {"stop_price": value})
        elif active == "target_r_multiple.r_multiple":
            _rule_update(payload, "target_r_multiple", {"r_multiple": value})
        elif active == "laddered_partial_take_profit.steps":
            _rule_update(payload, "laddered_partial_take_profit", {"steps": value})
        elif active == "trailing_stop.trail_r":
            _rule_update(payload, "trailing_stop", {"trail_r": value})
        elif active == "trailing_stop.trail_pct":
            _rule_update(payload, "trailing_stop", {"trail_pct": value})
        elif active == "breakeven_stop.trigger_r":
            _rule_update(payload, "breakeven_stop", {"trigger_r": value})
        elif active == "breakeven_stop.offset_r":
            _rule_update(payload, "breakeven_stop", {"offset_r": value}, force_enabled=False)
        elif active == "max_holding_bars.max_bars":
            _rule_update(payload, "max_holding_bars", {"max_bars": value})
        elif active == "cooldown.bars":
            _rule_update(payload, "cooldown", {"bars": value})
        elif active == "eod_exit.enabled":
            payload["eod_exit"] = {"enabled": _bool(value, active)}
        elif active == "time_exit.max_minutes":
            _rule_update(payload, "time_exit", {"max_minutes": value})
        elif active == "max_trades_per_day.limit":
            _rule_update(payload, "max_trades_per_day", {"limit": value})
    return payload


def _rule_update(
    payload: dict[str, Any],
    rule_name: str,
    updates: Mapping[str, Any],
    *,
    force_enabled: bool = True,
) -> None:
    current = payload.get(rule_name)
    if isinstance(current, Mapping):
        rule = dict(current)
    elif current in (None, False):
        rule = {}
    else:
        rule = {"enabled": True}
    rule.update(dict(updates))
    if force_enabled:
        rule["enabled"] = True
    payload[rule_name] = rule


def _features_for_management(
    spec: ManagementGridSpec,
    management_spec: ManagementSpec,
    parameters: Mapping[str, Any],
) -> tuple[str, ...]:
    features: set[str] = {"trade_summary", "equity_curve"}
    if spec.signal_pattern == "no_trade":
        features.add("no_trade")
    elif spec.direction == "short":
        features.add("simple_short")
    else:
        features.add("simple_long")
    if _has_positive(parameters.get("execution.fixed_bps")):
        features.add("costs")
    if management_spec.fixed_stop.enabled:
        features.add("management_fixed_stop")
    if management_spec.target_r_multiple.enabled:
        features.add("management_target")
    if management_spec.laddered_partial_take_profit.enabled:
        features.add("partial_exit")
    if management_spec.eod_exit.enabled:
        features.add("management_eod_exit")
    if management_spec.cooldown.enabled:
        features.add("cooldown")
    if management_spec.max_holding_bars.enabled:
        features.add("max_holding_bars")
    if management_spec.trailing_stop.enabled:
        features.add("trailing_stop")
    if management_spec.breakeven_stop.enabled:
        features.add("breakeven_stop")
    return tuple(sorted(features))


def _rejection_reason(spec: ManagementGridSpec, config: ManagementGridConfiguration) -> str | None:
    for rule in spec.rejection_rules:
        if rule.matches(config.parameters):
            return rule.reason
    return None


def _rejected(
    run_id: str,
    candidate_id: str,
    config: ManagementGridConfiguration,
    reason: str,
) -> RejectedManagementConfig:
    return RejectedManagementConfig(
        management_grid_run_id=run_id,
        candidate_id=candidate_id,
        config_id=config.config_id,
        reason=reason,
        parameters=dict(config.parameters),
    )


def _leaderboard_rows(
    run_id: str,
    spec: ManagementGridSpec,
    completed: Sequence[CompletedManagementConfig],
) -> tuple[ManagementLeaderboardRow, ...]:
    rows: list[ManagementLeaderboardRow] = []
    for item in completed:
        summary = item.result.summary
        rows.append(
            ManagementLeaderboardRow(
                rank=0,
                management_grid_run_id=run_id,
                candidate_id=spec.candidate_id,
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


def _baseline_comparison_rows(
    run_id: str,
    candidate_id: str,
    baseline_result: Any,
    leaderboard: Sequence[ManagementLeaderboardRow],
) -> tuple[BaselineComparisonRow, ...]:
    rows: list[BaselineComparisonRow] = []
    baseline_summary = baseline_result.summary
    baseline_values = {
        "net_pnl": baseline_summary.net_pnl,
        "final_equity": baseline_summary.final_equity,
        "total_trades": Decimal(baseline_summary.total_trades),
        "costs": baseline_summary.costs,
    }
    for row in leaderboard:
        candidate_values = {
            "net_pnl": row.net_pnl,
            "final_equity": row.final_equity,
            "total_trades": Decimal(row.total_trades),
            "costs": row.costs,
        }
        for metric, baseline_value in baseline_values.items():
            candidate_value = candidate_values[metric]
            rows.append(
                BaselineComparisonRow(
                    management_grid_run_id=run_id,
                    candidate_id=candidate_id,
                    config_id=row.config_id,
                    baseline_config_id="baseline_management",
                    metric=metric,
                    baseline_value=_decimal_text(baseline_value),
                    candidate_value=_decimal_text(candidate_value),
                    delta=_decimal_text(candidate_value - baseline_value),
                )
            )
    return tuple(rows)


def _monthly_breakdown_rows(
    run_id: str,
    candidate_id: str,
    completed: Sequence[CompletedManagementConfig],
) -> tuple[ManagementMonthlyBreakdownRow, ...]:
    rows = []
    for item in sorted(completed, key=lambda entry: entry.config.config_id):
        summary = item.result.summary
        rows.append(
            ManagementMonthlyBreakdownRow(
                management_grid_run_id=run_id,
                candidate_id=candidate_id,
                config_id=item.config.config_id,
                month=_result_month(item),
                total_trades=summary.total_trades,
                net_pnl=_decimal_text(summary.net_pnl),
                final_equity=_decimal_text(summary.final_equity),
                warning_count=len(item.warnings),
            )
        )
    return tuple(rows)


def _cost_sensitivity_rows(
    run_id: str,
    candidate_id: str,
    completed: Sequence[CompletedManagementConfig],
) -> tuple[ManagementCostSensitivityRow, ...]:
    rows = []
    for item in sorted(completed, key=lambda entry: entry.config.config_id):
        summary = item.result.summary
        cost_model = item.execution_config.cost_model
        rows.append(
            ManagementCostSensitivityRow(
                management_grid_run_id=run_id,
                candidate_id=candidate_id,
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


def _record_management_grid_run(
    spec: ManagementGridSpec,
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
        raise ManagementGridRunError(str(exc)) from exc
    status = init_registry(registry_path)
    if not status.valid:
        raise ManagementGridRunError(f"registry is not valid: {status.status_message}")
    git_info = capture_git_info(repo_root)
    record = RunRecord(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=_management_grid_code_hash(repo_root),
        config_hash=config_hash,
        data_version=spec.data_version,
        factor_versions=dict(spec.factor_versions),
        label_versions=dict(spec.label_versions),
        engine_version=spec.engine_version,
        parameters=parameters,
        artifact_paths=artifact_paths,
        decision_status="management_grid_recorded",
        warnings=tuple(warnings),
        status_message="Management grid recorded as review-only evidence; no promotion decision.",
    )
    with connect_registry(registry_path) as connection:
        insert_run_record(connection, "grid_runs", record)
    return registry_path.as_posix()


def _build_management_manifest(
    *,
    run_id: str,
    grid_id: str,
    engine_version: str,
    config_hash: str,
    config_payload: Mapping[str, Any],
    data_version: str,
    factor_versions: Mapping[str, str],
    label_versions: Mapping[str, str],
    parameters: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
    warnings: Sequence[str],
    failed_steps: Sequence[str],
    repo_root: Path,
) -> dict[str, Any]:
    git_info = capture_git_info(repo_root)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "grid_id": grid_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "git_commit": git_info.commit,
        "git_dirty": git_info.dirty,
        "git_status_message": git_info.status_message,
        "code_hash": _management_grid_code_hash(repo_root),
        "config_hash": config_hash,
        "config": dict(config_payload),
        "data_version": data_version,
        "factor_versions": dict(sorted(factor_versions.items())),
        "label_versions": dict(sorted(label_versions.items())),
        "engine_version": engine_version,
        "parameters": dict(parameters),
        "artifact_paths": dict(sorted(artifact_paths.items())),
        "decision_status": "research_evidence_only",
        "candidate_decision": "not_made_by_management_grid",
        "promotion_decision": None,
        "warnings": list(warnings),
        "failed_steps": list(failed_steps),
    }
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    return payload


def _run_warnings(completed: Sequence[CompletedManagementConfig]) -> tuple[str, ...]:
    warnings: list[str] = []
    for item in completed:
        warnings.extend(item.warnings)
    return tuple(dict.fromkeys(warnings))


def _result_month(item: CompletedManagementConfig) -> str:
    if item.result.equity_curve:
        return item.result.equity_curve[-1].bar_end_ts.strftime("%Y-%m")
    return "unknown"


def _management_grid_code_hash(repo_root: Path) -> str:
    module_root = Path(__file__).resolve().parent
    paths = tuple(module_root / name for name in MANAGEMENT_GRID_CODE_MODULES if (module_root / name).exists())
    if not paths:
        return hash_config({"module": __name__, "available": False})
    try:
        return hash_code_paths(paths, root=repo_root)
    except ValueError:
        return hash_code_paths(paths)


def _parameter_space(value: Any) -> dict[str, dict[str, tuple[Any, ...]]]:
    if not isinstance(value, Mapping) or not value:
        raise ManagementGridConfigError("parameter_space must be a non-empty mapping")
    unknown = tuple(sorted(set(str(key) for key in value).difference(MANAGEMENT_GRID_PARAMETER_GROUPS)))
    if unknown:
        raise ManagementGridConfigError(f"unsupported management grid group(s): {', '.join(unknown)}")
    normalized: dict[str, dict[str, tuple[Any, ...]]] = {}
    for group in MANAGEMENT_GRID_PARAMETER_GROUPS:
        dimensions = value.get(group, {})
        if dimensions in ({}, None):
            continue
        if not isinstance(dimensions, Mapping):
            raise ManagementGridConfigError(f"parameter_space.{group} must be a mapping")
        normalized[group] = {}
        for name, raw_values in dimensions.items():
            path = f"{group}.{name}"
            if path not in SUPPORTED_MANAGEMENT_PARAMETER_PATHS:
                raise ManagementGridConfigError(f"unsupported management grid parameter: {path}")
            normalized[group][str(name)] = _finite_values(raw_values, path)
    if not any(normalized.values()):
        raise ManagementGridConfigError("parameter_space must contain at least one finite parameter")
    return normalized


def _finite_values(value: Any, path: str) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        if "values" not in value:
            raise ManagementGridConfigError(f"parameter_space.{path} must use explicit values")
        value = value["values"]
    if value in (None, "", "*"):
        raise ManagementGridConfigError(f"parameter_space.{path} is unbounded")
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ManagementGridConfigError(f"parameter_space.{path} must be an explicit finite list")
    values = tuple(value)
    if not values:
        raise ManagementGridConfigError(f"parameter_space.{path} must contain at least one value")
    if any(item in (None, "", "*") for item in values):
        raise ManagementGridConfigError(f"parameter_space.{path} contains an unbounded value")
    return values


def _version_map(value: Any, field_name: str, *, allow_empty: bool) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ManagementGridConfigError(f"{field_name} must be a mapping")
    if not value and not allow_empty:
        raise ManagementGridConfigError(f"{field_name} must contain at least one version")
    return {_text(key, f"{field_name} key"): _text(version, f"{field_name} value") for key, version in value.items()}


def _workflow_steps(value: Any) -> tuple[str, ...]:
    if value is None:
        return SURVIVOR_WORKFLOW_STEPS
    steps = _text_tuple(value, "workflow_steps")
    if steps != SURVIVOR_WORKFLOW_STEPS:
        raise ManagementGridConfigError("workflow_steps must match the required survivor workflow order")
    return steps


def _text_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (_text(value, field_name),)
    if not isinstance(value, Sequence):
        raise ManagementGridConfigError(f"{field_name} must be a string or list of strings")
    return tuple(_text(item, field_name) for item in value)


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == {}


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManagementGridConfigError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value in (None, ""):
        return None
    return _text(value, field_name)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ManagementGridConfigError(f"{field_name} must be a positive integer")
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        raise ManagementGridConfigError(f"{field_name} must be a positive integer") from exc
    if active <= 0:
        raise ManagementGridConfigError(f"{field_name} must be positive")
    return active


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise ManagementGridConfigError(f"{field_name} must be boolean")


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= 0:
        raise ManagementGridConfigError(f"{field_name} must be positive")
    return active


def _decimal(value: Any, field_name: str = "value") -> Decimal:
    if isinstance(value, bool):
        raise ManagementGridRunError(f"{field_name} must be numeric")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ManagementGridRunError(f"{field_name} must be numeric") from exc


def _has_positive(value: Any) -> bool:
    if value in (None, ""):
        return False
    return _decimal(value, "value") > 0


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
