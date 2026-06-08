"""Lock the lane review policy so an executor cannot self-approve material work.

Codex executes; the Yellow and Red lanes must require an independent Claude review
before merge. Green (low-risk automatic) may skip review, but must not be a path
for merging un-reviewed material/external work. This test fails if frontier.yaml
weakens those gates.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _lanes() -> dict:
    data = yaml.safe_load((ROOT / "frontier.yaml").read_text(encoding="utf-8"))
    lanes = data.get("lanes") or data.get("lane_policy") or {}
    assert lanes, "frontier.yaml must define lanes"
    return lanes


def test_yellow_requires_independent_review() -> None:
    lanes = _lanes()
    assert lanes["yellow"]["require_claude_review"] is True


def test_red_requires_independent_review_and_no_blind_auto_merge() -> None:
    lanes = _lanes()
    red = lanes["red"]
    assert red["require_claude_review"] is True
    # Red never blind auto-merges; if it can auto-merge at all it is only under
    # armed scoped authorization.
    assert red.get("auto_merge") is False
    if red.get("can_auto_merge_when_authorized"):
        assert red.get("require_operation_scope_match", True) or red.get("merge_policy", {}).get(
            "require_operation_scope_match", False
        )


def test_green_is_low_risk_only() -> None:
    lanes = _lanes()
    green = lanes["green"]
    # Green may skip Claude review, but it is the low-risk automatic lane; material
    # engineering/research is Yellow. Guard against green being widened into a
    # review-free merge path for large changes.
    assert green["require_claude_review"] is False
    assert green.get("max_changed_files", 0) <= 120, "green must stay bounded/low-risk"
