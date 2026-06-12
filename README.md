# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`DISCOVERY_RIGOR_FLOOR_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress after `RIGOR-P07`: `RIGOR-P00` through `RIGOR-P07`
are complete in the campaign snapshot, pending Ralph-owned closeout review,
staging, commit, PR/CI, merge, and done-check handling. The active / next
campaign action is closeout review and done-check; FUTSUB kill-shot resume is a
coordinator step after campaign completion per
`handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md`.

New durable surfaces through `RIGOR-P07`:

- `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py` drives
  one synthetic study through the full gate stack and proves both happy and
  fail-closed directions.
- `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`
  records the value-free gate-to-bypass-canary table.
- `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` is the
  fail-closed kill-shot readiness checklist, including compass v4.4
  preconditions and the surrogate-calibration statistical floor.
- `docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md` maps the
  Track-B pre-registration payload field-for-field to
  `PooledHypothesisRecord`.
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` gives the
  coordinator-only ordered FUTSUB resume path.
- `docs/OPERATING_COMPASS_V4.md` now has the additive Stage B status note with
  `MET` and `PENDING-coordinator` readiness statuses.
- Earlier RIGOR surfaces remain in force: reason-code validation,
  trial-ledger and VariantLedger gates, sealed holdout and access log,
  executable 4/4 negative controls, planted-fake-alpha canary, surrogate-FDR
  machinery, and evidence-accrual requeue scan.

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
RIGOR-P05 is governance/calibration machinery only: surrogate study outputs,
shuffled labels, ledgers, and scratch registries are local-only isolated
namespace artifacts; the committed report is value-free and makes no alpha,
profitability, tradability, or production-readiness claim.
RIGOR-P04 is governance-only: it uses tiny synthetic fixtures, tmp namespaces,
and value-free pass/fail evidence to close the negative-control canary floor;
it does not run real-data studies, mutate production registries or ledgers, or
produce any score/value claim.
RIGOR-P07 is closeout-only: the integration audit uses pytest tmp namespaces,
and the readiness checklist, Track-B template, compass note, and FUTSUB resume
handoff are value-free coordinator artifacts. It does not resume FUTSUB, remove
STOP files, register Track B, run real-data studies, inspect Track A metrics, or
touch values, registries, broker surfaces, execution engines, or worktrees.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The requeue power estimator is planning-only and never a promotion gate. This
campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
