# FUTSUB-P21 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P21` - Roll-Splice and Maintenance-Crossing Label Guard Audit  
Executor outcome: `READY_FOR_REVIEW_NO_SILENT_CROSSINGS_FOUND`

## Files For Ralph To Stage

Leave unstaged for Ralph; executor did not stage or commit anything:

- `README.md`
- `docs/futures_substrate_scaleout/ROLL_GUARD_AUDIT.md`
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`
- `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md`
- `tests/unit/futures_substrate_scaleout/labels/test_roll_maintenance_guard_audit.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P21.md`

No `reviews/**`, run-local `review.md`, run-local `verdict.json`, PR, merge,
staging, commit, or push was created by the executor.

## Audit Method

- STOP check: the prompted run path had no `STOP` file in this worktree. The
  `runs/` directory itself is absent here, so no run-local handoff/review/
  verdict artifact was written.
- Registry metadata was read through `alpha label list --json --alpha-data-root
  /home/yuke_zhang/alpha_data/alpha_system` and
  `LabelRegistry.from_alpha_data_root(...).read_label_records()`.
- Materialized value metadata was checked through registry `value_record_count`,
  value-store manifests, and bounded `alpha_system.core.value_store` sample
  reads.
- Missing dropped-window counts were recomputed read-only from already-canonical
  local OHLCV/BBO timestamp rows via
  `alpha_system.data.foundation.canonical_loader`. No raw provider path was
  read and no provider call was made.
- Roll boundaries use the analytic approximate CME quarterly calendar from
  `docs/futures_substrate_scaleout/ROLL_GUARD.md`: third-Friday expiration,
  roll date eight calendar days before expiration, roll-window split two days
  before / one day after. This is not provider-exact splice truth.
- Drop counts for `extended_horizon`, `session_close_maintenance_flat`, and
  `path` were reused from the committed value-free materialization summaries /
  matrices and cross-checked against current local registry metadata.
- No registry write, value materialization, re-materialization, source-code edit,
  `src/**` edit, provider call, raw provider read, paper/live/broker/order
  operation, PR creation, or merge was performed.

## Policy And Registry Accounting

All current local registry records in the audit surface record
`roll_policy_id=roll_cme_index_futures_quarterly`,
`roll_guard_version=roll_guard_v1`, `roll_cross_policy=drop`,
`maintenance_policy_id=cme_index_futures_daily_maintenance_break_v1`,
`maintenance_guard_version=maintenance_crossing_guard_v1`, and
`maintenance_crossing_policy=drop`.

| Family | Active unique label-version units | Emitted label rows | Producer provenance observed |
| --- | ---: | ---: | --- |
| `fixed_horizon` | 144 | 44,505,301 | `alpha_system.labels.fast.pack_materializer.v1`; `alpha_system.labels.reference_engine.v1` |
| `extended_horizon` | 72 | 20,126,303 | `alpha_system.labels.reference_engine.v1` |
| `session_close_maintenance_flat` | 48 | 14,800,247 | `alpha_system.labels.reference_engine.v1` |
| `cost_adjusted` | 432 | 134,264,936 | `alpha_system.labels.reference_engine.v1` |
| `path` | 672 | 200,973,356 | `alpha_system.labels.fast.pack_materializer.v1` |

The current local registry has 2,325 label records. The fixed-horizon base
family exposes 145 raw records and 144 active unique records because the prior
repair deprecated duplicate `ES_2024_fwd_ret_5m`. The older P16 coverage
summary prose in this worktree still describes the pre-repair bounded run; this
audit treats that prose as stale and relies on registry/value metadata instead.
This is recorded as a non-blocking documentation discrepancy.

## Verification Results

The full per-family x symbol x year verification results are recorded in:

- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`

Aggregate disposition counts from those matrices:

| Family | Roll-overlap windows dropped | Maintenance-overlap windows dropped | Close-out boundary drops | Truncated | Flagged | Invalid | Silently measured |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_horizon` | 708,172 | 353,333 | 0 | 0 | 0 | 0 | 0 |
| `extended_horizon` | 334,684 | 986,770 | 0 | 0 | 0 | 0 | 0 |
| `session_close_maintenance_flat` | 247,167 | 0 | 320,006 | 0 | 0 | 0 | 0 |
| `cost_adjusted` | 2,096,436 | 5,187,270 | 0 | 0 | 0 | 0 | 0 |
| `path` | 810,951 | 2,720,160 | 0 | 0 | 0 | 0 | 0 |

Cost-adjusted counts are on the emitted label-version surface across the two
cost labels. Session-close / maintenance-flat labels use close-out boundary
semantics and do not measure forward returns across the maintenance break.

## Demonstrations

Known roll week: the chosen approximate boundary is the 2024 June CME
equity-index analytic roll date, `2024-06-13`. In the ES 2024 read-only local
canonical timestamp drill, the `2024-06-12T23:30:00+00:00` to
`2024-06-13T00:00:00+00:00` slice produced 64 fixed-horizon roll-crossing
windows and 308 cost-adjusted label-surface roll-crossing windows. Adjacent
fixed-horizon non-crossing windows in `2024-06-12T22:30:00+00:00` to
`2024-06-12T23:00:00+00:00` were counted as 180 non-crossing windows and were
not over-dropped.

Known maintenance break: the chosen ordinary break is January 2, 2024 at 16:00
America/Chicago (`2024-01-02T22:00:00+00:00`). In the ES 2024 read-only local
canonical timestamp drill, the `2024-01-02T21:30:00+00:00` to
`2024-01-02T22:00:00+00:00` slice produced 58 fixed-horizon maintenance
crossings and 296 cost-adjusted label-surface maintenance crossings. Adjacent
fixed-horizon non-crossing windows in `2024-01-02T20:30:00+00:00` to
`2024-01-02T21:00:00+00:00` were counted as 180 non-crossing windows and were
not over-dropped.

## Prior Repair Evidence Consumed

- Fixed-horizon INPUT_GAP repair: consumed from current local registry truth.
  The active base fixed-horizon surface is 144 unique label-version units across
  ES/NQ/RTY and 2019-2026; the deprecated duplicate
  `ES_2024_fwd_ret_5m` is excluded.
- Cost-adjusted COUNT_GAP repair: recomputed with read-only canonical BBO
  timestamp enumeration because dropped windows are not emitted rows. The
  matrix now records roll and maintenance drop counts for the current 432-label
  cost-adjusted surface.
- Reused rather than recomputed: P17/P18/P20 value-free drop counts from their
  committed summaries/matrices.

## Value-Store Samples

Bounded read-only samples through `alpha_system.core.value_store` confirmed
manifest/readability consistency and zero emitted roll/maintenance guard flags.
Dropped windows are not emitted rows, so these samples complement the matrix
count enumeration.

| Family | Sample | Registry rows | Manifest rows | Loaded rows | Emitted roll/maintenance guard-flag rows |
| --- | --- | ---: | ---: | ---: | ---: |
| `fixed_horizon` | `fwd_ret_30m` / `ES_2024_fwd_ret_30m` | 333,575 | 333,575 | 333,575 | 0 |
| `extended_horizon` | `fwd_ret_240m` / `ES_2024_fwd_ret_240m` | 281,318 | 281,318 | 281,318 | 0 |
| `session_close_maintenance_flat` | `maintenance_flat` / `ES_2024_maintenance_flat` | 340,740 | 340,740 | 340,740 | 0 |
| `cost_adjusted` | `cost_adjusted_fwd_ret` / `ES_2024_240m` | 306,903 | 613,806 | 613,806 | 0 |
| `path` | `path_mfe` / `ES_2024_240m` | 281,468 | 1,125,872 | 1,125,872 | 0 |

## Findings

- Blocking findings from this executor audit: none.
- Non-blocking finding: stale P16 fixed-horizon coverage-summary prose relative
  to current local registry truth. The audit evidence does not rely on that
  prose.
- No missing or inconsistent guard policy/version id was found in current local
  registry metadata.
- No silently measured roll-splice or maintenance-crossing window was found in
  the matrix evidence, demonstration slices, or value-store samples.

## Repair Attempt 1

Review found stale 2024 all-symbol aggregate prose in
`research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md`. The
matrices were the authoritative final enumeration and were internally
consistent; the evidence note was wrong because those three values came from an
earlier enumeration pass. This repair corrected the evidence note to match the
final matrix sums:

- fixed-horizon 2024 roll drops: 97,966.
- cost-adjusted 2024 roll drops: 289,370.
- cost-adjusted 2024 maintenance drops: 722,942.

Reconciliation check: both matrices were parsed and re-summed by family. The
all-year aggregate rows in this handoff,
`docs/futures_substrate_scaleout/ROLL_GUARD_AUDIT.md`, and
`research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md` match
the final matrix sums for roll drops, maintenance drops, close-out boundary
drops, and zero silently measured crossings. The 2024 all-symbol roll and
maintenance prose in the evidence note now matches the final matrix row sums:
roll drops 97,966 / 46,153 / 33,989 / 289,370 / 112,061 and maintenance drops
or close-out stops 47,731 / 137,016 / 46,287 / 722,942 / 361,440 for
fixed-horizon, extended-horizon, session-close / maintenance-flat,
cost-adjusted, and path respectively.

## Validation

- `python tools/frontier/status_doctor.py`: exit 0 with `VERDICT: WARN` because
  `core.hooksPath` is not `.githooks` and no live run dir with `state.json` was
  present for this campaign. No live run state or STOP condition was found in
  this worktree.
- `git status --short`: exit 0; showed the expected seven phase files only
  (`README.md` modified plus the six untracked commit-eligible audit/test/
  handoff files), with no `runs/**` or `reviews/**` path.
- `python - <<'PY' ...parse roll and maintenance matrices; assert all-year
  family sums and 2024 all-symbol family sums... PY`: passed,
  `matrix reconciliation passed`.
- `python - <<'PY' ...generate stale comma-formatted values from 99966,
  293568, and 722420; scan the audit note, durable doc, handoff, and matrices...
  PY`: passed, `stale-value scan passed`.
- `source /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && python tools/verify.py --smoke`:
  passed, exit 0, no output.
- `source /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/labels/test_roll_maintenance_guard_audit.py -q`:
  passed, `4 passed in 0.10s`.
- `source /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && python tools/hooks/canary_runner.py`:
  passed, all Frontier canaries passed.
- `test -f research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md && test -f research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md && test -f docs/futures_substrate_scaleout/ROLL_GUARD_AUDIT.md`:
  passed, exit 0.
- `git ls-files runs`: passed, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`:
  passed, empty output.
- `git diff --cached --name-only`: passed, empty output; no staged paths and no
  staged `runs/**` path.
- `grep -rn "polars\|value_store\|seed_pack\|data.storage" tests/unit/futures_substrate_scaleout/labels/test_roll_maintenance_guard_audit.py`:
  exit 1 / no output, expected because the synthetic test does not import the
  polars data layer or value-store/seed-pack modules.
- `grep -n "importorskip" tests/unit/futures_substrate_scaleout/labels/test_roll_maintenance_guard_audit.py`:
  exit 1 / no output. `pytest.importorskip("polars")` is not required because
  the test is pure guard logic and does not touch the polars data layer.

## Test Hygiene

The modified test file was grepped for `polars`, `value_store`, `seed_pack`,
and `data.storage`; there were no matches. It therefore does not need
`pytest.importorskip("polars")`, and no pure-compute test was blanket-skipped.
The test now mirrors the production guard order by classifying maintenance
crossings before roll crossings.

## Artifact Policy

No value, registry, raw provider, SQLite, roll-calendar data, Parquet, Arrow,
Feather, DBN, Zstd, log, cache, or run artifact was written into
commit-eligible paths. `runs/**` remains local-only; no run-local handoff,
review, or verdict artifact was created by the executor. `git ls-files runs`
and the heavy-artifact glob both returned empty.
