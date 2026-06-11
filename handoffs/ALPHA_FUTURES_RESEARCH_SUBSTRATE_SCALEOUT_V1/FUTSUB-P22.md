# FUTSUB-P22 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P22` - LabelPack Registry Integration, Coverage Audit, and Resolver Smoke  
Executor outcome: `READY_FOR_REVIEW_NO_CURRENT_GAPS_FOUND` (not a phase verdict)  
Executor: Codex  
Date: `2026-06-11`

## Files For Ralph To Stage

Executor left all changes unstaged. If Ralph stages this phase, stage only
these commit-eligible paths:

- `README.md`
- `docs/futures_substrate_scaleout/LABEL_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/label_packs/registry_integration_audit.md`
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`
- `tests/unit/futures_substrate_scaleout/labels/test_label_resolver_smoke.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P22.md`

Staged by Codex: none. No `reviews/**`, run-local `review.md`, run-local
`verdict.json`, PR, merge, staging, commit, push, or phase-pass verdict was
created by the executor.

## Scope Completed

- Read label registry metadata through `alpha label list --json` and
  `LabelRegistry.from_alpha_data_root(...).read_label_records()`.
- Built current label locks from write-free `alpha scaleout label-pack
  --dry-run --rollout full-window --json` previews for the five P16-P20 label
  surfaces.
- Resolved all current locks through
  `FeatureLabelPackResolver.resolve_label_packs`.
- Audited required registry fields, DatasetVersion acceptance states,
  `label_available_ts` ordering, roll/maintenance guard provenance, producer
  provenance, current Parquet sidecar content-hash consistency, identity
  collisions, deprecated-row disposition, and N_eff/overlap evidence
  provenance.
- Updated the focused synthetic resolver-smoke unit test to cover exact valid
  lock resolution and fail-closed behavior for absent, mutated, fuzzy-name, and
  deprecated exact-id refs.
- Refreshed the value-free integration and resolver-smoke reports, durable
  label integration doc, README snapshot, and this handoff.

No value materialization, registry write, diagnostics run, `src/**` edit,
provider call, raw provider read, paper/live/broker operation, PR creation,
merge, or phase verdict was performed.

## Integration Audit Result

Current dry-run preview surface:

| Surface | Expected locks | Active registered locks | Resolver gaps |
| --- | ---: | ---: | ---: |
| `fixed_base` | 144 | 144 | 0 |
| `fixed_extended` | 72 | 72 | 0 |
| `close_out` | 48 | 48 | 0 |
| `cost_adjusted` | 432 | 432 | 0 |
| `path` | 672 | 672 | 0 |
| **Total** | **1368** | **1368** | **0** |

For the 1368 current preview locks:

- Required registry fields were present and populated:
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, and `label_version_id`.
- `value_store_format=parquet`; each Parquet file existed and its sidecar
  content hash matched registry metadata.
- DatasetVersion and partition binding matched the dry-run unit for every
  current lock. Dataset states were `ACCEPTED` or `ACCEPTED_WITH_WARNINGS`.
- Dataset-state counts were `1026` `ACCEPTED` and `342`
  `ACCEPTED_WITH_WARNINGS`.
- No current `label_version_id` collision was observed.
- `label_available_ts` bounds were present and did not precede event timestamp
  bounds.
- Roll and maintenance provenance was present:
  `roll_policy_id=roll_cme_index_futures_quarterly`,
  `roll_guard_version=roll_guard_v1`, `roll_cross_policy=drop`,
  `maintenance_policy_id=cme_index_futures_daily_maintenance_break_v1`,
  `maintenance_guard_version=maintenance_crossing_guard_v1`, and
  `maintenance_crossing_policy=drop`.
- Producer engine was metadata only. Fixed-base current locks resolve across
  `126` V1 fast rows and `18` reference rows under the governed identities;
  extended/close-out/cost-adjusted resolve on the reference engine; path
  resolves on V1 fast.

Registry inventory:

- Total registry records: `2373`.
- Lifecycle states: `2324` `REGISTERED`, `49` `DEPRECATED`.
- Deprecated rows: `48` session-close / maintenance-flat stale rows plus `1`
  fixed-horizon duplicate.
- Deprecated rows in current preview surface: `0`.
- Current close-out preview locks: `48` / `48` active `REGISTERED` rows.
- Deprecated exact-id refs fail closed with `label_pack_deprecated` if supplied
  directly to the official resolver.
- Historical inventory note: `956` active cost-adjusted rows remain outside the
  current dry-run preview surface and are BBO DatasetVersion-bound records from
  earlier FUTSUB-P19 runs. They are not duplicate current ids and are not used
  as P22 current locks; the current cost-adjusted surface is the 432
  OHLCV-bound dry-run ids, all resolving exactly.

## N_eff / Overlap Evidence

Per the coordinator clarification:

| Surface | Evidence provenance | Result |
| --- | --- | --- |
| `fixed_base` | report-level: P22-computed conservative effective counts from current registry rows; P16/P21 carry row and overlap-window context | present |
| `fixed_extended` | registry-level `contract_metadata.horizon_overlap_metadata` | 72 / 72 present |
| `close_out` | report-level P18 effective samples as distinct close-out terminal events | present |
| `cost_adjusted` | report-level P19 horizon rows, effective N, and overlap rows | present |
| `path` | report-level P20 coverage summary / `coverage_matrix.json` horizon rows, effective N, and overlap rows | present |

Carried-forward follow-up, not fixed here: the V1 fast `register_pack`
registry-metadata path would not propagate `horizon_overlap_metadata` if
extended horizons ever registered through V1. This is latent today because
extended horizons register through the reference engine.

## Resolver-Smoke Result

- Current dry-run preview locks resolved: `1368` / `1368`.
- Current preview gaps: `0`.
- Negative probes in the synthetic fixture:
  - absent exact id -> `label_pack_not_found`;
  - mutated exact id -> `label_pack_not_found`;
  - fuzzy label name -> `invalid_label_pack_ref`;
  - deprecated exact id -> `label_pack_deprecated`.
- No fuzzy fallback, unit-id fallback, substitution, deprecated lifecycle
  fallback, or fabricated lock was accepted.

Per-family x horizon x symbol x accepted-year results are summarized in
`research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`.
Every row in that matrix has `Gap=0`.

## Explicit Gaps

Unexpected current-surface coverage gaps: none.

Unexpected resolver lifecycle gaps: none found in this executor audit.

Expected exclusions:

- `2018` is excluded because the DatasetVersion is `BLOCKED`.
- `2019` and `2026` are included as `ACCEPTED_WITH_WARNINGS`; warning state is
  surfaced in the reports.
- P21 guard-invalidated windows remain excluded from emitted rows and were not
  recomputed here.
- No P20 path unit was classified as infeasible in the current registry
  surface.

## Commands Run

Run:

```bash
test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP && test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P22/STOP && printf 'no STOP\n' || { printf 'STOP present\n'; exit 2; }
```

Outcome: exit `0`; no STOP file present.

Run-local reads:

```bash
sed -n '1,260p' runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/state.json
sed -n '1,260p' runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P22/spec.md
```

Outcome: both exited `2`; the prompted run-local state/spec paths are absent
in this worktree. The executor used the generated spec from the prompt.

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main label list --json > /tmp/futsub_p22_label_list.json
```

Outcome: exit `0`; `2373` label records, `2324` `REGISTERED`, `49`
`DEPRECATED`. Stderr contained only the known Python `runpy` warning.

Run dry-run previews:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --dry-run --rollout full-window --json > /tmp/futsub_p22_fixed_base_dryrun.json
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/extended_horizon.json --dry-run --rollout full-window --json > /tmp/futsub_p22_fixed_extended_dryrun.json
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/session_close_maintenance_flat.json --dry-run --rollout full-window --json > /tmp/futsub_p22_close_out_dryrun.json
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/cost_adjusted.json --dry-run --rollout full-window --engine reference --workers 1 --json > /tmp/futsub_p22_cost_adjusted_dryrun.json
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=8 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/path.json --dry-run --rollout full-window --engine v1 --workers 8 --json > /tmp/futsub_p22_path_dryrun.json
```

Outcome: all exited `0`; preview locks were `144`, `72`, `48`, `432`, and
`672` respectively. Stderr contained only the known Python `runpy` warning.

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python - <<'PY'
# read-only P22 registry/resolver audit using LabelRegistry, DatasetVersion
# acceptance APIs, value-store sidecar checks, and FeatureLabelPackResolver
PY
```

Outcome: exit `0`; `1368` / `1368` preview locks resolved, `0` gaps, required
fields present, no Parquet/hash mismatches, `72` / `72` extended-horizon
records had registry-level overlap metadata, and the deprecated exact-id probe
returned `label_pack_deprecated`.

Run before the test repair:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels/test_label_resolver_smoke.py -q
```

Outcome: exit `1`; `4 passed`, `1 failed` because the stale test expected a
deprecated exact-id ref to resolve. The production resolver now fails closed
with `label_pack_deprecated`. The test was updated in scope.

Run after the test repair:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels/test_label_resolver_smoke.py -q
```

Outcome: exit `0`; `5 passed in 0.33s`.

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke
```

Outcome: exit `0`.

Run:

```bash
test -f research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md && test -f docs/futures_substrate_scaleout/LABEL_INTEGRATION.md && test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P22.md
```

Outcome: exit `0`.

Run:

```bash
git ls-files runs
```

Outcome: exit `0`; empty output.

Run:

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'
```

Outcome: exit `0`; empty output.

Not run:

- `git status --short`: the executor prompt explicitly forbade `git status`.
- `git diff --cached --name-only`: Codex did not stage anything and the
  executor prompt explicitly forbade `git diff`.
- Reviewer / Claude / `review.md` / `verdict.json`: not run or created per
  executor instructions.
- PR creation, CI waiting, merge gate, merge, and phase-pass marking: not
  performed by Codex per executor instructions.

## Artifact Policy

- `git ls-files runs` returned empty output.
- Heavy tracked artifact glob returned empty output.
- Materialized values, manifests, checkpoints, local SQLite registries, and
  registry backups remain local-only under `ALPHA_DATA_ROOT`.
- `/tmp/futsub_p22_*` dry-run and audit scratch files are local-only and not
  commit-eligible.
- No `runs/**` path was staged or committed by the executor.
- The prompted run artifact directory is absent in this worktree, so no
  run-local handoff was written. The commit-eligible handoff is this file.

## Review Focus

- Confirm P22 stayed out of `src/**` and did not materialize or mutate registry
  state.
- Confirm the current resolver fail-closed evidence covers absent, mutated,
  fuzzy-name, and deprecated exact-id refs.
- Confirm per-family N_eff/overlap provenance is neither overstated nor skipped.
- Confirm the reports are value-free and contain no local data paths, values,
  content hashes, raw provider payloads, or profitability/tradability claims.
- Confirm Ralph's eventual staged set contains only the six commit-eligible
  paths listed above and no `runs/**` or heavy artifact paths.
