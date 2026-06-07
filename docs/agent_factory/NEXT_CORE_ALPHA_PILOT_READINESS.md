# Next Core Alpha Pilot Readiness

`ALPHA_AGENT_FACTORY_MVP` produces the controlled-team contract layer that a
future `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` campaign may consume. Readiness here
means the roles, permissions, tool contracts, research queue, separation rules,
records, memory, runtime bridge contract, and bounded dry-run protocol exist
and are wired to drive the Research Runtime safely. It does not mean any signal
is alpha, profitable, tradable, strategy-ready, paper-ready, live-ready,
broker-ready, or production-ready.

## What Carries Forward

The future Core Alpha Pilot remains a separate, separately authorized campaign
with its own governance, data-admissibility, evidence, review, and human gates.
Agent Factory only prepares the controlled operating layer: constrained roles,
default-deny permissions, value-free tool results, bounded tasks, independent
reviews, auditable records, and rejected-idea memory.

The Core Alpha Pilot must still satisfy the entry and data-readiness blockers
that this campaign carries forward:

- `FEATURE_LABEL_PARQUET_SINK_V1`: the deferred research-scale feature/label
  value sink from [ADR-0006](../../decisions/0006-feature-label-value-storage.md).
  JSONL remains the current audit/small tier; large-scale value-consuming
  studies need the local Parquet tier or separate human authorization.
- `SESSION_LABEL_GUARD_FIX_V1`: the named follow-up for session-context
  features (`rth_flag`, `eth_flag`, `session_minute`). Until it lands or those
  fields are explicitly marked available, session-context feature use remains
  blocked.
- Dataset-registry report rehydration: the structural backlog notes that
  `datasets.sqlite` persists report hashes, not full quality/coverage report
  objects. See
  [docs/STRUCTURAL_BACKLOG.md](../STRUCTURAL_BACKLOG.md#5-dataset-registry-does-not-persist-qualitycoverage-reports-coupling-gap).
  The pilot must use registry and runtime tools and must not bypass accepted
  DatasetVersion policy to work around this gap.

## Operating Boundary

The future pilot may consume Agent Factory only under its own reviewed campaign
contract. That contract must restate accepted-DatasetVersion-only consumption,
runtime-consumed-not-bypassed diagnostics, value-free structured tool outputs,
separation of duties, artifact discipline, and no-claims interpretation.

The human owns risk, capital, live-use, and external operating judgment. Agent
Factory readiness does not confer any paper, live, broker, account, order,
deployment, promotion, strategy, portfolio, or production authority.
