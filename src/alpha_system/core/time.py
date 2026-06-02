"""No-lookahead timestamp primitives for schema contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from alpha_system.core.enums import ExecutionTiming


@dataclass(frozen=True, slots=True, kw_only=True)
class BarAvailabilityPolicy:
    """Policy primitive for when completed bars may be consumed."""

    data_latency: timedelta
    execution_timing: ExecutionTiming = ExecutionTiming.NEXT_BAR_CONSERVATIVE

    def earliest_available_ts(self, bar_end_ts: datetime) -> datetime:
        """Return the first timestamp after bar completion and latency."""
        return bar_end_ts + self.data_latency

    @property
    def same_bar_execution_allowed(self) -> bool:
        """Signal that same-bar execution is not the default contract."""
        return self.execution_timing != ExecutionTiming.NEXT_BAR_CONSERVATIVE
