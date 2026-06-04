"""Register local Databento canonical DatasetVersions after fail-closed gates."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.core.hashing import hash_config, hash_file
from alpha_system.core.registry import connect_registry, is_local_only_registry_path
from alpha_system.data.cli_validation import load_cli_config
from alpha_system.data.databento.canonicalize import (
    BBO_PARTITION_SCHEMA,
    CANONICAL_PROVIDER_SEGMENT,
    OHLCV_PARTITION_SCHEMA,
    SOURCE_ID,
)
from alpha_system.data.databento.coverage import (
    bbo_coverage_report,
    expected_intervals_for_bars,
    ohlcv_coverage_report,
)
from alpha_system.data.databento.quality import bbo_quality_report, ohlcv_quality_report
from alpha_system.data.databento.request_spec import (
    DatabentoRequestSpec,
    load_json_mapping,
    request_spec_hash,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    compute_quality_report_hash,
    require_governance_metadata_for_locked_partition_use,
)
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.data.foundation.version_registry import persist_dataset_version
from alpha_system.data.ibkr._json_utils import json_ready as _json_ready
from alpha_system.data.ibkr.materialize import (
    _load_calendar,
    _partition_plan,
    _repo_root,
    _settings_for_symbols,
    _validate_data_root,
)


@dataclass(frozen=True, slots=True)
class RegisterSummary:
    """Redacted summary of Databento DatasetVersion registration."""

    ohlcv_dataset_version_id: str
    bbo_dataset_version_id: str
    symbols: tuple[str, ...]
    ohlcv_row_count: int
    bbo_row_count: int
    ohlcv_quality_status: str
    ohlcv_coverage_status: str
    bbo_quality_status: str
    bbo_coverage_status: str
    partition: str
    registry_path: str | None
    registered: bool
    blocking_summary: Mapping[str, object]
    provenance: Mapping[str, object]

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "ohlcv_dataset_version_id": self.ohlcv_dataset_version_id,
                "bbo_dataset_version_id": self.bbo_dataset_version_id,
                "symbols": self.symbols,
                "ohlcv_row_count": self.ohlcv_row_count,
                "bbo_row_count": self.bbo_row_count,
                "ohlcv_quality_status": self.ohlcv_quality_status,
                "ohlcv_coverage_status": self.ohlcv_coverage_status,
                "bbo_quality_status": self.bbo_quality_status,
                "bbo_coverage_status": self.bbo_coverage_status,
                "partition": self.partition,
                "registry_path": self.registry_path,
                "registered": self.registered,
                "blocking_summary": self.blocking_summary,
                "provenance": self.provenance,
            }
        )


def run_register_dataset(
    *,
    canonical_root: str | Path,
    request_spec: DatabentoRequestSpec | Mapping[str, object],
    registry_path: str | Path,
    ohlcv_data_version: str,
    bbo_data_version: str,
    partition: str,
    instrument_config_path: str | Path,
    calendar_config_path: str | Path,
    validation_config_path: str | Path,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> RegisterSummary:
    """Register OHLCV and companion BBO DatasetVersions only when gates pass."""

    spec = _coerce_request_spec(request_spec)
    registry = _validate_registry_path(Path(registry_path))
    data_root = _require_data_root(env)
    root = _validate_canonical_root(Path(canonical_root), data_root=data_root)
    created_at = _normalize_now(now)
    symbols = tuple(_root_from_symbol(symbol) for symbol in spec.symbols)
    instrument_config = load_cli_config(instrument_config_path)
    validation_config = load_cli_config(validation_config_path)
    calendar = _load_calendar(Path(calendar_config_path), instrument_config)
    settings_by_symbol = _settings_for_symbols(
        symbols=symbols,
        instrument_config=instrument_config,
    )

    ohlcv_bars = _read_ohlcv_records(root, ohlcv_data_version)
    bbo_records = _read_bbo_records(root, bbo_data_version)
    expected_intervals = expected_intervals_for_bars(
        bars=ohlcv_bars,
        symbols=symbols,
        partition_id=partition,
        settings_by_symbol=settings_by_symbol,
        calendar=calendar,
        start_ts=spec.start,
        end_ts=spec.end,
    )
    expected_sessions = tuple(
        sorted({settings.session_label for settings in settings_by_symbol.values()})
    )
    ohlcv_quality = ohlcv_quality_report(
        quality_report_id=f"dqr_{ohlcv_data_version}",
        dataset_version_id=ohlcv_data_version,
        bars=ohlcv_bars,
        expected_sessions=expected_sessions,
        expected_gap_intervals=expected_intervals,
    )
    ohlcv_coverage = ohlcv_coverage_report(
        coverage_report_id=f"covr_{ohlcv_data_version}",
        dataset_version_id=ohlcv_data_version,
        bars=ohlcv_bars,
        expected_intervals=expected_intervals,
    )
    bbo_quality = bbo_quality_report(
        quality_report_id=f"dqr_{bbo_data_version}",
        dataset_version_id=bbo_data_version,
        bbos=bbo_records,
        expected_ohlcv_bars=ohlcv_bars,
        expected_sessions=expected_sessions,
        abnormal_spread_threshold=validation_config.get("max_bbo_spread"),
    )
    bbo_coverage = bbo_coverage_report(
        coverage_report_id=f"covr_{bbo_data_version}",
        dataset_version_id=bbo_data_version,
        bbos=bbo_records,
        expected_intervals=expected_intervals,
    )

    plan = _partition_plan(partition)
    plan.permits_coverage_qa(partition)
    require_governance_metadata_for_locked_partition_use(
        partition_id=partition,
        purpose="data_qa_coverage_inspection",
        plan=plan,
    )
    contamination_metadata = MappingProxyType(
        {
            "purpose": "data_qa_coverage_inspection",
            "partition_id": partition,
            "partition_plan_id": plan.plan_id,
            "contamination_metadata_rules": plan.contamination_metadata_rules,
        }
    )
    provenance = _continuous_provenance(instrument_config)
    blocking = _blocking_summary(
        ohlcv_quality=ohlcv_quality,
        ohlcv_coverage=ohlcv_coverage,
        bbo_quality=bbo_quality,
        bbo_coverage=bbo_coverage,
    )
    if any(
        (
            ohlcv_quality.blocks_versioning,
            ohlcv_coverage.blocks_versioning,
            bbo_quality.blocks_versioning,
            bbo_coverage.blocks_versioning,
        )
    ):
        return _summary(
            ohlcv_data_version=ohlcv_data_version,
            bbo_data_version=bbo_data_version,
            symbols=symbols,
            ohlcv_bars=ohlcv_bars,
            bbo_records=bbo_records,
            ohlcv_quality=ohlcv_quality,
            ohlcv_coverage=ohlcv_coverage,
            bbo_quality=bbo_quality,
            bbo_coverage=bbo_coverage,
            partition=partition,
            registry_path=None,
            registered=False,
            blocking_summary=blocking,
            provenance=provenance,
        )

    ohlcv_manifest_hash = _canonical_manifest_hash(
        canonical_root=root,
        data_version=ohlcv_data_version,
        partition_schema=OHLCV_PARTITION_SCHEMA,
        request_spec=spec,
    )
    bbo_manifest_hash = _canonical_manifest_hash(
        canonical_root=root,
        data_version=bbo_data_version,
        partition_schema=BBO_PARTITION_SCHEMA,
        request_spec=spec,
    )
    ohlcv_code_hash = hash_config(
        {
            "module": "alpha_system.data.databento.register_dataset",
            "canonical_schema": "CanonicalBarRecord",
            "quality": "DataQualityReport.from_canonical_bars",
            "coverage": "CoverageReport.from_canonical_bars",
        }
    )
    bbo_code_hash = hash_config(
        {
            "module": "alpha_system.data.databento.register_dataset",
            "canonical_schema": "CanonicalBBORecord",
            "quality": "DataQualityReport.from_canonical_bbos",
            "coverage": "CoverageReport.from_canonical_bbos",
        }
    )
    base_config_payload = {
        "request_spec_hash": request_spec_hash(spec),
        "instrument_config": instrument_config,
        "validation_config": validation_config,
        "calendar_config_path": Path(calendar_config_path).as_posix(),
        "partition_metadata": contamination_metadata,
        "continuous_provenance": provenance,
    }
    ohlcv_config_hash = hash_config({**base_config_payload, "what_to_show": "TRADES"})
    bbo_config_hash = hash_config(
        {
            **base_config_payload,
            "what_to_show": "BBO",
            "companion_ohlcv_dataset_version_id": ohlcv_data_version,
        }
    )
    contract_universe = tuple(sorted({bar.contract_id for bar in ohlcv_bars}))
    roll_policy_id = next(iter(settings_by_symbol.values())).roll_policy_id
    ohlcv_version = DatasetVersion.from_mapping(
        {
            "dataset_version_id": ohlcv_data_version,
            "source": SOURCE_ID,
            "symbol_universe": symbols,
            "bar_size": "1 min",
            "what_to_show": "TRADES",
            "start_ts": spec.start.isoformat(),
            "end_ts": spec.end.isoformat(),
            "contract_universe": contract_universe,
            "roll_policy_id": roll_policy_id,
            "manifest_hash": ohlcv_manifest_hash,
            "code_hash": ohlcv_code_hash,
            "config_hash": ohlcv_config_hash,
            "quality_report_hash": compute_quality_report_hash(ohlcv_quality),
            "created_at": created_at.isoformat(),
        }
    )
    bbo_version = DatasetVersion.from_mapping(
        {
            "dataset_version_id": bbo_data_version,
            "source": SOURCE_ID,
            "symbol_universe": symbols,
            "bar_size": "1 min",
            "what_to_show": "BBO",
            "start_ts": spec.start.isoformat(),
            "end_ts": spec.end.isoformat(),
            "contract_universe": contract_universe,
            "roll_policy_id": roll_policy_id,
            "manifest_hash": bbo_manifest_hash,
            "code_hash": bbo_code_hash,
            "config_hash": bbo_config_hash,
            "quality_report_hash": compute_quality_report_hash(bbo_quality),
            "created_at": created_at.isoformat(),
        }
    )
    persist_dataset_version(
        registry,
        ohlcv_version,
        quality_report=ohlcv_quality,
        coverage_report=ohlcv_coverage,
        source_manifest={"manifest_hash": ohlcv_manifest_hash},
        code_hash=ohlcv_code_hash,
        config_hash=ohlcv_config_hash,
    )
    persist_dataset_version(
        registry,
        bbo_version,
        quality_report=bbo_quality,
        coverage_report=bbo_coverage,
        source_manifest={"manifest_hash": bbo_manifest_hash},
        code_hash=bbo_code_hash,
        config_hash=bbo_config_hash,
    )
    _persist_dataset_metadata(
        registry_path=registry,
        dataset_version_id=ohlcv_data_version,
        created_at=created_at,
        metadata_hash=hash_config(provenance),
        metadata={
            "partition_contamination_metadata": contamination_metadata,
            "continuous_provenance": provenance,
            "companion_bbo_dataset_version_id": bbo_data_version,
        },
    )
    _persist_dataset_metadata(
        registry_path=registry,
        dataset_version_id=bbo_data_version,
        created_at=created_at,
        metadata_hash=hash_config(
            {
                "provenance": provenance,
                "companion_ohlcv_dataset_version_id": ohlcv_data_version,
            }
        ),
        metadata={
            "partition_contamination_metadata": contamination_metadata,
            "continuous_provenance": provenance,
            "companion_ohlcv_dataset_version_id": ohlcv_data_version,
        },
    )
    return _summary(
        ohlcv_data_version=ohlcv_data_version,
        bbo_data_version=bbo_data_version,
        symbols=symbols,
        ohlcv_bars=ohlcv_bars,
        bbo_records=bbo_records,
        ohlcv_quality=ohlcv_quality,
        ohlcv_coverage=ohlcv_coverage,
        bbo_quality=bbo_quality,
        bbo_coverage=bbo_coverage,
        partition=partition,
        registry_path=registry.as_posix(),
        registered=True,
        blocking_summary=blocking,
        provenance=provenance,
    )


def _coerce_request_spec(
    request_spec: DatabentoRequestSpec | Mapping[str, object],
) -> DatabentoRequestSpec:
    return (
        request_spec
        if isinstance(request_spec, DatabentoRequestSpec)
        else DatabentoRequestSpec.from_mapping(request_spec)
    )


def _validate_registry_path(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    if not is_local_only_registry_path(resolved):
        msg = f"registry path is not local-only: {resolved.as_posix()}"
        raise DataFoundationValidationError(msg)
    return resolved


def _require_data_root(env: Mapping[str, str] | None) -> Path:
    source = os.environ if env is None else env
    value = source.get("ALPHA_DATA_ROOT")
    if value is None or not value.strip():
        msg = "ALPHA_DATA_ROOT is required for Databento DatasetVersion registration"
        raise DataFoundationValidationError(msg)
    return _validate_data_root(Path(value), _repo_root())


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_canonical_root(canonical_root: Path, *, data_root: Path) -> Path:
    resolved = _validate_data_root(canonical_root, _repo_root())
    if resolved != data_root and not _is_relative_to(resolved, data_root):
        msg = "canonical_root must resolve under ALPHA_DATA_ROOT"
        raise DataFoundationValidationError(msg)
    if resolved.name != CANONICAL_PROVIDER_SEGMENT:
        candidate = (
            resolved / "databento" / "canonical" / CANONICAL_PROVIDER_SEGMENT
        ).resolve(strict=False)
        if candidate.exists():
            return candidate
    return resolved


def _normalize_now(now: datetime | None) -> datetime:
    active = now or datetime.now(UTC)
    if active.tzinfo is None or active.utcoffset() is None:
        msg = "now must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return active.astimezone(UTC).replace(microsecond=0)


def _root_from_symbol(symbol: str) -> str:
    root = symbol.replace(".", " ").split()[0].upper()
    if root not in {"ES", "NQ", "RTY"}:
        msg = "Databento registration is scoped to ES/NQ/RTY"
        raise DataFoundationValidationError(msg)
    return root


def _read_ohlcv_records(canonical_root: Path, data_version: str) -> tuple[CanonicalBarRecord, ...]:
    return tuple(
        CanonicalBarRecord.from_mapping(row)
        for row in _read_schema_rows(canonical_root, data_version, OHLCV_PARTITION_SCHEMA)
    )


def _read_bbo_records(canonical_root: Path, data_version: str) -> tuple[CanonicalBBORecord, ...]:
    return tuple(
        CanonicalBBORecord.from_mapping(row)
        for row in _read_schema_rows(canonical_root, data_version, BBO_PARTITION_SCHEMA)
    )


def _read_schema_rows(
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
) -> tuple[Mapping[str, object], ...]:
    schema_root = canonical_root / data_version / f"schema={partition_schema}"
    if not schema_root.is_dir():
        msg = f"canonical schema directory does not exist: {schema_root.as_posix()}"
        raise DataFoundationValidationError(msg)
    rows: list[Mapping[str, object]] = []
    for path in _canonical_data_files(canonical_root, data_version, partition_schema):
        if path.suffix == ".jsonl":
            rows.extend(_read_jsonl(path))
        elif path.suffix == ".parquet":
            rows.extend(_read_parquet(path))
    if not rows:
        msg = f"no canonical records found for {data_version} {partition_schema}"
        raise DataFoundationValidationError(msg)
    return tuple(rows)


def _canonical_data_files(
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
) -> tuple[Path, ...]:
    schema_root = canonical_root / data_version / f"schema={partition_schema}"
    paths = []
    for path in sorted(schema_root.glob("root=*/part-*")):
        if path.name.endswith(".json") or path.name.endswith(".manifest"):
            continue
        if path.suffix in {".jsonl", ".parquet"}:
            paths.append(path)
    return tuple(paths)


def _read_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, Mapping):
                    msg = f"canonical JSONL row is not a mapping: {path.as_posix()}"
                    raise DataFoundationValidationError(msg)
                rows.append(MappingProxyType(dict(payload)))
    return tuple(rows)


def _read_parquet(path: Path) -> tuple[Mapping[str, object], ...]:
    pyarrow = _optional_module("pyarrow")
    if pyarrow is not None:
        parquet = importlib.import_module("pyarrow.parquet")
        return tuple(parquet.read_table(path).to_pylist())
    polars = _optional_module("polars")
    if polars is not None:
        return tuple(polars.read_parquet(path.as_posix()).to_dicts())
    msg = f"cannot read Parquet without pyarrow or polars: {path.as_posix()}"
    raise DataFoundationValidationError(msg)


def _optional_module(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise


def _canonical_manifest_hash(
    *,
    canonical_root: Path,
    data_version: str,
    partition_schema: str,
    request_spec: DatabentoRequestSpec,
) -> str:
    files = _canonical_data_files(canonical_root, data_version, partition_schema)
    if not files:
        msg = f"no canonical files found for manifest hash: {data_version}"
        raise DataFoundationValidationError(msg)
    return hash_config(
        {
            "schema": "alpha_system.databento.registered_canonical_manifest.v1",
            "data_version": data_version,
            "partition_schema": partition_schema,
            "request_spec_hash": request_spec_hash(request_spec),
            "files": tuple(
                {
                    "relative_path": path.relative_to(canonical_root).as_posix(),
                    "sha256": hash_file(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in files
            ),
        }
    )


def _continuous_provenance(config: Mapping[str, object]) -> Mapping[str, object]:
    raw = config.get("continuous_provenance")
    if isinstance(raw, Mapping):
        provenance = dict(raw)
    else:
        provenance = {}
    defaults = {
        "provider_continuous": True,
        "front_month": True,
        "unadjusted": True,
        "not_roll_truth": True,
        "primary_research_corpus": True,
    }
    for key, value in defaults.items():
        provenance.setdefault(key, value)
    missing = tuple(key for key, value in defaults.items() if provenance.get(key) is not value)
    if missing:
        msg = "Databento continuous provenance is incomplete: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    return MappingProxyType(provenance)


def _blocking_summary(
    *,
    ohlcv_quality: DataQualityReport,
    ohlcv_coverage: CoverageReport,
    bbo_quality: DataQualityReport,
    bbo_coverage: CoverageReport,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "ohlcv_quality_blocks": ohlcv_quality.blocks_versioning,
            "ohlcv_coverage_blocks": ohlcv_coverage.blocks_versioning,
            "bbo_quality_blocks": bbo_quality.blocks_versioning,
            "bbo_coverage_blocks": bbo_coverage.blocks_versioning,
            "ohlcv_quality_status": ohlcv_quality.status.value,
            "ohlcv_coverage_status": ohlcv_coverage.coverage_status.value,
            "bbo_quality_status": bbo_quality.status.value,
            "bbo_coverage_status": bbo_coverage.coverage_status.value,
        }
    )


def _summary(
    *,
    ohlcv_data_version: str,
    bbo_data_version: str,
    symbols: tuple[str, ...],
    ohlcv_bars: Sequence[CanonicalBarRecord],
    bbo_records: Sequence[CanonicalBBORecord],
    ohlcv_quality: DataQualityReport,
    ohlcv_coverage: CoverageReport,
    bbo_quality: DataQualityReport,
    bbo_coverage: CoverageReport,
    partition: str,
    registry_path: str | None,
    registered: bool,
    blocking_summary: Mapping[str, object],
    provenance: Mapping[str, object],
) -> RegisterSummary:
    return RegisterSummary(
        ohlcv_dataset_version_id=ohlcv_data_version,
        bbo_dataset_version_id=bbo_data_version,
        symbols=symbols,
        ohlcv_row_count=len(ohlcv_bars),
        bbo_row_count=len(bbo_records),
        ohlcv_quality_status=ohlcv_quality.status.value,
        ohlcv_coverage_status=ohlcv_coverage.coverage_status.value,
        bbo_quality_status=bbo_quality.status.value,
        bbo_coverage_status=bbo_coverage.coverage_status.value,
        partition=partition,
        registry_path=registry_path,
        registered=registered,
        blocking_summary=blocking_summary,
        provenance=provenance,
    )


def _persist_dataset_metadata(
    *,
    registry_path: Path,
    dataset_version_id: str,
    created_at: datetime,
    metadata_hash: str,
    metadata: Mapping[str, object],
) -> None:
    payload = json.dumps(_json_ready(metadata), sort_keys=True)
    with connect_registry(registry_path) as connection:
        try:
            connection.execute(
                """
                INSERT INTO artifact_manifest (
                    artifact_id,
                    run_id,
                    run_table,
                    artifact_key,
                    artifact_path,
                    content_hash,
                    artifact_role,
                    created_at,
                    metadata_json,
                    status_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"art_databento_metadata_{dataset_version_id}",
                    dataset_version_id,
                    "dataset_versions",
                    "databento_dataset_metadata",
                    registry_path.as_posix(),
                    metadata_hash,
                    "dataset_partition_and_continuous_provenance",
                    created_at.isoformat(),
                    payload,
                    "ADF1 Run 3a Databento dataset metadata",
                ),
            )
        except sqlite3.IntegrityError as exc:
            msg = f"Databento dataset metadata already exists for {dataset_version_id}"
            raise DataFoundationValidationError(msg) from exc


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register local Databento canonical OHLCV and BBO DatasetVersions",
    )
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--request-spec", type=Path, required=True)
    parser.add_argument("--registry-path", type=Path, required=True)
    parser.add_argument("--ohlcv-data-version", required=True)
    parser.add_argument("--bbo-data-version", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--instrument-config", type=Path, required=True)
    parser.add_argument("--calendar-config", type=Path, required=True)
    parser.add_argument("--validation-config", type=Path, required=True)
    return parser.parse_args(argv)


def _print_summary(summary: RegisterSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.databento.register_dataset``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = run_register_dataset(
            canonical_root=args.canonical_root,
            request_spec=DatabentoRequestSpec.from_mapping(load_json_mapping(args.request_spec)),
            registry_path=args.registry_path,
            ohlcv_data_version=args.ohlcv_data_version,
            bbo_data_version=args.bbo_data_version,
            partition=args.partition,
            instrument_config_path=args.instrument_config,
            calendar_config_path=args.calendar_config,
            validation_config_path=args.validation_config,
        )
    except DataFoundationValidationError as exc:
        print(f"register_dataset blocked: {exc}", file=sys.stderr)
        return 2
    _print_summary(summary)
    return 0 if summary.registered else 1


__all__ = ["RegisterSummary", "run_register_dataset"]


if __name__ == "__main__":
    raise SystemExit(main())
