# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` is closed as historical context: it added
an opt-in reference-worker path, measured workers=8 at 2.14x for
`cost_adjusted`, and kept default reference workers at 1 outside the documented
FUTSUB-P19 resume deviation.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the active Workflow 2
campaign. This `FUTSUB-P27` executor snapshot opens the `rerun` gate
(`FUTSUB-P27`...`FUTSUB-P29`) by re-locking the Core Pilot StudySpecs against
the full futures substrate where the current registry and strict resolver make
them newly resolvable. The StudySpec resolver-smoke recorded in the re-lock
report resolved 8 re-issued StudySpecs and preserved 2 named fail-closed gaps.

Active / next phase is Ralph-owned. Until Ralph validates, reviews, and merges
this executor snapshot, `FUTSUB-P27` remains the nominal active phase. After
merge, the nominal next phase is `FUTSUB-P28` - Re-run Previously INCONCLUSIVE
Core Pilot Studies.

New durable surfaces through this `FUTSUB-P27` executor snapshot:

- `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md` records
  the value-free re-lock evidence, old-to-new StudySpec mapping, resolver-smoke
  counts, P28 rerun list, and named remaining gaps.
- `research/futures_substrate_scaleout_v1/rerun/study_specs/` contains the
  re-issued value-free StudySpec lock documents.
- `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md` documents the bounded
  re-lock contract, fixed fields, re-issued fields, and fail-closed gap policy.
- `tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py`
  hermetically validates the committed re-lock artifacts without
  `ALPHA_DATA_ROOT` or local registries.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P27.md`
  records validation, changed paths, and artifact policy for coordinator use.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Value-free research evidence root:
  `research/reference_label_parallel_compute_v1/`
- Commit-eligible handoffs:
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root: `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle. Registry
writes remain parent-only and serial. Label values, registries, manifests,
checkpoints, roll-calendar data, and SQLite files stay local-only under
`ALPHA_DATA_ROOT`; labels must never silently cross a quarterly roll or the
daily maintenance / trade-date break. The roll calendar is analytic and
approximate, not provider-exact splice truth. Resolver semantics remain exact-id
with no fuzzy fallback; P22 also verifies deprecated exact-id refs fail closed.
P23 records coverage gaps explicitly rather than accepting the substrate by
subset. P24 exposes walk-forward fold metadata but does not treat rows as
independent samples for overlapping horizons. P25 adds N_eff as a reporting
input only; full multiple-testing / DSR / PBO / PSR governance remains deferred
to `ALPHA_VALIDATION_GOVERNANCE_V1`. P27 re-locks existing Core Pilot
StudySpecs only; it does not create new alpha ideas, tune parameters, run
diagnostics, materialize values, mutate registries, or weaken the strict
resolver.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
