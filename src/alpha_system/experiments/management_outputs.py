"""Schema-defined output writers for local management-grid artifacts."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import canonical_json
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.reports.prohibited_claims import validate_no_prohibited_claims


DEFAULT_MANAGEMENT_OUTPUT_ROOT = Path("artifacts") / "management_studies"
FORBIDDEN_MANAGEMENT_OUTPUT_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".log",
)

BASELINE_COMPARISON_COLUMNS: tuple[str, ...] = (
    "management_grid_run_id",
    "candidate_id",
    "config_id",
    "baseline_config_id",
    "metric",
    "baseline_value",
    "candidate_value",
    "delta",
)

MANAGEMENT_LEADERBOARD_COLUMNS: tuple[str, ...] = (
    "rank",
    "management_grid_run_id",
    "candidate_id",
    "config_id",
    "engine_requested",
    "engine_used",
    "total_trades",
    "open_positions",
    "gross_pnl",
    "costs",
    "net_pnl",
    "final_equity",
    "warning_count",
    "parameters_json",
    "decision_status",
)

MANAGEMENT_REJECTED_CONFIG_COLUMNS: tuple[str, ...] = (
    "management_grid_run_id",
    "candidate_id",
    "config_id",
    "status",
    "reason",
    "parameters_json",
)

MANAGEMENT_MONTHLY_BREAKDOWN_COLUMNS: tuple[str, ...] = (
    "management_grid_run_id",
    "candidate_id",
    "config_id",
    "month",
    "total_trades",
    "net_pnl",
    "final_equity",
    "warning_count",
)

MANAGEMENT_COST_SENSITIVITY_COLUMNS: tuple[str, ...] = (
    "management_grid_run_id",
    "candidate_id",
    "config_id",
    "cost_model",
    "fixed_bps",
    "minimum_cost",
    "total_trades",
    "costs",
    "net_pnl",
)

REQUIRED_MANAGEMENT_OUTPUT_FILENAMES: tuple[str, ...] = (
    "baseline_comparison.csv",
    "leaderboard.csv",
    "rejected_configs.csv",
    "monthly_breakdown.csv",
    "cost_sensitivity.csv",
    "run_manifest.json",
    "warnings.json",
    "survivor_eligibility_summary.json",
)


class ManagementOutputError(ValueError):
    """Raised when management output policy or schema writing fails."""


@dataclass(frozen=True, slots=True)
class BaselineComparisonRow:
    management_grid_run_id: str
    candidate_id: str
    config_id: str
    baseline_config_id: str
    metric: str
    baseline_value: str
    candidate_value: str
    delta: str

    def to_csv_row(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManagementLeaderboardRow:
    rank: int
    management_grid_run_id: str
    candidate_id: str
    config_id: str
    engine_requested: str
    engine_used: str
    total_trades: int
    open_positions: int
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    final_equity: Decimal
    warning_count: int
    parameters: Mapping[str, Any]
    decision_status: str = "research_evidence_only"

    def to_csv_row(self) -> dict[str, str]:
        return {
            "rank": str(self.rank),
            "management_grid_run_id": self.management_grid_run_id,
            "candidate_id": self.candidate_id,
            "config_id": self.config_id,
            "engine_requested": self.engine_requested,
            "engine_used": self.engine_used,
            "total_trades": str(self.total_trades),
            "open_positions": str(self.open_positions),
            "gross_pnl": _decimal_text(self.gross_pnl),
            "costs": _decimal_text(self.costs),
            "net_pnl": _decimal_text(self.net_pnl),
            "final_equity": _decimal_text(self.final_equity),
            "warning_count": str(self.warning_count),
            "parameters_json": canonical_json(self.parameters),
            "decision_status": self.decision_status,
        }


@dataclass(frozen=True, slots=True)
class ManagementMonthlyBreakdownRow:
    management_grid_run_id: str
    candidate_id: str
    config_id: str
    month: str
    total_trades: int
    net_pnl: str
    final_equity: str
    warning_count: int

    def to_csv_row(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class ManagementCostSensitivityRow:
    management_grid_run_id: str
    candidate_id: str
    config_id: str
    cost_model: str
    fixed_bps: str
    minimum_cost: str
    total_trades: int
    costs: str
    net_pnl: str

    def to_csv_row(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class ManagementOutputPaths:
    output_dir: str
    baseline_comparison_path: str
    leaderboard_path: str
    rejected_configs_path: str
    monthly_breakdown_path: str
    cost_sensitivity_path: str
    manifest_path: str
    warnings_path: str
    survivor_eligibility_summary_path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def resolve_management_output_dir(output_dir: str | Path | None) -> Path:
    """Resolve a local-only management-grid output directory."""
    candidate = assert_local_wsl_path(output_dir or DEFAULT_MANAGEMENT_OUTPUT_ROOT)
    if candidate.suffix.lower() in FORBIDDEN_MANAGEMENT_OUTPUT_SUFFIXES:
        raise ManagementOutputError("management output directory must not be a DB, log, or columnar path")
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_MANAGEMENT_OUTPUT_ROOT
        if not _is_relative_to(candidate, allowed):
            raise ManagementOutputError("management outputs inside the repo must stay under artifacts/management_studies")
    return candidate


def resolve_management_output_paths(
    output_dir: str | Path | None,
    *,
    manifest_path: str | Path | None = None,
) -> ManagementOutputPaths:
    """Resolve all required management output paths before writing."""
    root = resolve_management_output_dir(output_dir)
    active_manifest = root / "run_manifest.json" if manifest_path is None else assert_local_wsl_path(manifest_path)
    if active_manifest.suffix.lower() != ".json":
        raise ManagementOutputError("management run manifest must be a JSON file")
    repo_root = repository_root_from_module()
    if _is_relative_to(active_manifest, repo_root):
        allowed = repo_root / DEFAULT_MANAGEMENT_OUTPUT_ROOT
        if not _is_relative_to(active_manifest, allowed):
            raise ManagementOutputError("management manifests inside the repo must stay under artifacts/management_studies")
    return ManagementOutputPaths(
        output_dir=root.as_posix(),
        baseline_comparison_path=(root / "baseline_comparison.csv").as_posix(),
        leaderboard_path=(root / "leaderboard.csv").as_posix(),
        rejected_configs_path=(root / "rejected_configs.csv").as_posix(),
        monthly_breakdown_path=(root / "monthly_breakdown.csv").as_posix(),
        cost_sensitivity_path=(root / "cost_sensitivity.csv").as_posix(),
        manifest_path=active_manifest.as_posix(),
        warnings_path=(root / "warnings.json").as_posix(),
        survivor_eligibility_summary_path=(root / "survivor_eligibility_summary.json").as_posix(),
    )


def write_management_outputs(
    *,
    paths: ManagementOutputPaths,
    baseline_comparison: Sequence[BaselineComparisonRow],
    leaderboard: Sequence[ManagementLeaderboardRow],
    rejected_configs: Sequence[Any],
    monthly_breakdown: Sequence[ManagementMonthlyBreakdownRow],
    cost_sensitivity: Sequence[ManagementCostSensitivityRow],
    manifest: Mapping[str, Any],
    warnings: Sequence[str],
    survivor_eligibility_summary: Mapping[str, Any],
) -> None:
    """Write the exact required management-grid output files."""
    payloads = (
        [row.to_csv_row() for row in baseline_comparison],
        [row.to_csv_row() for row in leaderboard],
        [row.to_csv_row() for row in monthly_breakdown],
        [row.to_csv_row() for row in cost_sensitivity],
        dict(manifest),
        list(warnings),
        dict(survivor_eligibility_summary),
    )
    for payload in payloads:
        validate_no_prohibited_claims(payload, context="management grid output")

    root = Path(paths.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        Path(paths.baseline_comparison_path),
        BASELINE_COMPARISON_COLUMNS,
        (row.to_csv_row() for row in baseline_comparison),
    )
    _write_csv(
        Path(paths.leaderboard_path),
        MANAGEMENT_LEADERBOARD_COLUMNS,
        (row.to_csv_row() for row in leaderboard),
    )
    _write_csv(
        Path(paths.rejected_configs_path),
        MANAGEMENT_REJECTED_CONFIG_COLUMNS,
        (_rejected_row(rejected) for rejected in rejected_configs),
    )
    _write_csv(
        Path(paths.monthly_breakdown_path),
        MANAGEMENT_MONTHLY_BREAKDOWN_COLUMNS,
        (row.to_csv_row() for row in monthly_breakdown),
    )
    _write_csv(
        Path(paths.cost_sensitivity_path),
        MANAGEMENT_COST_SENSITIVITY_COLUMNS,
        (row.to_csv_row() for row in cost_sensitivity),
    )
    Path(paths.warnings_path).write_text(
        json.dumps(list(warnings), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    Path(paths.survivor_eligibility_summary_path).write_text(
        json.dumps(dict(survivor_eligibility_summary), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    Path(paths.manifest_path).write_text(
        json.dumps(dict(manifest), sort_keys=True, indent=2),
        encoding="utf-8",
    )


def rank_management_leaderboard(rows: Sequence[ManagementLeaderboardRow]) -> tuple[ManagementLeaderboardRow, ...]:
    """Rank completed management configs deterministically."""
    from dataclasses import replace

    ordered = sorted(
        rows,
        key=lambda row: (
            -row.net_pnl,
            -row.final_equity,
            row.costs,
            row.config_id,
        ),
    )
    return tuple(replace(row, rank=index) for index, row in enumerate(ordered, start=1))


def _write_csv(path: Path, columns: Sequence[str], rows: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _rejected_row(rejected: Any) -> dict[str, str]:
    return {
        "management_grid_run_id": rejected.management_grid_run_id,
        "candidate_id": rejected.candidate_id,
        "config_id": rejected.config_id,
        "status": rejected.status,
        "reason": rejected.reason,
        "parameters_json": canonical_json(rejected.parameters),
    }


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
