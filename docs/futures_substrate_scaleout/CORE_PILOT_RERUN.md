# Core Pilot Re-run Evidence

`FUTSUB-P28` is the bounded Core Pilot re-run step for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. It consumes the P110000 V2
StudySpec re-locks under
`research/futures_substrate_scaleout_v1/rerun/study_specs/` and does not edit
the original Core Pilot artifacts.

## Scope Boundary

This page is value-free. It records resolver and diagnostic execution metadata
only. It does not refresh `REJECT`, `INCONCLUSIVE`, `WATCH`, or
`CANDIDATE_RESEARCH` verdicts, does not promote any study, and does not make a
profitability, tradability, execution-quality, paper/live, broker, deployment,
or capital-allocation claim.

## Candidate Set

The P110000 V2 re-lock report made all six previously INCONCLUSIVE Core Pilot
studies re-runnable:

- `regime`: `sspec_dec89a327a9c50957adca780`
- `bbo_tradability`: `sspec_533f665ec4ac063dbb664a54`
- `liquidity_pa`: `sspec_840e8342564226f2c3257903`
- `liquidity_pa`: `sspec_c237c6a8ce40c2585836fae0`
- `vwap_session`: `sspec_1604b063f3a3401208ee0239`
- `vwap_session`: `sspec_f6cbd88caa0445f0f56d81fd`

The re-locked cross-market StudySpecs are prior-REJECT audit-only inputs in the
V2 report and were not rerun by this phase executor.

## What Ran Here

The repair replay ran under the research interpreter with
`ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`. The executor used
the sanctioned local runtime surfaces:

- DatasetVersion resolution through the local dataset registry.
- Feature and label lock resolution through
  `FeatureLabelPackResolver.resolve_feature_packs` and
  `resolve_label_packs`.
- Locked local Parquet feature and label value reads behind registered packs.
- Runtime factor and label diagnostics builders.
- N_eff reporting via `build_n_eff_sample_report`.

All six candidates were resolver-clean: each feature and label lock resolved to
a registered local pack, and every registered pack had an existing current
Parquet value-store manifest.

## Diagnostics Summary

Factor diagnostics completed for all six StudySpecs over real in-memory
observations joined from the locked local Parquet value stores. The replay used
all locked 5m, 10m, 15m, and 30m label horizons, required feature availability
before label availability, and exercised purge gap 10 / embargo gap 10
walk-forward folds.

| V2 StudySpec | Family | Factor status | Numeric pairs | Coverage | Rank IC | WF folds |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `sspec_dec89a327a9c50957adca780` | `regime` | `DIAGNOSTICS_COMPLETE` | 72,441 | 0.9712 | -0.0002 | 67 |
| `sspec_840e8342564226f2c3257903` | `liquidity_pa` | `DIAGNOSTICS_COMPLETE` | 72,595 | 0.9770 | 0.0008 | 67 |
| `sspec_c237c6a8ce40c2585836fae0` | `liquidity_pa` | `DIAGNOSTICS_COMPLETE` | 72,595 | 0.9770 | 0.0008 | 67 |
| `sspec_533f665ec4ac063dbb664a54` | `bbo_tradability` | `DIAGNOSTICS_COMPLETE` | 66,877 | 0.8920 | 0.0008 | 61 |
| `sspec_1604b063f3a3401208ee0239` | `vwap_session` | `DIAGNOSTICS_COMPLETE` | 66,067 | 0.8823 | -0.0011 | 61 |
| `sspec_f6cbd88caa0445f0f56d81fd` | `vwap_session` | `DIAGNOSTICS_COMPLETE` | 66,067 | 0.8823 | -0.0011 | 61 |

Label rows also loaded for every StudySpec, with 74,976 numeric outcomes per
study, 4/4 horizon coverage, missing outcome rate 0, valid label availability
timestamps, and declared cost-model metadata in the runtime label diagnostics
path. The label diagnostics builder returned conservative
`DIAGNOSTICS_FAILED` statuses with `weak_diagnostics` because the
`label_coverage_missingness_gate` fails closed when no separate feature/label
audit bundle is supplied. That residual warning is separate from the earlier
missing-reader issue: the locked Parquet values are now readable and loaded.
It remains a real caveat for `FUTSUB-P29`, not a clean label-diagnostics pass.

## N_eff Context

The locked label grid reports these value-free row and overlap counts from the
local LabelRegistry metadata through the P25 runtime N_eff surface
`build_n_eff_sample_report`. The replay supplied explicit overlap metadata for
each locked horizon, using 1-minute sampling cadence and discount factors equal
to the horizon minutes. That runtime path validates the metadata, applies
`floor(rows / discount_factor)`, marks rows as non-independent samples, and
attaches P24-shaped fold context through
`attach_n_eff_to_walk_forward_metadata`.

| Horizon | Rows | Overlap discount | N_eff |
| --- | ---: | ---: | ---: |
| `fwd_ret_5m` | 7,455,294 | 5 | 1,491,058 |
| `fwd_ret_10m` | 7,416,879 | 10 | 741,687 |
| `fwd_ret_15m` | 7,379,178 | 15 | 491,945 |
| `fwd_ret_30m` | 7,294,349 | 30 | 243,144 |

Rows are not independent samples. The factor diagnostics replay attached
purged/embargoed walk-forward context to the in-memory observation samples.

## Boundaries And Next Step

No source code, AlphaSpec, StudySpec, feature family, label family, registry,
value store, Parquet artifact, verdict, promotion, strategy, paper/live,
broker, deployment, or capital-allocation behavior was created by this phase.

`FUTSUB-P29` owns the verdict refresh after Ralph validation and review handling.
This page is evidence for that later review path, not a verdict or promotion.
The P29 review path must account for the unresolved label coverage/missingness
gate failure and the lack of any executor-created review artifact for P28.
