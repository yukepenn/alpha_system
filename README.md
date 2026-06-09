# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`FEATURE_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `FEATURE_COMPUTE_FAST_PATH_V1` has the P01 V1
engine core, governed feature packs through `cross_market`, the governed
fixed-horizon label pack, targeted / incremental scaleout selection, producer
provenance reconciliation, and the `FCFP-P13` bounded benchmark gate available
in this worktree. Ralph owns validation, staging, Yellow-lane review routing,
and any phase verdict.

Active / next integration path after P13 review and merge: `FCFP-P14` V1
Producer Path Integration + Resolver Smoke, then `FCFP-P15` Closeout + FUTSUB
Resume Handoff. Remaining phases merge serially.

New durable surfaces in this `FCFP-P13` executor snapshot:

- `tools/feature_compute_fast_path/benchmark_gate.py`, a bounded-real benchmark
  entrypoint that invokes the real reference runners and V1 pack runners on a
  self-validating roll-month slice.
- `research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`, a
  value-free benchmark summary with timing, throughput, scan-reduction,
  speedup, extrapolation, and real-data parity confirmation fields.
- `docs/feature_compute_fast_path/BENCHMARK_GATE.md`, documenting how to back up
  the local registry, run the bounded benchmark, and interpret the summary.
- Synthetic benchmark-harness tests under
  `tests/unit/feature_compute_fast_path/`.
- No full-window backfill, feature/label value artifact, broker/live/paper
  behavior, deployment behavior, or alpha/profitability claim is added.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/`
- Fast-path docs: `docs/feature_compute_fast_path/`
- Fast-path engine core: `src/alpha_system/features/fast/`
- Fast-path parity tests: `tests/unit/feature_compute_fast_path/`
- Value-free research evidence root:
  `research/feature_compute_fast_path_v1/`
- Commit-eligible handoffs:
  `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The reference feature/label engine remains the correctness oracle. Resolver
exact-id semantics, official keystone registry writes, and serial registry writes
are preserved. The fast engine produces values for existing governed identities;
it never mints V1-specific feature ids or label ids, and producer provenance
does not enter identity. Existing valid reference outputs remain preserved and
reconciled by policy; no manual SQLite write, paper/live/broker/order behavior,
or profitability/tradability claim is authorized. Feature/label values and
registries remain local-only under `ALPHA_DATA_ROOT`. Polars remains an optional
dependency guarded by `require_dependency("polars")`. The campaign uses
Green/Yellow scope only and introduces no Red scope.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data, feature
or label values, provider responses, heavy artifacts, local databases, logs,
caches, secrets, and credentials are never committed.

This campaign makes no profitability or tradability claim. Research outputs are
evidence for review only.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
