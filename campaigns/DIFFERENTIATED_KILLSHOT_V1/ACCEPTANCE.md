# ACCEPTANCE — DIFFERENTIATED_KILLSHOT_V1

## Campaign-level invariants (every phase)

- `python tools/hooks/canary_runner.py` all-PASS (incl. `planted_fake_alpha`, true-alpha pair,
  `forbidden_second_pnl_truth`, `forbidden_exploratory_promotion`, `governance_random_target`,
  `forbidden_scope_drift`).
- **FDR before metric:** no real-data IC/return/diagnostic value is inspected before (a) the
  `FDR_ACTIVE_SUBSET_RESTATEMENT.md` is committed (DK-P00, predating any variant) and (b) the
  study's surrogate-FDR calibration yields `ZERO_PASS_MET` (DK-P02). Surrogate-FDR zero-pass +
  no-lookahead/`available_ts` + roll/maintenance fail-closed guards intact.
- The existing **single-factor** path (`SINGLE_FACTOR_THRESHOLD_TEMPLATE`, `StudyConfig.factor_id`)
  is **byte-unchanged**; new calendar flags + the declared-conditioning-factor admission are
  strictly additive and pass the fast-vs-reference **parity** gate.
- **No second PnL truth:** `research/` imports zero `backtest`/`management`/`fast_path`/`value_store`
  (AST import guard + `forbidden_second_pnl_truth` canary green); values are loaded by
  `tools/`/`runtime/` and injected into the pure research probe.
- **No new dependency** (numpy/pandas/polars stay unimportable). No new paid data; `fomc/cpi`
  DEFERRED. FUTSUB / core-pilot research artifacts unmodified.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Allowed outputs only: `REJECT / INCONCLUSIVE+reason_code / WATCH / CANDIDATE_RESEARCH`. No
  promotion / profitability / tradability / FactorLibrary claim.

## Per-phase acceptance

### DK-P00 (YELLOW) — the FDR-before-metric gate
Bundle consistent; pointer set; YAML parses; `FDR_ACTIVE_SUBSET_RESTATEMENT.md` committed
(value-free, predates any variant; active = day_of_week+opex+month_end+roll_week+open_close;
`fomc/cpi` DEFERRED; per-mechanism `variant_budget` = horizon count; active effective pooled
surface = **6** = event-calendar{opex 1 + month_end 1}=2 + flow-seasonality{day_of_week 1 + roll_week
1 + open_close 2}=4); `REUSE_MAP` + `SCOPE` committed; smoke + canaries pass.

### DK-P01 (YELLOW) — zero-feed calendar substrate
Five new `SESSION_CALENDAR_ROLL` flags exist in **both** the reference family and the polars fast
path, value-identical under the **parity** gate; APPROVED `FeatureRequest`(s); `live=True`/CAUSAL/
known-ahead; no-lookahead/`available_ts` audits pass; opex/quad-witch = analytic third-Friday,
month/quarter-end = last trading session within the covered calendar (non-claim), in_roll_window via
`roll_guard.classify_roll_window` (no offline `bars_to_roll`/`minutes_to_roll`); flags materialized
ES/NQ/RTY (uncommitted); single-factor path + value engine untouched; canaries PASS.

### DK-P02 (YELLOW) — Track A specs + surrogate gate
Five Track A StudySpecs authored + locked (resolver-smoke); the declared-conditioning-factor
admission is **minimal** and preserves all gates (mutation-tested); surrogate-FDR zero-pass
calibration `ZERO_PASS_MET` for every study (reports value-free: ids/counts/seeds/gate only);
**no real-data metric inspected**; canaries PASS.

### DK-P03 (YELLOW) — Track A evidence + verdict
All five mechanisms scored on real data (post-gate); each has `primary_state + reason_code +
N_eff/power`; `verdict_refresh.md` committed (research-only language, no tradability claim); a
`WATCH/CANDIDATE_RESEARCH` survivor carries a `reviewer_verdict` artifact + reason_code and is
surfaced; `research/` imports no value engine; canaries PASS.

### DK-P04 (YELLOW) — Track B EXPLORATORY probe
One context≠trigger EXPLORATORY SetupSpec with **genuinely distinct** context vs trigger signals
(C1) compiled + run over materialized path labels via the injected-row harness; `EVIDENCE.json`
value-free, stamp `EXPLORATORY`, `promotion_eligible:false`, with surrogate-FDR gate + variant
binding + power (or honest `DATA_GAP`, no fabricated values — C2); promotion path refuses it (canary);
`conditional_probe.py` byte-unchanged; `research/` import-clean; canaries PASS.

### DK-P05 (YELLOW) — verdict + survivor gate
`CAMPAIGN_VERDICT.md` aggregates all five Track A + Track B items with `primary_state + reason_code`;
survivor gate applied (0 survivors documented as conclusive, or survivor surfaced with reviewer
verdict, no factory by inertia); evidence summary + `RUN_SUMMARY` written; research-only language;
no promotion; canaries PASS.

## Campaign done

DK-P00–DK-P05 merged with the above met; `RUN_SUMMARY` written; no promotion, no
profitability/tradability/alpha claim; `fomc/cpi` and the overnight family remain DEFERRED behind
their triggers; any survivor is surfaced for the survivor-gate decision, never auto-promoted.
