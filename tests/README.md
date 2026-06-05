# Tests

`tests/` holds ~420 `test_*.py` modules (the larger raw file count includes
fixtures and `__pycache__`). External providers (IBKR, Databento) are **never**
called in tests — they are mocked, fixture-driven, or dependency-injected, and the
live data flows refuse to run in CI.

## How to run

```bash
python -m pytest                      # full suite
CI=true python -m pytest -q           # reproduce CI gating locally
python tools/verify.py --all          # lint + typecheck + tests + boundaries + artifacts
python tools/hooks/canary_runner.py   # safety canaries (must all pass)
```

## Layout

- `tests/unit/` — contract, provider-adapter (databento / ibkr), governance,
  data-foundation, and artifact-policy unit tests.
- `tests/no_lookahead/` — `available_ts` / leakage / no-lookahead invariants.
- `tests/integration/` — synthetic end-to-end and fixture-pipeline tests.
- `tests/parity/` — reference-vs-fast-path parity.
- `tests/performance/` — local latency / throughput baselines.
- `tests/tools/` — harness-tool tests.
- `tests/fixtures/` — shared synthetic fixtures (no real market data).

## Fail-closed safety tests (do not weaken)

Guard tests that must stay fail-closed include: IBKR clientId `101`/`102`
hard-block; missing-manifest reject; missing `available_ts` reject; artifact /
data-commit blocked; `.dbn` / `.zst` guard; Databento key absent reject; and
governance negative controls. See also `tools/hooks/canary_runner.py` and
`evals/canaries/`.

## Adding Feature/Label tests

Mirror the module under test in `tests/unit/`; add `tests/no_lookahead/` coverage
when availability semantics are involved; keep external providers mocked. Do not
add tests that depend on real Databento/IBKR data or that hit paid APIs.
