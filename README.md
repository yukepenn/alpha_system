# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is active.
`FUTCORE-P07` of `FUTCORE-P00` through `FUTCORE-P30` is complete for this
post-merge snapshot and adds the cross-market AlphaSpec batch within the
parallel `alpha_specs` wave. The `foundation` merge group /
`bootstrap_and_inputs` gate is complete through `FUTCORE-P06`.

Active / next work: `FUTCORE-P07` is done. The next work is the remaining
`FUTCORE-P08` through `FUTCORE-P11` AlphaSpec family batches, followed by
`FUTCORE-P12` AlphaSpec Critic and Family Budget Audit.

New durable surfaces through `FUTCORE-P07`:

- `docs/futures_core_alpha_pilot/README.md`
- `docs/futures_core_alpha_pilot/OVERVIEW.md`
- `docs/futures_core_alpha_pilot/PREFLIGHT.md`
- `docs/futures_core_alpha_pilot/SCOPE.md`
- `docs/futures_core_alpha_pilot/INPUT_PACK.md`
- `docs/futures_core_alpha_pilot/COST_MODEL.md`
- `docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
- `docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md`
- `research/futures_core_alpha_pilot_v1/README.md`
- `research/futures_core_alpha_pilot_v1/.gitkeep`
- `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`
- `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`
- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`
- `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/README.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/`
- `research/futures_core_alpha_pilot_v1/queue/`
- `docs/futures_core_alpha_pilot/alpha_specs/cross_market.md`

No new commands, modules, runtime behavior, data readers, diagnostics, cost
calculations, reviews, agent runners, or broker surfaces are added by
`FUTCORE-P07`. The cross-market AlphaSpec drafts are value-free research
evidence only and remain subject to independent critique in `FUTCORE-P12`.

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
