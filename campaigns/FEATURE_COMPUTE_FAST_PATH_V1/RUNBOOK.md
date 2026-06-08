# RUNBOOK — FEATURE_COMPUTE_FAST_PATH_V1

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
python -m pytest tests/unit/feature_compute_fast_path/ -q
python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q
```

## Launch the live Workflow 2 run

This campaign is driven by the Ralph strict Workflow 2 loop with the DAG-wave scheduler
(parallel build, serial merge), mirroring how `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
ran. After the contract bundle is merged and `ACTIVE_CAMPAIGN.md` points here:

```bash
just frontier-run-parallel FEATURE_COMPUTE_FAST_PATH_V1 3
# or the repo's documented frontier run entrypoint; max 3 parallel build waves, serial merge.
```

Family-pack phases (FCFP-P02..P10) build in parallel and merge one PR at a time. Phases sharing
`materialization_registry` (P12 reconciliation, P13 benchmark, P14 integration) are serialized.

## STOP / resume

- `runs/<run_id>/STOP` is an active stop request. Resume after the blocking condition clears via
  the repo's `frontier-resume` entrypoint; Ralph resumes from recorded state, never regenerating
  completed work.
- To re-run a merged/blocked phase, reset its phase dict in `runs/<run_id>/state.json` to the
  clean PENDING key-set, clear STOP, remove its worktree/branch and phase dir, then resume
  (same recipe as FUTSUB).

## Parity-first development discipline

- The reference engine is the oracle. Every pack ships a synthetic-fixture parity test before it
  is the production path for that family.
- Use `research/futures_substrate_scaleout_v1/producer_fast_path/v1_proof_base_ohlcv.py` as the
  base_ohlcv reference pattern (empirical parity against materialized reference values).
- Documented float tolerance is allowed where expected (rolling-std summation order); any
  unexplained difference is a blocker.

## Artifact discipline

- Explicit staging only; never `git add .`/`-A`; no force push.
- Never commit values/SQLite/raw/canonical/heavy artifacts; commit value-free summaries only.
- Before each merge: `git status --short`, `git ls-files runs` (empty), and the
  parquet/sqlite/arrow/feather/dbn/zst globs (empty).
- Registries and materialized values stay local-only under `$ALPHA_DATA_ROOT`. Back up local
  registries before any registry-touching phase (P12/P13/P14):

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
cp $ALPHA_DATA_ROOT/registry/features.sqlite $ALPHA_DATA_ROOT/registry/features.sqlite.bak_fcfp_$TS
```

## After campaign closes

FCFP-P15 writes `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FUTSUB_RESUME_ON_V1.md`. The coordinator
then: amends FUTSUB so P06–P13 (features) and P16–P20 (labels) materialize via V1 and P14/P22
validate V1 output; reconciles the already-materialized reference outputs per ADR-0007; resets
FUTSUB-P14 → PENDING, clears STOP, and resumes FUTSUB P14 → P33 on V1.

## Stop conditions (request human input)

External provider calls; broker/live/order scope; raw/canonical/value artifacts needing commit;
weakening a safety invariant (resolver semantics, serial registry, reference oracle);
scope expansion beyond V1 (Ray/GPU/cluster, feature-compiler, alpha mining); registry corruption
that backup/restore cannot safely recover.
