# FactorLibrary And Multi-Horizon Mining Handoff

`FUTSUB-P32` creates the downstream requirement handoffs for
`ALPHA_FACTOR_LIBRARY_V1` and
`ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1`.

## Artifacts

- FactorLibrary requirements:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FACTOR_LIBRARY_HANDOFF.md`
- Multi-horizon mining requirements:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/MULTI_HORIZON_MINING_HANDOFF.md`
- Closeout evidence index:
  `research/futures_substrate_scaleout_v1/closeout/factor_library_and_mining_evidence_index.md`

## Current Verdict Context

The handoffs cite `FUTSUB-P29` as the verdict source. The current refreshed
boundary is `10 REJECT / 0 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`.
That means FUTSUB currently provides no FactorLibrary-ingestible survivor.

This page does not re-judge the verdict refresh, create a FactorLibrary entry,
start mining, run diagnostics, create AlphaSpecs or StudySpecs, or promote any
research output.

## Substrate Base For Downstream Consumers

The consumable base is the value-local, registry-resolved FUTSUB substrate
documented by value-free evidence:

- eight feature families over ES/NQ/RTY for the accepted 2019-2026 window;
- label surfaces from 1m through 240m plus session-close, maintenance-flat,
  cost-adjusted, and path labels;
- feature and label resolver-smoke evidence with exact-id, fail-closed
  semantics;
- feature-family, label-family, symbol-horizon, session-horizon, BBO-quality,
  cross-market-alignment, roll-window, and maintenance-crossing matrices;
- purged / embargoed walk-forward metadata and overlap-aware N_eff reporting
  contracts.

2018 remains expected-excluded. 2019 and 2026 remain usable only with warning
context preserved.

## FactorLibrary Reading Contract

`ALPHA_FACTOR_LIBRARY_V1` should treat FUTSUB as a no-entry / ingestion-gap
input unless a later reviewed campaign creates an eligible `WATCH` or
`CANDIDATE_RESEARCH` survivor. Any future ingestion must require exact StudySpec,
FeatureVersion, LabelVersion, DatasetVersion, verdict, review, coverage, guard,
N_eff, and artifact-locality references.

FactorLibrary records must reference evidence by path and stable id. They must
not embed values, local registry content, Parquet payloads, run-local artifacts,
or unsupported live/trading/production states.

## Mining Reading Contract

`ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1` should consume the substrate and
matrices as availability and quality gates, not as mined signal evidence. Any
mining campaign must pre-register the population, family budgets, variant
budgets, symbols, years, horizons, session segments, cost surfaces, BBO /
cross-market filters, split protocol, N_eff handling, guard handling,
duplicate-exposure grouping, and stopping rules before reading results.

Mining must preserve:

- exact-id resolver semantics;
- `available_ts <= decision_ts < label_available_ts`;
- roll-splice and maintenance-crossing guard drops;
- BBO proxy limits;
- cross-market strict-intersection semantics;
- rows-versus-effective-samples distinction;
- no-values-committed artifact policy.

## Non-Claims

These handoffs make no alpha, profitability, robustness, tradability,
production, paper/live, broker, order-routing, deployment, or
capital-allocation claim. They are requirement handoffs only.

