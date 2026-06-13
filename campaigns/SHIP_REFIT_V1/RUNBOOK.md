# Runbook — SHIP_REFIT_V1

## Preconditions (state-aware; verify before launch)

- `python tools/frontier/status_doctor.py` → no other campaign RUNNING; FUTSUB
  COMPLETED. Live run-state is the source of truth, not committed pointers.
- Git is **main-only** and clean; `git ls-files runs` empty.
- The **A-vs-B conditional re-score settler** has been run by the coordinator and its
  result recorded — P03 scope is amended (bounded if NULL, +interaction detector if
  NONZERO) **before** P03 runs.
- `ACTIVE_CAMPAIGN.md` repointed to SHIP_REFIT_V1 (coordinator-only; serial — do this at
  launch, not during authoring).

## Validation (no providers / no network / no merge)

```bash
python -c "import yaml; yaml.safe_load(open('campaigns/SHIP_REFIT_V1/campaign.yaml'))"
just frontier-plan SHIP_REFIT_V1            # plan-dag: parse phases + DAG + scheduler
just frontier-run-parallel-mock SHIP_REFIT_V1 2   # dry mock run (mock providers)
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

## Launch (Workflow 2, provider-wired, DAG-wave, max-parallel 2)

```bash
# coordinator repoints ACTIVE_CAMPAIGN first (serial), then:
just frontier-run-parallel SHIP_REFIT_V1 2
# P00 -> (P01 || P02) -> P03 -> P04 ; serial merge queue
```

## Standard checks per phase

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

## Phase-specific verification

- **P01** synthetic futex-hang fixture recovers <2 min; benign-slow not killed;
  `grep -q 3600 frontier.yaml`; watchdog regression tests pass.
- **P02** parity harness: byte-identical `diagnostic_summary` hashes fast vs reference,
  ≥10 seeds; assert numpy/pandas/polars unimportable; measure wall-clock + disk
  write-count ↓≥10×.
- **P03** every verdict carries a power statement; `n_eff.py` folds purge/embargo;
  settler result recorded.
- **P04** post-merge worktree prune works; runs/ rotation bounds growth; done-check no
  longer writes reviewer-owned paths.

## Watchdog / resilience (during the run)

- Driver heartbeat: `runs/<RID>/heartbeat.json`; events: `runs/<RID>/events.jsonl`.
- With P01 merged, the driver self-recovers the provider-hang class; before P01 merges,
  the coordinator keeps an external progress-watchdog armed (CPU-tick + event-freeze +
  futex detection) as the fallback.
- Hang signature: `wchan=futex_*`, frozen `/proc/<pid>/stat` ticks, no events growth.
  Benign: `hrtimer_nanosleep`/`poll_schedule_timeout` with advancing ticks or events.

## STOP / resume

- `runs/<RID>/STOP` is an active stop request; resume re-enters from recorded state.
- A terminal STOP ("stopped safely. Reason: All parsed phases completed.") is a
  completion marker, not a block.

## Hard stops

No paid data; no broker/live/order/capital; no non-regenerable data deletion; no
committing data/DB/Parquet/secrets; no truth-chain weakening; no major compass change
without user approval.
