from __future__ import annotations

from pathlib import Path

from alpha_system.governance.sealed_holdout import (
    SealedHoldoutRegistry,
    SealedHoldoutStatus,
)

DECLARATION_PATH = Path(
    "research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json"
)


def test_kill_shot_sealed_holdout_declaration_validates_value_free() -> None:
    registry = SealedHoldoutRegistry(DECLARATION_PATH)

    window = registry.active_window()

    assert window.window_id == "holdwin_d5cba50af19976275ab26f34"
    assert window.status is SealedHoldoutStatus.SEALED
    assert window.start_date == "2025-01-01"
    assert window.end_date == "2026-06-11"
    assert window.provenance is not None
    assert window.provenance["value_free"] is True
    assert "docs/OPERATING_COMPASS_V4.md" in str(window.provenance["compass_ref"])
