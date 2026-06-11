"""Read-only guard-drop enumerator for FUTSUB-P19 cost-adjusted labels.

This tool counts windows that the reference cost-adjusted label family drops
before emitting label rows. It does not compute label values, materialize
Parquet, or open label registries for writing.
"""

from __future__ import annotations

import argparse
import os
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from alpha_system.data.foundation.canonical_loader import load_canonical_bbo_rows
from alpha_system.data.foundation.datasets import (
    DatasetAcceptanceState,
    resolve_dataset_acceptance_lock,
)
from alpha_system.data.foundation.quotes import CanonicalBBORecord
from alpha_system.features.input_views import BBOInputRow
from alpha_system.features.scaleout import driver as scaleout_driver
from alpha_system.features.scaleout.driver import (
    ScaleoutTarget,
    ScaleoutUnit,
    build_scaleout_units,
    load_scaleout_config,
)
from alpha_system.labels.families.cost_adjusted.family import (
    _bbo_rows_by_key,
    _horizon_delta,
    _validated_rows,
)
from alpha_system.labels.families.fixed_horizon.family import (
    MAINTENANCE_GUARD_VERSION,
    MAINTENANCE_POLICY_ID,
    _crosses_maintenance_break,
    _roll_calendar_for_window,
    _root_symbol,
)
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
    RollCrossPolicy,
    RollGuardAction,
    evaluate_roll_guard,
)

REPORT_PATH = Path(
    "research/futures_substrate_scaleout_v1/label_packs/cost_adjusted/guard_drop_counts.md"
)
CONFIG_PATH = Path("configs/labels/scaleout/cost_adjusted.json")
ELIGIBLE_STATES = frozenset(
    {
        DatasetAcceptanceState.ACCEPTED.value,
        DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS.value,
    }
)


class GuardDropEnumeratorError(ValueError):
    """Raised when guard-drop enumeration cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class GuardDecision:
    """One source-to-terminal guard classification."""

    disposition: str
    reason: str
    roll_action: str = ""
    roll_calendar_id: str = ""
    roll_date: str = ""
    safe_default_applied: bool = False

    @property
    def kept(self) -> bool:
        return self.disposition == "keep"


@dataclass(slots=True)
class GuardCountRow:
    """Value-free guard counts for one symbol-year-horizon cell."""

    symbol: str
    year: int
    horizon: str
    ohlcv_dataset_version_id: str
    bbo_dataset_version_id: str
    acceptance_state: str
    source_row_count: int = 0
    terminal_present_count: int = 0
    missing_terminal_count: int = 0
    kept_count: int = 0
    roll_drop_count: int = 0
    maintenance_drop_count: int = 0
    truncated_count: int = 0
    flagged_count: int = 0
    contract_mismatch_drop_count: int = 0
    roll_invalid_count: int = 0
    safe_default_roll_drop_count: int = 0
    matched_roll_calendar_ids: set[str] = field(default_factory=set)

    @property
    def guard_drop_count(self) -> int:
        return (
            self.roll_drop_count + self.maintenance_drop_count + self.contract_mismatch_drop_count
        )


@dataclass(frozen=True, slots=True)
class EnumerationResult:
    """Full read-only enumeration result."""

    rows: tuple[GuardCountRow, ...]
    elapsed_seconds: float
    generated_at: str
    config_path: str
    canonical_root: str
    dataset_registry: str
    roll_policy: str
    registry_mismatches: tuple[str, ...]

    @property
    def totals(self) -> Mapping[str, int]:
        totals: dict[str, int] = defaultdict(int)
        for row in self.rows:
            totals["cells"] += 1
            totals["source_rows"] += row.source_row_count
            totals["terminal_present"] += row.terminal_present_count
            totals["missing_terminal"] += row.missing_terminal_count
            totals["kept"] += row.kept_count
            totals["roll_drops"] += row.roll_drop_count
            totals["maintenance_drops"] += row.maintenance_drop_count
            totals["guard_drops"] += row.guard_drop_count
            totals["truncated"] += row.truncated_count
            totals["flagged"] += row.flagged_count
            totals["contract_mismatch_drops"] += row.contract_mismatch_drop_count
            totals["roll_invalid"] += row.roll_invalid_count
            totals["safe_default_roll_drops"] += row.safe_default_roll_drop_count
        return dict(totals)


def classify_guard_window(
    source: BBOInputRow,
    terminal: BBOInputRow,
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], BBOInputRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[Any, ...]],
    policy: RollCrossPolicy = DEFAULT_CROSS_ROLL_POLICY,
) -> GuardDecision:
    """Classify a source/terminal pair using the reference-family guard order."""

    if source.contract_id != terminal.contract_id:
        return GuardDecision(
            disposition="contract_mismatch_drop",
            reason="contract_mismatch",
        )
    if _crosses_maintenance_break(source.event_ts, terminal.event_ts):
        return GuardDecision(
            disposition="maintenance_drop",
            reason="maintenance_crossing",
        )

    root_symbol = _root_symbol(source)
    if root_symbol is None:
        return GuardDecision(disposition="keep", reason="no_roll_root_symbol")

    calendar = _roll_calendar_for_window(
        root_symbol,
        source.event_ts,
        terminal.event_ts,
        cache=roll_calendar_cache,
    )
    if not _spans_roll_calendar_record(calendar, source.event_ts, terminal.event_ts):
        return GuardDecision(disposition="keep", reason="no_roll_boundary_in_window")

    verdict = evaluate_roll_guard(
        entry_ts=source.event_ts,
        label_horizon_ts=terminal.event_ts,
        calendar=calendar,
        policy=policy,
        root_symbol=root_symbol,
        roll_window_days_before=DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
        roll_window_days_after=DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    )

    roll_calendar_id = verdict.matched_roll_calendar_id or ""
    roll_date = verdict.roll_date.isoformat() if verdict.roll_date is not None else ""
    if verdict.action in {RollGuardAction.DROP, RollGuardAction.INVALID} or not verdict.valid:
        return GuardDecision(
            disposition="roll_drop",
            reason=verdict.reason,
            roll_action=verdict.action.value,
            roll_calendar_id=roll_calendar_id,
            roll_date=roll_date,
            safe_default_applied=verdict.safe_default_applied,
        )
    if verdict.action is RollGuardAction.TRUNCATE:
        if verdict.effective_label_horizon_ts is None:
            return GuardDecision(
                disposition="roll_drop",
                reason="roll_truncate_missing_effective_terminal",
                roll_action=verdict.action.value,
                roll_calendar_id=roll_calendar_id,
                roll_date=roll_date,
                safe_default_applied=verdict.safe_default_applied,
            )
        truncated = terminal_by_key.get(
            (source.series_id, source.contract_id, verdict.effective_label_horizon_ts)
        )
        if truncated is None:
            return GuardDecision(
                disposition="roll_drop",
                reason="roll_truncate_terminal_missing",
                roll_action=verdict.action.value,
                roll_calendar_id=roll_calendar_id,
                roll_date=roll_date,
                safe_default_applied=verdict.safe_default_applied,
            )
        return GuardDecision(
            disposition="truncated",
            reason=verdict.reason,
            roll_action=verdict.action.value,
            roll_calendar_id=roll_calendar_id,
            roll_date=roll_date,
            safe_default_applied=verdict.safe_default_applied,
        )
    if verdict.action is RollGuardAction.FLAG:
        return GuardDecision(
            disposition="flagged",
            reason=verdict.reason,
            roll_action=verdict.action.value,
            roll_calendar_id=roll_calendar_id,
            roll_date=roll_date,
            safe_default_applied=verdict.safe_default_applied,
        )
    return GuardDecision(
        disposition="keep",
        reason=verdict.reason,
        roll_action=verdict.action.value,
        roll_calendar_id=roll_calendar_id,
        roll_date=roll_date,
        safe_default_applied=verdict.safe_default_applied,
    )


def enumerate_counts_for_rows(
    rows: Iterable[BBOInputRow],
    *,
    symbol: str,
    year: int,
    horizons: Sequence[str],
    ohlcv_dataset_version_id: str,
    bbo_dataset_version_id: str,
    acceptance_state: str,
    policy: RollCrossPolicy = DEFAULT_CROSS_ROLL_POLICY,
) -> tuple[GuardCountRow, ...]:
    """Count reference guard outcomes for already-loaded BBO rows."""

    validated_rows = _validated_rows(tuple(rows))
    row_index = _bbo_rows_by_key(validated_rows)
    result_rows: list[GuardCountRow] = []
    for horizon in horizons:
        horizon_delta = _horizon_delta(horizon)
        counts = GuardCountRow(
            symbol=symbol,
            year=year,
            horizon=horizon,
            ohlcv_dataset_version_id=ohlcv_dataset_version_id,
            bbo_dataset_version_id=bbo_dataset_version_id,
            acceptance_state=acceptance_state,
            source_row_count=len(validated_rows),
        )
        roll_calendar_cache: dict[tuple[str, int, int], tuple[Any, ...]] = {}
        for source in validated_rows:
            terminal = row_index.get(
                (source.series_id, source.contract_id, source.event_ts + horizon_delta)
            )
            if terminal is None:
                counts.missing_terminal_count += 1
                continue
            counts.terminal_present_count += 1
            decision = classify_guard_window(
                source,
                terminal,
                terminal_by_key=row_index,
                roll_calendar_cache=roll_calendar_cache,
                policy=policy,
            )
            _accumulate_decision(counts, decision)
        result_rows.append(counts)
    return tuple(result_rows)


def enumerate_guard_drop_counts(
    *,
    config_path: str | Path = CONFIG_PATH,
    canonical_root: str | Path,
    dataset_registry: str | Path,
    symbols: Sequence[str] = (),
    years: Sequence[int] = (),
    policy: RollCrossPolicy = DEFAULT_CROSS_ROLL_POLICY,
) -> EnumerationResult:
    """Run read-only guard-drop enumeration over the selected accepted grid."""

    started = perf_counter()
    config = load_scaleout_config(config_path)
    if config.family != "cost_adjusted":
        raise GuardDropEnumeratorError("guard-drop enumeration is scoped to cost_adjusted")
    target = ScaleoutTarget(
        symbols=tuple(symbol.upper() for symbol in symbols),
        years=tuple(years),
    )
    units = build_scaleout_units(config, target=target)
    if not units:
        raise GuardDropEnumeratorError("no accepted cost_adjusted units selected")
    registry_mismatches = _registry_mismatches(units, Path(dataset_registry))
    if registry_mismatches:
        mismatch_text = "; ".join(registry_mismatches[:5])
        raise GuardDropEnumeratorError(
            "dataset acceptance lock mismatch; refusing to count: " + mismatch_text
        )

    grouped: dict[tuple[str, int], list[ScaleoutUnit]] = defaultdict(list)
    for unit in units:
        grouped[(unit.symbol, unit.year)].append(unit)

    rows: list[GuardCountRow] = []
    for key in sorted(grouped):
        group_units = sorted(grouped[key], key=lambda item: _horizon_sort_key(item.horizon))
        unit = group_units[0]
        bbo_dataset = _input_dataset(unit, "bbo_1m")
        if bbo_dataset is None:
            raise GuardDropEnumeratorError(f"unit {unit.unit_id} has no BBO input dataset")
        bbo_rows = _load_bbo_input_rows(
            canonical_root=Path(canonical_root),
            unit=unit,
            bbo_dataset_version_id=bbo_dataset.dataset_version_id,
            bbo_schema_id=bbo_dataset.schema_id,
        )
        rows.extend(
            enumerate_counts_for_rows(
                bbo_rows,
                symbol=unit.symbol,
                year=unit.year,
                horizons=tuple(unit.horizon for unit in group_units),
                ohlcv_dataset_version_id=unit.dataset_version_id,
                bbo_dataset_version_id=bbo_dataset.dataset_version_id,
                acceptance_state=unit.acceptance_state,
                policy=policy,
            )
        )

    return EnumerationResult(
        rows=tuple(
            sorted(
                rows,
                key=lambda row: (row.symbol, row.year, _horizon_sort_key(row.horizon)),
            )
        ),
        elapsed_seconds=perf_counter() - started,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        config_path=Path(config_path).as_posix(),
        canonical_root=Path(canonical_root).as_posix(),
        dataset_registry=Path(dataset_registry).as_posix(),
        roll_policy=policy.value,
        registry_mismatches=tuple(registry_mismatches),
    )


def render_markdown(result: EnumerationResult) -> str:
    """Render a value-free Markdown report."""

    totals = result.totals
    lines = [
        "# FUTSUB-P19 cost_adjusted guard-drop counts",
        "",
        "Value-free evidence only. This report contains counts and provenance, not "
        "label values, prices, returns, Parquet paths, SQLite contents, provider "
        "responses, or checkpoint payloads.",
        "",
        f"- Generated: `{result.generated_at}`",
        "- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`",
        "- Phase: `P121500_FUTSUB_P19_GUARD_COUNT_SURFACE`",
        "- Source family: `cost_adjusted`",
        f"- Config: `{result.config_path}`",
        f"- Canonical root read: `{result.canonical_root}`",
        f"- Dataset registry read-only check: `{result.dataset_registry}`",
        "- Values/registries written: `false`",
        "- Label rows emitted: `false`",
        "",
        "## Guard Provenance",
        "",
        f"- Roll policy id: `{ROLL_POLICY_ID}`",
        f"- Roll guard version: `{ROLL_GUARD_VERSION}`",
        f"- Roll cross policy: `{result.roll_policy}`",
        (
            f"- Roll window days before/after: `{DEFAULT_ROLL_WINDOW_DAYS_BEFORE}` / "
            f"`{DEFAULT_ROLL_WINDOW_DAYS_AFTER}`"
        ),
        f"- Maintenance policy id: `{MAINTENANCE_POLICY_ID}`",
        f"- Maintenance guard version: `{MAINTENANCE_GUARD_VERSION}`",
        "- Maintenance crossing policy: `drop`",
        (
            "- Calendar source: analytic CME equity-index quarterly roll calendar, "
            "approximate and not provider-exact."
        ),
        (
            "- Classification order matches the reference cost_adjusted family guard "
            "path: terminal existence, contract scope, maintenance crossing, then "
            "roll guard."
        ),
        "",
        "## Totals",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Cells | {totals.get('cells', 0)} |",
        f"| Source BBO rows considered across cells | {totals.get('source_rows', 0)} |",
        f"| Terminal-present windows checked by guards | {totals.get('terminal_present', 0)} |",
        f"| Missing terminal BBO windows, not guard drops | {totals.get('missing_terminal', 0)} |",
        f"| Kept by guard | {totals.get('kept', 0)} |",
        f"| Dropped by roll guard | {totals.get('roll_drops', 0)} |",
        f"| Dropped by maintenance crossing | {totals.get('maintenance_drops', 0)} |",
        f"| Total guard drops | {totals.get('guard_drops', 0)} |",
        f"| Truncated by roll guard | {totals.get('truncated', 0)} |",
        f"| Flagged by roll guard | {totals.get('flagged', 0)} |",
        f"| Roll invalid/drop subset | {totals.get('roll_invalid', 0)} |",
        f"| Safe-default roll-drop subset | {totals.get('safe_default_roll_drops', 0)} |",
        "",
        "## Per Symbol-Year-Horizon Counts",
        "",
        (
            "| Symbol | Year | Horizon | OHLCV DatasetVersion | BBO DatasetVersion | "
            "State | Source rows | Terminal present | Missing terminal | Roll drops | "
            "Maintenance drops | Guard drops | Truncated | Flagged | Roll calendar ids |"
        ),
        (
            "| --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | "
            "---: | ---: | ---: | ---: | --- |"
        ),
    ]
    for row in result.rows:
        calendar_ids = ", ".join(sorted(row.matched_roll_calendar_ids)) or "n/a"
        lines.append(
            "| "
            f"`{row.symbol}` | {row.year} | `{row.horizon}` | "
            f"`{row.ohlcv_dataset_version_id}` | `{row.bbo_dataset_version_id}` | "
            f"`{row.acceptance_state}` | {row.source_row_count} | "
            f"{row.terminal_present_count} | {row.missing_terminal_count} | "
            f"{row.roll_drop_count} | {row.maintenance_drop_count} | "
            f"{row.guard_drop_count} | {row.truncated_count} | {row.flagged_count} | "
            f"{calendar_ids} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            (
                "- Missing terminal BBO windows are counted separately because the "
                "reference family emits them as `label_gap` rows, not guard drops."
            ),
            (
                "- Roll and maintenance guard drops are not emitted as label rows by "
                "the reference family under the configured `drop` policy."
            ),
            (
                "- `Truncated` and `Flagged` are included for policy-surface "
                "completeness; the accepted P19 cost_adjusted policy is `drop`, "
                "so they are expected to be zero in this run."
            ),
            f"- Elapsed seconds: `{result.elapsed_seconds:.3f}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(result: EnumerationResult, output_path: str | Path) -> None:
    """Write the Markdown report to a repo-local path."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(result), encoding="utf-8")


def _accumulate_decision(counts: GuardCountRow, decision: GuardDecision) -> None:
    if decision.roll_calendar_id:
        counts.matched_roll_calendar_ids.add(decision.roll_calendar_id)
    if decision.disposition == "keep":
        counts.kept_count += 1
    elif decision.disposition == "roll_drop":
        counts.roll_drop_count += 1
        if decision.roll_action == RollGuardAction.INVALID.value:
            counts.roll_invalid_count += 1
        if decision.safe_default_applied:
            counts.safe_default_roll_drop_count += 1
    elif decision.disposition == "maintenance_drop":
        counts.maintenance_drop_count += 1
    elif decision.disposition == "truncated":
        counts.truncated_count += 1
    elif decision.disposition == "flagged":
        counts.flagged_count += 1
    elif decision.disposition == "contract_mismatch_drop":
        counts.contract_mismatch_drop_count += 1
    else:  # pragma: no cover - defensive against future disposition expansion.
        raise GuardDropEnumeratorError(f"unsupported guard disposition: {decision.disposition}")


def _load_bbo_input_rows(
    *,
    canonical_root: Path,
    unit: ScaleoutUnit,
    bbo_dataset_version_id: str,
    bbo_schema_id: str,
) -> tuple[BBOInputRow, ...]:
    rows = load_canonical_bbo_rows(
        canonical_root=canonical_root,
        dataset_version_id=bbo_dataset_version_id,
        symbol=unit.symbol,
        start_ts=unit.window_start_ts,
        end_ts=unit.window_end_ts,
        partition_schema=scaleout_driver._on_disk_partition_schema(
            canonical_root,
            bbo_dataset_version_id,
            bbo_schema_id,
        ),
    )
    if not rows:
        raise GuardDropEnumeratorError(
            f"no BBO rows loaded for {unit.symbol} {unit.year} {bbo_dataset_version_id}"
        )
    return tuple(_bbo_input_row_from_mapping(row) for row in rows)


def _bbo_input_row_from_mapping(row: Mapping[str, object]) -> BBOInputRow:
    record = CanonicalBBORecord.from_mapping(row)
    return BBOInputRow(
        instrument_id=record.instrument_id,
        contract_id=record.contract_id,
        series_id=record.series_id,
        bar_start_ts=record.bar_start_ts,
        bar_end_ts=record.bar_end_ts,
        event_ts=record.event_ts,
        available_ts=record.available_ts,
        ingested_at=record.ingested_at,
        bid=record.bid,
        ask=record.ask,
        bid_size=record.bid_size,
        ask_size=record.ask_size,
        mid=record.mid,
        spread=record.spread,
        data_version=record.data_version,
        quality_flags=record.quality_flags,
        session_label=record.session_label,
        spread_ticks=record.spread_ticks,
        microprice=record.microprice,
        bid_order_count=record.bid_order_count,
        ask_order_count=record.ask_order_count,
    )


def _input_dataset(unit: ScaleoutUnit, schema_id: str):
    for dataset in unit.input_datasets:
        if dataset.schema_id == schema_id:
            return dataset
    return None


def _registry_mismatches(units: Sequence[ScaleoutUnit], registry_path: Path) -> tuple[str, ...]:
    mismatches: list[str] = []
    checked: set[str] = set()
    for unit in units:
        for dataset in unit.input_datasets:
            if dataset.dataset_version_id in checked:
                continue
            checked.add(dataset.dataset_version_id)
            lock = resolve_dataset_acceptance_lock(registry_path, dataset.dataset_version_id)
            if lock is None:
                mismatches.append(f"{dataset.dataset_version_id}: missing persisted lock")
                continue
            if lock.state.value not in ELIGIBLE_STATES:
                mismatches.append(
                    f"{dataset.dataset_version_id}: registry state {lock.state.value} "
                    "is not eligible"
                )
                continue
            if lock.state.value != dataset.acceptance_state:
                mismatches.append(
                    f"{dataset.dataset_version_id}: unit state "
                    f"{dataset.acceptance_state} != registry state {lock.state.value}"
                )
    return tuple(mismatches)


def _spans_roll_calendar_record(
    calendar: Iterable[Any],
    entry_ts: datetime,
    terminal_ts: datetime,
) -> bool:
    entry_date = entry_ts.date()
    terminal_date = terminal_ts.date()
    return any(entry_date <= record.roll_date <= terminal_date for record in calendar)


def _horizon_sort_key(value: str) -> tuple[int, str]:
    text = value.strip().lower()
    if text.endswith("m") and text[:-1].isdigit():
        return (int(text[:-1]), text)
    return (10**9, text)


def _parse_csv_tokens(value: str | None) -> tuple[str, ...]:
    if value is None or not value.strip():
        return ()
    return tuple(token.strip() for token in value.split(",") if token.strip())


def _parse_csv_ints(value: str | None) -> tuple[int, ...]:
    return tuple(int(token) for token in _parse_csv_tokens(value))


def _default_alpha_data_root() -> Path:
    raw = os.environ.get("ALPHA_DATA_ROOT", "~/alpha_data/alpha_system")
    return Path(raw).expanduser().resolve(strict=False)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    alpha_root = _default_alpha_data_root()
    parser = argparse.ArgumentParser(
        description="Read-only cost_adjusted guard-drop count enumerator.",
    )
    parser.add_argument("--config", default=CONFIG_PATH.as_posix())
    parser.add_argument(
        "--canonical-root",
        default=(alpha_root / "databento" / "canonical" / "glbx_mdp3").as_posix(),
    )
    parser.add_argument(
        "--dataset-registry",
        default=(alpha_root / "registry" / "datasets.sqlite").as_posix(),
    )
    parser.add_argument("--output", default=REPORT_PATH.as_posix())
    parser.add_argument("--symbols", default="", help="Optional comma-separated symbol filter.")
    parser.add_argument("--years", default="", help="Optional comma-separated year filter.")
    parser.add_argument(
        "--roll-policy",
        default=DEFAULT_CROSS_ROLL_POLICY.value,
        choices=tuple(policy.value for policy in RollCrossPolicy),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = enumerate_guard_drop_counts(
        config_path=args.config,
        canonical_root=args.canonical_root,
        dataset_registry=args.dataset_registry,
        symbols=_parse_csv_tokens(args.symbols),
        years=_parse_csv_ints(args.years),
        policy=RollCrossPolicy(args.roll_policy),
    )
    write_report(result, args.output)
    totals = result.totals
    print(
        "guard-drop counts written: "
        f"{args.output}; cells={totals.get('cells', 0)}; "
        f"roll_drops={totals.get('roll_drops', 0)}; "
        f"maintenance_drops={totals.get('maintenance_drops', 0)}; "
        f"guard_drops={totals.get('guard_drops', 0)}; "
        f"elapsed_seconds={result.elapsed_seconds:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
