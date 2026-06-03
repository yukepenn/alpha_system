"""Instrument and contract placeholders.

DATA-P01 names only. DATA-P05 and DATA-P06 own contract-master behavior and
provider contract-detail snapshots.
"""


class InstrumentMasterRecord:
    """DATA-P05 placeholder for a root-level futures instrument definition."""


class FuturesContractRecord:
    """DATA-P05 placeholder for a dated futures contract record."""


class ContractDetailsSnapshot:
    """DATA-P06 placeholder for provider contract-detail metadata."""


__all__ = [
    "ContractDetailsSnapshot",
    "FuturesContractRecord",
    "InstrumentMasterRecord",
]
