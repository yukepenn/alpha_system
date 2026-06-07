# Handoff → ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

Source campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` (COMPLETE_WITH_WARNINGS)
Handoff owner: Coordinator (Ralph role)
Date: 2026-06-07

## Why this campaign

The Core Alpha Pilot proved the **research loop and the lock/identity invariant
are correct end-to-end** (keystone content-addressing fixed; StudySpecs resolve
to real Parquet values; honest REJECT/INCONCLUSIVE verdicts with zero forced
promotions). It also surfaced a concrete, bounded **substrate-coverage gap**:
three of five families could not be evaluated because the locked substrate is a
single-week, OHLCV-only, ES-centric smoke pack with only base-OHLCV +
session-context features and 5m/10m/30m labels.

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` exists to build and govern the
missing substrate so the same loop can actually evaluate regime, liquidity/PA,
BBO, and cross-market families — and re-run the pilot's INCONCLUSIVE studies
against real materialized inputs. It is **substrate engineering, not new alpha
ideation** (the AlphaSpecs/StudySpecs already exist and are reusable).

## Required DatasetVersions (accepted, locked)

- **ES, NQ, RTY OHLCV-1m**, full available history (not a one-week slice) —
  accepted DatasetVersions with no-lookahead `available_ts`.
- **ES, NQ, RTY BBO-1m / top-of-book**, full history — accepted DatasetVersions.
  This is the hard gap that made P20 a data gap; without an accepted BBO
  DatasetVersion, BBO tradability cannot be evaluated.
- Cross-instrument alignment must preserve per-instrument `available_ts` (no
  forward-fill across instruments), as the pilot's cross-market rejections
  required.

## Required FeaturePacks (materialized + registered, keystone identity)

1. **Base OHLCV** — returns, log-returns, rolling vol, rolling range, range
   position, volume z-score (already proven materializable).
2. **Session / calendar / maintenance** — RTH/ETH flags, session-minute,
   maintenance-window flags, holiday/half-day calendar (extends the pilot's
   `rth_flag` / `session_minute`).
3. **VWAP / session auction** — running VWAP, anchored/ETH VWAP, distance-to-VWAP,
   opening-range context (pilot gap `P15-G2`).
4. **Regime / trendiness / volatility / compression** — trendiness, ATR /
   volatility-regime buckets, range-compression boundaries (pilot gap `P15-G4`;
   directly unblocks P18).
5. **Liquidity sweep / failed-breakout / PA primitives** — prior-high/low sweep,
   close-back-inside, wick rejection, displacement, compression-breakout,
   failed-breakout flags (pilot gap; directly unblocks P19).
6. **Volume / activity** — participation, volume regime, activity bursts.
7. **BBO tradability / top-book** — spread, spread ticks, spread z-score,
   top-book depth, wide-spread / low-depth / missing-BBO / bad-quote flags
   (pilot gap `P15-G5`; requires the BBO DatasetVersion; unblocks P20).
8. **Cross-market alignment** — beta residual, ES/NQ/RTY basket residual,
   relative-strength rank, catch-up/rotation, pair divergence/agreement
   (pilot gap `P15-G3`; enriches P16).

All features must be materialized with stable keystone identity and pass a
resolver-smoke gate (every StudySpec lock resolves to a real Parquet value)
before diagnostics — the discipline proven in this pilot.

## Required LabelPacks (materialized + registered)

- **Diagnostic horizons**: 1m, 3m.
- **Primary horizons**: 5m, 10m, 15m, 30m (15m engine added in pilot `P15-G1`;
  needs materialization).
- **Extended horizons**: 60m, 120m, 240m.
- **Session-close** and **maintenance-flat** labels (close-out semantics).
- **Cost-adjusted** labels (net of the three-layer cost model).
- **Path-dependent** labels where feasible: MFE/MAE, target-before-stop,
  triple-barrier.

## Required matrices (coverage + diagnostics)

- **Symbol × horizon** coverage and diagnostics (ES/NQ/RTY × all horizons).
- **Session × horizon** (RTH/ETH/thin-session × horizons).
- **BBO quality** matrix (spread/depth regimes × outcomes).
- **Cross-market alignment** matrix (lead-lag / residual states).
- **Feature-family coverage** matrix (which families resolve for which
  instrument/partition).
- **Label-family coverage** matrix (which label packs resolve per
  instrument/horizon).

## Re-run obligation

After substrate materialization + re-lock, re-run the pilot's accepted
StudySpecs (especially the 6 `INCONCLUSIVE` survivors and the regime/liquidity/
BBO families) against the real materialized inputs, and re-issue honest
REJECT/INCONCLUSIVE/WATCH/CANDIDATE_RESEARCH verdicts. Promotion remains
evidence- and cost-gated; no human prior decides edge.

## Carry-over disciplines (proven in the pilot)

- Keystone identity + resolver-smoke gate before diagnostics.
- Runtime resolver fails closed on stale/unresolvable locks — never substitute.
- Honest outcomes only; no fabricated quotes/values.
- Explicit staging; never commit `runs/**`, raw/canonical/feature/label values,
  heavy artifacts, or local DB files.
- Incremental waves + serial merge; read per-idea diagnostics before scaling.
