"""Drift guard: docs/SYSTEM_MAP.md must match what the generator produces.

If this test fails, the system's shape changed (anchor moved, package added,
command renamed) without regenerating the map. Fix with: `just system-map`.
"""

from __future__ import annotations

from tools.frontier import system_map


def test_all_anchors_exist() -> None:
    missing = [path for _, path, _ in system_map.ANCHORS if not (system_map.ROOT / path).exists()]
    assert not missing, f"system map anchors missing (update ANCHORS): {missing}"


def test_committed_map_is_current() -> None:
    assert system_map.MAP_PATH.exists(), "docs/SYSTEM_MAP.md missing; run `just system-map`"
    committed = system_map.MAP_PATH.read_text(encoding="utf-8")
    assert committed == system_map.generate(), (
        "docs/SYSTEM_MAP.md is stale; regenerate with `just system-map`"
    )
