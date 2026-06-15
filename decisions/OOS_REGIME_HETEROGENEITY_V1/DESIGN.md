# OOS_REGIME_HETEROGENEITY_V1 — don't let cross-regime pooling bury regime-specific alpha

Status: PROPOSED (design; queued immediately AFTER PARTITION_RESOLVER_V0 lands)
Date: 2026-06-15
Lane: Yellow (research methodology + research_lane plumbing). Research-only.
Consistent with `docs/OPERATING_COMPASS.md` §3.8 — this REFINES "cross-year
consistency" into "regime-relative robustness", it does not weaken it.

## 0. The concern (user-raised, valid)

The V0 OOS mechanism (`BROAD_MINING_DRIVER_V0` + `aggregate_pooled_metric`) is
**equal-weight cross-year/instrument pooling**. That bakes in a **stationarity
assumption** — it credits effects that are roughly constant across 2019–2026 and
penalizes/erases effects that are **regime-specific** (e.g. a genuine edge that
only exists post-2023 due to a market-structure shift: 0DTE growth, participant/
tick changes, a volatility regime). Equal-weight pooling of a "+strong in
2023–2025, ~0 in 2019–2021" effect dilutes the pooled mean toward 0 → a real
recent edge is wrongly rejected. This is the classic robustness-vs-adaptivity /
stationary-vs-regime-dependent tradeoff. V0 is robust-first by design (cleanest
first survivors, most flukes killed) — this doc removes its blind spot WITHOUT
opening the floodgate to recent-overfit.

## 1. Principle

**"Robust" ≠ "stationary across all history."** A north-star-legitimate alpha can
be robust *within the forward-relevant regime* + *cross-sectionally (instruments)*
+ *forward (live)*. So OOS must be defined **relative to the regime the edge claims
to live in**, not blindly across all years. (Compass §3.8's "cross-year
consistency" is the strong default; this generalizes the *axis of independence*
from "years" to "years ∪ instruments ∪ regime sub-periods".)

## 2. The hard line (must NOT be crossed)

A regime-specific edge and a recent-overfit fluke look identical without
independent evidence. So we do NOT "trust recent because recent". A recent-only
signal earns attention only with **independent corroboration**: cross-instrument
in the same regime, sub-period stability within the regime, and ultimately forward
shadow/paper. The machine still never auto-promotes; this only changes how a
heterogeneous pooled result is ROUTED, not the promotion bar.

### 2a. Regime is a COUNTED VARIANT (anti regime-shopping — the load-bearing guard)

Regime heterogeneity multiplies the hypothesis space, so it is itself a
multiple-comparisons surface. To stop it becoming a new p-hacking lever
("high-vol null → try low-vol → try trend → keep the significant one"), it MUST
reuse the existing multiplicity machinery, NOT a parallel one (REUSE-MAP):

- **Every regime axis, every split threshold, every interaction, every horizon is a
  PRE-REGISTERED, COUNTED VARIANT** in `governance/variant_ledger.py` (the
  family/variant budget), authored BEFORE any metric is read; the budget only ever
  raises, never lowers, and amendments predate the earliest attempt.
- **The regime-conditioned tests of one idea form a co-mined batch** → routed
  through `CROSS_IDEA_FDR_BUDGET_V1` (`governance/family_fdr_correction.py` +
  `family_fdr_ledger.py`): the family-wise/FDR correction + surrogate-resolution
  adequacy apply across the regime variants exactly as across sibling ideas. A
  regime split that clears per-test but NOT family-corrected is not a signal.
- **Look at results only AFTER the axes + splits are registered** — never invent
  the regime after seeing the metric. The variant ledger + the pre-registration
  timestamp are the deterministic evidence a reviewer cites.

### 2b. Pre-registered discovery / validation / locked windows (no peeking)

Proposed default (a policy fork — overridable): **discovery 2019–2021** (2018 is
BLOCKED — RTY coverage < 0.90, per `alpha data inventory`), **validation 2022–2024**,
**locked-holdout 2025–latest accepted 2026** opened only at the reviewer-approved
candidate stage (sealed-holdout + contamination ledger, governance rule #4). Axes
and splits are registered on discovery; validation confirms; the locked window is
never touched during search. Cross-instrument (ES/NQ/RTY in the same window) is the
independence axis when cross-year is not available.

## 3. Design (low-cost, high-value; built on the resolver's per-partition output)

The driver already records `PartitionOutcome` per partition + `PartitionCoverage`.
Add, at the pooled-verdict step:

1. **Preserve + surface per-partition heterogeneity** — never let the pooled scalar
   erase the per-partition breakdown. Attach the per-(instrument,year) component
   vector to the pooled readout/record.
2. **Regime-trend classifier** (deterministic, value-free) over the per-partition
   components → one of: `consistent` (same sign, low dispersion across regimes),
   `recent_monotonic` (effect strengthening toward recent years / present only in
   the recent sub-window), `cross_sectional_only` (holds across instruments in a
   sub-window but not across years), `scattered` (no structure — noise-like).
3. **Heterogeneity-aware routing** — `consistent` → the existing pooled path
   (strongest evidence). `recent_monotonic` / `cross_sectional_only` → instead of
   graveyard, route to **requeue as a `regime_conditioned_followup`**: a
   pre-registered child hypothesis with the regime as an explicit CONTEXT (reuse
   the setup grammar `context ∩ trigger → outcome`; `regime_volatility_compression`
   features already make regime first-class) + an OOS scope **relative to that
   regime** (its sub-periods + cross-instrument). `scattered` → graveyard.
4. **Recency-weighted / regime-relative pooling (fork — propose, surface)** — the
   north star is forward Sharpe, so recent regimes are more representative of the
   near future. Offer recency-weighting + regime-relative OOS windows (with
   sealed-holdout) as the policy refinement; equal-weight stays the conservative
   default. This is the same family as the open "OOS window policy" fork.

## 4. Acceptance

- A synthetic "null early years + strong recent years" effect is NOT silently
  graveyard'd — it is classified `recent_monotonic` and routed to a
  regime-conditioned follow-up with its per-partition vector preserved.
- A genuinely scattered/noise effect still → graveyard (no false reprieve).
- The pooled record always carries the per-partition heterogeneity vector +
  classification (auditable; a reviewer sees WHY).
- No change to the promotion bar; machine never auto-promotes; research-only
  language. `pytest -q` + canaries green.

## 5. Sequencing (smallest real-OOS proof BEFORE widening)

1. `PARTITION_RESOLVER_V0` lands (makes multi-partition runs actually resolve data).
2. **A smallest real cross-year OOS PROOF gate** — before any regime widening, prove
   the mechanics on ONE–TWO representative factors/setups across multiple years:
   resolver maps factor/label → target partitions correctly; **per-year evidence is
   preserved separately** (not collapsed); aggregation is conservative with **no
   naive n_eff sum** (overlap-aware, per [[law-overlap-aware-ic-power-n-eff]]); no
   tuning on locked years; every outcome routed to memory; fail-closed on missing.
   Only when this proof passes does the regime build start. This prevents the build
   from drifting into unbounded research on unproven plumbing.
3. THEN `OOS_REGIME_HETEROGENEITY_V1` (this doc), with §2a regime-as-counted-variant
   + §2b pre-registered windows enforced.
4. Only AFTER regime diagnostics: idea-generation / parallel-researcher queue,
   regime-guided. No FactorLibrary/AlphaBook/paper/live until the trusted survivor
   gate — a regime-conditioned signal is a reviewer-pending thread, NOT a survivor.

TBBO stays background (BBO proxy suffices for first-pass diagnostics; TBBO is
execution-truth refinement before any Strategy-Reference/paper/live claim).
