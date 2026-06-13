# FactorLibrary And Multi-Horizon Mining Evidence Index

Phase: `FUTSUB-P32`  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Artifact class: value-free closeout evidence index

This index lists the FUTSUB artifacts consumed by the P32 downstream handoffs.
It does not create FactorLibrary entries, start mining, run diagnostics,
materialize values, write registries, or change verdicts.

## P32 Outputs

| Artifact | Purpose |
| --- | --- |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FACTOR_LIBRARY_HANDOFF.md` | Requirements for `ALPHA_FACTOR_LIBRARY_V1`, including the current no-entry state for FUTSUB. |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/MULTI_HORIZON_MINING_HANDOFF.md` | Requirements for `ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1`, including consumable substrate and guard constraints. |
| `docs/futures_substrate_scaleout/HANDOFF_FACTOR_LIBRARY_AND_MINING.md` | Durable docs mirror for downstream consumption. |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P32.md` | Executor handoff and validation record. |

## Evidence Inputs

| Evidence class | Paths |
| --- | --- |
| Dataset acceptance | `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md`; `research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md`; `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md` |
| Feature integration | `docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`; `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`; `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md` |
| Feature coverage | `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`; `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md` |
| Label integration | `docs/futures_substrate_scaleout/LABEL_INTEGRATION.md`; `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`; `research/futures_substrate_scaleout_v1/label_packs/registry_integration_audit.md` |
| Label coverage | `docs/futures_substrate_scaleout/LABEL_COVERAGE.md`; `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`; `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`; `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md` |
| Guard matrices | `docs/futures_substrate_scaleout/ROLL_GUARD_AUDIT.md`; `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`; `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`; `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md` |
| BBO and cross-market matrices | `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`; `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`; `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md` |
| Walk-forward and N_eff | `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md`; `research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md`; `docs/futures_substrate_scaleout/N_EFF.md`; `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md` |
| Re-lock, rerun, verdict refresh | `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md`; `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`; `docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`; `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`; `docs/futures_substrate_scaleout/VERDICT_REFRESH.md`; `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md` |
| Governance and artifact locality | `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/VALIDATION_GOVERNANCE_HANDOFF.md`; `docs/futures_substrate_scaleout/HANDOFF_VALIDATION_GOVERNANCE.md`; `docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md`; `research/futures_substrate_scaleout_v1/closeout/artifact_audit.md` |

## Key Facts Carried Forward

- P29 refreshed boundary: `10 REJECT / 0 INCONCLUSIVE / 0 WATCH / 0
  CANDIDATE_RESEARCH`; current FUTSUB has no FactorLibrary-ingestible survivor.
- Feature coverage: 216 family / symbol / year cells, with 144 clean, 48
  warned, 24 expected-excluded, and 0 unexpected gaps.
- Label coverage: 1368 active locks; 729 rendered cells, with 486 clean, 162
  warned, 81 expected-excluded, and 0 unexpected gaps.
- Accepted mining window: 2019-2026 with 2019 and 2026 warning context; 2018 is
  expected-excluded.
- Roll and maintenance matrices record explicit dropped or bounded windows and
  zero silently measured crossings.
- BBO is a sampled and forward-filled top-book proxy, not execution truth.
- Cross-market substrate uses strict intersection; contributor gaps are
  availability context.
- N_eff and walk-forward metadata are reporting and split-context inputs, not
  significance tests or promotion rules.

## Artifact Boundary

This index is markdown-only and value-free. It contains ids, counts, states,
paths, and requirements only. Values, local registries, raw/canonical provider
data, Parquet payloads, SQLite databases, roll-calendar data, run-local state,
logs, caches, and scratch reports remain local-only and are not copied here.

