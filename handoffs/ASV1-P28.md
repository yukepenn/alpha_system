# ASV1-P28 Handoff - Researcher and AI Agent Onboarding

## Scope Completed

Created the documentation-only onboarding layer for human researchers and
Workflow 2 AI Agents. No platform behavior, source code, tests, generated data,
registry schema, CLI implementation, or artifact generation was changed.

## Docs Changed

- `docs/ONBOARDING.md` - local-first quickstart, WSL2 path policy, editable
  install, CLI smoke checks, first safe steps, artifact discipline.
- `docs/RESEARCHER_GUIDE.md` - human research flow from data validation through
  review bundles, with factor, label, diagnostics, strategy, management,
  portfolio, backtest, grid, ML, and registry boundaries.
- `docs/AI_AGENT_GUIDE.md` - Workflow 2 role boundaries, state machine,
  STOP/resume, handoff rules, repair loop, explicit staging, artifact policy,
  blocked escalation, and failure visibility.
- `docs/CLI_REFERENCE.md` - concise reference for the eleven required
  `alpha ...` commands, with purpose, inputs, outputs, local-only restrictions,
  and `--help` as the exact-flag source of truth.
- `docs/EXAMPLE_WORKFLOWS.md` - fixture-based local narrative flows from data
  to factor diagnostics, grids, reference backtest, ML, registry inspection, and
  review bundle.
- `docs/TROUBLESHOOTING.md` - common WSL2/path, CLI, staging, dirty tree, STOP,
  hidden-failure, and overclaiming issues.
- `docs/RESEARCH_INTERPRETATION_POLICY.md` - prohibited unsupported claim
  vocabulary, recommendation-vs-approval, fixtures-not-market-evidence policy,
  evidence-layer boundaries, and L2/event-driven scope boundary.
- `AGENTS.md` - onboarding cross-references only.
- `CLAUDE.md` - onboarding cross-references only.
- `README.md` - compact snapshot through ASV1-P28 with ASV1-P29 named next and
  unchanged safety boundaries.
- `docs/PLAN.md` and `docs/ARCHITECTURE.md` - optional index link additions
  only.

## Coverage Checklist

- WSL2 setup and repo path policy: covered in `docs/ONBOARDING.md` and
  `docs/TROUBLESHOOTING.md`.
- Local-first stack: covered in `docs/ONBOARDING.md`.
- Workflow 2 operation and Ralph/Codex/Claude role boundaries: covered in
  `docs/AI_AGENT_GUIDE.md`.
- Full required CLI overview: covered in `docs/CLI_REFERENCE.md`.
- Artifact policy, explicit staging, no `git add .`, no `git add -A`, and no
  raw/heavy/local-DB commits: covered in onboarding, AI Agent guide,
  troubleshooting, and CLI reference.
- No-lookahead policy and label/factor separation: covered in
  `docs/RESEARCHER_GUIDE.md`, `docs/EXAMPLE_WORKFLOWS.md`, and interpretation
  policy.
- Factor lifecycle: covered in `docs/RESEARCHER_GUIDE.md`.
- Strategy vs management vs portfolio boundaries: covered in
  `docs/RESEARCHER_GUIDE.md`.
- Reference truth as single PnL truth and fast-path parity as acceleration
  only: covered in researcher guide, CLI reference, example workflows, and
  interpretation policy.
- Grid discipline and bounds: covered in researcher guide and example
  workflows.
- ML leakage policy: covered in researcher guide, CLI reference, and example
  workflows.
- Registry inspection: covered in onboarding, researcher guide, CLI reference,
  and example workflows.
- Review bundle generation and audit role: covered in researcher guide, CLI
  reference, example workflows, and interpretation policy.
- Report interpretation without overclaiming: covered in
  `docs/RESEARCH_INTERPRETATION_POLICY.md`.
- Handoff creation, blocked escalation, and hidden-failure prevention: covered
  in `docs/AI_AGENT_GUIDE.md` and `docs/TROUBLESHOOTING.md`.
- Broker/live/paper trading out of scope: restated across new docs and README.
- Fixtures are correctness validation, not market evidence: restated in CLI
  reference, example workflows, and interpretation policy.

## Files Changed And Explicit Staging Set

The explicit staging set for this phase is:

- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `handoffs/ASV1-P28.md`

No `runs/`, `src/`, `tests/`, `data/`, `metadata/*.db|*.sqlite`,
`artifacts/`, generated data, generated report bundle, log, cache, Parquet,
Arrow, or Feather path is in the staging set.

## Validation Results

Required validation commands were run after explicit staging of the allowed
paths. Results:

- `test -f docs/ONBOARDING.md` - passed.
- `test -f docs/RESEARCHER_GUIDE.md` - passed.
- `test -f docs/AI_AGENT_GUIDE.md` - passed.
- `test -f docs/CLI_REFERENCE.md` - passed.
- `test -f docs/EXAMPLE_WORKFLOWS.md` - passed.
- `test -f docs/TROUBLESHOOTING.md` - passed.
- `test -f docs/RESEARCH_INTERPRETATION_POLICY.md` - passed.
- `test -f handoffs/ASV1-P28.md` - passed.
- `grep -R "broker/live trading" docs AGENTS.md CLAUDE.md README.md || true`
  - exit 0; hits are out-of-scope/safety statements in the new docs and CLI
    reference, not operating instructions.
- `grep -R "git add ." docs AGENTS.md CLAUDE.md README.md || true` - exit 0;
  inspected hits are forbidden examples or existing policy text only.
- `grep -R "git add -A" docs AGENTS.md CLAUDE.md README.md || true` - exit 0;
  inspected hits are forbidden examples or existing policy text only.
- `git status --short` - exit 0; staged paths were:

```text
M  AGENTS.md
M  CLAUDE.md
M  README.md
A  docs/AI_AGENT_GUIDE.md
M  docs/ARCHITECTURE.md
A  docs/CLI_REFERENCE.md
A  docs/EXAMPLE_WORKFLOWS.md
A  docs/ONBOARDING.md
M  docs/PLAN.md
A  docs/RESEARCHER_GUIDE.md
A  docs/RESEARCH_INTERPRETATION_POLICY.md
A  docs/TROUBLESHOOTING.md
A  handoffs/ASV1-P28.md
```

- `git diff --cached --name-only` - exit 0; output:

```text
AGENTS.md
CLAUDE.md
README.md
docs/AI_AGENT_GUIDE.md
docs/ARCHITECTURE.md
docs/CLI_REFERENCE.md
docs/EXAMPLE_WORKFLOWS.md
docs/ONBOARDING.md
docs/PLAN.md
docs/RESEARCHER_GUIDE.md
docs/RESEARCH_INTERPRETATION_POLICY.md
docs/TROUBLESHOOTING.md
handoffs/ASV1-P28.md
```

- `git ls-files runs` - exit 0; no output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - exit 0;
  no output.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true`
  - exit 0; no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - exit
  0; no output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - exit 0;
  no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print`
  - exit 0; no output.
- `markdownlint docs README.md AGENTS.md CLAUDE.md || true` - exit 0 because
  of the non-blocking guard; shell output was
  `/bin/bash: line 1: markdownlint: command not found`.
- Claim-language spot check across changed docs found only prohibited
  vocabulary lists, negative scope statements, lifecycle names, or
  recommendation-vs-approval policy. No affirmative alpha, profitability,
  robustness, tradability, broker/live/paper, order-routing, deployment, or
  approval claim was introduced.

Additional non-required check:

- `git diff --cached --check` - exit 0 after EOF whitespace cleanup on newly
  staged docs.

## Artifact Policy Confirmation

Commit-eligible changes are documentation and `handoffs/ASV1-P28.md` only.
`runs/**` remains local-only and is not staged. No run-local `handoff.md`,
`review.md`, `verdict.json`, checks, or repair artifact was created for commit.
No data, generated artifact, DB, SQLite, Parquet, Arrow, Feather, log, cache, or
model file is staged or prepared for commit.

Explicit staging was used by path. The forbidden examples `git add .` and
`git add -A` were not used. No force push was used.

## Scope And Safety Confirmation

- No source behavior changes occurred.
- No test files were added, removed, modified, weakened, or skipped.
- No broker/live trading, paper trading, order routing, deployment, or
  production execution scope was introduced.
- No alpha, profitability, robustness, or tradability claim was introduced.
- README snapshot is factual and compact, names progress through ASV1-P28,
  names ASV1-P29 as next, lists the seven new docs and cross-reference updates,
  and restates unchanged safety boundaries.

## Review

Review was skipped because ASV1-P28 is GREEN, `review_required: false`, and the
changes are documentation-only. Ralph remains responsible for recording the
formal review skip reason, handoff validation, artifact policy gate, and
semantic done-check.

## Relevant Risks

- R-014 overclaiming: mitigated with the interpretation policy and repeated
  no-claims language.
- R-016 hidden failed runs: mitigated with AI Agent and troubleshooting guidance
  requiring failed runs, rejected configs, warnings, and unavailable checks to
  remain visible.
- R-020 path contamination: mitigated with WSL2 and forbidden synced path
  guidance.
- R-040 L2/event-driven completeness: mitigated by stating L2/event-driven
  scope is design-readiness or fixture-only where documented and not complete
  replay/queue/passive-fill/live behavior.

## Known Limitations

- This phase adds operating documentation only; it does not validate end-to-end
  v0.1 behavior or close the campaign. ASV1-P29 owns end-to-end validation and
  campaign closeout.
- Exact CLI flags are intentionally not duplicated beyond concise summaries;
  command `--help` remains the source of truth.
- Generated examples are narrative and fixture-oriented; they do not include or
  authorize real data, local DB commits, generated report commits, broker
  operations, paper trading, live trading, order routing, or deployment.
- `.git` intermittently rejected index-lock creation during EOF cleanup, but a
  later explicit re-stage succeeded and the final staged diff check passed.
