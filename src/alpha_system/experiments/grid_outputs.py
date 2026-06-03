"""Schema-defined output writers for local strategy-grid artifacts."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import canonical_json
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.experiments.grid import RejectedGridConfig
from alpha_system.experiments.leaderboard import LEADERBOARD_COLUMNS, LeaderboardRow


DEFAULT_GRID_OUTPUT_ROOT = Path("artifacts") / "strategy_grids"
FORBIDDEN_GRID_OUTPUT_SUFFIXES: tuple[str, ...] = (
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

MONTHLY_BREAKDOWN_COLUMNS: tuple[str, ...] = (
    "grid_run_id",
    "config_id",
    "month",
    "total_trades",
    "net_pnl",
    "final_equity",
    "warning_count",
)

COST_SENSITIVITY_COLUMNS: tuple[str, ...] = (
    "grid_run_id",
    "config_id",
    "cost_model",
    "fixed_bps",
    "minimum_cost",
    "total_trades",
    "costs",
    "net_pnl",
)

REJECTED_CONFIG_COLUMNS: tuple[str, ...] = (
    "grid_run_id",
    "config_id",
    "status",
    "reason",
    "parameters_json",
)

REQUIRED_OUTPUT_FILENAMES: tuple[str, ...] = (
    "leaderboard.csv",
    "grid_summary.md",
    "monthly_breakdown.csv",
    "cost_sensitivity.csv",
    "top_configs.yaml",
    "rejected_configs.csv",
    "run_manifest.json",
)

FORBIDDEN_CLAIM_PHRASES: tuple[str, ...] = (
    "profitable",
    "tradable",
    "production-ready",
    "guaranteed alpha",
    "market-beating",
    "approved",
)


class GridOutputError(ValueError):
    """Raised when grid output policy or schema writing fails."""


@dataclass(frozen=True, slots=True)
class MonthlyBreakdownRow:
    grid_run_id: str
    config_id: str
    month: str
    total_trades: int
    net_pnl: str
    final_equity: str
    warning_count: int

    def to_csv_row(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class CostSensitivityRow:
    grid_run_id: str
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
class GridOutputPaths:
    output_dir: str
    leaderboard_path: str
    summary_path: str
    monthly_breakdown_path: str
    cost_sensitivity_path: str
    top_configs_path: str
    rejected_configs_path: str
    manifest_path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def resolve_grid_output_dir(output_dir: str | Path | None) -> Path:
    """Resolve a local-only grid output directory."""
    candidate = assert_local_wsl_path(output_dir or DEFAULT_GRID_OUTPUT_ROOT)
    if candidate.suffix.lower() in FORBIDDEN_GRID_OUTPUT_SUFFIXES:
        msg = "grid output directory must not be a DB, log, or columnar artifact path"
        raise GridOutputError(msg)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        allowed = repo_root / DEFAULT_GRID_OUTPUT_ROOT
        if not _is_relative_to(candidate, allowed):
            msg = "grid outputs inside the repo must stay under artifacts/strategy_grids"
            raise GridOutputError(msg)
    return candidate


def resolve_grid_output_paths(
    output_dir: str | Path | None,
    *,
    manifest_path: str | Path | None = None,
) -> GridOutputPaths:
    """Resolve all required output paths before writing."""
    root = resolve_grid_output_dir(output_dir)
    active_manifest = root / "run_manifest.json" if manifest_path is None else assert_local_wsl_path(manifest_path)
    if active_manifest.suffix.lower() != ".json":
        msg = "grid run manifest must be a JSON file"
        raise GridOutputError(msg)
    repo_root = repository_root_from_module()
    if _is_relative_to(active_manifest, repo_root):
        allowed = repo_root / DEFAULT_GRID_OUTPUT_ROOT
        if not _is_relative_to(active_manifest, allowed):
            msg = "grid manifests inside the repo must stay under artifacts/strategy_grids"
            raise GridOutputError(msg)
    return GridOutputPaths(
        output_dir=root.as_posix(),
        leaderboard_path=(root / "leaderboard.csv").as_posix(),
        summary_path=(root / "grid_summary.md").as_posix(),
        monthly_breakdown_path=(root / "monthly_breakdown.csv").as_posix(),
        cost_sensitivity_path=(root / "cost_sensitivity.csv").as_posix(),
        top_configs_path=(root / "top_configs.yaml").as_posix(),
        rejected_configs_path=(root / "rejected_configs.csv").as_posix(),
        manifest_path=active_manifest.as_posix(),
    )


def write_grid_outputs(
    *,
    paths: GridOutputPaths,
    grid_id: str,
    grid_run_id: str,
    leaderboard: Sequence[LeaderboardRow],
    monthly_breakdown: Sequence[MonthlyBreakdownRow],
    cost_sensitivity: Sequence[CostSensitivityRow],
    rejected_configs: Sequence[RejectedGridConfig],
    manifest: Mapping[str, Any],
    top_config_count: int,
) -> None:
    """Write the exact required grid output files."""
    root = Path(paths.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    _write_csv(Path(paths.leaderboard_path), LEADERBOARD_COLUMNS, (row.to_csv_row() for row in leaderboard))
    _write_csv(
        Path(paths.monthly_breakdown_path),
        MONTHLY_BREAKDOWN_COLUMNS,
        (row.to_csv_row() for row in monthly_breakdown),
    )
    _write_csv(
        Path(paths.cost_sensitivity_path),
        COST_SENSITIVITY_COLUMNS,
        (row.to_csv_row() for row in cost_sensitivity),
    )
    _write_csv(
        Path(paths.rejected_configs_path),
        REJECTED_CONFIG_COLUMNS,
        (_rejected_row(grid_run_id, rejected) for rejected in rejected_configs),
    )
    Path(paths.top_configs_path).write_text(
        _top_configs_yaml(leaderboard[:top_config_count]),
        encoding="utf-8",
    )
    summary = _summary_markdown(
        grid_id=grid_id,
        grid_run_id=grid_run_id,
        completed_count=len(leaderboard),
        rejected_count=len(rejected_configs),
        manifest_path=paths.manifest_path,
    )
    if not no_forbidden_claims(summary):
        msg = "grid summary contains prohibited claim language"
        raise GridOutputError(msg)
    Path(paths.summary_path).write_text(summary, encoding="utf-8")
    Path(paths.manifest_path).write_text(
        json.dumps(dict(manifest), sort_keys=True, indent=2),
        encoding="utf-8",
    )


def no_forbidden_claims(payload: Mapping[str, Any] | Sequence[Any] | str) -> bool:
    """Return whether text avoids unsupported positive claim phrases."""
    text = payload.lower() if isinstance(payload, str) else json.dumps(payload, sort_keys=True).lower()
    return not any(phrase in text for phrase in FORBIDDEN_CLAIM_PHRASES)


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, str]] | Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _rejected_row(grid_run_id: str, rejected: RejectedGridConfig) -> dict[str, str]:
    return {
        "grid_run_id": grid_run_id,
        "config_id": rejected.config_id,
        "status": rejected.status,
        "reason": rejected.reason,
        "parameters_json": canonical_json(rejected.parameters),
    }


def _top_configs_yaml(rows: Sequence[LeaderboardRow]) -> str:
    lines = ["top_configs:"]
    for row in rows:
        lines.extend(
            [
                f"  - rank: {row.rank}",
                f"    config_id: {json.dumps(row.config_id)}",
                f"    net_pnl: {json.dumps(row.to_csv_row()['net_pnl'])}",
                f"    final_equity: {json.dumps(row.to_csv_row()['final_equity'])}",
                f"    engine_used: {json.dumps(row.engine_used)}",
                f"    parameters_json: {json.dumps(canonical_json(row.parameters))}",
            ]
        )
    if not rows:
        lines.append("  []")
    return "\n".join(lines) + "\n"


def _summary_markdown(
    *,
    grid_id: str,
    grid_run_id: str,
    completed_count: int,
    rejected_count: int,
    manifest_path: str,
) -> str:
    return (
        f"# Strategy Grid Summary\n\n"
        f"- Grid: `{grid_id}`\n"
        f"- Run: `{grid_run_id}`\n"
        f"- Completed configurations: {completed_count}\n"
        f"- Rejected configurations: {rejected_count}\n"
        f"- Decision status: research evidence only\n"
        f"- Reference truth: Tier 1 reference 1-minute engine remains canonical PnL truth\n"
        f"- Manifest: `{manifest_path}`\n\n"
        "This summary is evidence for offline review, not approval or a deployment signal.\n"
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
