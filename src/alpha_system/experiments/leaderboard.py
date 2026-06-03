"""Deterministic leaderboard construction for grid results."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any


LEADERBOARD_COLUMNS: tuple[str, ...] = (
    "rank",
    "grid_run_id",
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
)


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    """One ranked completed grid configuration."""

    rank: int
    grid_run_id: str
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

    def to_csv_row(self) -> dict[str, str]:
        from alpha_system.core.hashing import canonical_json

        return {
            "rank": str(self.rank),
            "grid_run_id": self.grid_run_id,
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
        }


def build_leaderboard(rows: Iterable[LeaderboardRow]) -> tuple[LeaderboardRow, ...]:
    """Rank completed rows by deterministic research metrics."""
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.net_pnl,
            -row.final_equity,
            row.costs,
            row.config_id,
        ),
    )
    return tuple(replace(row, rank=index) for index, row in enumerate(sorted_rows, start=1))


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
