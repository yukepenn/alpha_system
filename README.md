# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is in the
`bootstrap_and_inputs` gate. This snapshot records `FUTCORE-P03`, which locks
the registry-resolved DatasetVersion, Parquet FeaturePack, and Parquet
LabelPack references by id/hash/pointer metadata only.

Active / next work: the active phase is `FUTCORE-P03`; the next phase is
`FUTCORE-P04`, CostModelVersion and session-specific cost stress contract.
Ralph continues to own authoritative validation, review routing, staging, PR,
CI, merge, and done-check actions.

New durable surfaces in this `FUTCORE-P03` snapshot:

- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `research/futures_core_alpha_pilot_v1/input_pack/`

`FUTCORE-P03` adds no new modules, commands, source primitives, feature values,
label values, data readers, agent runners, or broker surfaces.

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
