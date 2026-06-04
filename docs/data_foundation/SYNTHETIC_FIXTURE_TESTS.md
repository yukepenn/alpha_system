# Synthetic IBKR Fixture Tests

DATA-P21 adds offline tests that compose the existing data-foundation records
against tiny synthetic IBKR-shaped fixtures. The tests are a precondition for
the later authorized smoke phases; they do not pull from IBKR and do not prove
provider availability.

## Fixtures

The primary fixture is
`tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json`. It is
hand-authored, deterministic, and labeled with:

- `synthetic: true`
- `real_provider_response: false`

It contains a fake read-only connection profile, fake contract-details fields,
one fake historical-bar CSV payload, manifest expectations, raw-object metadata,
and canonical timestamp expectations. The fixture is not derived from a real
IBKR response, is not raw market data, and is not canonical market data.

Existing tiny synthetic fixtures continue to support focused unit coverage:

- `synthetic_ibkr_raw_bars.csv` for parser behavior.
- `synthetic_contract_details_es_h5.json` for contract-details shape.
- `synthetic_pacing_resume_chunks.json` for resume-ledger behavior.
- `synthetic_quality_coverage_inputs.json` for aggregate quality and coverage.

## Pipeline Coverage

`tests/unit/data/test_synthetic_ibkr_fixture_composition.py` verifies the
composed connector/planner guard path:

- `DataAccessMode.synthetic()` is CI-allowed and has
  `allows_external_api = false`.
- `IBKRReadOnlyApiBoundary` refuses `reqHistoricalData` before a registered
  handler can run.
- `HistoricalRequestSpec` and `HistoricalRequestManifest` validate the
  manifest-driven request plan.
- `RequestPacingPolicy` accounts for `TRADES` and `BID_ASK` weights.
- `HistoricalChunkRecord` and `HistoricalPullLedger` reconcile completed and
  pending chunks, duplicate request keys, expected chunks, and resume tokens.

`tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py` drives the
end-to-end synthetic path:

```text
synthetic fixture
-> contract details / request manifest / pacing guard
-> raw object metadata + fake payload loader
-> ParsedBarRecord
-> CanonicalBarRecord
-> DataQualityReport + CoverageReport
-> DatasetVersion
-> temp local registry round-trip
```

The registry path is a pytest `tmp_path` local DB and is not committed.

## No External Call Guarantee

The DATA-P21 tests do not import an IBKR client library, open a socket, or call
a provider. The connector-facing proof uses `IBKRReadOnlyApiBoundary` in
synthetic mode with a test-local handler that raises if reached. The expected
behavior is stricter: the boundary rejects the external API call before the
handler is invoked, so the handler call counter remains zero.

The integration test uses a test-local synthetic transport that returns the
fixture payload from memory after manifest and pacing validation. It records
synthetic fixture usage separately from external attempts and asserts that the
external-attempt counter remains zero.

## Fail-Closed Assertions

DATA-P21 re-checks upstream guards when the records are composed:

- clientId `101` and `102` remain hard-blocked.
- Missing `HistoricalRequestManifest` blocks the simulated pull before fixture
  payload access.
- Missing `RequestPacingPolicy` blocks the simulated pull before fixture payload
  access.
- Missing `available_ts` blocks `CanonicalBarRecord` construction.
- Provider-continuous futures records cannot be used as dated-contract truth.
- Silent gaps, duplicate timestamps, non-monotonic timestamps, OHLC defects,
  and missing coverage are surfaced as blocking quality/coverage findings.
- Zero-volume bars are not silent; they are recorded as explicit warning
  anomalies under the DATA-P16 quality semantics.
- Blocking quality or coverage prevents `DatasetVersion` prerequisites from
  passing.

## Artifact Posture

DATA-P21 commits only tiny synthetic fixtures, tests, docs, README snapshot, and
handoff text. It does not commit raw data, canonical data, real provider
responses, Parquet/Arrow/Feather/Pickle/NumPy artifacts, local DB files, logs,
cache files, account material, credentials, or `runs/**` artifacts.

Quality and coverage outputs remain aggregate in tests. No report body embeds a
raw bar dump or a canonical data artifact.

No broker, order, account, position, paper, live, real-time feed, production
deployment, alpha-search, profitability, tradability, or production-readiness
scope is introduced.
