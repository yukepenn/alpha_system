# Backtest Truth Policy

## Single PnL Truth

For ALPHA_SYSTEM_V1, the Tier 1 reference 1-minute bar engine is the canonical
PnL truth for 1-minute strategy research. If another component needs PnL
semantics, it must defer to the reference engine's behavior.

There must not be a second or conflicting PnL truth in this campaign.

## Fast Path Rule

Fast-path simulation is deferred to ASV1-P19. When introduced, it is
acceleration only. It may not define separate accounting, fill, cost,
stop/target, or EOD semantics. It must prove deterministic parity with the
Tier 1 reference engine for the selected feature set before any use.

If parity fails, the reference engine is authoritative.

## No-Lookahead Rule

Backtest truth depends on information availability, not on event timestamps
alone. The reference engine uses bar and signal `available_ts` checks and
default next-bar conservative execution to prevent a signal from executing
before the information needed to create it was available.

## Research Boundary

The reference engine is offline research infrastructure. It does not route
orders, connect to brokers, operate live or paper accounts, deploy systems, or
promote strategy candidates. Fixture outputs are correctness checks only and are
not market evidence.
