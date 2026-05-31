# Phase Plan

Every phase must define id, lane, dependencies, purpose, scope, non-goals, expected files, forbidden changes, validation, artifact policy, done criteria, handoff requirement, review requirement, and auto-merge eligibility.

## P01_TEMPLATE

- Lane: yellow
- Dependencies: none
- Purpose: define the first reviewable increment.
- Scope:
  - TBD
- Non-goals:
  - TBD
- Expected files:
  - `specs/000-template/P01-template.md`
- Forbidden changes:
  - out-of-scope files
  - secrets
  - raw data
- Validation:
  - `python tools/verify.py --smoke`
- Artifact policy:
  - commit source, docs, specs, handoffs, reviews, decisions, and curated tests only
- Done criteria:
  - scope complete
  - validation recorded
  - handoff written
  - review complete
- Handoff requirement: `handoffs/000-template/P01_TEMPLATE.md`
- Review requirement: `reviews/000-template/P01_TEMPLATE-review.md`
- Auto-merge eligibility: yes, if lane policy passes

## P02_TEMPLATE

- Lane: yellow
- Dependencies: P01_TEMPLATE
- Purpose: define the next increment if needed.
- Scope:
  - TBD
- Non-goals:
  - TBD
- Expected files:
  - TBD
- Forbidden changes:
  - TBD
- Validation:
  - `python tools/verify.py --all`
- Artifact policy:
  - follow `frontier.yaml`
- Done criteria:
  - TBD
- Handoff requirement: required
- Review requirement: required
- Auto-merge eligibility: yes, if lane policy passes
