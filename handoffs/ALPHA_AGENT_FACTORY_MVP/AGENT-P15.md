# AGENT-P15 Handoff - Librarian and Memory Update Role Contract

## Scope Completed

Implemented the contracts-only Librarian role contract for
`ALPHA_AGENT_FACTORY_MVP/AGENT-P15`.

The role self-registers through the discovery registry at import time and does
not edit `src/alpha_system/agent_factory/roles/__init__.py` or
`src/alpha_system/agent_factory/roles/registry.py`. It derives callable tools
from the `librarian` permission-matrix entry, declares the
`librarian_needs_reviewer_verdict_ref` invariant, references existing
governance and queue primitives, and forbids promotion, registry writes without
a verdict, direct registry writes, raw/provider access, value materialization,
and alpha/tradability/profitability claims.

## Staging

Codex did not stage files. Per executor instructions, all changes were left
unstaged for Ralph/the driver.

Explicit file list for Ralph to stage:

- `src/alpha_system/agent_factory/roles/librarian.py`
- `tests/unit/agent_factory/roles/test_librarian.py`
- `docs/agent_factory/roles/librarian.md`
- `templates/agent_factory/roles/librarian.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P15.md`

No review artifacts were created by Codex. The executor instructions explicitly
forbid calling Claude, running reviewer, creating `review.md`, creating
`verdict.json`, marking the phase PASS, creating a PR, merging, staging, or
committing. Ralph owns review artifact generation and any commit-eligible review
promotion under `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P15/**`.

## Validation

- `git status --short`
  - Result: SKIPPED.
  - Reason: executor instructions explicitly forbid `git status`.

- `python -c "import alpha_system.agent_factory.roles.librarian"`
  - Result: FAIL, exit 1.
  - Output: `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: plain `python` in this shell does not include `src/` on `sys.path`.

- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.librarian"`
  - Result: PASS, exit 0.
  - Purpose: supplemental confirmation that the role module imports and
    self-registers when the repo source path is present.

- `python tools/verify.py --smoke`
  - Result: PASS, exit 0.

- `python -m pytest tests/unit/agent_factory/roles/test_librarian.py -q`
  - Result: PASS, exit 0.
  - Output: `10 passed in 0.05s`.

- `test -f docs/agent_factory/roles/librarian.md`
  - Result: PASS, exit 0.

- `test -f templates/agent_factory/roles/librarian.md`
  - Result: PASS, exit 0.

- `git ls-files runs`
  - Result: PASS, exit 0 with empty output.

- `python -m ruff check src/alpha_system/agent_factory/roles/librarian.py tests/unit/agent_factory/roles/test_librarian.py`
  - Result: PASS, exit 0.
  - Output: `All checks passed!`.

Broader merge-time checks were not run by Codex:

- `python tools/verify.py --all`
- `python tools/hooks/canary_runner.py`

Reason: the generated spec requested the narrow phase checks first, no shared
role behavior was intentionally touched, and the executor instructions assign
validation orchestration, review, verdict parsing, PR, CI, and merge gates to
Ralph.

## Artifact Audit

- `git ls-files runs` returned empty output.
- Codex did not create or edit run-local `handoff.md`, `review.md`,
  `verdict.json`, or repair-attempt artifacts.
- Codex did not run `git add`, `git commit`, `git push`, `git status`, or
  `git diff`.
- Because `git status` and `git diff --cached` were forbidden, Codex did not
  inspect the staged set. No staging commands were run by Codex.

## Shared Role Files

Confirmed by implementation and unit tests:

- `src/alpha_system/agent_factory/roles/__init__.py` was not edited.
- `src/alpha_system/agent_factory/roles/registry.py` was not edited.
- `alpha_system.agent_factory.roles.librarian` self-registers additively through
  the existing discovery registry.

## README Snapshot

`README.md` was updated with a compact AGENT-P15 campaign snapshot. The update
names the Librarian role contract, doc, and prompt template; points next work
toward AGENT-P16 separation-of-duties enforcement; and adds no run-local
details, alpha/profitability/tradability claims, broker/live/paper behavior,
deployment behavior, or promotion language.

## Caveats And Deferrals

- Fresh Claude review was not run and review artifacts were not created by
  Codex, per executor safety instructions. Ralph must route the required
  independent YELLOW-lane review.
- The exact plain import command failed because this shell lacks `src/` on
  `sys.path`; pytest and the supplemental `PYTHONPATH=src` import both confirm
  the Librarian module imports and registers under the repo source path.
- No docs index file was edited because it was not in this phase's generated
  allowed paths.
