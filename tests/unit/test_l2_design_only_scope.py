from __future__ import annotations

from pathlib import Path

from alpha_system.core.enums import ReadinessState
from alpha_system.l2 import design


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_l2_design_readiness_is_design_only() -> None:
    assert design.L2_READINESS_STATE is ReadinessState.DESIGN_ONLY
    assert design.L2_EXECUTION_IMPLEMENTATION == "none"
    assert design.L2_PNL_TRUTH == "tier1_reference_1minute_bar_engine"


def test_l2_future_capabilities_are_metadata_only() -> None:
    assert set(design.design_only_capability_ids()) == {
        "book_reconstruction",
        "queue_position",
        "latency_model",
        "passive_fills",
    }
    assert all(
        capability.readiness is ReadinessState.DESIGN_ONLY
        for capability in design.FUTURE_L2_CAPABILITIES
    )


def test_l2_modules_do_not_export_runtime_engine_classes() -> None:
    forbidden_names = {
        "L2ReplayEngine",
        "QueueModel",
        "PassiveFillModel",
        "BrokerClient",
        "LiveMarketDataClient",
        "PaperTrader",
    }

    assert forbidden_names.isdisjoint(set(dir(design)))


def test_l2_docs_state_design_only_scope() -> None:
    docs = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/L2_READINESS.md",
            "docs/FUTURE_L2_REPLAY.md",
            "docs/L2_SCOPE_BOUNDARIES.md",
        )
    ).lower()

    assert "design-only" in docs
    assert "not be read as complete execution infrastructure" in docs
    assert "single pnl truth" in docs
