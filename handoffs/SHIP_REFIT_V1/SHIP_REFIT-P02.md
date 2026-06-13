# SHIP_REFIT-P02 Handoff

## Scope Completed

- Replaced surrogate execution's per-seed shuffled-label JSONL materialization
  with pure-Python permutation-index relabeling in
  `src/alpha_system/governance/surrogate_run.py`.
- Kept the reference materialized writers (`write_label_shuffled_copy`,
  `write_trade_date_block_shuffled_copy`,
  `write_trade_date_block_bootstrap_copy`) and made them share the same
  permutation-index builders used by the fast path.
- Added an in-memory diagnostic panel in
  `src/alpha_system/research/diagnostics.py` so calibration can align once and
  reuse factor/time/horizon/stability grouping across seeds. The directional
  fast branch reuses precomputed factor ranks, label-source ranks, grouped
  indices, and factor-side Pearson terms when the panel is complete and numeric;
  unsupported or broader diagnostic requests still fall back to the existing
  summary path.
- Routed `calibrate_surrogate_fdr` through the batched panel path while
  preserving the existing `spec_index -> seed` formula:
  `base_seed + spec_index * run_budget + run_index`.
- Preserved per-seed study outputs, ledgers, surrogate records, detection
  threshold, zero-pass aggregation, and constant-factor exclusion behavior.
- Added the real-surrogate calibration guardrail:
  missing `--runs-per-config` defaults to `60`, oversized values cap at `60`,
  and explicit in-bound values pass through unchanged.
- Added parity/no-copy tests and docs:
  `tests/unit/governance/test_surrogate_run.py`,
  `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`,
  `docs/ship_refit_v1/DIAGNOSTICS_FAST_PATH.md`,
  `docs/ship_refit_v1/README.md`, and `README.md`.

## Parity Result

- Parity harness:
  `PYTHONPATH=src python -m pytest tests/unit/governance/test_surrogate_run.py -q`
  passed with `22 passed`.
- Hard parity test:
  `test_surrogate_fast_path_matches_reference_diagnostic_summary_hashes_for_10_seeds`.
- Fixed committed sample identity:
  `tests/fixtures/governance/study_spec_valid.json` via the synthetic
  `_study_spec` fixture in `tests/unit/governance/test_surrogate_run.py`.
- Seeds: `700..709` (`10` seeds).
- Proof: for each seed, the test writes the reference shuffled-label JSONL at
  the exact path used in the StudyConfig, computes and hashes
  `diagnostic_summary.json`, deletes the label copy, runs the fast path with the
  same config identity, and asserts SHA-256 hash equality. It also asserts the
  fast path leaves no `seed_<n>/labels/*.jsonl` file.

## Measurement

Command shape used for the K=60 measurement:

```bash
PYTHONPATH=src python - <<'PY'
# Inline local script generated a deterministic 10,000-row StudySpec from
# tests/fixtures/governance/study_spec_valid.json, ran seeds 3000..3059
# through the materialized reference path and the panel fast path at identical
# StudyConfig paths, SHA-256 compared diagnostic_summary.json bytes, and counted
# seed_<n>/labels/label_shuffle.jsonl writes.
PY
```

Result:

```json
{
  "sample": "deterministic synthetic 10000-row StudySpec derived from tests/fixtures/governance/study_spec_valid.json",
  "n_rows": 10000,
  "seed_count": 60,
  "seeds": [3000, 3059],
  "hashes_equal": true,
  "reference_seconds": 25.852788,
  "fast_seconds": 2.263115,
  "wall_clock_reduction_x": 11.424,
  "reference_label_copy_writes": 60,
  "fast_label_copy_writes": 0,
  "label_write_reduction": "infinite"
}
```

## Validation

- `python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('FORBIDDEN dependency importable: '+','.join(bad) if bad else 0)"`
  — PASS; no forbidden dependency importable.
- `PYTHONPATH=src python -m pytest tests -k "surrogate or fast_path or permutation or calibration" -q`
  — PASS; `112 passed, 64 skipped, 3237 deselected`.
- `python tools/verify.py --smoke` — PASS; exited 0.
- `python tools/hooks/canary_runner.py` — PASS; all Frontier canaries passed,
  including `planted_fake_alpha` and the TRUE-alpha detection pair.
- `python tools/verify.py --all` — FAIL in the inherited executor environment:
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  selected `RuntimeCacheStorageKind.ALPHA_DATA_ROOT` because
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` was exported.
  This is the known dirty-env cache-policy interaction, not a P02 regression.
- `env -u ALPHA_DATA_ROOT python tools/verify.py --all` — PASS;
  `3333 passed, 80 skipped`.
- `git ls-files runs` — PASS; printed nothing.

## Invariants And Boundaries

- No numpy, pandas, polars, or runtime dependency was added.
- `pyproject.toml` dependencies remain untouched.
- Detection threshold and surrogate-FDR zero-pass criterion are unchanged.
- Constant-factor zero-variance exclusion in
  `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` is unchanged.
- The `spec_index -> seed` mapping is unchanged.
- The fast path writes no per-seed shuffled-label JSONL copy; only existing
  study outputs, ledgers, and surrogate records remain.
- No data, registry, SQLite, Parquet, Arrow, Feather, log, broker, live,
  paper-trading, deployment, PR, merge, review, or verdict artifact was created.
- No `runs/` path was written for commit eligibility, and `git ls-files runs`
  is empty.

## Files For Ralph To Stage Explicitly

- `README.md`
- `docs/ship_refit_v1/README.md`
- `docs/ship_refit_v1/DIAGNOSTICS_FAST_PATH.md`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/research/diagnostics.py`
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `tests/unit/governance/test_surrogate_run.py`
- `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`
- `handoffs/SHIP_REFIT_V1/SHIP_REFIT-P02.md`

## Review Status

YELLOW-lane review remains Ralph/reviewer-owned. Per executor instructions, no
Claude call, `review.md`, `verdict.json`, PR, merge, staging, commit, push, or
PASS marking was performed by Codex.
