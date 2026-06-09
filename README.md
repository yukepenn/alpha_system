# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `FUTSUB-P15` is complete. The `feature_integration`
gate (`FUTSUB-P14` through `FUTSUB-P15`) is closed with the V1 feature
substrate materialized and integrated, resolver-smoke discipline preserved, and
feature-family coverage mapped cell-by-cell.

Active / next phase: `FUTSUB-P16` - Fixed-Horizon LabelPack Scaleout, opening
the `label_materialization` gate (`FUTSUB-P16` through `FUTSUB-P20`).

New durable surfaces in this `FUTSUB-P15` executor snapshot:

- `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md` records the value-free
  coverage summary and downstream consumption contract.
- `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
  records the machine-reviewable feature-family coverage matrix, registered row
  count context, quality/missingness summary, BBO flag rates, and explicit gap
  list.
- No production code, tests, materialization, label values, feature values,
  benchmark, broker/live/paper behavior, deployment behavior, or
  alpha/profitability claim is added.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate docs: `docs/futures_substrate_scaleout/`
- Feature coverage matrix:
  `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
- Value-free research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The reference feature/label engine remains the correctness oracle. Resolver
exact-id semantics, official keystone registry writes, and serial registry
writes are preserved; worker processes compute values only and never write
SQLite registry rows. The fast engine produces values for existing governed
identities; it never mints V1-specific feature ids or label ids, and producer
provenance does not enter identity. Existing valid reference outputs remain
preserved and reconciled by policy; no manual SQLite write,
paper/live/broker/order behavior, or profitability/tradability claim is
authorized. Feature/label values and registries remain local-only under
`ALPHA_DATA_ROOT`. Polars remains an optional dependency guarded by
`require_dependency("polars")`. The campaign uses Green/Yellow scope only and
introduces no Red scope.

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
