# P094500_DAMAGED_PACK_RESTORE_PLAN Handoff

Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
Phase: `P094500_DAMAGED_PACK_RESTORE_PLAN`
Lane: Yellow
Executor: Codex

## Status

Partial completion with blocking findings. I reconstructed the 408 active stale
FeatureVersion rows, added repair union configs and a value-free audit tool, and
ran the ES_2019 BBO proof through the sanctioned scaleout CLI. Session and
regime were not executed because their current dry-runs do not target the
baseline stale fvers.

## Artifacts

- Runbook: `research/futures_substrate_scaleout_v1/repair/PACK_RESTORE_RUNBOOK.md`
- Provenance Markdown table: `research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md`
- Pre-audit summary: `research/futures_substrate_scaleout_v1/repair/damaged_pack_pre_audit.md`
- ES_2019 proof Markdown table: `research/futures_substrate_scaleout_v1/repair/ES_2019_proof_results.md`
- ES_2019 post-proof summary: `research/futures_substrate_scaleout_v1/repair/ES_2019_post_proof_audit.md`
- Post-BBO proof audit: `research/futures_substrate_scaleout_v1/repair/damaged_pack_post_bbo_proof_audit.md`
- Audit tool: `tools/futures_substrate_scaleout/pack_restore_audit.py`
- Repair configs under `configs/features/scaleout/repair/`

## Provenance

Registry reads used Python stdlib SQLite with `file:...?mode=ro` because the
`sqlite3` shell binary is not installed in this environment. Active
`REGISTERED` stale rows matched the expected 408:

| Family | Active rows | Disk-present/hash-identical | Stale |
| --- | ---: | ---: | ---: |
| `session_calendar_maintenance` | 240 | 120 | 120 |
| `regime_volatility_compression` | 120 | 72 | 48 |
| `bbo_tradability_top_book` | 264 | 24 | 240 |

Every stale row is attributed in the provenance Markdown table with `feature_request_id`,
`materialization_plan_id`, producing phase, config path, repair config, command
template, and baseline `value_content_hash`.

## Proof Result

ES_2019 baseline stale rows:

| Family | Baseline stale fvers | Present after proof | Baseline hash identity | Current registry hash identity |
| --- | ---: | ---: | ---: | ---: |
| `session_calendar_maintenance` | 5 | 0 | 0 | 0 |
| `regime_volatility_compression` | 2 | 0 | 0 | 0 |
| `bbo_tradability_top_book` | 10 | 10 | 0 | 10 |

BBO proof command completed in `97.64` seconds and wrote only the ES_2019 BBO
pack via:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src ~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/repair/bbo_tradability_top_book_union_restore.json --rollout full-window --execute --force-recompute --symbols ES --years 2019 --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --json
```

The BBO proof made the 10 baseline stale ES_2019 fvers disk-present, but their
baseline hash was `sha256:da3ae4b38572266ff0f71f52945d05e3faecdd3d9951000e91a1bba91e99bbf0`
and the current full-pack hash is
`sha256:fd92da6790af4d95cea1f649e5f90164982c87a4eb409b1cbb313d923440645d`.
This confirms the expected BBO re-lock requirement.

## Blocking Findings

1. `session_calendar_maintenance` cannot be restored through the current union
   CLI: the 10-name union config fails dry-run because `bars_to_roll` and
   `minutes_to_roll` are now rejected as offline/non-causal.
2. The current 8-name session config also previews replacement fvers for
   `day_of_week`, `minutes_to_expiration`, and `halt_status_flag`; it does not
   target the baseline stale fvers.
3. `regime_volatility_compression` cannot restore the two baseline stale ES_2019
   fvers through the current CLI: dry-run previews replacement fvers for
   `range_expansion` and `momentum_reversion_state`.
4. The V1 serial execute path ignored `--force-recompute` for one-unit runs. I
   fixed that narrowly in `src/alpha_system/features/scaleout/driver.py` and
   added a unit regression test.

## Validation

| Command | Result |
| --- | --- |
| `PYTHONPATH=src python -m py_compile src/alpha_system/features/scaleout/driver.py tools/futures_substrate_scaleout/pack_restore_audit.py` | PASS |
| `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py -q` | PASS, `3 passed` |
| `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q` | PASS, `133 passed` |
| `PYTHONPATH=src ~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --partition ES_2019_full_year --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md --proof-out /tmp/P094500_ES_2019_proof_results.md` | PASS in repair validation below; verifies Markdown baseline input without modifying committed proof evidence. |
| `PYTHONPATH=src python tools/hooks/canary_runner.py` | PASS |
| `PYTHONPATH=src python tools/verify.py --smoke` | PASS |
| `env PYTHONPATH=/home/yuke_zhang/projects/alpha_system-wf1-pack-restore/src PATH=/home/yuke_zhang/.venvs/alpha_system_ci/bin:$PATH just ci-parity` | Historical pre-repair ENV COMMAND ERROR before `just`: inherited WSL PATH split on `Zhang/AppData/...`; superseded by repair rerun below. |
| `PYTHONPATH=/home/yuke_zhang/projects/alpha_system-wf1-pack-restore/src PATH="/home/yuke_zhang/.venvs/alpha_system_ci/bin:$PATH" just ci-parity` | Historical pre-repair claim superseded by repair rerun below; reviewer proved this final committed tree was CI-red because the CSVs were tracked. |

## Bounded Repair Update

Repair date: 2026-06-12.

- Converted the two tracked repair CSV artifacts to value-free Markdown tables
  with the same columns: `damaged_pack_provenance.md` has `408` rows;
  `ES_2019_proof_results.md` has `17` rows.
- Updated `tools/futures_substrate_scaleout/pack_restore_audit.py` so `.md`
  output paths write Markdown tables and `--baseline-provenance` can read the
  committed Markdown provenance table. CSV remains available for local scratch
  outputs only.
- Updated the runbook to state that full BBO re-materialization runs after the
  P085901 bar-grid fix from PR #401, now merged on `origin/main`, and that this
  post-grid-fix run supersedes the pre-fix ES_2019 proof content before
  `sspec_6088f0` re-lock.
- Added the deprecate-first step to the runbook: `168` unrestorable
  `REGISTERED` fvers must be deprecated through `FeatureStore.deprecate_feature`
  / `FeatureRegistry.deprecate_feature` before session/regime full-grid
  re-materialization (`48` R-036 countdown rows, `72` session
  transform-parameter migration rows, `48` regime transform-parameter migration
  rows). The runbook cites the P235500 data-op mechanism and records exact API
  command templates; manual SQLite edits remain forbidden.
- Removed the two CSV files from the staged tree and staged the Markdown
  replacements explicitly. `git ls-files` now reports the repair `.md` artifacts
  and no repair `.csv` artifacts.

### Repair Validation

| Command | Result |
| --- | --- |
| `PYTHONPATH=src ~/.venvs/alpha_system_research/bin/python -m py_compile tools/futures_substrate_scaleout/pack_restore_audit.py` | PASS |
| `PYTHONPATH=src ~/.venvs/alpha_system_research/bin/python tools/futures_substrate_scaleout/pack_restore_audit.py --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --partition ES_2019_full_year --baseline-provenance research/futures_substrate_scaleout_v1/repair/damaged_pack_provenance.md --proof-out /tmp/P094500_ES_2019_proof_results.md` | PASS; Markdown baseline parsed and emitted a `17`-row scratch proof table. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q` | PASS, `133 passed in 23.91s` |
| `python tools/hooks/canary_runner.py` | PASS, all Frontier canaries passed. |
| `python tools/verify.py --smoke` | PASS, exit code `0`. |
| `PYTHONPATH=$PWD/src PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" ~/.venvs/alpha_system_ci/bin/python -m pytest tests/integration/test_no_generated_data_committed.py -q` | PASS, `1 passed in 0.02s`; confirms the staged tree no longer tracks repair CSVs. |
| `PYTHONPATH=$PWD/src PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" just ci-parity` | PASS, `3305 passed, 75 skipped in 75.84s`. |

## Artifact Boundary

No `runs/**` path was staged. No Parquet, SQLite, DB, cache, log, raw data,
canonical data, feature values, label values, secrets, locks, or study specs
were committed by this handoff. The BBO proof intentionally wrote local-only
data under `/home/yuke_zhang/alpha_data/alpha_system` via the sanctioned CLI.

## Next Steps

1. Review whether session offline countdown fvers should be regenerated under a
   one-off reviewed restore exception or removed/re-locked from kill-shot inputs.
2. Review regime identity drift for `base_ohlcv_returns` and
   `base_ohlcv_rolling_range`; current CLI cannot reproduce the stale ids.
3. If BBO full-grid repair proceeds, run the BBO command in the runbook and
   re-lock the affected `sspec_6088f0` study spec family afterward.
