"""Shared feature-facing accessors for timestamp-derived session truth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from alpha_system.data.foundation.sessions import (
    CME_INDEX_FUTURES_SESSION_TEMPLATE_ID,
    SessionTemplate,
    load_session_template_by_id,
)

SESSION_TRUTH_SOURCE = "alpha_system.data.foundation.sessions"


@dataclass(frozen=True, slots=True)
class SessionTruthClock:
    """Resolved clock fields used by vectorized session classifiers."""

    timezone: str
    rth_open_seconds: int
    rth_close_seconds: int
    eth_start_seconds: int
    eth_crosses_midnight: bool


def default_session_template() -> SessionTemplate:
    """Return the canonical CME index futures session template."""

    return load_session_template_by_id(template_id=CME_INDEX_FUTURES_SESSION_TEMPLATE_ID)


def session_contract_parameters(template: SessionTemplate | None = None) -> dict[str, object]:
    """Return the session-truth identity payload for session-conditioned specs."""

    resolved = default_session_template() if template is None else template
    return {
        "session_template_id": resolved.template_id,
        "session_timezone": resolved.timezone,
        "rth_open_time_local": resolved.rth_start.isoformat(timespec="minutes"),
        "rth_close_time_local": resolved.rth_end.isoformat(timespec="minutes"),
        "session_truth_source": SESSION_TRUTH_SOURCE,
    }


def session_truth_clock(template: SessionTemplate | None = None) -> SessionTruthClock:
    """Return a compact clock for Polars/session grouping expressions."""

    resolved = default_session_template() if template is None else template
    return SessionTruthClock(
        timezone=resolved.timezone,
        rth_open_seconds=_seconds_since_midnight(resolved.rth_start),
        rth_close_seconds=_seconds_since_midnight(resolved.rth_end),
        eth_start_seconds=_seconds_since_midnight(resolved.eth_start),
        eth_crosses_midnight=_seconds_since_midnight(resolved.eth_end)
        <= _seconds_since_midnight(resolved.eth_start),
    )


def _seconds_since_midnight(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


__all__ = [
    "SESSION_TRUTH_SOURCE",
    "SessionTruthClock",
    "default_session_template",
    "session_contract_parameters",
    "session_truth_clock",
]
