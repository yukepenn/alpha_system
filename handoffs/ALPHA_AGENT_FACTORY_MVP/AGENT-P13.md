# AGENT-P13 Handoff - Diagnostics Runner Role Contract

## Scope Completed

Added the contracts-only Diagnostics Runner role contract, targeted unit tests,
human role doc, and operating prompt template.

No autonomous agent was instantiated. No runtime diagnostics were run. No
provider, broker, paper, live, order, deployment, PR, merge, review, or verdict
action was performed.

## Staging

Codex staged no files, per executor override.

Ralph explicit staging list:

- `src/alpha_system/agent_factory/roles/diagnostics_runner.py`
- `tests/unit/agent_factory/roles/test_diagnostics_runner.py`
- `docs/agent_factory/roles/diagnostics_runner.md`
- `templates/agent_factory/roles/diagnostics_runner.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P13.md`

Do not stage `runs/**`. Do not stage the run-local handoff copy.

## Validation Results

- `git status --short` - SKIPPED. Executor override explicitly forbids `git status`.
- `python -c "import alpha_system.agent_factory.roles.diagnostics_runner"` - FAILED in the bare shell with `ModuleNotFoundError: No module named 'alpha_system'`; this shell does not have `src/` on `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.diagnostics_runner"` - PASS.
- `python -m pytest tests/unit/agent_factory/roles/test_diagnostics_runner.py -q` - PASS, `10 passed`.
- `python tools/verify.py --smoke` - PASS.
- `test -f docs/agent_factory/roles/diagnostics_runner.md` - PASS.
- `test -f templates/agent_factory/roles/diagnostics_runner.md` - PASS.
- `git ls-files runs` - PASS, empty output.

Supplementary audits:

- `git diff --name-only -- src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py` - SKIPPED. Executor override explicitly forbids `git diff`.
- `rg -n "diagnostics_runner" src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py` - PASS, no matches.
- Provider/file-reader heuristic on `diagnostics_runner.py` - PASS, output: `no direct provider/file readers in diagnostics_runner.py`.

## Artifact Audit

- `git ls-files runs` returned empty.
- Codex performed no staging, so no staged `runs/` path, forbidden data path,
  heavy artifact, DB, cache, or log path was introduced by the executor.
- Ralph should run the authoritative cached/staged artifact audit after explicit
  staging, because Codex was instructed not to run staging or cached diff
  commands.

## Shared Files And README

- `src/alpha_system/agent_factory/roles/__init__.py` was not edited.
- `src/alpha_system/agent_factory/roles/registry.py` was not edited.
- `README.md` was not edited by Codex. Per the AGENT-P13 parallel-safety note,
  the README snapshot is coordinator-applied at serial merge time.

## Caveats

The exact bare import validation command failed only because the executor shell
does not expose the `src/` package root. The same import passed with
`PYTHONPATH=src`, and the targeted pytest plus smoke verifier passed.

YELLOW review remains required by Ralph/Claude before merge. Codex did not run
reviewer, create `review.md`, create `verdict.json`, create a PR, merge, mark
the phase PASS, stage, commit, or push.
