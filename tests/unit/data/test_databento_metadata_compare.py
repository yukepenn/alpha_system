from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.data.databento.compare_sources import run_compare_sources
from alpha_system.data.databento.manifest_files import DatabentoFileManifest
from alpha_system.data.databento.metadata_ingest import run_metadata_ingest
from alpha_system.data.databento.request_spec import write_json_mapping
from alpha_system.data.foundation.sources import DataFoundationValidationError

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
START = datetime(2024, 6, 3, 13, 30, tzinfo=UTC)


def _env(data_root: Path) -> dict[str, str]:
    return {"CI": "true", "ALPHA_DATA_ROOT": data_root.as_posix()}


def _write_file_manifest(tmp_path: Path, data_root: Path) -> Path:
    manifest = DatabentoFileManifest(
        raw_root=(data_root / "raw").as_posix(),
        files=(),
        file_count=0,
        total_bytes=0,
        created_at=NOW,
    )
    path = tmp_path / "databento_files.json"
    write_json_mapping(path, manifest.to_mapping())
    return path


def _metadata_record_source(**kwargs: object) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    del kwargs
    return {
        "definition": (
            {
                "schema": "definition",
                "instrument_id": 123,
                "raw_symbol": "ESM4",
                "expiration": "20240621",
                "activation": "2024-03-01T00:00:00Z",
                "min_price_increment": 250000000,
                "contract_multiplier": "50",
                "unit_of_measure": "USD",
                "security_type": "FUT",
            },
        ),
        "statistics": (
            {
                "schema": "statistics",
                "instrument_id": 123,
                "raw_symbol": "ESM4",
                "stat_type": "Settlement Price",
                "price": 5000125000000,
                "quantity": "100",
            },
        ),
        "status": (
            {
                "schema": "status",
                "instrument_id": 123,
                "raw_symbol": "ESM4",
                "ts_event": "2024-06-03T13:30:00Z",
                "action": "HALT",
                "reason": "pause",
                "is_trading": False,
                "is_quoting": False,
            },
        ),
    }


def test_metadata_ingest_writes_normalized_refs_and_warnings(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    manifest_path = _write_file_manifest(tmp_path, data_root)

    summary = run_metadata_ingest(
        file_manifest_path=manifest_path,
        output_root=data_root,
        record_source=_metadata_record_source,
        env=_env(data_root),
        now=NOW,
    )

    assert summary.counts_by_schema == {"definition": 1, "statistics": 1, "status": 1}
    assert any("without daily date refs" in warning for warning in summary.warnings)
    manifest_text = Path(summary.manifest_path).read_text(encoding="utf-8")
    assert "DATABENTO_API_KEY" not in manifest_text
    assert "db-" not in manifest_text
    for paths in summary.ref_paths.values():
        for path_text in paths:
            path = Path(path_text)
            path.relative_to(data_root)
            assert path.exists()
            text = path.read_text(encoding="utf-8")
            assert "DATABENTO_API_KEY" not in text
            assert "db-" not in text

    definition_payload = json.loads(Path(summary.ref_paths["definition"][0]).read_text())
    definition = definition_payload["records"][0]
    assert definition["root"] == "ES"
    assert definition["tick_size"] == "0.25"
    assert definition["contract_multiplier"] == "50"
    assert definition["expiration"] == "2024-06-21"

    status_payload = json.loads(Path(summary.ref_paths["status"][0]).read_text())
    assert status_payload["records"][0]["status_kind"] == "halt"


def test_metadata_ingest_rejects_in_repo_output_root(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    in_repo_output = Path.cwd() / "tmp_databento_metadata_should_not_exist"

    with pytest.raises(DataFoundationValidationError, match="repository"):
        run_metadata_ingest(
            file_manifest_path=_write_file_manifest(tmp_path, data_root),
            output_root=in_repo_output,
            record_source=_metadata_record_source,
            env=_env(data_root),
            now=NOW,
        )

    assert not in_repo_output.exists()


def _bar(
    *,
    root: str = "ES",
    provider: str,
    start: datetime,
    close: str,
    volume: str,
) -> dict[str, object]:
    return {
        "instrument_id": f"inst_{provider}_{root.lower()}",
        "contract_id": f"contract_{provider}_{root.lower()}",
        "series_id": f"series_{provider}_{root.lower()}",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": (start + timedelta(minutes=1)).isoformat(),
        "event_ts": (start + timedelta(minutes=1)).isoformat(),
        "available_ts": (start + timedelta(minutes=1)).isoformat(),
        "ingested_at": NOW.isoformat(),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": volume,
        "source": f"dsrc_{provider}_historical",
        "source_request_id": f"req_{provider}",
        "data_version": f"dsv_{provider}",
        "quality_flags": [],
        "session_label": "ETH",
    }


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def _write_registry(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE dataset_versions (data_version TEXT, source_uri TEXT, metadata_json TEXT)"
        )
        connection.execute(
            "INSERT INTO dataset_versions VALUES (?, ?, ?)",
            ("dsv_ibkr_es_dated_202404_validation_v1", "dsrc_ibkr_historical", "{}"),
        )


def _write_compare_inputs(data_root: Path) -> tuple[Path, Path]:
    databento_root = data_root / "databento" / "canonical" / "glbx_mdp3"
    ibkr_root = data_root / "ibkr" / "canonical"
    _write_jsonl(
        databento_root
        / "dsv_databento_ohlcv_unit"
        / "schema=ohlcv_1m"
        / "root=ES"
        / "part-00000.jsonl",
        (
            _bar(provider="databento", start=START, close="100.00", volume="10"),
            _bar(
                provider="databento",
                start=START + timedelta(minutes=1),
                close="101.00",
                volume="12",
            ),
            _bar(
                provider="databento",
                start=START + timedelta(minutes=2),
                close="102.00",
                volume="14",
            ),
        ),
    )
    _write_jsonl(
        databento_root
        / "dsv_databento_bbo_unit"
        / "schema=bbo_1m"
        / "root=ES"
        / "part-00000.jsonl",
        ({"bar_start_ts": START.isoformat(), "bid": "99.75", "ask": "100.00"},),
    )
    _write_jsonl(
        ibkr_root / "dsv_ibkr_unit" / "schema=ohlcv_1m" / "root=ES" / "part-00000.jsonl",
        (
            _bar(provider="ibkr", start=START, close="100.25", volume="9"),
            _bar(
                provider="ibkr",
                start=START + timedelta(minutes=1),
                close="100.75",
                volume="13",
            ),
            _bar(
                provider="ibkr",
                start=START + timedelta(minutes=3),
                close="103.00",
                volume="15",
            ),
        ),
    )
    return databento_root, ibkr_root


def test_compare_sources_writes_diagnostic_deltas_without_merge(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    registry = tmp_path / "registry.sqlite"
    _write_registry(registry)
    databento_root, ibkr_root = _write_compare_inputs(data_root)
    output = data_root / "reports" / "compare.json"

    summary = run_compare_sources(
        databento_canonical_root=databento_root,
        ibkr_registry_path=registry,
        ibkr_symbol_root=ibkr_root,
        output_path=output,
        env=_env(data_root),
        now=NOW,
    )

    assert summary.status == "COMPARED_WITH_WARNINGS"
    assert summary.diagnostic_only is True
    assert summary.merged_dataset_version_created is False
    assert summary.ibkr_dataset_version_ids == ("dsv_ibkr_es_dated_202404_validation_v1",)
    assert summary.overlapping_session_count == 1
    assert "Databento-only BBO-1m" in summary.bbo_availability_note
    session = summary.session_summaries[0]
    assert session["overlapping_interval_count"] == 2
    assert session["mean_abs_close_diff"] == "0.25"
    assert session["max_abs_close_diff"] == "0.25"
    assert session["missing_in_databento_count"] == 1
    assert session["missing_in_ibkr_count"] == 1
    assert session["volume_difference"] == "-1"
    assert any("close prices differ" in warning for warning in summary.warnings)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["merged_dataset_version_created"] is False
    assert "DATABENTO_API_KEY" not in output.read_text(encoding="utf-8")
    assert "db-" not in output.read_text(encoding="utf-8")


def test_compare_sources_no_overlap_is_explicit(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    registry = tmp_path / "registry.sqlite"
    _write_registry(registry)
    databento_root = data_root / "databento" / "canonical" / "glbx_mdp3"
    ibkr_root = data_root / "ibkr" / "canonical"
    _write_jsonl(
        databento_root
        / "dsv_databento_ohlcv_unit"
        / "schema=ohlcv_1m"
        / "root=ES"
        / "part-00000.jsonl",
        (_bar(provider="databento", start=START, close="100.00", volume="10"),),
    )
    _write_jsonl(
        ibkr_root / "dsv_ibkr_unit" / "schema=ohlcv_1m" / "root=ES" / "part-00000.jsonl",
        (
            _bar(
                provider="ibkr",
                start=START + timedelta(days=1),
                close="100.00",
                volume="10",
            ),
        ),
    )

    summary = run_compare_sources(
        databento_canonical_root=databento_root,
        ibkr_registry_path=registry,
        ibkr_symbol_root=ibkr_root,
        output_path=data_root / "reports" / "no_overlap.json",
        env=_env(data_root),
        now=NOW,
    )

    assert summary.status == "NO_OVERLAP"
    assert summary.overlapping_session_count == 0
    assert summary.session_summaries == ()
    assert any("no overlapping" in warning for warning in summary.warnings)
