# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` has reached fixed-horizon
LabelPack scaleout. `FUTSUB-P16` is active in the `label_materialization` gate.

Active / next phase: active `FUTSUB-P16` - Fixed-Horizon LabelPack Scaleout.
Next are the remaining `label_materialization` phases, starting with
`FUTSUB-P17` extended horizons.

New durable surfaces in this `FUTSUB-P16` executor snapshot:

- `src/alpha_system/labels/roll_guard.py` is wired into the shared
  fixed-horizon label terminal-resolution path.
- `alpha scaleout label-pack` provides a thin reference-engine dispatch through
  the existing scaleout driver and `run_seed_label_pack`.
- `configs/labels/scaleout/fixed_horizon.json` defines the fixed-horizon
  LabelPack scaleout grid and guard policy.
- `research/futures_substrate_scaleout_v1/label_packs/fixed_horizon/coverage_summary.md`
  records the value-free horizon coverage and guard summary.

The repository-level campaign pointer and live Workflow 2 state are
coordinator-owned. For current in-flight status, run
`python tools/frontier/status_doctor.py` rather than relying on committed
snapshot text.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate docs: `docs/futures_substrate_scaleout/`
- Feature coverage matrix:
  `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
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

The reference feature/label engine remains the parity oracle. Fast path !=
Reference truth. BBO proxy != execution truth. Approximate roll calendar !=
provider-exact. Resolver exact-id semantics, official keystone registry writes,
and serial registry writes are preserved; worker processes compute values only
and never write SQLite registry rows. Producer provenance does not enter
identity. No manual SQLite write, paper/live/broker/order behavior, or
profitability/tradability claim is authorized. Feature/label values and
registries remain local-only under `ALPHA_DATA_ROOT`. The campaign uses
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
