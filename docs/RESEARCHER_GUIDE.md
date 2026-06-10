# Researcher Guide

## Operating Boundary

`alpha_system` is for offline, local-first research. It helps a researcher move
from data checks to reviewable evidence while preserving point-in-time
semantics, artifact discipline, and clear domain boundaries.

It does not operate broker/live trading, paper trading, order routing,
deployment, or account state. It does not approve candidates or justify alpha,
profitability, robustness, tradability, or production-readiness claims.

## Research Order

Use this order unless an approved phase spec says otherwise:

1. Validate local input data.
2. Build canonical 1-minute bars.
3. Validate factor definitions and dependencies.
4. Materialize only eligible factor values to local-only stores.
5. Generate or inspect labels separately from factors.
6. Run factor diagnostics and factor cards.
7. Define signal and strategy intent.
8. Run bounded strategy grids only after diagnostics justify the question.
9. Run survivor-gated management grids only after an eligible survivor exists.
10. Validate finalists with the Reference 1-minute backtest truth.
11. Inspect management, portfolio, cost, and monthly evidence.
12. Build a review bundle.
13. Review claims, limitations, versions, hashes, manifests, failed steps, and
    rejected configs before any promotion decision.

## Factor Lifecycle

Factor work starts with a `FactorSpec`. The lifecycle is:

```text
draft -> candidate -> validated -> approved -> deprecated
```

Validation checks declared inputs, dependency boundaries, hashes, lifecycle
rules, and registry eligibility. A factor may not consume labels, future
outcomes, raw ad hoc fields, or undeclared inputs. Approval requires reviewed
promotion evidence; a command summary or diagnostic artifact is not approval.

Relevant docs:

- `docs/FACTOR_REGISTRY.md`
- `docs/FACTOR_COMPUTE.md`
- `docs/FACTOR_DIAGNOSTICS.md`
- `docs/FACTOR_CARDS.md`

## Labels And No-Lookahead

Labels are future-information targets for offline research. They are never
factor inputs, live strategy inputs, execution inputs, or order-routing inputs.
Research joins must keep `available_ts` and `label_available_ts` separate.

Any workflow that joins factors and labels must preserve:

- factor id and version
- label id and version
- data version
- instrument id
- event timestamp
- session id
- label horizon where applicable
- availability timestamps

If timestamp, version, hash, or manifest metadata is missing, the result is not
complete for review.

Relevant docs:

- `docs/LABEL_STORE.md`
- `docs/NO_LOOKAHEAD_POLICY.md`

## Diagnostics And Factor Cards

`alpha study run` produces local diagnostic evidence such as IC, rank IC,
bucket statistics, event-study counts, warnings, and a run manifest. Diagnostics
are Tier 0 evidence. They are not strategy PnL truth, not a backtest, not a
candidate decision, and not market evidence.

`alpha report build` can build factor cards and study reports from diagnostic
summaries. Factor cards should separate observed diagnostics, warnings,
recommendations, limitations, review status, and required follow-up.

Relevant docs:

- `docs/FACTOR_DIAGNOSTICS.md`
- `docs/FACTOR_CARDS.md`
- `docs/REPORT_LANGUAGE_POLICY.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`

## Signals, Strategies, Management, And Portfolio

Keep the boundaries explicit:

- Signal is strategy intent at a timestamp.
- Strategy declares entry or exit intent and required factor dependencies.
- Management owns post-entry exits and adjustments such as stops, targets,
  partials, cooldowns, trailing rules, and end-of-day behavior.
- Portfolio owns target sizing and exposure constraints.
- The Reference engine owns fills, costs, accounting, trade journals, and
  equity curves.

None of these layers owns broker state, live state, paper account state, or
production execution.

Relevant docs:

- `docs/SIGNALS_AND_STRATEGIES.md`
- `docs/STRATEGY_BOUNDARIES.md`
- `docs/POSITION_MANAGEMENT.md`
- `docs/PORTFOLIO_BOUNDARIES.md`
- `docs/PORTFOLIO_LAYER.md`

## Reference Truth And Fast Path

The Tier 1 Reference 1-minute bar engine is the single v0.1 PnL truth. It
enforces point-in-time timing, conservative next-bar execution, conservative
same-bar stop/target handling, costs, deterministic trade journals, and equity
curves.

Fast path is acceleration only. It may be used only for parity-certified feature
sets. If parity fails or a requested feature is unsupported, the Reference
engine is authoritative.

Relevant docs:

- `docs/REFERENCE_BACKTEST.md`
- `docs/BACKTEST_TRUTH_POLICY.md`
- `docs/COST_AND_SLIPPAGE.md`
- `docs/FAST_PATH_PARITY.md`
- `docs/FAST_PATH_LIMITATIONS.md`

## Grid Discipline

Grids are bounded local research tools. Every parameter dimension must be an
explicit finite list, and every run must preserve rejected configs and failed
steps. Do not expand grids until diagnostics justify the question.

Use this discipline:

- factor diagnostics before strategy grids
- strategy grids before survivor management grids
- survivor management only for eligible survivors
- finalist validation through the Reference engine
- no hidden rejected configs or failed runs

Relevant docs:

- `docs/GRID_ENGINE.md`
- `docs/GRID_OVERFIT_POLICY.md`
- `docs/MANAGEMENT_GRID_WORKFLOW.md`
- `docs/MANAGEMENT_OVERFIT_POLICY.md`

## ML Workflow

The ML MVP consumes versioned factor inputs and labels under leakage controls.
Labels are never features. Splits are chronological, with purge and embargo
support for leakage control. ML scores are research outputs and do not promote
candidates.

Relevant docs:

- `docs/ML_LAYER.md`
- `docs/ML_LEAKAGE_POLICY.md`

## Registry Inspection

Use `alpha registry status` to inspect local registry versions and run state.
Registry DB files are local-only. Do not stage or commit SQLite files from
`metadata/`, `/tmp`, or any local run location.

Relevant docs:

- `docs/METADATA_REGISTRY.md`
- `docs/EXPERIMENT_REGISTRY.md`

## Review Bundles

Use `alpha report build` to assemble review-bundle evidence after a research
run has manifests and artifacts. Review bundles include source maps, versions,
hashes, registry records, diagnostics, optional backtest sections, warnings,
failed steps, rejected configs, missing artifacts, known limitations, and
review status.

Generated bundles are local-only. They support review and audit; they do not
change lifecycle state or approve candidates.

Relevant docs:

- `docs/REVIEW_BUNDLES.md`
- `docs/SOURCE_MAPS.md`
- `docs/AUDIT_REPORTS.md`

## Research Workflow — Governance Order (folded from RESEARCH_WORKFLOW.md)

Local, reviewable, staged from diagnostics to validation:

1. Validate local input data and quality flags.
2. Build canonical bars with point-in-time timestamp semantics.
3. Validate factor definitions and declared inputs.
4. Run factor diagnostics before any strategy/grid interpretation.
5. Run bounded study grids for specific hypotheses.
6. Run survivor management grids only after initial diagnostics.
7. Validate finalists with the Reference 1-minute bar execution truth.
8. Build Markdown/CSV/optional static HTML reports.
9. Review evidence, limitations, versions, and run manifests.

This is research governance, not a tradability/profitability claim.

**Grid discipline:** diagnostics first; bounded grids defined before execution;
only survivors enter management-rule exploration; finalists return to the
Reference truth model. Fast paths add throughput only after Reference parity —
they never change the evidence standard. ML/factor-combination work uses
versioned factor inputs, must be purge/embargo/walk-forward ready, and labels are
never live features.

**Failure visibility:** failed runs stay visible in local run artifacts and
handoffs; never hide a failed run by rerunning until only successes remain.

> The Workflow-2 agent contract (Ralph/Codex/Claude roles, state machine, lanes,
> run artifacts) lives in `AGENTS.md` and `docs/AI_AGENT_GUIDE.md`.
