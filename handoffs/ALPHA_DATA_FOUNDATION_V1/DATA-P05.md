# DATA-P05 Handoff - Futures Instrument Master and Contract Economics

## Scope Executed

Implemented the DATA-P05 root-level futures instrument master under
`src/alpha_system/data/foundation/instruments.py`.

`InstrumentMasterRecord` now carries the campaign-required fields:

- `root_symbol`
- `ib_symbol`
- `exchange`
- `currency`
- `asset_class`
- `sec_type`
- `point_value`
- `tick_size`
- `tick_value`
- `multiplier`
- `timezone`
- `session_template_id`
- `roll_policy_id`
- `source`
- `source_retrieved_at`

Validation is fail-closed for missing config fields, empty text fields,
non-positive decimal economics, non-timezone-aware `source_retrieved_at`,
non-explicit timezone values, non-`FUT` `sec_type`, source IDs without the
`dsrc_` prefix, and exact `tick_value != tick_size * point_value`.

## Encoded Anchors

The six futures contract-economics anchors are encoded in
`configs/data/futures_instrument_master.json` with:

```text
anchor_status: to_be_verified_economic_anchor
certification_status: not_production_certified
source: dsrc_campaign_goal_contract_economics
source_retrieved_at: 2026-06-03T00:00:00+00:00
```

| Root | Point value | Tick size | Tick value | Multiplier |
| --- | ---: | ---: | ---: | ---: |
| `ES` | `50` | `0.25` | `12.50` | `50` |
| `NQ` | `20` | `0.25` | `5.00` | `20` |
| `RTY` | `50` | `0.10` | `5.00` | `50` |
| `MES` | `5` | `0.25` | `1.25` | `5` |
| `MNQ` | `2` | `0.25` | `0.50` | `2` |
| `M2K` | `5` | `0.10` | `0.50` | `5` |

All six anchors use `CME`, `USD`, `index_future`, `FUT`, and
`America/Chicago`. `session_template_id` and `roll_policy_id` are stored only
as future-phase references: `session_cme_index_futures_eth` and
`roll_cme_index_futures_quarterly`.

## Verification Method

The loader reads the declarative config, validates the to-be-verified and
not-production-certified posture, builds immutable `InstrumentMasterRecord`
instances, verifies unique roots, and validates exact `Decimal` arithmetic for
`tick_value = tick_size * point_value`.

`tests/unit/data/test_instrument_master.py` includes:

- one per-root economics assertion for `ES`, `NQ`, `RTY`, `MES`, `MNQ`, and
  `M2K`;
- required-field coverage for `REQUIRED_INSTRUMENT_MASTER_FIELDS`;
- fail-closed coverage for missing `tick_value`, bad tick value, non-positive
  `point_value`/`tick_size`, empty or implicit timezone, bad source prefix, and
  naive `source_retrieved_at`;
- config posture coverage rejecting a production-certified marker.

## README Snapshot

`README.md` was updated to record the DATA-P05 executor scope:
`InstrumentMasterRecord`, the six to-be-verified contract-economics anchors,
the exact tick-value validation, and
`docs/data_foundation/INSTRUMENT_MASTER.md`.

The README snapshot keeps the reviewed passing baseline at `DATA-P00` through
`DATA-P04` (5 of 25 phases) until Ralph review, verdict parsing, semantic
done-check, PR, CI, and merge gates record the DATA-P05 outcome. It also
restates the unchanged safety boundaries: IBKR read-only historical only,
clientId `101`/`102` fail-closed, data namespace `201-209`, no
broker/order/account/paper/live scope, real data local-only, and no
alpha/profitability/tradability claims.

## Validation Results

All requested and recommended local checks passed. No checks were skipped.

| Command | Result |
| --- | --- |
| `git status --short` | Ran before handoff/staging; showed only DATA-P05 source/config/test/doc/README changes. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `150 passed in 0.09s`. |
| `test -f docs/data_foundation/INSTRUMENT_MASTER.md` | Passed with no output. |
| `git ls-files runs` | Passed; output empty. |
| `python -m pytest tests/unit/data -q -k "instrument or economics"` | Passed: `18 passed, 132 deselected in 0.04s`. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed; output empty. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed; output empty. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed; output empty. |

## Explicit Staged File Set

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

```text
README.md
configs/data/futures_instrument_master.json
docs/data_foundation/INSTRUMENT_MASTER.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P05.md
src/alpha_system/data/foundation/instruments.py
tests/unit/data/test_instrument_master.py
```

Explicit staging discipline was used. `git add .` and `git add -A` were not
used. The run-local mirror
`runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/phases/DATA-P05/handoff.md`
is local-only and must not be staged or committed.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the verified staged set.
- No raw data, canonical data, factor data, label data, cache data, provider
  responses, account artifacts, DB files, logs, Parquet/Arrow/Feather files,
  model artifacts, or heavy artifacts were produced or staged.
- No external IBKR call, network provider pull, broker call, paper/live action,
  order routing, account access, or deployment was performed.

## Commit And Push Status

- Local executor commit was created.
- Push was attempted with `GIT_TERMINAL_PROMPT=0 git push origin HEAD`.
- Push failed because network DNS could not resolve GitHub:
  `fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com`.
- No PR, merge, verdict, PASS marker, or reviewer artifact was created.

## Non-Goals Preserved

- No current/front-month contract selection was introduced.
- No `trading_class` or `con_id` was added to `InstrumentMasterRecord`.
- No session template, trading calendar, roll calendar, or current roll logic
  was implemented.
- No broker/order/account/paper/live scope was introduced.
- No alpha, profitability, tradability, execution-sizing certification, broker
  readiness, production-readiness, or data-completeness claim was introduced.

## Review Status

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns review,
verdict parsing, done-checks, PR, CI, merge gate, and final phase outcome.
