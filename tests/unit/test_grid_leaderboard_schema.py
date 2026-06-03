from __future__ import annotations

from decimal import Decimal

from alpha_system.experiments.leaderboard import LEADERBOARD_COLUMNS, LeaderboardRow, build_leaderboard


def test_grid_leaderboard_schema_and_rank_are_deterministic() -> None:
    rows = build_leaderboard(
        (
            _row("cfg_000002", Decimal("1")),
            _row("cfg_000001", Decimal("2")),
        )
    )

    assert rows[0].config_id == "cfg_000001"
    assert rows[0].rank == 1
    assert tuple(rows[0].to_csv_row()) == LEADERBOARD_COLUMNS


def _row(config_id: str, net_pnl: Decimal) -> LeaderboardRow:
    return LeaderboardRow(
        rank=0,
        grid_run_id="grid_run",
        config_id=config_id,
        engine_requested="reference",
        engine_used="reference",
        total_trades=1,
        open_positions=0,
        gross_pnl=net_pnl,
        costs=Decimal("0"),
        net_pnl=net_pnl,
        final_equity=Decimal("100000") + net_pnl,
        warning_count=0,
        parameters={"strategy.direction": "long"},
    )
