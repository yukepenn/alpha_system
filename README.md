# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is advancing
through the `family_diagnostics` group. `FUTCORE-P17` records value-free
VWAP/session diagnostics for the pilot's `vwap_session` StudySpec subset.

Active / next work: after `FUTCORE-P17` merges, Ralph continues the remaining
family diagnostics, consolidation, review routing, serial merge handling,
staging, PR, CI, merge, and done-check actions.

New durable surfaces through this `FUTCORE-P17` snapshot:

- `docs/futures_core_alpha_pilot/diagnostics/vwap_session.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/`

`FUTCORE-P17` adds value-free runtime diagnostics reports and a compact family
diagnostics doc. It adds no new commands, source primitives, feature values,
label values, data readers, agent runners, broker surfaces, live/paper behavior,
or deployment behavior.

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
