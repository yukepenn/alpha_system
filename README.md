# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is
active. This snapshot reflects the post-merge state for `FUTSUB-P03`: the
Continuous Series / Roll Metadata / Roll-Splice Guard Contract within the
`bootstrap_and_contract` gate as phase 4 of 34. Ralph owns validation routing,
staging, commit, review routing, PR, CI, merge, and done-check actions.

Active / next work: the next phase is `FUTSUB-P04` - Value Store / Registry /
Keystone Identity Preflight.

New durable surfaces in this `FUTSUB-P03` snapshot:

- Approximate CME equity-index quarterly roll-calendar computation in
  `src/alpha_system/data/foundation/rolls.py`
- Roll-splice label guard primitive in `src/alpha_system/labels/roll_guard.py`
- `configs/data/roll_calendar/futsub_p03_roll_guard.json`
- `docs/futures_substrate_scaleout/ROLL_GUARD.md`
- `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_contract.md`

`FUTSUB-P03` adds no raw/provider data readers, feature or label materializers,
diagnostics, broker surfaces, live surfaces, paper-trading surfaces, order
routing, or deployment behavior. The roll calendar is analytic and approximate,
not provider-exact splice truth. Values, registries, and persisted
roll-calendar data remain local-only; committed evidence is value-free.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle:
  `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root:
  `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

Artifact discipline is unchanged: explicit staging only, value-free evidence
only, and runtime-tool-surface-only diagnostics. `runs/**` is local-only and
never committed. Raw or canonical data, feature or label values, provider
responses, heavy artifacts, local databases, roll-calendar data, logs, caches,
secrets, and credentials are never committed.

This campaign makes no profitability or tradability claim. Research outputs are
evidence for review only, and later phases must keep value data, local
registries, roll-calendar data, and run-local artifacts out of git.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
