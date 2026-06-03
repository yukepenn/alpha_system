from __future__ import annotations

import pytest

from alpha_system.management.spec import ManagementSpec, ManagementSpecError


def test_risk_per_trade_accepts_fraction_only() -> None:
    spec = ManagementSpec.from_mapping({"risk_per_trade": "0.01"})

    assert str(spec.risk_per_trade) == "0.01"

    with pytest.raises(ManagementSpecError):
        ManagementSpec.from_mapping({"risk_per_trade": "1.5"})
