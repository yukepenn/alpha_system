# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is active. The
`bootstrap_and_inputs` gate is complete through `FUTCORE-P06`. `FUTCORE-P10`
is complete as the Liquidity Sweep / PA AlphaSpec batch and as one
path-disjoint member of the parallel `alpha_specs` wave.

Active / next work: the remaining `alpha_specs` family batches (`FUTCORE-P07`,
`FUTCORE-P08`, `FUTCORE-P09`, and `FUTCORE-P11` as applicable) continue under
Workflow 2 review and serial merge handling, followed by `FUTCORE-P12`
AlphaSpec Critic and Family Budget Audit.

New durable surfaces in `FUTCORE-P10`:

- `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/`
- `docs/futures_core_alpha_pilot/alpha_specs/liquidity_pa.md`

`FUTCORE-P10` adds value-free liquidity/PA AlphaSpec drafts and the family
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
