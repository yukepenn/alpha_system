# RIGOR-P04 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P04` - Executable RANDOM_TARGET + End-to-End Planted-Fake-Alpha Canary  
Lane: YELLOW  
Executor: Codex

## Scope Completed

- Made all four `REQUIRED_NEGATIVE_CONTROL_TYPES` executable in canonical
  catalog order through `run_governance_canary`, `run_required_governance_canaries`,
  and `main(['--canary', ...])`.
- Added deterministic `RANDOM_TARGET` execution with recorded target-replacement
  metadata, seed, and digest, plus a tiny synthetic fixture under
  `evals/canaries/random_target/`.
- Added `PlantedFakeAlphaStudyCanary` using a tiny synthetic fixture where each
  label at bar `t` is derived from future bar `t+1` metadata.
- Extended `validate_evidence_ready_gate` so `DIAGNOSTICS_RUN -> EVIDENCE_READY`
  requires current `PASS` `NegativeControlResult`s for all required controls and
  blocks missing, failed, stale, malformed, or duplicate control results.
- Registered `governance_random_target` and expected-block `planted_fake_alpha`
  scenarios in `tools/hooks/canary_runner.py`.
- Added governance/discovery bypass tests, a value-free canary-floor evidence
  note, and a README snapshot update.

## Curated File List For Ralph

- `README.md`
- `docs/SYSTEM_MAP.md`
- `evals/canaries/planted_fake_alpha/README.md`
- `evals/canaries/planted_fake_alpha/synthetic_fixture.json`
- `evals/canaries/random_target/synthetic_fixture.json`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P04.md`
- `research/discovery_rigor_floor_v1/canary_floor/RIGOR-P04_canary_floor.md`
- `src/alpha_system/governance/canaries/__init__.py`
- `src/alpha_system/governance/canaries/harness.py`
- `src/alpha_system/governance/canaries/planted_fake_alpha.py`
- `src/alpha_system/governance/evidence_bundle.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py`
- `tests/unit/governance/test_canary_harness.py`
- `tests/unit/governance/test_cli.py`
- `tests/unit/governance/test_evidence_bundle.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`
- `tests/unit/governance/test_reviewer_independence.py`
- `tests/integration/governance/test_cli_smoke.py`
- `tests/integration/governance/test_end_to_end_dry_run.py`
- `tools/hooks/canary_runner.py`

No files were staged by the executor.

## 4/4 Executable-Control Inventory

| Catalog order | Control | Executable surface | Fixture | Result |
|---:|---|---|---|---|
| 1 | `random_target` | `run_random_target_canary`, harness CLI, canary runner | `evals/canaries/random_target/synthetic_fixture.json` | `PASS` |
| 2 | `permuted_labels` | `run_label_leakage_canary`, harness CLI, canary runner | `evals/canaries/permuted_labels/synthetic_fixture.json` | `PASS` |
| 3 | `future_shift` | `run_future_shift_canary`, harness CLI, canary runner | `evals/canaries/future_shift/synthetic_fixture.json` | `PASS` |
| 4 | `optimistic_fill` | `run_optimistic_fill_canary`, harness CLI, canary runner | `evals/canaries/optimistic_fill/synthetic_fixture.json` | `PASS` |

## Planted-Fake-Alpha Outcome

Outcome: `REJECTED`.

Blocking gate: `DIAGNOSTICS_RUN -> EVIDENCE_READY`.

Blocking issue: `locked_test_contamination_blocks_evidence_ready`.

Contamination mechanism: the synthetic fixture labels each bar `t` from future
bar `t+1` metadata; the canary records that as a trial-ledger locked-test
contamination flag and the existing P03 gate blocks it.

## Gate To Bypass-Test Map

| Gate / fail-closed path | Test that fails if neutered |
|---|---|
| All four controls executable in catalog order | `tests/unit/governance/test_canary_harness.py::test_required_governance_canaries_run_in_canonical_scope`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_required_negative_controls_are_four_executable_in_catalog_order` |
| RANDOM_TARGET missed guard records `FAIL` | `tests/unit/governance/test_canary_harness.py::test_missed_guard_is_recorded_as_fail[random_target-run_random_target_canary]` |
| Missing required control blocks `EVIDENCE_READY` | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_requires_all_required_negative_controls`; `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_missing_required_negative_control_through_gate` |
| Failed required control blocks `EVIDENCE_READY` | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_blocks_failed_negative_control_result` |
| Stale/mismatched control result blocks `EVIDENCE_READY` | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_blocks_stale_negative_control_result` |
| Planted lookahead-contaminated study is rejected | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_planted_fake_alpha_canary_rejects_contaminated_study` |
| De-contaminating planted fixture fails the canary | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_decontaminated_planted_fixture_fails_the_canary` |
| canary_runner has RANDOM_TARGET and planted expected-block registration | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_canary_runner_registers_random_target_and_planted_fake_alpha` |

## Validation Results

| Command | Result | Notes |
|---|---:|---|
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `python -m py_compile src/alpha_system/governance/canaries/harness.py src/alpha_system/governance/canaries/planted_fake_alpha.py src/alpha_system/governance/evidence_bundle.py tools/hooks/canary_runner.py tests/unit/governance/test_canary_harness.py tests/unit/governance/test_evidence_bundle.py tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py` | PASS | Exit 0. |
| `python - <<'PY' ... import alpha_system ... PY` | FAIL | `ModuleNotFoundError: No module named 'alpha_system'`; env-only import probe without `PYTHONPATH=src`. |
| `PYTHONPATH=src python - <<'PY' ... run_required_governance_canaries/run_planted_fake_alpha_canary ... PY` | PASS | Printed `['random_target', 'permuted_labels', 'future_shift', 'optimistic_fill']` and `REJECTED locked_test_contamination_blocks_evidence_ready PASS`. |
| `PYTHONPATH=src python -m pytest tests/unit/governance/test_canary_harness.py tests/unit/governance/test_evidence_bundle.py tests/unit/governance/test_promotion_gate_state_machine.py -q` | PASS | `134 passed in 0.21s`. |
| `PYTHONPATH=src python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py -q` | PASS | `13 passed in 0.07s`. |
| `PYTHONPATH=src python -m pytest tests/unit/governance/test_cli.py tests/unit/governance/test_reviewer_independence.py -q` | PASS | `21 passed in 2.56s`. |
| `PYTHONPATH=src python -m pytest tests/unit/governance/test_negative_controls.py -q` | PASS | `19 passed in 0.06s`. |
| `PYTHONPATH=src python -m pytest tests/unit/governance -q` | PASS | Final run: `606 passed in 2.89s`. |
| `PYTHONPATH=src python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | Final run: `15 passed in 0.06s`. |
| `python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed, including `governance_random_target` and `planted_fake_alpha`. |
| `python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `test -f evals/canaries/random_target/synthetic_fixture.json && test -f evals/canaries/planted_fake_alpha/synthetic_fixture.json` | PASS | Exit 0. |
| `git diff --quiet -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -o --exclude-standard -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | PASS | Exit 0, no output; no tracked or untracked changes under historical evidence dirs. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git ls-files -m -o --exclude-standard` | PASS | Output contained only the curated files listed above before this handoff was written; after handoff, add this handoff path to the same curated set. |

## Repair Attempt 1 - CI Failure 27390580288

Repair scope: only the CI failures shown for `RIGOR-P04`.

Changes:

- Fixed a package import cycle by lazily exporting planted-fake-alpha symbols
  from `alpha_system.governance.canaries`; direct submodule imports remain
  unchanged, and package-level imports still work through `__getattr__`.
- Updated the existing governance CLI smoke fixture to carry four current
  `NegativeControlResult` PASS records tied to its `StudySpec`, matching the
  stricter evidence-ready gate instead of the old free-form control metadata.
- Updated the synthetic governance end-to-end dry run to consume the now-4/4
  executable `run_required_governance_canaries()` output exactly once, removing
  the duplicate `random_target` result.
- Regenerated `docs/SYSTEM_MAP.md` so the generated canary inventory includes
  `planted_fake_alpha`.

Repair changed files:

- `docs/SYSTEM_MAP.md`
- `src/alpha_system/governance/canaries/__init__.py`
- `tests/integration/governance/test_cli_smoke.py`
- `tests/integration/governance/test_end_to_end_dry_run.py`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P04.md`

Repair validation:

| Command | Result | Notes |
|---|---:|---|
| `PYTHONPATH=src python -m pytest tests/integration/governance/test_cli_smoke.py::test_governance_cli_end_to_end_smoke -q` | PASS | `1 passed in 2.22s`. |
| `PYTHONPATH=src python -m pytest tests/integration/governance/test_end_to_end_dry_run.py::test_synthetic_end_to_end_governance_dry_run -q` | PASS | `1 passed in 3.34s`. |
| `PYTHONPATH=src python -m pytest tests/tools/test_system_map.py::test_committed_map_is_current -q` | PASS | `1 passed in 0.02s`. |
| `PYTHONPATH=src python -m pytest tests/integration/governance -q` | PASS | `8 passed in 7.52s`. |
| `PYTHONPATH=src python -m pytest tests/unit/governance tests/unit/discovery_rigor_floor -q` | PASS | `621 passed in 2.91s`. |
| `PYTHONPATH=src python -m pytest tests/tools/test_system_map.py -q` | PASS | `2 passed in 0.02s`. |
| `python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed. |
| `PYTHONPATH=src python -m pytest` | FAIL | Local env-only false negative: `3222 passed, 74 skipped, 1 failed`; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` saw `ALPHA_DATA_ROOT` exported and selected `alpha_data_root` instead of `run_artifacts`. |
| `env -u ALPHA_DATA_ROOT PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only -q` | PASS | `1 passed in 0.02s`. |
| `python tools/verify.py --smoke` | PASS | Exit 0; no stdout/stderr. |
| `python tools/frontier/status_doctor.py` | WARN | No live run dir with `state.json` found for this campaign; hook floor and runtime contract OK. |
| `env -u ALPHA_DATA_ROOT PYTHONPATH=src python -m pytest` | PASS | `3223 passed, 74 skipped in 54.35s`. |
| `git diff --check` | PASS | Exit 0. |
| `git status --short` | PASS | Modified files: `docs/SYSTEM_MAP.md`, `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P04.md`, `src/alpha_system/governance/canaries/__init__.py`, `tests/integration/governance/test_cli_smoke.py`, `tests/integration/governance/test_end_to_end_dry_run.py`. |
| `git diff --cached --name-only` | PASS | Exit 0, no output; no staged files. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git diff --quiet -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | PASS | Exit 0; historical evidence remains untouched. |

## Confirmations

- Historical Core Pilot evidence directories under `study_specs/`,
  `reviewer_verdicts/`, `evidence/`, and `ledgers/` were not edited by this
  executor; the allowed `git ls-files -m -o --exclude-standard -- ...` audit
  printed no output.
- `git ls-files runs` printed no output.
- Heavy tracked-artifact globs printed no output.
- The prompt-provided run artifact directory
  `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P04` was not
  present in this checkout; no run-local handoff was written.
- No `review.md`, `verdict.json`, or
  `reviews/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P04/**` artifact was created by the
  executor; Yellow-lane review is Ralph-owned.
- No `git add`, `git commit`, or `git push` was run. Repair audit did run
  `git status`, `git diff`, `git diff --cached`, and `git ls-files` checks
  listed above; no files are staged.
- No PR, merge, reviewer call, live trading, paper trading, broker operation,
  order routing, deployment, destructive cleanup, FUTSUB run-state change,
  market-data materialization, registry mutation, or value computation was
  performed.

## Notes For Review

- The evidence bundle constructor remains permissive for descriptive bundle
  construction; the stricter all-controls-PASS check is enforced at
  `validate_evidence_ready_gate` and the promotion-gate path that calls it.
- Planted-fake-alpha writes only to caller-supplied tmp paths or a temporary
  directory created by the canary module. Production registries and ledgers are
  never targets.
- Existing FUTURE_SHIFT, PERMUTED_LABELS, and OPTIMISTIC_FILL fixtures and guard
  semantics were left unchanged.

## Next Step

Ralph should stage the curated files explicitly, run handoff validation and the
fresh Yellow-lane review, then proceed with PR/CI/merge-gate handling if review
passes.
