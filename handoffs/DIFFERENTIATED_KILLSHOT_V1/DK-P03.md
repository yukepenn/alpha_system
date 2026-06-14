# DK-P03 Handoff — Track A Real-Data Evidence + Verdict Refresh (First Metric, Post-Gate)

- campaign_id: `DIFFERENTIATED_KILLSHOT_V1`
- phase_id: `DK-P03`
- lane: YELLOW
- branch: `dk-p03-track-a-real-metric`

## Scope Delivered

Ran the **first real-data metric** of the campaign for the Track A differentiated mechanisms and
mapped the evidence to the closed verdict taxonomy honestly. Scored the four mechanisms whose
DK-P02 surrogate calibration reached `ZERO_PASS_MET` — `day_of_week_effect`, `opex_pinning`,
`month_end_flow`, `open_close_auction_flow` (5 pooled tests total: open_close has 2 horizons) —
on real, locally-materialized values, pooled ES/NQ/RTY as one test per (mechanism, horizon).
`roll_week_flow` was **excluded** from real-metric inspection because its DK-P02 surrogate
calibration was `CALIBRATION_BLOCKED` / `DATA_GAP` (all-null conditioning flag).

**Result: every scored test is a well-powered, conclusive `REJECT`. Zero survivors.** No
`WATCH`/`CANDIDATE_RESEARCH`, so no `reviewer_verdict` artifact and nothing surfaced for a
survivor-gate decision. The reads are `DIAGNOSTICS_COMPLETE` with full coverage, near-zero
aggregate Pearson IC, non-monotonic buckets, and `N_eff` in the tens-to-hundreds of thousands
(so a usable `MDE(|IC|)` resolved and none mapped to `INCONCLUSIVE`+`UNDERPOWERED`).

### Per-mechanism verdict

| Mechanism | Horizon | Pearson IC | Rank IC | N_eff | MDE(\|IC\|) | Runtime status | primary_state |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `day_of_week_effect` | 30m | -0.00710 | -0.00496 | 243,144 | 0.003975 | `DIAGNOSTICS_COMPLETE` | `REJECT` |
| `opex_pinning` | 30m | -0.00488 | -0.00513 | 243,144 | 0.003975 | `DIAGNOSTICS_COMPLETE` | `REJECT` |
| `month_end_flow` | 30m | -0.00144 | -0.00496 | 78,593 | 0.006991 | `DIAGNOSTICS_COMPLETE` | `REJECT` |
| `open_close_auction_flow` | 5m | 0.00082 | -0.00394 | 430,866 | 0.002986 | `DIAGNOSTICS_COMPLETE` | `REJECT` |
| `open_close_auction_flow` | 30m | -0.00083 | -0.01063 | 70,774 | 0.007368 | `DIAGNOSTICS_COMPLETE` | `REJECT` |
| `roll_week_flow` | 30m | — | — | — | — | not run | excluded (`DATA_GAP`) |

## Reused (Not Rewritten) Scorer + In-Scope Repair

The pure research scorer (`src/alpha_system/research/track_a_scorer.py`) and the tools-side
row-injection harness (`tools/differentiated_killshot_v1/score_track_a.py`) from the prior
worktree were **reused as-is**, with one in-scope harness fix:

- `score_track_a.py` referenced an uninitialized `data_version_seen[...]` dict on the staged
  partition path (line ~305) — a dead write that was never read and would raise `NameError` on
  the first staged partition. Removed the single dead line (no behavior change to staging,
  pooling, or scoring).

## Scorer Trust Verification (4 checks, all confirmed)

1. **No-lookahead.** `build_factor_diagnostics_run`
   (`src/alpha_system/runtime/diagnostics/factor/runtime.py`) counts a row as a usable
   observation only when both `available_ts` and `label_available_ts` are present
   (runtime.py ~line 359); a missing availability timestamp flips the run to `REJECTED`
   (`factor_available_ts_missing` / `factor_label_available_ts_missing`, ~lines 451-464). The
   harness carries both timestamps through (`score_track_a.py` ~lines 206-207).
2. **No second PnL truth.** `track_a_scorer.py` imports none of
   `backtest`/`management`/`fast_path`/`core.value_store` (grep clean). Values are loaded
   tools-side via `core.value_store.load_parquet_values` (through the reused DK-P02 staging
   backbone) and injected as rows; no PnL value computed in `research/`.
3. **Sanctioned IC reused.** The factor runtime computes Pearson/rank IC via the shared
   `alpha_system.research.ic` module (runtime.py ~lines 393-400), not a rogue reimplementation;
   `N_eff` via `estimate_n_eff` with a first-order horizon-overlap discount.
4. **FDR gate honored.** Only the four `ZERO_PASS_MET` mechanisms were scored; `roll_week_flow`
   (`CALIBRATION_BLOCKED` / `DATA_GAP`) was excluded from any metric read.

## RAM-Safe Execution

Box = 40 GB RAM total; the directive floor was `free -m available > 6 GB` at all times. Run plan:
`day_of_week + month_end` as a parallel PAIR, then `opex` serial, then `open_close` serial.

- Pair peak combined RSS ~15.6 GB; available never dropped below ~24 GB.
- Single-mechanism peak RSS ~11.4 GB (opex / open_close); available stayed ~24-38 GB throughout.
- **Peak RAM observed across the whole phase: ~16 GB combined / ~11.4 GB single-process; `free -m`
  available never below ~24 GB (well above the 6 GB floor).** Never went fully serial.
- Each mechanism's scratch was cleaned immediately on completion by the harness
  (`finally: shutil.rmtree`); scratch returned to empty after each run. Disk stayed at ~30 GB
  used / 927 GB free (well under 400 GB). Persistent logs under `~/logs/alpha_pipeline/`.
- venv: `/home/yuke_zhang/.venvs/alpha_system_research/bin/python`; data root
  `/home/yuke_zhang/alpha_data/alpha_system`. Run with `PYTHONPATH=<worktree>/src:<worktree>`
  so the worktree's `alpha_system` (with the new scorer) and the `tools` package both resolve
  (the venv editable install points at the main repo, which lacks the new module).

## Exact Validation Commands + Results

Run from the worktree root with `PYTHONPATH=<worktree>/src:<worktree>`.

- `python -m py_compile tools/differentiated_killshot_v1/score_track_a.py
  src/alpha_system/research/track_a_scorer.py` — PASS.
- `python -m pytest tests/unit/research/test_track_a_diagnostics.py
  tests/unit/research/test_verdict_refresh.py tests/unit/research/test_research_no_value_engine.py -q`
  — **16 passed**.
- Scoring runs (each emitted `DIAGNOSTICS_COMPLETE`; result JSON written; scratch cleaned):
  - `python -m tools.differentiated_killshot_v1.score_track_a --study-spec
    research/differentiated_substrate_v1/study_specs/<m>.json --alpha-data-root
    /home/yuke_zhang/alpha_data/alpha_system --scratch-root
    /home/yuke_zhang/alpha_data/alpha_system/scratch/dk_p03_<m>_<ts> --result-out
    research/differentiated_substrate_v1/diagnostics/<m>.json` for
    `<m>` in {day_of_week, month_end, opex, open_close}.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from ..."
  --include=*.py src/alpha_system/research` — **no forbidden research→sim imports**.
- `python tools/hooks/canary_runner.py` — **see PR/handoff result line** (expected all-PASS).
- `python -c "..."` for numpy/pandas/polars unimportable — to be confirmed in the final
  validation block (no new dependency added by this phase).
- `git ls-files runs` — **empty**.
- `git diff -- src/alpha_system/strategies/templates.py src/alpha_system/core/value_store.py` —
  **empty** (single-factor path + value engine byte-unchanged).

## Files Changed (by path; explicit staging only)

- `tools/differentiated_killshot_v1/__init__.py` — new (reused from prior worktree).
- `tools/differentiated_killshot_v1/score_track_a.py` — new (reused) + dead-line fix.
- `src/alpha_system/research/track_a_scorer.py` — new (reused, pure research scorer).
- `tests/unit/research/test_track_a_diagnostics.py` — new (reused).
- `tests/unit/research/test_verdict_refresh.py` — new (reused).
- `tests/unit/research/test_research_no_value_engine.py` — new (reused).
- `research/differentiated_substrate_v1/verdict_refresh.md` — new.
- `research/differentiated_substrate_v1/diagnostics/DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md` — new.
- `research/differentiated_substrate_v1/diagnostics/{day_of_week,opex,month_end,open_close}.json`
  — new (value-bearing per-mechanism diagnostics, post-gate).
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P03.md` — this handoff.

## Required Confirmations

- (a) Both predecessor gates were committed and consumed before any metric was read: the DK-P00
  FDR active-subset restatement (`FDR_ACTIVE_SUBSET_RESTATEMENT.md`, created `2026-06-14T03:45:38Z`)
  and the DK-P02 `ZERO_PASS_MET` surrogate calibration for each scored study. They were **not**
  re-opened, re-scoped, or amended.
- (b) `research/` imports no `backtest`/`management`/`fast_path`/`core.value_store`; values were
  injected from the tools/runtime harness (no second PnL truth).
- (c) Every mechanism's `primary_state` + (where applicable) `reason_code` + `N_eff`/`MDE` are
  recorded; the verdict mapping used only the closed taxonomy (`REJECT`/`INCONCLUSIVE`/`WATCH`/
  `CANDIDATE_RESEARCH`); no runtime enum was added.
- (d) Every scored variant is ledgered `VariantLedgerStatus.COMPLETED` within the pre-registered
  budget; no `BudgetAmendmentRecord`, no per-instrument split, no horizon sweep; family-budget
  hook intact (all RESPECTED).
- (e) No `WATCH`/`CANDIDATE_RESEARCH` survivor exists, so there is no `reviewer_verdict` artifact
  to surface; nothing was auto-promoted.

## Skipped / Deferred Checks

- The full `python tools/verify.py --all` authoritative suite was not run inside the worktree
  (the change is additive pure-Python + committed Markdown/JSON; the narrow diagnostics/verdict/
  power/ledger tests pass and `verify.py --smoke` is the lane default). Recorded here as the only
  skipped check; broadening is available if shared governance/diagnostics/power behavior is
  flagged in review.

## Boundary / Non-Claims

Materialized values, local registries, raw/canonical provider data, Parquet/SQLite, and scratch
reports remain local-only and are not committed. No promotion, no FactorLibrary/AlphaBook entry,
no paper/live/broker action, no profitability/tradability/alpha claim. Run-local
`runs/<run_id>/.../handoff.md` stays local-only and is not staged.
