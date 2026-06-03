from __future__ import annotations

from pathlib import Path


def test_ml_docs_and_examples_avoid_overclaim_phrases() -> None:
    text = "\n".join(
        [
            Path("docs/ML_LAYER.md").read_text(encoding="utf-8"),
            Path("docs/ML_LEAKAGE_POLICY.md").read_text(encoding="utf-8"),
            Path("configs/ml/examples/run_config.json").read_text(encoding="utf-8"),
        ]
    ).lower()

    for phrase in (
        "profitable",
        "tradable",
        "production-ready",
        "guaranteed alpha",
        "market-beating",
        "ready to trade",
        "auto-approved",
    ):
        assert phrase not in text
    assert "research outputs" in text
