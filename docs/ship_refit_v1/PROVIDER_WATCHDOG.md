# Provider Watchdog

`SHIP_REFIT-P01` adds an opt-in liveness watchdog around provider subprocesses
started by the Workflow 2 driver. It is local-only harness resilience: it does
not call providers by itself, change diagnostics, write data, or introduce a new
recovery state machine.

## Detection

Provider commands run through `tools/frontier/command_runner.py` with
`start_new_session=True`, creating a process group for the provider and any
children it spawns. A sampler checks the process group and the run event ledger:

- CPU progress: summed `/proc/<pid>/stat` user+system ticks for all visible
  processes in the provider process group.
- Event progress: `events.jsonl` size or mtime growth.
- Default cadence: `30s`.
- Default hang threshold: wall-clock `> 60s`.
- Frozen CPU threshold: `cpu_delta <= 0` ticks over the sample window.

The kill predicate is deliberately conjunctive:

```text
wall > 60s AND cpu_delta <= 0 AND no events.jsonl growth
```

A provider with advancing CPU ticks or a growing events ledger is not killed,
even after the wall-clock threshold.

## Recovery

When the predicate fires, the runner emits `PROVIDER_HANG_DETECTED` into the
run's `events.jsonl` with `pid`, `pgid`, `wall_seconds`, `cpu_delta`,
`last_event_age_seconds`, `events_path`, and `wchan` where available. The runner
then kills the provider process group with `os.killpg`, returns code `124`, and
marks the result as timeout-class.

`tools/frontier/provider_adapters.py` classifies return code `124` as a provider
waiting status, so `tools/frontier/ralph_driver.py` continues through the
existing `handle_provider_nonzero` / provider-limit resume path. No parallel
recovery state is added.

## First-Light Check

Before a real provider run, the callable first-light check is:

```bash
python tools/frontier/ralph_driver.py first-light
```

It runs the feature and label resolver-smoke tests, then
`tools/hooks/canary_runner.py`. It performs no provider, network, broker, PR,
merge, deployment, paper-trading, or live-trading operation.
