---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P200000_FUTSUB_EXPOSURE_GUARD_LIFECYCLE
lane: yellow
status: in_progress
---

# P200000_FUTSUB_EXPOSURE_GUARD_LIFECYCLE: exposure guard must not count deprecated rows as active exposures

## Purpose

Coordinator re-materialization of the repaired session pack (post-P183000)
is blocked by `FeatureRequestGateError: duplicate-exposure guard found a
blocking exposure` even AFTER the 120 degenerate session FeatureVersions
were deprecated via the sanctioned API. Root cause (verified):
`FeatureRegistry.read_factor_versions` (`src/alpha_system/features/registry.py:747`)
— the read-only view injected into the governance duplicate-exposure guard —
selects ALL `feature_registry_records` with NO lifecycle filter. A
DEPRECATED row therefore still registers as an active blocking exposure,
which makes sanctioned supersession structurally impossible: a repaired
feature can never be re-implemented because its own deprecated predecessor
blocks it forever.

This is the same defect class as PR #362's F1 (lifecycle-blind read paths)
in a third location. The #362 admissibility decision applies: REGISTERED is
the only active state; DEPRECATED rows are historical audit records, not
active exposures. The guard's multiplicity-control purpose is preserved —
REGISTERED duplicates still block.

## Scope (in-bounds)

1. `src/alpha_system/features/registry.py` `read_factor_versions`: exclude
   non-REGISTERED rows from the duplicate-exposure guard view (SQL WHERE or
   post-load filter — match local style). Raw audit reads elsewhere
   unchanged.
2. Check the symmetric label-side guard view if one exists
   (`labels/registry.py` — any read_factor_versions-like exposure reader):
   close identically or record absence (file:line) in the handoff.
3. Tests (production-path, mutation-killable):
   - a DEPRECATED feature row does NOT produce a blocking exposure for a
     new equivalent FeatureRequest (guard passes);
   - an identical REGISTERED row STILL produces the blocking finding
     (multiplicity control intact — this assertion must fail if the filter
     is over-broadened);
   - registry raw reads still return deprecated rows.

## Hard constraints

- FORBIDDEN: registry write-paths/schema, `governance/duplicate_exposure.py`
  semantics (the guard logic itself is correct; only the injected VIEW is
  lifecycle-blind), labels value/engine code, weakening any existing guard
  test.
- No values/SQLite/runs committed; explicit staging only.
- Do NOT run any `git worktree` command; do not modify .git config.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "exposure or request_gate or registry" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite green modulo the 3 known pre-existing env failures; exact counts
in the handoff.

## Done criteria

- Deprecated rows no longer block supersession; REGISTERED duplicates still
  block (both proven by tests); full validation green; truthful handoff;
  fresh adversarial review verdict PASS or PASS_WITH_WARNINGS under
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
