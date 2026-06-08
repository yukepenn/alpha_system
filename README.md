# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`FEATURE_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `FEATURE_COMPUTE_FAST_PATH_V1` has `1/16` phases
complete after `FCFP-P00` Campaign Bootstrap and Active Pointer. `FCFP-P01`
executor work is present in the working tree and still requires Ralph
validation, staging, and fresh Yellow-lane review before it can be marked
complete.

Active / next phase: `FCFP-P01` V1 Engine Core + Reference-Parity Harness. The
root `ACTIVE_CAMPAIGN.md` pointer selects `FEATURE_COMPUTE_FAST_PATH_V1` and
records `FCFP-P01` as the active phase. The next build phase after P01
acceptance is `FCFP-P02` base_ohlcv Polars Pack + Parity.

New durable surfaces in this `FCFP-P01` executor snapshot:

- `PackMaterializer`, `FastFeaturePack`, and `FastFeatureDeclaration` under
  `src/alpha_system/features/fast/`
- Synthetic reference-parity harness under
  `tests/unit/feature_compute_fast_path/`
- Tiny documented synthetic fixtures under
  `tests/fixtures/feature_compute_fast_path/`
- Fast-path engine contract docs under `docs/feature_compute_fast_path/`
- Value-free evidence-directory skeleton under
  `research/feature_compute_fast_path_v1/`
- No production family pack, CLI command, real-data backfill, benchmark,
  feature/label value artifact, broker/live/paper behavior, or heavy artifact was
  added in this phase.

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
are unchanged. The campaign uses Green/Yellow scope only and introduces no Red
scope.

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
