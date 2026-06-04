from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from alpha_system.core.registry import connect_registry
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.data.materialize import main as materialize_main
from alpha_system.data.materialize import run_materialize

START = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
END = datetime(2026, 6, 1, 14, 33, tzinfo=UTC)
NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)


def _write_raw_payload(data_root: Path, rows: list[dict[str, str]]) -> Path:
    header = [
        "symbol",
        "contract_ref",
        "provider_ts",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "wap",
        "barCount",
    ]
    scratch = data_root / "scratch.csv"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    with scratch.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    payload = scratch.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    path = (
        data_root
        / "raw"
        / "source=dsrc_ibkr_historical"
        / "request=hrs_materialize_unit"
        / "chunk=hchunk_materialize_unit"
        / f"sha256={digest[:2]}"
        / f"{digest}.raw"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    scratch.unlink()
    return path


def _row(minute: int) -> dict[str, str]:
    return {
        "symbol": "ES",
        "contract_ref": "fcr_ibkr_es_fut_202606",
        "provider_ts": f"2026-06-01 14:{30 + minute:02d}:00 UTC",
        "open": "5000.00",
        "high": "5001.00",
        "low": "4999.50",
        "close": "5000.50",
        "volume": "10",
        "wap": "5000.25",
        "barCount": "3",
    }


def _write_calendar(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "calendar_id": "SYNTH_MATERIALIZE",
                "timezone": "UTC",
                "regular_session": {
                    "open": "14:30",
                    "close": "14:33",
                    "session_type": "regular",
                },
                "sessions": [
                    {"trading_date": "2026-06-01", "session_type": "regular"}
                ],
                "metadata": {"fixture_scope": "materialize_unit"},
            }
        ),
        encoding="utf-8",
    )


def _write_instrument_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "allow_non_fixture_input": True,
                "session_label": "RTH",
                "roll_policy_id": "roll_cme_index_futures_quarterly",
                "instruments": [
                    {
                        "symbol": "ES",
                        "instrument_id": "inst_ibkr_es",
                        "series_id": "series_ibkr_es_front_unadjusted",
                        "session_label": "RTH",
                        "roll_policy_id": "roll_cme_index_futures_quarterly",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_validation_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "allow_non_fixture_input": True,
                "available_latency_seconds": 0,
                "require_event_within_bar": True,
            }
        ),
        encoding="utf-8",
    )


def _configs(tmp_path: Path) -> tuple[Path, Path, Path]:
    instrument = tmp_path / "instrument.json"
    calendar = tmp_path / "calendar.json"
    validation = tmp_path / "validation.json"
    _write_instrument_config(instrument)
    _write_calendar(calendar)
    _write_validation_config(validation)
    return instrument, calendar, validation


def test_materialize_registers_passing_dataset_version(tmp_path: Path) -> None:
    data_root = tmp_path / "alpha_data"
    _write_raw_payload(data_root, [_row(0), _row(1), _row(2)])
    instrument, calendar, validation = _configs(tmp_path)
    registry = tmp_path / "registry.sqlite"

    summary = run_materialize(
        symbols=("ES",),
        registry_path=registry,
        data_version="dsv_materialize_unit_v1",
        partition="locked_test_candidate",
        start_ts=START,
        end_ts=END,
        instrument_config_path=instrument,
        calendar_config_path=calendar,
        validation_config_path=validation,
        env={"ALPHA_DATA_ROOT": data_root.as_posix()},
        now=NOW,
    )

    assert summary.registered is True
    assert summary.quality_status == "PASSING"
    assert summary.coverage_status == "PASSING"
    assert summary.canonical_row_count == 3
    version = resolve_dataset_version(registry, "dsv_materialize_unit_v1")
    assert version is not None
    assert version.contract_universe == ("fcr_ibkr_es_fut_202606",)
    with connect_registry(registry, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT metadata_json
            FROM artifact_manifest
            WHERE artifact_key = 'partition_contamination_metadata'
            """
        ).fetchone()
    assert row is not None
    metadata = json.loads(str(row["metadata_json"]))
    assert metadata["partition_id"] == "locked_test_candidate"
    assert metadata["contamination_metadata_rules"]["implies_research_approval"] is False


def test_materialize_gap_refuses_registry_write(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    data_root = tmp_path / "alpha_data"
    _write_raw_payload(data_root, [_row(0), _row(2)])
    instrument, calendar, validation = _configs(tmp_path)
    registry = tmp_path / "registry.sqlite"
    monkeypatch.setenv("ALPHA_DATA_ROOT", data_root.as_posix())

    result = materialize_main(
        [
            "--symbols",
            "ES",
            "--registry-path",
            registry.as_posix(),
            "--data-version",
            "dsv_materialize_gap_unit_v1",
            "--partition",
            "locked_test_candidate",
            "--start-ts",
            START.isoformat(),
            "--end-ts",
            END.isoformat(),
            "--instrument-config",
            instrument.as_posix(),
            "--calendar-config",
            calendar.as_posix(),
            "--validation-config",
            validation.as_posix(),
        ]
    )
    captured = capsys.readouterr()

    assert result == 1
    assert not registry.exists()
    payload = json.loads(captured.out)
    assert payload["registered"] is False
    assert payload["quality_status"] == "BLOCKING"
