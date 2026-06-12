---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P050912_SURROGATE_BLOCK_NULLS
lane: yellow
status: in_progress
---

# P050912_SURROGATE_BLOCK_NULLS: dependence-preserving surrogate nulls + real-data calibration runner

## Purpose

KILL_SHOT_READINESS row 6 (PENDING-coordinator) requires compass v4.4 §7.2
real-data surrogate calibration: "session/trade-date-block shuffling minimum
plus at least one block-bootstrap configuration", per-family, declared K≥60,
zero passes, bound statement. The merged RIGOR-P05 machinery
(`src/alpha_system/governance/surrogate_run.py`) implements ONLY i.i.d.
per-row `label_shuffle` (`_label_groups` keys on (label_id, label_type,
data_version) — no time structure) — verified gap at
`surrogate_run.py:1014-1021`. i.i.d. shuffling destroys intraday dependence
and overstates the null's harshness/legality; the floor demands
dependence-preserving nulls. This phase builds them. The actual real-data
calibration RUN stays coordinator-owned (handoff step 5) and is NOT in scope.

## Scope (in-bounds)

1. **TRADE_DATE_BLOCK_SHUFFLE perturbation** (surrogate_run.py — COMPOSE with
   the existing pattern, study `write_label_shuffled_copy` first):
   `SurrogatePerturbationType.TRADE_DATE_BLOCK_SHUFFLE = "trade_date_block_shuffle"`
   and `write_trade_date_block_shuffled_copy(labels_path, output_path, *, seed)`:
   group label rows WITHIN each existing (label_id, label_type, data_version)
   group BY TRADING DATE (derive the date from the label row's canonical
   timestamp field — inspect real label JSONL rows produced by the value
   store to find the authoritative field, e.g. `ts`/`label_available_ts`;
   document the choice in a comment; fail closed with a ValidationIssue if
   the field is absent), then apply a seeded DERANGEMENT OF WHOLE DATE
   BLOCKS: label values move between dates as intact same-length day blocks
   (pair only equal-length date blocks; dates with unmatched block lengths
   stay in place and are counted+reported in the summary; if fewer than 2
   equal-length blocks exist anywhere, fail closed like the existing
   `insufficient_label_rows_for_shuffle`). Within-day temporal dependence is
   preserved by construction.
2. **TRADE_DATE_BLOCK_BOOTSTRAP perturbation**:
   `SurrogatePerturbationType.TRADE_DATE_BLOCK_BOOTSTRAP = "trade_date_block_bootstrap"`
   and `write_trade_date_block_bootstrap_copy(...)`: seeded resampling of
   whole date blocks WITH REPLACEMENT to the same number of date blocks,
   values reassigned onto the original rows' identity/timestamp skeleton in
   date order (the output file must keep the original row count, ids, and
   timestamps — only `value` fields move, mirroring the existing shuffle's
   in-place value semantics). At least one date block must differ from the
   identity arrangement or fail closed.
3. **Thread through the runner**: `run_surrogate_study` accepts the two new
   perturbation types (keep `random_target` rejected as today;
   `label_shuffle` unchanged); the perturbation writer is selected by type;
   `SurrogateStudyRun` records carry the correct `perturbation_type`;
   `calibrate_surrogate_fdr` + `render_value_free_calibration_report` gain
   per-perturbation-type counts (report stays value-free).
4. **CLI**: `alpha governance surrogate-calibrate` gains
   `--perturbation {label_shuffle,trade_date_block_shuffle,trade_date_block_bootstrap}`
   (default label_shuffle, backward compatible).
5. **Real-data calibration runner tool**
   `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
   (coordinator runbook tool, no WF2 coupling): given
   `--study-spec <path>` (a committed re-locked rerun sspec under
   `research/futures_substrate_scaleout_v1/rerun/study_specs/`),
   `--alpha-data-root`, `--runs-per-config`, `--base-seed`, `--namespace`,
   `--report-out`: resolve the sspec's locked LABEL pack for its declared
   primary horizon to the real local label values file via the EXISTING
   runtime resolver/registry code paths (no new resolution truth — reuse
   whatever the study runtime uses; the relock smoke test
   `tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py`
   shows the resolution idiom), then execute K seeded runs per perturbation
   config through `run_surrogate_study` and write ONE per-study value-free
   report (declared K, per-config counts, zero-pass verdict, the bound
   statement "zero passes in K bounds false-pass rate at about 3/K at 95%").
   The tool must refuse non-isolated namespaces (reuse
   `require_isolated_namespace`) and never write under production registry
   paths. If labels resolve to Parquet, read via the sanctioned loader and
   materialize a JSONL copy inside the isolated namespace for the shuffle
   writers (values stay local-only).
6. **Tests** (tests/unit/governance/ + tests/unit/discovery_rigor_floor/):
   synthetic multi-day fixtures prove (a) block shuffle moves values across
   dates while preserving within-date order and row skeleton; (b) bootstrap
   resamples with replacement, same skeleton, identity arrangement rejected;
   (c) determinism per seed; (d) unmatched-length accounting; (e) runner
   threads types end-to-end (PASSED/BLOCKED statuses recorded); (f) CLI flag
   accepted + default unchanged; (g) the calibration tool's resolution path
   on the committed sspec fixtures with a synthetic data root (loud
   condition-driven skip if real local data absent, per the sanctioned
   local_data helper idiom).

## Hard constraints

- COMPOSE with surrogate_run.py idioms (validation issues, seeded
  determinism, canonical serialization, isolated namespaces); no changes to
  existing label_shuffle behavior or any gate semantics; no edits under
  src/alpha_system/{features,labels,runtime}/**.
- Values never leave isolated namespaces; nothing under runs/ or registries
  committed; explicit staging; research-only language (calibration proves
  false-pass control, never alpha).
- Real network/data purchases out of scope.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

Both dependence-preserving perturbations implemented + threaded + tested;
calibration runner resolves committed sspecs to real label inputs via
existing resolver truth and emits the value-free per-study report; existing
label_shuffle and all gates unchanged; validation green incl. ci-parity;
truthful handoff under handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/; fresh
adversarial review PASS/PASS_WITH_WARNINGS under
reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
