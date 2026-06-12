# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`DISCOVERY_RIGOR_FLOOR_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress after the `RIGOR-P04` merge:
`RIGOR-P00` through `RIGOR-P04` are complete, and `RIGOR-P06` has also landed
per the current campaign snapshot. The active / next phase is `RIGOR-P05`
(surrogate-FDR calibration), followed by `RIGOR-P07` closeout once the
remaining rigor-floor gates are merged.

New durable surfaces through `RIGOR-P03`:

- `research/discovery_rigor_floor_v1/` defines the value-free evidence root for
  gate inventories, canary pass/fail tables, calibration statistics, and
  readiness records.
- `src/alpha_system/governance/verdict_reason_code.py` defines the closed
  `VerdictReasonCode` taxonomy; `promotion_gate.py` requires a present,
  parseable, non-destructively writable trial ledger before `EVIDENCE_READY`.
- `research/futures_core_alpha_pilot_v1/verdict_annotations/` contains the six
  additive annotations for historical Core Pilot inconclusive verdicts.
- `research/discovery_rigor_floor_v1/RIGOR_P01_REASON_CODE_AND_LEDGER_GATES.md`
  records the value-free gate/test/annotation evidence for this phase.
- `src/alpha_system/governance/variant_ledger.py` defines first-class
  `VariantLedgerRecord` JSONL persistence, family budget roll-ups, and
  provenance-carrying budget amendments.
- `alpha governance variant-ledger-summary` provides a read-only ledger scan and
  optional family-budget status summary; `StudySpec.family_budget` remains
  optional for legacy StudySpec payloads.
- `research/discovery_rigor_floor_v1/RIGOR_P02_GATE_INVENTORY.md` records the
  value-free gate and bypass-test inventory.
- `src/alpha_system/governance/requeue.py`, `alpha governance requeue-scan`,
  and `research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md` provide the
  landed evidence-accrual requeue scan from `RIGOR-P06`.
- `src/alpha_system/governance/sealed_holdout.py` defines
  `SealedHoldoutWindow`, exactly-one-active declaration enforcement,
  terminal `BREACHED` transitions, and append-only `HoldoutAccessLog`
  persistence.
- The label leakage guard and study-entry budget hook can emit sealed-holdout
  access log records; missing or unwritable logs fail closed when those
  surfaces are armed.
- The governance `EVIDENCE_READY` transition now blocks locked-test
  contamination and BREACHED sealed-holdout declarations with no waiver path.
- `research/discovery_rigor_floor_v1/sealed_holdout/` contains the value-free
  initial kill-shot sealed-window declaration and RIGOR-P03 gate inventory.
- `src/alpha_system/governance/canaries/harness.py` now executes all four
  required negative controls in catalog order, including `RANDOM_TARGET`.
- `src/alpha_system/governance/canaries/planted_fake_alpha.py` provides the
  end-to-end planted lookahead canary; `tools/hooks/canary_runner.py` registers
  both `governance_random_target` and the expected-block `planted_fake_alpha`
  scenario.
- `validate_evidence_ready_gate` now requires current `PASS` results for all
  required negative controls before `EVIDENCE_READY`.
- `research/discovery_rigor_floor_v1/canary_floor/RIGOR-P04_canary_floor.md`
  records the value-free 4/4 canary inventory, planted-fake-alpha rejection,
  and gate-to-bypass-test mapping.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_BOUNDARY_STATE.md` records the
  FUTSUB boundary state at the P27/P28 gate.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P00.md` through `RIGOR-P03.md` and
  `RIGOR-P06.md` record executor verification and handoffs for completed
  landed phases; `RIGOR-P04.md` records this canary-floor phase.

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
RIGOR-P02 is governance-only: no historical Core Pilot artifacts, FUTSUB
research artifacts, run state, registries, values, broker surfaces, execution
engines, or worktrees are changed by this phase.
RIGOR-P03 is also governance-only: it declares and gates the sealed holdout
regime with value-free metadata and does not run, inspect, or mutate study
values, registries, FUTSUB run state, broker surfaces, or execution engines.
RIGOR-P04 is governance-only: it uses tiny synthetic fixtures, tmp namespaces,
and value-free pass/fail evidence to close the negative-control canary floor;
it does not run real-data studies, mutate production registries or ledgers, or
produce any score/value claim.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The requeue power estimator is planning-only and never a promotion gate. This
campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
