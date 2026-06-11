# Alpha System Operating Compass v4.3 — Consolidated Roadmap

Status: canonical. Supersedes Compass v2 / v2.1 / v3 / v3.5 (chat-only). Where
older routes conflict with this document, this document wins. Live phase status
always comes from `python tools/frontier/status_doctor.py`, never from this
file.

Adopted 2026-06-10; patched to v4.1 same day (user review: power numbers = planning priors; pooled-evaluation hard rules; primary_state + reason_code taxonomy; Stage B parallelism limits; kill-shot Track A/B split; narrowed FactorLibrary trigger; engine policy live-state vs permanent; non-binding ETAs; ambition clause). Inputs: Compass v2.1 (post-Core-Pilot consolidation),
Compass v3/v3.5 (Trustworthy Verdict First), the LCFP/FUTSUB execution record,
and the coordinator's statistical power analysis (§2).

---

## 0. Identity and North Star (unchanged, permanent)

alpha_system is a **local-first, evidence-gated, cost-aware, agent-assisted
futures intraday alpha factory**. It is not a backtester, not a strategy repo,
not a broker/live system, and never an AI-powered p-hacking machine.

```text
North star:
  Maximize robust out-of-sample, cost-adjusted, capacity-aware,
  low-correlation intraday Sharpe,
  subject to drawdown, turnover, liquidity, execution,
  and reproducibility constraints.
```

Commercial endpoint: a continuously-maintained portfolio of multiple active,
low-correlation, cost-surviving intraday futures alphas — discovered,
validated, combined, monitored, deweighted, rotated, and retired by the
factory — traded first as shadow, then paper, then micro-contract canary
(MES/MNQ/M2K), then ramped. Positive live PnL is the goal, never a promise the
system can make in advance; what the system maximizes is true discovery rate
and minimizes is false discovery, cost fantasy, capacity illusion, and decay
blindness.

### Performance target calibration (added 2026-06-10, user-set)

```text
Design floor (the portfolio mission is not accomplished below this):
  realized book Sharpe >= 2.0
  via 6-10+ validated low-correlation edges. Individual factor SR 0.3-0.8
  is the expected INPUT grade; the BOOK, not the factor, carries the target.

Stretch:
  book Sharpe 3+ via universe expansion (rates/FX/commodities),
  TBBO-calibrated execution realism, and 10-15 active edges.

Return level:
  chosen by LEVERAGE only after realized Sharpe is proven (Sharpe is
  leverage-invariant). At Sharpe 2 with a 15% max-drawdown budget, expect
  order 30-60%/yr; at Sharpe 3, ~60-100%/yr. Small-account capacity
  freedom (intraday micros) is a structural advantage: realized Sharpe
  here can exceed fund-scale benchmarks.

Ambition clause (user-set, 2026-06-10):
  All targets above are FLOORS, not ceilings. The factory's standing
  mission is to keep accumulating low-correlation edges without any
  documented-precedent argument used as a reason to stop; the aspirational
  asymptote is on the order of ~1%/day portfolio growth, pursued by edge
  accumulation (intraday PA, cross-asset spread, futures imbalance, and
  whatever the mining loop discovers) until the binding constraint becomes
  own-size liquidity impact and the associated alpha decay — a constraint
  the system should eventually MEASURE (capacity/impact monitoring), not
  assume. What stays non-negotiable on the way up: promotion is
  evidence-gated, return is realized through Sharpe-then-leverage (never
  by reaching for a daily-return number directly), and the drawdown
  budget binds at every step. For honest planning: 1%/day at book
  Sharpe 2 implies ~8% daily volatility and 40-60% drawdowns; the
  evidence ladder must therefore climb through realized Sharpe tiers
  (2 → 3 → 4+) with capacity headroom checks before each leverage step.
  Aim unbounded; promote bounded.
```

Permanent boundaries (any design that blurs one is wrong):

```text
Data ≠ Feature ≠ Factor ≠ Signal ≠ Strategy ≠ Portfolio ≠ Execution
Fast path ≠ Reference truth
Runtime diagnostics ≠ Strategy Reference validation
Validated research ≠ paper/live approval
Candidate ≠ capital allocation
Agent ≠ autonomous trader / self-reviewer / self-promoter
Sandbox/exploratory output ≠ promotion evidence
```

Operating rule (Compass v3, retained): **every campaign must (1) remove a
current blocker, (2) run a kill-shot experiment, or (3) validate a survivor —
otherwise it waits.** Before building anything, produce a REUSE MAP
(inspect-before-build; smallest upgrade from current state; never rebuild
existing ledgers/schemas/canaries/registries).

---

## 1. The layer model (fixed)

```text
Data Truth (Databento OHLCV+BBO; IBKR validation; TBBO/MBP-1 later; L2 much later)
→ Canonical Data / DatasetVersion registry
→ Feature / Label Layer (content-addressed, point-in-time, Parquet values,
  per-family engine policy: fast where benchmarked faster, reference oracle forever)
→ Research Runtime (diagnostics, probes, bounded grids, cost stress, no-lookahead)
→ AI Agent Factory (role contracts, separation of duties)
→ Discovery Rigor Floor (ledgers, variant budgets, holdout, canaries) ← gate layer
→ Kill-shot studies / bounded mining
→ FactorLibrary (evidence-backed memory)          [conditional]
→ Strategy Reference Validation (survivor-only)   [conditional]
→ Portfolio AlphaBook (marginal utility)          [conditional]
→ Research Runner (continuous factory)            [conditional]
→ Shadow / Decay monitoring → ML meta-labeling    [conditional]
→ Paper governance → Live canary → ramp           [RED lane, human-gated]
```

Storage/compute doctrine (ADR-0006/0007, unchanged): Parquet = research-scale
values; JSONL = audit/smoke/sample only; SQLite = metadata/pointer/lineage/hash
only; DuckDB/Polars = scans/joins; NumPy/Numba = hot loops; Workflow 2/Ralph =
process, gates, serial merge.

---

## 2. The math that shapes the whole roadmap (planning priors, NOT hard gates)

[v4.1] Everything in this section is a **planning prior / power heuristic**,
never an automatic pass/fail threshold. Our data is not IID annual returns:
labels overlap (severely at 15m+), session/regime autocorrelation exists, cost
and spread states are non-stationary, and IC diagnostics have different
statistical structure than strategy PnL. Actual detectability must be measured
per study using N_eff, purged/embargoed folds, day/session-level aggregation,
and block-bootstrap / HAC-style robustness where appropriate. Final evidence =
pre-registered splits + N_eff + cost stress + VariantLedger + holdout
discipline + reviewer verdict — not a formula.

```text
heuristic: t ≈ SR_annual × sqrt(years)            (planning prior only)
2σ single-test detectability:        SR ≈ 0.75–0.85
after multiple-testing correction
(6 families × bounded variants):     SR ≈ 1.1–1.2 effectively required
```

Consequences, baked into every stage below:

1. **Individually-validatable edges (true SR ≥ ~1.1) will be rare.** Most real
   edges in this space are weak (SR 0.3–0.8) and usually cannot clear a
   single-signal bar on 7 years. Therefore the system must support
   **pre-declared pooled evaluation** — under strict rules [v4.1]:

   ```text
   ALLOWED pooled evaluation:
     declared BEFORE seeing any results
     mechanism-based rationale
     fixed inclusion rule (membership cannot change post hoc)
     fixed weighting / aggregation rule
     fixed horizon / session / symbol set
     logged as ONE VariantLedger hypothesis
     pooled result AND individual components both reported

   FORBIDDEN pooled evaluation (= p-hacking, refuse):
     pooling after seeing which members worked
     dropping losers post hoc
     changing weights after validation
     trying many pool compositions and reporting one
     using the locked test to select the pool
   ```

2. **Verdict taxonomy: primary_state + reason_code** [v4.1 — keeps the existing
   four-state boundary; reasons are codes, not new states]:

   ```text
   primary_state:  REJECT / INCONCLUSIVE / WATCH / CANDIDATE_RESEARCH
   reason_code:    UNDERPOWERED / SUBSTRATE_GAP / COST_FRAGILE /
                   DATA_QUALITY / LEAKAGE_BLOCKED / DUPLICATE_EXPOSURE /
                   REGIME_UNSTABLE / BBO_PROXY_LIMITATION
   ```

   `INCONCLUSIVE + UNDERPOWERED` is eligible for pre-declared pooled retest;
   `INCONCLUSIVE + SUBSTRATE_GAP` is eligible for retest after blocker removal.
   Display names like "INCONCLUSIVE_UNDERPOWERED" are fine; registry/schema
   layers keep state + code separate. This taxonomy is a Rigor Floor
   deliverable that EXTENDS the existing Core Pilot verdict machinery.
3. **The VariantLedger is the keystone gate.** Deflated-Sharpe math is only as
   honest as the variant count. Tool-boundary auto-increment (every StudySpec
   run logged, no manual reconciliation) is mandatory before the kill-shot.
4. **Portfolio utility is the real unit of account.** A pooled book of eight
   SR-0.4 low-correlation edges ≈ SR 1.1+ portfolio. The factory's economic
   output is the book, not any single factor. This is why the user's goal
   ("multiple active factors, add/rotate/retire, no factor limit") and the
   verdict-first discipline are the same goal, not in tension.

---

## 3. The route — stages, gates, triggers

Each stage lists ENTRY (trigger), WORK, EXIT (gate). Conditional stages do not
start until their trigger fires. [v4.1] All ETAs are non-binding informational
estimates and never override `status_doctor` / live run-state.

### Stage A — FUTSUB minimum trusted substrate  [ACTIVE]

- ENTRY: now (P19 executing on per-family engine policy).
- WORK: P19 cost-adjusted tail (reference, checkpoint-resumed) → P20 path
  labels (V1 fast, workers 8, 10.2x) → P21 guard audit → P22 registry/resolver
  smoke → P23 label coverage → P24 walk-forward/purge/embargo wiring → P25
  N_eff/overlap reporting → P26 BBO/cross-market matrices.
- DISCIPLINE: minimum substrate only — each of P21–P26 is checked against "do
  the six INCONCLUSIVE families need this to rerun?"; anything beyond that bar
  is deferred, not silently expanded.
- EXIT: the six previously-INCONCLUSIVE Core Pilot families can rerun with no
  missing packs, labels, BBO primitives, guards, or N_eff metadata.
- ETA: ~1–2 days.

### Stage B — Discovery Rigor Floor  [next; prep may overlap A's tail]

- [v4.1] PARALLELISM LIMITS: while Stage A is in flight, ONLY value-free prep
  may overlap — REUSE MAP inspection, campaign-file drafting, docs/tests,
  VariantLedger design. FORBIDDEN until Stage A exits: mutating active
  StudySpec semantics, changing verdict schemas an in-flight phase consumes,
  consuming incomplete label substrate, or starting the kill-shot. Stage B's
  enforcement gates must be ACTIVE before CORE_PILOT_RERUN begins.
- ENTRY: REUSE MAP of existing governance surfaces (TrialLedger,
  RejectedIdeaLedger, duplicate-exposure hints, canary runner, locked-test
  policy, EvidenceBundle/FactorCard schemas) — inspect before building;
  smallest upgrade wins.
- WORK (upgrades, not rebuilds):
  1. TrialLedger / RejectedIdeaLedger: campaign-scoped → platform-cumulative;
     manual → tool-boundary auto-incrementing; recording → promotion-gating.
  2. VariantLedger: every StudySpec execution auto-logged with family budget
     accounting (keystone gate, see §2.3).
  3. Sealed holdout + holdout-access guard with contamination ledger
     (baseline split: 2019–2021 discovery / 2022–2024 validation /
     2025→latest locked test; family half-life protocols pre-registered, not
     split-shopped).
  4. Planted fake-alpha canary: a synthetic lookahead-contaminated factor must
     be REJECTED by the pipeline end-to-end, or the floor fails closed.
  5. No-leakage promotion blocker; BBO-proxy disclaimer gate; second-PnL-truth
     canary (DONE, PR #332).
  6. Verdict taxonomy upgrade (§2.2) incl. pre-declared pooled-evaluation
     support in StudySpec.
- REVIEW CONTRACT (permanent from here on): reviewer verdicts must cite
  deterministic evidence — ledger completeness, variant count, holdout access
  report, canary results, no-lookahead audit, cost report, duplicate-exposure
  status, resolver smoke. Prose alone gates nothing.
- EXIT: nothing can become WATCH/CANDIDATE unless ledgered, variant-counted,
  leakage-clean, holdout-disciplined, fake-alpha-tested, second-truth-clean,
  reviewer-approved. ETA: ~1–2 days of campaign work.

### Stage C — CORE_PILOT_RERUN_V1 (the kill-shot)  [the point of everything above]

- ENTRY: Stage A + B exits green. Named explicitly; realized as FUTSUB P27–P29
  (re-lock StudySpecs, rerun, honest verdict refresh) if the do-not-duplicate
  check at the P26/P27 boundary confirms; else a narrow named campaign.
- WORK [v4.1 — two strictly separated tracks]:
  - **Track A — Exact rerun:** the same (or faithfully translated) six
    previously-INCONCLUSIVE Core Pilot studies on trusted substrate + rigor
    floor, pre-declared variant budgets per family. Track A verdicts stand on
    their own and are never rewritten by Track B.
  - **Track B — Pre-declared pooled supplemental tests (optional):**
    mechanism-justified pooled hypotheses (cross-symbol, cross-horizon),
    REGISTERED BEFORE any Track A rerun metric is inspected, logged as
    separate pooled VariantLedger hypotheses per §2.1 rules.
  - No new alpha batch, no broad mining.
- OUTPUT: each study gets primary_state + reason_code (REJECT / INCONCLUSIVE
  [UNDERPOWERED | SUBSTRATE_GAP — must name the gap] / WATCH /
  CANDIDATE_RESEARCH), Track A and Track B reported separately.
- SUCCESS = conclusive, not positive. Zero clean survivors with no substrate
  excuse remaining is a successful kill-shot.
- ETA: days, not weeks (labels are fast now; diagnostics are cheap).

### Stage D — Survivor gate (route branches on evidence)

```text
0 survivors (all clean REJECT):
  → POST_KILLSHOT_DIAGNOSIS, not factory building. Ranked hypotheses to test:
    (a) idea quality: the six families are crowded priors → next narrow
        kill-shot from differentiated mechanisms (event-time bars, overnight/
        session-structure effects, cross-asset spillover) before any data buy;
    (b) horizon structure: pooled multi-horizon retest of UNDERPOWERED verdicts;
    (c) universe homogeneity: equity-index trio shares one beta → evaluate
        cross-asset expansion (Stage N trigger);
    (d) cost reality: if many die only at cost gates → Stage I sample-month
        calibration may rescue or confirm;
    (e) stop: if (a)-(d) are exhausted across 2-3 narrow kill-shots, that
        conclusion is itself valuable — revisit thesis with the human.
1 survivor:
  → minimal CandidateRecord/FactorCard (existing schemas), Strategy Reference
    next (Stage H). No AlphaBook, no FactorLibrary buildout.
2 survivors:
  → immediate orthogonality check (factor/signal/PnL-path correlation, regime
    overlap, shared exposure type, cost/turnover similarity). Same exposure =
    one survivor.
≥3 low-correlation survivors OR ≥1 validated pooled-family ensemble:
  → downstream portfolio path is earned: Stages E-J unlock.
```

### Stage E — Earned accelerants  [conditional]

- FEATURE_RESEARCH_FAST_LANE_V1 (ADR-0009 MVP: sandbox registry,
  SandboxFeatureResolver vs TrustedFeatureResolver fail-closed on UNVERIFIED,
  EXPLORATORY stamp, restricted expression spec, TTL/GC, promotion regenerates
  through trusted path). TRIGGER: survivors justify scaled search, OR
  post-kill-shot diagnosis names researcher iteration speed as the binding
  bottleneck. Not before.
- FAST_STRATEGY_SANDBOX_V1 (entry/stop/target/time-stop probes on path labels,
  BBO cost proxy, session/regime filters; EXPLORATORY only, never promotion
  evidence). TRIGGER: PA/strategy-shaped ideas dominate the queue or a
  survivor is strategy-like. The path-label substrate it needs already exists
  (LCFP).

### Stage F — ALPHA_MINING_V2  [conditional: survivor- or diagnosis-informed]

- Bounded, pre-declared (family budgets, variant budgets, horizons, sessions,
  DatasetVersions, locked-test policy) — never open-ended.
- Scope chosen by evidence from C/D, not by menu. Ensemble-aware: pooled
  hypotheses are first-class studies.
- Computed anti-crowding lands here (structural/correlation duplicate gates)
  if Stage B's inspection found only hint/manual duplicate machinery.
- Outputs only REJECT / INCONCLUSIVE_* / WATCH / CANDIDATE_RESEARCH.

### Stage G — FACTOR_LIBRARY_V1  [conditional — narrowed trigger, v4.1]

- TRIGGER: ≥1 WATCH/CANDIDATE_RESEARCH survivor, OR repeated manual research
  operation proves the ledger query surface is concretely blocking a named
  next campaign. Rejected-idea memory ALONE never triggers this stage — that
  function belongs to the Discovery Rigor Floor's TrialLedger/
  RejectedIdeaLedger upgrades (Stage B), not to a full FactorLibrary.
- Operational ingestion/query/memory over EXISTING schemas (FactorCard,
  EvidenceBundle, TrialLedger, PromotionDecision, FactorSpec — do not rebuild):
  EvidenceBundle→FactorCard ingestion, registry, verdict/decision links,
  rejected-idea memory, duplicate exposure groups, as-of point-in-time
  FactorLibrarySnapshot for walk-forward, query/list/search.
- Lifecycle: DRAFT / READY_FOR_STUDY / WATCH / CANDIDATE_RESEARCH /
  VALIDATED_RESEARCH / QUARANTINED / DEWEIGHTED / RETIRED / REJECTED.
  Forbidden states: LIVE_APPROVED, PRODUCTION_READY, CAPITAL_ALLOCATED.

### Stage H — STRATEGY_REFERENCE_VALIDATION_V1  [survivor-only]

- Conservative Reference 1m truth: next-bar semantics, same-bar ambiguity,
  fees/spread/slippage stress, drawdown/turnover accounting, bounded
  management grid. A factor candidate is not a strategy candidate until here.

### Stage I — Cost Reality Upgrade  [trigger: first CANDIDATE_RESEARCH]

- TBBO / MBP-1 SAMPLE MONTHS only (external paid data = hard-stop ask to the
  human first): effective spread, markouts, trade-side confirmation,
  thin-liquidity behavior → calibrate the BBO proxy. No full L2/MBO.
- Standing rule: no capital-relevant conclusion rests on the uncalibrated
  BBO proxy; cost_fragile (dies at double-cost) never validates.

### Stage J — PORTFOLIO_ALPHA_BOOK_V1  [trigger: ≥3 low-corr candidates or validated ensemble]

- Portfolio-level memory and allocation logic: marginal contribution,
  correlation clusters, capacity, drawdown contribution, regime/session/
  horizon exposure, weight/deweight/retire. Objective = marginal portfolio
  utility, never standalone Sharpe ranking. Weighting shrunk by posterior
  edge × orthogonality × capacity × confidence ÷ risk.

### Stage K — Shadow + Decay monitoring  [before any ML or paper]

- Live-like predictions, zero orders: feature/IC drift, bucket monotonicity,
  gross/net gap, cost-proxy drift, regime drift, posterior edge,
  quarantine/deweight/retire triggers. Decay is classified (data/infra vs
  signal vs monetization vs regime), never "lost 10 days → off".

### Stage L — ALPHA_AGENT_RESEARCH_RUNNER_V1  [the continuous factory]

- TRIGGER: the D→F→G loop has run manually at least once end-to-end and the
  human wants standing throughput.
- Daily/weekly multi-agent research queue over family budgets with full
  separation of duties (Scout proposes; Critic challenges; Runner executes;
  Reviewer verdicts; Librarian records; nobody self-promotes), feeding
  FactorLibrary and the AlphaBook rotation: new factors in, decayed factors
  deweighted/retired — the user's "multiple active factors, add/rotate/retire"
  steady state. This stage is where research throughput scales; it inherits
  every gate below it unchanged.

### Stage M — ML meta-labeling  [after stable base signals]

- take/skip, size buckets, regime routing, exit quality. Never first-stage
  black-box 1-minute direction prediction.

### Stage N — Universe expansion  [evidence-triggered, any time after D]

- TRIGGER: survivors are homogeneous (one equity-beta exposure), or the
  AlphaBook cannot reach low-correlation utility within ES/NQ/RTY.
- Candidates in order of data/mechanism leverage: rates (ZN/ZB), FX (6E/6J),
  commodities (CL/GC), vol (VX, licensing permitting). Each expansion = new
  Databento corpus = external cost = hard-stop ask. Substrate machinery
  (DatasetVersion → packs → labels → guards) is universe-generic by design;
  expansion is data + config, not new architecture.

### Stage O — Paper → Live canary → ramp  [RED lane, human-gated, last]

- Research validated → Shadow → ALPHA_PAPER_TRADING_GOVERNANCE_MVP (paper
  account, fill/slippage/reconciliation reality) → ALPHA_LIVE_CANARY_GOVERNANCE_V1
  (micros first: MES/MNQ/M2K; tiny risk; hard kill switch; max daily loss/order
  count/position; human approval; no overnight unless approved) → gradual ramp.
- Daily operation runs on four clocks: definitions slow (review-gated),
  calibration weekly/monthly, portfolio weights evidence-driven, execution/
  risk gates intraday. Estimates update fast; definitions change slowly;
  retirement only with evidence.

---

## 4. Standing doctrines (carried forward intact)

- **Horizon/session:** 1m = sampling not alpha horizon; 1–3m execution-fragile
  (stricter gates); 5–30m primary; 30m–4h extended (stronger overlap/regime
  tests); session-close / maintenance-flat valid; hard boundary = exchange
  maintenance/trade-date break, never midnight; ETH research-in-scope, not
  auto-trading-approved; point-in-time running_* features only.
- **Cost stack:** fees (versioned) + BBO spread crossing + bucketed slippage
  proxy; profiles zero_cost (diagnostic only) / base / stress_1 / stress_2 /
  double_cost; cost_fragile never validates; BBO is tradability proxy, not
  execution truth.
- **Walk-forward:** pre-registered per family half-life class (STRUCTURAL
  2–4y train / MEDIUM 1–2y / FAST 3m–1y); never split-shopped; locked test
  access always ledgered as contamination.
- **Agent constraints:** registry-resolved access only; no raw provider reads,
  no manual paths, no direct registry writes, no self-review/promotion, no
  unbounded grids, no profitability/tradability claims.
- **Engine policy [v4.1 — permanent doctrine vs live state]:** PERMANENT:
  reference engine remains the correctness oracle; a fast engine becomes the
  trusted production path per family ONLY after parity + benchmark gates;
  engine selection is recorded per family/version in the registry
  (producer_engine_id), never assumed. LIVE-STATE (changeable by future
  benchmarks, recorded here for context only): as of 2026-06-10, path +
  fixed_base fast, fixed_extended/close_out/cost_adjusted reference;
  reference-throughput upgrade path pre-authorized in
  docs/STRUCTURAL_BACKLOG.md §6.
- **Workflow:** every campaign = 6-file contract bundle + root
  ACTIVE_CAMPAIGN.md; frontier-plan → mock → live parallel; build parallel,
  merge serial; runs/** local-only; explicit staging; REUSE MAP before any new
  mechanism.

---

## 5. Decision checklist (apply to every new design)

1. Does it move us toward robust OOS, cost-adjusted, capacity-aware,
   low-correlation intraday Sharpe?
2. Does it preserve point-in-time correctness?
3. Does it reduce false discovery or enlarge the p-hacking surface?
4. Does it raise research throughput without bypassing evidence?
5. Does it make agents more constrained-and-useful or more free-and-dangerous?
6. Does it produce reusable contracts or one-off scripts?
7. Does it keep data/feature/factor/signal/strategy/portfolio/execution distinct?
8. Does it treat cost, slippage, and capacity honestly?
9. Does it improve marginal portfolio utility, not standalone Sharpe?
10. Does it keep research, shadow, paper, live, and capital strictly separate?
+ REUSE MAP: does it already exist; what is the smallest upgrade?
+ Compass rule: blocker, kill-shot, or survivor validation — else it waits.

---

## 6. Honest priors (scorable, written before the kill-shot)

Recorded 2026-06-10 so future evidence can grade them:

1. Kill-shot most likely yields 0–1 individually-validatable survivors; the
   most probable positive outcome is 1–2 pooled/ensemble WATCH verdicts from
   cross-market and regime-gated families.
2. The binding constraint after the kill-shot is more likely idea
   differentiation than infrastructure; the six families are crowded priors.
3. The weak-edge portfolio path (pre-declared ensembles → AlphaBook) is the
   most probable route to the commercial endpoint, not a single strong factor.
4. Cross-asset expansion (Stage N) becomes justified within 1–2 quarters if
   the trio's survivors share equity-beta exposure.
5. The factory's durable economic asset — regardless of survivor count — is
   the falling marginal cost of an honest verdict.

If the kill-shot contradicts these, the diagnosis branch (Stage D) wins over
the prior, by construction.

---

## 7. Upside options adopted post-v4.1 (v4.2, 2026-06-10 red-team)

Six gaps found by adversarial self-review; all additive, none delay the
kill-shot:

1. **Evidence-accrual loop.** The corpus grows ~36 symbol-months/year. Every
   `INCONCLUSIVE + UNDERPOWERED` verdict auto-requeues for retest when enough
   new accepted data lands to materially change its power. Time is an ally;
   underpowered is a queue state, not a tombstone. (Rigor Floor deliverable.)
2. **Pipeline FDR calibration (surrogate runs).** Beyond the single planted
   fake-alpha canary: periodically run the full study machinery on
   label-shuffled/surrogate data; any survivor = measured pipeline leakage.
   Cheap with fast labels; hardens the floor empirically. (Rigor Floor.)
3. **Economic event calendar substrate.** FOMC/CPI/NFP/OPEX/quad-witching
   calendar (essentially free data) becomes a substrate input before Mining
   V2; event-conditioned variants and event-day handling become declarable in
   StudySpecs. (Post-kill-shot substrate increment; small.)
4. **Calendar/flow seasonality family.** Day-of-week, month-end rebalancing,
   roll-week dynamics — flow-driven mechanism, structurally low-correlated
   with the six price-action families; computable from existing data.
   (Mining V2 family candidate.)
5. **Hypothesis-sourcing discipline.** Standing agent activity: mine
   literature/SSRN into mechanism cards feeding the research queue — attacks
   the idea-quality bottleneck with research time, not infrastructure.
   (May start any time; output is queue input, never evidence.)
6. **Data-tier upgrade as a diagnosis branch, not just cost calibration.**
   TBBO/MBP-1 sample months serve microstructure FEATURES (effective-spread
   dynamics, trade-side imbalance) in the zero-survivor diagnosis — the
   OHLCV+BBO tier is the most-mined tier; differentiated edge may need the
   next tier. (External cost = human ask, unchanged.)

USER-ADOPTED 2026-06-10 (both gated options approved by the user):

7. **Overnight edge class — ADOPTED as a separate governed family** (Mining V2
   scope). Doctrine refinement, not invariant weakening: the truth-chain rule
   was never "no overnight" — it was "never SILENTLY cross the maintenance /
   trade-date break." Intraday families keep the hard flat-before-maintenance
   boundary unchanged. The overnight family models the crossing EXPLICITLY:
   session-close → next-open (and close→close) labels, gap-risk measured and
   budgeted as a first-class diagnostic, roll-crossing still guarded, ETH
   liquidity/spread gates applied, and a separate (stricter) drawdown budget.
   Live overnight holding remains a human RED-lane sign-off at paper/live
   stages regardless of research verdicts.
8. **Early bounded ML — ADOPTED for Mining V2** as exactly ONE pre-declared
   ML pipeline (e.g. purged-CV gradient boosting over honest registry-resolved
   features) run as a Track-B pooled hypothesis: fixed feature set, fixed CV
   protocol, fixed hyperparameter budget declared up front, one VariantLedger
   entry. HARD PRECONDITION: the surrogate-FDR calibration (item 2) must pass
   first — if the pipeline finds "alpha" on shuffled labels, ML stays late.
   Feature importances are research output; the model is never promotion
   evidence by itself; Strategy Reference still validates any survivor.

L2/MBO doctrine (user, 2026-06-10): explicitly LONG-DEFERRED for cost — not
before sustained live profitability funds it. TBBO/MBP-1 SAMPLE MONTHS remain
the only microstructure purchase on the route (Stage I / diagnosis branch),
each an explicit human ask.
