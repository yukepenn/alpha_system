# P080820_SURROGATE_DETECTION_STATISTIC Handoff

Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
Phase: `P080820_SURROGATE_DETECTION_STATISTIC`
Lane: YELLOW
Branch: `wf1/surrogate-detection-statistic`

## Scope Completed

- Extracted one shared diagnostic statistic helper in
  `src/alpha_system/governance/detection_statistic.py`.
  `true_alpha_detection.py` now consumes that helper instead of owning private
  Pearson IC extraction.
- Changed surrogate pass semantics in `surrogate_run.py`:
  - `statistic_passed` is computed from shared diagnostic-layer
    `directional.pearson_ic` absolute value against the TRUE-alpha detection
    threshold `0.95`.
  - `passed` equals `statistic_passed`.
  - `eligibility_clean` records warning-free diagnostics as context only.
  - uncomputable statistics fail closed into `ERROR` rows during calibration.
- Updated `SurrogateCalibrationReport` and report rendering:
  - `statistic_pass_count` drives `threshold_verdict`.
  - `eligibility_clean_count` is reported as context.
  - `gate_pass_count` remains as a compatibility alias for the statistic pass
    count.
  - the bound statement is shared between the core renderer and real tool.
- Added `--rescore-existing` to
  `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`. It reads
  persisted seed outputs under `<namespace>/seed_*/study_outputs/` and does not
  re-run studies or resolve packs.
- Added value-free diagnosis record:
  `research/discovery_rigor_floor_v1/surrogate_fdr/REGIME_LEAKAGE_BLOCKED_DIAGNOSIS.md`.
- Updated tests for statistic/eligibility independence, report counts,
  re-score reproduction, missing-output ERROR behavior, and P05 synthetic
  calibration semantics.

## Persisted Output Shape Required

Re-score mode requires each declared seed to have:

- `<namespace>/seed_<seed>/study_outputs/diagnostic_summary.json`
- JSON root object.
- `warnings`: list. Empty list means `eligibility_clean=True`; non-empty means
  `eligibility_clean=False`.
- `diagnostics`: mapping.
- `diagnostics.directional.pearson_ic`: either a finite number or the persisted
  writer shape observed from `write_study_outputs`:
  `{"ic": <finite number>, "n": <sample count>}`.

If the file is absent, malformed, lacks the required diagnostic path, or has a
null/non-finite IC, the seed is recorded as `ERROR`. Optional
`seed_<seed>/surrogate_runs/*.json` is used for IDs and consistency checks when
present; if present, exactly one record must match the declared seed and
perturbation type.

## Validation

| Command | Outcome | Notes |
|---|---:|---|
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q` | PASS | `640 passed in 3.36s`. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | `37 passed in 0.87s`. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py` | PASS | 25 canaries passed; output ended `All Frontier canaries passed.` |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `PYTHONPATH=$PWD/src PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" just ci-parity` | PASS | `3304 passed, 75 skipped in 90.10s`. |
| `git diff --check` | PASS | Exit 0. |
| `git ls-files runs` | PASS | No output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | No output. |

Note: the research venv imports `alpha_system` from
`/home/yuke_zhang/projects/alpha_system/src` unless `PYTHONPATH=$PWD/src` is
set. The validation commands above force this worktree's source path so the
branch code is what ran.

## Artifact And Boundary Notes

- No real-data calibration was executed by Codex.
- No `src/alpha_system/{features,labels,runtime}/**` files were edited.
- No perturbation writer behavior, namespace policy, or gate-stack transition
  semantics were changed outside the surrogate pass/report fields.
- Test-generated caches and local runtime outputs were not staged.
- No `runs/`, SQLite, Parquet, Arrow, Feather, DBN, zstd, log, model, secret,
  raw/canonical data, feature values, or label values are tracked.
- Fresh Yellow-lane adversarial review artifacts under
  `reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/` were not created by Codex and
  remain required before merge/closeout.
- Per user instruction, this branch was not pushed and no PR was created.

## Curated Files

- `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P080820_SURROGATE_DETECTION_STATISTIC-signal-aligned-pass-semantics.md`
- `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P080820_SURROGATE_DETECTION_STATISTIC.md`
- `research/discovery_rigor_floor_v1/surrogate_fdr/REGIME_LEAKAGE_BLOCKED_DIAGNOSIS.md`
- `src/alpha_system/governance/detection_statistic.py`
- `src/alpha_system/governance/canaries/true_alpha_detection.py`
- `src/alpha_system/governance/surrogate_run.py`
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `tests/unit/governance/test_surrogate_run.py`
- `tests/unit/discovery_rigor_floor/test_p040500_true_alpha_detection_canary.py`
- `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p05_surrogate_fdr.py`
