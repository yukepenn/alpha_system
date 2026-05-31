---
name: frontier-repair
description: Repair in-scope Frontier review findings without broadening the active spec.
---
# Frontier Repair Skill

Read:

- active spec
- handoff
- Claude review
- verdict JSON

Fix only valid in-scope review findings.

Rules:

- do not broaden scope
- do not weaken tests
- do not rewrite architecture unless review requires it and the spec allows it
- update handoff with a repair summary
- run required checks
- commit curated files only
