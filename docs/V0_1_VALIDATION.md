# v0.1 Validation

## Status

ASV1-P29 performs fixture-only end-to-end validation for the `ALPHA_SYSTEM_V1`
local-first v0.1 foundation. The executor recommendation is
`COMPLETE_WITH_WARNINGS`.

The bounded repair re-ran validation in a sanitized local shell with
live-GitHub/auto-merge variables unset and `PYTHONPATH=src` set. The full suite,
required CLI help checks, compile check, campaign file checks, canaries, and
corrected artifact audit passed in that environment. Ralph still owns formal
validation recording, Claude Opus review, verdict parsing, semantic done-check,
PR, CI, and merge gates. This document is correctness validation only. It is not
market evidence and makes no alpha, profitability, robustness, or tradability
claim.

## Evidence Boundary

- Inputs are tiny deterministic fixtures and curated configs.
- Generated outputs are written to temporary local paths during tests.
- Registry checks use temporary local SQLite databases only.
- No raw data, canonical generated data, factor stores, label stores, signal
  stores, grid outputs, review bundles, SQLite databases, logs, caches, or model
  artifacts are commit-eligible evidence.
- L2 coverage is schema and fixture-feature validation only; no replay, queue,
  passive-fill, broker, live, paper, order-routing, or deployment behavior is in
  scope.

## End-to-End Fixture Coverage

| Step | Surface | Executor validation status |
| --- | --- | --- |
| 1 | Data validation | Covered by CLI fixture validation |
| 2 | Canonical 1-minute fixture bars | Covered by temp `build-bars` output |
| 3 | Calendar/session assignment | Covered by synthetic session and `bar_index` assertions |
| 4 | Factor validation | Covered by `FactorSpec` validation |
| 5 | Label generation/alignment | Covered by forward-return labels and diagnostics alignment |
| 6 | Factor compute | Covered by deterministic close-delta factor values |
| 7 | Factor diagnostics | Covered by local study run |
| 8 | Factor card/report generation | Covered by temp factor-card output |
| 9 | Signal/strategy generation | Covered by single-factor threshold signal and temp signal store |
| 10 | Reference backtest | Covered by Tier 1 `reference_1min_v1` run |
| 11 | Cost/slippage | Covered by explicit cost and slippage configs |
| 12 | Management rules | Covered by managed reference fixture |
| 13 | Portfolio sizing | Covered by fixed-notional target to reference quantity |
| 14 | Fast path parity | Covered by scoped parity certification |
| 15 | Bounded grid | Covered by two-combination grid fixture |
| 16 | Management grid | Covered by two-combination management grid fixture |
| 17 | Experiment registry | Covered by temp SQLite registry rows |
| 18 | ML MVP | Covered by temp registry ML run |
| 19 | Multi-symbol fixture | Covered by tiny two-symbol universe fixture |
| 20 | L2 schema/feature fixture | Covered by design-only top-of-book fixture feature |
| 21 | Review bundle generation | Covered by temp local-only review bundle |
| 22 | Registry status | Covered by temp registry status inspection |

## Closeout Gates

| Gate | Executor status |
| --- | --- |
| No-lookahead and timestamp semantics | Covered by aggregate tests and end-to-end alignment checks |
| Reference truth | Reference 1-minute engine remains the single PnL truth |
| Fast path | Acceleration-only and parity-gated for scoped features |
| Registry/reproducibility | Temp SQLite registry and manifests exercised |
| Artifact policy | Corrected audit passes; no generated local artifacts are commit-eligible |
| Claim language | Fixture results are correctness evidence only |
| Promotion governance | Candidate promotion still requires review |
| L2 boundary | Design/fixture-only; no replay or execution behavior |
| Safety boundary | No broker/live/paper/order-routing/deployment scope |

Command results and artifact-audit outputs are recorded in
`handoffs/ASV1-P29.md`.
