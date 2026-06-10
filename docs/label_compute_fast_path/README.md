# Label Compute Fast Path

`LABEL_COMPUTE_FAST_PATH_V1` builds a local, single-machine fast producer path
for governed label materialization. The per-row reference label engine remains
the correctness oracle; the fast path is accepted only after parity,
no-lookahead, guard, registry, and benchmark gates pass.

This campaign is substrate engineering only. It makes no alpha, profitability,
tradability, execution-quality, live-trading, paper-trading, broker, order, or
deployment claim.

## Campaign Bundle

- [GOAL.md](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/GOAL.md)
- [PHASE_PLAN.md](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/PHASE_PLAN.md)
- [campaign.yaml](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/campaign.yaml)
- [ACCEPTANCE.md](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md)
- [RISK_REGISTER.md](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/RISK_REGISTER.md)
- [RUNBOOK.md](../../campaigns/LABEL_COMPUTE_FAST_PATH_V1/RUNBOOK.md)

The root pointer is [ACTIVE_CAMPAIGN.md](../../ACTIVE_CAMPAIGN.md). It is
coordinator-owned; phase branches verify it but do not edit it.

## Durable Docs

- [OVERVIEW.md](OVERVIEW.md) summarizes the fast-label producer path, reference
  oracle, parity gates, and FUTSUB policy supersession condition.
- [PANEL_TERMINAL_CONTRACT.md](PANEL_TERMINAL_CONTRACT.md) records the LCFP-P02
  shared panel, terminal-index, guard-disposition, availability, and quality
  metadata contract consumed by P03/P04/P05.
- [SESSION_MAINTENANCE_COST_PACKS.md](SESSION_MAINTENANCE_COST_PACKS.md)
  records the LCFP-P04 session-close, maintenance-flat, and cost-adjusted fast
  pack surfaces plus the read-only cost-profile consistency design.
- [PATH_LABEL_PACKS.md](PATH_LABEL_PACKS.md) records the LCFP-P05 MFE, MAE,
  target-before-stop, and triple-barrier pack surface, kernel/fallback routing,
  and same-bar ambiguity policy.
- LCFP-P03 extends the fixed-horizon fast pack to governed fixed-minute
  trade-price 1/3/5/10/15/30/60/120/240m labels, keeps existing governed
  midprice minute labels, and routes `session_close` / `maintenance_flat` to
  LCFP-P04.
- LCFP-P04 adds governed `session_close`, `maintenance_flat`,
  `cost_adjusted_fwd_ret`, and `spread_adjusted_fwd_ret` fast packs with
  synthetic parity coverage against the reference families.
- LCFP-P05 adds governed `mfe`, `mae`, `target_before_stop`, and
  `triple_barrier` fast path-label coverage with synthetic parity against the
  reference path family and P02 guard checks for crossing rows.
- LCFP-P06 wires the fast label packs into `alpha scaleout label-pack` and
  `alpha label materialize --fast-path` targeting, checkpoint/restart,
  compute-only worker parallelism, serial label-registry registration, and
  strict resolver smoke coverage.
- LCFP-P07 adds the consolidated synthetic parity, no-lookahead, and guard
  suite for every governed fast label family, plus the value-free parity report
  at
  [parity_report.md](../../research/label_compute_fast_path_v1/parity/parity_report.md).
- LCFP-P08 adds the bounded real-data benchmark/readiness gate, per-family
  production engine selection, worker sweep evidence, and the value-free
  benchmark summary at
  [benchmark_summary.md](../../research/label_compute_fast_path_v1/benchmark/benchmark_summary.md).
- [Research evidence root](../../research/label_compute_fast_path_v1/README.md)
  defines the value-free evidence policy for this campaign.
- [LCFP-P01 inventory](../../research/label_compute_fast_path_v1/inventory/inventory.md)
  records the reference label engine, current fast-label surface, FUTSUB label
  needs, guard, availability, overlap, registry, and parity-harness contracts.
- [LCFP-P01 baseline](../../research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md)
  records the bounded reference-engine timing denominator for later comparison.
- [LCFP-P06 integration report](../../research/label_compute_fast_path_v1/integration/integration_report.md)
  records value-free targeting, worker, checkpoint, registry, and resolver smoke
  evidence.
- [LCFP-P07 parity report](../../research/label_compute_fast_path_v1/parity/parity_report.md)
  records the consolidated family-by-dimension parity matrix, no-lookahead
  coverage, guard cases, tolerances, and optional-dependency behavior.

## Evidence Root

Value-free summaries belong under
`research/label_compute_fast_path_v1/`. Per-row label values, Parquet payloads,
SQLite registries, raw/canonical data, logs, caches, and run-local artifacts
remain local-only and are not committed.

Owning phases create their own subdirectories:

- `inventory/` and `baseline/` in LCFP-P01
- shared-contract evidence as needed in LCFP-P02
- family and parity evidence in LCFP-P03 through LCFP-P07
- `benchmark/` in LCFP-P08
- `integration/` in LCFP-P06
- `closeout/` in LCFP-P09

LCFP-P01 also adds the bounded reference benchmark entrypoint:

```bash
PYTHONPATH=src python -m tools.label_compute_fast_path.baseline_benchmark
```

The command is read-only with respect to production registries and emits only a
value-free summary.

LCFP-P08 adds the bounded real-data benchmark gate entrypoint:

```bash
PYTHONPATH=src python -m tools.label_compute_fast_path.benchmark_gate
```

Create a timestamped local backup of
`$ALPHA_DATA_ROOT/registry/labels.sqlite` before running the gate. The command
writes benchmark values and isolated registries only under `ALPHA_DATA_ROOT`;
the committed summary remains value-free.

## Handoffs

Commit-eligible phase handoffs live under
`handoffs/LABEL_COMPUTE_FAST_PATH_V1/`.

- `LCFP-P00.md` records this bootstrap phase.
- `LCFP-P01.md` records the inventory and bounded baseline benchmark phase.
- `LCFP-P02.md` records the shared panel / terminal / availability contract
  phase.
- `LCFP-P03.md` records the fixed + extended horizon pack repair and parity
  phase.
- `LCFP-P04.md` records the session / maintenance / cost fast pack phase.
- `LCFP-P05.md` records the path-label fast pack phase.
- `LCFP-P06.md` records the worker / checkpoint / registry / resolver
  integration phase.
- `LCFP-P07.md` records the consolidated parity / no-lookahead / guard suite.
- `LCFP-P08.md` records the benchmark/readiness gate, selected per-family
  engine policy, registry backup, and local validation evidence.
- `FUTSUB_PAUSE_STATE.md` records the paused predecessor state and preserves the
  rule that reintegration/resume is coordinator-owned after LCFP-P09.
