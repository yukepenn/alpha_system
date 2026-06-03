# ARGOV-P03 Handoff — AlphaSpec Contract and No-Code Gate

## Summary

Implemented the `AlphaSpec` governance contract in
`alpha_system.governance.alpha_spec` using the ARGOV-P02 primitives for deterministic
IDs, canonical serialization, and fail-closed validation.

The contract requires all campaign-declared `AlphaSpec` fields, validates
`alpha_spec_id` as a deterministic content-bound `aspec_...` ID, validates
`hypothesis_id` and `label_references` as well-formed governance references, rejects
missing, null, empty, malformed, unknown, non-serializable, or vague substantive fields,
and round-trips through canonical JSON without defaults, coercion, or dropped fields.

The no-code gate is `validate_no_code_gate(...)` / `assert_implementation_allowed(...)`.
It is a pure precondition check for `REGISTERED -> IMPLEMENTATION_ALLOWED`: missing or
invalid `AlphaSpec` blocks the transition; a valid `AlphaSpec` returns the validated
record. It executes no implementation, reads no data, computes no factors, grants no
candidate status, and creates no factor-library entry.

Docs and template deliverables were added:

- `docs/governance/ALPHA_SPEC.md`
- `templates/governance/alpha_spec.template.yaml`

The README snapshot was updated in place to reflect ARGOV-P03 as active/just-completed,
ARGOV-P04 as next, the new module/docs/template, and unchanged safety boundaries. It
contains no run details, local artifact paths, PASS verdict text, or prohibited claims.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/ALPHA_SPEC.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P03.md`
- `src/alpha_system/governance/alpha_spec.py`
- `templates/governance/alpha_spec.template.yaml`
- `tests/fixtures/governance/alpha_spec_valid.json`
- `tests/unit/governance/test_alpha_spec.py`
- `tests/unit/governance/test_no_code_gate.py`

No `runs/**` path is staged.

## Validation Results

- `git status --short` — passed before handoff/staging. Output showed only ARGOV-P03
  allowed paths:

```text
 M README.md
 M src/alpha_system/governance/alpha_spec.py
?? docs/governance/ALPHA_SPEC.md
?? templates/governance/alpha_spec.template.yaml
?? tests/fixtures/governance/
?? tests/unit/governance/test_alpha_spec.py
?? tests/unit/governance/test_no_code_gate.py
```

- `python -m pytest tests/unit/governance/test_alpha_spec.py tests/unit/governance/test_no_code_gate.py -q` — passed:

```text
............                                                             [100%]
12 passed in 0.01s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
.......................................                                  [100%]
39 passed in 0.04s
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.
- `test -f src/alpha_system/governance/alpha_spec.py` — passed with exit 0.
- `test -f docs/governance/ALPHA_SPEC.md` — passed with exit 0.
- `test -f templates/governance/alpha_spec.template.yaml` — passed with exit 0.
- `python -c "import alpha_system.governance.alpha_spec"` — failed in the current
  uninstalled shell:

```text
ModuleNotFoundError: No module named 'alpha_system'
```

  Reason: bare `python -c` does not include `src` on `sys.path`, and this environment has
  no editable or wheel install for `alpha-system`. Diagnostic import
  `PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"` passed with exit
  0 and no output, confirming the module itself imports when the standard source path is
  present.

- `git ls-files runs` — passed with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — passed with empty
  output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — passed with empty
  output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — passed with empty
  output.

Skipped checks: none.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit staging.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB journal, WAL,
  Parquet, Arrow, Feather, log, cache, model binary, heavy artifact, or run artifact is
  staged.
- The run-local handoff under `runs/<run_id>/phases/ARGOV-P03/handoff.md` is local-only
  and not staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or `repair_attempts/` artifact
  was created or staged.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No broker, live, paper, order-routing, production-deployment, real-data-ingestion,
  alpha-search, factor-computation, diagnostics, backtest, registry/persistence, CLI,
  reviewer-verdict, promotion, or report-builder scope was introduced.
- `hypothesis_id` and `label_references` are validated only as well-formed references;
  cross-object resolution is left to later phases.
- No tests were weakened, skipped, or relaxed.
- ARGOV-P02 primitives were reused and not modified.
- No alpha, profitability, tradability, paper-readiness, live-readiness, broker-readiness,
  capital-allocation, production-readiness, deployment-readiness, candidate-status, or
  factor-library-entry claim was introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created. Ralph
owns validation orchestration, independent review routing, verdict parsing, PR creation,
CI, merge gates, semantic done-checks, and phase PASS marking.
