# Synthetic End-to-End Governance Dry Run

ARGOV-P18 adds a synthetic integration dry run for the governance lifecycle. The
dry run uses tiny deterministic fixtures under
`tests/fixtures/governance/end_to_end/` and persists objects only to a temporary
test registry.

This artifact is governance machinery only. It is not evidence of alpha
validity, profitability, tradability, robustness, production readiness, paper
readiness, live readiness, broker readiness, or readiness for real data.

## Exercised Path

`tests/integration/governance/test_end_to_end_dry_run.py` composes the existing
governance objects, gates, registry, CLI, canary harness, and unsupported-claim
guard. It does not add a new governance object type or copy gate logic.

The happy path walks one synthetic idea through these states:

| State | Existing surface exercised |
| --- | --- |
| `DRAFT` | `HypothesisCard` validation and temporary registry persistence |
| `REGISTERED` | `alpha governance validate-spec` and pre-registration gate |
| `IMPLEMENTATION_ALLOWED` | no-code gate, duplicate-exposure guard, label-leakage guard |
| `IMPLEMENTED` | implementation handoff reference gate |
| `DIAGNOSTICS_ALLOWED` | `StudySpec` diagnostics gate |
| `DIAGNOSTICS_RUN` | `TrialLedgerRecord` gate and CLI `register-trial` |
| `EVIDENCE_READY` | `EvidenceBundle` gate and CLI `build-evidence` |
| `REVIEWED` | independent `ReviewerVerdict` gate and CLI `review` |
| `CANDIDATE` | promotion gate and CLI `promote` |
| `VALIDATED` | promotion gate and CLI `promote` |

`CANDIDATE` and `VALIDATED` are governance states only. They do not authorize
capital allocation, live activity, order routing, or deployment.

## Gate Blocks Asserted

The integration test asserts the required fail-closed paths:

- missing `AlphaSpec` blocks `IMPLEMENTATION_ALLOWED`;
- missing `StudySpec` blocks diagnostics;
- missing `TrialLedgerRecord` blocks diagnostics and promotion;
- missing `EvidenceBundle` blocks `CANDIDATE`;
- missing independent `ReviewerVerdict` blocks `VALIDATED`;
- reviewer self-approval is rejected;
- unrecorded locked-test contamination blocks promotion;
- failed-run omission blocks promotion;
- unsupported claim text is rejected by the claim guard;
- `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` are absent from
  reachable states and rejected by the transition parser.

## Negative Controls

The dry run asserts all required negative controls in guard-behavior terms:

- `random_target` is checked through the catalogued `NegativeControlResult`
  contract.
- `future_shift`, `permuted_labels`, and `optimistic_fill` run through the
  executable governance canary harness.
- `python tools/hooks/canary_runner.py` is invoked by the integration test and
  expected to report the governance canaries as caught.

A canary `PASS` result means the guard caught the injected known-bad fixture. It
does not describe research quality or market behavior.

## Artifact Boundaries

The dry run writes temporary JSON command inputs and a temporary SQLite registry
only under pytest's temporary directory. No registry file, local DB, generated
bundle, heavy artifact, raw data, factor data, label data, cache, or `runs/**`
path is commit-eligible for this phase.
