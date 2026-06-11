# Adversarial Review — P172002_LCFP_P08_PANEL_CACHE_SPEEDUP (repair/lcfp-p08-blockers)

- Campaign: `LABEL_COMPUTE_FAST_PATH_V1`
- Phase: `P172002_LCFP_P08_PANEL_CACHE_SPEEDUP` (WF1 phase layered on the LCFP-P08 repair branch)
- Reviewer: fresh adversarial reviewer (frontier-review discipline), no stake in the diff
- Review target: entire uncommitted working tree vs `origin/main` (10 tracked files + 4 reviewed untracked files + `tools/label_compute_fast_path/benchmark_gate.py` + `tests/unit/label_compute_fast_path/test_benchmark_gate.py`)
- Date: 2026-06-10
- Verdict: **REWORK** (severity: warning — no correctness/safety violation found; two honesty-mechanics repairs required before this branch can satisfy the amended P08 contract)

## Verification actually run (research venv, PYTHONPATH=src, real ALPHA_DATA_ROOT)

- `pytest tests/unit/label_compute_fast_path/ tests/unit/futures_substrate_scaleout/labels/` → 71 passed
- `pytest tests/unit/futures_substrate_scaleout/` (full, driver-coupling check) → 83 passed
- `pytest tests/unit/feature_compute_fast_path/ tests/no_lookahead/feature_label/test_synthetic_fail_closed.py tests/unit/test_fast_path_artifact_policy.py` → 65 passed
- `python tools/verify.py --smoke` → exit 0
- `python tools/hooks/canary_runner.py` → all canaries PASS
- `git ls-files runs` → empty; parquet/sqlite/arrow/feather/db globs → empty; no `runs/**` in `git status`

## Checklist results

### 1. Contract surgery honesty — HONEST RE-SCOPING, but the gate code was not brought along (required repair 2)

- The amendment is explicit, dated, and attributed in BOTH texts:
  `campaigns/LABEL_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md` (worker-policy bullet, "*Amended 2026-06-10 after the first P08 attempt honestly returned BLOCKED_SPEEDUP; rationale in WF1 phase P172002_LCFP_P08_PANEL_CACHE_SPEEDUP*") and `campaign.yaml` LCFP-P08 `done_criteria` ("[Criterion amended 2026-06-10 ...]"). The two texts are semantically consistent with each other.
- The hard floor is preserved: both texts keep "the path family ... MUST be measured materially faster on the fast path". Slow families must be "documented honestly with component timings ... and stay on the reference engine". Both engines remain parity-gated, so correctness is engine-independent. This is evidence-driven re-scoping, not gate weakening: the committed benchmark shows path at 3.12x–10.29x compute speedup and cheap families at 0.32x–1.00x with the dominant residual disclosed per component.
- Claim tracing: "9.24 hr reference bottleneck" → committed P01 baseline (`research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md:51`). The 0.34–0.73x / 0.36–0.53x figures in the WF1 spec → committed `benchmark_summary.md` worker-sweep table. PASS.
- **Gap (warning):** the campaign.yaml rationale also cites profiling ("cheap-family warm residual is kernel + value-store write with the panel cache already in place") that exists in no committed artifact. It is rationale, not a speed claim, and the amendment itself says speed claims come only from the committed benchmark — acceptable, but the re-run summary should make the cheap-family component decomposition carry this on its own.
- **Required repair 2:** `tools/label_compute_fast_path/benchmark_gate.py` still encodes the PRE-amendment criterion: `run_benchmark` sets `BLOCKED_SPEEDUP` whenever ANY family's selected speedup ≤ 1.0 (benchmark_gate.py:676–686), and `render_summary_markdown` emits only a single global "Production Worker Policy" — there is no per-family engine + worker policy section anywhere in the summary. The amended done_criterion requires the committed summary to carry "the selected production engine + worker policy PER FAMILY". As written, even the post-cache re-run will (a) print a status that contradicts the amended contract when cheap families stay ≤ 1.0, and (b) omit the field the contract now requires. Align the gate (path-family ≤ 1.0 must remain a hard block; cheap families ≤ 1.0 must produce a per-family reference-engine selection, not a global block) before the P08 re-review.

### 2. Cache safety — PASS

- Frame cache key is the full frozen `LabelPanelFrameRequest` (`labels/fast/materializer.py`): canonical_root + OHLCV `dataset_version_id` + `bbo_dataset_version_id` + symbol + year + start/end ts + both partition schemas. A different dataset version or window can never alias a cached frame (worst case for `str` vs `Path` root or `None` vs explicit window is a cache MISS, the safe direction).
- Bounded: `_FRAME_CACHE_MAX_ENTRIES = 2`, FIFO eviction; eviction also pops the evicted frame's derived `_panel_cache` and `_terminal_model_cache` entries, so a derived panel cannot outlive its frame bound.
- The id()-keyed `_panel_cache` stores `(price_frame, panel)` with a strong reference plus an `cached[0] is price_frame` identity check — id reuse against a live entry is impossible, and the identity check covers it anyway. `SharedLabelPanel` direct inputs bypass the cache entirely.
- `_COST_MODEL_CONSTANTS` is keyed by content-addressed `label_version_id` (same id ⇒ same cost model by construction), bounded at 64. `lru_cache` on `_maintenance_local_cached` and `_root_symbol_cached` (`labels/fast/panel.py`) memoize pure functions (timezone conversion of an instant; regex on a string triple) — equal-instant datetime key collisions across tzinfo produce identical outputs.
- Process-local only: materializer instance dicts + module globals; `_shared_fast_label_materializer` is per-process; worker processes get their own. `reset_fast_label_materializer_caches()` (driver) clears all of it and is called at the top of every benchmark cell (`benchmark_gate.py:_run_worker_count`), so cells start cold exactly as the methodology text claims.
- Reference engine untouched: `git diff` contains no `labels/families/**` change; the oracle is read-only.

### 3. Semantic invisibility — PASS, real proof not a proxy

`tests/unit/label_compute_fast_path/test_panel_frame_cache.py` compares cached (one shared materializer, repeated requests) vs uncached (fresh materializer per run) on (a) full record-set equality and (b) registry-eligible payload identity = `compute_value_content_hash(_canonical_record_dicts(records))` + `metadata.to_dict()` — the actual content hash and metadata that reach the registry. Also proven: loader called exactly once per dataset-version pair; no aliasing across OHLCV or BBO dataset versions (every distinct pair reloads); FIFO bound enforced with derived caches; driver materializer process-local and cold-start resettable.

### 4. Parity / guard / identity — PASS

- No parity comparison, tolerance, or harness change: `tests/unit/feature_compute_fast_path/parity_harness.py` unmodified; tracked test diffs are purely additive (`test_path_label_pack.py` +98, `test_session_maintenance_cost_pack.py` +187, fixtures +56); the 1e-12 path tolerance in new tests matches the pre-existing tolerance at `test_path_label_pack.py:75` (unchanged).
- The path fast-kernel rewrite (`labels/fast/path.py`) REMOVES the roll/maintenance-guarded fixed-minute terminal model — verified against the oracle: `src/alpha_system/labels/families/path/family.py` `compute_path_label` resolves `horizon_steps` positionally over real trade rows with NO roll/maintenance guard and no contract filtering. The old guarded fast kernel was the bug (dropped 1628 records the reference emits); the new kernel reproduces reference semantics, and the benchmark's per-definition record-set check (`benchmark_gate.py:_confirm_unit_parity`, exact key-set equality before value comparison) plus the new gap/roll-window regression tests pin it. `label_available_ts` still derives through `derive_label_available_ts`; `label_version_id` stays content-addressed from the spec (fast path emits values only).
- Name-grain unit identity protected by a golden-id test (`test_label_horizon_grid_coverage.py:106`, `mbu_68b7777e24a6eb98ef16e40d`), so FUTSUB P16–P18 materialized unit ids are unchanged by the grid repair.

### 5. Engine default — PASS

`driver.py:838–841`: `engine=None` ⇒ label configs default to the REFERENCE engine until LCFP acceptance; `engine="v1"` is an explicit opt-in. `_resolve_engine_token` untouched by this diff; the benchmark gate opts in explicitly. No default flip anywhere in CLI/driver/benchmark.

### 6. Benchmark honesty — methodology/code MATCH; but the committed summary is stale vs this code (required repair 1)

- Timer placement verified in `benchmark_gate.py:_run_worker_count`: Component 1 = fast compute only (lines 793–821, includes panel load + compute + unit Parquet write), Component 2 = serial registration (823–844), Component 3 = parity reference re-run (847–859); `rows_per_second` divides by `fast_compute_seconds` only (869); speedup = fast compute rows/sec ÷ same-process bounded reference rerun (compute vs compute). Parity time never enters throughput — exactly what the committed summary's methodology section says, and `test_benchmark_gate.py::test_worker_result_discloses_component_timings_separately` regression-pins it (the contaminated 1000/1.25 figure is asserted wrong).
- Reference is timed only on the bounded slice (`p01.run_benchmark` with the window's start/end); full-window numbers are extrapolations from `p01._full_window_basis`. The asymmetry disclosure (fast window includes load+write, reference is pure compute over pre-built views — biases AGAINST the fast path) is true in the code.
- No threshold was relaxed; `BLOCKED_SPEEDUP` in the committed summary is honestly derived from its own data under the gate's coded (old) criterion.
- **Required repair 1 (staleness, mtime-confirmed):** `src/alpha_system/labels/fast/materializer.py` was last modified 2026-06-10 17:28Z — ten minutes AFTER the summary was generated (17:18:35Z) — and no benchmark process is currently running. The committed `benchmark_summary.md` is therefore measurably the PRE-cache measurement — the WF1 spec itself cites it as the "before" evidence and mandates a full re-run + regeneration, which is still in flight. Merging this branch with the 17:18Z summary would ship speed claims that do not describe the shipped code (conservative direction for path, but stale either way) and a "Status: BLOCKED_SPEEDUP / policy not released" summary as the committed artifact of a branch whose contract amendment supersedes that status logic. Do not merge until the post-cache summary is regenerated and committed.
- Minor (info): in a blocked summary the "Production Worker Policy" section reads `Status: SELECTED` because `_select_worker_policy` receives `blocked=` from wiring blocks only (`benchmark_gate.py:674`) — the speedup block is appended afterwards. The rationale sentence ("not released for downstream reruns while status is blocked") mitigates, but the field is mildly inconsistent; fix alongside repair 2.

### 7. Five blocker fixes + regression tests — PASS

- (a) Grid coverage: `build_scaleout_units` now expands the orthogonal horizon grid (one unit per horizon carrying every governed name) for cost_adjusted/path while keeping name-grain units byte-identical (`driver.py` unit_axes + `_label_config_needs_horizon_grid`); `test_label_horizon_grid_coverage.py` pins 6/3/2/18/28 definitions, distinct horizons/unit ids, per-unit horizon-correct definitions, and the golden name-grain unit id.
- (b) BBO routing: `LabelPanelFrameRequest.bbo_dataset_version_id` + `resolved_bbo_dataset_version_id` (materializer) and `_label_bbo_input_dataset` (driver, fails closed when a BBO-requiring unit has no wired BBO DatasetVersion); regression tests `test_panel_frame_request_routes_bbo_to_the_bbo_dataset_version` and `test_scaleout_unit_bbo_input_dataset_selection`.
- (c) mfe parity (1628 missing records): positional trade-bar kernel rewrite in `labels/fast/path.py`; `test_mfe_record_set_matches_reference_across_gaps_and_roll_windows` first PROVES the fixture triggers the old guarded-drop mechanism (asserts a `TerminalGuardDisposition.DROP` exists), then asserts exact record-set equality with the reference across a maintenance break and a roll window — a genuine recurrence trap, not a proxy.
- (d) Timing contamination: three-component decomposition (see §6) + regression test.
- (e) cost_adjusted zero records: kernel now iterates the un-joined `SharedLabelPanel.bbo_rows` (`SharedBBOQuoteRow`, sub-minute timestamps preserved) exactly like the reference family instead of the OHLCV-anchored join; `test_cost_adjusted_matches_reference_on_misaligned_bbo_timestamps` shifts BBO timestamps by sub-minute jitter (the real failure mechanism) and asserts one record per quote row with reference parity.

### 8. Artifact policy — PASS

`git ls-files runs` empty; parquet/sqlite/arrow/feather/db globs empty; no `runs/**` path in the working-tree change set; the summary is value-free (dataset-version ids, counts, timings, statuses only — no prices, label values, or row payloads); scratch root name documents a local-only `$ALPHA_DATA_ROOT` location.

### 9. Scope / coupling / inheritability — PASS with notes

- FUTSUB resume safety: registry skip-checks are engine-aware via `producer_engine_id` (`_registry_record_matches_engine` / `_label_registry_record_matches_engine`); name-grain unit ids unchanged (golden test); horizon-grid units get new ids (their old 2/18 + 4/28 wirings were the bug); full `tests/unit/futures_substrate_scaleout/` suite green (83 passed). `ScaleoutConfig.horizons` is populated via `_optional_text_tuple` (missing key ⇒ `()` ⇒ old behavior); no other direct `ScaleoutConfig(` construction exists outside the driver.
- Scope note (warning): `src/alpha_system/features/scaleout/driver.py` and the new test under `tests/unit/futures_substrate_scaleout/labels/` are OUTSIDE the WF2 run-spec's Allowed Paths / Allowed Test Paths for LCFP-P08. They are authorized by the WF1 phase spec (driver explicitly in scope) and the coordinator-run repair branch, and are additive/regression-strengthening — but the P08 re-review must treat the WF1 spec, not the run spec, as the authorization for these surfaces.
- Maintainability note (info): `_LABEL_ACCEPTED_CONTEXT_CACHE`'s key omits `partition_id`/label-set/`repo_root` — verified safe today because the accepted `DatasetVersion` handle is built only from dataset_version_id/symbol/window (`cli/seed_pack.py:667`) and `partition_id` is passed per-unit at `materialize_pack(...)`; this becomes a staleness trap if `_build_accepted_context` ever starts embedding partition or label-set data. Add a guard comment or include partition-invariant assertions.

## Required repairs (before merge / P08 re-review)

1. Re-run the full benchmark gate on this code (workers 1/2/4/8, parity + resolver smoke per count) and commit the regenerated value-free summary; the 17:18Z summary is pre-cache evidence and must not be the merged artifact. (Already in flight as coordinator task; this review blocks on its completion.)
2. Align `benchmark_gate.py` with the amended done_criterion: per-family engine + worker policy emitted in the summary (fast where measured faster, reference where not), path-family ≤ 1.0 remains a hard block, cheap-family ≤ 1.0 becomes a per-family reference-engine selection rather than a global `BLOCKED_SPEEDUP`; fix the `SELECTED`-while-blocked policy-status inconsistency at the same time.

## Warnings (non-blocking)

- campaign.yaml amendment rationale cites uncommitted local profiling; ensure the regenerated summary's component timings independently support the "warm residual is kernel + value-store write" claim or soften the wording.
- WF2 run-spec scope formally exceeded (driver.py, futures_substrate_scaleout test); authorized by the WF1 spec/coordinator — re-reviewer should confirm.
- `_LABEL_ACCEPTED_CONTEXT_CACHE` key fragility (see §9).

## Bottom line

The five blocker fixes are real, oracle-verified, and each carries a regression test that would catch recurrence. The cache is bounded, keyed on full dataset-version + window identity, process-local, proven semantically invisible at the content-hash level, and inert for the reference engine. The contract amendment is dated, rationaled, mutually consistent, and preserves the path-family speed floor — honest re-scoping, not gate-gaming. What blocks a PASS today is purely the evidence chain: the committed summary predates the code, and the gate tool still implements the superseded criterion, so the amended contract is not yet satisfiable by the artifacts this branch would merge.

---

## Coordinator closure addendum (2026-06-10T18:10Z)

Both required repairs from the REWORK verdict are closed:

1. **Stale summary**: full benchmark gate re-run on the final working-tree code
   (generated 2026-06-10T18:06:17Z) and the committed summary regenerated from it.
2. **Gate/criterion alignment**: `benchmark_gate.py` now emits the per-family
   engine + worker policy table, blocks on speedup only when the path family is
   not materially faster, and marks the policy `NOT_RELEASED_WHILE_BLOCKED` in
   blocked summaries (11 new unit tests).

Final gate result: Status `COMPLETE`; path family fast at 10.20x (workers=8);
fixed_base/fixed_extended/close_out/cost_adjusted honestly selected `reference`
with component timings. The authoritative fresh review of the final state is
the Workflow 2 LCFP-P08 re-run review.
