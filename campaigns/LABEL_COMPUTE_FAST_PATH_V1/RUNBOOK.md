# RUNBOOK — LABEL_COMPUTE_FAST_PATH_V1

## Environment

```bash
cd ~/projects/alpha_system
export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system
export PATH="$HOME/.venvs/alpha_system_research/bin:$PATH"
```

## Validation

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
python -m pytest tests/unit/label_compute_fast_path/ -q
# NOTE: the next test is currently RED with polars installed (stale FCFP-P10 pack
# vs the extended governed enum); LCFP-P03 repairs it — required green from P03 onward.
python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q
python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q
python -m pytest tests/unit/test_fast_path_artifact_policy.py -q
```

## Launch the live Workflow 2 run

This campaign is driven by the Ralph strict Workflow 2 loop with the DAG-wave scheduler
(parallel build, serial merge), mirroring `FEATURE_COMPUTE_FAST_PATH_V1`. After the contract
bundle is merged and `ACTIVE_CAMPAIGN.md` points here:

```bash
just frontier-plan LABEL_COMPUTE_FAST_PATH_V1          # read-only DAG sanity
just frontier-run-parallel LABEL_COMPUTE_FAST_PATH_V1 3
```

Label-pack phases (LCFP-P03/P04/P05) build in parallel after P02 and merge one PR at a time.
Phases sharing `materialization_registry` (P06 integration, P08 benchmark/readiness) are
serialized. Phase branches never write `ACTIVE_CAMPAIGN.md`.

## Predecessor state (do not disturb)

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` run
`2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is deliberately stopped at
FUTSUB-P19 (19/34; STOP present; state.json stale-RUNNING; P19 cost-adjusted labels ~60%
materialized, checkpointed/durable; two leftover worktrees). LCFP-P00 records this state in
`handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md`. **Nothing in LCFP deletes or
mutates FUTSUB run state, label values, or registry rows**; reintegration is a coordinator
action after LCFP-P09.

## STOP / resume

- `runs/<run_id>/STOP` is an active stop request. Resume after the blocking condition clears
  via the repo's `frontier-resume` entrypoint; Ralph resumes from recorded state, never
  regenerating completed work.
- To re-run a merged/blocked phase, reset its phase dict in `runs/<run_id>/state.json` to the
  clean PENDING key-set, clear STOP, remove its worktree/branch and phase dir, then resume
  (same recipe as FUTSUB/FCFP).

## Parity-first development discipline

- The per-row reference label engine is the oracle. Every fast family ships synthetic-fixture
  parity tests (value; label_available_ts EXACT; roll/maintenance guard EXACT; same-bar policy
  EXACT; gap/quality flags; overlap metadata; identity) before it is the production path.
- Extend the existing harness (`tests/unit/feature_compute_fast_path/parity_harness.py` —
  `LabelParityTolerance`, `assert_label_records_match`) rather than inventing a new one.
- Documented float tolerance is allowed where expected; any unexplained difference is a blocker.
- Benchmark rules are mandatory (FCFP-P13 required multiple attempts — initial execution plus
  bounded repairs/stops): bounded self-validating
  roll-containing slice; reference never timed on a full window; real runners wired, not stubbed.

## Artifact discipline

- Explicit staging only; never `git add .`/`-A`; no force push.
- Never commit values/SQLite/raw/canonical/heavy artifacts; commit value-free summaries only;
  Parquet-first, JSONL sample/manifest/audit tier only (no full-history JSONL payloads).
- Before each merge: `git status --short`, `git ls-files runs` (empty), and the
  parquet/sqlite/arrow/feather/dbn/zst globs (empty).
- Registries and materialized values stay local-only under `$ALPHA_DATA_ROOT`. Back up the
  local label registry before any registry-touching phase (P06/P08):

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp $ALPHA_DATA_ROOT/registry/labels.sqlite $ALPHA_DATA_ROOT/registry/labels.sqlite.bak_lcfp_$TS
```

## After campaign closes

LCFP-P09 writes `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`.
The coordinator then: amends the FUTSUB campaign/spec files per the handoff (P16–P20
materialize via the fast label path with the selected worker policy; the superseded
"reference-engine-only" non-goal in P18/P19 is retired); applies the preserve-don't-delete
cleanup rules for stale reference-label registry rows/values; resets FUTSUB P16–P20 phase
state as instructed, clears STOP, and resumes the FUTSUB run; repoints `ACTIVE_CAMPAIGN.md`
back to FUTSUB.

## Stop conditions (request human input)

External provider calls; broker/live/order scope; raw/canonical/value artifacts needing
commit; weakening a safety invariant (roll/maintenance guards, label_available_ts derivation,
resolver exact-id semantics, serial registry writes, the reference oracle); scope expansion
beyond the governed label families (alpha mining, new families, param search, Ray/GPU/cluster,
label-compiler); registry corruption that backup/restore cannot safely recover; any need to
delete FUTSUB run state or reference-label outputs.
