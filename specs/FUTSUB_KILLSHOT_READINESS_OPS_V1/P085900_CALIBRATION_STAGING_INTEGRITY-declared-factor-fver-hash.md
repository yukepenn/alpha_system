---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P085900_CALIBRATION_STAGING_INTEGRITY
lane: yellow
status: in_progress
---

# P085900_CALIBRATION_STAGING_INTEGRITY: stage the declared factor, fver-filtered, hash-verified

## Purpose

LIVE FINDINGS (2026-06-12, real-data calibration forensics): the surrogate
staging bridge in `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
has two integrity defects that made ALL SIX per-family calibrations run on
wrong factor data:
(1) `:319` picks the factor as `sorted(candidates)[0]` over the sspec's FULL
feature-lock set (528 locks spanning many families) — the "vwap_session"
calibration actually staged `session_calendar_roll_minutes_to_roll`; the
"bbo" one staged `bbo_tradability_bad_quote_flag`.
(2) `_load_value_rows` (`:724`) loads the entire Parquet at
`record.parquet_path` with NO feature_version_id filtering and NO content-hash
verification — when a pack file was overwritten on disk (the 2019 bbo packs
were clobbered 2026-06-12T02:01Z by a spread_zscore-only re-materialization),
staging silently produced rows stamped `factor_id=bad_quote_flag` carrying
spread_zscore values. Mislabeled data is worse than missing data.

## Scope (in-bounds)

1. **Declared-factor selection (one truth)**: find how the study runtime
   constructs `StudyConfig.factor_id` for a StudySpec (the path FUTSUB-P28 /
   the FUTCORE study runner uses — search src/alpha_system/research/ +
   runtime/ for StudyConfig construction from StudySpec/alpha_spec; the
   original FUTCORE studies ran per-factor configs). The calibration tool
   must derive its factor the SAME way (reuse/extract that code path, never
   a parallel rule). If the study runs multiple factors for a family, the
   calibration stages and reports the SAME set (per-factor sub-configs in
   one report). If derivation is ambiguous for a given sspec, FAIL CLOSED
   with a ValidationIssue naming what was missing — never fall back to
   sorted()[0].
2. **fver filtering**: stage only rows whose feature_version_id matches the
   sspec's lock for the chosen factor (and data_version/partition scope);
   row counts logged in the report provenance (counts only, value-free).
3. **Content-hash verification**: before staging, verify the pack file
   against the registry's recorded content/manifest hash (find the existing
   hash fields — the registry records value_content_hash/manifest hashes;
   reuse the existing verification helper if one exists in
   feature_lock_validation or the resolver). Mismatch = fail-closed error
   naming the path and both hashes (this must CATCH the clobbered 2019 bbo
   packs today — add a test fixture reproducing hash-mismatch refusal).
4. **Label-side same treatment**: labels staged for the declared label
   (config.label_id path) with lock/version filtering + hash verification;
   verify (and assert in a test) the staged label rows match the sspec's
   label_pack_locks. Also surface (report provenance) whether any locked
   label pack carries off-grid event_ts (the cost/spread-adjusted mirror
   defect) — count only, no behavior change.
5. **Tests**: synthetic multi-fver Parquet fixture → only the declared
   fver's rows staged; hash-mismatch fixture → refusal; ambiguous-factor
   fixture → refusal; rescore mode unaffected for valid namespaces; the
   six committed rerun sspecs each resolve to an UNAMBIGUOUS declared factor
   via the runtime rule (loud condition-driven skip if local registry absent,
   sanctioned idiom).

## Hard constraints

- ONE TRUTH: factor derivation reuses the study-runtime path; hash
  verification reuses existing registry/validation helpers (extract-shared,
  never duplicate). No changes to diagnostics join semantics, perturbation
  writers, detection statistic, or any gate.
- No src/alpha_system/{features,labels,runtime}/** behavior changes (a pure
  extract-to-shared refactor of the factor-derivation helper is allowed if
  the runtime path keeps identical behavior + its tests stay green).
- Values stay in isolated namespaces; explicit staging; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance tests/unit/discovery_rigor_floor -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/research -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

Tool stages the study's declared factor (runtime-derived, one truth),
fver-filtered, hash-verified, fail-closed on ambiguity/mismatch (clobbered-pack
class caught by test); label staging verified; validation green incl.
ci-parity; truthful handoff; fresh adversarial review PASS/PASS_WITH_WARNINGS
under reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
