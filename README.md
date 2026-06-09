# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer and live Workflow 2 state are
coordinator-owned. For current in-flight status, run
`python tools/frontier/status_doctor.py` rather than relying on committed
snapshot text.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is through executor work for
`FUTSUB-P14`, entering the `feature_integration` gate. The eight governed
FeaturePack families have local V1 fast-engine materialization evidence,
registry consistency evidence, and resolver-smoke evidence with representative
locks resolving to Parquet-backed registry rows. Phase review and final verdict
remain Workflow 2 responsibilities.

Active / next phase: active `FUTSUB-P14` - FeaturePack Registry Integration,
Coverage Audit, and Resolver Smoke. Next `FUTSUB-P15` - Feature Coverage Matrix
and Quality Report.

New durable surfaces in this `FUTSUB-P14` executor snapshot:

- `docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md` records the
  value-free FeaturePack integration and resolver contract.
- `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`
  records the value-free registry consistency audit.
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
  records the value-free resolver-smoke evidence.
- `tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py`
  gates exact feature-lock resolution, current Parquet sidecar evidence, and
  fail-closed absent-lock behavior.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate docs: `docs/futures_substrate_scaleout/`
- Feature scaleout configs: `configs/features/scaleout/`
- V1 fast producer engine: `src/alpha_system/features/fast/`
- Feature scaleout driver: `src/alpha_system/features/scaleout/driver.py`
- Value-free research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The reference feature/label engine remains the parity oracle. Resolver exact-id
semantics, official keystone registry writes, and serial registry writes are
preserved; worker processes compute values only and never write SQLite registry
rows. The fast engine produces values for existing governed identities, and
producer provenance does not enter identity. No manual SQLite write,
paper/live/broker/order behavior, or profitability/tradability claim is
authorized. Feature/label values and registries remain local-only under
`ALPHA_DATA_ROOT`. The campaign uses Green/Yellow scope only and introduces no
Red scope.

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
