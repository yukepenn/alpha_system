# FUTSUB-P15 Handoff - Feature Coverage Matrix and Quality Report

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P15`  
Executor: Codex  
Status: executor work complete; changes left unstaged for Ralph

## Files For Ralph To Stage

- `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
- `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P15.md`

No files under `runs/` were created or staged by the executor. No review or
verdict artifacts were created by the executor per the Workflow 2 prompt
constraints; Ralph owns review routing and verdict handling.

## Scope Completed

- Authored the value-free family x symbol x year matrix for all eight governed
  FeaturePack families across ES, NQ, RTY, and 2018-2026.
- Recorded per-cell status (`P`, `W`, `EE`, `UG`), registered row counts,
  registry FeatureVersion counts, quality/missingness summary rates, and BBO
  flag rates.
- Recorded explicit expected exclusions and confirmed there are no unexpected
  family / symbol / year gaps in the accepted/warned 2019-2026 window.
- Added the durable docs summary and README snapshot.

## Coverage Summary

Scope: 8 families x 3 symbols x 9 years = 216 cells.

| Status | Cells |
| --- | ---: |
| Present clean (`P`) | 144 |
| Present warned (`W`) | 48 |
| Expected-excluded (`EE`) | 24 |
| Unexpected gap (`UG`) | 0 |

All 2019-2026 family / symbol / year cells resolve to registered
FeatureVersions with registry-backed value rows. The 2018 cells are expected
exclusions because required 2018 `ohlcv_1m` / `bbo_1m` DatasetVersions are
`BLOCKED`.

## Quality / Missingness Highlights

- Registered row counts range from 138,593 to 357,420 across present/warned
  cells.
- Every present/warned cell has complete family registry membership for its
  actual registered FeatureVersion set.
- Aggregate missing `available_ts` rate is 0.000000 across present/warned
  cells.
- Max null-like and quality-flag rates are recorded by family in the matrix.
  Nonzero rates are surfaced value gaps or quality flags, not silent coverage.
- BBO missingness / bad-quote / wide-spread / low-depth rates are recorded per
  symbol/year. The largest observed BBO flag rates are value-free summary
  statistics only.

## Explicit Gap List

Expected exclusions:

- 2018 x all eight families x ES/NQ/RTY = 24 cells.
- Classification: expected.
- Reason: required `ohlcv_1m` and `bbo_1m` 2018 DatasetVersions are `BLOCKED`;
  the documented root cause is the RTY 2018 sparse-history coverage gap, and the
  feature window uses dataset-level fallback rather than fabricated per-symbol
  acceptance.

Unexpected gaps:

- None.

## Validation

`git status --short` was not run because the executor prompt explicitly forbids
`git status`. `git diff --cached --name-only` was not run because the executor
prompt explicitly forbids `git diff`, and Codex did not stage anything.

| Command | Outcome |
| --- | --- |
| `python tools/frontier/status_doctor.py` | WARN: active campaign pointer resolved, but no live run dir with `state.json` was found for this campaign in this worktree. Execution continued from the supplied generated spec and committed/local registry evidence. |
| `python tools/verify.py --smoke` | Passed. |
| `test -f research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md` | Passed. |
| `test -f docs/futures_substrate_scaleout/FEATURE_COVERAGE.md` | Passed. |
| `python tools/hooks/canary_runner.py` | Passed; all Frontier canaries passed. |
| `git ls-files runs` | Passed; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | Passed; output empty. |

## Artifact Policy

- No raw data, canonical data, feature values, label values, provider responses,
  Parquet/Arrow/Feather/DBN/Zstd files, SQLite/DB files, logs, caches, or
  secrets were authored.
- The committed artifacts are markdown-only and value-free.
- The executor did not run `git add`, `git commit`, `git push`, `git status`, or
  `git diff`.
- The executor did not call Claude, run a reviewer, create `review.md`, create
  `verdict.json`, create a PR, merge, or mark the phase PASS.

## Notes

- The generated spec path named in the prompt,
  `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P15.md`, was not
  present in this worktree. The executor used the generated spec text supplied
  in the prompt.
- The run-local directory named in the prompt,
  `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P15`,
  was not present in this worktree. No run-local handoff was written.
