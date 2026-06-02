# ASV1-P02 Handoff

## Phase

- Phase ID: `ASV1-P02`
- Phase name: Architecture Baseline and Local-First PLAN.md
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p02-architecture-baseline-and-local-first-plan.md`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Base commit before P02 edits: `eb828b2`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P02` (local-only)

## Files Created Or Updated

Docs:

- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/LOCAL_FIRST_STACK.md`
- `docs/RESEARCH_WORKFLOW.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

Decision records:

- `decisions/0001-local-first-stack.md`
- `decisions/0002-reference-backtest-truth.md`
- `decisions/0003-domain-boundary-separation.md`
- `decisions/0004-no-broker-live-in-v1.md`
- `decisions/0005-l2-readiness-design-only.md`

Optional small status/link updates:

- `README.md`
- `PROJECT_STATUS.md`

Handoff:

- `handoffs/ASV1-P02.md`

## Architecture Summary

The baseline documents `alpha_system` as a local-first Alpha Research Platform,
not merely a backtester. The architecture separates local storage and registry,
data validation, factor definitions, labels, diagnostics, signals, strategies,
portfolio management, Reference backtest truth, Fast path acceleration, reports,
and Workflow 2 orchestration.

The docs lock down point-in-time timestamp semantics, domain boundaries,
artifact discipline, reproducibility requirements, target CLI design intent,
human researcher workflow, and Workflow 2 agent workflow. This phase is
documentation and decision-record only.

## Local-First Stack

V1 stack intent:

- Local Parquet for large datasets.
- SQLite as the local metadata and registry source of truth, design intent
  only.
- DuckDB for local SQL over Parquet.
- Polars for lazy dataframe pipelines.
- NumPy for arrays.
- Numba for hot loops and Fast path acceleration only.
- Markdown, CSV, and optional static HTML reports with no server required.

Explicitly excluded as hard dependencies for v1: ClickHouse, QuestDB,
DolphinDB, kdb+, ArcticDB, S3, cloud object storage, paid databases, database
servers, Dagster, Prefect, Ray, MLflow server, and web UI.

## Backtest Tiers

The tier model is documented in `docs/BACKTEST_TIERS.md` and
`decisions/0002-reference-backtest-truth.md`.

- Tier 0: factor research engine; no full trade simulation and no tradability
  claims.
- Tier 1: Reference 1-minute bar execution truth; conservative,
  deterministic, point-in-time, and the single canonical PnL truth for v1.
- Tier 2: Fast path parity; NumPy/Numba acceleration only and never a second
  PnL truth.
- Tier 3: future event-driven execution truth design-readiness only.
- Tier 4: future L2/L3 replay design only.

There must never be two conflicting PnL truths. If a fast or future design path
disagrees with the Reference engine, Reference behavior wins.

## No-Lookahead Summary

`docs/NO_LOOKAHEAD_POLICY.md` defines separate `event_ts`, `bar_start_ts`,
`bar_end_ts`, `receive_ts`, `available_ts`, and `label_available_ts` semantics.
Completed bars are usable only after `bar_end_ts` plus configured latency.
Signals on bar `t` cannot execute inside bar `t` by default. The default is
conservative next-bar execution, with conservative same-bar stop and target
handling.

Labels remain separate from live feature inputs. Missing timestamp/version/hash
metadata makes a result incomplete for review.

## Domain Boundaries

`docs/DOMAIN_BOUNDARIES.md` and
`decisions/0003-domain-boundary-separation.md` state the core invariants,
including `Data is not factor`. The docs also state that factor is not signal,
signal is not strategy, strategy is not portfolio, portfolio is not execution,
backtest is not live trading, and fast research simulation is not execution
truth.

Draft factor values are not automatically long-term stored. Only validated and
reviewed factors may be materialized into the long-term factor store.

## L2 Design-Only Confirmation

L2 readiness is documented as design, schema-readiness language, and skeleton
planning only. V1 does not implement L2 replay, queue modeling, passive-fill
simulation, or real L2 ingestion. Tier 4 remains future design-only.

## Validation Results

All commands below were run locally by Codex for handoff evidence. Ralph still
owns formal checks recording, review routing, verdict parsing, done-check, PR,
CI, and merge gates.

```text
test -f runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - no STOP file was active before Codex execution.

git status --short
PASS - showed only expected ASV1-P02 docs, decisions, README/status updates
and handoff changes.

test -f docs/PLAN.md
test -f docs/ARCHITECTURE.md
test -f docs/LOCAL_FIRST_STACK.md
test -f docs/RESEARCH_WORKFLOW.md
test -f docs/DOMAIN_BOUNDARIES.md
test -f docs/NO_LOOKAHEAD_POLICY.md
test -f docs/BACKTEST_TIERS.md
test -f docs/ARTIFACT_POLICY.md
test -f docs/REPRODUCIBILITY_PRINCIPLES.md
test -f docs/CLI_COMMANDS_TARGET.md
test -f decisions/0001-local-first-stack.md
test -f decisions/0002-reference-backtest-truth.md
test -f decisions/0003-domain-boundary-separation.md
test -f decisions/0004-no-broker-live-in-v1.md
test -f decisions/0005-l2-readiness-design-only.md
PASS

grep -R "Data is not factor" docs decisions
PASS - found in docs/ARCHITECTURE.md, docs/DOMAIN_BOUNDARIES.md, and
decisions/0003-domain-boundary-separation.md.

grep -R "Reference" docs/BACKTEST_TIERS.md decisions/0002-reference-backtest-truth.md
PASS - found in both required files.

grep -R "Fast path" docs/BACKTEST_TIERS.md docs/ARCHITECTURE.md
PASS - found in both required files.

grep -R "No broker" docs decisions README.md || true
PASS - found in docs and decisions.

git ls-files runs
PASS - returned empty.

git ls-files data metadata artifacts
WARN - returned existing tracked README placeholders only:
artifacts/README.md
data/cache/README.md
data/canonical/README.md
data/factors/README.md
data/labels/README.md
data/raw/README.md
metadata/README.md
No ASV1-P02 change touched or staged data, metadata, or artifact payload paths.

find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

grep -R "git add ." docs decisions || true
PASS - occurrences are prohibition statements only.

grep -R "git add -A" docs decisions || true
PASS - occurrences are prohibition statements only.

markdownlint docs decisions || true
NON-BLOCKING - markdownlint unavailable in this environment.

git diff --check
PASS

git diff --name-only -- src tests data metadata artifacts pyproject.toml
PASS - returned empty.

find . -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" -o -name "*.log" \) -print
PASS - returned empty.
```

## Final Staged Set

Files were staged explicitly by path. `git add .`, `git add -A`, and force push
were not used.

```text
git diff --cached --name-only
PASS - staged files:
PROJECT_STATUS.md
README.md
decisions/0001-local-first-stack.md
decisions/0002-reference-backtest-truth.md
decisions/0003-domain-boundary-separation.md
decisions/0004-no-broker-live-in-v1.md
decisions/0005-l2-readiness-design-only.md
docs/ARCHITECTURE.md
docs/ARTIFACT_POLICY.md
docs/BACKTEST_TIERS.md
docs/CLI_COMMANDS_TARGET.md
docs/DOMAIN_BOUNDARIES.md
docs/LOCAL_FIRST_STACK.md
docs/NO_LOOKAHEAD_POLICY.md
docs/PLAN.md
docs/REPRODUCIBILITY_PRINCIPLES.md
docs/RESEARCH_WORKFLOW.md
handoffs/ASV1-P02.md

git diff --cached --name-only | grep '^runs/' || true
PASS - returned empty.

git diff --cached --name-only | grep -E '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.log$)' || true
PASS - returned empty.

git diff --cached --check
PASS
```

## Commit-Eligible Vs Local-Only

Commit-eligible ASV1-P02 files are the docs, decisions, optional README and
PROJECT_STATUS updates, and this handoff. All `runs/**` artifacts remain
local-only and were not staged. Codex did not write a run-local
`runs/<run_id>/phases/ASV1-P02/handoff.md` for this execution.

## Artifact Policy Confirmation

No raw data, canonical data, factor values, label values, generated reports,
heavy artifacts, local SQLite files, DB files, Parquet, Arrow, Feather, logs,
caches, model binaries, secrets, or local environment files were staged or
committed by this phase.

## Scope Confirmation

No source, data, registry, schema, migration, execution, packaging, tests,
hooks, CI, PR, merge, broker, paper trading, live trading, order routing, or
production deployment implementation occurred.

Broker, paper, and live trading remain out of scope. No alpha, tradability,
profitability, robustness, production-readiness, or live-readiness claims were
introduced.

## Known Limitations

- `ACTIVE_CAMPAIGN.md` still points to `ASV1-P01`; it was not touched because it
  is not an allowed ASV1-P02 path.
- No standalone `specs/ASV1-P02/spec.md` file exists in the repo. Execution used
  the generated spec provided to Codex and the matching campaign phase-plan
  section.
- `git ls-files data metadata artifacts` returns existing tracked README
  placeholders from the baseline, not P02 payloads.
- Markdown lint was unavailable and is recorded as non-blocking.
- Claude review, verdict parsing, formal checks recording, semantic done-check,
  PR, CI, merge gate, and merge are Ralph-owned and were not run by Codex.

## Relevant Risks

- R-009 Execution truth ambiguity: mitigated in docs/decision records by Tier 1
  Reference as the single canonical PnL truth and Fast path acceleration only.
- R-014 Alpha/tradability overclaiming: mitigated by explicit no-claim language;
  no unsupported claims were introduced.
- R-017 Test weakening/gaming: mitigated; no tests were added, modified, or
  removed.
- R-023 Cloud/server dependency creep: mitigated by local-first stack docs and
  ADR-0001 exclusions.
- R-040 Event-driven/L2 design mistaken as complete execution: mitigated by
  Tier 3/Tier 4 and L2 design-only statements.

## Review Focus

- Verify the architecture reads as an Alpha Research Platform foundation, not
  merely a backtester.
- Verify domain boundaries are stated as enforceable invariants.
- Verify the local-first stack excludes cloud, paid, and server dependencies in
  v1.
- Verify Reference is the single canonical v1 PnL truth and Fast path is
  acceleration only.
- Verify timestamp semantics and no-lookahead rules are explicit.
- Verify L2 readiness is design-only.
- Verify artifact policy, explicit staging, and `runs/**` local-only handling.
- Verify no broker/live/paper scope, implementation scope, tests, or unsupported
  claims were introduced.
