"""Value-free damaged FeaturePack provenance and restore-proof audit.

The tool reads the feature registry through a SQLite read-only URI and inspects
only Parquet metadata columns plus sidecar manifests. It never edits registry
rows, pack values, locks, or run state.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FAMILY_CONFIGS: dict[str, tuple[str, str]] = {
    "session_calendar_maintenance": (
        "configs/features/scaleout/session_calendar_maintenance.json",
        "configs/features/scaleout/repair/session_calendar_maintenance_union_restore.json",
    ),
    "regime_volatility_compression": (
        "configs/features/scaleout/regime_volatility_compression.json",
        "configs/features/scaleout/repair/regime_volatility_compression_union_restore.json",
    ),
    "bbo_tradability_top_book": (
        "configs/features/scaleout/bbo_tradability_top_book.json",
        "configs/features/scaleout/repair/bbo_tradability_top_book_union_restore.json",
    ),
}


PROVENANCE_FIELDS = [
    "family",
    "partition_id",
    "feature_id",
    "feature_version_id",
    "feature_request_id",
    "materialization_plan_id",
    "dataset_version_id",
    "lifecycle_state",
    "registered_at",
    "producer_campaign",
    "producer_phase",
    "producer_engine_id",
    "value_schema_version",
    "registry_value_content_hash",
    "parquet_path",
    "current_manifest_hash",
    "current_disk_feature_count",
    "current_disk_row_count",
    "status_at_audit",
    "source_config_path",
    "repair_config_path",
    "command_template",
]


PROOF_FIELDS = [
    "family",
    "partition_id",
    "feature_id",
    "feature_version_id",
    "baseline_registry_value_content_hash",
    "current_registry_value_content_hash",
    "current_manifest_hash",
    "present_on_disk",
    "baseline_hash_identity",
    "current_registry_hash_identity",
    "current_disk_feature_count",
    "current_disk_row_count",
    "status_at_audit",
    "parquet_path",
]


@dataclass(frozen=True)
class RegistryRow:
    family: str
    partition_id: str
    feature_id: str
    feature_version_id: str
    feature_request_id: str
    materialization_plan_id: str
    dataset_version_id: str
    lifecycle_state: str
    registered_at: str
    producer_campaign: str
    producer_phase: str
    producer_engine_id: str
    value_schema_version: str
    registry_value_content_hash: str
    parquet_path: str


@dataclass(frozen=True)
class DiskInfo:
    exists: bool
    feature_version_ids: frozenset[str]
    manifest_hash: str
    row_count: int
    error: str = ""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    registry_path = Path(args.alpha_data_root).expanduser() / "registry" / "features.sqlite"
    families = tuple(args.family or FAMILY_CONFIGS)
    rows = _load_registry_rows(
        registry_path,
        families=families,
        include_deprecated=args.include_deprecated,
        partition=args.partition,
    )
    disk_cache: dict[str, DiskInfo] = {}
    statuses = [_row_status(row, disk_cache) for row in rows]
    stale_rows = [item for item in statuses if item[1] == "stale"]

    if args.provenance_out:
        _write_provenance(args.provenance_out, statuses)
    if args.proof_out:
        proof_rows = statuses
        baseline_hashes: dict[str, str] = {}
        if args.baseline_provenance:
            baseline_hashes = _read_baseline_hashes(
                args.baseline_provenance,
                args.partition,
                families,
            )
            baseline_ids = set(baseline_hashes)
            proof_rows = [item for item in statuses if item[0].feature_version_id in baseline_ids]
        _write_proof(args.proof_out, proof_rows, baseline_hashes=baseline_hashes)
    if args.summary_out:
        _write_summary(args.summary_out, statuses)

    _print_summary(statuses)
    if args.require_stale_count is not None and len(stale_rows) != args.require_stale_count:
        print(
            "pack_restore_audit error: expected "
            f"{args.require_stale_count} stale rows, found {len(stale_rows)}",
            file=sys.stderr,
        )
        return 2
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alpha-data-root",
        default="/home/yuke_zhang/alpha_data/alpha_system",
        help="Local alpha data root; registry is read through file:...?mode=ro.",
    )
    parser.add_argument(
        "--family",
        action="append",
        choices=tuple(FAMILY_CONFIGS),
        help="Family to audit; repeatable. Defaults to the three damaged families.",
    )
    parser.add_argument("--partition", help="Optional partition_id filter.")
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        help="Include deprecated rows. Default audits active REGISTERED rows only.",
    )
    parser.add_argument("--provenance-out", type=Path)
    parser.add_argument("--proof-out", type=Path)
    parser.add_argument(
        "--baseline-provenance",
        type=Path,
        help="CSV or Markdown table from --provenance-out; proof output is limited to those fvers.",
    )
    parser.add_argument("--summary-out", type=Path)
    parser.add_argument("--require-stale-count", type=int)
    return parser.parse_args(argv)


def _load_registry_rows(
    registry_path: Path,
    *,
    families: tuple[str, ...],
    include_deprecated: bool,
    partition: str | None,
) -> list[RegistryRow]:
    family_clauses = []
    params: list[str] = []
    for family in families:
        family_clauses.append("(parquet_path LIKE ? OR materialization_output_path LIKE ?)")
        params.extend((f"%/{family}/%", f"%/{family}/%"))
    where = " OR ".join(family_clauses)
    lifecycle = "" if include_deprecated else "AND lifecycle_state = 'REGISTERED'"
    partition_clause = ""
    if partition:
        partition_clause = "AND partition_id = ?"
        params.append(partition)
    query = f"""
        SELECT
            feature_version_id,
            feature_id,
            feature_request_id,
            lifecycle_state,
            materialization_plan_id,
            dataset_version_id,
            partition_id,
            parquet_path,
            value_content_hash,
            value_schema_version,
            producer_engine_id,
            registered_at,
            metadata_json
        FROM feature_registry_records
        WHERE ({where}) {lifecycle} {partition_clause}
        ORDER BY partition_id, feature_id, registered_at, feature_version_id
    """
    connection = sqlite3.connect(f"file:{registry_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        loaded = []
        for row in connection.execute(query, params):
            loaded.append(_registry_row_from_sql(row))
        return loaded
    finally:
        connection.close()


def _registry_row_from_sql(row: sqlite3.Row) -> RegistryRow:
    metadata = json.loads(row["metadata_json"])
    registry_metadata = _mapping(metadata.get("registry_metadata"))
    materialization = _mapping(metadata.get("materialization"))
    family = _text(registry_metadata.get("family"), "registry_metadata.family")
    return RegistryRow(
        family=family,
        partition_id=_text(row["partition_id"], "partition_id"),
        feature_id=_text(row["feature_id"], "feature_id"),
        feature_version_id=_text(row["feature_version_id"], "feature_version_id"),
        feature_request_id=_text(row["feature_request_id"], "feature_request_id"),
        materialization_plan_id=_text(row["materialization_plan_id"], "materialization_plan_id"),
        dataset_version_id=_text(row["dataset_version_id"], "dataset_version_id"),
        lifecycle_state=_text(row["lifecycle_state"], "lifecycle_state"),
        registered_at=_text(row["registered_at"], "registered_at"),
        producer_campaign=_text(registry_metadata.get("campaign_id"), "campaign_id"),
        producer_phase=_text(registry_metadata.get("phase_id"), "phase_id"),
        producer_engine_id=_text(
            row["producer_engine_id"] or materialization.get("producer_engine_id"),
            "producer_engine_id",
        ),
        value_schema_version=_text(row["value_schema_version"], "value_schema_version"),
        registry_value_content_hash=_text(row["value_content_hash"], "value_content_hash"),
        parquet_path=_text(row["parquet_path"], "parquet_path"),
    )


def _row_status(
    row: RegistryRow,
    disk_cache: dict[str, DiskInfo],
) -> tuple[RegistryRow, str, DiskInfo]:
    disk = disk_cache.get(row.parquet_path)
    if disk is None:
        disk = _disk_info(Path(row.parquet_path))
        disk_cache[row.parquet_path] = disk
    if not disk.exists:
        return row, "missing_path", disk
    if disk.error:
        return row, "unreadable_path", disk
    if row.feature_version_id not in disk.feature_version_ids:
        return row, "stale", disk
    if row.registry_value_content_hash != disk.manifest_hash:
        return row, "hash_mismatch", disk
    return row, "hash_identity", disk


def _disk_info(path: Path) -> DiskInfo:
    if not path.exists():
        return DiskInfo(False, frozenset(), "", 0)
    try:
        import polars as pl

        frame = pl.read_parquet(path.as_posix(), columns=["feature_version_id"])
        feature_version_ids = frozenset(str(value) for value in frame["feature_version_id"].unique())
        manifest_hash = _read_manifest_hash(path)
        return DiskInfo(True, feature_version_ids, manifest_hash, frame.height)
    except Exception as exc:  # noqa: BLE001 - audit must report unreadable packs.
        return DiskInfo(True, frozenset(), "", 0, error=f"{type(exc).__name__}: {exc}")


def _read_manifest_hash(path: Path) -> str:
    manifest_path = Path(str(path.expanduser().resolve(strict=False)) + ".manifest.json")
    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return _text(payload.get("content_hash"), "manifest.content_hash")


def _write_provenance(path: Path, rows: list[tuple[RegistryRow, str, DiskInfo]]) -> None:
    output_rows = []
    for row, status, disk in rows:
        if status != "stale":
            continue
        source_config, repair_config = FAMILY_CONFIGS[row.family]
        output_rows.append(
            {
                "family": row.family,
                "partition_id": row.partition_id,
                "feature_id": row.feature_id,
                "feature_version_id": row.feature_version_id,
                "feature_request_id": row.feature_request_id,
                "materialization_plan_id": row.materialization_plan_id,
                "dataset_version_id": row.dataset_version_id,
                "lifecycle_state": row.lifecycle_state,
                "registered_at": row.registered_at,
                "producer_campaign": row.producer_campaign,
                "producer_phase": row.producer_phase,
                "producer_engine_id": row.producer_engine_id,
                "value_schema_version": row.value_schema_version,
                "registry_value_content_hash": row.registry_value_content_hash,
                "parquet_path": row.parquet_path,
                "current_manifest_hash": disk.manifest_hash,
                "current_disk_feature_count": len(disk.feature_version_ids),
                "current_disk_row_count": disk.row_count,
                "status_at_audit": status,
                "source_config_path": source_config,
                "repair_config_path": repair_config,
                "command_template": _command_template(repair_config),
            }
        )
    _write_rows(path, PROVENANCE_FIELDS, output_rows)


def _write_proof(
    path: Path,
    rows: list[tuple[RegistryRow, str, DiskInfo]],
    *,
    baseline_hashes: dict[str, str],
) -> None:
    output_rows = []
    for row, status, disk in rows:
        baseline_hash = baseline_hashes.get(
            row.feature_version_id,
            row.registry_value_content_hash,
        )
        present = row.feature_version_id in disk.feature_version_ids
        output_rows.append(
            {
                "family": row.family,
                "partition_id": row.partition_id,
                "feature_id": row.feature_id,
                "feature_version_id": row.feature_version_id,
                "baseline_registry_value_content_hash": baseline_hash,
                "current_registry_value_content_hash": row.registry_value_content_hash,
                "current_manifest_hash": disk.manifest_hash,
                "present_on_disk": str(present).lower(),
                "baseline_hash_identity": str(
                    present and baseline_hash == disk.manifest_hash
                ).lower(),
                "current_registry_hash_identity": str(status == "hash_identity").lower(),
                "current_disk_feature_count": len(disk.feature_version_ids),
                "current_disk_row_count": disk.row_count,
                "status_at_audit": status,
                "parquet_path": row.parquet_path,
            }
        )
    _write_rows(path, PROOF_FIELDS, output_rows)


def _write_summary(path: Path, rows: list[tuple[RegistryRow, str, DiskInfo]]) -> None:
    _ensure_parent(path)
    lines = [
        "# Damaged Pack Audit Summary",
        "",
        "| Family | Rows | Hash identity | Stale | Hash mismatch | Missing path | Unreadable |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    by_family: dict[str, list[tuple[RegistryRow, str, DiskInfo]]] = {}
    for item in rows:
        by_family.setdefault(item[0].family, []).append(item)
    for family in sorted(by_family):
        statuses = [status for _, status, _ in by_family[family]]
        lines.append(
            "| {family} | {rows} | {identity} | {stale} | {mismatch} | {missing} | {unreadable} |".format(
                family=family,
                rows=len(statuses),
                identity=statuses.count("hash_identity"),
                stale=statuses.count("stale"),
                mismatch=statuses.count("hash_mismatch"),
                missing=statuses.count("missing_path"),
                unreadable=statuses.count("unreadable_path"),
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_summary(rows: list[tuple[RegistryRow, str, DiskInfo]]) -> None:
    by_family: dict[str, list[str]] = {}
    for row, status, _ in rows:
        by_family.setdefault(row.family, []).append(status)
    for family in sorted(by_family):
        statuses = by_family[family]
        print(
            f"{family}: rows={len(statuses)} "
            f"hash_identity={statuses.count('hash_identity')} "
            f"stale={statuses.count('stale')} "
            f"hash_mismatch={statuses.count('hash_mismatch')} "
            f"missing_path={statuses.count('missing_path')} "
            f"unreadable={statuses.count('unreadable_path')}"
        )


def _read_baseline_hashes(
    path: Path,
    partition: str | None,
    families: tuple[str, ...],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in _read_rows(path):
        if partition and row.get("partition_id") != partition:
            continue
        if row.get("family") not in families:
            continue
        if row.get("status_at_audit") != "stale":
            continue
        feature_version_id = _text(row.get("feature_version_id"), "feature_version_id")
        values[feature_version_id] = _text(
            row.get("registry_value_content_hash"),
            "registry_value_content_hash",
        )
    return values


def _write_rows(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    _ensure_parent(path)
    if path.suffix.lower() == ".md":
        _write_markdown_table(path, fields, rows)
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown_table(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(_markdown_cell(row.get(field, "")) for field in fields)
            + " |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".md":
        return _read_markdown_table(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_markdown_table(path: Path) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    table_lines = [line for line in table_lines if line.startswith("|")]
    if len(table_lines) < 2:
        raise ValueError(f"Markdown table has no header: {path}")
    header = _split_markdown_row(table_lines[0])
    if not _is_markdown_separator(_split_markdown_row(table_lines[1])):
        raise ValueError(f"Markdown table has no separator row: {path}")
    rows = []
    for line in table_lines[2:]:
        cells = _split_markdown_row(line)
        if len(cells) != len(header):
            raise ValueError(f"Markdown table row has {len(cells)} cells, expected {len(header)}")
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def _split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells: list[str] = []
    current = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def _is_markdown_separator(cells: list[str]) -> bool:
    for cell in cells:
        marker = cell.replace(":", "").replace("-", "").strip()
        if marker:
            return False
    return True


def _markdown_cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _command_template(config_path: str) -> str:
    return (
        "ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src "
        "python -m alpha_system.cli scaleout feature-pack "
        f"--config {config_path} --rollout full-window --execute --force-recompute "
        "--symbols <SYMBOL> --years <YEAR> "
        "--alpha-data-root \"$ALPHA_DATA_ROOT\" "
        "--dataset-registry \"$ALPHA_DATA_ROOT/registry/datasets.sqlite\" --json"
    )


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
