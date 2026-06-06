# Research Runtime Overview

`ALPHA_RESEARCH_RUNTIME_MVP` builds the executable research loop layer between
the completed Feature/Label substrate and the future Agent Factory. Its job is
to make one approved `AlphaSpec` plus `StudySpec` runnable as a deterministic,
local, fail-closed study. It records descriptive diagnostics and governed
evidence, not alpha claims.

## Mission

The runtime will orchestrate existing primitives to resolve accepted
DatasetVersions and registered Feature/Label packs, run diagnostics, cost
stress, bounded probes, variant-budget checks, and no-lookahead audits, then
emit an `EvidenceDraft`, rejection reasons, and a
`ReferenceCandidateHandoff` when the run reaches that point.

The runtime owns the execution loop for approved studies. It does not decide
what to study, search broadly for hypotheses, promote factors, validate
strategies, optimize portfolios, or make trading claims.

## Tier Model

The campaign uses four descriptive tiers to keep runtime outputs scoped:

- Tier 0 diagnostics: feature/factor, label, session/regime/RTH/ETH,
  cross-market, and cost-aware diagnostics. These reports describe coverage,
  quality, stability, and sensitivity. They do not validate alpha.
- Tier 1 probe: a simple, bounded signal probe tied to an approved
  `AlphaSpec` and `StudySpec`, with cost stress and no same-bar optimistic
  fills. A signal probe is not a strategy candidate.
- Tier 2 handoff: a `ReferenceCandidateHandoff` package for downstream
  Reference validation. It is not completed Reference validation and does not
  promote a candidate.
- Tier 3 evidence draft: an `EvidenceDraft` assembled from diagnostics, probe,
  cost, bounded-grid, and audit outputs for governance consumption. It is not a
  candidate and is not Reference truth.

The tier labels are an orientation model, not a promotion ladder. The fast path
is not Reference truth.

## Runtime Decision Lifecycle

The campaign contracts the runtime lifecycle as:

```text
RUNTIME_REQUESTED
  -> INPUTS_RESOLVED
  -> PLAN_VALIDATED
  -> DIAGNOSTICS_READY
  -> DIAGNOSTICS_RUNNING
  -> DIAGNOSTICS_COMPLETE / DIAGNOSTICS_FAILED
  -> SIGNAL_PROBE_READY
  -> SIGNAL_PROBE_COMPLETE
  -> COST_STRESS_COMPLETE
  -> EVIDENCE_DRAFT_READY
  -> REFERENCE_HANDOFF_READY
```

Terminal outcomes are `REJECTED`, `INCONCLUSIVE`, and `BLOCKED`. The most
advanced survivor state is `REFERENCE_HANDOFF_READY`.

The prohibited MVP states are not valid runtime outcomes:
`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`,
`LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`, and
`PRODUCTION_READY`.

## Load-Bearing Boundaries

- No `AlphaSpec` plus `StudySpec` means no runtime run.
- Accepted DatasetVersions are consumed only through
  `alpha_system.data.foundation.version_registry.resolve_dataset_version`.
- Feature inputs carry `available_ts`; label inputs carry
  `label_available_ts`; labels are never exposed as live features.
- Raw provider files, provider responses, parquet, arrow, feather, DBN, Zstd,
  local DBs, runtime heavy outputs, and generated reports remain local-only and
  uncommitted.
- Databento and IBKR DatasetVersions are separate inputs. Databento is the
  primary deep-history research source; IBKR is broker-source recent validation
  only. This campaign makes no external provider calls.
- Cost stress is required for probes and handoffs. Slippage is labeled as a
  proxy, and zero-cost results are never a promotion basis.
- Every grid is bounded by a `VariantBudget`; there is no unbounded grid and no
  locked-test selection without governance contamination metadata.
- Failed and inconclusive runs remain visible through rejection and decision
  records.
- Runtime modules orchestrate existing research, experiments, governance,
  backtest, data, feature, and label primitives instead of duplicating them.
- The campaign introduces no broker, live, paper, order, account, broad
  alpha-search, factor-promotion, strategy, backtest, portfolio, tradability,
  profitability, or production scope.
