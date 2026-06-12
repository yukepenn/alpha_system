from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from alpha_system.governance.canaries import (
    REGISTRY_EVENT_TS_GRID_ALLOWLIST,
    RegistrationEventRange,
    run_registry_event_ts_grid_canary,
    scan_registry_event_ts_grid,
)


def test_registry_event_ts_grid_canary_allows_visible_known_debt() -> None:
    result = run_registry_event_ts_grid_canary()

    assert result.passed
    assert result.skipped is False
    assert result.scanned_count == 3
    assert result.violations == ()
    assert {issue.allowlist_reason_code for issue in result.allowed_debt} == {
        "BBO_PENDING_RE_MATERIALIZATION",
        "COST_SPREAD_LABEL_MIRROR_DEFECT",
    }
    assert any("family=bbo_tradability" in line for line in result.detail_lines())
    assert any("family=cost_adjusted" in line for line in result.detail_lines())


def test_registry_event_ts_grid_canary_fails_without_grandfather_allowlist() -> None:
    result = run_registry_event_ts_grid_canary(allowlist=())

    assert result.passed is False
    assert result.allowed_debt == ()
    assert {issue.family for issue in result.violations} == {
        "bbo_tradability",
        "cost_adjusted",
    }


def test_registry_event_ts_grid_canary_names_unallowlisted_family_and_pack() -> None:
    result = scan_registry_event_ts_grid(
        (
            RegistrationEventRange(
                registration_kind="feature",
                family="base_ohlcv",
                pack_id="feature_set_off_grid_unknown",
                registration_id="base_ohlcv_returns",
                version_id="fver_unknown_off_grid",
                first_event_ts=datetime(2024, 1, 2, 14, 31, 0, 1, tzinfo=UTC),
                last_event_ts=datetime(2024, 1, 2, 14, 32, tzinfo=UTC),
            ),
        ),
        allowlist=REGISTRY_EVENT_TS_GRID_ALLOWLIST,
    )

    assert result.passed is False
    assert len(result.violations) == 1
    assert "family=base_ohlcv pack=feature_set_off_grid_unknown" in result.violations[0].to_line(
        "VIOLATION"
    )


def test_registry_event_ts_grid_live_mode_skips_loudly_without_registry() -> None:
    result = run_registry_event_ts_grid_canary(mode="live", env={})

    assert result.passed
    assert result.skipped
    assert "ALPHA_DATA_ROOT is unset" in result.summary_line()


def test_registry_event_ts_grid_live_mode_scans_sqlite_rows(tmp_path: Path) -> None:
    feature_registry = tmp_path / "features.sqlite"
    label_registry = tmp_path / "labels.sqlite"
    _write_feature_registry(feature_registry)
    _write_label_registry(label_registry)

    result = run_registry_event_ts_grid_canary(
        mode="live",
        feature_registry_path=feature_registry,
        label_registry_path=label_registry,
    )

    assert result.passed
    assert result.scanned_count == 2
    assert {issue.allowlist_reason_code for issue in result.allowed_debt} == {
        "BBO_PENDING_RE_MATERIALIZATION",
        "COST_SPREAD_LABEL_MIRROR_DEFECT",
    }


def _write_feature_registry(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE feature_registry_records (
                feature_version_id TEXT NOT NULL,
                feature_id TEXT NOT NULL,
                lifecycle_state TEXT NOT NULL,
                first_event_ts TEXT NOT NULL,
                last_event_ts TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO feature_registry_records
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "fver_live_bbo_mid",
                "bbo_tradability_mid",
                "REGISTERED",
                "2024-01-02T14:31:00.800000+00:00",
                "2024-01-02T14:32:00.800000+00:00",
                json.dumps(
                    {
                        "feature_spec": {"family": "bbo_tradability"},
                        "feature_set_membership": {"feature_set_id": "feature_set_live_bbo"},
                    }
                ),
            ),
        )


def _write_label_registry(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE label_registry_records (
                label_version_id TEXT NOT NULL,
                label_id TEXT NOT NULL,
                lifecycle_state TEXT NOT NULL,
                first_event_ts TEXT NOT NULL,
                last_event_ts TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO label_registry_records
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "lver_live_cost_adjusted",
                "spread_adjusted_fwd_ret",
                "REGISTERED",
                "2024-01-02T14:31:00.250000+00:00",
                "2024-01-02T14:32:00.250000+00:00",
                json.dumps(
                    {
                        "label_contract": {"family": "cost_adjusted"},
                        "registry_metadata": {"label_pack_id": "label_pack_live_cost_adjusted"},
                    }
                ),
            ),
        )
