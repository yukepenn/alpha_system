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
campaign. This `FUTSUB-P25` executor snapshot continues the
`wiring_and_matrices` gate (`FUTSUB-P24`...`FUTSUB-P26`) by adding
overlap-aware N_eff reporting with an explicit rows-vs-effective-samples
distinction to the runtime diagnostics surface.

Active / next phase is Ralph-owned. Until Ralph validates, reviews, and merges
this executor snapshot, `FUTSUB-P25` remains the nominal active phase. After
merge, the nominal next phase is `FUTSUB-P26` - BBO Quality and Cross-Market
Alignment Matrices; `FUTSUB-P27` also depends on this phase's N_eff metadata for
the Core Pilot re-lock path.

New durable surfaces through this `FUTSUB-P25` executor snapshot:

- `src/alpha_system/runtime/diagnostics/splits/walk_forward.py` provides the
  value-free split-plan callable path over the existing experiment primitives.
- `src/alpha_system/runtime/diagnostics/factor/runtime.py` accepts opt-in
  `walk_forward_config` and emits fold metadata or a visible inconclusive
  reason when requested.
- `src/alpha_system/runtime/diagnostics/splits/n_eff.py` provides the
  deterministic overlap-aware N_eff estimator, session/day aggregation hooks,
  and P24 fold-metadata attachment helpers.
- `src/alpha_system/runtime/diagnostics/label/runtime.py` accepts opt-in
  N_eff metadata and emits `label_n_eff_report` without changing default label
  diagnostics calls.
- `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md` summarizes the P24
  runtime wiring, protocol hooks, and deferred statistical scope.
- `docs/futures_substrate_scaleout/N_EFF.md` documents the estimator,
  rows-vs-effective-samples report contract, session/day hooks, and
  Validation Governance handoff shape.
- `research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md`
  records the value-free wiring smoke case.
- `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
  records the value-free synthetic N_eff sample evidence.
- `tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py` covers the
  estimator, fail-closed behavior, aggregation hooks, fold attachment, label
  report integration, backward compatibility, and determinism.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P25.md`
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
to `ALPHA_VALIDATION_GOVERNANCE_V1`.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
