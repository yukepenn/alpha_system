# RIGOR-P06 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P06` - Evidence-Accrual Requeue (UNDERPOWERED Retest Scan)  
Lane: YELLOW  
Executor: Codex

## Scope Completed

- Added `src/alpha_system/governance/requeue.py` with
  `RequeuedVerdictRecord`, a planning-prior power estimator, deterministic
  UNDERPOWERED scan logic, materiality constants, table rendering, and
  caller-supplied record output.
- Added the additive `alpha governance requeue-scan` CLI subcommand.
- Added the additive `just requeue-scan` recipe.
- Added tiny synthetic value-free fixtures and tests for schema validation,
  estimator math, determinism, both sides of the materiality rule, input
  no-mutation, malformed/missing evidence fail-closed behavior, CLI output, and
  promotion-gate isolation.
- Added `research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md` documenting
  the materiality rule, input contract, planning-only estimator status, and
  manual coordinator cadence.
- Updated `README.md` with the requested post-merge snapshot.

## Curated File List For Ralph

- `README.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P06.md`
- `justfile`
- `research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md`
- `src/alpha_system/cli/governance.py`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/requeue.py`
- `tests/unit/discovery_rigor_floor/fixtures/requeue/acceptance_evidence.json`
- `tests/unit/discovery_rigor_floor/fixtures/requeue/annotations/annotation_sspec_requeue_eligible.json`
- `tests/unit/discovery_rigor_floor/fixtures/requeue/annotations/annotation_sspec_requeue_not_eligible.json`
- `tests/unit/discovery_rigor_floor/fixtures/requeue/annotations/annotation_sspec_requeue_substrate_gap.json`
- `tests/unit/governance/test_requeue.py`

No files were staged by the executor.

## Materiality Rule

The declared rule lives in `src/alpha_system/governance/requeue.py`:

- `REQUEUE_REASON = "UNDERPOWERED_EVIDENCE_ACCRUAL"`
- `MATERIALITY_MIN_ACCRUED_MONTHS = 6`
- `MATERIALITY_MIN_POWER_DELTA = 0.25`

Eligibility requires both accrued accepted months and planning-power delta to
clear those thresholds. The same rule is cited in
`research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md`.

## Isolation And Mutation Confirmations

- The planning-prior estimator is documented as a heuristic only and is isolated
  in `alpha_system.governance.requeue`.
- `promotion_gate.py` was not edited; the test
  `tests/unit/governance/test_requeue.py::test_requeue_estimator_is_not_imported_by_promotion_gate`
  pins that gate code does not import the requeue module, estimator, or record.
- The scanner reads verdict/annotation/acceptance evidence inputs and writes
  only when the caller supplies `--out`; it never writes to ledgers,
  registries, verdicts, annotations, or schedulers.
- The test
  `tests/unit/governance/test_requeue.py::test_requeue_scan_does_not_mutate_inputs`
  confirms fixture input bytes are identical before and after a scan.
- No daemon, scheduler, cron, watcher, auto-rerun, reviewer call, PR, merge,
  live trading, paper trading, broker operation, order routing, deployment, or
  destructive cleanup was performed.

## Validation Results

| Command | Result | Notes |
|---|---:|---|
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `python -m ruff check src/alpha_system/governance/requeue.py src/alpha_system/cli/governance.py tests/unit/governance/test_requeue.py` | PASS | All checks passed. |
| `python -m pytest tests/unit/governance/test_requeue.py -q` | PASS | 10 passed in 0.29s. |
| `python -m pytest tests/unit/governance -q` | PASS | 567 passed in 3.07s. |
| `python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | 1 passed in 0.01s. |
| `python tools/verify.py --smoke` | PASS | Exit 0. |
| `python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed. |
| `grep -n "requeue-scan" justfile` | PASS | Lines 33-34 show the recipe. |
| `test -f research/discovery_rigor_floor_v1/requeue/REQUEUE_SCAN.md` | PASS | Exit 0. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git ls-files '**/*.sqlite3' '**/*.db-journal' '**/*.wal' '**/*.duckdb' '**/*.pkl' '**/*.npy' '**/*.npz'` | PASS | Exit 0, no output. |
| `git diff --stat main -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -o --exclude-standard -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | PASS | Exit 0, no output; no tracked or untracked changes in the historical Core Pilot evidence dirs. |

## Artifact And Git Confirmations

- `git ls-files runs` is empty.
- Heavy tracked-artifact globs are empty.
- Historical Core Pilot `study_specs`, `reviewer_verdicts`, `evidence`, and
  `ledgers` were not edited.
- No `runs/` handoff, `review.md`, or `verdict.json` was created.
- No `reviews/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P06/**` artifact was created by
  this executor; Yellow-lane review is Ralph/reviewer-owned.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.

## Notes

The run artifact directory named in the executor prompt,
`runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P06`, was absent
in this worktree. This did not block execution because the prompt supplied the
full generated phase spec and the required handoff is commit-eligible under
`handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P06.md`.
