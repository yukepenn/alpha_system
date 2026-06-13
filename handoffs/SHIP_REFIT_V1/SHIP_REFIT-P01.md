# SHIP_REFIT-P01 Handoff

## Scope Completed

- Added an opt-in provider watchdog in `tools/frontier/command_runner.py`.
  Provider calls can now run in a new process group (`start_new_session=True`),
  sample process-group CPU ticks from `/proc`, watch `events.jsonl` growth, emit
  `PROVIDER_HANG_DETECTED`, and kill the provider process group on the conjunctive
  hang predicate.
- Wired Workflow 2 provider calls in `tools/frontier/ralph_driver.py` to pass the
  run event ledger and event callback into the watchdog. Timeout-class return
  code `124` is routed through the existing `handle_provider_nonzero` /
  provider-limit resume path; no new recovery state machine was added.
- Added the callable first-light preflight:
  `python tools/frontier/ralph_driver.py first-light`.
- Lowered `frontier.yaml` `providers.timeout_seconds` from `21600` to `3600`.
- Added watchdog regression tests under `tests/frontier/`.
- Added the watchdog design/operation note at
  `docs/ship_refit_v1/PROVIDER_WATCHDOG.md` and updated the README snapshots.

## Files Changed

- `tools/frontier/command_runner.py`
- `tools/frontier/ralph_driver.py`
- `frontier.yaml`
- `tests/frontier/test_provider_watchdog.py`
- `docs/ship_refit_v1/README.md`
- `docs/ship_refit_v1/PROVIDER_WATCHDOG.md`
- `README.md`
- `handoffs/SHIP_REFIT_V1/SHIP_REFIT-P01.md`

## Watchdog Behavior

- Production defaults: sample every `30s`; hang threshold `wall > 60s`;
  frozen-CPU threshold `cpu_delta <= 0` ticks; event progress is any
  `events.jsonl` size or mtime increase.
- Kill predicate:

```text
wall > 60s AND cpu_delta <= 0 AND no events.jsonl growth
```

- A provider with advancing CPU ticks or growing events is not killed.
- A detected hang emits `PROVIDER_HANG_DETECTED` with `pid`, `pgid`,
  `wall_seconds`, `cpu_delta`, `last_event_age_seconds`, `events_path`, and
  `wchan` when available.
- The process group is terminated with `os.killpg`; the runner returns `124`.
- Ralph maps `124` to the provider waiting status for the provider and reuses
  the existing provider-limit resume artifacts and `WAITING_*` path.

The synthetic timing probe used accelerated test thresholds for a hermetic local
test and recovered in `62 ms` (`wall_seconds=0.061`, `cpu_delta=0`,
`return_code=124`, event `PROVIDER_HANG_DETECTED`). With production defaults,
the 30s sampler plus `wall > 60s` predicate detects on the next sample, about
90s after start, below the `< 2 min` criterion.

## Validation

- `python -m py_compile tools/frontier/command_runner.py tools/frontier/ralph_driver.py tests/frontier/test_provider_watchdog.py` — PASS.
- `PYTHONPATH=src python -m pytest tests/frontier -k "watchdog or command_runner or hang" -q` — PASS; `5 passed in 0.69s`.
- `PYTHONPATH=src python -m pytest tests/test_command_runner.py tests/test_provider_adapters.py -q` — PASS; `16 passed in 0.16s`.
- `python tools/verify.py --smoke` — PASS.
- `python tools/hooks/canary_runner.py` — PASS; all Frontier canaries passed, including `planted_fake_alpha`.
- `grep -q "3600" frontier.yaml` — PASS.
- `git ls-files runs` — PASS; printed no tracked `runs/` paths.
- `python tools/frontier/ralph_driver.py first-light` — PASS; resolver-smoke tests reported `7 passed, 2 skipped`, then canaries passed.
- Synthetic timing probe:
  `PYTHONPATH=src python - <<'PY' ... CommandRunner(... ProviderWatchdogConfig(sample_interval_seconds=0.02, hang_after_seconds=0.06) ...) ... PY`
  — PASS; `return_code=124`, `duration_ms=62`,
  `event=PROVIDER_HANG_DETECTED`, `wall_seconds=0.061`, `cpu_delta=0`.

## Repair Attempt 1

Finding repaired:

- CI parity failed before review in
  `tests/test_ralph_driver.py::test_fresh_provider_run_prepares_phase_branch_before_executor_and_preserves_main`
  because the new driver watchdog plumbing passed `watchdog=` into a local
  monkeypatched `codex_noninteractive` test double that only accepted
  `prompt` and `root`.

Repair:

- Added `_codex_noninteractive_for_driver` in `tools/frontier/ralph_driver.py`.
  Production Codex calls still receive the watchdog when the callable supports
  `watchdog`; narrower in-process substitutes are called with the legacy
  keyword set they declare. The existing provider watchdog path, return-code
  routing, and hang discriminator were not changed.

Repair validation:

- `PYTHONPATH=src python -m pytest tests/test_ralph_driver.py::test_fresh_provider_run_prepares_phase_branch_before_executor_and_preserves_main -q`
  — PASS; `1 passed in 0.29s`.
- `PYTHONPATH=src python -m pytest tests/frontier -k "watchdog or command_runner or hang" -q`
  — PASS; `5 passed in 0.68s`.
- `PYTHONPATH=src python -m pytest tests/test_ralph_driver.py tests/unit/frontier/test_ralph_driver_ci_repair.py -q`
  — PASS; `73 passed in 3.27s`.
- `python -m py_compile tools/frontier/ralph_driver.py` — PASS.
- `python tools/verify.py --smoke` — PASS.
- `python tools/hooks/canary_runner.py` — PASS; all Frontier canaries passed,
  including `planted_fake_alpha`.
- `grep -q "3600" frontier.yaml` — PASS.
- `git ls-files runs` — PASS; printed no tracked `runs/` paths.
- `git diff --cached --name-only` — PASS; printed no staged paths.
- `just ci-parity` — FAIL in the current shell only because
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` makes
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  select `RuntimeCacheStorageKind.ALPHA_DATA_ROOT` instead of `RUN_ARTIFACTS`.
  The repaired `tests/test_ralph_driver.py` failure did not recur.
- `PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only -q`
  — FAIL with `ALPHA_DATA_ROOT` exported; same local environment failure as
  above.
- `env -u ALPHA_DATA_ROOT PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only -q`
  — PASS; `1 passed in 0.02s`.
- `env -u ALPHA_DATA_ROOT just ci-parity` — PASS;
  `3330 passed, 80 skipped in 76.76s`.

## Artifact And Staging Discipline

- No staging, commit, push, PR, merge, reviewer call, or reviewer artifact was
  performed by the executor.
- No `runs/` artifact was created for commit; `git ls-files runs` printed
  nothing.
- No diagnostics, power, data, registry, broker/live/execution, or forbidden
  path was touched.
- No dependency was added.

## Review Status

YELLOW-lane review remains Ralph/reviewer-owned. Per executor safety
instructions, no `review.md`, `verdict.json`, PR, merge, or PASS marking was
created here.
