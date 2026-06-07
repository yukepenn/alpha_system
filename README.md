# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is active.
`FUTCORE-P03` of `FUTCORE-P00` through `FUTCORE-P30` is complete for this
post-merge snapshot and locks the registry-resolved DatasetVersion, FeaturePack,
and LabelPack input references for the pilot. The `foundation` merge group /
`bootstrap_and_inputs` gate remains in progress.

Active / next work: next phase is `FUTCORE-P04` - CostModelVersion and
Session-Specific Cost Stress Contract.

New durable surfaces through `FUTCORE-P03`:

- `docs/futures_core_alpha_pilot/README.md`
- `docs/futures_core_alpha_pilot/OVERVIEW.md`
- `docs/futures_core_alpha_pilot/PREFLIGHT.md`
- `docs/futures_core_alpha_pilot/SCOPE.md`
- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `research/futures_core_alpha_pilot_v1/README.md`
- `research/futures_core_alpha_pilot_v1/.gitkeep`
- `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`
- `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`
- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`

No new commands, modules, runtime behavior, data readers, diagnostics, or broker
surfaces are added by `FUTCORE-P03`.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`
- Pilot docs: `docs/futures_core_alpha_pilot/`
- Value-free pilot research evidence root:
  `research/futures_core_alpha_pilot_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

Artifact discipline is unchanged: explicit staging only; `runs/**` is
local-only and never committed; raw/canonical data, feature or label values,
provider responses, heavy artifacts, local databases, logs, caches, secrets, and
credentials are never committed.

The pilot makes no profitability or tradability claim. Research outputs are
evidence for review only, and later phases must keep value data and run-local
artifacts out of git.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
