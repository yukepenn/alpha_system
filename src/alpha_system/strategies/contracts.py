"""Strategy contract primitives and domain boundary fields."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from alpha_system.core.contracts import ConfigParameters, ContractMetadata
from alpha_system.core.enums import Direction


@dataclass(frozen=True, slots=True, kw_only=True)
class StrategySpec:
    strategy_id: str
    name: str
    version: str
    owner: str
    description: str
    entry_signal: str
    exit_signal: str
    direction: Direction
    required_factor_ids: tuple[str, ...]
    parameters: ConfigParameters
    metadata: ContractMetadata
    confidence_score: Decimal | float | None = None
    desired_exposure: Decimal | float | None = None
