# FUTSUB-P19 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P19`  
Family: `cost_adjusted`  
Executor: Codex  
Date: `2026-06-11`

## Ralph Staging List

Executor left all changes unstaged. If Ralph stages this phase, stage only these
commit-eligible paths:

- `README.md`
- `configs/labels/scaleout/cost_adjusted.json`
- `research/futures_substrate_scaleout_v1/label_packs/cost_adjusted/coverage_summary.md`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/labels/families/cost_adjusted/family.py`
- `tests/unit/futures_substrate_scaleout/labels/test_cost_adjusted_scaleout.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P19.md`

No `runs/**`, Parquet, SQLite, DB, Arrow, Feather, DBN, ZST, log, cache, or
provider payload was staged or committed by the executor.

## Scope Completed

- Reused the official scaleout label-mode dispatch and reference label engine.
- Kept this family off the V1 fast label producer path.
- Added partition-scoped materialization scope to cost-adjusted label contracts
  so `label_version_id` differs by symbol/year/horizon/window while still
  excluding producer provenance.
- Corrected cost-adjusted scaleout registry metadata to record the actual
  terminal contract: `series_id+contract_id+bar_end_ts` and
  `bar_end_aligned_bbo_proxy`.
- Materialized and registered the current cost-adjusted accepted grid:
  `216` units, `432` label versions, ES/NQ/RTY, years 2019-2026, horizons
  `1m/3m/5m/10m/15m/30m/60m/120m/240m`.
- Preserved checkpoint/restart discipline. The old unscoped P19 label-version
  progress was treated as superseded by the partition-scoped identity repair;
  the current full run then skipped the bounded serial `ES`/`2024` units from
  checkpoint + registry truth.

## Materialization Commands

Bounded serial validation:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=1 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/cost_adjusted.json --execute --rollout full-window --symbols ES --years 2024 --engine reference --workers 1 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --summary-out /tmp/futsub_p19_es2024_serial_summary.md --json
```

Outcome: exit `0`; completed `9`, skipped `0`, failed `0`; force recompute
`false`; engine `reference`; requested/effective workers `1`.

Full accepted-window resume:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=8 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/cost_adjusted.json --execute --rollout full-window --engine reference --workers 8 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --summary-out research/futures_substrate_scaleout_v1/label_packs/cost_adjusted/coverage_summary.md --json
```

Outcome: exit `0`; completed `207`, skipped `9`, failed `0`; accepted unit
count `216`; bounded unit count `27`; requested workers `8`; effective workers
`8`; threads per worker `2`; no worker reductions; force recompute `false`.
The only stderr output was repeated Python `runpy` warnings from child
interpreters.

Registration stayed parent-only serial. Worker-computed units were registered
with messages of the form `worker compute registered by serial writer`.

## Resume / Coverage Accounting

Current registry + checkpoint truth:

- Current completed units: `216`.
- Remaining or stale units under current identity: `0`.
- Completed by symbol: `ES=72`, `NQ=72`, `RTY=72`.
- Completed by year: `2019=27`, `2020=27`, `2021=27`, `2022=27`, `2023=27`,
  `2024=27`, `2025=27`, `2026=27`.
- Accepted-state units: `ACCEPTED=162`, `ACCEPTED_WITH_WARNINGS=54`.
- `2018` excluded as `BLOCKED`; reference:
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.

Value-free aggregate scan of current outputs:

- Label rows scanned: `134264936`.
- `label_available_ts` null rows: `0`.
- Gap rows (`label_gap`): `5045570`.
- `missing_terminal_bbo`: `5001728`.
- `entry_bbo_gap`: `22322`.
- `terminal_bbo_gap`: `21520`.
- `missing_bbo` surfaced in BBO gap flags: `43842`.
- Guard-flagged emitted rows: `0`.

The coverage summary records per symbol-year coverage and horizon-level
overlap-aware N_eff. Effective N is conservatively reported as
`floor(row_count / horizon_minutes)` at one-minute sampling; rows are not
claimed independent.

## Cost / Fee / Slippage Assumptions

- Label cost model version: `cost_adjusted_reference_v1`.
- `cost_adjusted_fwd_ret`: existing governed `spread_plus_bps` model,
  `fixed_cost_bps=0.25`, `spread_adjustment=half_spread_round_trip`.
- `spread_adjusted_fwd_ret`: existing governed `spread_adjusted` model,
  `fixed_cost_bps=0`, `spread_adjustment=half_spread_round_trip`.
- Mid-to-mid is the internal BBO gross forward-return terminal used before
  subtracting governed cost components; it is not emitted as a separate P19
  label id.
- Slippage-stress-adjusted output is unsupported by the current sanctioned
  `cost_adjusted` label contract and was not fabricated.
- Sanctioned cost context remains documented in
  `configs/labels/scaleout/cost_adjusted.json`: `default_conservative` and
  `spread_sensitive_conservative`, both `engine_version=reference_1min_v1`.

BBO-1m spreads are treated strictly as a time-sampled, forward-filled
tradability proxy, not execution truth. No passive-fill, queue-priority,
intra-minute-impact, execution-quality, profitability, or production claim is
made.

## Guard / Identity / Registry Evidence

- Shared FUTSUB-P16 roll-splice and maintenance-crossing guard wiring is reused
  through `_guarded_forward_terminal`; no forked guard was introduced.
- Guard policy is `drop`, so dropped roll/maintenance windows are not emitted as
  label rows. The focused synthetic P19 test covers both drop paths; the
  materialized outputs have zero emitted guard-flag rows. FUTSUB-P21 owns the
  full guard matrix audit.
- Current registry check covered all `432` label versions. Required fields were
  present for every current label version: `value_store_format`, `parquet_path`,
  `value_content_hash`, `value_schema_version`, `dataset_version_id`,
  `label_version_id`.
- `value_store_format=parquet` for all current label versions.
- `producer_engine_id=alpha_system.labels.reference_engine.v1` for all current
  label versions.
- `label_version_id` does not encode `producer_engine_id`.

## Validation

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke
```

Outcome: exit `0`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels/test_cost_adjusted_scaleout.py -q
```

Outcome: exit `0`; `12 passed in 0.29s`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/labels/families/cost_adjusted/test_cost_adjusted_family.py -q
```

Outcome: exit `0`; `6 passed in 0.12s`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py
```

Outcome: exit `0`; all Frontier canaries passed.

Run:

```bash
test -f configs/labels/scaleout/cost_adjusted.json && test -d research/futures_substrate_scaleout_v1/label_packs/cost_adjusted
```

Outcome: exit `0`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m json.tool configs/labels/scaleout/cost_adjusted.json
```

Outcome: exit `0`.

Run:

```bash
git ls-files runs
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'
```

Outcome: both commands returned empty output.

Not run:

- `git status --short`: executor prompt explicitly forbade `git status`.
- `git diff --cached --name-only`: Codex did not stage anything and the prompt
  forbade `git diff`.
- Reviewer / Claude / `review.md` / `verdict.json`: not run or created per
  executor instructions.

## Local-Only Artifacts

- Materialized cost-adjusted label values, manifests, checkpoints, and
  `registry/labels.sqlite` updates are local-only under
  `/home/yuke_zhang/alpha_data/alpha_system`.
- Command captures and aggregate scratch files were written under `/tmp`.
- No run-local `runs/<run_id>/phases/FUTSUB-P19/handoff.md` was created.

## Executor Boundary

- Did not call Claude.
- Did not run reviewer.
- Did not create `review.md`.
- Did not create `verdict.json`.
- Did not create a PR.
- Did not merge.
- Did not mark the phase PASS.
- Did not run `git add`, `git commit`, `git push`, `git status`, or `git diff`.
- Did not stage or commit anything under `runs/`.
