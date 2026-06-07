# FUTCORE-P13 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P13` - Data Contract / FeaturePack / LabelPack Audit
Executor: Codex GPT-5.5
Lane: Yellow
Status: executor work complete, review and authoritative staging pending Ralph

## Scope Completed

- Audited the 10 `accept-for-StudySpec` AlphaSpecs from the P12 budget audit.
- Resolved the P03 locked DatasetVersion, eight FeaturePack records, and three
  LabelPack records through sanctioned registry/resolver surfaces by reference
  only.
- Confirmed all eight locked FeaturePack records carry valid non-empty
  `available_ts` windows and all three locked LabelPack records carry valid
  non-empty `label_available_ts` windows.
- Wrote the per-AlphaSpec primitive mapping and the consolidated minimal P15
  gap list.
- Updated the durable docs page and README snapshot.

No consumed primitive under `src/alpha_system/**` was edited. No tests were
added or modified. No FeatureRequest, LabelSpec, StudySpec, diagnostic, review
artifact, `review.md`, `verdict.json`, PR, merge, staging, commit, provider
call, raw/value data read, live, paper, broker, order, account, deployment, or
production action was performed.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`
- `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`
- `docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`

## Explicit Commit-Eligible File List For Ralph

The executor staged nothing. Ralph should stage only these paths explicitly,
subject to its authoritative artifact and staged-set checks:

- `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`
- `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`
- `docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`

No `runs/**` path should be staged.

## Audit Outcome

Locked and available by reference:

- DatasetVersion `dsv_databento_ohlcv_05404069799decb0` resolves for ES/NQ/RTY
  OHLCV 1 minute bars.
- FeaturePack records resolve for:
  `base_ohlcv_log_returns`, `base_ohlcv_range_position`,
  `base_ohlcv_returns`, `base_ohlcv_rolling_range`,
  `base_ohlcv_rolling_volatility`, `base_ohlcv_rth_flag`,
  `base_ohlcv_session_minute`, and `base_ohlcv_volume_zscore`.
- LabelPack records resolve for `fwd_ret_5m`, `fwd_ret_10m`, and
  `fwd_ret_30m`.
- One value-free `StudyInputPack` shape validates for each accepted AlphaSpec
  using the locked feature request ids, label spec ids, and DatasetVersion
  scope.

Minimal P15 gap budget items:

1. `fwd_ret_15m` LabelPack binding.
2. VWAP/session FeaturePack binding.
3. Cross-market derived-state FeaturePack binding.
4. Additional regime/liquidity base-OHLCV derived-state FeaturePack binding.
5. BBO top-book confirmation FeaturePack binding.

The gap list has exactly five grouped candidate request budget items and does
not exceed the campaign cap. P15 still owns any implementation or no-op
decision.

## Cross-Market / Cross-Instrument Flags

- DatasetVersion metadata resolves the universe as `ES`, `NQ`, and `RTY`; P13
  does not inspect value rows, so symbol-level row coverage remains for later
  diagnostics/audits.
- Cross-market accepted specs still require P16/P23 checks for
  cross-instrument `available_ts` alignment, late/stale row handling, no
  silent forward-fill/backfill, and label timing.
- Accepted source drafts cite stale session FeatureVersion ids
  (`fver_c365f971...` and `fver_17dfce...`). The primitive names resolve in P03
  under `fver_acbfa783...` and `fver_fd739ad...`; P14 must bind the P03 ids.
- Accepted source drafts that describe only a locked `5m` label should be
  corrected by P14 binding: P03 resolves `5m`, `10m`, and `30m`; only `15m`
  remains missing.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from alpha_system.cli.feature import _feature_records
from alpha_system.cli.label import _label_records
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.features.registry import FeatureRegistry
from alpha_system.features.store import FeatureStore
from alpha_system.labels.registry import LabelRegistry
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver
from alpha_system.governance.study_input_pack import validate_study_input_pack

feature_registry = Path('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite')
label_registry = Path('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite')
dataset_registry = Path('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite')
dataset_id = 'dsv_databento_ohlcv_05404069799decb0'
partition = 'development_partition'
alpha_spec_ids = [
    'aspec_0ebd90cecfd475607685b445',
    'aspec_8d9e272e4b78eedcd27f0bec',
    'aspec_a41dcccac5552de945aba825',
    'aspec_fa4895a43a80d4eef0a607a4',
    'aspec_b40aee52d4399dd5b855a6ed',
    'aspec_43cd6c154bca2fcc419eee83',
    'aspec_eb962fc197eaf3955c5e4711',
    'aspec_df2d040e45564c259ef3de6d',
    'aspec_39ffc190cfbfa6ba0b1a2a25',
    'aspec_1284e49b083df11eeb0481ea',
]
if resolve_dataset_version(dataset_registry, dataset_id) is None:
    raise SystemExit('dataset did not resolve')
features = _feature_records(feature_registry)
labels = _label_records(label_registry)
resolver = FeatureLabelPackResolver(
    feature_store=FeatureStore(FeatureRegistry(feature_registry)),
    label_registry=LabelRegistry(label_registry),
)
feature_handles = resolver.resolve_feature_packs(
    [r.feature_version_id for r in features],
    expected_dataset_version_id=dataset_id,
    expected_feature_request_ids=[r.feature_request_id for r in features],
    partition_id=partition,
)
label_handles = resolver.resolve_label_packs(
    [r.label_version_id for r in labels],
    expected_dataset_version_id=dataset_id,
    expected_label_spec_ids=[r.label_spec_id for r in labels],
    partition_id=partition,
)
if not all(h.first_available_ts and h.last_available_ts and h.first_available_ts <= h.last_available_ts for h in feature_handles):
    raise SystemExit('feature availability invalid')
if not all(h.first_label_available_ts and h.last_label_available_ts and h.first_label_available_ts <= h.last_label_available_ts for h in label_handles):
    raise SystemExit('label availability invalid')
feature_request_ids = sorted({r.feature_request_id for r in features})
label_spec_ids = sorted({r.label_spec_id for r in labels})
for alpha_spec_id in alpha_spec_ids:
    validate_study_input_pack({
        'feature_request_ids': feature_request_ids,
        'label_spec_ids': label_spec_ids,
        'alpha_spec_id': alpha_spec_id,
        'dataset_scope': {
            'dataset_version_id': dataset_id,
            'partition_id': partition,
            'symbol_universe': ['ES', 'NQ', 'RTY'],
            'value_store_format': 'dual',
        },
    })
print('dataset=resolved')
print(f'feature_handles={len(feature_handles)}')
print(f'label_handles={len(label_handles)}')
print(f'study_input_packs={len(alpha_spec_ids)}')
print('availability_windows=valid')
PY
```

Result: exit code `0`; output:

```text
dataset=resolved
feature_handles=8
label_handles=3
study_input_packs=10
availability_windows=valid
```

```bash
python -c "import alpha_system.governance.study_input_pack"
```

Result: exit code `0`.

```bash
PYTHONPATH=src python -c "import alpha_system.governance.study_input_pack"
```

Result: exit code `0`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/audits/data_contract
```

Result: exit code `0`.

```bash
test -f research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

```bash
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13
```

Result: exit code `0`; Codex created no commit-eligible review artifact.

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P13/review.md
```

Result: exit code `0`; Codex created no run-local `review.md`.

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P13/verdict.json
```

Result: exit code `0`; Codex created no run-local `verdict.json`.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`; Codex staged nothing. Ralph owns authoritative staged-set
  validation.
- `git add`, `git commit`, `git push`: not run because the user explicitly
  forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer. Ralph owns review orchestration.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.

## Review Artifacts

Codex did not create `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13/**`
artifacts, `review.md`, or `verdict.json` because the user override explicitly
forbade reviewer execution and review/verdict artifact creation. Ralph owns
review orchestration and verdict parsing.

## Exceptions Or Blockers

- No executor blocker.
- The gap list is non-empty and exactly at the campaign cap of five grouped
  items. If P15 cannot resolve or explicitly defer those items within its own
  scope, Ralph/human review should treat that as the next bounded-pilot scope
  decision point.
- `git status` and `git diff --cached` were skipped only due to the explicit
  executor override in the prompt.

## Boundaries

The work remains research-only and value-free. It adds no raw/canonical data,
feature values, label values, provider responses, Parquet/Arrow/Feather, DBN,
Zstd, SQLite/DB/WAL files, logs, caches, secrets, tests, runtime behavior,
broker/live/paper/order code, deployment behavior, diagnostics, StudySpecs,
FeatureRequests, LabelSpecs, promotion decisions, review artifacts, PR/merge
actions, staging, or commits.
