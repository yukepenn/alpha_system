# FCFP-P14 Handoff - V1 Producer Path Integration + Resolver Smoke

## Context

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P14`
- Branch: `auto/feature_compute_fast_path_v1/fcfp-p14-v1-producer-path-integration-resolver-smoke`
- Base HEAD: `c8a3685` (`FEATURE_COMPUTE_FAST_PATH_V1: add FCFP-P15 benchmark-driven CPU worker phase (#301)`)
- Executor commits: none
- Executor staging: none

The executor prompt explicitly forbade `git status`, `git diff`, `git add`,
`git commit`, `git push`, review execution, PR creation, merge, and PASS
marking. Changes are left unstaged for Ralph.

## Scope Completed

- `src/alpha_system/features/scaleout/driver.py` routes execute-mode scaleout to
  V1 by default with `engine="v1"` and retains `engine="reference"` for the
  per-family reference executors.
- `src/alpha_system/cli/scaleout.py` exposes `--engine {v1,reference}` and
  includes the selected engine in summaries.
- V1 materialization uses `build_fast_feature_pack`, `PackMaterializer`, and
  `PackMaterializer.register_pack` with the official `FeatureStore` write path.
- Checkpoint / registry skip-completed behavior is engine-aware: reference
  producer records are not accepted as V1 completion evidence.
- Targeted subset execution is supported by the V1 family and fixed-horizon label
  pack validators for non-empty governed subsets.
- A bounded-real, local-only smoke materialized representative V1 feature and
  label locks under `ALPHA_DATA_ROOT`.
- Official resolver smoke resolved the final representative positive locks and
  failed closed on stale/fuzzy controls.
- Value-free report written:
  `research/feature_compute_fast_path_v1/integration/integration_report.md`.
- Docs and README snapshot updated.

## Files Changed

Executor-edited commit-eligible files:

```text
README.md
docs/feature_compute_fast_path/OVERVIEW.md
docs/feature_compute_fast_path/PRODUCER_PATH_INTEGRATION.md
docs/feature_compute_fast_path/README.md
docs/feature_compute_fast_path/TARGETED_SCALEOUT.md
handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P14.md
research/feature_compute_fast_path_v1/integration/integration_report.md
src/alpha_system/cli/scaleout.py
src/alpha_system/features/fast/base_ohlcv.py
src/alpha_system/features/fast/bbo_tradability.py
src/alpha_system/features/fast/cross_market_panel.py
src/alpha_system/features/fast/materializer.py
src/alpha_system/features/fast/regime_vol_compression.py
src/alpha_system/features/fast/session_calendar_roll.py
src/alpha_system/features/fast/volume_activity.py
src/alpha_system/features/fast/vwap_session_auction.py
src/alpha_system/features/scaleout/__init__.py
src/alpha_system/features/scaleout/driver.py
src/alpha_system/labels/fast/fixed_horizon.py
tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py
tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py
tests/unit/feature_compute_fast_path/test_v1_resolver_smoke.py
tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_liquidity_pa_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_regime_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_targeting.py
tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py
tests/unit/futures_substrate_scaleout/scaleout/test_volume_activity_scaleout_driver.py
```

No `runs/**` files were created in this checkout; the user-provided run
artifact directory was absent.

## Local-Only Artifacts

Registry backups created before registry-touching materialization:

```text
/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite.bak_fcfp_p14_20260609T050520Z
/home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite.bak_fcfp_p14_20260609T050520Z
```

Local-only integration smoke root:

```text
/home/yuke_zhang/alpha_data/alpha_system/fcfp_p14_smoke_20260609T050520Z
```

This root contains local Parquet values, registries, and checkpoints and must
not be staged or committed.

## Engine Routing Summary

- Default engine: `v1`
- Reference fallback: `--engine reference`
- V1 feature producer provenance:
  `alpha_system.features.fast.pack_materializer.v1`
- V1 feature value schema:
  `alpha_system.features.fast.values.v1`
- V1 label producer provenance:
  `alpha_system.labels.fast.pack_materializer.v1`
- V1 label value schema:
  `alpha_system.labels.fast.values.v1`

V1 and reference use the same governed `feature_version_id` /
`label_version_id` identities. Producer provenance and request provenance do not
enter identity.

## Resolver Smoke Counts

Final representative resolver-smoke set:

| Check | Count | Result |
| --- | ---: | --- |
| Positive feature/label lock pairs | 2 | resolved |
| Positive resolver gaps | 0 | none |
| Stale feature controls | 1 | fail-closed |
| Stale label controls | 1 | fail-closed |
| Fuzzy label-name controls | 1 | fail-closed |

Positive pairs:

- `base_ohlcv` `returns` feature on the accepted OHLCV 2024 ES slice plus
  `fwd_ret_1m` label.
- `bbo_tradability_top_book` `mid` feature on the accepted BBO 2024 ES slice
  plus `mid_fwd_ret_1m` label.

Negative resolver reasons:

```text
feature_pack_not_found
label_pack_not_found
invalid_label_pack_ref
```

Diagnostic note: a dense-grid `session_calendar_maintenance` `day_of_week`
feature and matching label were materialized locally, but the resolver blocked
that pair with `label_as_feature_input` because the current runtime resolver
treats unannotated `session_label` feature inputs conservatively. The resolver
was not weakened; the final representative pass set used Base OHLCV and BBO
families.

## Commands Run

Registry backup:

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp "$ALPHA_DATA_ROOT/registry/features.sqlite" \
   "$ALPHA_DATA_ROOT/registry/features.sqlite.bak_fcfp_p14_$TS"
cp "$ALPHA_DATA_ROOT/registry/labels.sqlite" \
   "$ALPHA_DATA_ROOT/registry/labels.sqlite.bak_fcfp_p14_$TS"
```

Outcome: created the two local-only backups listed above.

Targeted tests during implementation:

```bash
python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py tests/unit/feature_compute_fast_path/test_v1_resolver_smoke.py -q
```

Outcome: `6 passed`.

```bash
python -m pytest tests/unit/feature_compute_fast_path/ -q
```

Outcome: `39 passed`.

```bash
python -m pytest tests/unit/futures_substrate_scaleout/ -q
```

Outcome after old dispatcher tests were updated for the new default/fallback
contract: `54 passed`.

```bash
python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py tests/unit/feature_compute_fast_path/test_v1_resolver_smoke.py tests/unit/futures_substrate_scaleout/ -q
```

Outcome: `59 passed`.

Bounded-real V1 materialization commands:

```bash
PYTHONPATH=src python -m alpha_system.cli.main scaleout feature-pack \
  --config configs/features/scaleout/base_ohlcv.json \
  --execute --rollout bounded-real --bounded-year 2024 \
  --feature-id returns --symbols ES --years 2024 \
  --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system/fcfp_p14_smoke_20260609T050520Z \
  --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite \
  --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 \
  --engine v1 --json
```

Outcome: completed `1`, failed `0`, skipped `0`; engine `v1`.

```bash
PYTHONPATH=src python -m alpha_system.cli.main scaleout feature-pack \
  --config configs/features/scaleout/session_calendar_maintenance.json \
  --execute --rollout bounded-real --bounded-year 2024 \
  --feature-id day_of_week --symbols ES --years 2024 \
  --dataset-version-ids dsv_databento_ohlcv_dense_2024_v1 \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system/fcfp_p14_smoke_20260609T050520Z \
  --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite \
  --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 \
  --engine v1 --json
```

Outcome: first attempt exposed a real dense-grid Polars schema-inference error;
`PackMaterializer.frame_from_rows` now scans all rows for deterministic schema
inference. Rerun completed `1`, failed `0`, skipped `0`; engine `v1`.

```bash
PYTHONPATH=src python -m alpha_system.cli.main scaleout feature-pack \
  --config configs/features/scaleout/bbo_tradability_top_book.json \
  --execute --rollout bounded-real --bounded-year 2024 \
  --feature-id mid --symbols ES --years 2024 \
  --dataset-version-ids dsv_databento_bbo_f9e1d70a04d9dae4 \
  --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system/fcfp_p14_smoke_20260609T050520Z \
  --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite \
  --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 \
  --engine v1 --json
```

Outcome: completed `1`, failed `0`, skipped `0`; engine `v1`.

Label materialization was run through Python snippets using
`FastLabelMaterializer` and `LabelRegistry` on matching accepted DatasetVersions:

- OHLCV `fwd_ret_1m`: `346386` records.
- Dense OHLCV `fwd_ret_1m`: `346833` records.
- BBO `mid_fwd_ret_1m`: `7` records.

One dense label snippet failed after successful registration while printing a
nonexistent convenience attribute; registry inspection confirmed the label
record and metadata through `LabelRegistry`.

Final resolver smoke:

```bash
PYTHONPATH=src python - <<'PY'
# RuntimeEntryRequest + resolve_runtime_input_pack against the smoke
# FeatureStore/LabelRegistry and official DatasetVersion resolver.
PY
```

Outcome:

```text
POSITIVE base_returns_with_ohlcv_label STATUS INPUTS_RESOLVED REASONS runtime_input_pack_resolved
POSITIVE bbo_mid_with_midprice_label STATUS INPUTS_RESOLVED REASONS runtime_input_pack_resolved
NEGATIVE stale_feature STATUS INPUTS_BLOCKED REASONS feature_pack_not_found
NEGATIVE stale_label STATUS INPUTS_BLOCKED REASONS label_pack_not_found
NEGATIVE fuzzy_label STATUS INPUTS_BLOCKED REASONS invalid_label_pack_ref
SUMMARY positive_resolved=2 positive_gaps=0 negative_fail_closed=3 negative_gaps=0
```

Idempotency reruns:

```bash
PYTHONPATH=src python -m alpha_system.cli.main scaleout feature-pack ...base_ohlcv... --engine v1 --json
PYTHONPATH=src python -m alpha_system.cli.main scaleout feature-pack ...bbo_tradability_top_book... --engine v1 --json
```

Outcome: both representative units returned completed `0`, skipped `1`, failed
`0` with message `completed unit skipped from checkpoint + registry truth`.

Required validation:

```bash
git status --short
```

Outcome: not run. The executor override explicitly forbade `git status`.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python tools/verify.py --smoke
```

Outcome: passed with no output.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/ tests/unit/feature_compute_fast_path/ -q
```

Outcome: `94 passed in 3.19s`.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q
```

Outcome: `12 passed in 0.14s`.

```bash
test -f research/feature_compute_fast_path_v1/integration/integration_report.md
```

Outcome: passed.

```bash
git ls-files runs
```

Outcome: passed, empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Outcome: passed, empty output.

Yellow-lane gates:

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python tools/verify.py --all
```

Outcome: nonzero. Full suite result was `2961 passed`, `4 failed` in `48.73s`.
Failures were outside the FCFP-P14 allowed paths and were not repaired:

```text
tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture
  expected list-shaped rows; function returned a tuple

tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture
  expected list-shaped rows; function returned a tuple

tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline
  expected JSONL OHLCV rows; observed empty list

tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only
  observed ALPHA_DATA_ROOT cache root instead of run-artifact root
```

The same command also ran status doctor and canaries after pytest:
status doctor returned `WARN` because no live run dir with `state.json` was
present; canaries passed.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python tools/hooks/canary_runner.py
```

Outcome: all Frontier canaries passed.

## Artifact Audit

- `git ls-files runs`: empty
- `git ls-files '**/*.parquet' '**/*.sqlite'`: empty
- No `runs/**` path staged by the executor.
- No files staged by the executor at all.
- Local-only smoke values, registries, manifests, and checkpoints remain under
  `/home/yuke_zhang/alpha_data/alpha_system/fcfp_p14_smoke_20260609T050520Z`.

Explicit staged file list by executor:

```text
<none>
```

Suggested Ralph stage set is the commit-eligible file list in "Files Changed"
above, subject to Ralph's artifact audit.

## Risks And Caveats

- `python tools/verify.py --all` is not green because of four broad-suite
  failures outside this phase's allowed paths. The requested focused tests,
  smoke verification, no-lookahead boundary test, artifact audits, and canary
  gate passed.
- The session/calendar dense-grid feature resolver diagnostic shows a current
  resolver policy gap around unannotated `session_label` metadata. This phase did
  not change resolver semantics or reference-family contracts to force that
  pair through.
- Real materialization was performed in an isolated local-only smoke root under
  `ALPHA_DATA_ROOT` to avoid mutating the shared feature/label registries.
- No review artifacts were created by the executor per prompt override; Ralph
  owns Yellow review routing.

## Review Request Focus

- Confirm default V1 dispatch and reference fallback selection in the driver/CLI.
- Confirm the engine-aware skip-completed guard prevents silent reference/V1
  completion mixing.
- Confirm subset validator changes preserve governed-only pack admission.
- Confirm resolver-smoke evidence is value-free and uses official registry and
  runtime resolver paths.
- Confirm local-only artifact boundaries and no `runs/**` commit exposure.

## Next Recommended Step

Ralph should perform its artifact audit, run or route the Yellow semantic review,
decide how to handle the nonzero broad `--all` gate, then stage only explicit
commit-eligible paths if the phase is accepted for review. The executor did not
create a review, verdict, PR, merge, or PASS marker.

