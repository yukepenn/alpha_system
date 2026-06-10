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
- [Research evidence root](../../research/label_compute_fast_path_v1/README.md)
  defines the value-free evidence policy for this campaign.
- [LCFP-P01 inventory](../../research/label_compute_fast_path_v1/inventory/inventory.md)
  records the reference label engine, current fast-label surface, FUTSUB label
  needs, guard, availability, overlap, registry, and parity-harness contracts.
- [LCFP-P01 baseline](../../research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md)
  records the bounded reference-engine timing denominator for later comparison.

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

## Handoffs

Commit-eligible phase handoffs live under
`handoffs/LABEL_COMPUTE_FAST_PATH_V1/`.

- `LCFP-P00.md` records this bootstrap phase.
- `LCFP-P01.md` records the inventory and bounded baseline benchmark phase.
- `FUTSUB_PAUSE_STATE.md` records the paused predecessor state and preserves the
  rule that reintegration/resume is coordinator-owned after LCFP-P09.
