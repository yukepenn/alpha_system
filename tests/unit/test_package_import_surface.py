from __future__ import annotations

import importlib

import pytest


IMPORTABLE_MODULES = (
    "alpha_system",
    "alpha_system.backtest",
    "alpha_system.cli",
    "alpha_system.core",
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
    "alpha_system.execution",
    "alpha_system.experiments",
    "alpha_system.factors",
    "alpha_system.governance",
    "alpha_system.governance.ids",
    "alpha_system.governance.serialization",
    "alpha_system.governance.validation",
    "alpha_system.governance.alpha_spec",
    "alpha_system.governance.hypothesis_card",
    "alpha_system.governance.feature_request",
    "alpha_system.governance.duplicate_exposure",
    "alpha_system.governance.label_spec",
    "alpha_system.governance.label_leakage_guard",
    "alpha_system.governance.study_spec",
    "alpha_system.governance.trial_ledger",
    "alpha_system.governance.evidence_bundle",
    "alpha_system.governance.rejected_idea",
    "alpha_system.governance.promotion",
    "alpha_system.governance.reviewer_verdict",
    "alpha_system.governance.canaries",
    "alpha_system.governance.registry",
    "alpha_system.governance.claims",
    "alpha_system.governance.report",
    "alpha_system.l2",
    "alpha_system.labels",
    "alpha_system.management",
    "alpha_system.portfolio",
    "alpha_system.reports",
    "alpha_system.research",
    "alpha_system.signals",
    "alpha_system.strategies",
)


@pytest.mark.parametrize("module_name", IMPORTABLE_MODULES)
def test_package_import_surface(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module is not None
    assert module.__name__ == module_name


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
