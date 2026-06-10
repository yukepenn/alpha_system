# FUTSUB-P18 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P18`  
Lane: Yellow  
Executor: Codex

## Scope Completed

Materialized and registered the `session_close` and `maintenance_flat` close-out LabelPacks for ES/NQ/RTY across the accepted year inventory, excluding blocked 2018 and including the warned 2019 and partial 2026 units. Execution used the scaleout label-pack dispatch into `cli.seed_pack.run_seed_label_pack`; no fast label worker path, direct registry mutation, new label family, or label-engine rewrite was added.

The close-out support is implemented as fixed-horizon family close-out labels with symbolic horizons and the existing shared guarded terminal path.

## Files For Ralph To Stage Explicitly

- `README.md`
- `configs/labels/scaleout/session_close_maintenance_flat.json`
- `research/futures_substrate_scaleout_v1/label_packs/session_close_maintenance_flat/coverage_summary.md`
- `src/alpha_system/cli/seed_pack.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/futures_substrate_scaleout/labels/test_session_close_scaleout.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P18.md`

No `runs/**`, Parquet, SQLite, DB, Arrow, Feather, DBN, Zstandard, raw provider, roll-calendar, checkpoint, or registry artifact is commit-eligible.

## Close-Out Semantics Used

- `session_close`: terminal is the same-contract RTH close-out bar for the source bar's CME trade date, selected by the explicit 08:30-15:00 America/Chicago RTH clock boundary. A source row at or after the terminal has no remaining same-session horizon and is dropped.
- `maintenance_flat`: terminal is the same-contract last bar at or before the 16:00 America/Chicago daily maintenance / trade-date break. A source row at or after the terminal has no remaining same-break horizon and is dropped.
- Terminal lookup is contract-scoped and break-scoped: `series_id+contract_id+event_ts` for the terminal key and `series_id+contract_id+close_out_boundary` for close-out scope.
- `label_available_ts` is derived from the selected terminal row availability and is present on every materialized label.

## Guard Results

The shared fixed-horizon guarded terminal path was reused. The implementation calls the existing roll/maintenance guard plumbing rather than forking label compute. Roll-crossing policy is `drop` under `roll_guard_v1`; maintenance-crossing policy is `drop` under `maintenance_crossing_guard_v1`.

Aggregate value-free guard and coverage counts:

| Horizon | Units | Input rows | Candidate terminals | Rows materialized | Boundary dropped | Maintenance dropped | Roll dropped | Roll flagged | Roll truncated | Effective samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `session_close` | 24 | 7,683,710 | 7,369,395 | 7,248,193 | 314,315 | 0 | 121,202 | 0 | 0 | 5,598 |
| `maintenance_flat` | 24 | 7,683,710 | 7,678,019 | 7,552,054 | 5,691 | 0 | 125,965 | 0 | 0 | 5,604 |

The full per symbol x year x horizon table, including DatasetVersion id, acceptance state, row count, effective samples, boundary-dropped count, maintenance-dropped count, and roll-dropped count, is recorded in `research/futures_substrate_scaleout_v1/label_packs/session_close_maintenance_flat/coverage_summary.md`.

## Materialization Results

All materialization commands were run with:

```bash
source ~/.venvs/alpha_system_research/bin/activate
export PYTHONPATH=src
export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system
```

`PYTHONPATH=src` was required because the research venv editable install otherwise imported `/home/yuke_zhang/projects/alpha_system/src` rather than this P18 worktree.

Dry-run identity preview:

```bash
python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/session_close_maintenance_flat.json --dry-run --rollout full-window --json
```

Outcome: passed. Planned `48` accepted units, `6` bounded-real units, `0` failed units, engine `reference`.

Bounded-real first pass:

```bash
python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/session_close_maintenance_flat.json --execute --rollout bounded-real --bounded-year 2024 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --json
```

Initial outcome before the session-close terminal repair: failed with `3` completed and `3` failed because session-close registration had no materialized `LabelValueRecord`s. Cause was an overly narrow RTH session-label predicate on real canonical rows around the close. Repair switched terminal selection to the explicit America/Chicago RTH clock boundary while preserving contract and break scope. Final bounded-real rerun outcome: passed with `3` completed, `3` skipped from prior registry/checkpoint evidence, `0` failed.

Full-window execution:

```bash
python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/session_close_maintenance_flat.json --execute --rollout full-window --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --json
```

Outcome: passed. Completed `42`, skipped `6` bounded-real units from registry/checkpoint evidence, failed `0`. The completed marker set contains all `48` label units.

Registry evidence checked for the coverage report:

- Required registry fields present for `48` / `48` label records: `value_store_format`, `parquet_path`, `value_content_hash`, `value_schema_version`, `dataset_version_id`, `label_version_id`.
- Registry records with `label_available_ts` ranges: `48` / `48`.
- Storage is Parquet-first under `ALPHA_DATA_ROOT`; no label values or registries are committed.
- Checkpoint/restart behavior was exercised by bounded-real skips and full-window skips.
- Registry writes remained serial through the label-pack driver.

## Accepted Window Notes

- Accepted states included: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`.
- Accepted state counts: `36` `ACCEPTED`, `12` `ACCEPTED_WITH_WARNINGS`.
- `2018` remains blocked and excluded per `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.
- `2019` and `2026` are included as warned units; `2026` is partial-year.

## Validation

All validation commands below were run from the repository root.

```bash
source ~/.venvs/alpha_system_research/bin/activate && export PYTHONPATH=src && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python tools/verify.py --smoke
```

Outcome: passed with exit code `0`.

```bash
source ~/.venvs/alpha_system_research/bin/activate && export PYTHONPATH=src && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python -m pytest tests/unit/futures_substrate_scaleout/labels/test_session_close_scaleout.py -q
```

Outcome: passed, `3 passed in 0.32s`.

```bash
source ~/.venvs/alpha_system_research/bin/activate && export PYTHONPATH=src && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python tools/hooks/canary_runner.py
```

Outcome: passed; all Frontier canaries passed.

```bash
test -f configs/labels/scaleout/session_close_maintenance_flat.json
```

Outcome: passed.

```bash
test -d research/futures_substrate_scaleout_v1/label_packs/session_close_maintenance_flat
```

Outcome: passed.

```bash
git ls-files runs
```

Outcome: passed; output was empty.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'
```

Outcome: passed; output was empty.

Spec validation also listed `git status --short`, but the executor prompt explicitly forbade running `git status`; it was not run. No staging validation was run because the executor prompt also forbade staging and commits. Ralph owns staging and the staged-set audit.

## Local-Only / Not Run

- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.
- No Claude call, reviewer run, `review.md`, or `verdict.json` was created.
- No PR, CI wait, merge gate, merge, or PASS marking was initiated.
- No run-local handoff was written under `runs/**`; this commit-eligible handoff is the execution handoff.
