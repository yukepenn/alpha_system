# FUTCORE-P08 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P08`  
Lane: Yellow  
Executor: Codex  
Status: executor work complete; Ralph owns staging, commit, review, verdict,
PR, CI, merge, and done-check.

## Scope Completed

Drafted the VWAP / session-auction AlphaSpec batch under
`research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/`.

Draft count: `8`, matching the family target and maximum from the
`FUTCORE-P05` protocol.

## Files For Ralph Staging

Executor-staged files: none. The executor override forbids `git add`, commit,
push, `git status`, and `git diff`; all paths below are working-tree changes
for Ralph to stage explicitly.

- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_01.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_02.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_03.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_04.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_05.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_06.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_07.md`
- `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_08.md`
- `docs/futures_core_alpha_pilot/alpha_specs/vwap_session.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P08.md`

No `runs/` path is included in this list.

## Draft Coverage

- `01` - RTH running-VWAP reclaim after the opening window.
- `02` - Objective running-VWAP reject / close-back-side event.
- `03` - Bucketed distance to running VWAP.
- `04` - Completed opening range with running-VWAP confluence.
- `05` - Completed overnight high/low context with running RTH VWAP.
- `06` - RTH gap construction with first eligible running-VWAP context.
- `07` - RTH open versus completed ETH VWAP.
- `08` - Diagnostic pre-RTH/post-RTH transition distance to running VWAP.

The batch covers VWAP reclaim/reject, distance-to-VWAP, opening range,
overnight high/low, gap, and RTH-open-vs-ETH ideas. Volume/activity was not
introduced as a standalone family.

## Running-Vs-Final VWAP

Every draft declares `running_vwap_so_far` as a point-in-time input under
`available_ts`. Every draft rejects final-session VWAP, high, low, range,
volume, and other final aggregates as intraday inputs before the relevant
session completes.

Each draft also declares opening-range availability, overnight high/low
availability, gap construction timing, session-transition handling, and final
aggregate lookahead rejection.

## Cost, Horizon, Session, And Roles

Each draft cites `CostModelVersion`
`cmv_futcore_pilot_three_layer_session_stress_v1`.

The cost profile keys are exactly `zero_cost`, `base`, `stress_1`, `stress_2`,
and `double_cost`. `zero_cost` is diagnostic-only and excluded from all
continuation criteria. ETH, pre-RTH, and post-RTH views carry thin-session
overlays.

Primary horizons are five, ten, fifteen, and thirty minutes. One-minute and
three-minute views are diagnostic-only. Extended intraday views are caveated
diagnostics. No modeled holding interval may cross the exchange daily
maintenance / trade-date break.

`created_by` is `Hypothesis Scout:rq.p08.vwap_session_drafting` in every draft.
No critic, reviewer, diagnostics runner, promoter, or human capital role is
listed as drafter.

## Artifact Boundaries

No consumed `src/alpha_system/**` primitive was edited. No tests were edited.
No raw/provider/canonical data, feature values, label values, diagnostics
values, Parquet, Arrow, Feather, DBN, Zstd, SQLite, DB files, logs, caches,
secrets, or credentials were created or committed.

No review artifact, `review.md`, or `verdict.json` was created by the executor,
per the explicit executor override. Ralph owns the Yellow-lane review routing.

## Validation Results

Skipped by explicit executor override:

```text
git status --short
SKIPPED: user override forbids executor from running git status.

git diff --cached --name-only
SKIPPED: user override forbids executor from running git diff. Executor staged
nothing; Ralph owns authoritative staging-set validation.
```

Spec command:

```text
python -c "import alpha_system.governance.alpha_spec"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'alpha_system'
```

Reason: this shell does not have `src` on the default Python import path.
Supplemental repo-layout import check:

```text
PYTHONPATH=src python -c "import alpha_system.governance.alpha_spec"
(no output; exit 0)
```

Smoke:

```text
python tools/verify.py --smoke
(no output; exit 0)
```

File and quota checks:

```text
test -d research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session
(no output; exit 0)

test -f docs/futures_core_alpha_pilot/alpha_specs/vwap_session.md
(no output; exit 0)

test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P08.md
(no output; exit 0)

sh -c 'n=$(ls research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_*.md 2>/dev/null | wc -l); test "$n" -ge 6 -a "$n" -le 8'
(no output; exit 0)
```

Artifact-policy guards:

```text
git ls-files runs
(empty output; exit 0)

git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
(empty output; exit 0)
```

Additional schema validation run by the executor:

```text
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from alpha_system.governance.alpha_spec import ALPHA_SPEC_REQUIRED_FIELDS, validate_alpha_spec
root = Path('research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session')
paths = sorted(root.glob('FUTCORE-P08_vwap_session_*.md'))
print(f'draft_count={len(paths)}')
for path in paths:
    payload = json.loads(path.read_text(encoding='utf-8'))
    assert tuple(payload) == ALPHA_SPEC_REQUIRED_FIELDS, path
    validate_alpha_spec(payload)
    assert tuple(payload['cost_assumptions']['profiles'].keys()) == ('zero_cost', 'base', 'stress_1', 'stress_2', 'double_cost'), path
    print(f'{path.name}: schema_valid {payload["alpha_spec_id"]}')
PY
draft_count=8
FUTCORE-P08_vwap_session_01.md: schema_valid aspec_b40aee52d4399dd5b855a6ed
FUTCORE-P08_vwap_session_02.md: schema_valid aspec_8c9bc3ea6722e507f02b94de
FUTCORE-P08_vwap_session_03.md: schema_valid aspec_668088ee803855ce3e5617e6
FUTCORE-P08_vwap_session_04.md: schema_valid aspec_4a0e170d68918d3c787db230
FUTCORE-P08_vwap_session_05.md: schema_valid aspec_ee701ec09d58e30b746c8e06
FUTCORE-P08_vwap_session_06.md: schema_valid aspec_497f906c7b8f8ed80b64f42b
FUTCORE-P08_vwap_session_07.md: schema_valid aspec_43cd6c154bca2fcc419eee83
FUTCORE-P08_vwap_session_08.md: schema_valid aspec_5abca2fa010fc9e7174e0d7d
```
