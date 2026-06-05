# L2 Scope Boundaries

> **Design-only — not implemented.** Future, non-MVP L2/replay concepts for a
> later campaign. No L2 replay, passive-fill, queue, or live/order behavior is
> implemented or authorized in the current system.

The ALPHA_SYSTEM_V1 L2 surface is schema and design readiness only.

## Allowed In This Campaign

- L2 snapshot and event/delta field definitions.
- Explicit `event_ts`, `receive_ts`, and `available_ts` semantics.
- In-memory synthetic validation for required fields, enums, book-level bounds, data versions, quality flags, and snapshot/delta consistency.
- Tiny deterministic synthetic config examples under `configs/data/l2_examples/`.
- Documentation of future replay, queue-position, latency, and passive-fill requirements.

## Not Allowed In This Campaign

- L2 replay engine.
- L3 order-book reconstruction.
- Queue-position model.
- Passive-fill simulation.
- Live market data feed or real-time ingestion.
- Broker, live, or paper trading.
- Executable L2 strategy validation.
- Real L2 data or order-book datasets.
- Alpha, profitability, robustness, tradability, production-execution, or deployment claims.

## Timestamp Boundary

`event_ts` may describe when a source says the book event occurred. `receive_ts` records when the local or feed process received the information. `available_ts` is the earliest valid research-use timestamp. Future L2-derived features must propagate `available_ts` and must fail closed when availability cannot be established.

## Execution Truth Boundary

The Tier 1 reference 1-minute bar engine remains the single PnL truth. L2 design metadata may inform future reviewed work, but it cannot define accounting, fills, order routing, passive fill assumptions, latency simulation, or alternative PnL semantics.

## Artifact Boundary

No real L2 data, order-book data, replay output, generated store, local SQLite/DB file, Parquet, Arrow, Feather, log, cache, or heavy artifact belongs in git. Run-local files under `runs/**` remain local-only and are never staged.
