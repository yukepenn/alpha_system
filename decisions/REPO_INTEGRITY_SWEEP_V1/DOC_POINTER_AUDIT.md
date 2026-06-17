# Repo Integrity Sweep V1 - Doc Pointer Audit

## Live Truth

`python tools/frontier/status_doctor.py` reports:

- Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`
- Status: `COMPLETED`
- Progress: merged `7/7`
- Verdict: OK
- Hook floor: `core.hooksPath = .githooks`

This report records the audit result; it is not a replacement for
`status_doctor` as the live authority.

## Docs Checked

- `AGENTS.md`
- `CRITICAL.md`
- `docs/OPERATING_COMPASS.md`
- `docs/SYSTEM_MAP.md`
- `README.md`
- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `PROGRESS.md`
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`

## Edits

- Reworded `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md` so it no longer states a current
  survivor count or uses "live exemplar" language for historical IVL examples.

## Preserved

- Historical docs that already banner themselves as not-live status.
- `docs/OPERATING_COMPASS.md`; there is only one fixed compass file and no
  `docs/OPERATING_COMPASS_V*.md` live copy.
- Generated `docs/SYSTEM_MAP.md`; no system-map regeneration was required by the
  scoped code changes.

## Guard

Targeted scan after edit:

`rg -n "Survivor count remains|live exemplar|selected live|merged [0-9]+/[0-9]+|phase [0-9]+ of|Next campaign" docs/IDEA_TO_VERDICT_SCHEMA_MAP.md docs/OPERATING_COMPASS.md README.md ACTIVE_CAMPAIGN.md PROJECT_STATUS.md PROGRESS.md`

Result: no matches.
