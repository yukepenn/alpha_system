# ARGOV-P16 Handoff - Governance CLI and Validation Tools

## Summary

Implemented the `alpha governance` CLI command group and wired it into the
existing argparse entry point. The CLI is a deterministic JSON-file wrapper over
the existing governance validators, `GovernanceRegistry`, and promotion gate. It
does not introduce new governance objects, lifecycle states, gate semantics, or
market behavior.

Added commands:

- `validate-spec`: loads an `AlphaSpec` and referenced `HypothesisCard`, validates
  both objects, then routes the pair through `DRAFT -> REGISTERED` via
  `validate_governance_transition`.
- `register-trial`: validates a `TrialLedgerRecord` and persists it under
  `DIAGNOSTICS_RUN`; failed and abandoned records are preserved with their
  failure and variant metadata because no filtering or overwrite path is added.
- `build-evidence`: validates an `EvidenceBundle`, resolves its `StudySpec` and
  referenced trial records from the registry, validates `DIAGNOSTICS_RUN ->
  EVIDENCE_READY`, and persists under `EVIDENCE_READY`.
- `review`: validates a `ReviewerVerdict` and persists under `REVIEWED` only
  through the registry's required `PromotionGateContext`; missing independence
  statements, reviewer identity equal to implementer identity, and reviewer role
  equal to implementer role fail closed.
- `promote`: validates a `PromotionDecision`, resolves the referenced reviewer
  verdict, and persists only through `GovernanceRegistry.save(...,
  gate_context=...)`, which revalidates `REVIEWED -> decision.next_state` through
  the promotion gate.

For `CANDIDATE` and `VALIDATED`, `promote` resolves the referenced evidence
bundle and supplies all registry-visible `DIAGNOSTICS_RUN` `TrialLedgerRecord`
entries matching the evidence bundle's alpha/study pair to the existing gate.
This preserves the failed-run omission block at the CLI boundary instead of
letting the command pass only the trial refs in the decision payload.

No force-promote, self-approve, ledger edit, ledger overwrite, gate skip, direct
state mutation, prohibited MVP state, broker, live, paper, order-routing,
production deployment, real-data ingestion, alpha search, factor computation, or
label materialization path was added.

## Validation Tool

Added `tools/governance/validate_objects.py`, a local batch validator that imports
the same CLI validation helpers. It supports:

- `--object KIND:PATH` for canonical object validation through the same object
  validators used by the CLI.
- `--alpha-spec PATH --hypothesis-card PATH` for the same `DRAFT -> REGISTERED`
  pre-registration validation used by `alpha governance validate-spec`.

The helper is read-only and writes only JSON console output.

## Documentation And README

Added `docs/governance/CLI.md` documenting command syntax, exit codes, gate
enforcement, registry/artifact policy, local-first posture, and no-claims
boundary.

Updated `README.md` per the snapshot policy: current progress is now P16, next
phase is `ARGOV-P17 - Unsupported-Claim Guard and Governance Report Templates`,
new durable CLI/tool/docs paths are listed, and safety boundaries remain
unchanged.

## Staged Files

Exact files staged explicitly:

```text
README.md
docs/governance/CLI.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P16.md
src/alpha_system/cli/governance.py
src/alpha_system/cli/main.py
tests/integration/governance/test_cli_smoke.py
tests/unit/governance/test_cli.py
tools/governance/validate_objects.py
```

No `runs/**` path is included.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed ARGOV-P16 paths:

```text
 M README.md
 M src/alpha_system/cli/main.py
?? docs/governance/CLI.md
?? src/alpha_system/cli/governance.py
?? tests/integration/governance/test_cli_smoke.py
?? tests/unit/governance/test_cli.py
?? tools/governance/
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance -q` - passed:

```text
475 passed in 2.10s
```

- `python -m pytest tests/integration/governance -q` - passed:

```text
6 passed in 2.78s
```

- `test -f docs/governance/CLI.md` - passed with exit 0 and no output.

- `git ls-files runs` - passed with empty output.

Supporting safe checks:

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - passed
  with empty output.

- `git diff --name-only --cached` - passed after explicit staging with exactly
  the staged set listed above.

Additional local validation:

- `python -m ruff format src/alpha_system/cli/governance.py src/alpha_system/cli/main.py tools/governance/validate_objects.py tests/unit/governance/test_cli.py tests/integration/governance/test_cli_smoke.py`
  - passed; final run reported:

```text
5 files left unchanged
```

- `python -m ruff check src/alpha_system/cli/governance.py src/alpha_system/cli/main.py tools/governance/validate_objects.py tests/unit/governance/test_cli.py tests/integration/governance/test_cli_smoke.py`
  - passed:

```text
All checks passed!
```

- `python -m pytest tests/unit/governance/test_cli.py -q` - passed:

```text
9 passed in 1.52s
```

- `python -m pytest tests/integration/governance/test_cli_smoke.py -q` - passed:

```text
2 passed in 1.60s
```

- `python tools/governance/validate_objects.py --object AlphaSpec:tests/fixtures/governance/alpha_spec_valid.json`
  - passed with exit 0 and JSON `status: ok`.

- `git diff --check` - passed with exit 0 and no output.

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json` were
not run or created by Codex because the executor prompt reserves review and
verdict handling for Ralph and the independent reviewer.

## Test Coverage

Added `tests/unit/governance/test_cli.py` covering:

- linked `validate-spec` success and mismatched hypothesis rejection;
- failed `register-trial` persistence with variant metadata preserved;
- `build-evidence` fail-closed behavior for missing manifest and missing
  registry refs;
- `review` self-approval rejection;
- `promote` failed-run omission rejection with complete registry-visible trial
  context supplied to the gate;
- `promote` prohibited MVP state rejection before persistence;
- validation helper reuse of the same pre-registration gate.

Added `tests/integration/governance/test_cli_smoke.py` covering subprocess
module-entry CLI wiring for the happy path from validation through candidate
promotion against a temp registry, plus self-review rejection.

## Artifact Policy

- `git ls-files runs` returned empty output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` returned
  empty output.
- No SQLite, DB, DB journal, WAL, raw/canonical/factor/label/cache data,
  Parquet, Arrow, Feather, log, cache, model binary, generated report bundle,
  credential, or heavy artifact is staged.
- No `runs/**` path is staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair artifact was created or staged by Codex.

## Staging Discipline

Explicit staging only. `git add .`, `git add -A`, force push, PR creation, merge,
reviewer invocation, and destructive cleanup were not used. No commit was created
by Codex in this executor step.

Post-staging validation:

- `git diff --cached --name-only` - passed after explicit staging with exactly
  this curated set:

```text
README.md
docs/governance/CLI.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P16.md
src/alpha_system/cli/governance.py
src/alpha_system/cli/main.py
tests/integration/governance/test_cli_smoke.py
tests/unit/governance/test_cli.py
tools/governance/validate_objects.py
```

- `git diff --cached --check` - passed with exit 0 and no output.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. `rg`
  returned exit 1 because no staged path matched `runs/`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/|^artifacts/|\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|pkl|joblib|onnx|npy|log)$)'`
  - passed with no matches. `rg` returned exit 1 because no staged path matched
  forbidden artifact patterns.

## Scope Confirmation

No broker, live, paper, order-routing, production deployment, real-data
ingestion, alpha search, factor computation, label materialization, strategy
optimization, portfolio allocation, live approval, capital allocation, or
production-readiness scope was introduced.

No alpha, profitability, tradability, or production-readiness claim was
introduced. The CLI and helper record and validate governance metadata only.
