# ALPHA_RESEARCH_GOVERNANCE_MVP Campaign Goal

## Campaign Identity

**ALPHA_RESEARCH_GOVERNANCE_MVP — Admissibility and Evidence-Governance Protocol for AI Alpha Research**

* **Campaign ID:** `ALPHA_RESEARCH_GOVERNANCE_MVP`
* **Campaign path:** `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP`
* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories
* **Project profile:** `trading_research` / `research` hybrid
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2
* **Campaign driver:** Ralph strict autonomous loop
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking

## Mission

Build the **admissibility and evidence-governance layer** for AI alpha research:
pre-registration, study control, trial accounting, evidence bundles, reviewer
verdicts, promotion gates, a rejected-idea ledger, and negative controls.

This campaign creates the **admissibility protocol for future AI alpha research**.
It does not search for alpha. It does not validate profitability. It does not touch
broker, live, or paper trading.

## Why This Campaign Exists

After `ALPHA_SYSTEM_V1` and `ASV1_RELEASE_HYGIENE`, the system can run a clean,
deterministic, local-first research harness. But before real data ingestion, broad
AI alpha search, an Agent Factory, ES/NQ/RTY alpha research, an AlphaBook, or any
paper/live/broker integration, the repository needs a **governed evidence pipeline**.

The strategic framing is precise:

```text
ALPHA_SYSTEM_V1        made the system able to run.
ASV1_RELEASE_HYGIENE   made the V1 release baseline clean.
ALPHA_RESEARCH_GOVERNANCE_MVP   decides what research results are allowed to be believed.
```

`alpha_system` is becoming an **AI Alpha Research Factory**, not merely a backtester
and not merely a strategy repository. The long-term north star is an AI-driven,
evidence-gated, cost-aware intraday alpha factory that continuously discovers,
validates, combines, monitors, deweights, and retires alphas under strict
point-in-time and reproducibility rules.

In that factory:

* AI generates research throughput.
* `alpha_system` owns evidence and truth.
* Ralph / Workflow 2 owns process and gates.
* Claude reviews semantics and runs done-checks.
* Codex implements scoped phase specs.
* The human owns direction and risk/capital judgment.

Without this governance layer, moving straight to real data or AI alpha search would
turn the system into a fast overfit machine:

```text
fast idea generation -> fast backtest mining -> fast overfit -> fast false confidence
```

With this layer, every future alpha idea must leave an auditable trail:

```text
who proposed it
why it exists
what hypothesis it tests
what data, features, and labels it uses
what was pre-registered
how many variants were tried
what failed
what was rejected
whether the locked test was touched
whether OOS was reused
what evidence exists
who reviewed it
why it was promoted, rejected, or quarantined
```

## Baseline from ALPHA_SYSTEM_V1 and ASV1_RELEASE_HYGIENE

Both prior campaigns are treated as **complete**. The current baseline is a clean
local-first research harness foundation that already provides:

* domain contracts,
* a factor registry foundation,
* a label store foundation,
* research diagnostics,
* a reference 1-minute backtest execution truth,
* artifact policy and explicit-staging discipline,
* review bundles and source maps,
* deterministic fixture validation,
* release hygiene with validation gates and reference semantics.

That baseline deliberately did **not** provide alpha idea pre-registration, study
budget control, variant-count accounting, failed-run accounting, duplicate-exposure
governance, locked-test contamination records, a reviewer independence protocol,
evidence-bundle requirements, a promotion state machine, a research graveyard, a
negative-control canary catalog, or an agent permission matrix. This campaign supplies
exactly that missing layer.

## What This Campaign Builds

The campaign defines, implements, tests, and documents the governance layer through
20 Workflow 2 phases (`ARGOV-P00` … `ARGOV-P19`). It progressively builds:

* a governance package skeleton and canonical naming,
* governance IDs, serialization, and fail-closed validation primitives,
* the `AlphaSpec` contract and a no-code-before-spec gate,
* the `HypothesisCard` and a pre-registration protocol,
* the `FeatureRequest` object and a duplicate/equivalent exposure guard,
* the `LabelSpec` object and a label-leakage guard,
* the `StudySpec` object and a study-budget protocol,
* the `TrialLedger` with variant accounting and failed-run visibility,
* the `EvidenceBundle` and its manifest contract,
* the `RejectedIdeaLedger` (research graveyard) with first-class rejected records,
* the `PromotionDecision` object and a promotion-gate state machine,
* the `ReviewerVerdict` object and reviewer-independence rules,
* a negative-control canary catalog,
* a no-lookahead / label-leakage / optimistic-fill canary harness,
* governance registry integration with the existing local persistence layer,
* a governance CLI and validation tools,
* an unsupported-claim guard and governance report templates,
* a synthetic end-to-end governance dry run over fixtures,
* Workflow 2 handoff/review/verdict integration, an acceptance audit, and closeout.

It also defines a lightweight `AlphaBookRecord` **stub** purely as a future-compatibility
pointer — it is not the future Portfolio AlphaBook and carries no capital, live, or
production semantics.

## What This Campaign Does Not Build

This campaign must not implement or require any of the following:

* no real alpha search,
* no real data ingestion,
* no IBKR or any broker data connectivity,
* no broad Agent Factory,
* no AlphaBook V1 (only a stub pointer),
* no live trading,
* no paper trading,
* no broker integration,
* no order routing,
* no L2 replay engine,
* no ML/DL expansion,
* no strategy optimization,
* no portfolio allocation,
* no production execution,
* no production-readiness, profitability, or tradability claims.

The campaign ends with no broker integration, no paper trading, no live trading, no
real-data dependency, no production execution adapter, and no alpha/tradability/
profitability claims.

## Hard Governance Rules

```text
No AlphaSpec        -> no code.
No StudySpec        -> no diagnostics.
No EvidenceBundle   -> no candidate.
No TrialLedger      -> no promotion.
No reviewer verdict -> no factor library entry.

Failed ideas remain visible.
Rejected ideas are first-class records.
Variant mining is visible.
Locked-test reuse is recorded as contamination metadata.

Implementation agent cannot approve itself.
Reviewer cannot be the same role as implementer.

Promotion is not live approval.
Validated is not production.
Candidate is not capital allocation.

No real-data campaign begins before governance gates exist.
No AI alpha-search campaign begins before governance gates exist.
```

## Long-Term Principles

The governance layer is intentionally **aggressive about evidence governance** and
**conservative about market claims and trading scope**. It is designed assuming that
future agents will, by default, try many variants, accidentally reuse OOS data,
overinterpret noise, prefer pretty charts, bury failed ideas, promote ambiguous
results, create duplicate factors, leak labels into features, ignore costs, and weaken
tests to pass. The objective is therefore not to trust agents but to make those
behaviors **detectable, blockable, and auditable**.

The layer must remain compatible with — but must not pre-implement — these future
campaigns:

```text
ALPHA_DATA_FOUNDATION_V1
ALPHA_FEATURE_LABEL_FOUNDATION_V1
ALPHA_AGENT_FACTORY_MVP
ALPHA_FUTURES_CORE_ALPHA_V1
ALPHA_PORTFOLIO_ALPHA_BOOK_V1
ALPHA_VALIDATION_GOVERNANCE_V1
```

One sentence captures the posture:

```text
Be aggressive about evidence governance.
Be conservative about market claims and trading scope.
```

## Required Governance Objects

| Object | Purpose | Must not imply |
| ------ | ------- | -------------- |
| `HypothesisCard` | hypothesis rationale and falsification anchor | implementation approval or alpha validity |
| `AlphaSpec` | pre-registered alpha research specification | candidate status or factor library entry |
| `FeatureRequest` | feature/factor input request with duplicate-exposure checks | implementation permission without validation |
| `LabelSpec` | explicit label definition and leakage guard | label quality or predictive value |
| `StudySpec` | diagnostics plan and research budget | diagnostics passed |
| `TrialLedgerRecord` | record of every attempt, including failures | success |
| `EvidenceBundle` | candidate evidence package | promotion unless the gate accepts it |
| `RejectedIdeaRecord` | research graveyard record | permanent ban (reconsideration must be explicit and linked) |
| `PromotionDecision` | controlled state-transition decision | live approval, capital allocation, or production readiness |
| `ReviewerVerdict` | independent semantic review record | market truth or profitability |
| `NegativeControlResult` | record that known-bad controls fail closed | alpha validity (only validates guard behavior) |
| `AlphaBookRecord` (stub) | future-compatibility pointer only | capital allocation, live status, or production approval |

Field-level requirements for each object are specified in `campaign.yaml`
(`governance_objects`) and audited in `ACCEPTANCE.md`.

## Governance State Model Summary

The objects move research ideas through a controlled lifecycle:

```text
DRAFT
  -> REGISTERED              (valid HypothesisCard + AlphaSpec)
  -> IMPLEMENTATION_ALLOWED  (AlphaSpec validation, no blocking duplicate/leakage issue)
  -> IMPLEMENTED             (scoped implementation handoff)
  -> DIAGNOSTICS_ALLOWED     (valid StudySpec)
  -> DIAGNOSTICS_RUN         (diagnostics recorded in TrialLedger)
  -> EVIDENCE_READY          (EvidenceBundle with manifest and trial refs)
  -> REVIEWED                (independent ReviewerVerdict)
  -> REJECTED | WATCH | CANDIDATE | VALIDATED   (PromotionDecision + gate checks)

Any state -> REJECTED        (RejectedIdeaRecord and reason)
```

Blocked transitions:

* missing `AlphaSpec` blocks code,
* missing `StudySpec` blocks diagnostics,
* missing `TrialLedger` blocks promotion,
* missing `EvidenceBundle` blocks candidate,
* missing `ReviewerVerdict` blocks factor library entry,
* self-review blocks promotion,
* locked-test contamination without metadata blocks promotion,
* failed-run omission blocks promotion,
* unsupported claims block merge.

The states `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` are **prohibited
MVP states**. They may be named only as future, non-MVP concepts and must not be
reachable by any transition implemented in this campaign.

## Success Definition

The campaign is successful when `alpha_system` has a governance layer that:

1. Refuses code without a valid `AlphaSpec`.
2. Anchors every idea to a pre-registered `HypothesisCard` with falsification criteria.
3. Routes feature requests through a duplicate/equivalent exposure guard against the existing factor registry.
4. Defines labels through `LabelSpec` and blocks label-as-feature and future leakage.
5. Requires a `StudySpec` with explicit study budget before diagnostics run.
6. Records every trial — including failures, variants, OOS-touched, and locked-test contamination — in a `TrialLedger`.
7. Requires an `EvidenceBundle` with a manifest, hashes, versions, and negative-control results before any candidate.
8. Treats rejected, duplicate, leaky, and weak ideas as first-class `RejectedIdeaRecord` ledger entries.
9. Gates promotion through a state machine that cannot reach candidate/validated without trial ledger, evidence, and an independent reviewer verdict.
10. Enforces reviewer independence and blocks implementer self-approval.
11. Provides negative-control canaries that fail closed and a no-lookahead/leakage/optimistic-fill harness.
12. Integrates governance objects with the existing local registry/persistence layer without committing the database.
13. Exposes a governance CLI and validation tools.
14. Blocks unsupported alpha/profitability/tradability claims and provides governance report templates.
15. Passes a synthetic end-to-end governance dry run over fixtures, with negative controls failing closed.
16. Integrates with Workflow 2 handoff/review/verdict semantics and passes an acceptance audit and semantic done-check.
17. Commits no raw data, heavy artifacts, local databases, caches, or logs.
18. Contains no broker/live/paper scope and no real-data or alpha-search scope.

## Out-of-Scope Claims

This campaign must not claim that any alpha is validated, that any strategy is
profitable, tradable, robust, production-ready, paper-ready, live-ready, or
broker-ready, or that the system is ready for real data. It produces governance
machinery only; it produces no market evidence and no market claims.

## Relationship to Next Campaigns

`ALPHA_RESEARCH_GOVERNANCE_MVP` is the gate that future campaigns must pass through.
Once the admissibility protocol exists and is reviewed, later campaigns may add real
data ingestion (`ALPHA_DATA_FOUNDATION_V1`), feature/label foundations
(`ALPHA_FEATURE_LABEL_FOUNDATION_V1`), an agent factory
(`ALPHA_AGENT_FACTORY_MVP`), core futures alpha research
(`ALPHA_FUTURES_CORE_ALPHA_V1`), a portfolio AlphaBook
(`ALPHA_PORTFOLIO_ALPHA_BOOK_V1`), and deeper validation governance
(`ALPHA_VALIDATION_GOVERNANCE_V1`) — each only under its own explicitly authorized
campaign contract, and each constrained by the governance gates this campaign installs.
