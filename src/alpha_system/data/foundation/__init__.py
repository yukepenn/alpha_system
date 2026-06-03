"""Data-foundation placeholder namespace for ALPHA_DATA_FOUNDATION_V1.

DATA-P01 establishes importable names only. Later DATA-P02+ phases own
validation behavior, schemas, persistence, and provider integrations.
"""

from alpha_system.data.foundation.bars import (
    CanonicalBarRecord,
    ParsedBarRecord,
    RawDataObject,
    TimestampSemanticsPolicy,
)
from alpha_system.data.foundation.batches import MicroBatchPolicy, SymbolBatchPlan
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
)
from alpha_system.data.foundation.ibkr import (
    IBKRClientIdPolicy,
    IBKRConnectionProfile,
    run_connection_doctor,
)
from alpha_system.data.foundation.instruments import (
    ContractDetailsSnapshot,
    FuturesContractRecord,
    InstrumentMasterRecord,
)
from alpha_system.data.foundation.requests import (
    DataIngestionRunRecord,
    HistoricalChunkRecord,
    HistoricalPullLedger,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    ProviderErrorRecord,
    RequestPacingPolicy,
)
from alpha_system.data.foundation.rolls import RollCalendarRecord, RollPolicy
from alpha_system.data.foundation.series import (
    ContinuousFuturesSeriesRecord,
    DatedFuturesSeriesRecord,
)
from alpha_system.data.foundation.sessions import SessionTemplate, TradingCalendarRecord
from alpha_system.data.foundation.sources import (
    DataAccessMode,
    DataSourceProfile,
    LocalDataRootPolicy,
)

__all__ = [
    "CanonicalBarRecord",
    "ContractDetailsSnapshot",
    "ContinuousFuturesSeriesRecord",
    "CoverageReport",
    "DataAccessMode",
    "DataIngestionRunRecord",
    "DataQualityReport",
    "DataSourceProfile",
    "DatasetPartitionPlan",
    "DatasetVersion",
    "DatedFuturesSeriesRecord",
    "FuturesContractRecord",
    "HistoricalChunkRecord",
    "HistoricalPullLedger",
    "HistoricalRequestManifest",
    "HistoricalRequestSpec",
    "IBKRClientIdPolicy",
    "IBKRConnectionProfile",
    "InstrumentMasterRecord",
    "LocalDataRootPolicy",
    "MicroBatchPolicy",
    "ParsedBarRecord",
    "ProviderErrorRecord",
    "RawDataObject",
    "RequestPacingPolicy",
    "RollCalendarRecord",
    "RollPolicy",
    "SessionTemplate",
    "SymbolBatchPlan",
    "TimestampSemanticsPolicy",
    "TradingCalendarRecord",
    "run_connection_doctor",
]
