# ALPHA_RESEARCH_RUNTIME_MVP / RT-P00 Handoff

## Scope

RT-P00 bootstrap created the durable `docs/research_runtime/` documentation root,
updated the root README snapshot for the active Research Runtime campaign, and
confirmed the six campaign contract files are present. Runtime code, tests,
review artifacts, verdict artifacts, run-local artifacts, and `ACTIVE_CAMPAIGN.md`
were not modified by this phase branch.

## Explicit Staging

Codex did not run `git add` or stage files because the executor prompt forbids
all staging. Exact staged file list by Codex:

- none

Ralph should stage only these commit-eligible paths if the driver accepts this
handoff:

- `docs/research_runtime/README.md`
- `docs/research_runtime/OVERVIEW.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00.md`

No campaign contract files required edits; the existing files under
`campaigns/ALPHA_RESEARCH_RUNTIME_MVP/` were present and parseable.

## Validation

- `git status --short`: skipped. The executor prompt explicitly forbids Codex
  from running `git status`; Ralph owns the authoritative status/staged-set
  inspection.
- `test -f ACTIVE_CAMPAIGN.md`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RISK_REGISTER.md`: OK.
- `test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md`: OK.
- `test '!' -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACTIVE_CAMPAIGN.md`: OK.
- `test -f docs/research_runtime/README.md`: OK.
- `test -f docs/research_runtime/OVERVIEW.md`: OK.
- `test -f handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00.md`: OK.
- `grep -q "ALPHA_RESEARCH_RUNTIME_MVP" ACTIVE_CAMPAIGN.md`: OK.
- `python -c "import yaml; d=yaml.safe_load(open('campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml')); ids=[p['id'] for p in d['phases']]; assert ids==[f'RT-P{n:02d}' for n in range(27)], ids; gp=[p for g in d['acceptance_gates'].values() for p in g['phases']]; assert sorted(gp)==sorted(ids) and len(gp)==len(ids); print('campaign.yaml OK:', len(ids), 'phases; gates cover each phase once')"`:
  OK. Output: `campaign.yaml OK: 27 phases; gates cover each phase once`.
- Additional campaign scope check for scheduler and lane consistency: OK. Output:
  `campaign scheduler OK: dag_wave; parallel_execution true; serial merge; no RED phases`.
- STOP check before smoke: OK. Output: `STOP absent before smoke`.
- `python tools/verify.py --smoke`: OK, exit code 0, no stdout.
- `git ls-files runs`: OK, empty stdout.

## Artifact Audit

- `git ls-files runs` returned empty; no `runs/` path is tracked.
- Codex did not run `git add`; no path was staged by this executor.
- No `runs/` path was staged by this executor.
- `ACTIVE_CAMPAIGN.md` was read and grepped only; it was not modified by this
  phase branch.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was created.
- No review artifact, verdict artifact, runtime code, tests, data path, DB path,
  cache path, log path, or heavy artifact path was created or edited by this
  phase.
- Staged forbidden-path inspection via `git status --short` or
  `git diff --cached --name-only` was not performed because the executor prompt
  forbids `git status` and `git diff`. Ralph should perform the authoritative
  staged-set audit before committing.

## Caveats And Follow-Ups

RT-P01 should implement the runtime entry contract after Feature/Label using the
campaign boundaries recorded here: accepted DatasetVersion-only consumption,
Feature/Label store inputs, `AlphaSpec` plus `StudySpec` required, no raw
provider access, and no broker/live/paper/order/account scope.
