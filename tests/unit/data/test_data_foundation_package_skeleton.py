from __future__ import annotations

import importlib


def test_data_package_and_foundation_namespace_import_cleanly() -> None:
    modules = [
        "alpha_system.data",
        "alpha_system.data.foundation",
        "alpha_system.data.foundation.bars",
        "alpha_system.data.foundation.batches",
        "alpha_system.data.foundation.datasets",
        "alpha_system.data.foundation.ibkr",
        "alpha_system.data.foundation.instruments",
        "alpha_system.data.foundation.requests",
        "alpha_system.data.foundation.rolls",
        "alpha_system.data.foundation.series",
        "alpha_system.data.foundation.sessions",
        "alpha_system.data.foundation.sources",
        "alpha_system.data.foundation.version_registry",
    ]

    for module_name in modules:
        assert importlib.import_module(module_name) is not None


def test_foundation_namespace_exposes_canonical_placeholder_names() -> None:
    foundation = importlib.import_module("alpha_system.data.foundation")

    expected_names = {
        "CanonicalBarRecord",
        "ContractDetailsSnapshot",
        "ContinuousFuturesSeriesRecord",
        "CoverageReport",
        "DATASET_VERSION_FIELDS",
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
        "IBKRReadOnlyApiBoundary",
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
        "ReadOnlyBoundaryViolation",
        "build_read_only_ibkr_boundary",
        "compute_quality_report_hash",
        "persist_dataset_version",
        "resolve_dataset_version",
    }

    for name in expected_names:
        assert hasattr(foundation, name)
