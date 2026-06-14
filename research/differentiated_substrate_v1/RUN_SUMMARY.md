# DIFFERENTIATED_KILLSHOT_V1 — Run Summary (Campaign Closeout)

Campaign `DIFFERENTIATED_KILLSHOT_V1` (the **second** narrow kill-shot; FUTSUB was the first).
Closeout authored at `DK-P05`. This is the `RUN_SUMMARY`-equivalent: it summarizes what each phase
delivered, the substrate-gap recovery, the shipyard `--workers` refit, the coordinator-driven
execution, the final boundary + survivor gate, cost / lessons, and a **POST-DK next-shot
adjudication** (a recommendation for the coordinator / Captain — **not** a launch and **not** a new
campaign contract). Research-only language throughout: **no** profitability / tradability / alpha
claim; **no** promotion.

## Mission Recap

The first kill-shot (FUTSUB) rejected all six crowded single-factor price-action / BBO mechanisms at
near-zero IC (0 survivors). DIFFERENTIATED_KILLSHOT_V1 tested a **differentiated** thesis: that a set
of **zero-feed, exchange-calendar-deterministic** mechanisms — day-of-week, OPEX / quad-witch
pinning, month-end / quarter-end flow, roll-week flow, open/close auction proximity — might carry
intraday behavior the efficient price-action substrate did not. It ran them as **pooled (ES/NQ/RTY)
conditional studies on the EXISTING rigor path (Track A)**, plus **one context≠trigger SetupSpec
EXPLORATORY probe** over materialized path labels using the SSRL strategy-shaped lane (Track B). The
whole surface was pre-registered under an FDR active-subset restatement **before any metric**, and
every readout was surrogate-FDR zero-pass gated, variant-ledgered, and `N_eff`/power-qualified.

## Per-Phase Deliverables (DK-P00 → DK-P05)

| Phase | Lane | Delivered | Key gate / outcome |
| --- | --- | --- | --- |
| **DK-P00** | YELLOW | Bootstrap + `FDR_ACTIVE_SUBSET_RESTATEMENT.md` (value-free, predates any variant) + `REUSE_MAP` + `SCOPE` lock; ACTIVE_CAMPAIGN repoint | **The FDR-before-metric gate.** Active pooled surface = day_of_week + opex + month_end + roll_week + open_close; `fomc`/`cpi` DEFERRED = `needs_paid_data`; active effective pooled surface = **6**. Restatement is **not** a `BudgetAmendmentRecord` (strictly-increasing → cannot encode a downward re-scope). |
| **DK-P01** | YELLOW | Five new `SESSION_CALENDAR_ROLL` zero-feed calendar flags in **both** the reference family and the polars fast path | Value-identical under the fast-vs-reference **parity** gate; APPROVED `FeatureRequest`(s); `live=True` / CAUSAL / known-ahead; no-lookahead / `available_ts` audits pass. Single-factor path + value engine **byte-unchanged**. |
| **DK-P02** | YELLOW | Five Track A StudySpecs authored + locked (resolver-smoke); minimal declared-conditioning-factor admission (mutation-tested); surrogate-FDR calibration per study | **4 mechanisms `ZERO_PASS_MET`** (day_of_week, opex, month_end, open_close); **`roll_week` `CALIBRATION_BLOCKED` / `DATA_GAP`** (`no_numeric_declared_factors_for_surrogate` — all-null `in_roll_window_flag`). **No real-data metric inspected.** |
| **DK-P03** | YELLOW | First real-data metric of the campaign for the 4 gated mechanisms; `verdict_refresh.md` + per-mechanism diagnostics JSON + diagnostics summary | **4 mechanisms / 5 pooled tests all `REJECT`**, well-powered (`N_eff` tens-to-hundreds of thousands, usable `MDE(\|IC\|)`), near-zero Pearson IC, non-monotonic buckets. `roll_week` carried as `DATA_GAP` (excluded). **0 survivors.** No `reviewer_verdict`. |
| **DK-P04** | YELLOW | One DIFFERENTIATED `context≠trigger` `SetupSpec` + `MechanismCard`, run through the SSRL `conditional_probe.py` (byte-unchanged) over **real** ES_2024 path labels; value-free `EVIDENCE.json` | `EXPLORATORY`, `promotion_eligible: false`; surrogate `ZERO_PASS_MET` (`run_count 64`, `gate_pass_count 0`). C1 distinct context vs trigger confirmed. **Honest substrate `DATA_GAP`**: the only materialized 120m `target_before_stop` slice is single-class (all `False`, `horizon_no_barrier`) → conditioning not exercised; **no fabricated values**. Probe plumbing validated; bet UNANSWERED. Refused by the promotion path (canary). |
| **DK-P05** | YELLOW | This closeout: `CAMPAIGN_VERDICT.md` (per-item states + boundary roll-up + survivor gate), `RUN_SUMMARY.md`, handoff | **Aggregation + adjudication only** (no new study/metric/calibration). **0 survivors** documented as a conclusive trustworthy negative; no factory by inertia. |

## Final Boundary + Survivor Gate

| State | Track A | Track B | Total items |
| --- | ---: | ---: | ---: |
| `REJECT` | 4 mechanisms / 5 scored tests | 0 | 4 |
| `INCONCLUSIVE` (+`reason_code` = `DATA_GAP`) | 1 (`roll_week_flow`) | 1 (single-class 120m slice) | 2 |
| `WATCH` | 0 | 0 | 0 |
| `CANDIDATE_RESEARCH` | 0 | 0 | 0 |
| **Total** | **5** | **1** | **6** |

**Survivor count = 0.** No-survivor branch of the asymmetric survivor gate: no `reviewer_verdict`
survivor artifact is required; nothing surfaced for a survivor-gate decision; **nothing promoted**.
The four gated mechanisms are a **well-powered CLEAN NULL → conclusive kill-shot**; `roll_week` and
Track B are **substrate `DATA_GAP`s (UNANSWERED), not nulls and not `REJECT`s**. The trustworthy-negative
argument (FDR-before-metric + surrogate zero-pass incl. fail-closed `roll_week` + planted/true-alpha
canaries green + well-powered reads) is recorded in `CAMPAIGN_VERDICT.md` and is **earned, not
asserted**.

## Substrate-Gap Recovery (the operational story)

Two substrate gaps were hit and handled **honestly** rather than papered over:

- **`roll_week` (Track A):** the offline `in_roll_window_flag` is all-null / zero-variance across all
  24 partitions (R-036 constraint). DK-P02 **fail-closed** (`CALIBRATION_BLOCKED` /
  `no_numeric_declared_factors_for_surrogate`) instead of fabricating a pass, and DK-P03 excluded it
  from any real-metric read. Carried as `INCONCLUSIVE` + `DATA_GAP`, never as `REJECT`.
- **Track B 120m path slice:** DK-P04 ran on real ES_2024 rows, but the only materialized 120m
  `target_before_stop` slice (`ES_2024_120m_lcfp_p08_es_202406`, the LCFP-P08 June-2024 benchmark) was
  single-class (every outcome `False`, `horizon_no_barrier`), so the context≠trigger conditioning
  could not be exercised. Reported as an `EXPLORATORY` substrate-coverage `DATA_GAP` with
  `single_class_path_outcome: true` and `fabricated_values: false` — **not** a clean null, **not** a
  failure. The probe plumbing (real Parquet load via the tools-side `core.value_store` loader → rows
  injected into the byte-unchanged pure probe → label-shuffle surrogate → value-free EVIDENCE) is
  validated end-to-end.

Both gaps were absorbed into the verdict taxonomy as honest `DATA_GAP`s; neither was allowed to become
a false `REJECT` or a fabricated pass. This is the discipline that makes the 0-survivor result
trustworthy.

## Shipyard `--workers` Refit (in-flight harness improvement)

Mid-campaign, `SHIPYARD SURROGATE_FDR_CALIBRATION_PARALLELISM_V1` (PR #448, merged before DK-P04)
added a **byte-identical `--workers`** option + RAM planner to the surrogate-FDR calibration path, so
the calibration phases run faster without changing any value (byte-identical output is the
correctness contract). DK-P03 / DK-P04 then ran RAM-safe on the 40 GB box: DK-P03 used a
`day_of_week + month_end` parallel pair then serial `opex` / `open_close` (pair peak ~15.6 GB RSS,
single-process peak ~11.4 GB, `free -m` available never below ~24 GB, well above the 6 GB floor);
DK-P04 peaked at ~0.73 GB. Scratch was cleaned on completion (`finally: shutil.rmtree`).

## Coordinator-Driven Execution

The campaign ran as a coordinator-driven sequence of isolated git worktrees (one per phase:
`dk-p02`, `dk-p03`, `dk-p04`, and this `dk-p05`), each branched off `main`, reviewed, and merged by
the coordinator (PRs #443–#449 plus the shipyard #448). DK-P05 was authored in an isolated worktree
and opens a closeout PR; **the coordinator owns the merge and any state surgery** (no self-merge).

## Cost / Lessons

- **Compute:** the campaign's real metric was four pooled factor-diagnostics runs (DK-P03) + one
  conditional probe (DK-P04), all on locally-materialized values with no external provider / network
  call. RAM-bounded, scratch-cleaned, no new dependency.
- **The substrate-gap-as-honest-`DATA_GAP` discipline is the load-bearing lesson:** a fail-closed
  surrogate gate (`roll_week`) and a single-class outcome slice (Track B) were both reported as
  `DATA_GAP`, not forced into `REJECT` / a fabricated pass. The 0-survivor verdict is conclusive on
  the 4 gated mechanisms **because** the gaps were named, not hidden.
- **FDR-before-metric held mechanically:** the value-free restatement predated every variant; the
  surrogate zero-pass gate preceded every real metric; the down-scope stayed a pre-registration note
  (not a strictly-increasing `BudgetAmendmentRecord`).
- **Carried-evidence non-claims (C2/C3) survived aggregation:** SSRL first-light stays a `DATA_GAP`
  (not cited as evidence); the de-stack `0.068 / 6862` stays a restatement (not corroboration).

## Carried Caveats (forward)

All caveats from `CAMPAIGN_VERDICT.md` are carried forward: zero-feed calendar approximations
(analytic third-Friday opex/quad-witch; month/quarter-end = last covered-window trading session,
non-exchange-official; analytic CME quarterly `in_roll_window`); month/quarter-end 2024-26 coverage;
within-mechanism near-duplicate secondary exposures (not independent tests); first-order `N_eff` /
power / MDE limits (`statistical_validity_claim: false`, rows not independent); `roll_week` `DATA_GAP`;
Track B single-class-slice `DATA_GAP`; `fomc` / `cpi` DEFERRED = `needs_paid_data`; governed overnight
family DEFERRED (no cards this round, RED at paper/live); C2/C3 non-claims.

---

## POST-DK Adjudication — Next-Shot Recommendation (for the coordinator / Captain)

**This is a recommendation, NOT a launch and NOT a new campaign contract.** Per the spec's Non-Goals,
authoring or queueing the next campaign is a separate, triggered, user-owned decision. This section
adjudicates the fork with evidence so the Captain can decide.

### The fork

- **(A) Close the Track-B substrate gap + re-run the SAME pre-registered probe** on a barrier-resolving
  120m `target_before_stop` path-label slice (the DATA_GAP "close the gap and re-run" doctrine — **no
  new mechanism, no hypothesis change, no new data buy**), so the context≠trigger conditioning is
  actually exercised.
- **(B) Move to a fresh narrow EXISTING-DATA shot:** `GOVERNED_OVERNIGHT_KILLSHOT_V1`, or
  `STRATEGY_SHAPED_KILLSHOT_V2`, or a PA/VWAP setup shot (Compass §9 + the night-sailing addendum).
  **No universe expansion, no paid data.**

### Feasibility check for (A) — verified against existing local data (load-bearing)

The Track B `DATA_GAP` was caused **only** by the specific slice DK-P04 happened to use — the narrow
LCFP-P08 **June-2024** benchmark slice (`ES_2024_120m_lcfp_p08_es_202406`), which is single-class
(barrier never hit). It is **not** a property of the substrate at large. Inspection of the durable
materialized label store confirms full-year 120m `target_before_stop` path slices exist for **ES/NQ/RTY
across 2019-2026** (e.g. `labels/materialized/futures_substrate_scaleout_v1/path/.../ES_2020_120m/`),
already materialized, with **zero new data required**. A direct value-distribution check of one
candidate full-year slice (sanctioned `core.value_store` loader, read-only) found:

- **`ES_2020_120m` (full-year, high-volatility COVID period): 313,156 `target_before_stop` events,
  309,206 `False` AND 3,950 `True` — barrier-resolving (NOT single-class).**

So a non-degenerate 120m `target_before_stop` slice **is materializable / already materialized** from
existing ES/NQ/RTY data. Option (A) is **feasible with zero new data and zero new mechanism** — it is
the textbook DATA_GAP "close the gap and re-run the same pre-registered probe" move.

### Recommendation: **(A) — close the Track-B substrate gap and re-run the same pre-registered probe.**

**Reasoning:**

1. **The bet is UNANSWERED, not answered.** Track A is now a solid, well-powered clean null — that
   question is closed. But the differentiated *context≠trigger* thesis (the genuinely novel,
   strategy-shaped part of this campaign, and the reason SSRL was built) was **never actually tested**:
   the conditioning could not be exercised on a single-class slice. Moving to a new shot (B) would
   leave the campaign's headline differentiated bet permanently unevaluated for a purely accidental
   substrate reason. Closing a known, cheap, zero-new-data gap before declaring the *idea* dead is the
   honest sequence (and the explicit "close the gap and re-run" DATA_GAP doctrine).
2. **It is the cheapest unexhausted test.** No new mechanism, no hypothesis change, no new data, no
   universe expansion, no paid feed. The probe engine (`conditional_probe.py`), the SetupSpec /
   MechanismCard, the surrogate gate, the variant ledger, and the tools-side row-injection harness all
   already exist and are validated end-to-end (DK-P04 proved the plumbing). The only change is pointing
   the harness at a barrier-resolving full-year slice that already exists on disk.
3. **It maximally reuses, minimally risks (REUSE-MAP rule).** Re-running the **same pre-registered**
   probe stays inside the FDR active-subset surface (the family budget already accounted for one Track B
   variant) and keeps the EXPLORATORY quarantine intact — it does not open a new family or a new budget.
   A fresh shot (B) would consume new pre-registered budget and new authoring/review cycles for an idea
   class (overnight / new PA setup) that has **not** earned priority over an unanswered in-scope bet.
4. **It respects the Compass Stage D(a) sequence.** §3 Stage D's 0-survivor branch (a) is "next narrow
   kill-shot from differentiated mechanisms already in scope … before any data buy." The context≠trigger
   probe **is** that already-in-scope differentiated mechanism; finishing it is more faithful to the
   roadmap than jumping to the overnight family (which Compass §7.7 / the design note hold to a stricter
   RED-lane gap-risk standard and which has **no cards authored** — it is further from ready).

**Honest caveat on (A):** re-running on a barrier-resolving slice may itself land a clean null (the
context≠trigger bet may simply not carry signal), or may surface a `WATCH`/`CANDIDATE_RESEARCH` that
must then be surfaced under the survivor gate. Either is a **conclusive** outcome and is the point —
the goal is to *answer* the bet, not to confirm a prior. The re-run must keep the same pre-registered
SetupSpec / threshold / geometry (no post-hoc tuning), keep the surrogate-FDR zero-pass gate as a hard
precondition, keep the EXPLORATORY quarantine, and report `statistical_validity_claim: false` (`N_eff`
will rise on the larger slice but pooled-row independence still does not hold).

### Why NOT (B) yet

A fresh existing-data shot (overnight / strategy-shaped v2 / PA-VWAP setup) is a **legitimate and
reachable** next move and stays available (Compass §3 Stage D branches (a)–(e); the overnight family
design note is already written). But it is **second**, not first, because:

- it would **abandon an unanswered, cheap, in-scope bet** (the context≠trigger probe) to start a new
  one — the opposite of "run the cheapest unexhausted test now";
- the **governed overnight family is the furthest from ready**: no mechanism cards, no `LabelSpec`, no
  `FeatureRequest` authored (only a value-free design note), and it is **RED-lane at paper/live**
  (gap-risk approval gate) — materially more authoring + review + risk surface than re-pointing an
  existing, validated probe at an existing slice;
- a new `STRATEGY_SHAPED_KILLSHOT_V2` / PA-VWAP setup shot consumes **new pre-registered FDR budget**
  and new author→review→verdict latency for an idea class that has not earned priority over the
  in-flight differentiated bet.

If (A) is run and the context≠trigger bet lands a clean, well-powered null (or exhausts), **then** (B)
— a fresh narrow existing-data shot — becomes the natural next move, and the overnight-family cards /
`LabelSpec` authoring (Yellow, value-free) can be queued behind its trigger. The macro-surprise cards
(`fomc` / `cpi`) and any universe / paid-data expansion remain DEFERRED behind their explicit triggers
regardless.

> **For the Captain:** this is a recommendation only. No probe was re-run, no slice was re-materialized,
> no campaign was authored or queued in this phase. The next-shot launch is a separate, triggered,
> user-owned decision.
