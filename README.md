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
campaign. This `FUTSUB-P26` executor snapshot produces the BBO quality matrix
and cross-market alignment matrix, completing the `wiring_and_matrices` gate
(`FUTSUB-P24`...`FUTSUB-P26`) with value-free substrate quality and alignment
evidence.

Active / next phase is Ralph-owned. Until Ralph validates, reviews, and merges
this executor snapshot, `FUTSUB-P26` remains the nominal active phase. After
merge, the nominal next phase is `FUTSUB-P27` - Re-lock Core Pilot StudySpecs
Against Full Substrate.

New durable surfaces through this `FUTSUB-P26` executor snapshot:

- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md` records the
  value-free BBO quality matrix over registered P12 BBO FeaturePack values.
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`
  records the value-free cross-market state coverage, strict-intersection
  survival, and availability-discipline matrix over registered P13 values.
- `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`
  documents how P27...P29, Validation Governance, and future mining campaigns
  should consume the matrices.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P26.md`
  records validation, inputs, quality context, and artifact policy for
  coordinator use.

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
to `ALPHA_VALIDATION_GOVERNANCE_V1`. P26 keeps BBO as a time-sampled and
forward-filled tradability proxy, never execution truth, and records
cross-market `strict_intersection` alignment with per-instrument `available_ts`
discipline and no cross-instrument forward-fill.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
