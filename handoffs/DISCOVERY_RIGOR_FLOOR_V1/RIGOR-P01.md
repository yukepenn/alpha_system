# RIGOR-P01 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P01` - Verdict Reason-Code Taxonomy + Ledger-Presence Gates + Core Pilot Annotations  
Lane: YELLOW  
Executor: Codex

## Scope Completed

- Added `VerdictReasonCode` with exactly the eight campaign reason codes and
  fail-closed validation for exact enum/string values only.
- Added optional `reason_code` to `ReviewerVerdict`, `EvidenceBundle`, and
  `PromotionDecision`; present values are taxonomy-validated, and INCONCLUSIVE
  primary states require it.
- Added `ReviewerVerdictOutcome.INCONCLUSIVE`,
  `PromotionDecisionOutcome.INCONCLUSIVE`, and
  `PromotionLifecycleState.INCONCLUSIVE`. The lifecycle state is non-positive:
  it is not in `POSITIVE_PROMOTION_TARGET_STATES` and does not enter the
  candidate/validated evidence gate branch.
- Added `require_trial_ledger_present()` and invoked it on the
  `DIAGNOSTICS_RUN -> EVIDENCE_READY` promotion-gate path via
  `PromotionGateContext.trial_ledger_path`.
- Added six additive Core Pilot verdict annotations under
  `research/futures_core_alpha_pilot_v1/verdict_annotations/`; original
  verdict files were not edited.
- Added value-free evidence summary and README snapshot update.

## Curated File List For Ralph

- `README.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P01.md`
- `research/discovery_rigor_floor_v1/RIGOR_P01_REASON_CODE_AND_LEDGER_GATES.md`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/INDEX.md`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_9f6f741192a4b534f06e51c0.json`
- `research/futures_core_alpha_pilot_v1/verdict_annotations/annotation_sspec_aff70fcbc4b7ff226fcc8149.json`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/evidence_bundle.py`
- `src/alpha_system/governance/promotion.py`
- `src/alpha_system/governance/promotion_gate.py`
- `src/alpha_system/governance/registry.py`
- `src/alpha_system/governance/reviewer_verdict.py`
- `src/alpha_system/governance/verdict_reason_code.py`
- `tests/unit/discovery_rigor_floor/test_verdict_annotations.py`
- `tests/unit/governance/test_evidence_bundle.py`
- `tests/unit/governance/test_promotion.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`
- `tests/unit/governance/test_reviewer_verdict.py`
- `tests/unit/governance/test_verdict_reason_code.py`

No files were staged by the executor.

## Design Decisions

- Module name: `src/alpha_system/governance/verdict_reason_code.py`.
  Rationale: isolates the taxonomy and validator from verdict/promotion record
  modules while following existing governance module layout.
- EvidenceBundle coupling surface:
  `diagnostics_summary.diagnostics_status == "INCONCLUSIVE"`. Rationale:
  `EvidenceBundle` has no closed verdict/status enum today; this is the
  existing metadata surface that can express an inconclusive diagnostics state
  without inventing a new bundle status.
- ID derivation: `reason_code` is omitted from serialization and ID components
  when absent, preserving existing persisted-record IDs. When present, it is
  included in deterministic ID components for all three records.
- Promotion INCONCLUSIVE representation: added
  `PromotionLifecycleState.INCONCLUSIVE` so `PromotionDecision.decision` can
  remain matched to `next_state`. It is not a positive/advancing target.
- Ledger probe mechanism: `require_trial_ledger_present()` checks file
  existence, regular-file status, read/write permission bits, non-destructive
  `r+` open/read, and JSON parseability. It never writes to the ledger.
- CLI: no CLI changes were made; the gate-level API now requires callers that
  drive `DIAGNOSTICS_RUN -> EVIDENCE_READY` to provide
  `PromotionGateContext.trial_ledger_path`.

## Existing-Test Edits

- `tests/unit/governance/test_reviewer_verdict.py`: additive tests for
  INCONCLUSIVE reason-code requirement, free-text rejection, merge-ineligible
  inconclusive verdicts, and ID behavior when `reason_code` is present.
- `tests/unit/governance/test_promotion.py`: additive tests for
  `PromotionDecision` INCONCLUSIVE reason-code requirement, free-text
  rejection, non-advancing representation, and ID behavior.
- `tests/unit/governance/test_evidence_bundle.py`: additive tests for
  inconclusive diagnostics requiring `reason_code`, free-text rejection, and ID
  behavior.
- `tests/unit/governance/test_promotion_gate_state_machine.py`: one existing
  positive EVIDENCE_READY test was updated to pass a tmp ledger path because
  the ledger gate is now required; additive tests cover missing, unwritable,
  unparseable, and non-destructive probe behavior plus non-advancing
  `REVIEWED -> INCONCLUSIVE`.

No tests were deleted, skipped, xfailed, narrowed, or weakened.

## Annotation Table

| study_spec_id | reason_code | basis citation | original sha256 |
|---|---|---|---|
| `sspec_02c400a561891171a33c0c66` | `SUBSTRATE_GAP` | `judgement.basis`: objective trigger counts unresolved without locked structure FeaturePack; thin-session subsegments unresolved | `b5089ce28bdeb48e3fac9f034910abb620331cf5bea1f4835ef88b0b1cc334bf` |
| `sspec_267cc052e37668339c38d179` | `SUBSTRATE_GAP` | `judgement.basis`: locked trendiness and activation binding missing; source probe arms rejected | `a44718e28be05fedfddb5792a573580bf822b809e1b685412d72fa9cfa0ce25e` |
| `sspec_27bf1262b0bd23d27191cc86` | `SUBSTRATE_GAP` | `judgement.basis`: objective trigger counts unresolved without locked structure FeaturePack; thin-session subsegments unresolved | `9e35cfb38126d4f42ffb756ca02f313a1e254c4eeea59bf5f8eb11f1eb7ca590` |
| `sspec_69c22ec5847395ac8e81b5b6` | `SUBSTRATE_GAP` | `judgement.basis`: VWAP/session trigger FeaturePack not locked; 15m label pack unresolved | `1025459249320d297a850ff4b660b3e5912911de6ab35c31a9fb42c1ad374fda` |
| `sspec_9f6f741192a4b534f06e51c0` | `BBO_PROXY_LIMITATION` | `judgement.basis`: no locked BBO FeaturePack resolves; RTH session cost cells zero-fill or inconclusive | `011501dbfd9685bfd2c802026636aa5fad9882c68f2897ab6fb9a97c16ac9523` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `SUBSTRATE_GAP` | `judgement.basis`: VWAP FeaturePack binding not locked; active-session final aggregates unproven | `77537504219f3d07dfdcd50690e771db4d0b08dc6217c8d3c1a2b9e95e7b6eba` |

## Gate To Bypass-Test Map

- Exact taxonomy and free-text rejection:
  `tests/unit/governance/test_verdict_reason_code.py::test_verdict_reason_code_taxonomy_is_exactly_the_compass_set`,
  `test_verdict_reason_code_rejects_free_text_near_misses_and_placeholders`.
- `ReviewerVerdict` reason-code coupling:
  `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_requires_reason_code`,
  `test_reviewer_verdict_rejects_free_text_reason_code`,
  `test_reviewer_verdict_inconclusive_reason_code_is_not_merge_eligible`.
- `PromotionDecision` reason-code coupling:
  `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_requires_reason_code`,
  `test_promotion_decision_rejects_free_text_reason_code`,
  `test_promotion_decision_inconclusive_is_non_advancing_and_reason_coded`.
- `EvidenceBundle` diagnostics coupling:
  `tests/unit/governance/test_evidence_bundle.py::test_evidence_bundle_diagnostics_inconclusive_requires_reason_code`,
  `test_evidence_bundle_rejects_free_text_reason_code`.
- Ledger presence gate:
  `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_missing_trial_ledger`,
  `test_evidence_ready_transition_blocks_unwritable_trial_ledger`,
  `test_trial_ledger_presence_probe_blocks_unparseable_json`,
  `test_trial_ledger_presence_probe_is_non_destructive`.
- Annotation integrity:
  `tests/unit/discovery_rigor_floor/test_verdict_annotations.py::test_core_pilot_verdict_annotations_bind_to_original_inconclusive_verdicts`.

## Validation Results

| Command | Result | Notes |
|---|---:|---|
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `python -m pytest tests/unit/governance -q` | PASS | 556 passed in 3.06s. |
| `python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | 1 passed in 0.01s. |
| `python tools/verify.py --smoke` | PASS | Exit 0. |
| `python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git diff --stat main -- research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -- research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | PASS | Exit 0, no output; no tracked modifications in historical Core Pilot evidence dirs. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git ls-files -m -o --exclude-standard` | PASS | Output contained only the curated files listed above. |
| `sha256sum research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_*.json` | PASS | Hashes matched the annotation content references listed above. |

The prompt-provided run artifact directory
`runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P01` was absent
in this worktree, and there is no `runs/` directory here. No run-local handoff,
review, or verdict artifact was written.

## Confirmations

- Historical Core Pilot originals under `reviewer_verdicts/`, `study_specs/`,
  `evidence/`, and `ledgers/` were not edited by this executor.
- `git ls-files runs` is empty.
- Heavy tracked-artifact globs are empty.
- `reviews/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P01/` was not created by this
  executor; review is Ralph-owned.
- No `review.md` or `verdict.json` was created for this phase.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.
- No PR, merge, reviewer call, live trading, paper trading, broker operation,
  order routing, deployment, destructive cleanup, or FUTSUB run-state change
  was performed.

## Out-Of-Scope Findings

- The run artifact directory named in the executor prompt was not present in
  this worktree. This did not block the commit-eligible handoff because the
  prompt supplied the full phase spec and run-local artifacts are local-only.
