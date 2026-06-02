"""Label contract primitives for future-looking research targets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from alpha_system.core.contracts import ContractMetadata
from alpha_system.core.enums import LabelType


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelSchema:
    label_id: str
    instrument_id: str
    event_ts: datetime
    horizon: timedelta
    label_type: LabelType
    value: Decimal | float | int | str | bool | None
    path_metadata: ContractMetadata
    data_version: str
    label_available_ts: datetime
