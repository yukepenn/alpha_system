# Scope Lock - DIFFERENTIATED_KILLSHOT_V1

Status: DK-P00 documentation-only scope lock. This document records the campaign
boundary before any metric exists. It creates no code, test, engine change,
study result, or governance object.

## In Scope For DK-P00

- Confirm the `DIFFERENTIATED_KILLSHOT_V1` bundle and active pointer.
- Record the value-free FDR active-subset restatement.
- Pin reused machinery in `REUSE_MAP.md`.
- Record explicit out-of-scope boundaries here.
- Keep README current with a compact factual snapshot.

## Out Of Scope For This Campaign Run

The following items are explicitly out of scope unless a later approved campaign
and phase contract changes that boundary:

- `fomc_drift` and `cpi_surprise_reversion` until an external feed is onboarded
  and approved; they are `needs_paid_data` and out this round.
- The governed overnight family; no overnight cards are exercised this round.
- Per-instrument splits. ES/NQ/RTY pooling is one pooled test surface, not three
  instrument-specific hypothesis surfaces.
- Geometry sweeps, horizon sweeps, or any grid expansion beyond the
  pre-registered horizons.
- Any edit to the single-factor template path, including
  `src/alpha_system/strategies/templates.py`.
- Any edit to FUTSUB or core-pilot research artifacts, including
  `research/futures_substrate_scaleout_v1/**` and
  `research/futures_core_alpha_pilot_v1/**`.
- Any second PnL truth, value-accounting truth, or research-to-reference-sim
  bridge.
- Any import from `research/` into the value loader, backtest, management, or
  fast-path value/accounting surfaces.
- Any live trading, paper trading, broker operation, order routing, deployment,
  account operation, or production operation.
- Any profitability, tradability, execution-readiness, or alpha claim.

## DK-P00 Non-Goals

DK-P00 does not author StudySpecs, FeatureRequests, LabelSpecs, SetupSpecs,
MechanismCards, TrialLedger records, VariantLedger records, surrogate reports,
diagnostic reports, evidence bundles, review artifacts, verdict artifacts, PRs,
or merge artifacts.

DK-P00 does not inspect or report real-data IC, returns, buckets, walk-forward,
N_eff, power, diagnostics, or trading values.

## Later-Phase Boundary

Later phases may only add the specific objects authorized by their own reviewed
phase specs. They must preserve the FDR-before-metric order, surrogate-FDR
zero-pass gate, no-second-PnL-truth boundary, additive-only single-factor path,
explicit artifact discipline, and research-only language.
