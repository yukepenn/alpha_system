# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is active.
`FUTCORE-P09` records the regime-family AlphaSpec batch for the
`FUTCORE-P07` through `FUTCORE-P11` parallel AlphaSpec wave. The
`alpha_spec_batches` gate remains bounded by the serial review and merge queue
for the family batches.

Active / next work: Ralph owns authoritative validation, review routing, and
serial merge handling for `FUTCORE-P09`; the remaining AlphaSpec batch wave and
downstream `FUTCORE-P12` critique stay under Workflow 2 control.

New durable surfaces through `FUTCORE-P09`:

- `docs/futures_core_alpha_pilot/README.md`
- `docs/futures_core_alpha_pilot/OVERVIEW.md`
- `docs/futures_core_alpha_pilot/PREFLIGHT.md`
- `docs/futures_core_alpha_pilot/SCOPE.md`
- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `docs/futures_core_alpha_pilot/COST_MODEL.md`
- `docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
- `docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md`
- `docs/futures_core_alpha_pilot/alpha_specs/regime.md`
- `research/futures_core_alpha_pilot_v1/README.md`
- `research/futures_core_alpha_pilot_v1/.gitkeep`
- `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`
- `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`
- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`
- `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/README.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/regime/`
- `research/futures_core_alpha_pilot_v1/queue/`

`FUTCORE-P09` adds value-free regime AlphaSpec drafts and the regime family
index only. It adds no commands, modules, runtime behavior, data readers,
diagnostics, cost calculations, reviews, agent runners, or broker surfaces.

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
