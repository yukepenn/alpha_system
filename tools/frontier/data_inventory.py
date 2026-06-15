"""Canonical on-disk materialized data inventory (the data-existence truth).

Single authoritative reader for "what materialized feature/label data actually
exists on disk", walking the resolved ``ALPHA_DATA_ROOT`` materialized store and
(optionally) cross-checking the governance acceptance-lock config inventories.

Anti-second-truth contract
---------------------------
Two layers can answer "what data is available" and they answer *different*
questions:

* ``configs/{features,labels}/scaleout/dataset_version_inventory.json`` records
  the **governance acceptance-lock** bookkeeping state (ACCEPTED / BLOCKED). It
  is intent + gate state, not disk presence. It can say ``BLOCKED`` while the
  values were already materialized (exactly the misread that motivated this
  tool: config ``BLOCKED:27`` vs disk full of ES/NQ/RTY values.parquet).
* The on-disk materialized store (``<root>/{features,labels}/materialized/...``)
  records what was **actually produced**. This module reads that, and that is
  the data-existence source of truth.

This reader is read-only and deterministic. It never recomputes, never writes,
and never touches the network. The DISAGREEMENT section flags any place where
the acceptance-lock config and disk presence diverge so the misread can never
recur silently.

On-disk layout (variable namespace depth, fixed trailing segments)::

    <root>/<layer>/materialized/<namespace...>/<dsv_id>/<partition_id>/values.parquet

where ``<layer>`` is ``features`` or ``labels``; ``<namespace...>`` is one or
more set/family directories (features carry a feature_set_version dir, labels do
not, so the depth varies); and the final three segments are always
``<dataset_version_id>/<partition_id>/values.parquet``. ``partition_id`` is
conventionally ``<INSTRUMENT>_<YEAR>_<horizon>`` (e.g. ``ES_2024_full_year``,
``RTY_2025_5m``).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Conventional repo default when neither an explicit root nor the env var is set.
# Mirrors frontier.yaml's documented resolution order and
# tools/frontier/runtime_paths.DEFAULT_ALPHA_SYSTEM_ROOT.
DEFAULT_ALPHA_DATA_ROOT = Path("~/alpha_data/alpha_system")

# Acceptance-lock config inventories (governance bookkeeping, NOT disk truth).
_CONFIG_INVENTORY_RELPATHS = (
    Path("configs/features/scaleout/dataset_version_inventory.json"),
    Path("configs/labels/scaleout/dataset_version_inventory.json"),
)

_ELIGIBLE_ACCEPTANCE_STATES = frozenset({"ACCEPTED", "ACCEPTED_WITH_WARNINGS"})

# partition_id convention: <INSTRUMENT>_<YEAR>_<horizon...>
_PARTITION_RE = re.compile(r"^(?P<instrument>[A-Za-z0-9]+)_(?P<year>\d{4})_(?P<horizon>.+)$")


def resolve_data_root(
    explicit: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    frontier_data_root: str | Path | None = None,
) -> Path:
    """Resolve the data root using the documented frontier.yaml order.

    Order: explicit argument, then ``ALPHA_DATA_ROOT`` env var, then the
    ``frontier.yaml`` ``data_root`` value (when provided), then the repo default
    ``~/alpha_data/alpha_system``. Never hardcodes an absolute user path.
    """

    source = os.environ if env is None else env
    if explicit is not None:
        raw: str | Path = explicit
    elif source.get("ALPHA_DATA_ROOT"):
        raw = source["ALPHA_DATA_ROOT"]
    elif frontier_data_root:
        raw = frontier_data_root
    else:
        raw = DEFAULT_ALPHA_DATA_ROOT
    return Path(raw).expanduser()


@dataclass(frozen=True, slots=True)
class PartitionEntry:
    """One materialized partition that is present on disk with a values file."""

    layer: str  # "features" | "labels"
    materialized_set: str  # top namespace dir under <layer>/materialized
    namespace: str  # full namespace path relative to <layer>/materialized
    set_id: str  # the set/family/factor dir directly above the dsv dir
    dataset_version_id: str
    partition_id: str
    instrument: str | None
    year: int | None
    horizon: str | None
    parquet_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "materialized_set": self.materialized_set,
            "namespace": self.namespace,
            "set_id": self.set_id,
            "dataset_version_id": self.dataset_version_id,
            "partition_id": self.partition_id,
            "instrument": self.instrument,
            "year": self.year,
            "horizon": self.horizon,
            "parquet_path": self.parquet_path,
        }


@dataclass(frozen=True, slots=True)
class Disagreement:
    """One config-vs-disk acceptance-lock divergence."""

    kind: str
    dataset_version_id: str
    detail: str
    config_state: str | None = None
    config_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "dataset_version_id": self.dataset_version_id,
            "detail": self.detail,
            "config_state": self.config_state,
            "config_file": self.config_file,
        }


@dataclass(frozen=True, slots=True)
class DataInventory:
    """Canonical on-disk materialized inventory result."""

    data_root: str
    materialized_root_exists: bool
    entries: tuple[PartitionEntry, ...]
    disagreements: tuple[Disagreement, ...]
    config_inventories_read: tuple[str, ...] = field(default_factory=tuple)
    nonempty_only: bool = True

    # --- coverage summaries -------------------------------------------------

    def coverage_summary(self) -> dict[str, Any]:
        """Compact instruments x years x families coverage with counts."""

        instruments: set[str] = set()
        years: set[int] = set()
        layers: Counter[str] = Counter()
        sets_by_layer: dict[str, set[str]] = defaultdict(set)
        per_set: Counter[tuple[str, str]] = Counter()
        instr_years: dict[str, set[int]] = defaultdict(set)

        for entry in self.entries:
            layers[entry.layer] += 1
            sets_by_layer[entry.layer].add(entry.materialized_set)
            per_set[(entry.layer, entry.materialized_set)] += 1
            if entry.instrument is not None:
                instruments.add(entry.instrument)
                if entry.year is not None:
                    instr_years[entry.instrument].add(entry.year)
            if entry.year is not None:
                years.add(entry.year)

        return {
            "total_partitions": len(self.entries),
            "instruments": sorted(instruments),
            "years": sorted(years),
            "partitions_by_layer": dict(sorted(layers.items())),
            "sets_by_layer": {
                layer: sorted(names) for layer, names in sorted(sets_by_layer.items())
            },
            "partitions_per_set": {
                f"{layer}/{name}": count
                for (layer, name), count in sorted(per_set.items())
            },
            "years_by_instrument": {
                instr: sorted(yrs) for instr, yrs in sorted(instr_years.items())
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_root": self.data_root,
            "materialized_root_exists": self.materialized_root_exists,
            "nonempty_only": self.nonempty_only,
            "config_inventories_read": list(self.config_inventories_read),
            "coverage_summary": self.coverage_summary(),
            "disagreements": [d.to_dict() for d in self.disagreements],
            "partitions": [e.to_dict() for e in self.entries],
        }


def _parse_partition(partition_id: str) -> tuple[str | None, int | None, str | None]:
    match = _PARTITION_RE.match(partition_id)
    if match is None:
        return None, None, None
    return match.group("instrument"), int(match.group("year")), match.group("horizon")


def _parquet_nonempty(path: Path) -> bool:
    """Cheap non-empty check: the file exists with a positive byte size.

    A genuine parquet always has a multi-byte header/footer, so a positive size
    is a safe, dependency-free proxy and keeps the reader free of polars.
    """

    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _walk_layer(layer_root: Path, layer: str, *, nonempty_only: bool) -> list[PartitionEntry]:
    entries: list[PartitionEntry] = []
    if not layer_root.is_dir():
        return entries
    for parquet in sorted(layer_root.rglob("values.parquet")):
        if nonempty_only and not _parquet_nonempty(parquet):
            continue
        # Trailing fixed segments: <dsv>/<partition>/values.parquet
        rel = parquet.relative_to(layer_root)
        parts = rel.parts
        if len(parts) < 3:
            continue
        dataset_version_id = parts[-3]
        partition_id = parts[-2]
        namespace_parts = parts[:-3]
        namespace = "/".join(namespace_parts)
        materialized_set = namespace_parts[0] if namespace_parts else ""
        set_id = namespace_parts[-1] if namespace_parts else ""
        instrument, year, horizon = _parse_partition(partition_id)
        entries.append(
            PartitionEntry(
                layer=layer,
                materialized_set=materialized_set,
                namespace=namespace,
                set_id=set_id,
                dataset_version_id=dataset_version_id,
                partition_id=partition_id,
                instrument=instrument,
                year=year,
                horizon=horizon,
                parquet_path=str(parquet),
            )
        )
    return entries


@dataclass(frozen=True, slots=True)
class _ConfigInventory:
    """Parsed acceptance-lock config inventory (governance bookkeeping)."""

    config_file: str
    # dataset_version_id -> committed_summary_state (per-record truth)
    states: dict[str, str]
    # selection_contract.current_committed_summary_counts header (may be stale)
    header_counts: dict[str, int] | None


def _load_config_inventories(repo_root: Path) -> tuple[list[_ConfigInventory], list[str]]:
    """Parse the acceptance-lock config inventories.

    Returns one ``_ConfigInventory`` per readable file plus the list of relative
    paths read. Missing files are skipped (the tool still reports disk truth
    without them).
    """

    inventories: list[_ConfigInventory] = []
    read_files: list[str] = []
    for relpath in _CONFIG_INVENTORY_RELPATHS:
        path = repo_root / relpath
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        read_files.append(str(relpath))

        states: dict[str, str] = {}
        schemas = payload.get("schemas")
        if isinstance(schemas, Mapping):
            for _schema, years in schemas.items():
                if not isinstance(years, Mapping):
                    continue
                for _year, record in years.items():
                    if not isinstance(record, Mapping):
                        continue
                    dsv = record.get("dataset_version_id")
                    state = record.get("committed_summary_state")
                    if isinstance(dsv, str) and isinstance(state, str):
                        states[dsv] = state

        header_counts: dict[str, int] | None = None
        contract = payload.get("selection_contract")
        if isinstance(contract, Mapping):
            counts = contract.get("current_committed_summary_counts")
            if isinstance(counts, Mapping):
                header_counts = {
                    str(k): int(v)
                    for k, v in counts.items()
                    if isinstance(v, int) and not isinstance(v, bool)
                }

        inventories.append(
            _ConfigInventory(
                config_file=str(relpath),
                states=states,
                header_counts=header_counts,
            )
        )
    return inventories, read_files


def _compute_disagreements(
    entries: tuple[PartitionEntry, ...],
    inventories: list[_ConfigInventory],
) -> tuple[Disagreement, ...]:
    """Cross-check on-disk presence against config acceptance-lock states.

    Flags:
    * ``config_blocked_but_disk_present``: config marks the dsv BLOCKED (or any
      non-eligible state) yet materialized values exist on disk.
    * ``disk_present_config_missing``: values exist on disk for a dsv that the
      acceptance-lock config never lists at all.
    * ``config_header_stale``: the ``selection_contract`` summary-counts header
      contradicts the file's own per-record ``committed_summary_state`` values
      (the exact "BLOCKED:27" misread that motivated this tool — a stale header
      that lies about its own records and about disk).
    """

    disagreements: list[Disagreement] = []
    present_dsvs: dict[str, int] = Counter()
    for entry in entries:
        present_dsvs[entry.dataset_version_id] += 1

    for dsv, count in sorted(present_dsvs.items()):
        # Scan every config file (no first-wins masking): a stale BLOCKED in the
        # labels inventory must surface even when the features inventory marks
        # the same dsv ACCEPTED. Listing in any file means "not missing".
        listed_anywhere = False
        for inventory in inventories:
            state = inventory.states.get(dsv)
            if state is None:
                continue
            listed_anywhere = True
            if state not in _ELIGIBLE_ACCEPTANCE_STATES:
                disagreements.append(
                    Disagreement(
                        kind="config_blocked_but_disk_present",
                        dataset_version_id=dsv,
                        detail=(
                            f"acceptance-lock config marks state={state!r} (not "
                            f"eligible) but {count} materialized partition(s) are "
                            "present on disk"
                        ),
                        config_state=state,
                        config_file=inventory.config_file,
                    )
                )
        if not listed_anywhere:
            disagreements.append(
                Disagreement(
                    kind="disk_present_config_missing",
                    dataset_version_id=dsv,
                    detail=(
                        f"{count} materialized partition(s) present on disk but the "
                        "acceptance-lock config does not list this dataset_version_id"
                    ),
                )
            )

    # Header summary-counts vs the file's own per-record state histogram.
    for inventory in inventories:
        if inventory.header_counts is None:
            continue
        actual = Counter(inventory.states.values())
        # Compare only on the states the header asserts (it may omit zero rows).
        for state, header_value in sorted(inventory.header_counts.items()):
            actual_value = actual.get(state, 0)
            if header_value != actual_value:
                disagreements.append(
                    Disagreement(
                        kind="config_header_stale",
                        dataset_version_id="(header)",
                        detail=(
                            f"selection_contract header asserts {state}={header_value} "
                            f"but the file's own per-record committed_summary_state has "
                            f"{state}={actual_value}; the header is stale and must not be "
                            "read as data truth"
                        ),
                        config_state=state,
                        config_file=inventory.config_file,
                    )
                )
    return tuple(disagreements)


def build_inventory(
    *,
    data_root: str | Path | None = None,
    repo_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    frontier_data_root: str | Path | None = None,
    nonempty_only: bool = True,
    check_config: bool = True,
) -> DataInventory:
    """Walk the on-disk materialized store and build the canonical inventory.

    ``data_root`` resolution follows :func:`resolve_data_root`. ``repo_root`` is
    where the acceptance-lock config inventories are read from (defaults to the
    repo containing this file). Read-only and deterministic.
    """

    resolved_root = resolve_data_root(
        data_root, env=env, frontier_data_root=frontier_data_root
    )
    if repo_root is None:
        repo_root_path = Path(__file__).resolve().parents[2]
    else:
        repo_root_path = Path(repo_root).expanduser()

    entries: list[PartitionEntry] = []
    materialized_exists = False
    for layer in ("features", "labels"):
        layer_root = resolved_root / layer / "materialized"
        if layer_root.is_dir():
            materialized_exists = True
        entries.extend(_walk_layer(layer_root, layer, nonempty_only=nonempty_only))

    entries_tuple = tuple(entries)

    inventories: list[_ConfigInventory] = []
    read_files: list[str] = []
    if check_config:
        inventories, read_files = _load_config_inventories(repo_root_path)

    disagreements = (
        _compute_disagreements(entries_tuple, inventories) if check_config else ()
    )

    return DataInventory(
        data_root=str(resolved_root),
        materialized_root_exists=materialized_exists,
        entries=entries_tuple,
        disagreements=disagreements,
        config_inventories_read=tuple(read_files),
        nonempty_only=nonempty_only,
    )


def render_summary(inventory: DataInventory) -> str:
    """Render a deterministic human-readable coverage + disagreement summary."""

    cov = inventory.coverage_summary()
    lines: list[str] = []
    lines.append("ON-DISK MATERIALIZED DATA INVENTORY (data-existence source of truth)")
    lines.append(f"data_root: {inventory.data_root}")
    lines.append(f"materialized_root_exists: {inventory.materialized_root_exists}")
    lines.append(f"total_partitions (values.parquet present): {cov['total_partitions']}")
    lines.append("")
    lines.append("COVERAGE SUMMARY")
    lines.append(f"  instruments: {', '.join(cov['instruments']) or '(none)'}")
    years = cov["years"]
    if years:
        lines.append(f"  years: {years[0]}..{years[-1]} ({', '.join(map(str, years))})")
    else:
        lines.append("  years: (none)")
    for layer, count in cov["partitions_by_layer"].items():
        lines.append(f"  {layer}: {count} partitions across sets:")
        for name in cov["sets_by_layer"].get(layer, []):
            n = cov["partitions_per_set"].get(f"{layer}/{name}", 0)
            lines.append(f"      - {name}: {n}")
    lines.append("")
    lines.append("DISAGREEMENT (config acceptance-lock vs on-disk presence)")
    lines.append(
        "  config inventories read: "
        + (", ".join(inventory.config_inventories_read) or "(none)")
    )
    if not inventory.disagreements:
        lines.append("  OK: no config-vs-disk acceptance-lock disagreements detected.")
    else:
        lines.append(f"  {len(inventory.disagreements)} disagreement(s) FLAGGED:")
        for d in inventory.disagreements:
            lines.append(f"    [{d.kind}] {d.dataset_version_id}: {d.detail}")
    return "\n".join(lines) + "\n"


def run_inventory(
    *,
    data_root: str | Path | None = None,
    repo_root: str | Path | None = None,
    nonempty_only: bool = True,
    check_config: bool = True,
    emit_json: bool = False,
    out: Any = None,
) -> int:
    """Build the inventory and print a JSON or human summary. Returns exit code.

    Exit code is ``0`` always (read-only report); disagreements are surfaced in
    the output, not via a nonzero code, so callers can choose how to gate.
    """

    stream = sys.stdout if out is None else out
    inventory = build_inventory(
        data_root=data_root,
        repo_root=repo_root,
        nonempty_only=nonempty_only,
        check_config=check_config,
    )
    if emit_json:
        print(json.dumps(inventory.to_dict(), sort_keys=True, indent=2), file=stream)
    else:
        print(render_summary(inventory), end="", file=stream)
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data_inventory",
        description=(
            "Canonical on-disk materialized data inventory (the data-existence "
            "source of truth). Read-only."
        ),
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help=(
            "Explicit data root. Default resolution: ALPHA_DATA_ROOT env, then "
            "frontier.yaml data_root, then ~/alpha_data/alpha_system."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root for reading acceptance-lock config inventories.",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include values.parquet entries that are zero-byte/empty.",
    )
    parser.add_argument(
        "--no-config-check",
        action="store_true",
        help="Skip the config-vs-disk acceptance-lock disagreement cross-check.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for ``python tools/frontier/data_inventory.py``."""

    args = _build_arg_parser().parse_args(argv)
    return run_inventory(
        data_root=args.data_root,
        repo_root=args.repo_root,
        nonempty_only=not args.include_empty,
        check_config=not args.no_config_check,
        emit_json=args.json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
