---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P090500_PACK_OVERWRITE_GUARD
lane: yellow
status: in_progress
---

# P090500_PACK_OVERWRITE_GUARD: registry-aware write-once guard for pack rewrites

## Purpose

INCIDENT (2026-06-12T00:29-02:01Z, forensically confirmed): a coordinator
data-op ran `scaleout feature-pack --execute --force-recompute` with
trimmed-scope configs (subset of a pack's features). The value store is
pack-grained (one values.parquet per family×partition, all fvers together);
the rewrite replaced whole files with only the supplied scope — destroying
10/11 bbo, 5/10 session_calendar_maintenance, and 2/5 regime fvers on disk
across 24 partitions each (96 paths now registry-vs-disk mismatched) while
REGISTERED rows + content hashes still point at the files. The hazard is
structural and must become structurally impossible, not policy-dependent.

## Scope (in-bounds)

1. **Pre-write superset guard** in the scaleout unit execution path
   (`src/alpha_system/features/scaleout/driver.py`, where a unit's existing
   `parquet_path` is about to be replaced) and equally in any other writer
   that can replace a registered pack file (search for parquet_path writers
   under features/fast/** pack materialization): before overwriting an
   existing file, query the live feature registry for all REGISTERED
   (non-deprecated) fvers whose parquet_path equals the target; FAIL CLOSED
   unless the incoming feature set is a SUPERSET of them. Error names the
   path, the missing fvers, and the remediation ("deprecate first or run
   full-scope config"). An explicit `--allow-shrink` style override must NOT
   be added (no escape hatch).
2. **Post-write reconciliation**: after a pack write + registration, assert
   every REGISTERED fver for that path exists in the file and the stored
   content hash matches; mismatch = fail the unit loudly (no silent
   success).
3. **Repair-visibility helper**: a read-only CLI/tool subcommand (smallest
   honest surface, e.g. `scaleout pack-audit`) that sweeps all REGISTERED
   parquet paths and reports registry-vs-disk fver-set and hash mismatches
   (counts + ids only, value-free) — the tool the coordinator runs after
   any re-materialization to prove repair completeness.
4. **Tests**: synthetic registry+pack fixture → subset rewrite refused;
   superset rewrite allowed; post-write reconciliation catches a tampered
   file; pack-audit reports the three damage classes (stale-registry,
   benign-extra, clean) correctly.

## Hard constraints

- COMPOSE with existing driver/registry code; no schema changes; no changes
  to feature computation, identity, or registration semantics for valid
  (superset) runs — existing full-scope scaleout behavior must be
  bit-identical.
- No values/SQLite committed; explicit staging; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout tests/unit/features -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

Subset rewrites structurally refused at both write sites; post-write
reconciliation loud; pack-audit tool reports mismatches; full-scope behavior
unchanged; validation green incl. ci-parity; truthful handoff; fresh
adversarial review PASS/PASS_WITH_WARNINGS under
reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
