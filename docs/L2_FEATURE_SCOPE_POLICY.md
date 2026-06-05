# L2 Feature Scope Policy

> **Design-only — not implemented.** Future, non-MVP L2/replay concepts for a
> later campaign. No L2 replay, passive-fill, queue, or live/order behavior is
> implemented or authorized in the current system.

The ASV1-P26 L2 feature surface is limited to declarative specs, tiny synthetic
fixtures, deterministic in-memory transforms, and tests for timing and artifact
discipline.

## Allowed

- Draft `FactorSpec`-compatible L2 feature declarations.
- In-memory synthetic fixture transforms over ASV1-P25 snapshot and delta rows.
- `available_ts` propagation from L2 inputs to derived feature values.
- Label-input rejection and no-lookahead tests.
- Quality-flag propagation and conservative missing-level behavior.
- Documentation and tiny synthetic config examples.

## Not Allowed

- Real L2 data ingestion.
- L2 replay engines or order-book reconstruction.
- L3 reconstruction.
- Queue-position models.
- Passive-fill or latency simulation.
- Live or real-time market data feeds.
- Broker, paper-trading, live-trading, order-routing, or deployment scope.
- L2 strategy validation or execution simulation.
- Factor-store materialization by default.
- Alpha, profitability, robustness, tradability, production-readiness, or
  execution-completeness claims.

## Artifact Boundary

No real L2 data, generated feature values, replay output, factor store, local DB,
SQLite file, Parquet, Arrow, Feather, log, cache, or heavy artifact belongs in
git for this phase.

Run-local files under `runs/**` remain local-only and must never be staged. The
commit-eligible handoff belongs under `handoffs/ALPHA_SYSTEM_V1/ASV1-P26.md`.

## Promotion Boundary

The ASV1-P26 declarations are not registered or promoted. A later campaign would
need reviewed replay assumptions, canonical alignment, validation evidence,
artifact policy updates, and explicit human approval before any L2-derived
feature could move toward long-term factor-store materialization.
