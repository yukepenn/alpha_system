from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from alpha_system.signals.io import (
    SignalIOError,
    default_signal_store_root,
    resolve_signal_output_dir,
    write_signal_records,
)
from alpha_system.signals.store import (
    LocalSignalStore,
    SignalStoreError,
    is_local_only_signal_store_path,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_signal_store_default_paths_are_local_only() -> None:
    default_root = default_signal_store_root()

    assert default_root.as_posix().startswith("/tmp/alpha_system/signals")
    assert not _is_relative_to(default_root, REPO_ROOT)
    assert resolve_signal_output_dir(default_root) == default_root


def test_signal_store_refuses_committed_or_forbidden_locations(tmp_path: Path) -> None:
    repo_signal_path = REPO_ROOT / "data" / "signals"

    assert is_local_only_signal_store_path(repo_signal_path, repo_root=REPO_ROOT) is False
    with pytest.raises(SignalIOError, match="outside the repo"):
        resolve_signal_output_dir(repo_signal_path)
    with pytest.raises(SignalStoreError, match="local-only"):
        LocalSignalStore(repo_signal_path, repo_root=REPO_ROOT)
    with pytest.raises(SignalIOError, match=".jsonl"):
        write_signal_records(
            [_signal_record()],
            output_dir=tmp_path,
            file_name="signals.parquet",
        )


def _signal_record() -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    return {
        "signal_id": "sig-policy",
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
