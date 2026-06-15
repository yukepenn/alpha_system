# Powered Discovery Batch V0 — Ground Truth and Corrected Route

Status: decision note (2026-06-15). Author: coordinator (Claude Opus), grounded by
a 4-lane repo/registry reconnaissance crew. This note records what the repo
**actually** supports (verified against code + the live SQLite registries +
on-disk parquet) and the corrected forward route. It exists to keep the next
discovery batch grounded in repo truth rather than in repo-blind assumptions.

> Provenance: an external advisor (no repo access) proposed a multi-year powered
> discovery plan. The direction was largely right; several load-bearing execution
> assumptions were wrong. This note keeps the right parts and corrects the wrong
> parts with `file:symbol` / query evidence. Treat advisor text as a hypothesis
> source, not as repo fact (AGENTS.md headless trust boundary).

## 1. Verified ground truth (what exists today)

**Data substrate — VERIFIED dense (zero new materialization needed):**
- `cost_adjusted_fwd_ret`, `spread_adjusted_fwd_ret`, `fwd_ret_{1m,3m,5m,10m,15m,30m,60m,120m,240m}`,
  and path labels `path_{mfe,mae,target_before_stop,triple_barrier}` are REGISTERED
  and on-disk for **ES, NQ, RTY × 2019–2025 (full years) + 2026 (PARTIAL, through
  2026-05-29 only)**. (Continuous fwd-ret = {1m…240m}; path labels = {5m…240m}.)
- 54 REGISTERED `feature_id`s per instrument-year, covering VWAP/PA
  (`base_ohlcv_*`), liquidity/tradability (`bbo_tradability_*`), PA structure
  (`liquidity_structure_*`), session/calendar (`session_calendar_roll_*`), and
  cross-market (`cross_market_*`, stored on a combined `ES_NQ_RTY_<year>_full_year`
  partition).
- Partition naming (load-bearing): labels `<INST>_<YEAR>_<HORIZON>` (e.g.
  `ES_2021_60m`); features `<INST>_<YEAR>_full_year` (horizon-agnostic).
- `dataset_version_id` is **per-year**, not global. Authoring a non-2020 seed is a
  coordinated swap of `partition_id` + per-year `dataset_version_id` + per-year
  REGISTERED `feature_version_id`/`label_version_id` — never a naive year-string
  swap. Cross-market features sit on a different per-year dsv lineage than base
  features (do not mix them in one slice under a single expected dsv).

**Engine reach — what runs end-to-end via `alpha idea run`:**
- `main_effect` lane: factor IC (Pearson + rank) vs a continuous label, now with
  **overlap-aware N_eff** (PR #474, [[law-overlap-aware-ic-power-n-eff]]).
- `context_not_equal_trigger` (setup) lane: a two-factor context≠trigger
  exploratory probe over **pre-materialized path labels**, gated by a label-shuffle
  zero-pass surrogate-FDR gate + family variant budget.
- Anti-p-hacking gates that are REAL and wired in the fast lane: variant/family
  budget enforcement (`variant_ledger.py evaluate_family_budget`), zero-pass
  surrogate gate (`conditional_probe.py` → `surrogate_run.py ZERO_PASS_MET`), and
  dedup (`duplicate_exposure.py check_duplicate_exposure` + `agent_factory/memory
  detect_duplicate_idea`).

## 2. Corrections to the repo-blind plan (verified REFUTED / overstated)

1. **Multi-year pooled probes do NOT exist.** `fast_probe`/`SliceSpec` is strictly
   ONE `(instrument, year, horizon)` partition; the resolver enforces single-
   partition match (the only relaxation is same-instrument-same-year
   `full_year`→`<horizon>` feature serving). A "2019–2021 discovery pool" is
   therefore **not a single probe**. `governance/pooled_hypothesis.py` is a
   value-free meta-aggregation over already-computed per-member metric records, not
   a data-level multi-partition scan. → Multi-year evidence must be produced as
   **per-year probes + cross-year aggregation**, or by building a new pooling
   capability. We choose aggregation (REUSE), see §4.

2. **The setup lane does not compute `expected_R` / `hit_rate vs base_rate` /
   cost-adjusted expectancy today.** `conditional_probe.evaluate_setup_conditional_probe`
   emits exactly `target_before_stop_probability` + `post_event_mfe_mae` (+ power +
   surrogate gate + variant binding). `expected_R`, base-rate lift, `triple_barrier`
   as a probe diagnostic, and `time_to_target/stop` are **not wired** (some helper
   functions exist in `research/management_features.py` / `research/diagnostics.py`
   / `research/events.py event_study` but are not called by the probe). Path-label
   stop/target/R geometry is **content-hash-frozen at materialization**, so every
   new R-geometry is a re-materialized label = a counted variant (advisor correct
   on this point).

3. **The "trusted slow path" that produces an `EvidenceBundle` does not exist as an
   executable producer.** `promotion_gate`, `PromotionDecision`, `EvidenceBundle`,
   `TrialLedger`, `ReviewerVerdict` are all real fail-closed CONTRACTS with a wired
   state machine, but every fast-path readout is hard-stamped `EXPLORATORY` and
   refused as promotion evidence; `EvidenceBundle`s are only minted by canaries and
   surrogate calibration. `FactorLibrary` has no store (survivor count = 0);
   `AlphaBook` is an enum value only. → **L0–L2 are executable; L3+ is
   enforced-as-refusal scaffold.** Promotion is deliberately not buildable from the
   fast lane — by design, not by accident.

## 3. The evidence ladder — with honest current reach

| Level | Meaning | Reachable today? |
|---|---|---|
| L0 Idea | MechanismCard / AlphaSpec / idea.yaml; no evidence | ✅ executable |
| L1 Diagnostic | IC (main_effect) or path-outcome (setup) under honest power; non-promoting | ✅ executable |
| L2 Signal-pending-reviewer | machine-classified resolved signal on a non-promoting shelf | ✅ executable |
| L3 WATCH / CANDIDATE_RESEARCH | independent reviewer approves a trusted follow-up | ⛔ scaffold (no trusted-study executor) |
| L4 FactorLibrary survivor | trusted StudySpec + EvidenceBundle + ReviewerVerdict + TrialLedger + FDR + OOS/cost-stress | ⛔ scaffold (no store; survivor = 0) |
| L5 AlphaBook portfolio | low-correlation survivor ensemble | ⛔ not built (enum only) |
| L6 shadow → paper → canary → ramp | staged trust rail before capital | ⛔ not built (human-gated) |

**The rail (unchanged law):** the machine may CLASSIFY evidence autonomously (L0→L2)
but may NEVER PROMOTE it (L3+). IC is the L1 diagnostic for factor-shaped ideas;
path-outcome is the L1 diagnostic for setup-shaped ideas; **neither is a graduation
certificate.** A single calendar year is a smoke / first-powered slice, never
final evidence; research evidence requires cross-year consistency under honest
overlap-aware power; promotion evidence requires the (not-yet-built) trusted path.

## 4. Corrected route (the actual optimal next moves)

Search broadly for ideas; test narrowly with pre-registration. The binding
constraint on honest powered discovery is **sample independence**: single-year
60m honest N_eff ≈ rows/60 ⇒ MDE ≈ 0.027, a brutal floor at which most factor ICs
are nulls. The highest-leverage unlock is cross-year evidence — built by REUSE,
not a risky new pooling engine.

**Pre-registered windows (declared before metric; do not shop after results):**
- Discovery: 2019–2021 · Validation: 2022–2024 · Locked: 2025–2026(partial,
  through 2026-05-29). Locked stays sealed until a reviewer-approved candidate
  stage (which does not exist yet — so locked is sealed for the foreseeable batch).
- Universe: ES/NQ/RTY only. Primary label: `cost_adjusted_fwd_ret`. Each
  `factor × label × horizon × instrument × year` is a counted variant.

**Build order (each a small, tested, REUSE-first PR):**
1. **Multi-year cross-year-consistency aggregation** (the unlock): run the same
   factor through per-year `main_effect` probes across the discovery years, then
   aggregate the per-year IC readouts via the EXISTING `pooled_hypothesis`
   meta-aggregation into a cross-year consistency verdict (sign stability +
   overlap-aware-N_eff-weighted combination). This tests regime robustness instead
   of assuming stationarity (naive row-pooling would assume the very thing we test).
   Do NOT build a new pooling engine; wire existing primitives.
2. **DeepResearch idea sourcing + REUSE/dedup** → an `IDEA_BACKLOG.md` of 50–100
   ideas (factor-shaped + setup-shaped), collapsed to canonical families, filtered
   against graveyard/requeue/duplicate_exposure, no re-running of already-rejected
   exposures (e.g. simple day_of_week/opex/month_end/open_close calendar effects).
3. **Batch 0**: 10–20 canonical ideas through the right lane (factor → main_effect
   cross-year; setup → context≠trigger), all pre-registered, all memory-routed,
   all overlap-aware. Crew-parallelize only after one runs clean.
4. **(Deferred, separate decision)** setup-lane diagnostic enrichment (`expected_R`,
   base-rate lift) and the trusted-study executor (L3→L4 bridge) — both are real
   capability gaps, both larger, both to be chartered only when a cross-year signal
   actually earns them (anti-bloat: build on trigger, not by sequence).

**Out of scope / hard stops (unchanged):** no paid data, no universe expansion, no
FactorLibrary/AlphaBook before a reviewed survivor, no paper/live/broker, no raw-row
N_eff, no horizon/threshold/R-geometry/label shopping after results, no committing
raw/canonical/value parquet or SQLite, no weakening of no-lookahead/FDR/ledger/
no-second-truth rails. ML/CUDA are speed/meta-labeling tools, never an evidence
shortcut (Compass §5).
