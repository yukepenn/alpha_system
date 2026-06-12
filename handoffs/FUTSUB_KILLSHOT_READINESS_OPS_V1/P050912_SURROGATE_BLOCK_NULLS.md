# P050912_SURROGATE_BLOCK_NULLS Handoff

Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
Phase: `P050912_SURROGATE_BLOCK_NULLS`
Lane: YELLOW
Branch: `wf1/surrogate-block-nulls`

## Scope Completed

- Added dependence-preserving surrogate perturbations in
  `src/alpha_system/governance/surrogate_run.py`:
  - `trade_date_block_shuffle`: deranges equal-length whole trade-date blocks
    within each existing `(label_id, label_type, data_version)` group.
    Unmatched block lengths stay in place and are counted in the summary.
  - `trade_date_block_bootstrap`: resamples equal-length whole trade-date
    blocks with replacement onto the original row skeleton and fails closed on
    an identity arrangement.
- Preserved existing `label_shuffle` behavior:
  - `write_label_shuffled_copy` was not changed.
  - The default CLI perturbation remains `label_shuffle`.
  - The old `label_shuffle.jsonl` output name and trial parameter keys remain
    intact for label-shuffle runs.
- Threaded the new perturbation types through `run_surrogate_study`,
  `SurrogateStudyRun`, `calibrate_surrogate_fdr`, value-free report rendering,
  and `alpha governance surrogate-calibrate --perturbation`.
- Added per-perturbation-type calibration counts and the value-free bound
  statement: "zero passes in K bounds false-pass rate at about 3/K at 95%".
- Added coordinator runbook tool
  `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`.
  It resolves committed re-locked StudySpec pack locks through
  `FeatureLabelPackResolver`/registry APIs, stages JSONL copies under the
  isolated namespace, runs K per block-null config, and writes one value-free
  report.
- Added tests for block shuffle, block bootstrap, deterministic seeds,
  unmatched-length accounting, runner threading, CLI flag/default behavior,
  and the real-calibration tool's committed-sspec resolution path.

## Timestamp Field Rationale

The block writers use `event_ts` as the authoritative trading-date timestamp.
Real label value-store rows serialize from `LabelValueRecord.to_dict()` with
`event_ts`, `horizon_end_ts`, and `label_available_ts`; the value-store tests
compare Parquet loads directly to that shape. `event_ts` is the canonical label
event/decision alignment key used by diagnostics, while `label_available_ts` is
the post-horizon availability guard. Using `label_available_ts` would group by
when the label became safe to read, not by the decision/event date skeleton.
The code documents this at the block-date parser and fails closed when
`event_ts` is absent or invalid.

## Validation

| Command | Outcome | Notes |
|---|---:|---|
| `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q` | PASS | `638 passed in 3.31s`. |
| `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | `35 passed in 0.66s`. |
| `~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py` | PASS | 25 Frontier canaries passed; output ended `All Frontier canaries passed.` |
| `~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" just ci-parity` | PASS | `3300 passed, 75 skipped in 80.71s`. |
| `git diff --check` | PASS | Exit 0. |
| `git ls-files runs` | PASS | No output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | No output. |

Additional note: `~/.venvs/alpha_system_research/bin/python -m ruff check ...`
could not run because `ruff` is not installed in the research venv. This was
not one of the phase-required validation commands; `ci-parity` passed in the
pinned CI venv.

## Artifact And Boundary Notes

- No real-data calibration was executed by Codex; this phase adds the
  coordinator tool only.
- All generated values in tests stayed under pytest temp namespaces.
- The coordinator tool requires `require_isolated_namespace` and rejects report
  writes under `ALPHA_DATA_ROOT/registry`.
- No files under `src/alpha_system/{features,labels,runtime}/**` were edited.
- No `runs/`, registry DB, Parquet, Arrow, Feather, DBN, zstd, log, cache,
  secret, model, or raw/canonical/value data artifacts are tracked.
- Review artifacts were not created by Codex. A fresh Yellow-lane adversarial
  review under `reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/` remains required
  before merge/closeout; Codex did not self-approve this phase.

## Curated Files

- `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P050912_SURROGATE_BLOCK_NULLS-dependence-preserving-calibration.md`
- `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P050912_SURROGATE_BLOCK_NULLS.md`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/cli/governance.py`
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `tests/unit/governance/test_surrogate_run.py`
- `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`
