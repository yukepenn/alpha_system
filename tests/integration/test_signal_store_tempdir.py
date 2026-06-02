from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from alpha_system.signals.store import LocalSignalStore


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_signal_store_writes_only_to_temp_local_path(tmp_path: Path) -> None:
    store_root = tmp_path / "signals"
    store = LocalSignalStore(store_root, repo_root=REPO_ROOT)

    result = store.write_signals("threshold_signals", [_signal_record()])
    loaded = store.read_signals("threshold_signals")

    assert result.record_count == 1
    assert result.signals_path.exists()
    assert result.manifest_path.exists()
    assert loaded[0].strategy_id == "threshold_strategy"
    assert not _is_relative_to(result.signals_path.resolve(), REPO_ROOT)
    assert not _is_relative_to(result.manifest_path.resolve(), REPO_ROOT)


def _signal_record() -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    return {
        "signal_id": "sig-store",
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "signal_type": "entry",
        "direction": "long",
        "score": 0.8,
        "confidence": 0.7,
        "desired_exposure": 0.25,
        "strategy_id": "threshold_strategy",
        "strategy_version": "v1",
        "factor_versions": {"fixture_close_delta": "v1"},
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
    }


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
