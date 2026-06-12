---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P041500_CI_PARITY_GATE
lane: yellow
status: in_progress
---

# P041500_CI_PARITY_GATE: CI failures must happen locally, before the PR exists

## Purpose

Every CI failure in the 2026-06-11/12 ledger (RIGOR-P01/P04/P05/P06 + the
P022000 near-miss) was real, deterministic, and caused by ONE mechanism:
phase-local checks run a narrow subset (e.g. `pytest tests/unit/governance
tests/unit/discovery_rigor_floor -q`) while CI `validate` runs bare
`python -m pytest` over the whole tree (.github/workflows/frontier-ci.yml,
"Python tests" step) in an environment with ONLY `pytest pyyaml jinja2`
installed. Consequences: (a) any phase touching a contract consumed by
distant tests fails only at CI_WAIT — costing a ~15-25 min self-repair cycle
per occurrence; (b) the environments disagree in both directions
(polars/duckdb tests run locally but skip on CI; local-data tests would be
red on CI). Fix the class at the root.

## Scope (in-bounds)

1. **CI-parity venv + recipe**: `just ci-parity` — bootstraps (idempotent)
   `~/.venvs/alpha_system_ci` containing exactly CI's deps (pytest, pyyaml,
   jinja2 — read the workflow file and mirror it; pin a requirements file
   under tools/frontier/ or configs/ so workflow drift is detectable), then
   runs `python -m pytest` from the repo/worktree root exactly as CI does.
   Also `just ci-parity-fast` variant accepting extra pytest args.
2. **Workflow-drift test**: a unit test asserting the pinned parity deps ==
   the deps installed in .github/workflows/frontier-ci.yml (parse the
   workflow YAML) — when CI's environment changes, the parity venv pin must
   change in the same commit.
3. **Driver integration (surgical, ralph_driver.py)**: for YELLOW/RED lanes,
   CHECKS_RUN additionally executes the ci-parity command in the phase
   worktree BEFORE handoff/review; failure routes through the EXISTING
   bounded checks-repair loop (NOT a new mechanism). Env escape
   `FRONTIER_SKIP_CI_PARITY=1` for emergencies, logged loudly as an event
   when used. Green lane unchanged (cheap phases stay cheap).
4. **Sanctioned local-data skip idiom**: a tiny helper (e.g.
   tests/_helpers/local_data.py or conftest fixture) exposing
   `skip_unless_local_registry(path_resolver)` that issues a LOUD
   `pytest.skip` with a standard message. Amend
   tools/hooks/test_tamper_guard.py to ALLOW exactly this helper's
   invocation pattern (e.g. permit `local_data_skip(` token while still
   forbidding raw `pytest.skip(`/`@pytest.mark.skip`) — the guard must keep
   failing on ad-hoc skips; add a guard self-test for both directions.
   Migrate the one existing authorized skip
   (tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py)
   to the idiom so FRONTIER_ALLOWED_TEST_PATHS is no longer needed there.
5. **Auto-merge wrapper upgrade (tools/frontier/pr_merge.py +
   github_utils.py merge path)**: attempt `--auto` squash merge first (so
   GitHub merges the moment required checks pass — eliminates poll/retry
   cycles and serializes concurrent PR races); fall back to the current
   direct-merge path when auto-merge is unavailable. Keep the locked
   `_run_gh` + core.bare restore semantics unchanged.
6. Mock-mode driver tests: yellow phase runs parity check; parity failure
   routes bounded repair (not a stop); skip-escape emits the loud event;
   green lane does not run parity.

## Hard constraints

- Surgical ralph_driver.py edits; no reformatting; no state-order change;
  STOP semantics untouched; existing repair budgets reused.
- The tamper guard must remain fail-closed for ad-hoc skips (mutation test:
  raw pytest.skip still flagged).
- No src/alpha_system/** changes. Explicit staging; no runs/values;
  research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/frontier tests/test_ralph_driver.py tests/test_hooks.py -q
just ci-parity   # must pass on this branch (proves the gate is green on a clean tree)
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

Exact counts in the handoff; record ci-parity wall time (the budget claim is
~2-4 min — measure it honestly).

## Done criteria

CI-parity command == CI behavior (drift-tested); yellow/red phases fail
locally instead of at CI_WAIT with bounded repair routing; sanctioned
local-data skip idiom replaces ad-hoc escapes (guard still fail-closed);
auto-merge first with safe fallback; mock tests prove routing; validation
green incl. a real ci-parity run; truthful handoff; fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
