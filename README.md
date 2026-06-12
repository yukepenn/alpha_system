# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`DISCOVERY_RIGOR_FLOOR_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress after the `RIGOR-P06` merge:
`DISCOVERY_RIGOR_FLOOR_V1` includes the evidence-accrual requeue scan for
UNDERPOWERED verdicts. The active / next phase is `RIGOR-P07`, Integration
Audit + Kill-Shot Readiness + Resume Handoff, after `RIGOR-P04`, `RIGOR-P05`,
and `RIGOR-P06` all merge.

New durable surfaces through `RIGOR-P01`:

- `research/discovery_rigor_floor_v1/` defines the value-free evidence root for
  gate inventories, canary pass/fail tables, calibration statistics, and
  readiness records.
- `src/alpha_system/governance/verdict_reason_code.py` defines the closed
  `VerdictReasonCode` taxonomy used by reason-coded inconclusive verdicts.
- `src/alpha_system/governance/promotion_gate.py` exposes
  `require_trial_ledger_present()` and invokes it on the
  `DIAGNOSTICS_RUN -> EVIDENCE_READY` path.
- `research/futures_core_alpha_pilot_v1/verdict_annotations/` contains the six
  additive annotations for historical Core Pilot inconclusive verdicts.
- `research/discovery_rigor_floor_v1/RIGOR_P01_REASON_CODE_AND_LEDGER_GATES.md`
  records the value-free gate/test/annotation evidence for this phase.
- `src/alpha_system/governance/requeue.py` defines
  `RequeuedVerdictRecord`, the planning-prior power estimator, and the
  deterministic evidence-accrual scan logic.
- `alpha governance requeue-scan` and `just requeue-scan` expose the manual,
  deterministic UNDERPOWERED retest-eligibility scan.
- `research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md` documents the
  declared materiality rule, input contract, and coordinator cadence.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_BOUNDARY_STATE.md` records the
  FUTSUB boundary state at the P27/P28 gate.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P01.md` records the executor
  verification and handoff for this phase.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P06.md` records the executor
  verification and handoff for the requeue scan phase.

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

RIGOR-P01 changes governance code, tests, value-free evidence, and additive
verdict annotations only. Historical Core Pilot evidence remains append-only:
the original reviewer verdicts, study specs, evidence, and ledgers are not
changed. FUTSUB research artifacts, run state, registries, values, and
worktrees remain untouched.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The requeue power estimator is planning-only and never a promotion gate. This
campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
