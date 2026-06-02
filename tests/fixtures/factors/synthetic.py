from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.factors.registry import record_factor_validation_run
from alpha_system.factors.spec import FactorSpec, compute_factor_config_hash


DATA_VERSION = "data:synthetic-factor-compute:v1"


def make_bars(
    closes: list[str | int | float | Decimal],
    *,
    session_id: str = "XNYS:2026-01-02:regular",
    instrument_id: str = "SYNTH_FACTOR",
    data_version: str = DATA_VERSION,
    quality_flags: tuple[str, ...] = ("synthetic", "correctness_only"),
    start: datetime = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc),
    available_delay: timedelta = timedelta(seconds=5),
) -> list[dict[str, Any]]:
    close_values = [_decimal(value) for value in closes]
    bars: list[dict[str, Any]] = []
    for index, close in enumerate(close_values):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        spread = Decimal("0.20")
        bars.append(
            {
                "instrument_id": instrument_id,
                "session_id": session_id,
                "bar_index": index,
                "bar_start_ts": bar_start,
                "bar_end_ts": bar_end,
                "event_ts": bar_end,
                "available_ts": bar_end + available_delay,
                "open": close_values[index - 1] if index else close,
                "high": close + Decimal("0.50"),
                "low": close - Decimal("0.50"),
                "close": close,
                "volume": Decimal("1000") + Decimal(index),
                "vwap": close,
                "trade_count": 10 + index,
                "bid": close - (spread / Decimal("2")),
                "ask": close + (spread / Decimal("2")),
                "spread": spread,
                "source_version": "src:synthetic-factor-compute:v1",
                "data_version": data_version,
                "quality_flags": quality_flags,
            }
        )
    return bars


def factor_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "factor_id": "fixture_close_delta",
        "name": "Fixture Close Delta",
        "version": "v1",
        "owner": "research_governance",
        "description": "Synthetic deterministic correctness fixture; not alpha evidence.",
        "input_fields": [
            {"name": "close_price", "domain": "bar", "source_field": "close"}
        ],
        "parameters": {
            "data_version": DATA_VERSION,
            "fixture_compute": {
                "name": "close_delta",
                "input_name": "close_price",
                "lag_bars": 1,
            },
            "normalization": {"method": "identity"},
        },
        "frequency": "1m",
        "warmup_bars": 2,
        "session_reset": True,
        "availability_lag": 60,
        "factor_type": "continuous",
        "evaluation_type": "point_in_time",
        "code_hash": "f" * 64,
        "config_hash": "0" * 64,
        "status": "draft",
        "created_at": "2026-01-02T14:30:00Z",
        "validation_artifact_path": None,
    }
    payload.update(overrides)
    payload["config_hash"] = compute_factor_config_hash(payload)
    return payload


def factor_spec(**overrides: object) -> FactorSpec:
    return FactorSpec.from_mapping(factor_payload(**overrides))


def validated_factor_spec() -> FactorSpec:
    return factor_spec(
        status="validated",
        validation_artifact_path="artifacts/factor_compute_fixture_validation.md",
    )


def seed_validated_registry(registry_path: Path, spec: FactorSpec) -> None:
    record_factor_validation_run(
        registry_path,
        spec,
        run_id=f"validation:{spec.factor_id}:{spec.version}",
        decision_status="accepted",
        reviewer="fixture-review",
    )


def write_bars_jsonl(path: Path, bars: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(_json_bar(bar), sort_keys=True) + "\n" for bar in bars),
        encoding="utf-8",
    )
    return path


def write_spec_json(path: Path, spec: FactorSpec) -> Path:
    path.write_text(json.dumps(spec.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return path


def _json_bar(bar: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in bar.items():
        if isinstance(value, datetime):
            payload[key] = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        elif isinstance(value, Decimal):
            payload[key] = str(value)
        elif isinstance(value, tuple):
            payload[key] = list(value)
        else:
            payload[key] = value
    return payload


def _decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
