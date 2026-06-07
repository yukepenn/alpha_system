# Futures Core Alpha Pilot Overview

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is a bounded research-only pilot for the
completed Data, Feature/Label, Research Runtime, and Agent Factory stack. It is
designed to exercise one controlled ES/NQ/RTY research loop through sanctioned
interfaces and produce reviewable, value-free evidence artifacts.

The campaign bundle is the source of truth. If this overview disagrees with
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`, the campaign bundle wins and the
disagreement should stop execution until repaired.

## Mission

The pilot tests whether the research operating system can move from a bounded
hypothesis through AlphaSpec, StudySpec, runtime diagnostics, cost/session/regime
review, no-lookahead audit, TrialLedger and RejectedIdeaLedger recording, and a
bounded research decision.

Allowed decision states are:

```text
REJECT
INCONCLUSIVE
WATCH
CANDIDATE_RESEARCH
```

These states are research states only. They do not authorize factor promotion,
strategy validation, paper trading, live trading, broker operations, order
routing, production deployment, or capital allocation.

## Lanes

- `FUTCORE-P00` is Green bootstrap scaffolding.
- `FUTCORE-P01` through `FUTCORE-P30` are Yellow phases unless a later reviewed
  spec says otherwise.
- The campaign expects no Red scope. External, destructive, live, production,
  costly, or broker-adjacent operations require explicit scoped authorization and
  are outside this bootstrap phase.

## Boundaries

- Inputs resolve only through approved registry and runtime tool surfaces.
- Research-scale value scans use registry-resolved Parquet packs; raw provider
  files, arbitrary value paths, and external provider calls are out of scope.
- Diagnostics run through the Research Runtime tool surface and are not
  reimplemented in pilot code.
- The pilot consumes `src/alpha_system` primitives. It does not edit runtime,
  governance, agent factory, research, experiment, backtest, data, core, signal,
  strategy, portfolio, report, factor, CLI, feature, or label primitives in this
  phase.
- Features and labels may be added only in `FUTCORE-P15`, and only through the
  campaign's FeatureRequest / LabelSpec process.
- `runs/**`, raw or canonical data, feature or label values, provider responses,
  heavy artifacts, local databases, logs, caches, and secrets remain local-only.

## Source Of Truth

- Campaign contract: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`
- Active pointer: `ACTIVE_CAMPAIGN.md`
- Commit-eligible research evidence root:
  `research/futures_core_alpha_pilot_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`
- Optional commit-eligible reviews:
  `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`
