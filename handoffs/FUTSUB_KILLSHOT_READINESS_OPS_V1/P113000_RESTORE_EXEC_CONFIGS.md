# P113000_RESTORE_EXEC_CONFIGS Handoff

Campaign: FUTSUB_KILLSHOT_READINESS_OPS_V1
Phase: P113000_RESTORE_EXEC_CONFIGS
Branch: wf1/restore-exec-configs
Commit: local branch commit containing this handoff
Executor: Codex
Date: 2026-06-12

## Scope Completed

- Added executable v2 restore configs:
  - `configs/features/scaleout/repair/session_calendar_maintenance_union_restore_v2.json`
  - `configs/features/scaleout/repair/regime_volatility_compression_union_restore_v2.json`
- Repaired the V1 force-recompute preparation path so mixed already-registered and missing preview fvids can be prepared without rebuilding active rows through the duplicate-exposure gate.
- Added regression coverage for mixed existing/missing force-recompute context.
- Updated `research/futures_substrate_scaleout_v1/repair/PACK_RESTORE_RUNBOOK.md` with v2 commands, unblock rationale, and superseded blocker history.
- Did not run any `--execute` command.

## Root Cause

The duplicate-exposure gate is invoked by `evaluate_feature_request_gate` before implementation admission (`src/alpha_system/features/request_gate.py:168` and `src/alpha_system/features/request_gate.py:194`). A blocking duplicate is rejected with the exact coordinator error string at `src/alpha_system/features/request_gate.py:223`.

The request signature is built in `_request_signature` from:

- `requested_inputs`;
- formula input names;
- `formula_sketch` exposure identity from `exposure_family`, `exposure`, `family`, `factor_id`, or `name`;
- normalized operation from `operation`, `operator`, `transform`, `method`, or `formula`;
- window/lookback/period/horizon;
- tokens across `requested_inputs`, `formula_sketch`, `availability_assumptions`, and `data_requirements`.

See `src/alpha_system/governance/duplicate_exposure.py:281`.

The registry entry signature mirrors this from active registry rows using factor id/version/name, metadata/parameters exposure family, operation, window, inputs, and tokens (`src/alpha_system/governance/duplicate_exposure.py:313`). The blocking case is exact exposure identity or a request input naming an existing factor/name/exposure family (`src/alpha_system/governance/duplicate_exposure.py:361`). Same operation/window/input overlap is only a warning (`src/alpha_system/governance/duplicate_exposure.py:387`).

The live registry reader exposes only `REGISTERED` rows to the duplicate guard (`src/alpha_system/features/registry.py:747`) and adapts each record back into `factor_id`, `name`, metadata `exposure_family`, operation, inputs, and window (`src/alpha_system/features/registry.py:1317`).

Scaleout requests put the per-unit exposure family in both `requested_inputs` and `formula_sketch.exposure_family`:

- session: `src/alpha_system/features/scaleout/driver.py:5577`
- regime: `src/alpha_system/features/scaleout/driver.py:5880`
- BBO: `src/alpha_system/features/scaleout/driver.py:6464`

The committed session/regime configs collided because force-recompute had a mixed set after deprecation: active unchanged fvids plus missing replacement fvids. The previous force-recompute helper returned no existing context if any preview fvid was missing, so the coordinator rebuilt the whole family against the live registry. Already-registered active rows then matched the same per-unit exposure families and triggered blocking duplicate findings.

The P094500 BBO repair config did not collide because the relevant preview set was already fully registered, so force-recompute could reuse existing specs/request payloads and did not re-enter the duplicate gate for active exposures. P113000 generalizes that behavior for mixed packs by reusing existing request provenance for registered preview fvids and rebuilding only missing replacement fvids (`src/alpha_system/features/scaleout/driver.py:3285`).

## Config Decisions

Session post-deprecation scope is the 8 committed governed names:

`session_id`, `minutes_from_rth_open`, `minutes_to_rth_close`, `rth_segment_flag`, `eth_segment_flag`, `day_of_week`, `minutes_to_expiration`, `halt_status_flag`.

`bars_to_roll` and `minutes_to_roll` stay excluded per R-036. The read-only registry check found 48 `coordinator/P094500_deprecate_first` countdown deprecations with no replacement pointers.

Regime post-deprecation scope remains the 5 governed names:

`trendiness`, `atr_volatility_regime`, `range_compression`, `range_expansion`, `momentum_reversion_state`.

The current code still regenerates the two pack-local base OHLCV input copies through governed bindings: `range_expansion` maps to primitive `ohlcv` `rolling_range` (`src/alpha_system/features/scaleout/driver.py:5981`), and `momentum_reversion_state` maps to primitive `ohlcv` `returns` (`src/alpha_system/features/scaleout/driver.py:5988`). Therefore the expected regime set does not shrink.

Both v2 configs keep the existing family value namespaces and pack-restore checkpoint roots:

- `features/materialized/futures_substrate_scaleout_v1/session_calendar_maintenance`
- `features/materialized/futures_substrate_scaleout_v1/regime_volatility_compression`

## Dry-Run Proof

Commands run without `--execute`:

```bash
PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/repair/session_calendar_maintenance_union_restore_v2.json --rollout full-window --json > /tmp/p113_session_v2_dryrun.json
PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/repair/regime_volatility_compression_union_restore_v2.json --rollout full-window --json > /tmp/p113_regime_v2_dryrun.json
```

Results:

- Session: `dry_run=true`, `accepted_unit_count=24`, `planned_count=24`, `failed_count=0`, feature count per unit `8`, symbols `ES/NQ/RTY`, years `2019-2026`.
- Regime: `dry_run=true`, `accepted_unit_count=24`, `planned_count=24`, `failed_count=0`, feature count per unit `5`, symbols `ES/NQ/RTY`, years `2019-2026`.

Additional read-only prepare probe against the live registry completed all force-recompute preparations without writes:

- `session_calendar_maintenance prepared_units 24 feature_count 8`
- `regime_volatility_compression prepared_units 24 feature_count 5`

Read-only replacement-pointer verification against `/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite?mode=ro` found no mismatches between v2 preview fvids and `coordinator/P094500_deprecate_first` replacement pointers:

- Session identity replacements: 72 rows across `day_of_week`, `minutes_to_expiration`, `halt_status_flag`.
- Session R-036 no-successor deprecations: 48 rows across `bars_to_roll`, `minutes_to_roll`.
- Regime identity replacements: 48 rows across `base_ohlcv_returns`, `base_ohlcv_rolling_range`.
- Mismatches: 0.

## Validation

| Command | Result |
| --- | --- |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py -q` | PASS: 4 passed |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m py_compile src/alpha_system/features/scaleout/driver.py` | PASS |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q` | FAIL: 1 failed, 133 passed |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py` | PASS |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke` | PASS |
| `PYTHONPATH=$PWD/src PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" just ci-parity` | FAIL: 1 failed, 3312 passed, 77 skipped |
| `git diff --check` | PASS |
| `git ls-files runs` | PASS: empty |

The unit-suite and ci-parity failures are the same live-registry failure, not a v2 dry-run failure. `tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py:126` resolves committed relock feature locks against the live registry, and the deprecate-first operation has already deprecated some locked fvids before this phase is allowed to execute restore writes. First observed failing fvid: `fver_082cbb1b6cf5bfdfebd744c7e1959cf93a1984bdadaee05e746bac591fcc8160` (`regime base_ohlcv_rolling_range`, `ES_2019`), rejected because `feature_pack lifecycle_state must be REGISTERED for runtime resolution`.

## Review Focus

- Confirm the mixed existing/missing force-recompute behavior in `src/alpha_system/features/scaleout/driver.py:3285` is acceptable for repair configs and still fail-closes duplicate feature ids.
- Confirm session scope intentionally excludes R-036 countdowns and regime scope remains 5 governed names.
- Confirm coordinator execution uses the v2 configs and no old union-restore configs.

## Next Step

Coordinator can execute the two v2 restore commands from the runbook, then rerun relock/ci-parity after the replacement fvids are registered and materialized.
