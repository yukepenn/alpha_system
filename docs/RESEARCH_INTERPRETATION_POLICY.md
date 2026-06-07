# Research Interpretation Policy

## Purpose

This policy governs how researchers and AI Agents interpret `alpha_system`
diagnostics, grids, ML outputs, backtests, reports, review bundles, and fixture
results. It exists to prevent unsupported claims and review drift.

## Prohibited Unsupported Claims

Do not state or imply that a factor, strategy, management rule, portfolio
setting, model, report, or bundle is:

- alpha
- profitable
- robust
- tradable
- approved
- promoted
- production-ready
- deployable
- suitable for live use
- suitable for paper trading
- suitable for broker execution
- safe to route orders

These words may appear in policy text as prohibited vocabulary. They must not
appear as affirmative claims about a research output unless a later reviewed
campaign explicitly authorizes the claim standard and the evidence satisfies it.

## Recommendation Is Not Approval

A report may recommend additional review or mark a candidate for follow-up when
the underlying command supports that advisory field. That is not approval.

Approval requires the reviewed lifecycle or promotion gate for the relevant
object. A diagnostic recommendation, grid rank, ML score, backtest result, or
review bundle is evidence for review, not a state transition by itself.

## Fixtures Are Not Market Evidence

Tiny deterministic fixtures validate correctness properties such as schema
handling, timestamp alignment, conservative fills, parity, rejected-config
visibility, and artifact-policy behavior.

Fixture outputs are not evidence that a hypothesis works in market data. Do
not use fixture results to support alpha, profitability, robustness,
tradability, approval, production, broker, paper, or live-use claims.

## Evidence Layer Boundaries

Interpret each layer according to its scope:

| Layer | What It Can Say | What It Cannot Say |
| --- | --- | --- |
| Data validation | Local input conforms to configured schema, calendar, quality, and timestamp checks. | Data source is complete, reliable for all research, or free of future issues. |
| Factor validation | A spec satisfies declared input, hash, lifecycle, and dependency rules. | The factor has predictive value or is approved. |
| Labels | Future-information targets are generated with availability metadata. | Labels may be used as live features or strategy inputs. |
| Diagnostics | Descriptive relationships, warnings, and alignment evidence for versioned factor/label pairs. | PnL truth, candidate approval, market evidence, or tradability. |
| Strategy grids | Bounded local comparisons under declared configs and versions. | Exhaustive search, proof of robustness, or promotion. |
| Management grids | Survivor-gated exploration of post-entry rules. | Approval of a strategy or replacement for reference truth. |
| ML runs | Fixture or local model scoring under leakage controls. | Production model readiness or promotion approval. |
| Reference backtest | Canonical v0.1 1-minute PnL accounting for declared local bars and signals. | Broker/live trading, paper trading, order routing, deployment, or strategy approval. |
| Fast path | Acceleration for parity-certified feature sets. | Separate PnL truth or relaxed evidence standard. |
| Review bundle | Inspectable local evidence package for review. | Automatic lifecycle state change or approval. |

## Required Report Language

Use factual language:

- "diagnostic summary"
- "local fixture"
- "bounded grid"
- "reference backtest output"
- "candidate for review"
- "review required"
- "warning"
- "known limitation"
- "rejected config"
- "failed step"
- "missing artifact"

Avoid language that makes the evidence sound final. If evidence is incomplete,
say what is missing: sample size, versions, hashes, label coverage, cost
sensitivity, review status, registry record, source map, run manifest, failed
run visibility, or no-lookahead validation.

## Promotion And Review

Promotion requires a separate reviewed decision with reviewer metadata and
recorded status. A CLI command may record diagnostics or run evidence, but it
must not silently approve a factor, strategy, model, or portfolio configuration.

If review is missing, state "review required" or "not reviewed". Do not phrase
missing review as a warning that can be ignored.

## Horizon And Session-Segment Scope

The primary starting research horizon is the 5–30 minute band; it is a starting
band, not a hard cap, and only a later authorized campaign may extend it. The one
hard intraday boundary is that research holdings are flat before the exchange
daily maintenance / trade-date break and intraday targets resolve on the same
trade date.

ETH, RTH, pre-RTH, and post-RTH are all research-in-scope, but session-segment
results must be interpreted with per-segment diagnostics and with stricter cost
stress in thin sessions (ETH, pre-RTH, post-RTH). Do not generalize a result
measured in one session segment to another, and do not treat liquid-RTH cost
assumptions as valid for thin sessions. Session-segment fields such as
`session_label`, `session_segment`, `rth_flag`, `eth_flag`, and `session_minute`
are point-in-time session metadata, not labels; see
[SESSION_LABEL_GUARD_FIX_V1](../decisions/0006-feature-label-value-storage.md)
context and the no-lookahead guard.

## L2 And Event-Driven Scope

During this campaign, L2 and event-driven execution are design-readiness or
fixture-only scopes where documented. Do not describe L2 replay, queue
position, passive-fill simulation, live event processing, or complete
event-driven execution as implemented unless a later reviewed phase explicitly
adds that behavior.
