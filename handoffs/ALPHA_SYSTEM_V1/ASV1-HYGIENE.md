# ASV1-HYGIENE Handoff

Result: `PASS_WITH_WARNINGS`

## Scope

ASV1_RELEASE_HYGIENE is post-closeout release hygiene only. No real data, broker,
paper/live, order-routing, deployment, factor/strategy/ML extension, or market
claim is included. Reference-engine behavior was preserved; new tests lock
existing conservative semantics.

## Changes

- Replaced `CHANGELOG.md` and `PROGRESS.md` scaffold text with current
  post-closeout status language and no-claims warnings.
- Appended a small current-status block to `PROJECT_STATUS.md`.
- Added `ruff>=0.8` to dev dependencies and appended ruff configuration to
  `pyproject.toml`.
- Made `tools/verify.py` lint and typecheck gates real, kept lint standalone,
  added explicit run-local tracked-path checks, and added a custom Git
  environment guard.
- Bumped the four Frontier workflow Python versions from 3.11 to 3.12.
- Added verifier and artifact-guard tests under `tests/tools/`.
- Added same-fill-bar stop/target golden tests for target-only and stop-only
  reference-engine behavior.
- Added concise same-fill-bar risk-management clarifications to
  `docs/NO_LOOKAHEAD_POLICY.md` and `docs/BACKTEST_TIERS.md`.

## Validation

- `PYTHONPATH=src python -m pytest -q`
  - Initial attempt: FAIL, `1 failed, 831 passed`.
  - Cause: ignored local file `runs/asv1-hygiene-local/codex_run.log` was present
    and tripped the existing repository-wide `.log` artifact-policy test.
  - Action: removed that ignored run-local log only; no `runs/**` path is tracked
    or staged.
  - Rerun: PASS, `832 passed in 15.57s`.
- `python tools/verify.py --all`
  - PASS, `832 passed in 15.25s`.
  - Output included:
    - `+ /usr/bin/python -m compileall -q src tests tools`
    - `+ /usr/bin/python -m pytest`
- `python tools/verify.py --typecheck`
  - PASS.
  - Output: `+ /usr/bin/python -m compileall -q src tests tools`
- `python -m compileall -q src tests tools`
  - PASS, no output.
- `python tools/hooks/canary_runner.py`
  - PASS.
  - Output: all 12 Frontier canaries passed.
- `git ls-files runs .frontier/upgrade_reports`
  - PASS, no output.
- `git status --short`
  - Final status is recorded below after this handoff file exists.

## Final Git Status

`git status --short`:

```text
 M .github/workflows/frontier-automerge.yml
 M .github/workflows/frontier-canaries.yml
 M .github/workflows/frontier-ci.yml
 M .github/workflows/frontier-nightly-audit.yml
 M CHANGELOG.md
 M PROGRESS.md
 M PROJECT_STATUS.md
 M docs/BACKTEST_TIERS.md
 M docs/NO_LOOKAHEAD_POLICY.md
 M frontier.yaml
 M pyproject.toml
 M tools/frontier/provider_config.py
 M tools/frontier/ralph_driver.py
 M tools/verify.py
?? handoffs/ASV1-HYGIENE.md
?? tests/tools/
?? tests/unit/test_same_bar_stop_target_policy.py
```

Untracked `tests/tools/` contains:

```text
tests/tools/test_artifact_guard.py
tests/tools/test_verify.py
```

## Warnings

- Validation is fixture-only correctness validation and is not market evidence.
- No alpha, profitability, robustness, tradability, paper/live, broker,
  order-routing, or deployment claim is made.
- Formal validation recording, semantic done-check, PR, CI, merge gate, and final
  human/Claude/Ralph review remain outside Codex execution.
- Full-repo ruff lint has an existing backlog and is intentionally not wired
  into `--all` or `--ci`; lint is a real standalone gate.
- Existing unrelated modifications to `frontier.yaml`,
  `tools/frontier/provider_config.py`, and `tools/frontier/ralph_driver.py`
  were present before this pass and were not edited by Codex.
