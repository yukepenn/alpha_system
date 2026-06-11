# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`LABEL_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress:
`LABEL_COMPUTE_FAST_PATH_V1` is the active Workflow 2 campaign. `LCFP-P00`
adds the bootstrap documentation, value-free evidence root, and FUTSUB pause
handoff. `LCFP-P01` adds the value-free label-engine inventory, a bounded
reference-engine baseline benchmark summary, and the read-only benchmark
harness used to produce that baseline. `LCFP-P02` adds the shared label panel,
terminal-index, guard-disposition, `label_available_ts`, and quality-metadata
contract in `alpha_system.labels.fast`. `LCFP-P03` extends the fixed-horizon
fast pack to the governed fixed-minute trade-price horizons
1/3/5/10/15/30/60/120/240m, preserves the existing governed midprice minute
horizons, and routes symbolic `session_close` / `maintenance_flat` labels to
LCFP-P04 without crashing on their enum tokens. `LCFP-P04` adds fast
session-close, maintenance-flat, cost-adjusted, and spread-adjusted label packs
with synthetic parity coverage against the reference families. `LCFP-P05` adds
the governed path-label pack for MFE, MAE, target-before-stop, and
triple-barrier labels with synthetic parity coverage against the reference path
family and P02 guard checks for crossing rows. `LCFP-P06` wires the merged fast
label packs into targeted dry-run/execute materialization, checkpoint/restart,
compute-only label workers, strictly serial registry registration, and strict
identity resolver smoke coverage. `LCFP-P07` adds the consolidated synthetic
parity, no-lookahead, and guard suite for every governed fast label family,
including exact `label_available_ts` and identity parity plus a value-free
parity report. `LCFP-P08` runs the bounded real-data benchmark/readiness gate
with registry backup, slice self-validation, real reference and fast runners,
worker sweep, resolver/parity checks, and selected per-family engine
policy. `LCFP-P09` adds the value-free closeout verdict plus the
coordinator-only FUTSUB reintegration handoff. The selected engine policy is per
family: fast for `fixed_base` and `path`, reference for `fixed_extended`,
`close_out`, and `cost_adjusted`.

Active / next phase after this branch: after LCFP-P09 review and merge, the
coordinator should repoint `ACTIVE_CAMPAIGN.md` back to
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` and resume the stopped FUTSUB run
per the reintegration handoff. The phase branch does not perform that repoint or
resume.

New durable surfaces through this `LCFP-P09` executor snapshot:

- `docs/label_compute_fast_path/README.md` indexes the campaign bundle,
  durable docs, value-free evidence root, P01 artifacts, benchmark command, and
  handoffs.
- `docs/label_compute_fast_path/OVERVIEW.md` summarizes the fast-label producer
  path, reference-oracle policy, parity/no-lookahead/guard gates, and FUTSUB
  supersession condition.
- `docs/label_compute_fast_path/PANEL_TERMINAL_CONTRACT.md` documents the
  shared panel, terminal-index, roll/maintenance guard, availability, and
  quality metadata surface for P03/P04/P05.
- `src/alpha_system/labels/fast/panel.py` defines `SharedLabelPanel`,
  `TerminalRequest`, `resolve_terminal_indices`, `derive_label_available_ts`,
  and value-free quality metadata helpers.
- `src/alpha_system/labels/fast/fixed_horizon.py` declares the P03 fixed-minute
  fast pack coverage and explicit P04 routing for symbolic close-out labels.
- `src/alpha_system/labels/fast/session_maintenance.py` declares the P04
  `session_close` / `maintenance_flat` fast pack.
- `src/alpha_system/labels/fast/cost_adjusted.py` declares the P04
  `cost_adjusted_fwd_ret` / `spread_adjusted_fwd_ret` fast pack.
- `src/alpha_system/labels/fast/path.py` declares the P05 `mfe`, `mae`,
  `target_before_stop`, and `triple_barrier` fast pack with reference fallback
  routing outside the P02 proof boundary.
- `src/alpha_system/labels/fast/worker.py` declares value-free fast-label worker
  manifests for local checkpoint/restart.
- `src/alpha_system/features/scaleout/driver.py` routes label scaleout through
  V1 fast labels, targeting, checkpoint/registry skip, force recompute,
  compute-only workers, and serial label-registry registration.
- `src/alpha_system/cli/scaleout.py` exposes `scaleout label-pack --engine`,
  `--workers`, `--horizon-group`, and `--force`.
- `src/alpha_system/cli/label.py` exposes `label materialize --fast-path` for
  the same targeted label scaleout path.
- `tests/unit/label_compute_fast_path/test_fixed_horizon_extended_pack.py`
  covers all nine governed trade-price fixed-minute horizons plus roll and
  maintenance drop parity against the reference family.
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py`
  covers P04 close-out and cost-adjusted parity, including session gaps,
  roll-drop rows, and BBO missingness flags.
- `tests/unit/label_compute_fast_path/test_path_label_pack.py` covers P05 path
  parity, same-bar ambiguity policy variants, timeout rows, no-trade session
  gaps, and P02 roll/maintenance guard crossing rows.
- `tests/unit/label_compute_fast_path/test_worker_checkpoint_registry_integration.py`
  covers P06 targeting, dry-run, checkpoint skip, force recompute, worker order,
  and label worker env precedence.
- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py` covers the
  consolidated P07 family-by-dimension parity matrix, required synthetic guard
  cases, same-bar policy variants, roll policy dispositions, and overlap
  metadata preservation.
- `tests/no_lookahead/label_fast_path/test_fast_label_available_ts.py` covers
  fast label `label_available_ts` parity against the reference derivation and
  labels-only canonical input contracts.
- `tests/unit/feature_compute_fast_path/parity_harness.py` now includes
  value-free label parity summary statistics used by the P07 report.
- `docs/label_compute_fast_path/SESSION_MAINTENANCE_COST_PACKS.md` documents
  the P04 pack surfaces and read-only `backtest/costs.py` cost-profile design.
- `docs/label_compute_fast_path/PATH_LABEL_PACKS.md` documents the P05 path
  pack surface, kernel/fallback routing, same-bar policy, and guard coverage.
- `research/label_compute_fast_path_v1/` is the value-free evidence root for
  inventory, baseline, parity, benchmark, integration, and closeout summaries.
- `research/label_compute_fast_path_v1/inventory/inventory.md` records the
  reference label engine, current fast-label surface, FUTSUB label needs,
  roll-guard and availability rules, overlap metadata, registry schema, and
  parity-harness surface.
- `research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md`
  records the bounded reference-engine timing denominator for later comparison.
- `research/label_compute_fast_path_v1/parity/LCFP-P04.md` records value-free
  P04 parity coverage and the documented cost-label float tolerance.
- `research/label_compute_fast_path_v1/parity/LCFP-P05.md` records value-free
  P05 path parity coverage and the documented path-label float tolerance.
- `research/label_compute_fast_path_v1/integration/integration_report.md`
  records value-free P06 targeting, worker, checkpoint, registry, and resolver
  smoke evidence.
- `research/label_compute_fast_path_v1/parity/parity_report.md` records the
  consolidated P07 parity/no-lookahead/guard matrix, case counts, tolerances,
  optional-dependency behavior, and residual-gap status.
- `research/label_compute_fast_path_v1/benchmark/benchmark_summary.md` records
  the bounded P08 reference/fast benchmark, worker sweep, file counts, registry
  deltas, resolver/parity outcomes, full-window extrapolations, and per-family
  engine policy.
- `research/label_compute_fast_path_v1/closeout/CLOSEOUT.md` records the
  campaign closeout verdict, five separate acceptance status fields, parity and
  benchmark evidence, validation results, and recommended coordinator-owned
  `ACTIVE_CAMPAIGN.md` repoint.
- `tools/label_compute_fast_path/baseline_benchmark.py` is a read-only
  reference-engine benchmark entrypoint for bounded slices.
- `tools/label_compute_fast_path/benchmark_gate.py` is the bounded real-data
  benchmark/readiness gate for P08. It requires a local registry backup before
  execution and writes only the value-free committed summary under the repo.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md` records the
  paused FUTSUB state without deleting or mutating run state, values, registry
  rows, or worktrees.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P03.md` records the fixed-horizon
  enum repair, shared-panel terminal implementation, parity coverage, and local
  validation results for this phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P04.md` records the
  session/maintenance/cost implementation, parity coverage, and local
  validation results for this phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P05.md` records the path-label
  implementation, parity coverage, and local validation results for this
  phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P06.md` records the worker,
  checkpoint, registry, resolver, integration-smoke, and validation evidence
  for this phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P07.md` records the consolidated
  parity, no-lookahead, guard, report, and validation evidence for this phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P08.md` records the benchmark run,
  selected per-family engine policy, registry backup, and validation evidence
  for this phase.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
  records the coordinator-only FUTSUB amendment text, P16-P20 reset/rerun
  recipe, stopped-run resume recipe, and preserve-don't-delete registry rules.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P09.md` records the closeout and
  reintegration handoff work plus local validation evidence for this phase.

The repository-level campaign pointer and live Workflow 2 state are
coordinator-owned. For current in-flight status, run
`python tools/frontier/status_doctor.py` rather than relying on committed
snapshot text.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/LABEL_COMPUTE_FAST_PATH_V1/`
- Label compute fast path docs: `docs/label_compute_fast_path/`
- Value-free research evidence root: `research/label_compute_fast_path_v1/`
- Commit-eligible handoffs:
  `handoffs/LABEL_COMPUTE_FAST_PATH_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle forever. The
fast label producer path emits values only and stays reference-parity-gated.
After `LABEL_COMPUTE_FAST_PATH_V1` acceptance, only the benchmark-selected
families (`fixed_base` and `path`) move to the fast materialization engine;
families where the reference engine remains faster stay on the reference engine.
Resolver exact-id semantics, official keystone registry writes, serial registry
writes, roll and maintenance guards, and `label_available_ts` no-lookahead
behavior are preserved.

FUTSUB-P18/P19 historical "reference-engine-only" text is superseded only by
this campaign's explicit acceptance condition and the LCFP-P09 coordinator
reintegration handoff. Supersession is per family, not fast everywhere, and the
reference engine remains the oracle forever.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data, feature
or label values, provider responses, heavy artifacts, local databases, logs,
caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Research outputs are evidence for review only.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
