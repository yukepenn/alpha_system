I have enough to render a verdict. Let me record my findings.

## Claude Review — ALPHA_RESEARCH_RUNTIME_MVP / RT-P16 — EvidenceBundle Draft Builder

### Scope & lane
YELLOW, integration merge group, `must_run_alone`. The change is confined to the new additive subpackage and required artifacts. `git status` shows exactly six touched paths, all within the spec's Allowed Paths (§5):

- `src/alpha_system/runtime/evidence/{__init__.py,draft.py}`
- `tests/unit/runtime/evidence/test_evidence_draft.py`
- `docs/research_runtime/EVIDENCE_DRAFT.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md`

No forbidden path touched: nothing under `governance/**`, `research/**`, `experiments/**`, `backtest/**`, `features/**`, `labels/**`, `data/**`, broker/live/paper/order trees, sibling runtime subpackages, or coordinator files. ✔

### Governance boundary — consumed, not duplicated
`draft.py` imports `EvidenceBundle`, `create_evidence_bundle`, `EvidenceArtifactManifestEntry` from `alpha_system.governance.evidence_bundle`, the governance serialization helpers, and `TrialLedgerRecord` from `governance.trial_ledger`. The builder calls the real `create_evidence_bundle(...)` and re-validates via `EvidenceBundle.from_mapping`. No governance logic is re-implemented or edited. ✔

### Safety properties (verified by reading the contract code)
- **Not a candidate / not promotion**: hard-coded flags `not_a_candidate`, `not_reference_truth`, `not_finalized_evidence_bundle`, `promotion_basis_allowed=False` on the object, the diagnostics summary, and every section. ✔
- **Terminal-state visibility**: `_coerce_decision` carries `REJECTED/INCONCLUSIVE/BLOCKED` with their `RejectionReasonRecord`s; a forward state never overwrites a terminal one; `_decision_only_section` guarantees a visibility section. ✔
- **No raw/heavy data**: `_checked_key` rejects value-bearing key tokens (`values`, `rows`, `series`, `array`, `dataframe`, …) and `_pruned_json_value` permits only JSON scalar/summary metadata, raising on arbitrary objects. ✔
- **Cost discipline**: forward `EVIDENCE_DRAFT_READY` requires a cost report, a no-lookahead result, and a diagnostics report; `_cost_section` enforces `base`+`double_cost` profiles, `slippage_labeled_proxy is True`, and rejects any `promotion_basis_allowed` profile. A referenced `SignalProbeReport` must match the supplied cost report. ✔
- **No-claims guard**: `_required_text` fails closed on promotional phrases (`profitable`, `tradable`, `alpha validated`, `production-ready`, …) and on vague placeholders, applied to all text fields. ✔
- No prohibited MVP state token appears (handoff `rg` returned no match; confirmed in source). No external provider/file readers in the subpackage. ✔

### Artifact policy
`git ls-files runs` empty; no `runs/` path staged or created; no heavy/data/DB artifacts; explicit-staging discipline preserved (Codex staged nothing, left work unstaged as required). `just verify-canaries` → all 17 canaries PASS; `just frontier-doctor` PASS. README update is factual, compact, and within the snapshot policy. ✔

### Docs & README
`EVIDENCE_DRAFT.md` accurately describes the object, governance-feeds relationship, decision coupling, cost discipline, and data policy with correct non-promotional boundaries. README advances 16/27→17/27, sets active/next RT-P16/RT-P17, lists the new module/doc, restates safety boundaries. ✔

### Warnings
1. **`python tools/verify.py --all` is not green: 13 failures** (`tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` + 12 `tests/test_ralph_driver.py` Workflow 2 / Ralph state-machine tests). These are structurally unrelated to an isolated new `runtime/evidence/` subpackage, none of those files were touched, and the failure set matches the project's known inherited harness/env flakiness (cf. prior FLF closeout). The handoff discloses them truthfully rather than hiding them. RT-P16's own gates are green: `tests/unit/runtime/evidence` 5 passed, `tests/unit/runtime` 165 passed, smoke + canaries pass. I could not independently re-run pytest here (sandbox approval gate), so I relied on the executor's reported results plus the independently-supplied canary/doctor PASS and a full read of the source — the full-suite red is a pre-existing-condition warning, not a regression introduced by this phase.
2. The promotional-phrase substring filter is aggressively conservative (e.g. a limitation containing "not tradable" would raise). This fails closed (safe) and the default limitations avoid it; noting as a latent usability edge, not a defect.
3. Yellow-lane independent review/verdict artifacts remain to be written by the reviewer; correctly out of Codex's scope.

### Conclusion
Scope-compliant, boundary-correct, non-promotional, artifact-clean, and faithful in disclosure. The only reservation is the unrelated, truthfully-reported full-suite failures, which keep this short of an unqualified PASS.

VERDICT: PASS_WITH_WARNINGS
