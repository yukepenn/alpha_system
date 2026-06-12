from __future__ import annotations

import json
import sqlite3
import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from alpha_system.data.databento import canonicalize as canonicalize_module
from alpha_system.data.databento.canonicalize import run_canonicalize
from alpha_system.data.databento.manifest_files import (
    DatabentoFileManifest,
    DatabentoFileRecord,
)
from alpha_system.data.databento.register_dataset import run_register_dataset
from alpha_system.data.databento.request_spec import DatabentoRequestSpec, write_json_mapping
from alpha_system.data.foundation.sources import DataFoundationValidationError

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
SESSION_START = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)
SESSION_END = datetime(2024, 1, 3, 22, 0, tzinfo=UTC)
ROOTS = ("ES", "NQ", "RTY")
SYMBOLS = tuple(f"{root}.v.0" for root in ROOTS)
INSTRUMENT_CONFIG = Path("configs/data/databento_es_nq_rty_instruments.json")
CALENDAR_CONFIG = Path("configs/data/session_templates_and_calendar.json")
VALIDATION_CONFIG = Path("configs/data/databento_materialize_validation.json")
PRICE_SCALE = Decimal("1000000000")
DATABENTO_UNDEF_PRICE = 2**63 - 1


def _spec() -> DatabentoRequestSpec:
    return DatabentoRequestSpec(
        symbols=SYMBOLS,
        stype_in="continuous",
        schemas=("ohlcv-1m", "bbo-1m"),
        start=SESSION_START,
        end=SESSION_END,
    )


def _tbbo_spec() -> DatabentoRequestSpec:
    return DatabentoRequestSpec(
        symbols=SYMBOLS,
        stype_in="continuous",
        schemas=("tbbo",),
        start=SESSION_START,
        end=SESSION_END,
    )


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


def _fixed_price(value: Decimal) -> int:
    return int(value * PRICE_SCALE)


def _record_source(
    *,
    drop_ohlcv: set[tuple[str, int]] | None = None,
    drop_bbo: set[tuple[str, int]] | None = None,
    crossed_bbo: set[tuple[str, int]] | None = None,
    out_of_interval_bbo: set[tuple[str, int]] | None = None,
    undefined_bbo_price: set[tuple[str, int]] | None = None,
) -> object:
    drop_ohlcv = drop_ohlcv or set()
    drop_bbo = drop_bbo or set()
    crossed_bbo = crossed_bbo or set()
    out_of_interval_bbo = out_of_interval_bbo or set()
    undefined_bbo_price = undefined_bbo_price or set()

    def source(**kwargs: object) -> Mapping[str, tuple[Mapping[str, object], ...]]:
        del kwargs
        ohlcv_rows = []
        bbo_rows = []
        minute_count = int((SESSION_END - SESSION_START).total_seconds() // 60)
        base_prices = {"ES": Decimal("5000"), "NQ": Decimal("17000"), "RTY": Decimal("2000")}
        for root in ROOTS:
            symbol = f"{root}.v.0"
            base = base_prices[root]
            for index in range(minute_count):
                start = SESSION_START + timedelta(minutes=index)
                end = start + timedelta(minutes=1)
                open_price = base + (Decimal(index) / Decimal("100"))
                close_price = open_price + Decimal("0.01")
                high_price = close_price + Decimal("0.02")
                low_price = open_price - Decimal("0.02")
                if (root, index) not in drop_ohlcv:
                    ohlcv_rows.append(
                        {
                            "schema": "ohlcv-1m",
                            "symbol": symbol,
                            "instrument_id": index + 1,
                            "ts_event": start,
                            "open": _fixed_price(open_price),
                            "high": _fixed_price(high_price),
                            "low": _fixed_price(low_price),
                            "close": _fixed_price(close_price),
                            "volume": "10",
                        }
                    )
                if (root, index) in drop_bbo:
                    continue
                bid = close_price - Decimal("0.25")
                ask = close_price
                if (root, index) in crossed_bbo:
                    ask = bid - Decimal("0.25")
                bid_value = _fixed_price(bid)
                ask_value = _fixed_price(ask)
                if (root, index) in undefined_bbo_price:
                    bid_value = DATABENTO_UNDEF_PRICE
                event_ts = start + timedelta(seconds=30)
                if (root, index) in out_of_interval_bbo:
                    event_ts = end + timedelta(seconds=1)
                bbo_rows.append(
                    {
                        "schema": "bbo-1m",
                        "symbol": symbol,
                        "instrument_id": index + 1,
                        "bar_start_ts": start,
                        "ts_event": event_ts,
                        "bid_px_00": bid_value,
                        "ask_px_00": ask_value,
                        "bid_sz_00": "12",
                        "ask_sz_00": "11",
                        "bid_ct_00": 2,
                        "ask_ct_00": 3,
                    }
                )
        return {"ohlcv-1m": tuple(ohlcv_rows), "bbo-1m": tuple(bbo_rows)}

    return source


def _tbbo_record_source() -> object:
    def source(**kwargs: object) -> Mapping[str, tuple[Mapping[str, object], ...]]:
        del kwargs
        base_prices = {"ES": Decimal("5000"), "NQ": Decimal("17000"), "RTY": Decimal("2000")}
        rows = []
        for index, root in enumerate(ROOTS):
            symbol = f"{root}.v.0"
            trade_price = base_prices[root] + Decimal("0.50")
            bid = trade_price - Decimal("0.25")
            ask = trade_price + Decimal("0.25")
            rows.append(
                {
                    "schema": "tbbo",
                    "symbol": symbol,
                    "instrument_id": index + 1,
                    "ts_event": SESSION_START + timedelta(minutes=index, seconds=15),
                    "price": _fixed_price(trade_price),
                    "size": str(index + 2),
                    "side": "A" if root == "ES" else "B",
                    "bid_px_00": _fixed_price(bid),
                    "ask_px_00": _fixed_price(ask),
                    "bid_sz_00": str(11 + index),
                    "ask_sz_00": str(12 + index),
                    "bid_ct_00": 2 + index,
                    "ask_ct_00": 3 + index,
                    "sequence": 1000 + index,
                    "ts_in_delta": 500 + index,
                }
            )
        return {"tbbo": tuple(rows)}

    return source


def _env(data_root: Path) -> dict[str, str]:
    return {"CI": "true", "ALPHA_DATA_ROOT": data_root.as_posix()}


def _canonicalize(
    tmp_path: Path,
    data_root: Path,
    *,
    record_source: object,
):
    return run_canonicalize(
        file_manifest_path=_write_file_manifest(tmp_path, data_root),
        request_spec=_spec(),
        output_root=data_root,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        record_source=record_source,
        env=_env(data_root),
        now=NOW,
    )


def _jsonl_rows(paths: tuple[str, ...]) -> list[dict[str, object]]:
    rows = []
    for path_text in paths:
        path = Path(path_text)
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle if line.strip())
            continue
        if path.suffix == ".parquet":
            pyarrow = canonicalize_module._optional_module("pyarrow")
            if pyarrow is not None:
                parquet = canonicalize_module.importlib.import_module("pyarrow.parquet")
                rows.extend(parquet.read_table(path).to_pylist())
                continue
            polars = canonicalize_module._optional_module("polars")
            if polars is not None:
                rows.extend(polars.read_parquet(path.as_posix()).to_dicts())
                continue
    return rows


def test_databento_tbbo_canonicalize_partition_manifest_and_fields_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root = tmp_path / "alpha_data"
    monkeypatch.setattr(canonicalize_module, "_optional_module", lambda module_name: None)

    summary = run_canonicalize(
        file_manifest_path=_write_file_manifest(tmp_path, data_root),
        request_spec=_tbbo_spec(),
        output_root=data_root,
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        record_source=_tbbo_record_source(),
        env=_env(data_root),
        now=NOW,
    )

    assert summary.ohlcv_row_count == 0
    assert summary.bbo_row_count == 0
    assert summary.tbbo_row_count == 3
    assert summary.missing_bbo_row_count == 0
    assert summary.quarantined_row_count == 0
    assert tuple(summary.output_paths) == ("tbbo",)
    assert summary.tbbo_data_version is not None

    manifest_path = Path(summary.canonical_root) / summary.tbbo_data_version / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["partition_schema"] == "tbbo"
    assert manifest["row_count"] == 3
    assert tuple(manifest["paths"]) == summary.output_paths["tbbo"]

    rows = _jsonl_rows(summary.output_paths["tbbo"])
    assert len(rows) == 3
    first = next(row for row in rows if row["instrument_id"] == "inst_databento_es")
    assert first["event_ts"] == (SESSION_START + timedelta(seconds=15)).isoformat()
    assert first["available_ts"] == (SESSION_START + timedelta(seconds=20)).isoformat()
    assert Decimal(str(first["trade_price"])) == Decimal("5000.50")
    assert Decimal(str(first["trade_size"])) == Decimal("2")
    assert first["aggressor_side"] == "ask"
    assert Decimal(str(first["bid"])) == Decimal("5000.25")
    assert Decimal(str(first["ask"])) == Decimal("5000.75")
    assert Decimal(str(first["bid_size"])) == Decimal("11")
    assert Decimal(str(first["ask_size"])) == Decimal("12")
    assert first["session_label"] == "ETH"
    assert first["sequence"] == 1000
    assert first["ts_in_delta"] == 500


def test_databento_canonicalize_quality_coverage_and_register_offline(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "registry.sqlite"

    summary = _canonicalize(tmp_path, data_root, record_source=_record_source())

    assert summary.ohlcv_row_count == summary.bbo_row_count == 3 * 23 * 60
    assert summary.missing_bbo_row_count == 0
    assert summary.quarantined_row_count == 0
    assert "databento" not in sys.modules
    assert "databento_dbn" not in sys.modules
    for paths in summary.output_paths.values():
        for path_text in paths:
            Path(path_text).relative_to(data_root)

    ohlcv_rows = _jsonl_rows(summary.output_paths["ohlcv_1m"])
    assert ohlcv_rows
    first_ohlcv = next(
        row for row in ohlcv_rows if row["bar_start_ts"] == SESSION_START.isoformat()
    )
    assert Decimal(str(first_ohlcv["open"])) == Decimal("5000")
    assert Decimal(str(first_ohlcv["high"])) == Decimal("5000.03")
    assert Decimal(str(first_ohlcv["low"])) == Decimal("4999.98")
    assert Decimal(str(first_ohlcv["close"])) == Decimal("5000.01")
    for row in ohlcv_rows[:25]:
        bar_end = datetime.fromisoformat(str(row["bar_end_ts"]))
        event = datetime.fromisoformat(str(row["event_ts"]))
        available = datetime.fromisoformat(str(row["available_ts"]))
        ingested = datetime.fromisoformat(str(row["ingested_at"]))
        assert event == bar_end
        assert available >= bar_end
        assert ingested != available

    bbo_rows = _jsonl_rows(summary.output_paths["bbo_1m"])
    assert bbo_rows
    first_bbo = next(
        row
        for row in bbo_rows
        if row["bar_start_ts"] == SESSION_START.isoformat()
        and Decimal(str(row["bid"])) == Decimal("4999.76")
    )
    bbo_start = datetime.fromisoformat(str(first_bbo["bar_start_ts"]))
    bbo_end = datetime.fromisoformat(str(first_bbo["bar_end_ts"]))
    bbo_event = datetime.fromisoformat(str(first_bbo["event_ts"]))
    bbo_available = datetime.fromisoformat(str(first_bbo["available_ts"]))
    assert bbo_start < bbo_event < bbo_end
    assert bbo_event == bbo_start + timedelta(seconds=30)
    assert bbo_available >= bbo_end
    assert Decimal(str(first_bbo["bid"])) == Decimal("4999.76")
    assert Decimal(str(first_bbo["ask"])) == Decimal("5000.01")

    registered = run_register_dataset(
        canonical_root=summary.canonical_root,
        request_spec=_spec(),
        registry_path=registry_path,
        ohlcv_data_version=summary.ohlcv_data_version,
        bbo_data_version=summary.bbo_data_version,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    assert registered.registered is True
    assert registered.ohlcv_quality_status == "PASSING"
    assert registered.ohlcv_coverage_status == "PASSING"
    assert registered.bbo_quality_status == "PASSING"
    assert registered.bbo_coverage_status == "PASSING"
    assert registered.provenance["provider_continuous"] is True
    assert registered.provenance["not_roll_truth"] is True

    with sqlite3.connect(registry_path) as connection:
        dataset_rows = connection.execute(
            "SELECT data_version FROM dataset_versions ORDER BY data_version"
        ).fetchall()
        metadata_rows = connection.execute(
            """
            SELECT metadata_json
            FROM artifact_manifest
            WHERE artifact_key = 'databento_dataset_metadata'
            ORDER BY run_id
            """
        ).fetchall()

    assert {row[0] for row in dataset_rows} == {
        summary.ohlcv_data_version,
        summary.bbo_data_version,
    }
    metadata = [json.loads(row[0]) for row in metadata_rows]
    assert any(
        item.get("companion_bbo_dataset_version_id") == summary.bbo_data_version
        for item in metadata
    )
    assert any(
        item.get("companion_ohlcv_dataset_version_id") == summary.ohlcv_data_version
        for item in metadata
    )


def test_databento_real_dbn_loader_requests_raw_fixed_point_prices(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_root = tmp_path / "alpha_data" / "raw"
    calls = []

    class FakeFrame:
        def __init__(self, path_name: str) -> None:
            self.path_name = path_name

        def reset_index(self) -> FakeFrame:
            return self

        def to_dict(self, orient: str) -> list[Mapping[str, object]]:
            assert orient == "records"
            if self.path_name == "b.dbn.zst":
                return [{"symbol": "ES.v.0", "price": _fixed_price(Decimal("5000.25"))}]
            return [{"symbol": "ES.v.0", "open": _fixed_price(Decimal("5000"))}]

    class FakeStore:
        def __init__(self, path_name: str) -> None:
            self.path_name = path_name

        def to_df(self, **kwargs: object) -> FakeFrame:
            calls.append(kwargs)
            return FakeFrame(self.path_name)

    class FakeDBNStore:
        @staticmethod
        def from_file(path: Path) -> FakeStore:
            assert path.name in {"a.dbn.zst", "b.dbn.zst"}
            return FakeStore(path.name)

    monkeypatch.setitem(
        sys.modules,
        "databento_dbn",
        SimpleNamespace(DBNStore=FakeDBNStore),
    )
    manifest = DatabentoFileManifest(
        raw_root=raw_root.as_posix(),
        files=(
            DatabentoFileRecord(
                relative_path="glbx_mdp3/continuous/ohlcv-1m/job-a/a.dbn.zst",
                schema="ohlcv-1m",
                job_id="job-a",
                sha256="0" * 64,
                size_bytes=0,
            ),
            DatabentoFileRecord(
                relative_path="glbx_mdp3/continuous/tbbo/job-b/b.dbn.zst",
                schema="tbbo",
                job_id="job-b",
                sha256="1" * 64,
                size_bytes=0,
            ),
        ),
        file_count=2,
        total_bytes=0,
        created_at=NOW,
    )

    rows = canonicalize_module._load_real_dbn_rows(manifest)

    assert calls == [
        {"price_type": "fixed", "pretty_ts": True, "map_symbols": True},
        {"price_type": "fixed", "pretty_ts": True, "map_symbols": True},
    ]
    assert rows["ohlcv-1m"][0]["job_id"] == "job-a"
    assert rows["tbbo"][0]["job_id"] == "job-b"


def test_databento_missing_bbo_metric_does_not_block_registration(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "missing_bbo.sqlite"
    summary = _canonicalize(
        tmp_path,
        data_root,
        record_source=_record_source(
            drop_bbo={("RTY", 20)},
        ),
    )

    assert summary.quarantined_row_count == 0
    assert summary.missing_bbo_row_count == 1

    registered = run_register_dataset(
        canonical_root=summary.canonical_root,
        request_spec=_spec(),
        registry_path=registry_path,
        ohlcv_data_version=summary.ohlcv_data_version,
        bbo_data_version=summary.bbo_data_version,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    assert registered.registered is True
    assert registered.registry_path == registry_path.as_posix()
    assert registered.ohlcv_quality_status == "PASSING"
    assert registered.ohlcv_coverage_status == "PASSING"
    assert registered.bbo_quality_status == "WARNING"
    assert registered.blocking_summary["bbo_quality_blocks"] is False
    assert registered.blocking_summary["bbo_missing_metric"]["count"] == 1
    assert registry_path.exists()


def test_databento_out_of_interval_and_undefined_bbo_quarantine_blocks_registration(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "alpha_data"
    registry_path = tmp_path / "bad_bbo.sqlite"
    summary = _canonicalize(
        tmp_path,
        data_root,
        record_source=_record_source(
            out_of_interval_bbo={("ES", 40)},
            undefined_bbo_price={("NQ", 41)},
        ),
    )

    assert summary.quarantined_row_count >= 2
    assert summary.missing_bbo_row_count >= 2

    registered = run_register_dataset(
        canonical_root=summary.canonical_root,
        request_spec=_spec(),
        registry_path=registry_path,
        ohlcv_data_version=summary.ohlcv_data_version,
        bbo_data_version=summary.bbo_data_version,
        partition="development_partition",
        instrument_config_path=INSTRUMENT_CONFIG,
        calendar_config_path=CALENDAR_CONFIG,
        validation_config_path=VALIDATION_CONFIG,
        env=_env(data_root),
        now=NOW,
    )

    assert registered.registered is False
    assert registered.bbo_quality_status == "BLOCKING"
    assert not registry_path.exists()


def test_databento_canonicalize_rejects_in_repo_output_root(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    in_repo_output = Path.cwd() / "tmp_databento_canonical_should_not_exist"

    with pytest.raises(DataFoundationValidationError, match="repository"):
        run_canonicalize(
            file_manifest_path=_write_file_manifest(tmp_path, data_root),
            request_spec=_spec(),
            output_root=in_repo_output,
            instrument_config_path=INSTRUMENT_CONFIG,
            calendar_config_path=CALENDAR_CONFIG,
            validation_config_path=VALIDATION_CONFIG,
            record_source=_record_source(),
            env=_env(data_root),
            now=NOW,
        )

    assert not in_repo_output.exists()
