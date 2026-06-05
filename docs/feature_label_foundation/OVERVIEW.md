# Feature/Label Foundation Overview

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` builds the research substrate between the
accepted data foundation and future governed studies. Its target surface is a
versioned, no-lookahead-safe, deduplicated, cost-aware, BBO-aware FeatureStore
and LabelStore over accepted DatasetVersions.

The campaign does not search for alpha, evaluate strategies, run backtests, make
portfolio decisions, call external providers, or operate broker interfaces. It
prepares the controlled substrate that later research workflows may consume
through governance.

## Substrate Shape

The data foundation is the only entry point. Feature and label workflows consume
DatasetVersions resolved from the local registry, then reconstruct rows through
canonical record contracts. They do not inspect Databento DBN/Zstd files, IBKR
responses, parquet, arrow, feather, or other provider-shaped files directly.

The substrate is built around four boundaries:

- Accepted DatasetVersions: only `VERSIONED` or `READY_FOR_RESEARCH` inputs with
  non-blocking quality and coverage are admissible.
- Point-in-time availability: features carry `available_ts`; labels carry
  `label_available_ts`; joins and audits preserve the distinction.
- Governance reuse: `FeatureRequest`, `LabelSpec`, `StudySpec`, `AlphaSpec`,
  duplicate-exposure, and label-leakage guards are consumed from the existing
  governance layer rather than redefined.
- Local-only materialization: feature values, label values, registry databases,
  raw data, canonical data, logs, caches, and heavy artifacts remain outside the
  repository.

## No-Lookahead Posture

Canonical OHLCV and BBO records already carry availability semantics. Feature
input views must order usability by `available_ts`, not by provider time,
`event_ts`, or `ingested_at`. Feature transforms must be causal for live-feature
contracts: future and centered windows are not valid live feature inputs.

Labels may use future observations inside their declared horizon, but only as
offline targets. A label becomes usable for research at `label_available_ts`.
Labels are never exposed as features, strategy inputs, broker inputs, order
inputs, or live decision inputs.

BBO data is explicit about quote quality. Missing or quarantined top-book data
is flagged with `missing_bbo` or `bbo_quarantined`, not silently forward-filled.
Dense research grids are explicit about no-trade minutes: synthetic rows carry
`has_trade=false`, `synthetic=true`, and the `no_trade` quality flag.

## FeatureStore Responsibilities

The FeatureStore side of the substrate will organize feature contracts,
versions, lineage, materialization plans, quality reports, coverage reports,
duplicate-exposure reports, equivalent-feature groups, and deprecation records.

It is not a dumping ground. A feature must pass through the request and spec
gates before implementation and materialization. Duplicate or equivalent
exposure is recorded, grouped, rejected, or deprecated rather than silently
accumulated under a new name.

Feature families planned by the campaign cover:

- base OHLCV transforms;
- BBO/top-book and liquidity-quality diagnostics;
- session, calendar, and roll context;
- ES/NQ/RTY cross-market context;
- liquidity sweep and structure primitives.

These families are substrate inputs only. Their existence does not make any
claim about predictive value.

## LabelStore Responsibilities

The LabelStore side of the substrate will organize label contracts, versions,
lineage, materialization plans, quality reports, coverage reports, leakage
audits, and availability policies.

Label families planned by the campaign cover:

- fixed-horizon and midprice forward labels;
- cost-adjusted and spread-adjusted labels;
- path labels such as MFE, MAE, and triple barrier;
- strategy-agnostic event labels.

Labels are offline research targets. They are not live features, not candidate
signals, and not strategy logic.

## DatasetVersion Entry Flow

The expected entry flow is:

```text
accepted DatasetVersion
  -> canonical OHLCV / BBO / dense-grid input views
  -> governed FeatureSpec or LabelSpec
  -> local-only materialization plan
  -> FeatureVersion or LabelVersion
  -> FeatureStore or LabelStore registry record
  -> StudySpec input pack
```

The flow is fail-closed: missing request/spec governance, inadmissible
DatasetVersions, missing availability timestamps, missing contamination metadata
for locked-test use, or raw-provider access blocks the path.

## DAG-Wave Execution Posture

The campaign runs under Workflow 2 with the DAG-wave scheduler. Ralph owns phase
selection, STOP checks, validation orchestration, review routing, verdict
parsing, PR/CI/merge gates, done-checks, and run summaries. Codex executes the
generated phase spec and writes truthful handoffs. `ACTIVE_CAMPAIGN.md` is
coordinator-owned in DAG-wave mode and phase branches do not write it.

FLF-P00 is a run-alone bootstrap phase in merge group `foundation`.

The intended wave shape is:

- Wave 0: sequential bootstrap and core contracts (`FLF-P00` through
  `FLF-P07`).
- Wave 1: parallel feature-family phases (`FLF-P08` through `FLF-P12`) with
  disjoint paths.
- Wave 2: sequential feature integration (`FLF-P13` through `FLF-P15`).
- Wave 3: label contracts, then parallel label-family phases (`FLF-P16`
  through `FLF-P20`).
- Wave 4: sequential label integration (`FLF-P21` through `FLF-P23`).
- Wave 5: diagnostics, fixtures, governance integration, and docs fan-out
  (`FLF-P24` through `FLF-P29`, with only the declared disjoint phases
  parallelized).
- Wave 6: sequential dry run and closeout (`FLF-P30` and `FLF-P31`).

Builds may run concurrently only for phases with explicit parallel-safe DAG
metadata and disjoint allowed paths. Merges remain serial.
