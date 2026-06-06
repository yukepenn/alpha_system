# AGENT-P09 Handoff - AlphaSpec Critic Role Contract

## Scope Completed

Created the contracts-only AlphaSpec Critic role declaration, phase-scoped unit
test, role documentation, and operating prompt template. The role self-registers
on import through `alpha_system.agent_factory.roles.registry.register(...)` and
does not edit `roles/__init__.py`, `roles/registry.py`, sibling role modules,
runtime, governance, research, data, or broker-related packages.

No autonomous agent was instantiated. No AlphaSpec was drafted or edited. No
runtime diagnostics, promotion, paper/live/broker operation, deployment, PR,
merge, Claude call, reviewer run, `review.md`, or `verdict.json` was created by
the executor.

## Files For Ralph To Stage

- `src/alpha_system/agent_factory/roles/alpha_spec_critic.py`
- `tests/unit/agent_factory/roles/test_alpha_spec_critic.py`
- `docs/agent_factory/roles/alpha_spec_critic.md`
- `templates/agent_factory/roles/alpha_spec_critic.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P09.md`

The spec also allows `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P09/**`, but the
executor did not create review artifacts because the executor prompt explicitly
forbade creating `review.md`, `verdict.json`, or running the reviewer.

## Git Visibility

- `git status --short`: skipped. The executor prompt explicitly forbade running
  `git status`.
- `git diff --name-only -- src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py`:
  skipped. The executor prompt explicitly forbade running `git diff`.
- Staging: no `git add`, `git commit`, or `git push` was run by the executor.
- Staged-set audit: not independently inspected by Codex because the required
  cached diff command is a `git diff` command and was prohibited. Ralph should
  perform the authoritative staged audit before commit.

## Validation Results

- STOP check: no run-level or phase-level STOP file was present when execution
  began.
- `python -c "import alpha_system.agent_factory.roles.alpha_spec_critic"`:
  failed in the bare shell with `ModuleNotFoundError: No module named
  'alpha_system'`. This workspace uses a `src/` layout and pytest config sets
  `pythonpath = ["src"]`; the bare Python command does not load that config.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.alpha_spec_critic"`:
  passed.
- `python -c "import alpha_system.agent_factory.roles.alpha_spec_critic as m; from alpha_system.agent_factory.roles import registry; r = registry.get('alpha_spec_critic'); print('registered:', r.role_id)"`:
  failed in the bare shell with `ModuleNotFoundError: No module named
  'alpha_system'` for the same source-layout reason.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.alpha_spec_critic as m; from alpha_system.agent_factory.roles import registry; r = registry.get('alpha_spec_critic'); print('registered:', r.role_id)"`:
  passed; output was `registered: alpha_spec_critic`.
- `python tools/verify.py --smoke`: passed.
- `python -m pytest tests/unit/agent_factory/roles/test_alpha_spec_critic.py -q`:
  passed, `7 passed in 0.02s`.
- `python -m pytest tests/unit/agent_factory/roles -q`: passed,
  `33 passed in 0.02s`.
- `test -f docs/agent_factory/roles/alpha_spec_critic.md`: passed.
- `grep -REn "\.dbn|\.zst|read_parquet|to_parquet|pyarrow|databento|ib_insync|ibapi|\.feather|\.arrow" src/alpha_system/agent_factory/roles/alpha_spec_critic.py || echo "no direct provider/file readers in alpha_spec_critic.py"`:
  passed; output was `no direct provider/file readers in alpha_spec_critic.py`.
- `python -m ruff check src/alpha_system/agent_factory/roles/alpha_spec_critic.py tests/unit/agent_factory/roles/test_alpha_spec_critic.py`:
  initially failed on one long line and import ordering; both were fixed.
- `python -m ruff check src/alpha_system/agent_factory/roles/alpha_spec_critic.py tests/unit/agent_factory/roles/test_alpha_spec_critic.py`:
  passed after the fix; output was `All checks passed!`.
- `rg -n "ALPHA_VALIDATED|FACTOR_PROMOTED|CANDIDATE_PROMOTED|read_parquet|to_parquet|pyarrow|databento|ib_insync|ibapi|\.dbn|\.zst|\.feather|\.arrow" src/alpha_system/agent_factory/roles/alpha_spec_critic.py tests/unit/agent_factory/roles/test_alpha_spec_critic.py docs/agent_factory/roles/alpha_spec_critic.md templates/agent_factory/roles/alpha_spec_critic.md`:
  no matches.
- `git ls-files runs`: passed with empty output.

## Skipped Checks And Reasons

- `git status --short`: skipped because the executor prompt explicitly forbade
  `git status`.
- `git diff --name-only -- src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py`:
  skipped because the executor prompt explicitly forbade `git diff`.
- `python tools/verify.py --all`: not run. The spec requested broadening only if
  shared role behavior appeared affected; the phase-scoped and roles-slice tests
  passed. Also, `--all` includes artifact checks that run `git diff --cached`,
  which conflicts with the executor prompt's `git diff` prohibition.
- Review generation: skipped because the executor prompt explicitly forbade
  calling Claude, running reviewer, creating `review.md`, or creating
  `verdict.json`.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No files under `runs/**` were written by the executor.
- The run-local phase directory was not present in this worktree, and no
  run-local handoff was created.
- No review artifacts were created by the executor.
- No staging was performed by the executor; Ralph remains responsible for
  explicit staging and the authoritative no-forbidden-path staged audit.

## Caveats

- The bare `python -c` import commands in the generated spec fail in this shell
  unless `PYTHONPATH=src` is supplied. Pytest succeeds because `pyproject.toml`
  configures `pythonpath = ["src"]`.
- `README.md` was not edited because AGENT-P09 is a parallel-safe role-wave
  phase and the generated spec reconciles README snapshots as coordinator-owned.
