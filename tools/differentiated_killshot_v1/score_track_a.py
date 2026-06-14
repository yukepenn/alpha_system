#!/usr/bin/env python3
"""DK-P03 Track A real-data scoring harness (tools/runtime side of the rail).

This coordinator harness is the **only** place a real-data metric is read for the
DIFFERENTIATED_KILLSHOT_V1 Track A mechanisms, and only after both predecessor
gates are committed: the DK-P00 FDR active-subset restatement and the DK-P02
``ZERO_PASS_MET`` surrogate calibration for the scored study.

Data flow (no research->sim bridge):

1. Resolve the locked feature/label packs through ``FeatureLabelPackResolver``.
2. Load already-materialized values via ``core.value_store.load_parquet_values``
   (reusing the proven DK-P02 staging functions from
   ``tools/discovery_rigor_floor/run_real_surrogate_calibration.py``).
3. Align factor<->label rows on ``(instrument_id, event_ts, session_id)`` and
   **pool** ES/NQ/RTY across all locked partitions into one observation list per
   (mechanism, horizon) pooled test.
4. Inject the pooled rows into the pure research scorer
   (``alpha_system.research.track_a_scorer.score_mechanism``), which calls the
   runtime factor diagnostics engine and attaches N_eff / power.
5. Ledger each scored variant ``COMPLETED`` within the pre-registered budget and
   emit a value-bearing per-mechanism diagnostics JSON (committed) plus a
   value-free run summary.

``research/`` imports none of ``backtest`` / ``management`` / ``fast_path`` /
``value_store``; the value loader lives here on the tools side and hands rows in.
No promotion, no second PnL truth, no alpha/tradability claim.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Reuse the proven DK-P02 staging backbone (resolve + load_parquet_values +
# factor/label JSONL materialization + version filtering). This is the
# tools-side value loader; research/ never imports it.
from tools.discovery_rigor_floor import run_real_surrogate_calibration as cal

from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.study_spec import StudySpec
from alpha_system.governance.variant_ledger import (
    VariantLedger,
    VariantLedgerRecord,
    VariantLedgerStatus,
    evaluate_family_budget,
)
from alpha_system.research.track_a_scorer import (
    MechanismDiagnostics,
    score_mechanism,
)
from alpha_system.runtime.diagnostics.splits.n_eff import HorizonOverlapMetadata
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver

DK_P03_SCHEMA = "alpha_system.tools.differentiated_killshot_v1.track_a_run.v1"

# A forward-return horizon-overlap discount: bars sampled at 1m cadence,
# label horizon = horizon_seconds; the overlap discount equals the number of
# overlapping 1m bars in the horizon window (first-order, value-free; mirrors
# the FUTSUB N_eff convention).
_BAR_SECONDS = 60

# DK-P03 scratch namespaces must be local WSL paths under a declared scratch
# prefix and isolated from the production registry roots.
_DK_P03_SCRATCH_PREFIX = "dk_p03_"
_PRODUCTION_DIR_NAMES = frozenset({"registry", "features", "labels", "canonical", "metadata"})


class TrackARunError(ValueError):
    """Raised when the DK-P03 scratch namespace is not a safe isolated target."""


def require_isolated_scratch(namespace: str | Path) -> Path:
    """Create + return a local, isolated, non-production scratch directory.

    Disk-safe: the caller cleans this namespace immediately after the mechanism
    completes. We refuse production registry roots and require an explicit
    ``dk_p03_`` scratch prefix (or a pytest tmp path) so a fat-fingered root can
    never be the write target.
    """

    candidate = assert_local_wsl_path(namespace)
    is_tmp = any(part in {"tmp", "pytest-of-" + Path.home().name} for part in candidate.parts) or (
        candidate.as_posix().startswith("/tmp/")
    )
    if not is_tmp and not candidate.name.startswith(_DK_P03_SCRATCH_PREFIX):
        raise TrackARunError(
            f"DK-P03 scratch namespace must use the {_DK_P03_SCRATCH_PREFIX!r} prefix "
            f"or be a pytest/tmp path, got {candidate.as_posix()!r}"
        )
    if candidate.name in _PRODUCTION_DIR_NAMES:
        raise TrackARunError(
            f"DK-P03 scratch namespace must not target a production root, got "
            f"{candidate.as_posix()!r}"
        )
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


@dataclass(frozen=True, slots=True)
class _PooledTest:
    """One pooled (mechanism, horizon, primary factor) observation set."""

    mechanism_id: str
    horizon_text: str
    horizon_seconds: int
    primary_factor_id: str
    secondary_factor_ids: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    partition_count: int
    excluded_partition_count: int


def _utc_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _overlap_metadata(horizon_seconds: int) -> HorizonOverlapMetadata:
    discount = max(1.0, float(horizon_seconds) / float(_BAR_SECONDS))
    return HorizonOverlapMetadata(
        horizon=float(horizon_seconds),
        horizon_unit="seconds",
        sampling_cadence=float(_BAR_SECONDS),
        sampling_cadence_unit="seconds",
        discount_factor=discount,
        metadata_source="dk_p03_forward_return_first_order_overlap",
    )


def _aligned_observations(
    factor_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
    *,
    horizon_seconds: int,
) -> list[dict[str, Any]]:
    """Build pooled observation rows for one staged sub-config.

    Mirrors ``run_real_surrogate_calibration._aligned_factor_value_series``:
    the primary label index is keyed by ``(instrument_id, event_ts, session_id)``
    on the single staged ``label_version`` and the declared horizon, and each
    numeric factor row is joined to it. We additionally carry the no-lookahead
    ``available_ts`` / ``label_available_ts`` so the runtime diagnostics
    availability gate can evaluate them.
    """

    if not factor_rows:
        return []
    sample = factor_rows[0]
    factor_id = str(sample.get("factor_id", ""))
    factor_version = str(sample.get("factor_version", ""))
    data_version = str(sample.get("data_version", ""))
    label_version = cal._staged_label_version(label_rows)
    if label_version is None:
        return []

    primary_index: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in label_rows:
        path_metadata = row.get("path_metadata")
        if not isinstance(path_metadata, Mapping):
            continue
        if str(path_metadata.get("label_version", "")) != label_version:
            continue
        if str(row.get("data_version", "")) != data_version:
            continue
        if cal._horizon_seconds_value(row.get("horizon")) != horizon_seconds:
            continue
        key = (
            str(row.get("instrument_id", "")),
            cal._iso_text(row.get("event_ts"), "event_ts"),
            str(path_metadata.get("session_id", "")),
        )
        primary_index.setdefault(key, []).append(dict(row))

    observations: list[dict[str, Any]] = []
    for row in factor_rows:
        if str(row.get("factor_id", "")) != factor_id:
            continue
        if str(row.get("factor_version", "")) != factor_version:
            continue
        if str(row.get("data_version", "")) != data_version:
            continue
        factor_value = cal._aligned_numeric_factor_value(row)
        if factor_value is None:
            continue
        key = (
            str(row.get("instrument_id", "")),
            cal._iso_text(row.get("event_ts"), "event_ts"),
            str(row.get("session_id", "")),
        )
        for label_row in primary_index.get(key, ()):
            label_value = cal._optional_float(label_row.get("value"))
            if label_value is None:
                continue
            observations.append(
                {
                    "factor_value": factor_value,
                    "label_value": label_value,
                    "horizon_seconds": horizon_seconds,
                    "available_ts": row.get("available_ts"),
                    "label_available_ts": label_row.get("label_available_ts"),
                    "instrument_id": row.get("instrument_id"),
                    "event_ts": row.get("event_ts"),
                    "trade_date": cal._iso_text(row.get("event_ts"), "event_ts")[:10],
                    "session_label": row.get("session_id"),
                }
            )
    return observations


def _stage_pooled_tests(
    study_spec: StudySpec,
    *,
    resolver: FeatureLabelPackResolver,
    scratch_root: Path,
) -> list[_PooledTest]:
    """Stage + pool every pre-registered (horizon, primary factor) test."""

    scope = study_spec.dataset_scope
    declared_feature_family = cal._declared_feature_family(scope)
    declared_factor_ids = cal._declared_conditioning_feature_ids(scope)
    primary_factor_id = declared_factor_ids[0] if declared_factor_ids else ""
    secondary_factor_ids = tuple(declared_factor_ids[1:])

    primary_horizons = scope.get("primary_horizons")
    horizons: list[str]
    if isinstance(primary_horizons, Sequence) and not isinstance(primary_horizons, str):
        horizons = [str(item) for item in primary_horizons]
    else:
        horizons = [str(scope.get("declared_primary_horizon", ""))]

    pooled: list[_PooledTest] = []
    for horizon_text in horizons:
        normalized = horizon_text.strip().lower()
        if normalized not in cal.SUPPORTED_FORWARD_HORIZONS:
            continue
        horizon_seconds, label_type = cal.SUPPORTED_FORWARD_HORIZONS[normalized]
        label_locks = cal._select_label_locks(scope, normalized)

        input_root = scratch_root / "track_a_inputs" / study_spec.study_spec_id / normalized
        input_root.mkdir(parents=True, exist_ok=True)

        # Accumulate observations only for the PRIMARY declared factor; the
        # mechanism is one pooled test per horizon (per the pre-registered
        # variant_budget). Secondary declared factors (quad-witch, quarter-end,
        # the second proximity feature) are carried as caveats, not extra tests.
        rows: list[dict[str, Any]] = []
        partition_count = 0
        excluded_partition_count = 0
        for label_lock in label_locks:
            feature_locks = cal._declared_feature_locks_for_label(
                scope,
                label_lock=label_lock,
                declared_feature_family=declared_feature_family,
            )
            for feature_lock in feature_locks:
                if str(feature_lock.get("feature_id", "")) != primary_factor_id:
                    continue
                resolved = cal._resolve_records(
                    resolver,
                    feature_lock=feature_lock,
                    label_lock=label_lock,
                )
                part_dir = (
                    input_root
                    / cal._path_token(str(label_lock["partition"]))
                    / cal._path_token(str(feature_lock["feature_id"]))
                )
                part_dir.mkdir(parents=True, exist_ok=True)
                data_version = (
                    f"dk_p03:{label_lock['dataset_version_id']}:{label_lock['partition']}"
                )
                factor_staged = cal._materialize_factor_jsonl(
                    resolved["feature_record"],
                    part_dir / "factor-values.jsonl",
                    data_version=data_version,
                    feature_lock=feature_lock,
                )
                if factor_staged.exclusion is not None or factor_staged.pack is None:
                    excluded_partition_count += 1
                    continue
                label_staged = cal._materialize_label_jsonl(
                    resolved["label_record"],
                    part_dir / "labels.jsonl",
                    data_version=data_version,
                    horizon_seconds=horizon_seconds,
                    label_type=label_type,
                    label_lock=label_lock,
                )
                factor_rows = cal._read_staged_jsonl(factor_staged.pack.path)
                label_rows = cal._read_staged_jsonl(label_staged.path)
                part_obs = _aligned_observations(
                    factor_rows,
                    label_rows,
                    horizon_seconds=horizon_seconds,
                )
                rows.extend(part_obs)
                partition_count += 1

        pooled.append(
            _PooledTest(
                mechanism_id=study_spec.dataset_scope.get("mechanism_id", study_spec.study_spec_id),
                horizon_text=normalized,
                horizon_seconds=horizon_seconds,
                primary_factor_id=primary_factor_id,
                secondary_factor_ids=secondary_factor_ids,
                rows=tuple(rows),
                partition_count=partition_count,
                excluded_partition_count=excluded_partition_count,
            )
        )
    return pooled


def score_study(
    study_spec_path: str | Path,
    *,
    alpha_data_root: str | Path,
    scratch_root: str | Path,
    resolver: FeatureLabelPackResolver | None = None,
    caveats: Sequence[str] = (),
    clean_scratch: bool = True,
) -> dict[str, Any]:
    """Score one mechanism StudySpec on real data; return value-bearing result."""

    active_scratch = require_isolated_scratch(scratch_root)
    study_spec = cal._load_study_spec(study_spec_path)
    active_resolver = resolver or FeatureLabelPackResolver(alpha_data_root=alpha_data_root)

    family_id = str(study_spec.dataset_scope.get("family_id", ""))
    mechanism_id = str(study_spec.dataset_scope.get("mechanism_id", study_spec.study_spec_id))
    variant_budget = int(study_spec.variant_budget)

    try:
        pooled_tests = _stage_pooled_tests(
            study_spec,
            resolver=active_resolver,
            scratch_root=active_scratch,
        )
        mechanism_results: list[MechanismDiagnostics] = []
        ledger_path = active_scratch / "variant_ledger.jsonl"
        ledger_path.write_text("", encoding="utf-8")
        ledger = VariantLedger(ledger_path)
        validated_records: list[VariantLedgerRecord] = []
        ledger_records: list[dict[str, Any]] = []
        alpha_spec_id = str(study_spec.alpha_spec_id or study_spec.study_spec_id)
        scored_at = _utc_now()
        secondary_caveat: tuple[str, ...] = ()
        for pooled in pooled_tests:
            if pooled.secondary_factor_ids:
                secondary_caveat = (
                    "Secondary declared conditioning feature(s) "
                    + ", ".join(pooled.secondary_factor_ids)
                    + " are within-mechanism near-duplicate exposures folded into the "
                    "single pooled hypothesis (not independent confirmations).",
                )
            test_caveats = tuple(caveats) + secondary_caveat
            result = score_mechanism(
                mechanism_id=f"{mechanism_id}@{pooled.horizon_text}",
                factor_id=pooled.primary_factor_id,
                rows=pooled.rows,
                horizon_overlap_metadata=_overlap_metadata(pooled.horizon_seconds),
                caveats=test_caveats,
            )
            mechanism_results.append(result)
            trial_id = generate_governance_id(
                GovernanceIdKind.TRIAL_LEDGER_RECORD,
                {
                    "study_spec_id": study_spec.study_spec_id,
                    "horizon": pooled.horizon_text,
                    "factor_id": pooled.primary_factor_id,
                    "phase": "DK-P03",
                },
            )
            record = VariantLedgerRecord.from_mapping(
                {
                    "variant_id": f"{study_spec.study_spec_id}:{pooled.horizon_text}",
                    "alpha_spec_id": alpha_spec_id,
                    "study_spec_id": study_spec.study_spec_id,
                    "family_id": family_id,
                    "attempt_count": 1,
                    "trial_ids": [trial_id],
                    "status": VariantLedgerStatus.COMPLETED.value,
                    "created_at": scored_at,
                }
            )
            validated_records.append(record)
            ledger_records.append(record.to_dict())

        ledger.append_records(tuple(validated_records))

        # Pre-registered budget check: observed pooled tests must not exceed the
        # variant budget. No BudgetAmendmentRecord is authored here.
        observed_variants = len(mechanism_results)
        budget_ok = observed_variants <= variant_budget
        family_budget = int(study_spec.family_budget)
        family_check = evaluate_family_budget(
            family_id=family_id,
            family_budget=family_budget,
            records=tuple(validated_records),
        )

        payload: dict[str, Any] = {
            "schema": DK_P03_SCHEMA,
            "mechanism_id": mechanism_id,
            "study_spec_id": study_spec.study_spec_id,
            "family_id": family_id,
            "variant_budget": variant_budget,
            "observed_variants": observed_variants,
            "variant_budget_respected": budget_ok,
            "family_budget": family_budget,
            "family_budget_check": family_check.to_dict(),
            "budget_amendment_authored": False,
            "per_instrument_split": False,
            "pooled_as_one_test_per_horizon": True,
            "scored_at": _utc_now(),
            "tests": [
                {
                    "horizon": pooled.horizon_text,
                    "primary_factor_id": pooled.primary_factor_id,
                    "secondary_factor_ids": list(pooled.secondary_factor_ids),
                    "partition_count": pooled.partition_count,
                    "excluded_partition_count": pooled.excluded_partition_count,
                    "diagnostics": result.to_dict(),
                }
                for pooled, result in zip(pooled_tests, mechanism_results, strict=True)
            ],
            "variant_ledger_records": ledger_records,
            "statistical_validity_claim": False,
            "no_tradability_or_profitability_or_alpha_claim": True,
        }
        return payload
    finally:
        if clean_scratch:
            shutil.rmtree(active_scratch, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DK-P03 Track A real-data scoring (one mechanism StudySpec).",
    )
    parser.add_argument("--study-spec", required=True, help="Committed locked StudySpec JSON.")
    parser.add_argument("--alpha-data-root", required=True, help="Local alpha data root.")
    parser.add_argument(
        "--scratch-root",
        required=True,
        help="Isolated local scratch namespace (cleaned after the run).",
    )
    parser.add_argument(
        "--result-out",
        required=True,
        help="Value-bearing per-mechanism diagnostics JSON output path.",
    )
    parser.add_argument(
        "--keep-scratch",
        action="store_true",
        help="Do not delete the scratch namespace after scoring (debug only).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = score_study(
        args.study_spec,
        alpha_data_root=args.alpha_data_root,
        scratch_root=args.scratch_root,
        clean_scratch=not args.keep_scratch,
    )
    out_path = Path(args.result_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_out": str(out_path), "mechanism_id": payload["mechanism_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
