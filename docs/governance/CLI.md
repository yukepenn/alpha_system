# Governance CLI

The governance CLI is exposed under `alpha governance`. It is a thin local
orchestration layer over the existing governance validators, registry, and
promotion gate. It does not add lifecycle states, edit records in place, run
diagnostics, ingest data, call a broker, route orders, or grant any live,
capital, or production status.

All commands emit deterministic JSON. Success exits `0`. Fail-closed validation,
registry, or gate rejection exits `2` and writes a structured JSON error payload
to stderr with `issues`.

## Commands

### `validate-spec`

```bash
alpha governance validate-spec ALPHA_SPEC.json --hypothesis-card HYPOTHESIS_CARD.json
```

Validates the `AlphaSpec` and referenced `HypothesisCard`, then routes the pair
through the existing `DRAFT -> REGISTERED` pre-registration gate. A mismatched
`hypothesis_id`, malformed ID, missing required field, unknown field, or
non-canonical JSON fails closed.

### `register-trial`

```bash
alpha governance register-trial --registry-path /tmp/governance.sqlite3 TRIAL.json
```

Validates a `TrialLedgerRecord` and persists it under `DIAGNOSTICS_RUN` in the
local governance registry. Failed and abandoned trials are accepted only when
their required failure metadata is present. The registry is immutable: repeated
writes are idempotent only for identical content, and conflicting writes fail
closed.

### `build-evidence`

```bash
alpha governance build-evidence --registry-path /tmp/governance.sqlite3 EVIDENCE.json
```

Validates an `EvidenceBundle`, resolves its `StudySpec` and all referenced
`TrialLedgerRecord` IDs from the registry, routes the bundle through the existing
`DIAGNOSTICS_RUN -> EVIDENCE_READY` gate, and persists it under
`EVIDENCE_READY`. Missing manifests, hashes, data/factor/label versions,
negative-control results, study refs, or trial refs fail closed.

### `review`

```bash
alpha governance review \
  --registry-path /tmp/governance.sqlite3 \
  --implementer-id codex:argov-p16-executor \
  --implementer-role codex_executor \
  REVIEWER_VERDICT.json
```

Validates a `ReviewerVerdict` and persists it under `REVIEWED` only after the
existing `EVIDENCE_READY -> REVIEWED` gate accepts the reviewer context. The
verdict must include a non-empty independence statement. Reviewer identity and
role must differ from the implementer identity and role.

### `promote`

```bash
alpha governance promote \
  --registry-path /tmp/governance.sqlite3 \
  --implementer-id codex:argov-p16-executor \
  --implementer-role codex_executor \
  PROMOTION_DECISION.json
```

Validates a `PromotionDecision`, resolves the referenced reviewer verdict, and
persists the decision only through the existing `REVIEWED -> next_state`
promotion gate. For `CANDIDATE` and `VALIDATED`, the CLI resolves the referenced
evidence bundle and supplies all registry-visible `DIAGNOSTICS_RUN`
`TrialLedgerRecord` entries for the same alpha/study pair to the gate, so failed
or abandoned trial omission is blocked.

Optional gate context:

```bash
--locked-test-contamination-metadata CONTAMINATION.json
--rejected-idea-record REJECTED_IDEA.json
--rejection-reason "Explicit local rejection reason"
```

Prohibited MVP states (`LIVE_APPROVED`, `CAPITAL_ALLOCATED`,
`PRODUCTION_READY`) are not reachable through the command because the decision
validator and promotion gate reject them before persistence.

## Validation Helper

Batch validation helper:

```bash
python tools/governance/validate_objects.py \
  --object AlphaSpec:tests/fixtures/governance/alpha_spec_valid.json
```

Pre-registration pair validation:

```bash
python tools/governance/validate_objects.py \
  --alpha-spec ALPHA_SPEC.json \
  --hypothesis-card HYPOTHESIS_CARD.json
```

The helper imports the same validation functions used by `alpha governance`.

## Registry And Artifacts

Commands that persist data require `--registry-path`. Use a temp or other
local-only path for tests and operator exercises. Do not stage or commit SQLite
databases, journals, WAL files, raw data, generated outputs, cache files, or
`runs/**` runtime artifacts.

The CLI records governance metadata only. It makes no alpha, profitability,
tradability, or production-readiness claim.
