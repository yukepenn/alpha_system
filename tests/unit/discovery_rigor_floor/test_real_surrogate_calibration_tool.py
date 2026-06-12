from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tests._helpers.local_data import skip_unless_local_registry
from tools.discovery_rigor_floor.run_real_surrogate_calibration import (
    run_real_surrogate_calibration,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
COMMITTED_STUDY_SPEC = (
    REPO_ROOT
    / "research/futures_substrate_scaleout_v1/rerun/study_specs/"
    "sspec_da1bba367710c983b2ca644f.json"
)


def test_real_surrogate_calibration_tool_resolves_committed_locks_via_resolver(
    tmp_path: Path,
) -> None:
    feature_rows, label_rows = _value_rows()
    feature_path = _write_jsonl(tmp_path / "feature-values.jsonl", feature_rows)
    label_path = _write_jsonl(tmp_path / "label-values.jsonl", label_rows)
    resolver = _FakeResolver(
        feature_record=_FeatureRecord(
            feature_version_id="fver_" + "1" * 64,
            materialization_output_path=feature_path.as_posix(),
        ),
        label_record=_LabelRecord(
            label_version_id="lver_" + "2" * 64,
            materialization_output_path=label_path.as_posix(),
        ),
    )
    namespace = tmp_path / "rigor_p05_surrogate_real_tool"
    namespace.mkdir()
    report_path = tmp_path / "report.md"
    base_seed = _base_seed_without_bootstrap_identity(label_rows)

    result = run_real_surrogate_calibration(
        study_spec_path=COMMITTED_STUDY_SPEC,
        alpha_data_root=tmp_path / "alpha_data",
        runs_per_config=1,
        base_seed=base_seed,
        namespace=namespace,
        report_out=report_path,
        resolver=resolver,
    )

    assert result["accepted"] is True
    assert result["run_count"] == 2
    assert result["gate_pass_count"] == 0
    assert resolver.label_calls
    assert resolver.feature_calls
    rendered = report_path.read_text(encoding="utf-8")
    assert "Declared K per perturbation config: 1" in rendered
    assert "zero passes in K bounds false-pass rate at about 3/K at 95%" in rendered
    assert "trade_date_block_shuffle" in rendered
    assert "trade_date_block_bootstrap" in rendered
    staged_labels = namespace / "real_surrogate_inputs" / result["study_spec_id"] / "labels.jsonl"
    assert staged_labels.exists()
    assert json.loads(staged_labels.read_text(encoding="utf-8").splitlines()[0])[
        "event_ts"
    ].startswith("2026-01-02")


def test_real_local_label_registry_absence_is_loud_skip() -> None:
    data_root = Path(os.environ.get("ALPHA_DATA_ROOT", "~/alpha_data/alpha_system")).expanduser()
    skip_unless_local_registry(
        lambda: data_root / "registry/labels.sqlite",
        reason=(
            "real local label registry absent; synthetic resolver path covers CI "
            "and coordinator runs this against private local data"
        ),
    )


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_id: str = "fixture_close_delta"


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str
    materialization_output_path: str
    value_store_format: str = "jsonl"
    parquet_path: str | None = None
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str
    materialization_output_path: str
    value_store_format: str = "jsonl"
    parquet_path: str | None = None


class _FakeFeatureStore:
    def __init__(self, record: _FeatureRecord) -> None:
        self.record = record

    def resolve_registered_feature(self, feature_version_id: str) -> _FeatureRecord:
        return _FeatureRecord(
            feature_version_id=feature_version_id,
            materialization_output_path=self.record.materialization_output_path,
            feature_spec=self.record.feature_spec,
        )


class _FakeLabelRegistry:
    def __init__(self, record: _LabelRecord) -> None:
        self.record = record

    def resolve_registered_label(self, label_version_id: str) -> _LabelRecord:
        return _LabelRecord(
            label_version_id=label_version_id,
            materialization_output_path=self.record.materialization_output_path,
        )


class _FakeResolver:
    def __init__(self, *, feature_record: _FeatureRecord, label_record: _LabelRecord) -> None:
        self.feature_store = _FakeFeatureStore(feature_record)
        self.label_registry = _FakeLabelRegistry(label_record)
        self.feature_calls: list[dict[str, Any]] = []
        self.label_calls: list[dict[str, Any]] = []

    def resolve_label_packs(
        self,
        label_pack_refs: tuple[str, ...],
        *,
        expected_dataset_version_id: str,
        expected_label_spec_ids: tuple[str, ...],
        partition_id: str,
    ) -> tuple[object, ...]:
        self.label_calls.append(
            {
                "refs": label_pack_refs,
                "dataset_version_id": expected_dataset_version_id,
                "label_spec_ids": expected_label_spec_ids,
                "partition_id": partition_id,
            }
        )
        return ()

    def resolve_feature_packs(
        self,
        feature_pack_refs: tuple[str, ...],
        *,
        expected_dataset_version_id: str,
        expected_feature_request_ids: tuple[str, ...],
        partition_id: str,
    ) -> tuple[object, ...]:
        self.feature_calls.append(
            {
                "refs": feature_pack_refs,
                "dataset_version_id": expected_dataset_version_id,
                "feature_request_ids": expected_feature_request_ids,
                "partition_id": partition_id,
            }
        )
        return ()


def _value_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    values = [1.0, 2.0, -1.0, -2.0, 1.5, -1.5]
    for index, value in enumerate(values):
        event_ts = datetime(2026, 1, 2 + index // 2, 14, 31 + index % 2, tzinfo=UTC)
        horizon_end_ts = event_ts + timedelta(minutes=5)
        feature_rows.append(
            {
                "entity_id": "SYNTH",
                "event_ts": _text(event_ts),
                "available_ts": _text(event_ts + timedelta(seconds=5)),
                "value": value,
                "quality_flags": ["synthetic"],
            }
        )
        label_rows.append(
            {
                "entity_id": "SYNTH",
                "event_ts": _text(event_ts),
                "horizon_end_ts": _text(horizon_end_ts),
                "label_available_ts": _text(horizon_end_ts + timedelta(seconds=5)),
                "value": value / 100.0,
                "quality_flags": ["synthetic"],
            }
        )
    return feature_rows, label_rows


def _base_seed_without_bootstrap_identity(label_rows: list[dict[str, object]]) -> int:
    from alpha_system.governance.surrogate_run import write_trade_date_block_bootstrap_copy

    tmp = Path(os.environ.get("PYTEST_TMPDIR", "/tmp")) / "surrogate_seed_probe_labels.jsonl"
    out = Path(os.environ.get("PYTEST_TMPDIR", "/tmp")) / "surrogate_seed_probe_out.jsonl"
    _write_jsonl(tmp, _converted_label_rows(label_rows))
    for bootstrap_seed in range(1, 200):
        try:
            write_trade_date_block_bootstrap_copy(tmp, out, seed=bootstrap_seed)
        except Exception:
            continue
        return bootstrap_seed - 1
    raise AssertionError("no non-identity bootstrap seed found")


def _converted_label_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    converted: list[dict[str, object]] = []
    for row in rows:
        converted.append(
            {
                "label_id": "forward_return_5m",
                "instrument_id": row["entity_id"],
                "event_ts": row["event_ts"],
                "horizon": 300,
                "label_type": "forward_return_5m",
                "value": row["value"],
                "path_metadata": {
                    "session_id": f"SYNTH:{str(row['event_ts'])[:10]}:surrogate",
                    "label_version": "labels:v1",
                    "horizon_end_ts": row["horizon_end_ts"],
                    "required_future_bars": 1,
                    "observed_future_bars": 1,
                },
                "data_version": "data:v1",
                "label_available_ts": row["label_available_ts"],
            }
        )
    return converted


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
