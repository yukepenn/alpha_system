# LCFP-P03 Handoff

Phase: `LCFP-P03` - Fast Fixed + Extended Horizon Labels

Lane: `YELLOW`

## Status

code_status: implemented

parity_status: local synthetic parity checks passed for the P03 fixed-minute
surface. This is not a benchmark result and does not claim the fast path is
accepted for production label materialization.

Ralph owns staging, commit, review routing, verdict parsing, PR, CI, merge
gate, merge, and done-check. Codex left changes unstaged.

## Files Changed

Commit-eligible changed files:

- `src/alpha_system/labels/fast/fixed_horizon.py`
- `src/alpha_system/labels/fast/materializer.py`
- `tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`
- `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py`
- `tests/unit/label_compute_fast_path/test_fixed_horizon_extended_pack.py`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `README.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P03.md`

Run-local handoff copy:

- `runs/2026-06-10T102615Z_LABEL_COMPUTE_FAST_PATH_V1/phases/LCFP-P03/handoff.md`

The run-local copy is ignored/local-only and must not be staged.

## Repair Summary

- Repaired fixed-horizon token handling so non-minute governed enum values
  `session_close` and `maintenance_flat` no longer crash `_horizon_minutes`.
- Updated the FCFP-P10 synthetic fixture to build valid governed `LabelSpec`s
  for every current `FixedHorizonLabelName`, including close-out symbolic
  labels.
- Added explicit P04 routing for symbolic close-out labels:
  `build_fixed_horizon_label_pack(...)` and `supports_fixed_horizon_label_pack(...)`
  reject those definitions with a `FastLabelPackError` naming LCFP-P04 rather
  than raising `ValueError`.
- Corrected `governance_gap_note`: P03 coverage is governed fixed-minute
  trade-price 1/3/5/10/15/30/60/120/240m plus existing governed fixed-minute
  midprice 1/3/5/10/30m; `session_close` and `maintenance_flat` are P04.

## Implementation Summary

- `FastLabelMaterializer` now converts the prepared frame into the LCFP-P02
  `SharedLabelPanel` and computes fixed-minute records from cached
  `TerminalIndexModel`s.
- Terminal resolution is cached once per distinct horizon minute. This is the
  bounded deviation from a literal one-pass-all-horizons guard pass: the P02
  `TerminalRequest` contract is horizon-scoped, so each horizon has its own
  terminal model while panel load/input adaptation is still shared.
- Record emission preserves reference-shaped values and quality flags. Broader
  P02 quality metadata remains value-free metadata; emitted records keep exact
  fixed-horizon family flag parity.
- Per-label metadata now includes the governed `HorizonOverlapMetadata` payload
  from `compute_horizon_overlap_metadata(...)`.
- No label identities were minted or changed; output records retain
  reference-derived `label_version_id`s from `LabelContractSpec`.

## Parity Coverage

Covered by local synthetic tests:

- All nine governed trade-price fixed-minute horizons:
  1m, 3m, 5m, 10m, 15m, 30m, 60m, 120m, 240m.
- Existing governed fixed-minute midprice labels:
  1m, 3m, 5m, 10m, 30m.
- Value parity against `compute_fixed_horizon_labels(...)`.
- `label_available_ts` exact parity.
- Roll / contract terminal drop parity and maintenance-crossing drop parity.
- Trade no-trade gap flags and BBO missing/quarantined gap flags.
- `HorizonOverlapMetadata` version, label id, horizon minutes, raw row count,
  and effective sample count.
- `label_version_id` identity parity.

Documented tolerance:

- BBO arithmetic invariant checks in the fast record path use `1e-9` absolute
  tolerance to avoid false `bbo_invariant_violation` flags from float
  representation after Polars conversion. This matches the existing BBO fast
  feature invariant tolerance and does not widen value comparison tolerance.

## Validation Commands

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`.
  - Replacement changed-file inventory used:
    `git ls-files --modified --others --exclude-standard`.
- `python tools/verify.py --smoke`
  - Succeeded with exit 0 and no output using
    `/home/yuke_zhang/.venvs/alpha_system_research/bin/python`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - `12 passed in 0.69s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q`
  - `4 passed in 1.54s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - `12 passed in 0.20s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - `2 passed in 0.22s`.
- `git ls-files runs`
  - Succeeded with empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Succeeded with empty output.

Additional checks:

- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src/alpha_system/labels/fast tests/unit/label_compute_fast_path tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`
  - Succeeded with exit 0 and no output.
- `git ls-files --deleted`
  - Succeeded with empty output.

## Changed-File Inventory

`git ls-files --modified --others --exclude-standard` reported:

```text
handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P03.md
tests/unit/label_compute_fast_path/test_fixed_horizon_extended_pack.py
README.md
docs/label_compute_fast_path/OVERVIEW.md
docs/label_compute_fast_path/README.md
src/alpha_system/labels/fast/fixed_horizon.py
src/alpha_system/labels/fast/materializer.py
tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py
tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py
```

No `runs/**`, value file, SQLite/DB, Parquet, Arrow, Feather, raw/canonical
data, log, cache, secret, review artifact, or verdict artifact is listed for
staging.

## Run Artifact Notes

The prompt named
`runs/2026-06-10T102615Z_LABEL_COMPUTE_FAST_PATH_V1/phases/LCFP-P03`, but this
worktree initially had no `runs/` directory and no run-local `state.json`,
`heartbeat.json`, or `spec.md`. Codex created only the ignored run-local
handoff path required for local audit.

Preflight STOP check:

- `test -e runs/2026-06-10T102615Z_LABEL_COMPUTE_FAST_PATH_V1/STOP; printf '%s\n' $?`
  - Output `1`, meaning no STOP file was present at the requested run path.

Codex did not create `review.md`, `verdict.json`, review artifacts, a PR, a
merge, a commit, or staged changes.
