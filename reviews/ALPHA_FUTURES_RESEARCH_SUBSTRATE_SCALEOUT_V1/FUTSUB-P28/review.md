# Fresh Review — FUTSUB-P28: Re-run Previously INCONCLUSIVE Core Pilot Studies

- Date: `2026-06-13`
- Phase: `FUTSUB-P28` (YELLOW research; kill-shot Core Pilot rerun)
- Reviewer: coordinator-adjudicated fresh review of the **repaired** artifacts,
  backed by 3 independent adversarial verifiers (workflow `p28-killshot-verdict-verify`).
- Provenance note: this review is the on-record fresh review of the repaired
  artifacts that the FUTSUB-P28 done-check (`REWORK`) reason 1 required. The
  run-local repair review (`runs/.../phases/FUTSUB-P28/repair_attempts/001/repair_review.md`,
  `PASS_WITH_WARNINGS`) and this committed review agree. The phase had BLOCKED on
  repair-exhaustion because the executor cannot write `reviews/` (Ralph/reviewer-owned)
  and a transient codex provider-hang exhausted the repair budget — a provenance/
  infrastructure block, not a substantive defect.

## Verdict: PASS_WITH_WARNINGS

The repaired P28 artifacts are substantively complete, validation-green, value-free,
and honestly scoped (no verdict refresh, no promotion, no profitability/tradability
claim — those are P29's). Three independent adversarial verifiers each returned PASS;
synthesis returned `RESOLVE_PASS_WITH_WARNINGS` with zero must-fix.

## What was verified (independently, against the live repo)

1. **Candidate set correct / audit-only boundary honored.** Exactly the 6 prior-
   INCONCLUSIVE V2 StudySpecs were rerun (`sspec_dec89a3` regime, `sspec_840e83` +
   `sspec_c237c6` liquidity_pa, `sspec_533f665` bbo_tradability, `sspec_1604b0` +
   `sspec_f6cbd88` vwap_session); the 4 prior-REJECT cross_market sspecs appear 0×
   (R-024 no new-alpha mining). Original→V2 ids match `studyspec_relock.md`.
2. **Diagnostics internally consistent, near-zero IC.** Pearson IC
   −0.0204/0.0072/0.0072/−0.0050/0.0033/0.0033; rank IC |·| ≤ 0.0011; coverage =
   numeric_pairs/rows to 5 decimals for all six; coverage+missingness = 1.0000.
   No inflated/fabricated values. (Verified by internal arithmetic + cross-doc
   agreement + the wired-builder source; the Parquet engine was not re-executed —
   `ALPHA_DATA_ROOT`/scratch are intentionally local-only.)
3. **N_eff provenance is the sanctioned P25 overlap-aware builder** (`src/alpha_system/
   runtime/diagnostics/splits/n_eff.py` `build_n_eff_sample_report`, fail-closed
   `HorizonOverlapMetadata.__post_init__`, P24 walk-forward fold attachment). Decisive
   default field-name fingerprints (`session_label,...` / `trade_date,...`) exist only
   in that builder. Not an ad-hoc divide. (R-019 satisfied; first-order discount —
   see caveats.)
4. **Label-gate is a genuine, honestly-disclosed config fail-closed.** All six returned
   `DIAGNOSTICS_FAILED`/`weak_diagnostics` at `label_coverage_missingness_gate`
   (`require_label_audit`/`require_feature_label_coverage` default True; no audit bundle
   supplied). Disclosed as a P29 residual in all three docs — NOT a substrate gap, NOT
   suppressed. Under-claims where uncertain.
5. **Posture clean.** `canary_runner.py` all PASS (incl. `planted_fake_alpha`,
   `forbidden_second_pnl_truth`, `forbidden_scope_drift`, `forbidden_runs_staging`,
   `governance_random_target`, true-alpha detection pair); worktree touches only the 4
   value-free paths; `git ls-files runs` empty; no heavy artifacts; no `src/`/test/
   boundary edits.

## Warnings / caveats that MUST travel into FUTSUB-P29's verdict refresh

1. **Label-gate fail-closed**: P29 must supply the feature/label audit bundle to close
   the `label_coverage_missingness_gate`; until then the label gate cannot PASS in this
   configuration regardless of label quality. Do not read factor `DIAGNOSTICS_COMPLETE`
   as a clean label result.
2. **Near-zero IC reality**: |Pearson IC| ≤ 0.0204, |Rank IC| ≤ 0.0011, non-monotone
   buckets — descriptive statistics only, not significance/promotion/profitability.
   P29 owns the verdict.
3. **Within-family near-duplicates**: liquidity_pa (840e83/c237c6) and vwap_session
   (1604b0/f6cbd88) report byte-identical factor diagnostics (shared feature/horizon
   grid across ES/NQ/RTY). P29 must treat within-family pairs as near-duplicates for
   multiple-testing / FDR accounting.
4. **N_eff is first-order**: flat per-horizon discount (= rows/horizon for non-overlapping
   1m cadence) on ~7.4M registered rows; does not yet fold purge/embargo, session
   clustering, or label-window autocorrelation; `statistical_validity_claim` False. A
   session-clustered/autocorrelation-adjusted N_eff is a legitimate P29 refinement.
5. **Provenance row-population split**: the headline N_eff (registered rows, millions) and
   the factor diagnostics (capped ~74k observation samples) describe different row
   populations (documented in method_notes); P29 must not conflate them.
6. **BBO is a proxy**: bbo_tradability inputs are time-sampled, forward-filled top-of-book
   proxies — not execution truth, not passive-fill/queue/impact evidence. The BBO study's
   verdict evidence must carry this proxy caveat.
7. **Pre-existing accepted debt (not introduced by P28)**: two `registry_event_ts_grid`
   ALLOW lines (`BBO_PENDING_RE_MATERIALIZATION`, `COST_SPREAD_LABEL_MIRROR_DEFECT`)
   remain accepted debt (allowed_debt=4, violations=0); unrelated to the P28 label gate.

## Value-Free Attestation

This review records ids, statuses, counts, code citations, and issue codes only — no
feature/label/return/IC values beyond the aggregate descriptive statistics already in the
value-free phase artifacts. No alpha/profitability/tradability/production claim is made.
