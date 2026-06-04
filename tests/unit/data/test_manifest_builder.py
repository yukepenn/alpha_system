from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from alpha_system.data.foundation.ibkr import IBKRConnectionProfile
from alpha_system.data.foundation.requests import HistoricalRequestManifest
from alpha_system.data.ibkr.manifest_builder import (
    build_full_backfill_manifest,
    build_recent_slice_manifest,
    write_manifest_json,
)

NOW = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
DATA_ROOT = (Path.home() / "alpha_data" / "alpha_system_manifest_builder_unit").as_posix()
ENV = {
    "ALPHA_IBKR_HOST": "127.0.0.1",
    "ALPHA_IBKR_PORT": "4002",
    "ALPHA_IBKR_CLIENT_ID": "201",
    "ALPHA_DATA_ROOT": DATA_ROOT,
}


def _profile() -> IBKRConnectionProfile:
    return IBKRConnectionProfile.from_env(ENV)


def test_recent_slice_manifest_shape() -> None:
    manifest = build_recent_slice_manifest(
        env=ENV,
        profile=_profile(),
        now=NOW,
        symbols=("ES", "NQ", "RTY"),
        trading_days=2,
    )

    assert manifest.chunk_count == 3
    assert len(manifest.request_specs) == 3
    assert manifest.expected_coverage["quality_claim"] is False
    assert manifest.expected_coverage["real_coverage_claim"] is False
    assert {spec.symbol_root for spec in manifest.request_specs} == {"ES", "NQ", "RTY"}
    for spec in manifest.request_specs:
        assert spec.sec_type == "CONTFUT"
        assert spec.bar_size == "1 min"
        assert spec.what_to_show == "TRADES"
        assert spec.use_rth is False
        assert spec.duration == "2 D"
        assert spec.end_datetime_policy == "ibkr_contfut_uses_empty_end_datetime"
        assert spec.chunk_policy["planned_chunks"] == 1


def test_full_backfill_manifest_enumerates_quarterly_dated_futures() -> None:
    manifest = build_full_backfill_manifest(
        env=ENV,
        profile=_profile(),
        now=NOW,
        symbols=("ES",),
        start_date=date(2018, 1, 1),
        end_date=date(2018, 12, 31),
    )

    assert manifest.chunk_count == 4
    refs = tuple(spec.contract_ref for spec in manifest.request_specs)
    assert refs == (
        "fcr_ibkr_es_fut_201803",
        "fcr_ibkr_es_fut_201806",
        "fcr_ibkr_es_fut_201809",
        "fcr_ibkr_es_fut_201812",
    )
    codes = tuple(spec.chunk_policy["contract_month_code"] for spec in manifest.request_specs)
    assert codes == ("H", "M", "U", "Z")
    for spec in manifest.request_specs:
        assert spec.sec_type == "FUT"
        assert spec.end_ts.tzinfo is not None
        assert spec.end_datetime_policy == "explicit_dated_fut_end_ts"
        assert spec.contract_ref[-6:].isdigit()
        assert spec.contract_ref[-6:] in spec.contract_ref
    assert manifest.expected_coverage["quality_claim"] is False
    assert manifest.expected_coverage["real_coverage_claim"] is False


def test_manifest_json_round_trips(tmp_path: Path) -> None:
    manifest = build_full_backfill_manifest(
        env=ENV,
        profile=_profile(),
        now=NOW,
        symbols=("ES", "NQ"),
        start_date=date(2018, 1, 1),
        end_date=date(2019, 12, 31),
    )

    path = write_manifest_json(manifest, tmp_path / "full.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    loaded = HistoricalRequestManifest.from_mapping(payload)

    assert loaded == manifest
    assert loaded.chunk_count == 16
