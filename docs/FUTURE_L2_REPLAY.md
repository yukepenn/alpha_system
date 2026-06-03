# Future L2 Replay

This document records future replay design needs without implementing replay in ALPHA_SYSTEM_V1.

## Future Book Reconstruction Needs

A reviewed future campaign would need source-specific sequencing rules, gap detection, reset handling, snapshot refresh rules, crossed-book policy, level compaction rules, and recovery behavior for missing or duplicated deltas. ASV1-P25 only defines fields that such a design would need to inspect.

## Event Ordering

Future reconstruction must distinguish source-event order from research-availability order:

- Source-event ordering starts with `event_ts`, then `receive_ts`, then `available_ts`, with `sequence_id` as a deterministic tie-breaker when present.
- Research consumption starts with `available_ts`; records are not usable before that timestamp even when `event_ts` is earlier.

This separation protects no-lookahead behavior for future L2-derived features.

## Snapshot/Delta Consistency

Snapshots and deltas must share instrument, session, and data-version context. A future replay design also needs explicit rules for sequence gaps, snapshot resets, crossed or locked states, deletes for absent levels, and clear actions. ASV1-P25 validates only the schema-level consistency contract on synthetic in-memory records.

## Queue Position, Latency, And Passive Fills

Future queue-position research would need venue priority rules, order-count semantics, cancels, replaces, and L3 assumptions. Future latency models would need clock policy, feed receive behavior, and evidence for availability delays. Future passive-fill research would require validated replay and reviewed queue assumptions.

None of those engines or simulations exists in this campaign.

## Out Of Scope

L2 replay is out of scope because ALPHA_SYSTEM_V1 keeps one execution truth: the Tier 1 reference 1-minute bar engine. This phase does not add a second PnL truth, order-book reconstruction, passive-fill simulation, queue-position model, executable L2 strategy validation, live feed ingestion, broker execution, paper trading, or deployment behavior.

The L2 design must not be read as complete execution infrastructure or production execution readiness.
