# Handoff - FUTCORE-P01

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P01` - Preflight  
Executor: Codex  
Date: 2026-06-07

## Executor Status

Execution artifacts are written and left unstaged in the working tree. This
handoff does not mark the phase PASS; Ralph owns validation orchestration,
review, staging, commit, PR, CI, merge, and done-check.

No source primitive under `src/alpha_system/**` was edited. No tests were added
or modified. No review artifact, `review.md`, or `verdict.json` was created.
No live, paper, broker, order, account, deployment, provider acquisition, or
destructive operation was performed.

## Files Written Or Updated

- `docs/futures_core_alpha_pilot/PREFLIGHT.md`
- `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P01.md`
- `README.md`

## Staged Files

None. The executor did not run `git add`, `git commit`, `git push`,
`git status`, or `git diff` per the explicit Workflow 2 executor instructions.

Ralph should stage only the commit-eligible files listed above, subject to its
authoritative artifact and staged-set checks. No `runs/**` path should be
staged.

## Gate Status Table

| Gate | Status | Evidence reference | Note |
| --- | --- | --- | --- |
| Consumed primitive imports | `PASS` | `. /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && python -c "import alpha_system.governance, alpha_system.runtime, alpha_system.agent_factory"` exited `0`; `PYTHONPATH=src` import check also returned `imports_ok`. | Default shell package discovery lacks an editable install; validation used the project research venv from campaign runtime metadata. |
| `FEATURE_LABEL_PARQUET_SINK_V1` complete | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; registry metadata fields printed from local-only smoke registries. | `parquet_sink_landed=true`; feature/label rows record `value_store_format`, `parquet_path`, `value_content_hash`, and `value_schema_version`. |
| `SESSION_LABEL_GUARD_FIX_V1` complete | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; `docs/research_runtime/SESSION_LABEL_GUARD.md`. | `session_label_guard_fixed=true`; true labels / forward-looking fields remain blocked by policy. |
| Research Runtime real-data smoke status | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; `docs/research_runtime/REAL_SMOKE.md`. | Recorded smoke status is `PASS` with `real_dataset_version_smoke_ran=true`; no live acquisition was rerun. |
| Accepted DatasetVersion resolvable | `PASS` | `resolve_dataset_version('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite', 'dsv_databento_ohlcv_05404069799decb0')` returned a record. | Resolved ES/NQ/RTY Databento OHLCV DatasetVersion by id and metadata only. |
| Parquet FeaturePack / LabelPack availability | `PASS` | Read-only feature/label registry APIs over `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/{features,labels}.sqlite`. | Two FeatureVersion refs and one LabelVersion ref recorded with Parquet metadata references only. |
| Agent Factory preflight | `PASS` | `evaluate_agent_factory_preflight(...)` with smoke registry root and landed blocker flags returned `PREFLIGHT_PASS`; roles/permissions/queue/separation imports succeeded. | No agent was instantiated and no runner was started. |

## Evidence Commands

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP; printf 'STOP_EXISTS=%s\n' "$?"
```

Result: output `STOP_EXISTS=1`; no active STOP file was present.

```bash
PYTHONPATH=src python -c "import alpha_system.governance, alpha_system.runtime, alpha_system.agent_factory; print('imports_ok')"
```

Result: exit code `0`; output `imports_ok`.

```bash
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite; printf 'datasets_sqlite_test_status=%s\n' "$?"
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite; printf 'features_sqlite_test_status=%s\n' "$?"
test -f /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite; printf 'labels_sqlite_test_status=%s\n' "$?"
```

Result: outputs `datasets_sqlite_test_status=0`,
`features_sqlite_test_status=0`, and `labels_sqlite_test_status=0`.

```bash
PYTHONPATH=src python -m alpha_system.cli.main feature list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite --json
```

Result: exit code `0`; `record_count=2`; refs:
`fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`
and `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`.

```bash
PYTHONPATH=src python -m alpha_system.cli.main label list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite --json
```

Result: exit code `0`; `record_count=1`; ref
`lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`.

```bash
PYTHONPATH=src python - <<'PY'
import json
from alpha_system.data.foundation.version_registry import resolve_dataset_version
record = resolve_dataset_version(
    "/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite",
    "dsv_databento_ohlcv_05404069799decb0",
)
payload = record.to_mapping() if record is not None else {}
print(json.dumps({
    "resolved": record is not None,
    "dataset_version_id": payload.get("dataset_version_id"),
    "source": payload.get("source"),
    "symbol_universe": payload.get("symbol_universe"),
    "bar_size": payload.get("bar_size"),
    "what_to_show": payload.get("what_to_show"),
    "manifest_hash": payload.get("manifest_hash"),
    "config_hash": payload.get("config_hash"),
}, indent=2, sort_keys=True))
PY
```

Result: exit code `0`; `resolved=true`; id
`dsv_databento_ohlcv_05404069799decb0`; source
`dsrc_databento_historical`; symbols `ES`, `NQ`, `RTY`; bar size `1 min`;
what-to-show `TRADES`.

```bash
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from alpha_system.cli.feature import _feature_records
from alpha_system.labels.registry import LabelRegistry
feature_records = _feature_records(Path("/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite"))
label_records = LabelRegistry("/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite").read_label_records()
print(json.dumps({
    "feature_packs": [
        {
            "feature_version_id": r.feature_version_id,
            "value_store_format": r.value_store_format,
            "parquet_path": r.parquet_path,
            "value_content_hash": r.value_content_hash,
            "value_schema_version": r.value_schema_version,
        }
        for r in feature_records
    ],
    "label_packs": [
        {
            "label_version_id": r.label_version_id,
            "value_store_format": r.value_store_format,
            "parquet_path": r.parquet_path,
            "value_content_hash": r.value_content_hash,
            "value_schema_version": r.value_schema_version,
        }
        for r in label_records
    ],
}, indent=2, sort_keys=True))
PY
```

Result: exit code `0`; printed two feature pack metadata references and one
label pack metadata reference. All three rows had `value_store_format=dual`,
non-empty `parquet_path`, non-empty `value_content_hash`, and non-empty
`value_schema_version`.

```bash
PYTHONPATH=src python - <<'PY'
import json
from alpha_system.agent_factory.entry_contract import evaluate_agent_factory_preflight
import alpha_system.agent_factory.roles
import alpha_system.agent_factory.permissions
import alpha_system.agent_factory.queue
import alpha_system.agent_factory.separation.wiring
import alpha_system.agent_factory.separation.enforcement
result = evaluate_agent_factory_preflight(config={
    "registries": {"alpha_data_root": "/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke"},
    "runtime_real_smoke": {
        "real_dataset_version_smoke_ran": True,
        "status_source": "PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1",
    },
    "future_blockers": {
        "parquet_sink_landed": True,
        "session_label_guard_fixed": True,
    },
    "request_scope": {
        "large_scale_value_consuming_study_requested": True,
        "session_context_features_requested": ["rth_flag", "session_minute"],
    },
})
print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
PY
```

Result: exit code `0`; top-level status `PREFLIGHT_PASS`; no blocking findings.

## Validation Commands

`git status --short` was not run because the executor instructions explicitly
forbid `git status`.

```bash
. /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && python -c "import alpha_system.governance, alpha_system.runtime, alpha_system.agent_factory"
```

Result: exit code `0`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`.

```bash
python tools/hooks/canary_runner.py
```

Result: exit code `0`; all Frontier canaries passed.

```bash
test -f docs/futures_core_alpha_pilot/PREFLIGHT.md
test -f research/futures_core_alpha_pilot_v1/preflight/preflight_report.md
```

Result: exit code `0`; both files exist.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

## Blockers Or Escalations

No readiness gate blocker was recorded.

Executor safety exceptions / ownership notes:

- `git status --short` was skipped by explicit user instruction.
- No staged-set inspection was performed because the executor was instructed not
  to run `git diff`; the executor staged nothing.
- Yellow-lane review artifacts were not created by the executor. Ralph owns
  reviewer invocation and any commit-eligible review promotion.

## Artifact Confirmation

- `git ls-files runs` returned empty.
- Tracked heavy-artifact globs for `*.parquet`, `*.sqlite`, `*.dbn`, and `*.zst`
  returned empty.
- No `runs/**` file was written by this executor.
- No raw/canonical data, feature values, label values, Parquet, SQLite, provider
  response, local DB, log, cache, secret, credential, or heavy artifact was
  added to the repository.
