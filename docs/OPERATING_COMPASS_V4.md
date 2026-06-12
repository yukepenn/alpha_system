# Alpha System Operating Compass v4.5 — Consolidated Roadmap

Status: canonical. Supersedes Compass v2 / v2.1 / v3 / v3.5 (chat-only). Where
older routes conflict with this document, this document wins. Live phase status
always comes from `python tools/frontier/status_doctor.py`, never from this
file.

Adopted 2026-06-10; patched to v4.1 same day (user review: power numbers = planning priors; pooled-evaluation hard rules; primary_state + reason_code taxonomy; Stage B parallelism limits; kill-shot Track A/B split; narrowed FactorLibrary trigger; engine policy live-state vs permanent; non-binding ETAs; ambition clause). Inputs: Compass v2.1 (post-Core-Pilot consolidation),
Compass v3/v3.5 (Trustworthy Verdict First), the LCFP/FUTSUB execution record,
and the coordinator's statistical power analysis (§2).

Patched to v4.4 on 2026-06-12 after a 16-agent adversarial red-team
(8-surface repo inspection, 5 perspectives, 3-skeptic triage; user-approved).
The route A→O is unchanged. v4.4 fixes verified wiring gaps before the
kill-shot and re-bases ambition honestly: kill-shot readiness hardening
(§3.C), pooled evaluation made mandatory-minimum (§3.C Track B), surrogate
statistics sharpened (§3.B item 7, §7.2), detection power added alongside
false-positive control (§3.B item 4), first-book existence bar vs ramp bar
(§0.1), backfill-as-accrual + standing weak-edge book (§3.D, §7.1),
producer-side standardization doctrine (§4), Stage-stage REUSE annotations
(§3.E/G/H/J/K), and operational-truth requirements (§3.K/O). Changes are
recorded inline with [v4.4] tags; §8 records the red-team verdict.

Patched to v4.5 on 2026-06-12 (user-directed course correction, pre-kill-shot):
(a) §3.C readiness preconditions marked DELIVERED with evidence pointers —
the obligations became artifacts; (b) Stage L gains the STAGED CREW DOCTRINE —
researcher-crew count is an output of measured per-lane economics, never an
ambition input; onboarding many agent researchers early is explicitly named
an anti-pattern; (c) new §9 digest queue records open decisions awaiting the
post-kill-shot war council so they are neither lost nor prematurely decided.
Changes carry [v4.5] tags.

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

First-book existence bar vs ramp bar [v4.4]:
  The 2.0 floor governs LEVERAGE AND RAMP, not existence. First-book
  existence bar: realized net shadow/paper Sharpe >= 1.0 at the declared
  vol target under the declared cost profile. Honest arithmetic: 2.0 via
  6-10 edges at input grade SR 0.3-0.8 requires near-zero pairwise
  correlation; within ES/NQ/RTY (shared equity beta, shared vol regimes,
  realistically rho ~0.25) the per-edge requirement climbs back to the
  "rare" grade, and genuinely distinct in-trio mechanism clusters at
  5-30m from OHLCV+BBO plausibly number 3-5, not 6-10. Therefore treat
  Stage N (universe expansion) as the DEFAULT-EXPECTED route to the
  floor, not a remote conditional. Neither bar ever bypasses an evidence
  gate; both are measured on realized shadow/paper, never on backtests.

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
   [v4.4] Ledger boundary clarified: variant/holdout enforcement binds at
   STUDY EXECUTION, not at evidence assembly. A gate that arms only when a
   caller supplies ledger paths counts declared variants, not executed ones —
   the exact forking-paths failure the ledger exists to prevent. Until the
   runtime wiring exists, a kill-shot-scope RECONCILIATION AUDIT (every study
   invocation provably matched to a ledger entry) is a readiness precondition
   (§3.C), and runtime wiring is a hard precondition for any agent-driven
   mining (Stage F/L).
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
     [v4.4] DETECTION leg added: a planted TRUE-alpha canary (synthetic
     genuine signal of known strength) must be DETECTED by the same pipeline,
     and a clean twin of the contaminated fixture must PASS the same gated
     path — false-positive control without measured detection power is a
     pipeline whose stationary output is INCONCLUSIVE forever. The
     contaminated-fixture handoff must name WHICH gate fired (value-level
     evidence, not self-declared metadata).
  5. No-leakage promotion blocker; BBO-proxy disclaimer gate; second-PnL-truth
     canary (DONE, PR #332).
  6. Verdict taxonomy upgrade (§2.2) incl. pre-declared pooled-evaluation
     support in StudySpec.
  7. Pipeline FDR calibration (§7.2): the full study machinery run on
     label-shuffled/surrogate data; any survivor = measured pipeline leakage;
     must pass before the kill-shot and is a HARD precondition for the early
     bounded-ML pipeline (§7.8). [v4.4] Statistical floor for the calibration
     itself: (a) the surrogate run count K is DECLARED with its implied
     false-pass bound (zero passes in K runs bounds the rate at ~3/K at 95%;
     K>=60 → ~5% — K=20 is a useless 15%); (b) nulls must be
     DEPENDENCE-PRESERVING — iid label shuffling destroys the overlap
     autocorrelation of 5-30m labels and yields an anti-conservative null;
     minimum is session/trade-date-block shuffling, and at least one
     configuration should circular-block-bootstrap returns and regenerate
     labels through the real engine; (c) configurations are per-family, not
     one generic pipeline nobody runs.
  8. Evidence-accrual loop (§7.1): INCONCLUSIVE+UNDERPOWERED verdicts
     auto-requeue for retest when newly accepted data materially changes
     their power.
- REVIEW CONTRACT (permanent from here on): reviewer verdicts must cite
  deterministic evidence — ledger completeness, variant count, holdout access
  report, canary results, no-lookahead audit, cost report, duplicate-exposure
  status, resolver smoke. Prose alone gates nothing.
- EXIT: nothing can become WATCH/CANDIDATE unless ledgered, variant-counted,
  leakage-clean, holdout-disciplined, fake-alpha-tested, second-truth-clean,
  reviewer-approved. ETA: ~1–2 days of campaign work.

#### Stage B status note — DISCOVERY_RIGOR_FLOOR_V1 closeout

Rigor Floor gate machinery and closeout artifacts are delivered by
`RIGOR-P07`; the kill-shot remains fail-closed until every
`research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` item is `MET`.

- Full gated-path integration audit: `MET` — `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py::test_full_gated_path_engages_every_rigor_floor_gate_and_blocks_bypasses`.
- Sealed window exactly one active declaration: `MET` — `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json` and P03 declaration tests.
- 4/4 negative controls plus planted fake-alpha: `MET` — P04 canary-floor note and `python tools/hooks/canary_runner.py`.
- TrialLedger and VariantLedger presence/writability gates: `MET` — P07 integration audit plus P01/P02 gate tests.
- Reason-code validation for INCONCLUSIVE: `MET` — P01 verdict/promotion/evidence tests and P07 audit.
- Surrogate calibration v4.4 section 7.2 statistical floor: `PENDING-coordinator` — real-data K>=60 dependence-preserving per-family calibration required; synthetic P05 K=2 report is not enough.
- HOLDOUT COVERAGE: `MET` — P033000 intersection contract test over re-locked inputs.
- VARIANT RECONCILIATION: `PENDING-coordinator` — six rerun invocations need live VariantLedger reconciliation before STOP removal.
- SUBSTRATE-INVARIANT AUDIT: `PENDING-coordinator` — live registry audit still required.
- POWER MEMOS: `MET` — `research/discovery_rigor_floor_v1/power_memos/KILL_SHOT_POWER_MEMOS.md`.
- TRACK-B MANDATORY MINIMUM: `PENDING-coordinator` — actual cross-symbol and cross-horizon registrations deferred to kill-shot time before Track A metrics.
- SUBSTRATE-CAVEAT REGISTER: `MET` — R-037 `contract_id` caveat and BBO-proxy limits recorded in the readiness checklist and resume handoff.
- REAL FEE CONSTANTS: `MET` — P035000 fee schedule tests and review.

### Stage C — CORE_PILOT_RERUN_V1 (the kill-shot)  [the point of everything above]

- ENTRY: Stage A + B exits green. Named explicitly; realized as FUTSUB P27–P29
  (re-lock StudySpecs, rerun, honest verdict refresh) if the do-not-duplicate
  check at the P26/P27 boundary confirms; else a narrow named campaign.
- WORK [v4.1 — two strictly separated tracks]:
  - **Track A — Exact rerun:** the same (or faithfully translated) six
    previously-INCONCLUSIVE Core Pilot studies on trusted substrate + rigor
    floor, pre-declared variant budgets per family. Track A verdicts stand on
    their own and are never rewritten by Track B.
  - **Track B — Pre-declared pooled supplemental tests [v4.4: MANDATORY
    MINIMUM]:** mechanism-justified pooled hypotheses, REGISTERED BEFORE any
    Track A rerun metric is inspected, logged as separate pooled VariantLedger
    hypotheses per §2.1 rules. The minimum is no longer optional: at least ONE
    cross-symbol and ONE cross-horizon pooled hypothesis must be registered,
    because the compass's own honest prior (§6.1) names pooled weak edges as
    the most probable positive outcome — an optional Track B makes the most
    probable win legally skippable.
  - No new alpha batch, no broad mining.
- READINESS PRECONDITIONS [v4.4 — verified gaps from the 2026-06-12 red-team;
  the kill-shot does not fire until each is green]
  [v4.5 STATUS: ALL DELIVERED 2026-06-12 — holdout coverage contract test
  (PR #388 + re-verified against RELOCK_V2), reconciliation + substrate
  audits committed (PR #398), power memos (PR #394), caveat register
  (KILL_SHOT_READINESS.md), real fees v2 (PR #390), Track-B registered
  pre-metric against V2 ids; the remaining live gate is the real-data
  surrogate calibration (row 6), running at patch time. The checklist file
  research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md is the
  deterministic truth; this list remains as the design record]:
  1. Sealed-holdout coverage: the declared window MUST intersect every locked
     StudySpec input (all symbols, both dataset families, rolling end_date) —
     proven by a contract test, not by reading the declaration. A window that
     does not cover the kill-shot's own inputs is rigor theater.
  2. Variant-ledger reconciliation audit: every kill-shot study invocation
     provably matched to a ledger entry (§2.3 boundary clause).
  3. Read-only substrate-invariant audit over the live registries: no
     constant-valued flag columns, >=2 session values per trading day,
     role markers present, zero locks referencing DEPRECATED records.
  4. Per-study power memo: minimum detectable effect on real N_eff, written
     BEFORE metrics, so UNDERPOWERED outcomes are predicted, not discovered.
  5. Substrate-caveat register in the kill-shot context: known residuals
     stated up front (R-037 contract_id caveat, BBO-proxy regime limits) so
     verdicts inherit caveats instead of rediscovering them.
  6. Real fee constants (§3.I) in the cost stack — placeholder fees make
     "net edge" a symbolic quantity.
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
        kill-shot from differentiated mechanisms already in scope (§7):
        event-calendar conditioning, calendar/flow seasonality, the governed
        overnight family, event-time bars, cross-asset spillover — before any
        data buy;
    (b) horizon structure: pooled multi-horizon retest of UNDERPOWERED
        verdicts. [v4.4] Two named levers here: BACKFILL-AS-ACCRUAL —
        extending the accepted window backward (2018←) changes power
        immediately versus waiting on calendar accrual, and the requeue scan
        already consumes accrued-data metadata; and the STANDING WEAK-EDGE
        BOOK HYPOTHESIS — one fixed-rule, equal-weight, mechanism-justified
        pooled book of ALL underpowered edges, pre-registered as ONE
        VariantLedger hypothesis and retested once per accrual epoch. This
        operationalizes §2.4 (the book is the unit of account), which
        otherwise has no mechanism;
    (c) universe homogeneity: equity-index trio shares one beta → evaluate
        cross-asset expansion (Stage N trigger);
    (d) data tier: if many die only at cost gates → Stage I sample-month
        calibration may rescue or confirm; TBBO/MBP-1 samples also serve
        microstructure FEATURES (§7.6), not just cost validation;
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

- [v4.4] REUSE: entry/stop/target probes overlap backtest/fast_path.py +
  management/ + LCFP path labels; the sandbox is mostly a lane policy, not
  new compute. Build the quarantine boundary, reuse the engines.
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
- Family candidates beyond the original six (all §7-adopted, each still
  budget-bounded): calendar/flow seasonality (§7.4), event-calendar-conditioned
  variants (§7.3), the governed overnight family (§7.7 — explicit-crossing
  labels, gap-risk budget), and exactly ONE pre-declared ML pooled pipeline
  (§7.8 — only if the surrogate-FDR calibration passed).
- Computed anti-crowding lands here (structural/correlation duplicate gates)
  if Stage B's inspection found only hint/manual duplicate machinery.
- Outputs only REJECT / INCONCLUSIVE_* / WATCH / CANDIDATE_RESEARCH.

### Stage G — FACTOR_LIBRARY_V1  [conditional — narrowed trigger, v4.1]

- TRIGGER: ≥1 WATCH/CANDIDATE_RESEARCH survivor, OR repeated manual research
  operation proves the ledger query surface is concretely blocking a named
  next campaign. Rejected-idea memory ALONE never triggers this stage — that
  function belongs to the Discovery Rigor Floor's TrialLedger/
  RejectedIdeaLedger upgrades (Stage B), not to a full FactorLibrary.
- [v4.4] REUSE: factors/registry.py, factors/spec.py, factors/validation.py,
  factors/contracts.py, reports/factor_card.py, and the governance ledgers
  already exist — this stage is ingestion/query/lifecycle glue, never engine.
- Operational ingestion/query/memory over EXISTING schemas (FactorCard,
  EvidenceBundle, TrialLedger, PromotionDecision, FactorSpec — do not rebuild):
  EvidenceBundle→FactorCard ingestion, registry, verdict/decision links,
  rejected-idea memory, duplicate exposure groups, as-of point-in-time
  FactorLibrarySnapshot for walk-forward, query/list/search.
- Lifecycle: DRAFT / READY_FOR_STUDY / WATCH / CANDIDATE_RESEARCH /
  VALIDATED_RESEARCH / QUARANTINED / DEWEIGHTED / RETIRED / REJECTED.
  Forbidden states: LIVE_APPROVED, PRODUCTION_READY, CAPITAL_ALLOCATED.

### Stage H — STRATEGY_REFERENCE_VALIDATION_V1  [survivor-only]

- [v4.4] REUSE: the conservative reference engine semantics largely exist
  (backtest/ package, management/ grid, cost stack); this stage is a
  VALIDATION CAMPAIGN over that engine, not an engine build.
- Conservative Reference 1m truth: next-bar semantics, same-bar ambiguity,
  fees/spread/slippage stress, drawdown/turnover accounting, bounded
  management grid. A factor candidate is not a strategy candidate until here.

### Stage I — Cost Reality Upgrade  [trigger split, v4.4]

- [v4.4] PULLED FORWARD, ZERO COST: real fee constants (public CME exchange +
  clearing + broker schedules; order $0.25-0.85/side all-in micros,
  $1.5-3 minis) replace Layer-1 placeholders NOW — before the kill-shot —
  because placeholder fees make every net-edge number symbolic. One day of
  work, no purchase.
- TBBO / MBP-1 SAMPLE MONTHS only (external paid data = hard-stop ask to the
  human first): effective spread, markouts, trade-side confirmation,
  thin-liquidity behavior → calibrate the BBO proxy. No full L2/MBO.
  [v4.4] Trigger WIDENED from "first CANDIDATE_RESEARCH" to "before any
  survivor verdict is treated as commercially meaningful" — the prior trigger
  was circular (the uncalibrated gate can prevent the CANDIDATE that triggers
  calibration). At 5-30m horizons gross edge is 1-3 ticks and a full ES
  round-trip cross is ~1 tick + slippage; uncalibrated costs both over-kill
  passively-monetizable edges (false COST_FRAGILE) and under-kill queue-toxic
  ones. Report cost-sensitive results as a band (aggressive vs mid) until
  calibrated.
- Standing rule: no capital-relevant conclusion rests on the uncalibrated
  BBO proxy; cost_fragile (dies at double-cost) never validates.

### Stage J — PORTFOLIO_ALPHA_BOOK_V1  [trigger: ≥3 low-corr candidates or validated ensemble]

- [v4.4] REUSE: portfolio/ already holds allocation.py, risk.py, sizing.py,
  targets.py, universe_constraints.py, integration.py — this stage wires and
  validates, it does not invent.
- Portfolio-level memory and allocation logic: marginal contribution,
  correlation clusters, capacity, drawdown contribution, regime/session/
  horizon exposure, weight/deweight/retire. Objective = marginal portfolio
  utility, never standalone Sharpe ranking. Weighting shrunk by posterior
  edge × orthogonality × capacity × confidence ÷ risk.
- [v4.4] FREEZE-BEFORE-SURVIVORS rule: the book acceptance metric (net Sharpe
  at a declared vol target under a declared cost profile; the marginal-utility
  formula) is written down BEFORE any survivor exists — otherwise Stage J gets
  specified while staring at candidate PnL, the classic way targets get
  fitted to results.

### Stage K — Shadow + Decay monitoring  [before any ML or paper]

- [v4.4] SEQUENCING: Stage K runs FIRST on the Stage J book subset; a
  standing sandbox SHADOW LEDGER (live-like predictions, zero orders,
  EXPLORATORY stamp, never promotion evidence) MAY start for any
  WATCH-or-better signal immediately after Stage D — calendar time is the
  scarcest evidence asset and shadow accrual is free. Full Stage K gates and
  classification are unchanged and still required before ML or paper.
- [v4.4] REUSE: the diagnostic primitives exist (research/ ic.py,
  stability.py, buckets.py, regimes.py, correlation.py; reports/
  factor_card.py); what is genuinely new is the live-like scheduler and decay
  CLASSIFICATION, not the metrics.
- Live-like predictions, zero orders: feature/IC drift, bucket monotonicity,
  gross/net gap, cost-proxy drift, regime drift, posterior edge,
  quarantine/deweight/retire triggers. Decay is classified (data/infra vs
  signal vs monetization vs regime), never "lost 10 days → off".
- [v4.4] DECAY-ALERT SLA: every decay classification names an owner and a
  response clock (quarantine decision within one trading day of a confirmed
  signal-decay classification); monitoring that pages nobody is decoration.

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
- [v4.5] STAGED CREW DOCTRINE (user-set, 2026-06-12): crew count is an
  OUTPUT of measured economics, never an ambition input. Onboarding many
  agent researchers early is an anti-pattern: each lane multiplies compute,
  review bandwidth, and FDR/variant budget consumption BEFORE it multiplies
  validated output, and unproven substrate value makes that spend
  unrecoverable. Scaling gates:
  - L0 (pilot): EXACTLY ONE researcher lane, only after (i) the kill-shot
    verdict is read and the survivor-gate branch chosen, and (ii)
    SHIP_REFIT_V1 has made operations boring (first-light smoke standard,
    diagnostics fast-path, job-runner/merge/disk-RAM hardening). The pilot
    runs >=3 full idea→verdict cycles with a clean ledger: cost per verdict,
    review hours per verdict, FDR budget consumed, defects escaped (target 0).
  - L1 (second lane): only after L0 economics are measured and the
    variant/FDR budget model is re-derived for 2 concurrent lanes (parallel
    miners multiply false-discovery pressure; budgets must be partitioned,
    not duplicated).
  - L2+ (widen): only when validated idea throughput — not enthusiasm — is
    the binding constraint: the hypothesis-sourcing pipeline (§7.5)
    produces more well-formed ideas than existing lanes can verdict, AND
    marginal lane cost < marginal expected validated-edge value under the
    measured L0/L1 numbers.

### Stage M — ML meta-labeling  [after stable base signals]

- take/skip, size buckets, regime routing, exit quality. Never first-stage
  black-box 1-minute direction prediction.
- Exception already adopted (§7.8): one pre-declared, surrogate-FDR-gated ML
  pooled pipeline may run earlier inside Mining V2; this stage is the full ML
  layer, which still waits for stable base signals.

### Stage N — Universe expansion  [evidence-triggered, any time after D]

- TRIGGER: survivors are homogeneous (one equity-beta exposure), or the
  AlphaBook cannot reach low-correlation utility within ES/NQ/RTY, or
  [v4.4] fewer than 4 distinct mechanism clusters are identified within the
  trio after the first conclusive kill-shot cycle (per §0.1, Stage N is the
  default-expected route to the book floor).
- [v4.4] PRECONDITION: the NEW_UNIVERSE_ONBOARDING checklist
  (docs/sops/NEW_UNIVERSE_ONBOARDING.md, written post-kill-shot) is executed
  per root: declared session template + calendar, roll policy wired (not
  audited after), cost/tick/multiplier profile, register-time invariants
  green on first materialization, resolver smoke, no-lookahead audit,
  N_eff/coverage matrix. The 2026-06-11 session-truth saga (one undeclared
  truth source → 6 repair phases, 496 deprecated rows, 4 re-materialized
  packs, invalidated re-locks — inside an ALREADY-onboarded universe) is the
  template incident this checklist exists to prevent.
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
- [v4.4] KILL-SWITCH CANARY: the hard kill switch is PROVEN to fire (an
  executable canary in the existing evals/canaries pattern — a guard that
  cannot be demonstrated to trip has not earned a live order). Same for max
  daily loss and position caps. Additionally, liveness is a first-class
  invariant from research onward: a harness that can sit stale-RUNNING
  undetected in research will, unchanged, sit stale-RUNNING with positions
  on — heartbeat-staleness detection (status_doctor) is the standing
  down-payment on this stage.
- Daily operation runs on four clocks: definitions slow (review-gated),
  calibration weekly/monthly, portfolio weights evidence-driven, execution/
  risk gates intraday. Estimates update fast; definitions change slowly;
  retirement only with evidence.

---

## 4. Standing doctrines (carried forward intact)

- **Horizon/session:** 1m = sampling not alpha horizon; 1–3m execution-fragile
  (stricter gates); 5–30m primary; 30m–4h extended (stronger overlap/regime
  tests); session-close / maintenance-flat valid; hard boundary = exchange
  maintenance/trade-date break, never midnight — FOR INTRADAY FAMILIES; the
  governed overnight family (§7.7) is the sole exception and must model the
  crossing explicitly (never silently); ETH research-in-scope, not
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
- **Producer-side standardization [v4.4 — doctrine, from the session-truth
  saga and the Never-Again map]:** (1) ONE DECLARED TRUTH SOURCE per
  market-structure dimension (sessions, rolls, calendars, halts) — consumers
  derive from the shared truth module, never from a copied constant or a
  per-family reimplementation; a single-truth boundary canary enforces it.
  (2) REGISTER-TIME VALUE-FREE INVARIANTS — a flag column must not be
  constant, a session dimension must show >=2 values per trading day, role
  markers must be present where contracts declare session inputs; degenerate
  substrate is caught at registration, never at study time. (3) FIXTURE
  HONESTY — a test fixture must never implement the property under test
  (static labels + real timestamps, not fixture-computed labels). (4) GUARDS
  ARE WIRED BEFORE TRUSTED — a guard that exists but is not invoked on the
  consuming path (roll_guard, holdout emission, ledger append) counts as
  absent; guard-wiring canaries verify invocation, not existence. (5) POLICY
  LISTS TRACK CONTRACTS — when a campaign contract authorizes a path/file,
  the global policy allow-lists must be reconciled in the same change, with a
  drift test.

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

---

## 8. v4.4 red-team record (2026-06-12)

A 16-agent adversarial red-team (8 read-only repo inspectors → 5 perspectives:
statistical reviewer, trader/PM, platform architect, agent designer,
harness/live operator → 3 independent skeptics triaging 30 recommendations)
reviewed v4.3 against the live repo. Executive verdict: KEEP THE ROUTE, FIX
THE WIRING. No missing stage, no wrong order; the verified gaps were wiring
(holdout window not covering kill-shot inputs; variant counting at
evidence-assembly instead of study execution; detection power unmeasured;
pooled channel unimplemented while being the declared most-probable win;
placeholder fee constants) and honesty of ambition (in-trio Sharpe-2.0
arithmetic). All fixes are encoded above as [v4.4] tags; the kill-shot
readiness preconditions (§3.C) are the binding additions. Items deliberately
DEFERRED by the skeptics' operating-rule triage: machine-validated reviewer
evidence (pre-mining), holdout authorization artifacts + evaluation budgets
(pre-mining, before any agent touches the holdout), thin researcher tooling
MVP (first post-kill-shot campaign), SOP documents (post-kill-shot),
primitive-grain driver targeting (post-kill-shot), differentiated-substrate
scheduling (Stage D(a) decision or explicit user pull-forward). Two standing
user decisions: TBBO sample-month purchase timing; differentiated-substrate
start timing. Honest priors in §6 stand unchanged and remain scorable.

---

## 9. v4.5 digest queue (open items for the post-kill-shot war council — recorded, not yet decided)

Parking these here so they are neither lost nor decided prematurely. Each is
a DECISION to make with kill-shot evidence in hand, not a commitment:

1. TBBO measured-cost integration: fold the 3-month ES TBBO calibration into
   the cost stack's spread/slippage layers (versioned, like fees v2); decide
   NQ/RTY treatment (conservative multipliers vs more data — spending freeze
   in force, hard-stop ask either way).
2. Diagnostics fast-path: LCFP-pattern parity-gated engine for
   research/diagnostics.py (~10x precedent) — turns the surrogate floor from
   a day-burner into a sub-hour routine; top SHIP_REFIT_V1 candidate.
3. SHIP_REFIT_V1 scope: seam audit (implicit cross-layer contracts →
   written contracts + canaries + guards; label-side pack writers are the
   known open seam) + ops pain log (RAM/disk budgeting for compute chains,
   job-runner discipline, merge babysitter, runbook state-aware
   preconditions, first-light smoke as campaign-close gate).
4. DIFFERENTIATED_SUBSTRATE_V1 contract authoring (overnight §7.7, events
   §7.3, seasonality §7.4, hypothesis sourcing §7.5) — timing depends on the
   survivor-gate branch.
5. bbo_tradability_spread_ticks substrate finding: zero numeric values across
   all partitions/years (caveat register + first-light case study) — decide
   repair vs retire for the feature.
6. Statusline/ops niceties carried as standing config, not campaign work.

Promotion rule: an item leaves this queue only by becoming a campaign
contract, a standing doctrine section above, or an explicit REJECTED note.
