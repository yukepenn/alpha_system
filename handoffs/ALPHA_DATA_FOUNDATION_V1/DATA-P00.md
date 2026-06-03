# DATA-P00 Handoff - Data Foundation Campaign Bootstrap

## Branch And Commit State

Branch:

```text
auto/alpha_data_foundation_v1/data-p00-data-foundation-campaign-bootstrap
```

No commit was created by Codex. The DATA-P00 files are staged explicitly for
Ralph-owned handoff validation, review routing, commit, PR, CI, merge gates,
merge, and run summary.

This handoff does not mark `DATA-P00` as `PASS`.

Commits:

```text
No commit was created by Codex.
```

## Scope Completed

Created the data-foundation docs root:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

Updated `README.md` with the DATA-P00 snapshot:

- `ALPHA_DATA_FOUNDATION_V1` is the active campaign.
- `DATA-P00` is complete at executor handoff, with Ralph-owned review,
  verdict parsing, semantic done-check, PR, CI, and merge gates still required
  before any phase PASS is recorded.
- `DATA-P01` - Data Package Skeleton and Naming - is the next phase.
- The new durable docs root is `docs/data_foundation/`.
- Safety boundaries remain unchanged: IBKR read-only historical only; no
  broker, order, account, paper, live, or real-time signal scope; clientId
  `101`/`102` hard-blocked; data namespace `201-209`; real data local-only;
  explicit staging only.

Confirmed `ACTIVE_CAMPAIGN.md` already points to `ALPHA_DATA_FOUNDATION_V1`.
It was not edited because the required root campaign pointer was already
correct. No campaign-local `campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md`
was created.

Confirmed the campaign contract bundle is present under
`campaigns/ALPHA_DATA_FOUNDATION_V1/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

Executor inspection found the generated phase scope aligned with the contract
bundle for `DATA-P00`: phase ID `DATA-P00`, name `Data Foundation Campaign
Bootstrap`, lane `YELLOW`, no dependencies, and acceptance gate
`campaign_bootstrap`.

No campaign contract file was rewritten.

## Files Changed

- `README.md`
- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md`

## Staged Files

Exact files staged explicitly:

```text
README.md
docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md
```

`ACTIVE_CAMPAIGN.md` was confirmed but not staged because it did not require an
edit. The campaign contract bundle was confirmed but not staged because no
contract file required an edit.

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed after explicit staging with only curated
  DATA-P00 paths:

```text
M  README.md
A  docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md
A  docs/data_foundation/README.md
A  handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md
```

- `test -f ACTIVE_CAMPAIGN.md` - passed with exit 0 and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md` - passed with exit 0
  and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md` - passed with
  exit 0 and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml` - passed with
  exit 0 and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md` - passed with
  exit 0 and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md` - passed with
  exit 0 and no output.
- `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md` - passed with exit 0
  and no output.
- `test '!' -f campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md` - passed
  with exit 0 and no output.
- `test -f docs/data_foundation/README.md` - passed with exit 0 and no output.
- `test -f docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md` - passed with
  exit 0 and no output.
- `test -f handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md` - passed with exit
  0 and no output.
- `grep -q "ALPHA_DATA_FOUNDATION_V1" ACTIVE_CAMPAIGN.md` - passed with exit
  0 and no output.
- `python tools/verify.py --smoke` - passed with exit 0.
- `git ls-files runs` - passed with empty output.

Skipped checks: none.

## Non-Runs And Why

- `python tools/verify.py --all` was not run because DATA-P00 requested smoke
  validation only.
- `python tools/hooks/canary_runner.py` was not run because it was not part of
  the generated phase spec validation set.
- Reviewer execution, Claude calls, `review.md`, `verdict.json`, PR creation,
  merge, and phase PASS marking were not run because the prompt assigns those
  gates to Ralph and the independent reviewer.
- No run-local `runs/<run_id>/phases/DATA-P00/handoff.md` was written because
  the spec required the commit-eligible handoff under
  `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md` and local run artifacts must
  not be staged.

## Artifact Policy

- `git ls-files runs` returned empty output.
- `git diff --cached --name-only` returned exactly:

```text
README.md
docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P00.md
```

- `git diff --name-only` returned empty output after explicit staging.
- `git diff --cached --name-only | rg '^runs/'` returned no matches.
- The staged set contains no raw data, canonical data, factor data, label data,
  cache data, provider response, account artifact, local DB file, log, heavy
  artifact, Parquet, Arrow, Feather, or run artifact path.
- No run-local `runs/<run_id>/phases/DATA-P00/handoff.md` was created or
  staged.
- No `review.md` or `verdict.json` was created.

## Staging Discipline

- Explicit staging only.
- Staged paths were provided by name.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No commit was created by Codex.

## Scope Confirmation

- No `src/alpha_system/data/**` source was added or modified.
- No `tests/**` files were added or modified.
- No configs or templates were added or modified.
- No IBKR connector code was added.
- No `src/alpha_system/data/ibkr/**`,
  `src/alpha_system/execution/broker/**`, `live/**`, `paper/**`, or
  `order_router*` path was added.
- No broker, live, paper, order-routing, account, real-time feed, provider
  pull, external call, deployment, alpha search, factor research, label
  research, strategy research, ML/DL, L2 replay, optimization, or portfolio
  allocation scope was added.
- No alpha, profitability, tradability, or production-readiness claim was
  added.

## Risks Or Caveats

- Independent semantic review, handoff validation, verdict parsing, semantic
  done-check, PR, CI, and merge gates remain pending for Ralph-owned workflow
  states.
- `ACTIVE_CAMPAIGN.md` was confirmed as the correct root pointer but was not
  edited; its run/phase bookkeeping remains Ralph-owned.
- The README states DATA-P00 completion at executor handoff only and does not
  record a phase PASS.

## Review Request Focus

- Confirm the data-foundation docs describe object names, lifecycle states,
  prohibited MVP states, and IBKR read-only posture without implementing source,
  tests, schemas, validation, connector behavior, or pull behavior.
- Confirm the README snapshot is compact, factual, and free of run-local paths,
  market-result claims, broker/live/paper/deployment behavior, or duplicated
  handoff content.
- Confirm the staged set is commit-eligible only and contains no `runs/**` or
  forbidden data/provider/account/heavy/DB artifacts.

## Next Recommended Step

Ralph should validate this handoff, run the independent DATA-P00 semantic
review, parse the reviewer verdict, and continue through the configured
Workflow 2 gates.
