# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`DISCOVERY_RIGOR_FLOOR_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress after the `RIGOR-P00` merge: `RIGOR-P00` is the
bootstrap and boundary-state record; the active / next phase is `RIGOR-P01`,
Reason-Code Taxonomy + Ledger-Presence Gates + Annotations.

New durable surfaces through `RIGOR-P00`:

- `research/discovery_rigor_floor_v1/` defines the value-free evidence root for
  gate inventories, canary pass/fail tables, calibration statistics, and
  readiness records.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_BOUNDARY_STATE.md` records the
  FUTSUB boundary state at the P27/P28 gate.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P00.md` records the executor
  verification and handoff for this phase.

The gated FUTSUB run
`2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` remains
stopped before FUTSUB-P28. It resumes only after
`DISCOVERY_RIGOR_FLOOR_V1` closes and the coordinator follows the RIGOR-P07
resume handoff.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/DISCOVERY_RIGOR_FLOOR_V1/`
- Value-free research evidence root:
  `research/discovery_rigor_floor_v1/`
- Commit-eligible handoffs:
  `handoffs/DISCOVERY_RIGOR_FLOOR_V1/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

RIGOR-P00 is docs-only: no governance code, tests, historical Core Pilot
artifacts, FUTSUB research artifacts, run state, registries, values, or
worktrees are changed by this phase.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
