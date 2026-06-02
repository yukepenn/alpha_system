# ADR-0005: L2 Readiness Is Design Only

## Status

Accepted for v1 design baseline.

## Context

The campaign wants future L2/L3 readiness without creating false execution
completeness. L2 replay, queue modeling, passive fills, and real L2 ingestion
are materially different from 1-minute Reference backtesting.

## Decision

L2 readiness in this campaign is limited to design, schema-readiness language,
and skeleton planning when later phases authorize it. V1 does not implement an
L2 replay engine, queue modeling, passive-fill simulation, or real L2
ingestion.

Tier 4 remains future design-only. Tier 1 Reference 1-minute bar execution is
the canonical v1 truth.

## Consequences

Docs, reports, and handoffs must not describe L2 readiness as complete
execution validation. Review should reject any implementation or claim that
turns design-only L2 scope into a functioning replay or execution engine during
this campaign.
