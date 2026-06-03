from __future__ import annotations

import pytest

from alpha_system.portfolio.spec import PortfolioSpec, PortfolioSpecError


def test_future_correlation_aware_allocation_is_contract_only() -> None:
    spec = PortfolioSpec.from_mapping(
        {
            "future_correlation_aware_allocation": {
                "mode": "contract_only",
                "enabled": False,
                "inputs": ["future_correlation_matrix"],
            }
        }
    )

    assert spec.future_correlation_aware_allocation.mode.value == "contract_only"
    assert spec.future_correlation_aware_allocation.inputs == ("future_correlation_matrix",)

    with pytest.raises(PortfolioSpecError):
        PortfolioSpec.from_mapping(
            {"future_correlation_aware_allocation": {"mode": "contract_only", "enabled": True}}
        )
