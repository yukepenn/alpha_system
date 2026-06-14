# DK-P05 Handoff — Campaign Verdict Aggregation, Survivor Gate, and Closeout

- campaign_id: `DIFFERENTIATED_KILLSHOT_V1`
- phase_id: `DK-P05`
- lane: YELLOW
- branch: `dk-p05-verdict-closeout` (isolated git worktree off `main` @ `3a51db6`)

## Scope Delivered

Aggregation + adjudication only — **no new study, no new metric, no new calibration, no re-score**.
Consumed the locked, committed DK-P03 (Track A) and DK-P04 (Track B) evidence **verbatim** and mapped
it to the closed campaign verdict taxonomy.

- `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` — per-item `primary_state` +
  `reason_code` for all **5 Track A mechanisms + 1 Track B item**, the boundary roll-up, the applied
  survivor gate (0 survivors → conclusive trustworthy negative), the well-powered-clean-null vs
  substrate-`DATA_GAP` distinction, and all carried caveats. Research-only; no promotion.
- `research/differentiated_substrate_v1/RUN_SUMMARY.md` — per-phase deliverables (P00-P05), the
  substrate-gap recovery, the shipyard `--workers` refit, coordinator-driven execution, cost/lessons,
  and the **POST-DK next-shot adjudication** (recommendation **(A)** with the why-not for (B);
  recommendation only, not a launch).
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md` — this handoff.

No conditional `reviewer_verdict` survivor artifact was produced because there is **no**
`WATCH`/`CANDIDATE_RESEARCH` survivor (the asymmetric no-survivor branch; mirrors FUTSUB-P29).

## Final Aggregated Verdict

| State | Track A | Track B | Total items |
| --- | ---: | ---: | ---: |
| `REJECT` | 4 mechanisms / 5 scored tests | 0 | 4 |
| `INCONCLUSIVE` (`DATA_GAP`) | 1 (`roll_week_flow`) | 1 (single-class 120m slice) | 2 |
| `WATCH` | 0 | 0 | 0 |
| `CANDIDATE_RESEARCH` | 0 | 0 | 0 |
| **Total** | **5** | **1** | **6** |

**Survivor count = 0.** Four gated mechanisms (`day_of_week_effect`, `opex_pinning`, `month_end_flow`,
`open_close_auction_flow`) are a **well-powered CLEAN NULL → conclusive kill-shot** (the 2nd to land
clean; FUTSUB 1st). `roll_week_flow` and the Track B context≠trigger probe are honest substrate
`DATA_GAP`s (UNANSWERED) — **not** nulls, **not** `REJECT`s. Only the four closed allowed states are
used.

## Exact Validation Commands + Results (run in the isolated worktree, clean env)

venv `/home/yuke_zhang/.venvs/alpha_system_research/bin/python`.

| Command | Result |
| --- | --- |
| `python tools/verify.py --smoke` (FRONTIER_* unset) | **exit 0** |
| `python tools/verify.py --all` (FRONTIER_* unset) | **exit 1 — 2 failed, 3622 passed, 1 skipped.** The only 2 failures are pre-existing, env-library, doc-unrelated (see below). |
| `python tools/hooks/canary_runner.py` | **All canaries PASS** (incl. `planted_fake_alpha`, `true_alpha_detection_*`, `forbidden_second_pnl_truth`, `forbidden_exploratory_promotion`, `governance_random_target`, `forbidden_scope_drift`) |
| numpy/pandas/polars dependency check (corrected one-liner) | `numpy`/`pandas` **not** importable; `polars` importable (**pre-existing** — runtime dep of the sanctioned `core.value_store` Parquet loader via FEATURE_LABEL_PARQUET_SINK_V1, **not** added by this phase, which writes only Markdown) |
| no research→sim bridge grep (`src/alpha_system/research`) | **no forbidden research→sim imports** |
| `test -f research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` | present |
| `git ls-files runs` | **empty** |
| `git status --short` (worktree) | only the 2 new docs + this handoff — no test/code/data touched |

### The `--all` exit-1 failure — pre-existing environmental false negative (NOT introduced here)

The two failing tests are:

- `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
- `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`

Both are tiny optional integration fixtures asserting an exact tuple/list + float-equality result from
the `duckdb` / `polars` query backends in the local research venv. **Verified pre-existing:** running
these two tests on the clean `main` baseline (`/home/yuke_zhang/projects/alpha_system` @ `3a51db6`,
zero of this phase's changes) reproduces **the identical 2 failures**. This phase changed only two
Markdown files (`CAMPAIGN_VERDICT.md`, `RUN_SUMMARY.md`) + this handoff; it touched no test, no code,
no fixture, no dependency. This is a known-style local-env-≠-CI false negative (the same class as the
documented `FRONTIER_*`-env false negative). **No check was weakened, skipped, or special-cased to make
it pass** — it is recorded here as the only `--all` red, per the spec's "document the outcome rather
than weakening any check" instruction.

## Required Confirmations

1. **`CAMPAIGN_VERDICT.md` carries all 5 Track A + 1 Track B item** with `primary_state` + `reason_code`,
   uses **only** the four allowed states (`REJECT`/`INCONCLUSIVE`+code/`WATCH`/`CANDIDATE_RESEARCH`),
   and the boundary roll-up is internally consistent (4 `REJECT` + 2 `INCONCLUSIVE`+`DATA_GAP` = 6
   items; 5 scored tests; `WATCH`=0, `CANDIDATE_RESEARCH`=0). Every per-item state reproduces DK-P03
   `verdict_refresh.md` / DK-P04 `EVIDENCE.json` verbatim.
2. **The survivor gate was applied — no-survivor branch.** 0 `WATCH`/`CANDIDATE_RESEARCH` survivors ⇒
   conclusive trustworthy negative with the earned argument (FDR-before-metric + surrogate zero-pass
   incl. the fail-closed `roll_week` refusal + planted/true-alpha canaries green + well-powered reads);
   **no** `reviewer_verdict` artifact required; **nothing surfaced, nothing auto-promoted, no factory
   built.**
3. **No DK-P03/DK-P04 verdict was changed and no new metric/calibration was produced.** States are
   carried, not re-derived; no re-run, no re-score, no new surrogate run; no down-scope
   `BudgetAmendmentRecord`.
4. **`research/` imports none of `backtest`/`management`/`fast_path`/`core.value_store`** (grep clean) —
   no second PnL truth; this phase reads committed Markdown/JSON only and computes no value.
5. **Caveats carried forward** (zero-feed calendar approximations; month/quarter-end 2024-26 coverage;
   within-mechanism near-duplicate secondary exposures; first-order `N_eff`/power/MDE,
   `statistical_validity_claim: false`; `roll_week` `DATA_GAP`; Track B single-class-slice `DATA_GAP`;
   `fomc`/`cpi` DEFERRED=`needs_paid_data`; overnight family DEFERRED, RED at paper/live; C2/C3
   non-claims). **No** profitability/tradability/alpha claim; **no** promotion; Track B stays
   permanently `EXPLORATORY`/non-promotion.
6. **Canaries all-PASS; `numpy`/`pandas` unimportable; `git ls-files runs` empty.** `polars` is a
   pre-existing sanctioned-loader dependency, not added here.

## POST-DK Next-Shot Recommendation (recommendation only — for the coordinator / Captain)

Recommend **(A): close the Track-B substrate `DATA_GAP` and re-run the SAME pre-registered
context≠trigger probe** on a barrier-resolving 120m `target_before_stop` path-label slice — **no new
mechanism, no hypothesis change, no new data, no universe expansion, no paid feed**.

**Feasibility verified against existing local data (load-bearing):** DK-P04's `DATA_GAP` was caused
only by the narrow LCFP-P08 **June-2024** benchmark slice (`ES_2024_120m_lcfp_p08_es_202406`), which is
single-class. Durable full-year 120m `target_before_stop` path slices already exist for **ES/NQ/RTY,
2019-2026**. A read-only value-distribution check (sanctioned `core.value_store` loader) of one
candidate confirmed **`ES_2020_120m` is barrier-resolving: 313,156 events = 309,206 `False` + 3,950
`True` (NOT single-class)**. So a non-degenerate slice is already materialized; option (A) needs zero
new data and reuses the validated DK-P04 probe plumbing.

**Why (A) over (B):** the campaign's headline *differentiated* context≠trigger bet is **UNANSWERED**
(conditioning never exercised on a single-class slice), not answered negatively; closing a cheap,
zero-new-data, in-scope gap before declaring the idea dead is the honest "close the gap and re-run"
DATA_GAP doctrine and the cheapest unexhausted test. **(B)** (a fresh existing-data shot —
`GOVERNED_OVERNIGHT_KILLSHOT_V1` / `STRATEGY_SHAPED_KILLSHOT_V2` / a PA-VWAP setup shot) stays
available and reachable but is **second**: the overnight family has no cards/`LabelSpec` authored and
is RED-lane at paper/live (furthest from ready), and any new shot consumes new pre-registered FDR
budget + author→verdict latency for an idea class that has not earned priority over the in-flight bet.
If (A) lands a clean well-powered null (or exhausts), (B) becomes the natural next move. `fomc`/`cpi`
and any paid/universe expansion remain DEFERRED behind their explicit triggers. **No probe was re-run,
no slice re-materialized, no campaign authored or queued** — the next-shot launch is a separate,
triggered, user-owned decision.

## Files Changed (by path; explicit staging only)

- `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` — new.
- `research/differentiated_substrate_v1/RUN_SUMMARY.md` — new.
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md` — this handoff.

## Skipped / Deferred Checks

- None skipped. The full `python tools/verify.py --all` suite was run; its only red is the 2
  pre-existing `duckdb`/`polars` integration-fixture failures documented above (reproduced identically
  on the clean `main` baseline; doc-unrelated; no check weakened). No optional `tests/**` consistency
  test was added (it is **not** in this phase's Allowed Paths; the consistency was verified by the
  reviewer/manual roll-up reconciliation per the spec).

## Boundary / Non-Claims

This is an evidence summary + allowed-state verdict record + recommendation only. No FactorLibrary
ingestion, no AlphaBook/Strategy-Reference entry, no `PromotionDecision`, no paper/live/broker action,
no deployment, no capital allocation, no profitability/tradability/alpha claim. Materialized values,
local registries, raw/canonical provider data, Parquet/SQLite, and scratch reports remain local-only
and are not committed. The run-local `runs/<run_id>/.../handoff.md` stays local-only and is not staged.
DK-P05 was authored in an isolated git worktree; the coordinator owns the merge and any state surgery
(no self-merge).
