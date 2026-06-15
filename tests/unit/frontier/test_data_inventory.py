"""Unit tests for the canonical on-disk materialized data inventory reader.

These tests build a tiny synthetic on-disk store (a temp dir with a couple of
``values.parquet`` stubs) and a synthetic acceptance-lock config tree, then
assert coverage parsing and that the config-vs-disk disagreement guard fires
when the governance config and the disk diverge.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.frontier import data_inventory as di


def _write_parquet_stub(root: Path, layer: str, namespace: str, dsv: str, partition: str) -> None:
    """Create a non-empty ``values.parquet`` stub at the materialized layout path."""

    leaf = root / layer / "materialized" / namespace / dsv / partition / "values.parquet"
    leaf.parent.mkdir(parents=True, exist_ok=True)
    # Real parquet content is irrelevant to the inventory walk; a positive byte
    # size is the non-empty proxy the reader uses.
    leaf.write_bytes(b"PAR1-stub")


def _write_config(
    repo_root: Path,
    relpath: str,
    *,
    states: dict[str, str],
    header_counts: dict[str, int] | None,
) -> None:
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    schemas: dict[str, dict[str, dict[str, str]]] = {"ohlcv_1m": {}}
    for index, (dsv, state) in enumerate(states.items()):
        schemas["ohlcv_1m"][str(2019 + index)] = {
            "dataset_version_id": dsv,
            "committed_summary_state": state,
        }
    payload: dict[str, object] = {
        "schema": "test.dataset_version_inventory.v1",
        "schemas": schemas,
    }
    if header_counts is not None:
        payload["selection_contract"] = {
            "current_committed_summary_counts": header_counts
        }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build(data_root: Path, repo_root: Path, **kwargs: object) -> di.DataInventory:
    return di.build_inventory(
        data_root=str(data_root),
        repo_root=str(repo_root),
        **kwargs,  # type: ignore[arg-type]
    )


def test_resolve_data_root_order(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit"
    assert di.resolve_data_root(explicit, env={}) == explicit
    assert di.resolve_data_root(None, env={"ALPHA_DATA_ROOT": "/env/root"}) == Path("/env/root")
    assert di.resolve_data_root(None, env={}, frontier_data_root="/fy/root") == Path("/fy/root")
    assert di.resolve_data_root(None, env={}) == di.DEFAULT_ALPHA_DATA_ROOT.expanduser()


def test_walks_disk_and_parses_coverage(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(
        data_root,
        "features",
        "base_ohlcv/feature_set_base/v1_es_2024",
        "dsv_ohlcv_aaa",
        "ES_2024_full_year",
    )
    _write_parquet_stub(
        data_root,
        "features",
        "base_ohlcv/feature_set_base/v1_nq_2025",
        "dsv_ohlcv_bbb",
        "NQ_2025_full_year",
    )
    _write_parquet_stub(
        data_root,
        "labels",
        "path/lset_xyz",
        "dsv_ohlcv_aaa",
        "RTY_2025_5m",
    )

    inventory = _build(data_root, repo_root, check_config=False)
    cov = inventory.coverage_summary()

    assert inventory.materialized_root_exists is True
    assert cov["total_partitions"] == 3
    assert cov["instruments"] == ["ES", "NQ", "RTY"]
    assert cov["years"] == [2024, 2025]
    assert cov["partitions_by_layer"] == {"features": 2, "labels": 1}
    # Trailing segments parsed: dsv id and partition are correctly split off.
    dsvs = {e.dataset_version_id for e in inventory.entries}
    assert dsvs == {"dsv_ohlcv_aaa", "dsv_ohlcv_bbb"}
    horizons = {e.horizon for e in inventory.entries}
    assert horizons == {"full_year", "5m"}


def test_empty_parquet_excluded_by_default(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(data_root, "features", "ns/set", "dsv_a", "ES_2024_full_year")
    # Zero-byte parquet should be treated as absent under nonempty_only.
    empty = data_root / "features" / "materialized" / "ns/set" / "dsv_b" / "ES_2025_full_year"
    empty.mkdir(parents=True, exist_ok=True)
    (empty / "values.parquet").write_bytes(b"")

    default = _build(data_root, repo_root, check_config=False)
    assert default.coverage_summary()["total_partitions"] == 1

    with_empty = _build(data_root, repo_root, check_config=False, nonempty_only=False)
    assert with_empty.coverage_summary()["total_partitions"] == 2


def test_disagreement_fires_when_config_blocked_but_disk_present(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(data_root, "labels", "path/lset_xyz", "dsv_blocked", "ES_2024_5m")
    # Config marks the materialized dsv BLOCKED -> the core second-truth case.
    _write_config(
        repo_root,
        "configs/labels/scaleout/dataset_version_inventory.json",
        states={"dsv_blocked": "BLOCKED"},
        header_counts={"BLOCKED": 1},
    )

    inventory = _build(data_root, repo_root)
    kinds = {d.kind for d in inventory.disagreements}
    assert "config_blocked_but_disk_present" in kinds
    flagged = [d for d in inventory.disagreements if d.kind == "config_blocked_but_disk_present"]
    assert flagged[0].dataset_version_id == "dsv_blocked"
    assert flagged[0].config_state == "BLOCKED"


def test_disagreement_fires_when_disk_present_but_config_missing(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(data_root, "features", "ns/set", "dsv_unlisted", "NQ_2026_full_year")
    _write_config(
        repo_root,
        "configs/features/scaleout/dataset_version_inventory.json",
        states={"dsv_other": "ACCEPTED"},
        header_counts={"ACCEPTED": 1},
    )

    inventory = _build(data_root, repo_root)
    missing = [d for d in inventory.disagreements if d.kind == "disk_present_config_missing"]
    assert len(missing) == 1
    assert missing[0].dataset_version_id == "dsv_unlisted"


def test_header_stale_disagreement_fires(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    # Header claims BLOCKED:27 but the per-record states are all ACCEPTED.
    _write_config(
        repo_root,
        "configs/features/scaleout/dataset_version_inventory.json",
        states={"dsv_a": "ACCEPTED", "dsv_b": "ACCEPTED"},
        header_counts={"BLOCKED": 27, "ACCEPTED": 0},
    )

    inventory = _build(data_root, repo_root)
    stale = [d for d in inventory.disagreements if d.kind == "config_header_stale"]
    assert stale, "stale header (counts vs own records) must be flagged"
    assert any("BLOCKED" in d.detail for d in stale)


def test_no_disagreement_when_config_matches_disk(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(data_root, "features", "ns/set", "dsv_ok", "ES_2024_full_year")
    _write_config(
        repo_root,
        "configs/features/scaleout/dataset_version_inventory.json",
        states={"dsv_ok": "ACCEPTED"},
        header_counts={"ACCEPTED": 1},
    )

    inventory = _build(data_root, repo_root)
    assert inventory.disagreements == ()


def test_missing_materialized_root_is_clean(tmp_path: Path) -> None:
    inventory = _build(tmp_path / "nope", tmp_path / "repo", check_config=False)
    assert inventory.materialized_root_exists is False
    assert inventory.coverage_summary()["total_partitions"] == 0


def test_render_summary_is_deterministic(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    _write_parquet_stub(data_root, "features", "ns/set", "dsv_a", "ES_2024_full_year")
    inventory = _build(data_root, repo_root, check_config=False)
    first = di.render_summary(inventory)
    second = di.render_summary(inventory)
    assert first == second
    assert "ON-DISK MATERIALIZED DATA INVENTORY" in first
