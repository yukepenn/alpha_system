from __future__ import annotations

import pytest

from alpha_system.management.spec import ManagementSpec, ManagementSpecError


def test_max_position_percent_accepts_fraction_only() -> None:
    spec = ManagementSpec.from_mapping({"max_position_percent": "0.2"})

    assert str(spec.max_position_percent) == "0.2"

    with pytest.raises(ManagementSpecError):
        ManagementSpec.from_mapping({"max_position_percent": "1.1"})
