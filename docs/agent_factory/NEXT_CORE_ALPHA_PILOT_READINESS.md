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

- `FEATURE_LABEL_PARQUET_SINK_V1`: **LANDED** by
  `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`. The research-scale Parquet feature/label
  value sink from [ADR-0006](../../decisions/0006-feature-label-value-storage.md) is
  implemented (`core/value_store.py`, dual JSONL+Parquet writer/reader, registry
  `parquet_path`/`value_content_hash`/`value_store_format` metadata, and
  `feature|label materialize --value-store {jsonl,parquet,dual}`). JSONL remains the
  audit/small tier; Parquet is the research-scale tier. The preflight
  `parquet_sink_landed` gate is now satisfied.
- `SESSION_LABEL_GUARD_FIX_V1`: **LANDED** by
  `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`. Session-context features (`rth_flag`,
  `eth_flag`, `session_minute`) now pass the runtime no-lookahead/leakage guard when
  their canonical `session_label` input is declared `SESSION_METADATA` via
  `FeatureInputSpec.input_metadata.field_roles`; true labels and forward-looking
  fields remain blocked regardless of declaration. See
  [SESSION_LABEL_GUARD.md](../research_runtime/SESSION_LABEL_GUARD.md). The preflight
  `session_label_guard_fixed` gate is now satisfied.
- Dataset-registry report rehydration: the structural backlog notes that
  `datasets.sqlite` persists report hashes, not full quality/coverage report
  objects. See
  [docs/STRUCTURAL_BACKLOG.md](../STRUCTURAL_BACKLOG.md#5-dataset-registry-does-not-persist-qualitycoverage-reports-coupling-gap).
  The pilot must use registry and runtime tools and must not bypass accepted
  DatasetVersion policy to work around this gap.

## Horizon And Session-Segment Research Policy

This policy states forward-looking research scope for the future Core Alpha
Pilot. It is policy text, not implemented enforcement: this hardening campaign
does not build an event calendar, does not change the seed-pack scope, and does
not materialize a broad label family. The seed smoke remains the small ES window
with `fwd_ret_5m`/`fwd_ret_10m`/`fwd_ret_30m`.

- **Primary starting horizon, not a hard cap.** The 5–30 minute horizon band is
  the *primary starting* research horizon for the future pilot, not a hard
  ceiling. Later, separately authorized work may extend the horizon band when
  diagnostics and cost evidence support it. Existing seed labels stay at
  5–30 minutes; nothing here widens materialized label horizons.
- **Hard intraday boundary.** The hard intraday boundary is flat before the
  exchange daily maintenance / trade-date break. No position or label horizon may
  cross that break: holdings are flat ahead of it, and intraday targets resolve
  on the same trade date. This is the one non-negotiable horizon limit.
- **Session segments are research-in-scope.** ETH, RTH, pre-RTH (pre-open), and
  post-RTH (post-close) are all research-in-scope for the future pilot. None is
  excluded a priori; the system design lets diagnostics and cost gates — not a
  human prior — decide which segments carry usable signal.
- **Required guards for session-segment research.** Any session-segment study
  must (1) report session-segment diagnostics (per-segment coverage, sample
  counts, and signal/turnover behavior split by ETH / RTH / pre-RTH / post-RTH),
  and (2) apply stricter cost stress in thin sessions — wider spread/slippage and
  capacity assumptions for ETH and pre/post-RTH segments relative to liquid RTH.
  Session-segment context is consumed as point-in-time session metadata (see
  `SESSION_LABEL_GUARD_FIX_V1`), never as a future-resolved label.

## Operating Boundary

The future pilot may consume Agent Factory only under its own reviewed campaign
contract. That contract must restate accepted-DatasetVersion-only consumption,
runtime-consumed-not-bypassed diagnostics, value-free structured tool outputs,
separation of duties, artifact discipline, and no-claims interpretation.

The human owns risk, capital, live-use, and external operating judgment. Agent
Factory readiness does not confer any paper, live, broker, account, order,
deployment, promotion, strategy, portfolio, or production authority.
