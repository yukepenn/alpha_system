"""Historical request, pacing, ledger, and ingestion-run placeholders.

DATA-P01 names only. DATA-P07, DATA-P08, DATA-P09, and DATA-P10 own request
manifests, chunk records, pacing, ledgers, error records, and ingestion runs.
"""


class HistoricalRequestSpec:
    """DATA-P07 placeholder for a declarative historical request."""


class HistoricalRequestManifest:
    """DATA-P07 placeholder for a planned historical pull manifest."""


class HistoricalChunkRecord:
    """DATA-P08 placeholder for one chunk request lifecycle record."""


class HistoricalPullLedger:
    """DATA-P10 placeholder for pull audit and resume state."""


class ProviderErrorRecord:
    """DATA-P10 placeholder for provider error metadata."""


class RequestPacingPolicy:
    """DATA-P09 placeholder for historical request pacing rules."""


class DataIngestionRunRecord:
    """DATA-P10 placeholder for a historical ingestion run record."""


__all__ = [
    "DataIngestionRunRecord",
    "HistoricalChunkRecord",
    "HistoricalPullLedger",
    "HistoricalRequestManifest",
    "HistoricalRequestSpec",
    "ProviderErrorRecord",
    "RequestPacingPolicy",
]
