from __future__ import annotations

from alpha_system.management.state import ManagementRuntimeState


def test_max_trades_per_day_is_session_scoped() -> None:
    state = ManagementRuntimeState().record_entry(session_id="session-a")

    assert not state.can_enter(session_id="session-a", bar_index=2, max_trades_per_day=1)

    reset = state.for_session("session-b", session_reset=True)

    assert reset.can_enter(session_id="session-b", bar_index=0, max_trades_per_day=1)
