# FUTSUB-P03 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Phase: `FUTSUB-P03` - Continuous Series / Roll Metadata / Roll-Splice Guard Contract
Executor: Codex

## Scope Completed

- Added analytic CME equity-index quarterly roll-calendar builders in
  `src/alpha_system/data/foundation/rolls.py` using the existing `RollPolicy`
  and `RollCalendarRecord` contracts.
- Added `src/alpha_system/labels/roll_guard.py` with deterministic
  `drop | truncate | flag | invalid` cross-roll policy handling and
  `roll_window` classification.
- Added value-free config under `configs/data/roll_calendar/`.
- Added roll-guard docs and value-free research contract summary.
- Added tiny synthetic known-roll-week fixture and focused unit tests.
- Persisted approximate roll calendar records local-only under `runs/**`.

## Identifiers

- `roll_policy_id`: `roll_cme_index_futures_quarterly`
- `roll_guard_version`: `roll_guard_v1`
- Default cross-roll policy: `drop`
- Missing or ambiguous calendar policy: `drop`
- Calendar status: `unvalidated`

The calendar is analytic and approximate. It is not provider-exact splice truth
and is not reconciled to provider-internal volume-based splice metadata.

## Commit-Eligible Files For Ralph

Codex did not stage files. Ralph should stage curated paths explicitly if this
handoff is accepted.

- `README.md`
- `configs/data/roll_calendar/futsub_p03_roll_guard.json`
- `docs/futures_substrate_scaleout/ROLL_GUARD.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P03.md`
- `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_contract.md`
- `src/alpha_system/data/foundation/rolls.py`
- `src/alpha_system/labels/roll_guard.py`
- `tests/fixtures/futures_substrate_scaleout/roll_guard/known_roll_week.json`
- `tests/unit/futures_substrate_scaleout/test_roll_guard.py`

Explicit staged file list from Codex: none. Codex did not run staging, commit,
push, status, or diff commands per the executor override.

## Local-Only Artifacts

- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P03/roll_calendar_records.jsonl`
  - Generated with `PYTHONPATH=src`.
  - Contains 108 approximate `RollCalendarRecord` rows for ES/NQ/RTY, 2018
    through 2026.
  - Local-only. Do not stage or commit.

No values, registries, SQLite files, Parquet/Arrow/Feather files, provider
responses, or roll-calendar data files were staged or committed by Codex.

## Validation

Commands run from the repository root:

| Command | Result |
| --- | --- |
| `find runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1 -maxdepth 3 -name STOP -print` | exit 0, empty output |
| roll calendar persistence command 1, shown below | exit 1, failed because Python imported an older installed `alpha_system` package path instead of this worktree |
| roll calendar persistence command 2, shown below | exit 0, persisted 108 local-only records under `runs/**` |
| `python tools/verify.py --smoke` | exit 0 |
| `python tools/verify.py --lint` | exit 0; `ruff` is not installed, so the verify tool skipped lint |
| `python tools/verify.py --typecheck` | exit 0 |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_roll_guard.py -q` | exit 0; 9 tests passed |
| `python tools/hooks/canary_runner.py` | exit 0; all Frontier canaries passed |
| `test -f docs/futures_substrate_scaleout/ROLL_GUARD.md` | exit 0 |
| `test -f research/futures_substrate_scaleout_v1/roll_guard/roll_guard_contract.md` | exit 0 |
| `git ls-files runs` | exit 0, empty output |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'` | exit 0, empty output |

Roll calendar persistence command 1:

```bash
python - <<'PY'
from pathlib import Path
from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
    persist_roll_calendar_records_jsonl,
)

records = build_analytic_cme_equity_index_quarterly_roll_calendar(
    root_symbols=("ES", "NQ", "RTY"),
    start_year=2018,
    end_year=2026,
)
path = Path("runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P03/roll_calendar_records.jsonl")
persist_roll_calendar_records_jsonl(records, path)
print(f"persisted {len(records)} records to {path}")
PY
```

Roll calendar persistence command 2:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
    persist_roll_calendar_records_jsonl,
)

records = build_analytic_cme_equity_index_quarterly_roll_calendar(
    root_symbols=("ES", "NQ", "RTY"),
    start_year=2018,
    end_year=2026,
)
path = Path("runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P03/roll_calendar_records.jsonl")
persist_roll_calendar_records_jsonl(records, path)
print(f"persisted {len(records)} records to {path}")
PY
```

Commands intentionally not run by Codex due to explicit executor override:

- `git status --short`
- `git diff --cached --name-only`
- any staging, commit, push, PR, merge, review, or verdict command

No review artifacts, `review.md`, or `verdict.json` were created by Codex.
Ralph owns review routing, staged-set audit, verdict parsing, PR, CI, merge
gate, and done-check actions.
