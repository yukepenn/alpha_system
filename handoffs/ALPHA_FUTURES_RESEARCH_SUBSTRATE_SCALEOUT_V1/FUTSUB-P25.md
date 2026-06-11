# FUTSUB-P25 Handoff

Phase: `FUTSUB-P25` - N_eff / Overlap-Aware Sample Reporting  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-11  
Executor: Codex

## Scope Completed

- Added `src/alpha_system/runtime/diagnostics/splits/n_eff.py` with a
  deterministic, pure, overlap-aware N_eff reporting surface over
  caller-supplied horizon/cadence/discount metadata.
- Added session/day aggregation hooks that count existing caller-supplied
  session and trade-date fields without deriving new session logic.
- Added P24 fold-metadata attachment helpers that consume
  `WalkForwardSplitPlan.to_dict()` / `SplitWindow.to_dict()` records and attach
  train/validation rows and N_eff counts beside `split_id`, purge/embargo, and
  protocol metadata.
- Wired opt-in label diagnostics integration through
  `build_label_diagnostics_report(..., n_eff_overlap_metadata=...,
  walk_forward_metadata=...)`. Calls without an N_eff request keep the prior
  payload shape and omit `label_n_eff_report`.
- Added value-free N_eff documentation and synthetic sample evidence.

No walk-forward split construction, protocol defaults, purge/embargo behavior,
factor diagnostics, shared diagnostics contracts, resolver, registry, value
store, feature/label family code, StudySpec/governance code, broker path,
paper/live path, PR, merge, review artifact, verdict artifact, staging, commit,
or push was performed by the executor.

## Files For Ralph To Stage

- `README.md`
- `docs/futures_substrate_scaleout/N_EFF.md`
- `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
- `src/alpha_system/runtime/diagnostics/label/runtime.py`
- `src/alpha_system/runtime/diagnostics/splits/__init__.py`
- `src/alpha_system/runtime/diagnostics/splits/n_eff.py`
- `tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P25.md`

No `runs/` path should be staged.

## Estimator Definition

Required caller metadata:

- label horizon in bars/minutes/seconds;
- sampling cadence in matching bars or time units;
- explicit `discount_factor` / overlap-factor alias.

Formula:

```text
implied_discount_factor = max(1, horizon / sampling_cadence)
n_eff = floor(rows / discount_factor), bounded to [0, rows]
```

For `rows > 0`, the lower bound after discounting is one effective sample; for
`rows == 0`, `n_eff == 0`. The supplied discount factor must be at least the
implied horizon/cadence factor. Missing, non-finite, incompatible, or
understated metadata fails closed. Conservatism direction: raw rows are
discounted and `n_eff` is never allowed above rows; extended horizons get
stronger discounts at the same cadence. This is a reporting input only, not a
significance or promotion rule.

## Report Contract

When requested, label diagnostics emit `label_n_eff_report` with:

- `rows`, `n_eff`, and `rows_are_not_independent_samples: true`;
- `overlap_metadata` containing horizon, cadence, discount factor, implied
  factor, overlap fraction, and metadata source;
- `session_day_aggregation` with configured field names, observation count,
  session unit count, trade-date unit count, session/trade-date unit count, and
  missing-field counts;
- `walk_forward_fold_n_eff` when walk-forward metadata is supplied, with each
  fold preserving `split_id`, `half_life_protocol` when present, `purge_gap`,
  `embargo_gap`, and nested train/validation rows/N_eff blocks.

The N_eff + fold metadata handoff for FUTSUB-P27...P29 / FUTSUB-P31 /
Validation Governance is: consume `label_n_eff_report`, require the
rows-not-independent marker and explicit overlap metadata, use `n_eff` as the
overlap-aware count input, preserve session/day aggregate counts, and preserve
per-fold train/validation N_eff records when walk-forward context is present.

## Fail-Closed And Compatibility

- Missing metadata: `estimate_n_eff(..., None)` raises
  `NEffSampleReportingError`.
- Inconsistent metadata: a discount factor below the implied horizon/cadence
  overlap raises `NEffSampleReportingError`.
- Label diagnostics requested with fold metadata but no N_eff metadata returns
  `DIAGNOSTICS_FAILED` with reason code
  `n_eff_overlap_metadata_unavailable`; it does not equate rows to N_eff.
- Label diagnostics without an N_eff request keep the prior payload shape; the
  focused test asserts no `label_n_eff_report` and no `n_eff_reporting`
  metadata field.
- Determinism is covered by same-input/same-report test coverage.

No out-of-allowed-path exposure gap was encountered. The N_eff report surface
was exposed from the allowed `runtime/diagnostics/splits/**` and
`runtime/diagnostics/label/**` code paths without editing `contracts.py`,
`factor/**`, `cross_market/**`, `experiments/splits.py`, the resolver, or
registry/governance modules.

## Sample Report

`research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md` exists
and is value-free. It records synthetic rows vs N_eff for a 30m primary horizon
and a 240m extended horizon, session/day aggregate counts, P24-shaped fold
N_eff examples, and fail-closed verification. It contains no per-row
observations, prices, outcomes, provider payloads, local paths, heavy artifacts,
or deployment language.

## Validation

| Command | Outcome |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP && printf 'NO_STOP\n' || { printf 'STOP_PRESENT\n'; sed -n '1,80p' runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP; }` | PASS, printed `NO_STOP`; no `runs/` directory exists in this worktree |
| `python -m ruff format src/alpha_system/runtime/diagnostics/splits/n_eff.py src/alpha_system/runtime/diagnostics/splits/__init__.py src/alpha_system/runtime/diagnostics/label/runtime.py tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py` | PASS; one file reformatted |
| `python -m ruff check --fix tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py` | PASS; one import-order issue fixed |
| `python -m ruff check src/alpha_system/runtime/diagnostics/splits/n_eff.py src/alpha_system/runtime/diagnostics/splits/__init__.py src/alpha_system/runtime/diagnostics/label/runtime.py tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py` | PASS, `All checks passed!` |
| `python -m ruff format --check src/alpha_system/runtime/diagnostics/splits/n_eff.py src/alpha_system/runtime/diagnostics/splits/__init__.py src/alpha_system/runtime/diagnostics/label/runtime.py tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py` | PASS, `4 files already formatted` |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py -q` | PASS, `10 passed` |
| `python -m pytest tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py -q` | PASS, `5 passed` |
| `python tools/verify.py --smoke` | PASS, exit 0, no output |
| `test -f research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md` | PASS, exit 0, no output |
| `test -f docs/futures_substrate_scaleout/N_EFF.md` | PASS, exit 0, no output |
| `test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P25.md` | PASS, exit 0, no output |
| `rg -n -i "profit|tradab|alpha" research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md || true` | PASS, empty output |
| `python tools/hooks/canary_runner.py` | PASS, all Frontier canaries passed |
| `git ls-files runs` | PASS, empty output |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS, empty output |
| `find . -path './.git' -prune -o -path './__pycache__' -prune -o -path './.pytest_cache' -prune -o -path './.ruff_cache' -prune -o -type f \( -name '*.parquet' -o -name '*.sqlite' -o -name '*.arrow' -o -name '*.feather' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' -o -name '*.log' \) -print` | PASS, empty output |

`git status --short` was not run because the executor prompt explicitly
forbade `git status`. The executor also did not run `git diff`, `git add`,
`git commit`, `git push`, PR creation, reviewer calls, review generation,
verdict generation, or merge operations.

## Artifact Policy Confirmation

- No `runs/` directory was present in this worktree at execution time.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair-attempt artifact was created.
- No review artifact or verdict artifact was created.
- No feature value, label value, raw/canonical data, provider payload, Parquet,
  Arrow, Feather, SQLite/DB, DBN/ZST, model artifact, cache, log, secret, or
  local data artifact was created.
- Changes are left unstaged for Ralph.
