# RIGOR-P05 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P05` - Surrogate-FDR Calibration  
Lane: YELLOW  
Branch: not queried by executor; prompt forbids `git status`  
Commits: none by executor; all changes left unstaged for Ralph

## Scope Completed

- Added `src/alpha_system/governance/surrogate_run.py` with:
  - `SurrogateStudyRun` schema, closed `perturbation_type` enum
    (`label_shuffle`, `random_target`), deterministic IDs, and canonical
    round-trip serialization.
  - Deterministic seeded label-value shuffling before the existing diagnostics
    path runs.
  - Isolated namespace enforcement that rejects production repo registry/data,
    historical evidence, `runs/`, artifact, DB, and heavy-file targets; non-temp
    scratch namespaces must use the `rigor_p05_surrogate_` prefix.
  - Surrogate runner that writes shuffled labels, diagnostics output, trial
    ledger JSON, variant-ledger JSONL, and the `SurrogateStudyRun` record only
    under the caller-supplied isolated namespace.
  - Calibration harness with run count, error count, gate-pass count, pass-rate,
    seed/outcome table, `zero-pass-met`, `LEAKAGE_BLOCKED`, and
    fail-closed `CALIBRATION_BLOCKED` for errored runs.
  - Value-free Markdown report rendering.
- Extended `TrialLedgerRecord` with additive `surrogate_flag` threading:
  - Existing production payloads remain valid and keep their old IDs because
    `surrogate_flag=False` is omitted from production `to_dict()` output.
  - `surrogate_flag=True` creates distinct trial IDs and is persisted in
    surrogate ledgers.
  - `TrialLedgerAccounting` excludes surrogate records from production
    variant/family budget counts while retaining first-class attempt/status
    accounting.
- Added `alpha governance surrogate-calibrate` with required `--study-spec`,
  `--runs`, `--base-seed`, `--namespace`, and optional `--report-out`.
  The command exits non-zero on `LEAKAGE_BLOCKED` or errored calibration.
- Added `SurrogateStudyRun` governance ID prefix `surrun_`.
- Added schema, runner, determinism, threshold, CLI, and bypass-canary tests.
- Added value-free synthetic calibration evidence at
  `research/discovery_rigor_floor_v1/surrogate_fdr/RIGOR-P05_synthetic_calibration.md`.
- Updated `README.md` snapshot for RIGOR-P05 machinery and unchanged safety
  boundaries.

## Curated File List For Ralph

- `README.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P05.md`
- `research/discovery_rigor_floor_v1/surrogate_fdr/RIGOR-P05_synthetic_calibration.md`
- `src/alpha_system/cli/governance.py`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/governance/trial_ledger.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py`
- `tests/unit/governance/test_ids.py`
- `tests/unit/governance/test_surrogate_run.py`
- `tests/unit/governance/test_trial_ledger.py`

No files were staged by the executor.

## Synthetic Calibration Summary

- Synthetic run budget: `N=2`
- Base seed: `5000`
- Error count: `0`
- Gate pass count: `0`
- Gate pass rate: `0.000000`
- Threshold verdict: `zero-pass-met`
- Per-run outcomes:
  - seed `5000`: `BLOCKED`, reason `UNDERPOWERED`,
    surrogate `surrun_b09c096721fcf0be8d19edba`
  - seed `5001`: `BLOCKED`, reason `UNDERPOWERED`,
    surrogate `surrun_6b1c51e8d138a968b82e18c0`

The synthetic calibration used `/tmp/rigor_p05_synthetic_report` for all
surrogate outputs. The committed report contains counts, rates, seeds,
outcomes, IDs, and inventory only; no label, feature, return, or diagnostic
values are committed.

## Machinery To Bypass-Test Map

| Fail-closed path | Test that fails if neutered |
|---|---|
| Production namespace targeting rejected | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_production_namespace_canary_blocks_surrogate_targeting` |
| `surrogate_flag` preserved on trial records | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_surrogate_flag_canary_marks_trial_records` |
| Surrogate records excluded from production budget counts | `tests/unit/governance/test_trial_ledger.py::test_trial_ledger_accounting_excludes_surrogates_from_production_budget` |
| Surrogate-only ledgers remain first-class but budget-neutral | `tests/unit/governance/test_trial_ledger.py::test_surrogate_only_trial_ledger_is_first_class_but_budget_neutral` |
| Any shuffled pass yields `LEAKAGE_BLOCKED` | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_zero_pass_threshold_canary_blocks_any_shuffled_pass` |
| Errored runs cannot mask zero-pass success | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_error_masking_canary_blocks_zero_pass_success` |
| Same seed and StudySpec repeat gate outcome | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_seed_determinism_canary_repeats_gate_outcome` |
| CI-runnable synthetic calibration stays zero-pass | `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py::test_synthetic_calibration_canary_is_zero_pass_in_ci` |
| CLI writes a value-free report and returns success only for zero-pass | `tests/unit/governance/test_surrogate_run.py::test_surrogate_calibrate_cli_writes_value_free_report` |

## Validation Results

| Command | Outcome | Notes |
|---|---:|---|
| `python -m py_compile src/alpha_system/governance/surrogate_run.py src/alpha_system/governance/trial_ledger.py src/alpha_system/governance/ids.py src/alpha_system/cli/governance.py tests/unit/governance/test_surrogate_run.py tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py tests/unit/governance/test_trial_ledger.py tests/unit/governance/test_ids.py` | OK | Exit 0. |
| `python -m pytest tests/unit/governance/test_surrogate_run.py tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py tests/unit/governance/test_trial_ledger.py tests/unit/governance/test_ids.py -q` | OK | `82 passed in 0.38s`. |
| `python -m pytest tests/unit/governance -q` | OK | `613 passed in 3.00s`. |
| `python -m pytest tests/unit/discovery_rigor_floor -q` | OK | `17 passed in 0.09s`. |
| `python -m ruff check src/alpha_system/governance/surrogate_run.py src/alpha_system/governance/trial_ledger.py src/alpha_system/governance/ids.py src/alpha_system/cli/governance.py tests/unit/governance/test_surrogate_run.py tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py tests/unit/governance/test_trial_ledger.py tests/unit/governance/test_ids.py` | OK | `All checks passed!`. |
| `python tools/verify.py --smoke` | OK | Exit 0, no stdout/stderr. |
| `python tools/hooks/canary_runner.py` | OK | All Frontier canaries passed. |
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `git diff --quiet -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -o --exclude-standard -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | OK | Exit 0, no output; no tracked or untracked changes under historical evidence dirs. |
| `git ls-files runs` | OK | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | OK | Exit 0, no output. |
| `git ls-files -m -o --exclude-standard` | OK | Output contained only the curated files listed above before this handoff was written; after handoff, add this path to the same curated set. |

## Isolation And Artifact Confirmation

- All surrogate writes performed by tests and synthetic report generation stayed
  in pytest tmp paths or `/tmp/rigor_p05_synthetic_report`.
- No production registry, production ledger, historical Core Pilot artifact,
  FUTSUB artifact, FUTSUB run state, broker surface, execution surface, live
  surface, or strategy/portfolio surface was intentionally read/write targeted
  by the surrogate output path.
- `git ls-files runs` printed no output.
- Heavy tracked-artifact globs printed no output.
- Historical evidence audit via allowed `git ls-files -m -o --exclude-standard`
  printed no output for the forbidden historical evidence directories.
- The prompt-provided run artifact directory
  `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P05` was not
  present in this checkout; no run-local handoff was written.
- No `review.md`, `verdict.json`, or
  `reviews/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P05/**` artifact was created by the
  executor; Yellow-lane review is Ralph-owned.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.
- No PR, merge, reviewer call, live trading, paper trading, broker operation,
  order routing, deployment, destructive cleanup, FUTSUB run-state change, or
  production registry mutation was performed.

## Real-Data Calibration Status

Real-data surrogate calibration over the declared kill-shot StudySpec remains a
coordinator runbook step before FUTSUB-P28 kill-shot resume. This phase landed
the machinery, CLI, threshold logic, and CI-runnable synthetic calibration; it
did not execute real-data calibration in-phase.

## Risks And Caveats

- The runner uses the existing diagnostics and governance transition primitives
  with an injected deterministic study run id. It does not call external
  reviewers or synthesize reviewer approval.
- Errored runs produce `CALIBRATION_BLOCKED`, not `zero-pass-met`; any shuffled
  pass produces `LEAKAGE_BLOCKED`. There is no tolerance or waiver flag.
- The `random_target` enum value is schema-only in this phase. Execution remains
  fail-closed for `random_target`, which is RIGOR-P04 territory.

## Review Request Focus

- Confirm the runner shuffles label values before invoking the existing
  diagnostics path and then traverses the real `DIAGNOSTICS_ALLOWED ->
  DIAGNOSTICS_RUN -> EVIDENCE_READY` gate stack.
- Confirm namespace validation prevents production ledger/registry targets and
  all surrogate outputs are local-only.
- Confirm `surrogate_flag` defaults preserve legacy TrialLedger behavior and
  true surrogate records are excluded from production budget accounting.
- Confirm zero-pass threshold behavior has no tolerance/waiver path and errors
  cannot be counted as non-passes.
- Confirm the committed synthetic report is value-free.
- Confirm no RIGOR-P04 scope leaked in: `tools/hooks/canary_runner.py` and
  `evals/canaries/**` were not edited.

## Next Step

Ralph should explicitly stage the curated files, run handoff validation and the
Yellow-lane fresh review, then proceed with PR/CI/merge-gate handling if review
accepts the phase.
