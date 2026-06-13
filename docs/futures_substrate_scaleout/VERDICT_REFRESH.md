# Verdict Refresh

`FUTSUB-P29` refreshes the Core Pilot promotion boundary after the
`FUTSUB-P27` re-lock and `FUTSUB-P28` rerun evidence. It is a value-free
documentation artifact. It does not re-run diagnostics, materialize values,
change StudySpecs, tune parameters, promote a study outside the allowed
research states, or create paper/live/broker/deployment behavior.

Allowed states for this refresh are only `REJECT`, `INCONCLUSIVE`, `WATCH`, and
`CANDIDATE_RESEARCH`.

## Updated Boundary

| Boundary | `REJECT` | `INCONCLUSIVE` | `WATCH` | `CANDIDATE_RESEARCH` |
| --- | ---: | ---: | ---: | ---: |
| Inherited Core Pilot | 4 | 6 | 0 | 0 |
| Refreshed after P29 | 10 | 0 | 0 | 0 |
| Change | +6 | -6 | 0 | 0 |

The four prior cross-market `REJECT` states are unchanged audit-only inputs.
The six studies rerun by `FUTSUB-P28` now receive `REJECT` because the
substrate gap was removed and the deterministic rerun evidence did not support
`WATCH` or `CANDIDATE_RESEARCH`.

No independent `WATCH` or `CANDIDATE_RESEARCH` reviewer artifact is attached by
this executor because no refreshed study received those states. The Workflow 2
driver still owns the Yellow-lane review after this executor handoff.

## Refreshed Rerun States

| V2 StudySpec | Family | Refreshed state | P28 evidence basis |
| --- | --- | --- | --- |
| `sspec_dec89a327a9c50957adca780` | `regime` | `REJECT` | Resolver-clean rerun; `DIAGNOSTICS_COMPLETE`; `72,441` numeric pairs; rank IC `-0.0002`; `67` walk-forward folds; label gate caveat retained. |
| `sspec_840e8342564226f2c3257903` | `liquidity_pa` | `REJECT` | Resolver-clean rerun; `DIAGNOSTICS_COMPLETE`; `72,595` numeric pairs; rank IC `0.0008`; `67` walk-forward folds; label gate and duplicate-exposure caveats retained. |
| `sspec_c237c6a8ce40c2585836fae0` | `liquidity_pa` | `REJECT` | Same aggregate diagnostics as the paired liquidity/PA rerun; duplicate exposure is retained as context, not independent survivor evidence. |
| `sspec_533f665ec4ac063dbb664a54` | `bbo_tradability` | `REJECT` | Resolver-clean rerun; `DIAGNOSTICS_COMPLETE`; `66,877` numeric pairs; rank IC `0.0008`; `61` walk-forward folds; BBO proxy caveat retained. |
| `sspec_1604b063f3a3401208ee0239` | `vwap_session` | `REJECT` | Resolver-clean rerun; `DIAGNOSTICS_COMPLETE`; `66,067` numeric pairs; rank IC `-0.0011`; `61` walk-forward folds; label gate and duplicate-exposure caveats retained. |
| `sspec_f6cbd88caa0445f0f56d81fd` | `vwap_session` | `REJECT` | Same aggregate diagnostics as the paired VWAP/session rerun; duplicate exposure is retained as context, not independent survivor evidence. |

All six P28 label diagnostics loaded label rows and numeric outcomes with
complete locked-horizon coverage, but the label diagnostics builder returned
`DIAGNOSTICS_FAILED` with `weak_diagnostics` at
`label_coverage_missingness_gate` because no separate feature/label audit
bundle was supplied. That caveat remains explicit and is not treated as a clean
label-diagnostics pass. The P28 N_eff context is first-order horizon-overlap
metadata over registered label rows, not a session-clustered or
autocorrelation-adjusted count, and it must not be conflated with the capped
factor-diagnostics observation samples.

## Evidence Summary

The scaleout campaign removed the Core Pilot substrate blocker without
broadening scope:

- DatasetVersion acceptance-lock records exact local registry resolution and
  accepted/warned/blocked yearly DatasetVersion states:
  `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md`.
- Feature coverage records all eight governed feature families over ES/NQ/RTY
  for 2019-2026, with `0` unexpected accepted-window gaps:
  `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`.
- Feature resolver smoke records exact-id `PASS` and fail-closed missing-lock
  behavior:
  `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`.
- Label resolver smoke records `1368/1368` current preview locks resolved and
  `0` current preview gaps:
  `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`.
- Label coverage records full accepted-window label coverage and horizon/N_eff
  provenance while preserving the rows-vs-effective-samples distinction:
  `docs/futures_substrate_scaleout/LABEL_COVERAGE.md`.
- Roll and maintenance guards record approximate roll-window handling and zero
  silently measured crossings:
  `docs/futures_substrate_scaleout/ROLL_GUARD.md` and
  `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`.
- BBO and cross-market matrices preserve BBO proxy limits and strict
  cross-market availability discipline:
  `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`.
- Walk-forward and N_eff surfaces preserve purge/embargo metadata and
  fail-closed overlap reporting:
  `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md` and
  `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`.
- P28 rerun diagnostics provide the direct value-free evidence for this refresh:
  `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`.

## Boundary

This page is not a FactorLibrary ingestion decision, Strategy Reference
validation, AlphaBook decision, paper/live/broker/order action, deployment
decision, capital-allocation decision, profitability claim, or tradability
claim. It records allowed research verdict states, counts, caveats, and
evidence references only.
