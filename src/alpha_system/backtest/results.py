"""Reference backtest result container and local-only output policy."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.backtest.equity import EquityPoint
from alpha_system.backtest.fills import ReferenceFill
from alpha_system.backtest.trades import TradeRecord
from alpha_system.core.hashing import hash_config
from alpha_system.data.fixture_policy import repository_root_from_module
from alpha_system.data.paths import assert_local_wsl_path


DEFAULT_BACKTEST_OUTPUT_ROOT = Path("/tmp/alpha_system/backtests")
FORBIDDEN_BACKTEST_SUFFIXES: tuple[str, ...] = (
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


class BacktestOutputError(ValueError):
    """Raised when backtest outputs would violate artifact policy."""


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    run_id: str
    engine_version: str
    strategy_id: str
    strategy_version: str
    data_version: str
    total_trades: int
    open_positions: int
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    final_equity: Decimal
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "engine_version": self.engine_version,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "data_version": self.data_version,
            "total_trades": self.total_trades,
            "open_positions": self.open_positions,
            "gross_pnl": _decimal_text(self.gross_pnl),
            "costs": _decimal_text(self.costs),
            "net_pnl": _decimal_text(self.net_pnl),
            "final_equity": _decimal_text(self.final_equity),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BacktestOutputPaths:
    output_dir: str
    trades_path: str
    equity_path: str
    summary_path: str
    manifest_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "output_dir": self.output_dir,
            "trades_path": self.trades_path,
            "equity_path": self.equity_path,
            "summary_path": self.summary_path,
            "manifest_path": self.manifest_path,
        }


@dataclass(frozen=True, slots=True)
class ReferenceBacktestResult:
    summary: BacktestSummary
    trades: tuple[TradeRecord, ...]
    equity_curve: tuple[EquityPoint, ...]
    fills: tuple[ReferenceFill, ...]
    manifest: Mapping[str, Any]
    output_paths: BacktestOutputPaths | None = None
    registry_path: str | None = None
    registry_written: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "trades": [trade.to_dict() for trade in self.trades],
            "equity_curve": [point.to_dict() for point in self.equity_curve],
            "fills": [fill.to_dict() for fill in self.fills],
            "manifest": dict(self.manifest),
            "output_paths": None if self.output_paths is None else self.output_paths.to_dict(),
            "registry_path": self.registry_path,
            "registry_written": self.registry_written,
        }


def resolve_backtest_output_dir(output_dir: str | Path | None) -> Path:
    """Resolve a local-only directory for full trade/equity artifacts."""
    candidate = assert_local_wsl_path(output_dir or DEFAULT_BACKTEST_OUTPUT_ROOT)
    if candidate.suffix.lower() in FORBIDDEN_BACKTEST_SUFFIXES:
        msg = "backtest output directory must not be a DB, log, or columnar artifact path"
        raise BacktestOutputError(msg)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        msg = "backtest trade/equity outputs must be temp/local paths outside the repo"
        raise BacktestOutputError(msg)
    return candidate


def resolve_backtest_manifest_path(
    manifest_path: str | Path | None,
    output_dir: Path,
) -> Path:
    """Resolve a local-only run manifest path."""
    candidate = output_dir / "run_manifest.json" if manifest_path is None else assert_local_wsl_path(manifest_path)
    if candidate.suffix.lower() != ".json":
        msg = "backtest run manifest must be a JSON file"
        raise BacktestOutputError(msg)
    repo_root = repository_root_from_module()
    if _is_relative_to(candidate, repo_root):
        msg = "backtest run manifests must be temp/local paths outside the repo"
        raise BacktestOutputError(msg)
    return candidate


def write_backtest_outputs(
    result: ReferenceBacktestResult,
    *,
    output_dir: str | Path | None,
    manifest_path: str | Path | None,
    config_hash: str,
    config_payload: Mapping[str, Any],
) -> BacktestOutputPaths:
    """Write full local-only trade/equity artifacts plus summary and manifest."""
    root = resolve_backtest_output_dir(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    trades_path = root / "trades.jsonl"
    equity_path = root / "equity.jsonl"
    summary_path = root / "summary.json"
    active_manifest_path = resolve_backtest_manifest_path(manifest_path, root)
    active_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    _write_jsonl(trades_path, (trade.to_dict() for trade in result.trades))
    _write_jsonl(equity_path, (point.to_dict() for point in result.equity_curve))
    summary_path.write_text(
        json.dumps(result.summary.to_dict(), sort_keys=True, indent=2),
        encoding="utf-8",
    )
    manifest = manifest_payload(
        result,
        config_hash=config_hash,
        config_payload=config_payload,
        artifact_paths={
            "trades": trades_path.as_posix(),
            "equity": equity_path.as_posix(),
            "summary": summary_path.as_posix(),
        },
    )
    active_manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return BacktestOutputPaths(
        output_dir=root.as_posix(),
        trades_path=trades_path.as_posix(),
        equity_path=equity_path.as_posix(),
        summary_path=summary_path.as_posix(),
        manifest_path=active_manifest_path.as_posix(),
    )


def manifest_payload(
    result: ReferenceBacktestResult,
    *,
    config_hash: str,
    config_payload: Mapping[str, Any],
    artifact_paths: Mapping[str, str],
) -> dict[str, Any]:
    """Build the deterministic run manifest payload."""
    payload = {
        "run_id": result.summary.run_id,
        "engine_version": result.summary.engine_version,
        "strategy_id": result.summary.strategy_id,
        "strategy_version": result.summary.strategy_version,
        "data_version": result.summary.data_version,
        "config_hash": config_hash,
        "parameters": dict(config_payload),
        "artifact_paths": dict(sorted(artifact_paths.items())),
        "warnings": list(result.summary.warnings),
        "status_message": "Tier 1 reference 1-minute bar PnL truth; local research only.",
    }
    payload["manifest_hash"] = hash_config(
        {key: value for key, value in payload.items() if key != "manifest_hash"}
    )
    return payload


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]] | Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True))
            handle.write("\n")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
