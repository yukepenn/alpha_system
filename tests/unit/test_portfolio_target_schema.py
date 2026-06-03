from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from alpha_system.core.enums import Direction
from alpha_system.portfolio.targets import (
    PORTFOLIO_TARGET_SCHEMA_FIELDS,
    PortfolioTarget,
    targets_to_records,
    validate_target_schema,
)


def test_portfolio_target_schema_is_stable_and_validated() -> None:
    target = PortfolioTarget(
        target_id="target:SYNTH:0:entry",
        instrument_id="SYNTH",
        event_ts=datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc),
        available_ts=datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc),
        session_id="XNYS:2026-01-02:regular",
        bar_index=0,
        direction=Direction.LONG,
        target_notional=Decimal("1000"),
        target_quantity=Decimal("10"),
        target_weight=Decimal("0.01"),
        source_signal_id="entry",
        strategy_id="strategy",
        strategy_version="v1",
        data_version="data:v1",
        quality_flags=("synthetic",),
    )

    payload = target.to_dict()

    assert tuple(payload) == PORTFOLIO_TARGET_SCHEMA_FIELDS
    assert validate_target_schema(payload) is True
    assert targets_to_records([target])[0] == payload
