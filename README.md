# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is active.
`FUTCORE-P11` records the value-free BBO tradability / top-book confirmation
AlphaSpec draft batch and completes the five-family AlphaSpec batch wave
(`FUTCORE-P07` through `FUTCORE-P11`) for downstream independent critique.

Active / next work: `FUTCORE-P12` is the next phase and owns AlphaSpec Critic
review plus the family budget audit. Ralph continues to own authoritative
validation, review routing, serial merge handling, staging, PR, CI, merge, and
done-check actions.

New durable surfaces through this `FUTCORE-P11` snapshot:

- `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/`
- `docs/futures_core_alpha_pilot/alpha_specs/bbo_tradability.md`

No new commands, modules, runtime behavior, data readers, diagnostics, cost
calculations, reviews, agent runners, or broker surfaces are added by
`FUTCORE-P11`. The BBO batch records draft AlphaSpec payloads, assumptions,
limitations, and diagnostic declarations only.

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
