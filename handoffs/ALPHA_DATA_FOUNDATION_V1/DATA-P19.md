# DATA-P19 Handoff - Micro Batch Policy for MES/MNQ/M2K

## Scope Executed

Implemented `MicroBatchPolicy` in
`src/alpha_system/data/foundation/batches.py` as a frozen, fail-closed planning
record with exactly these required fields:

- `batch_id`
- `symbols`
- `start_date`
- `separate_batch`
- `parity_check_targets`

The canonical policy is exposed as `MICRO_BATCH_POLICY`, and the declarative
secondary micro-batch plan is exposed as `MICRO_BATCH_PLAN`.

## Mini/Micro Separation

`symbols` must equal `("MES", "MNQ", "M2K")`. Validation rejects any mini root
from `ES/NQ/RTY`, rejects partial or duplicate micro sets, and requires
`separate_batch = true`.

`MicroBatchPolicy.validate_batch_roots(...)` and
`MicroBatchPolicy.validate_manifest_roots(...)` reject mini roots in micro
batches/manifests and require the canonical MES/MNQ/M2K micro set. The policy
references the DATA-P10 `SymbolBatchPlan` separation contract:
`do_not_mix_mini_and_micro_batches = true` and `max_concurrent_roots = 3`.

## DATA-P05 And Parity References

`MICRO_BATCH_PLAN` references the DATA-P05 `InstrumentMasterRecord` economics
for `MES`, `MNQ`, and `M2K` without duplicating point values, tick sizes, tick
values, multipliers, or certification state.

The parity-check targets are declarations only:

- `ES -> MES`
- `NQ -> MNQ`
- `RTY -> M2K`

Validation rejects missing, duplicated, reversed, non-canonical, or result-like
parity target records. No parity result or parity conclusion is encoded.

## Start Date Default

The canonical `start_date` is `2020-01-01`. It is documented in
`docs/data_foundation/MICRO_BATCH.md` as a to-be-verified planning default, not
a data-availability, coverage, quality, or provider-support claim. The policy
also admits the explicit marker `earliest_clean_available_to_be_verified` for a
future verified availability workflow.

## Docs And README

Added `docs/data_foundation/MICRO_BATCH.md` documenting the micro batch policy,
the separate-batch guarantee, DATA-P05/DATA-P10 references, declaration-only
parity targets, the to-be-verified start-date default, and that micros are not a
primary alpha source in V1.

Updated the root `README.md` snapshot for `secondary_data_tracks`, DATA-P19
executor-scope completion, next phase `DATA-P20`, the new `MicroBatchPolicy`
object, and unchanged safety boundaries. No run-local paths or generated run
details were added.

No synthetic fixture was needed; unit tests exercise the policy with in-test
fake dictionaries only.

## Explicit Staging Status

Intended explicit staged set:

- `README.md`
- `docs/data_foundation/MICRO_BATCH.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P19.md`
- `src/alpha_system/data/foundation/batches.py`
- `tests/unit/data/test_micro_batch_policy.py`

The exact explicit staging command attempted was:

```bash
git add README.md docs/data_foundation/MICRO_BATCH.md handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P19.md src/alpha_system/data/foundation/batches.py tests/unit/data/test_micro_batch_policy.py
```

The command failed because this executor sandbox has `.git` mounted read-only:

```text
fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/index.lock': Read-only file system
```

Actual `git diff --cached --name-only` output is empty. No `runs/` path or
forbidden artifact path is staged. `git add .` and `git add -A` were not used.

## Validation Results

- `git status --short` - passed; final worktree changes were only the DATA-P19
  source, test, doc, README, and handoff files listed above.
- `python tools/verify.py --smoke` - passed with no output.
- `python -m pytest tests/unit/data -q` - passed: `315 passed in 0.25s`.
- `test -f docs/data_foundation/MICRO_BATCH.md` - passed.
- `git ls-files runs` - passed with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - passed
  with empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - passed
  with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - passed
  with empty output.
- `git diff --cached --name-only` - passed with empty output after the
  read-only `.git` staging failure.

Additional local sanity checks run during implementation also passed:

- `python -m pytest tests/unit/data/test_micro_batch_policy.py -q` -
  `5 passed`.
- `python -m pytest tests/unit/data/test_mini_batch_plan.py -q` - `6 passed`.
- `python -m ruff check src/alpha_system/data/foundation/batches.py tests/unit/data/test_micro_batch_policy.py`
  - passed.
- `python -m compileall -q src/alpha_system/data/foundation/batches.py tests/unit/data/test_micro_batch_policy.py`
  - passed.
- `git diff --check` - passed.

No required or supplementary checks were skipped.

## Artifact And Safety Confirmation

`runs/**` remains local-only; no run-local handoff, review, verdict, or repair
artifact was staged. `git ls-files runs` returned empty. Explicit staging was
attempted for curated paths only, but the sandbox blocked index writes because
`.git` is read-only. `git add .` and `git add -A` were not used.

No raw data, canonical data, factor data, label data, cache data, provider
response, account artifact, SQLite/DB/journal/WAL file, Parquet/Arrow/Feather
file, log, model artifact, heavy artifact, secret, or credential was created or
staged.

No external provider pull, IBKR connection, manifest pull, raw write,
canonical write, broker operation, live trading, paper trading, order routing,
account access, real-time feed, production deployment, PR creation, merge,
reviewer invocation, `review.md`, `verdict.json`, or phase PASS marking was
performed.

No alpha research, factor research, label research, strategy work,
profitability claim, tradability claim, or production-readiness claim was
introduced. Micros are documented only as a separate secondary path and not a
primary alpha source in V1.

Ralph owns handoff validation, independent Yellow review, verdict parsing,
semantic done-check, PR, CI, merge gate, merge, and final phase outcome.
