# FUTSUB-P29 Verdict Refresh

Value-free verdict refresh for `FUTSUB-P29` in
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

This document consumes the already-produced `FUTSUB-P27` re-lock report and
`FUTSUB-P28` rerun diagnostics evidence. It does not re-run studies, re-lock
StudySpecs, materialize values, tune parameters, create new AlphaSpecs, or
promote any study outside the allowed campaign states.

Allowed primary states here are only `REJECT`, `INCONCLUSIVE`, `WATCH`, and
`CANDIDATE_RESEARCH`.

## Evidence Inputs

Primary rerun evidence:

- `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
- `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`
- `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P28/review.md`

Scaleout context:

- `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md`
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`
- `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`
- `docs/futures_substrate_scaleout/LABEL_COVERAGE.md`
- `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`
- `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md`
- `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
- `docs/futures_substrate_scaleout/ROLL_GUARD.md`
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`

## Boundary Refresh

Inherited Core Pilot boundary:

| State | Count |
| --- | ---: |
| `REJECT` | 4 |
| `INCONCLUSIVE` | 6 |
| `WATCH` | 0 |
| `CANDIDATE_RESEARCH` | 0 |

Refreshed boundary after consuming `FUTSUB-P28` rerun evidence:

| State | Count | Change vs inherited |
| --- | ---: | ---: |
| `REJECT` | 10 | +6 |
| `INCONCLUSIVE` | 0 | -6 |
| `WATCH` | 0 | 0 |
| `CANDIDATE_RESEARCH` | 0 | 0 |

The four prior cross-market `REJECT` states remain unchanged and were audit-only
inputs in the P27/P28 rerun gate. The six prior `INCONCLUSIVE` studies became
resolvable after the scaleout substrate and were rerun in P28. Their refreshed
state is `REJECT`, with caveats carried forward below. No `WATCH` or
`CANDIDATE_RESEARCH` state is assigned, so this executor did not create an
independent reviewer verdict artifact.

## Refreshed Verdict Table

| Original StudySpec | V2 StudySpec | Family | Prior state | Refreshed state | Deterministic P28 evidence | Residual caveats |
| --- | --- | --- | --- | --- | --- | --- |
| `sspec_267cc052e37668339c38d179` | `sspec_dec89a327a9c50957adca780` | `regime` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `456` feature locks and `96` label locks. P28 factor diagnostics returned `DIAGNOSTICS_COMPLETE` with `74,592` rows, `72,441` numeric pairs, `0.9712` coverage, Pearson IC `-0.0204`, rank IC `-0.0002`, and `67` walk-forward folds. P28 reported mixed direction and no bucket monotonicity. | Label diagnostics loaded `74,976` numeric outcomes but failed closed with `weak_diagnostics` at `label_coverage_missingness_gate`; this is a diagnostic caveat, not a missing-lock result. |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_840e8342564226f2c3257903` | `liquidity_pa` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `552` feature locks and `96` label locks. P28 factor diagnostics returned `DIAGNOSTICS_COMPLETE` with `74,304` rows, `72,595` numeric pairs, `0.9770` coverage, Pearson IC `0.0072`, rank IC `0.0008`, and `67` walk-forward folds. P28 reported mixed direction and no bucket monotonicity. | Same label diagnostics fail-closed caveat as above. P28 review also records that the two liquidity/PA reruns are within-family near-duplicates with identical factor summaries. |
| `sspec_02c400a561891171a33c0c66` | `sspec_c237c6a8ce40c2585836fae0` | `liquidity_pa` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `552` feature locks and `96` label locks. P28 factor diagnostics returned the same aggregate evidence as `sspec_840e8342564226f2c3257903`: `74,304` rows, `72,595` numeric pairs, `0.9770` coverage, Pearson IC `0.0072`, rank IC `0.0008`, and `67` walk-forward folds. | Same label diagnostics fail-closed caveat as above. The identical liquidity/PA summaries are treated as duplicate exposure context, not independent survivor evidence. |
| `sspec_9f6f741192a4b534f06e51c0` | `sspec_533f665ec4ac063dbb664a54` | `bbo_tradability` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `600` feature locks and `96` label locks. P28 factor diagnostics returned `DIAGNOSTICS_COMPLETE` with `74,976` rows, `66,877` numeric pairs, `0.8920` coverage, Pearson IC `-0.0050`, rank IC `0.0008`, and `61` walk-forward folds. | Same label diagnostics fail-closed caveat as above. BBO remains a time-sampled, forward-filled top-of-book proxy and is not execution truth, passive-fill evidence, queue evidence, or impact evidence. |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_1604b063f3a3401208ee0239` | `vwap_session` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `480` feature locks and `96` label locks. P28 factor diagnostics returned `DIAGNOSTICS_COMPLETE` with `74,880` rows, `66,067` numeric pairs, `0.8823` coverage, Pearson IC `0.0033`, rank IC `-0.0011`, and `61` walk-forward folds. P28 reported mixed direction and no bucket monotonicity. | Same label diagnostics fail-closed caveat as above. P28 review records that the two VWAP/session reruns are within-family near-duplicates with identical factor summaries. |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_f6cbd88caa0445f0f56d81fd` | `vwap_session` | `INCONCLUSIVE` | `REJECT` | P27 V2 lock resolved `480` feature locks and `96` label locks. P28 factor diagnostics returned the same aggregate evidence as `sspec_1604b063f3a3401208ee0239`: `74,880` rows, `66,067` numeric pairs, `0.8823` coverage, Pearson IC `0.0033`, rank IC `-0.0011`, and `61` walk-forward folds. | Same label diagnostics fail-closed caveat as above. The identical VWAP/session summaries are treated as duplicate exposure context, not independent survivor evidence. |

All six label reruns loaded `74,976` label rows and `74,976` numeric outcomes,
with `4/4` locked horizon coverage, missing outcome rate `0`, valid label
availability timestamps, and declared cost-model metadata. The shared label
diagnostics status remains `DIAGNOSTICS_FAILED` with `weak_diagnostics` because
the runtime coverage/missingness gate expects a separate audit bundle. P29 does
not fabricate that bundle and does not call this a clean label-diagnostics pass.

The P28 N_eff context used the P25 runtime surface with explicit 1-minute
sampling cadence and horizon-overlap metadata. The locked fixed-horizon label
grid reported:

| Horizon | Registered rows | Overlap discount | N_eff |
| --- | ---: | ---: | ---: |
| `fwd_ret_5m` | 7,455,294 | 5 | 1,491,058 |
| `fwd_ret_10m` | 7,416,879 | 10 | 741,687 |
| `fwd_ret_15m` | 7,379,178 | 15 | 491,945 |
| `fwd_ret_30m` | 7,294,349 | 30 | 243,144 |

Rows are not independent samples. P28 also used purge gap `10` and embargo gap
`10` walk-forward context. The N_eff numbers are metadata, not a statistical
significance result or a promotion rule. They are also first-order
horizon-overlap metadata over registered label rows; they are not
session-clustered or autocorrelation-adjusted effective sample counts. The
registered-row N_eff population is different from the capped factor-diagnostics
observation samples in the verdict table and must not be conflated with those
runtime observation counts.

## Why No WATCH Or CANDIDATE_RESEARCH

No P28 evidence supports a `WATCH` or `CANDIDATE_RESEARCH` state:

- factor diagnostics are complete and resolver-clean, but the aggregate IC
  summaries are near zero and bucket monotonicity is false for every rerun;
- the two liquidity/PA reruns and the two VWAP/session reruns are within-family
  near-duplicate diagnostic exposures, not independent confirmations;
- label diagnostics retain the fail-closed `label_coverage_missingness_gate`
  caveat;
- BBO inputs remain proxy quality evidence only;
- no independent reviewer verdict for `WATCH` or `CANDIDATE_RESEARCH` was
  produced by this executor, and the assigned states do not require one.

The result is a no-survivor refresh: all six formerly substrate-blocked
reruns now have enough deterministic evidence for a conservative `REJECT`
state instead of remaining `INCONCLUSIVE` due to missing substrate.

## Scaleout Evidence Summary

The rerun gate is closed by evidence that the missing-substrate condition was
removed without changing the research-only boundary:

- DatasetVersion acceptance-lock: `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md`
  records exact local registry resolution and persisted `ACCEPTED`,
  `ACCEPTED_WITH_WARNINGS`, or `BLOCKED` states for the Databento OHLCV,
  OHLCV dense-grid, and BBO yearly versions. The 2018 window remains an expected
  exclusion; 2019 and 2026 preserve warning metadata.
- Feature substrate: `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`
  records all eight governed feature families over ES/NQ/RTY for 2019-2026,
  with `0` unexpected accepted-window gaps. The P14 feature resolver smoke
  records `PASS` for exact-id resolution and fail-closed behavior.
- Label substrate: `docs/futures_substrate_scaleout/LABEL_COVERAGE.md` and
  `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`
  record `1368/1368` current preview label locks resolved, `0` current preview
  gaps, and no deprecated ids in the current preview surface.
- Guarding: `docs/futures_substrate_scaleout/ROLL_GUARD.md`,
  `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`,
  and `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`
  record approximate roll-window and maintenance-crossing guard evidence with
  zero silently measured crossings.
- BBO and cross-market context:
  `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md` records
  BBO as a time-sampled and forward-filled top-of-book proxy and records
  cross-market `strict_intersection` availability discipline, not predictive or
  execution evidence.
- Walk-forward and N_eff:
  `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md` and
  `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
  record the purged/embargoed walk-forward callable path and fail-closed
  overlap-aware sample reporting contract.
- Rerun evidence:
  `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`
  records six resolver-clean reruns over locked local Parquet-backed values,
  with no external provider call, no registry mutation, no value artifact
  committed, and no verdict refresh until this P29 document.

## Boundary And Non-Claims

This refresh is an evidence summary and allowed-state verdict record only. It
does not create a FactorLibrary ingestion record, Strategy Reference validation,
AlphaBook entry, paper or live trading behavior, broker/order behavior,
deployment behavior, capital-allocation decision, profitability claim, or
tradability claim.

Values, local registries, raw/canonical provider data, Parquet payloads, SQLite
databases, roll-calendar data, and scratch reports remain local-only and are not
committed by this phase.
