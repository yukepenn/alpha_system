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
campaign. This `FUTSUB-P23` executor snapshot completes the
`label_integration` gate (`FUTSUB-P21`...`FUTSUB-P23`): label guards are
audited, current LabelPack locks are integrated and resolver-smoke covered, and
the label substrate is now coverage-mapped cell by cell.

Active / next phase is Ralph-owned. The nominal next phase is `FUTSUB-P24` -
Purged / Embargo Walk-Forward Runtime Wiring, opening the
`wiring_and_matrices` gate (`FUTSUB-P24`...`FUTSUB-P26`) after Ralph validation
and Yellow-lane review complete.

New durable surfaces through this `FUTSUB-P23` executor snapshot:

- `docs/futures_substrate_scaleout/LABEL_COVERAGE.md` summarizes the
  value-free label coverage and horizon-quality context.
- `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`
  records the family x symbol x horizon x year matrix with explicit
  present/warned/expected-excluded/gap status.
- `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`
  records the symbol x horizon rollup across label families.
- `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md`
  records the session/guard x horizon coverage view.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P23.md`
  records validation, matrix counts, overlap provenance, gap classification,
  and artifact policy for coordinator use.

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
subset, and rows are not treated as independent samples for overlapping
horizons.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
