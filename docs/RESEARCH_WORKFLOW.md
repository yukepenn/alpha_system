# Research Workflow

## Human Researcher Workflow

The human workflow is local, reviewable, and staged from diagnostics to
validation:

1. Validate local input data and quality flags.
2. Build canonical bars with point-in-time timestamp semantics.
3. Validate factor definitions and declared inputs.
4. Run factor diagnostics before any strategy or grid interpretation.
5. Run bounded study grids for specific hypotheses.
6. Run survivor management grids only after initial diagnostics.
7. Validate finalists with the Reference 1-minute bar execution truth.
8. Build Markdown, CSV, or optional static HTML reports.
9. Review evidence, limitations, versions, and run manifests.

This workflow is for research governance. It does not assert that any result is
tradable, profitable, robust, production-ready, or suitable for live use.

## Workflow 2 Agent Workflow

Workflow 2 uses Ralph as the strict driver and state machine owner. Ralph owns
STOP checks, validation orchestration, handoff validation, review routing,
verdict parsing, repair routing, PR/CI, merge gates, done-checks, and run
summaries.

Codex executes a generated phase spec, makes only scoped repairs when routed,
runs authorized local checks, and writes truthful handoffs. Claude review is a
separate Ralph-routed step for Yellow phases.

Run-local artifacts under `runs/**` remain local-only. Commit-eligible handoffs
belong under `handoffs/<PHASE_ID>.md`.

## Grid Discipline

Grid work follows a diagnostics-first order:

- Diagnostics first: use factor and label diagnostics before grid expansion.
- Bounded grids: define constrained parameter ranges before execution.
- Survivor management grid: only survivors enter management-rule exploration.
- Finalist validation: candidates must return to the Reference truth model.

Fast paths may support throughput only after parity with the Reference engine.
They do not change the evidence standard.

## ML And Factor Combination

ML and factor-combination work is design intent in this baseline. Later phases
must use versioned factor inputs only. They must be ready for purge, embargo,
and walk-forward validation. Labels are not live features. Model reports must
carry data, factor, label, engine, config, code, and run-manifest versions.

## Failure Visibility

Failed runs are part of the research record. They must remain visible in local
run artifacts and handoffs when relevant. A failed run must not be hidden by
rerunning until only successful artifacts remain.
