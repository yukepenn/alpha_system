from __future__ import annotations

import json
from typing import Any

from alpha_system.cli import scaleout as scaleout_cli
from alpha_system.cli.main import main
from alpha_system.features.scaleout import ScaleoutTarget


def test_scaleout_feature_pack_cli_builds_targeting_request(
    monkeypatch: Any,
    capsys: Any,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr(scaleout_cli, "load_scaleout_config", lambda _path: object())

    def fake_run_scaleout(_config: object, **kwargs: Any) -> _Summary:
        captured.update(kwargs)
        return _Summary(
            target=kwargs["target"],
            execute=bool(kwargs["execute"]),
            engine=kwargs["engine"],
        )

    monkeypatch.setattr(scaleout_cli, "run_scaleout", fake_run_scaleout)

    rc = main(
        [
            "scaleout",
            "feature-pack",
            "--dry-run",
            "--family",
            "base_ohlcv",
            "--feature-id",
            "returns,log_returns",
            "--feature-group",
            "price_change",
            "--label-id",
            "fixed_horizon_return_1m",
            "--label-group",
            "fixed_horizon",
            "--symbols",
            "es,nq",
            "--years",
            "2024,2025",
            "--dataset-version-ids",
            "dsv_one,dsv_two",
            "--engine",
            "reference",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    target = captured["target"]
    assert rc == 0
    assert isinstance(target, ScaleoutTarget)
    assert target.family == "base_ohlcv"
    assert target.feature_ids == ("returns", "log_returns")
    assert target.feature_groups == ("price_change",)
    assert target.label_ids == ("fixed_horizon_return_1m",)
    assert target.label_groups == ("fixed_horizon",)
    assert target.symbols == ("ES", "NQ")
    assert target.years == (2024, 2025)
    assert target.dataset_version_ids == ("dsv_one", "dsv_two")
    assert captured["engine"] == "reference"
    assert captured["execute"] is False
    assert payload["target"]["feature_ids"] == ["returns", "log_returns"]
    assert payload["engine"] == "reference"


def test_scaleout_feature_pack_cli_rejects_dry_run_execute_combo(capsys: Any) -> None:
    rc = main(["scaleout", "feature-pack", "--dry-run", "--execute"])

    captured = capsys.readouterr()
    assert rc == 2
    assert "--dry-run and --execute cannot be combined" in captured.err


class _Summary:
    def __init__(self, *, target: ScaleoutTarget, execute: bool, engine: str) -> None:
        self.target = target
        self.execute = execute
        self.engine = engine
        self.failed_count = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "campaign_id": "TEST",
            "phase_id": "FCFP-P11",
            "family": self.target.family or "base_ohlcv",
            "engine": self.engine,
            "target": self.target.to_dict(),
            "rollout": "bounded-then-full",
            "dry_run": not self.execute,
            "bounded_year": 2024,
            "accepted_unit_count": 0,
            "bounded_unit_count": 0,
            "dry_run_estimate": None,
            "planned_count": 0,
            "completed_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "records": [],
        }
