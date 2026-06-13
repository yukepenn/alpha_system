# STRATEGY_SHAPED_RESEARCH_LANE_V0 — Goal

## Mission

Remove the verified **expressibility blocker** that stops alpha_system from being a generic
strategy-shaped alpha research platform. Today the study engine is **single-primary-factor
by hard enforcement** (`StudyConfig.factor_id` scalar; `templates.py` `SINGLE_FACTOR_THRESHOLD_TEMPLATE`
the only template; the conditional lens collapses context AND trigger from the *same*
`value>0` at `diagnostics.py:1037-1038`). So a human or AI researcher **cannot express**
the shape of a real intraday idea — *context ≠ trigger*, confirmation, invalidation,
stop/target/hold-time, path outcome. This V0 makes that class of idea **expressible,
explorable, ledgered, and honestly rejectable** — the smallest real capability.

## What this is (and is NOT)

- **IS:** a `SetupSpec`/`MechanismCard` contract + a bounded **context≠trigger** conditional
  probe that **reuses** the existing path labels (MFE/MAE/target-before-stop/triple-barrier)
  and the **already-wired** path-outcome diagnostics, EXPLORATORY-quarantined, FDR-budgeted.
- **IS NOT:** a strategy backtester, a PA grammar pack, FactorLibrary/AlphaBook, a feature
  fast lane, paper/live/broker, or new paid data. No new dependency.

## Honest framing (no over-promise)

This is a **capability investment, decoupled from any alpha bet.** It does *not* claim to
find alpha. It makes the *whole class* of strategy-shaped hypotheses (Brooks PA, VWAP/session,
event-driven, overnight, 1h–4h, and future AI-generated setups) testable cheaply and honestly
— which is the platform product. The cheap, unexhausted **de-stack diagnostic** runs alongside
(SSRL-P03) so we keep gathering evidence while building the capability.

## Hard invariants (the boundaries that keep this safe)

1. **EXPLORATORY ≠ promotion evidence** — the trusted/promotion path must *refuse* EXPLORATORY
   artifacts (enforced + a canary).
2. **No research→reference-sim bridge** — `research/` must not import `backtest/management/fast_path`;
   outcomes come only from materialized path labels. The reference engine stays the
   **survivor-only PnL truth** (no second PnL truth, per AGENTS.md).
3. **Additive only** — the existing single-factor path + all truth-chain invariants (canary,
   surrogate-FDR zero-pass, parity, roll/maintenance fail-closed) are unchanged.
4. **Bounded** — pre-registered VariantLedger/family-budget; no grid; **no multi-bar sequence,
   no geometry sweeps, no feature fast lane** (all deferred behind a later trigger).

## Why now (not build-by-inertia)

The corrective war council verified this is the **foundational platform blocker**, and the
user issued an explicit **generic-capability mandate** — the exact trigger the council named
as earning the build. It is *not* "chase alpha on a 0-survivor board"; it is "make the
research shape the platform needs expressible." Sequence and the sim-bridge stay deferred
until proof earns them.

## Definition of Campaign Done

A human/AI researcher can express ONE strategy-shaped idea (context≠trigger + path-outcome
target/stop/hold) and run it end-to-end on a small slice as an EXPLORATORY, variant-ledgered,
surrogate-FDR + power-qualified probe that **cannot** become promotion evidence; a trusted-handoff
scaffold + happy-path docs exist; all invariants hold; `RUN_SUMMARY` written.
