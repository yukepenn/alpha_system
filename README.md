# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` is closed as historical context: it added
an opt-in reference-worker path, measured workers=8 at 2.14x for
`cost_adjusted`, and kept default reference workers at 1 outside the documented
FUTSUB-P19 resume deviation.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the active Workflow 2
campaign. This `FUTSUB-P20` executor snapshot materialized and registered the
path LabelPacks for ES/NQ/RTY across the accepted 2019-2026 window, alongside
the fixed-horizon (P16), extended-horizon (P17), session-close /
maintenance-flat (P18), and cost-adjusted (P19) packs. The
`label_materialization` gate (P16-P20) is now closed from the executor side,
pending Ralph-owned validation, review, staging, PR, CI, merge, and done-check
state transitions.

Active / next phase after this branch: `FUTSUB-P21` - Roll-Splice and
Maintenance-Crossing Label Guard Audit, opening the `label_integration` gate
for P21-P23.

New durable surfaces through this `FUTSUB-P20` executor snapshot:

- `configs/labels/scaleout/path.json` is the governed path-label scaleout
  config for ES/NQ/RTY accepted windows, including V1 fast-engine selection,
  worker/thread caps, path variants, horizon set, guard policy, and R-021
  feasibility bounds.
- `src/alpha_system/labels/families/path/family.py` and
  `src/alpha_system/labels/fast/path.py` apply the shared roll-splice and
  maintenance-crossing guard to the full path window before MFE/MAE excursion
  or barrier-touch measurement.
- `src/alpha_system/features/scaleout/driver.py` carries the path
  materialization scope into label identity and registry metadata so dry-run
  identity preview, execution, registry records, and resolver locks use the
  same partition-scoped label-version ids.
- `research/futures_substrate_scaleout_v1/label_packs/path/coverage_summary.md`
  and `coverage_matrix.json` are value-free coverage evidence for the accepted
  window, including feasibility accounting, guard drop/flag counts,
  `label_available_ts`, registry metadata, and overlap-aware N_eff summaries.
- `tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py` covers
  synthetic MFE/MAE values, first-touch barrier `label_available_ts`,
  roll-crossing drops, maintenance-crossing drops, and partition-scoped path
  label identity.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P20.md`
  records materialization evidence, validation, and residual review focus for
  reviewer and coordinator use.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Value-free research evidence root:
  `research/reference_label_parallel_compute_v1/`
- Commit-eligible handoffs:
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root: `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle. Registry
writes remain parent-only and serial. Label values, registries, manifests,
checkpoints, and SQLite files stay local-only under `ALPHA_DATA_ROOT`; path
labels must never silently cross a quarterly roll or the daily maintenance /
trade-date break. Infeasible path units must be flagged with recorded bounds,
not silently skipped. Resolver semantics remain exact-id and fail-closed, with
no fuzzy fallback.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
