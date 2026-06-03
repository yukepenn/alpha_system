from __future__ import annotations

import pytest

from alpha_system.experiments.ml_outputs import MLOutputError, ScoreToPortfolioContract


def test_score_to_portfolio_contract_is_representation_only() -> None:
    contract = ScoreToPortfolioContract()

    assert contract.sizing_implementation == "deferred"
    assert contract.execution_implementation == "none"
    assert contract.to_dict()["score_field"] == "score"


def test_score_to_portfolio_contract_rejects_execution_implementation() -> None:
    with pytest.raises(MLOutputError, match="must not implement execution"):
        ScoreToPortfolioContract(execution_implementation="orders")
