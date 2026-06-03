from __future__ import annotations

from alpha_system.management.state import ManagementRuntimeState


def test_cooldown_blocks_entries_until_configured_bar() -> None:
    state = ManagementRuntimeState().record_exit(
        session_id="session-a",
        exit_bar_index=5,
        cooldown_bars=2,
    )

    assert not state.can_enter(session_id="session-a", bar_index=6, max_trades_per_day=None)
    assert state.can_enter(session_id="session-a", bar_index=7, max_trades_per_day=None)
    assert state.can_enter(session_id="session-b", bar_index=6, max_trades_per_day=None)
