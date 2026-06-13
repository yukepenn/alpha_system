# FactorLibrary Requirement Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Downstream campaign: `ALPHA_FACTOR_LIBRARY_V1`  
Prepared in: `FUTSUB-P32`  
Artifact class: value-free requirement handoff

This handoff defines what `ALPHA_FACTOR_LIBRARY_V1` may consume from FUTSUB and
what it must still build. It is not a FactorLibrary implementation, does not
create FactorCards, does not ingest survivors, does not re-run diagnostics, and
does not change any verdict.

## Current Ingestion State

FUTSUB-P29 is the only verdict-refresh source cited here. Its refreshed
boundary is:

| State | Count |
| --- | ---: |
| `REJECT` | 10 |
| `INCONCLUSIVE` | 0 |
| `WATCH` | 0 |
| `CANDIDATE_RESEARCH` | 0 |

Therefore the current FUTSUB campaign provides no FactorLibrary-ingestible
survivor. `ALPHA_FACTOR_LIBRARY_V1` should record this as a no-entry /
ingestion-gap condition if it consumes FUTSUB, not as draft factor entries.

The no-survivor state is cited from
`research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md` and
`docs/futures_substrate_scaleout/VERDICT_REFRESH.md`. This handoff does not
re-judge those states and does not promote any study.

## Boundary

FactorLibrary V1 is a downstream ingestion, query, lifecycle, and memory layer
over already-reviewed research evidence. It must not become a new compute
engine, a mining campaign, Strategy Reference validation, AlphaBook allocation,
paper/live/broker/order logic, or production deployment.

Rejected or non-surviving FUTSUB evidence may be used only as requirements and
negative memory. Rejection memory alone does not justify a full FactorLibrary
buildout unless a separate campaign explicitly accepts that trigger.

All consumed evidence must remain value-free by reference. Do not copy raw
market data, canonical data, feature values, label values, Parquet payloads,
SQLite registry content, local paths, provider payloads, run-local artifacts, or
per-row diagnostics into FactorLibrary artifacts.

## Required Ingestion Eligibility

Before FactorLibrary V1 may ingest any candidate from FUTSUB or a later
FUTSUB-derived campaign, it must require:

1. An allowed research state of `WATCH` or `CANDIDATE_RESEARCH` from a reviewed
   verdict artifact.
2. A reviewer-accepted evidence bundle for any `WATCH` or `CANDIDATE_RESEARCH`
   state.
3. A Validation Governance decision or explicit governance status covering the
   study population, multiple-testing / false-discovery policy, locked-test
   policy, contamination ledger, negative controls, and survivor-statistics
   requirements.
4. Exact StudySpec, AlphaSpec, feature-lock, label-lock, dataset-version, and
   registry identity references. Fuzzy name matching or feature-family fallback
   must fail closed.
5. Coverage and quality matrix references for every feature family, label
   surface, symbol, horizon, session segment, and year used by the evidence.
6. Guard provenance for roll-splice and maintenance-crossing policies, including
   explicit dropped-window handling and zero silent-crossing evidence.
7. N_eff and walk-forward fold metadata where any overlapping horizon is used.
8. Cost model and BBO proxy context for any cost-adjusted or BBO-dependent
   evidence.
9. Duplicate-exposure grouping for paired or within-family near-duplicate
   studies.
10. Artifact-locality confirmation that no value, registry, provider, DB, heavy,
    or run-local artifact is committed as part of ingestion.

For FUTSUB as of P32, requirement 1 is not satisfied because P29 has zero
`WATCH` and zero `CANDIDATE_RESEARCH` states.

## FactorCard / EvidenceBundle Minimum Fields

When a future eligible survivor exists, FactorLibrary V1 should require an
EvidenceBundle that records at least:

| Field class | Required content |
| --- | --- |
| Campaign lineage | Source campaign id, phase id, handoff path, verdict path, review path, and evidence-generation timestamp when available. |
| Research identity | AlphaSpec id, StudySpec id, StudyInputPack refs, split protocol, metric surface, cost model id, stopping rules, and variant budget. |
| Dataset locks | DatasetVersion ids, acceptance state, symbol, year, schema, warning state, and explicit 2018 exclusion handling when relevant. |
| Feature locks | Exact `feature_version_id` refs, feature family, FeatureRequest id, DatasetVersion id, partition id, value-store format, content-hash provenance, producer engine provenance, and `available_ts` contract. |
| Label locks | Exact `label_version_id` refs, label family, horizon or terminal event, DatasetVersion id, partition id, value-store format, content-hash provenance, `label_available_ts` contract, and guard provenance. |
| Coverage context | Feature-family, label-family, symbol-horizon, session-horizon, BBO-quality, cross-market-alignment, roll-window, and maintenance-crossing matrix refs. |
| Diagnostics context | Runtime status, rows, numeric pairs or outcomes, coverage, missingness, IC summaries or equivalent diagnostics, fold counts, reason codes, and residual caveats by path. |
| Statistical context | N_eff metadata, fold metadata, duplicate-exposure group, governance correction status, negative-control status, and locked-test contamination status. |
| Interpretation limits | Explicit no-profitability, no-tradability, no-production, no-paper/live/broker, and no-capital-allocation language. |

FactorCard records must link to EvidenceBundle records by stable ids and paths;
they must not embed value payloads.

## Required FUTSUB Inputs By Path

Substrate and resolver evidence:

- `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md`
- `docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `docs/futures_substrate_scaleout/LABEL_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`

Coverage and quality matrices:

- `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`
- `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
- `docs/futures_substrate_scaleout/LABEL_COVERAGE.md`
- `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md`
- `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`
- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`

Walk-forward, N_eff, rerun, and verdict evidence:

- `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md`
- `research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md`
- `docs/futures_substrate_scaleout/N_EFF.md`
- `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md`
- `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`
- `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`
- `docs/futures_substrate_scaleout/VERDICT_REFRESH.md`
- `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`

Governance and artifact locality:

- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/VALIDATION_GOVERNANCE_HANDOFF.md`
- `docs/futures_substrate_scaleout/HANDOFF_VALIDATION_GOVERNANCE.md`
- `docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md`
- `research/futures_substrate_scaleout_v1/closeout/artifact_audit.md`

## Required Downstream Outputs

If `ALPHA_FACTOR_LIBRARY_V1` consumes FUTSUB, it should produce:

- a FUTSUB no-entry / ingestion-gap report for the current P29 no-survivor
  boundary;
- a FactorCard schema or schema mapping that includes the minimum fields above;
- an EvidenceBundle schema or schema mapping with value-free path references;
- an exact-id ingestion validator over StudySpec, feature, label, dataset, and
  verdict references;
- duplicate-exposure grouping and query requirements;
- an as-of snapshot contract that preserves point-in-time evidence and lifecycle
  state without fuzzy fallback;
- a lifecycle rule that forbids live, production, paper, broker, order, or
  capital-allocation states;
- a query surface for no-entry, rejected, watch, and candidate research records
  that keeps rejection memory separate from candidate ingestion.

## Explicit Non-Claims

This handoff makes no alpha, profitability, robustness, tradability,
production, paper/live, broker, order-routing, deployment, or
capital-allocation claim. It starts no FactorLibrary ingestion and creates no
FactorCard.

