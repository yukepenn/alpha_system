I have enough to complete the review. All key claims are verified: the doc's scheduler block matches `campaign.yaml` byte-for-byte, the wave plan matches the actual DAG metadata (P07–P15 and P19–P21 are the only `parallel_safe: true` phases), the change is docs-only, no `runs/` is tracked, and all canaries + frontier-doctor pass.

---

# Claude Review — AGENT-P24: Workflow 2 DAG Integration and Parallel Plan

## Scope and Lane
YELLOW, documentation-only. The phase authors one durable doc (`docs/agent_factory/WORKFLOW2_DAG.md`), updates `README.md`, and writes the commit-eligible handoff. No code, no scheduler/tooling/campaign edits, no consumed-primitive edits. Confirmed against the working tree: only `README.md` (modified) plus two new untracked files; `git diff --stat` shows a 22-line README change and nothing else.

## Verification Performed

**Factual accuracy of the doc (the core risk for a "records the config" phase):**
- Scheduler block in the doc (`mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`, `merge_queue: serial`, `update_active_campaign: coordinator_only`) matches `campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml:60-66` exactly. ✓
- Parallel-safety claim verified against phase metadata: the only `parallel_safe: true` / `must_run_alone: false` phases are the 9 `agent_roles` phases (P07–P15) and the 3 `assets` phases (P19–P21). All other 14 phases are `parallel_safe: false` / `must_run_alone: true`. The doc states this exactly. ✓
- Wave shape (W0 P00–P06 alone, W1 P07–P15 parallel, W2 P16–P18 alone, W3 P19–P21 parallel, W4 P22–P25 alone) and the 18-wave / max-width-3 planner expansion are internally consistent with the metadata and merge groups. ✓
- P24 itself is correctly described as run-alone (`closeout`, `parallel_safe: false`). ✓

**Safety / artifact policy:**
- `git ls-files runs` empty; `frontier-doctor` PASS; all 16 canaries PASS (including `forbidden_scope_drift`, `forbidden_raw_data_commit`, `forbidden_boundary_import`, `forbidden_local_artifacts`, `forbidden_secret`). ✓
- No-claims language honored: the doc's Boundary section and the README snapshot explicitly disclaim agent instantiation, continuous runner, provider calls, order routing, broker/live/paper/account scope, factor promotion, and research efficacy. ✓
- Executor left everything unstaged; handoff is truthful and discloses its skips (`git status` forbidden by executor prompt; `frontier-run-parallel-mock` documented rather than run — correct for a docs-only phase).

## Warnings

1. **README authorized by spec policy, not by `campaign.yaml` allowed_paths.** P24's `allowed_paths` in `campaign.yaml` lists only the doc, handoff, reviews, and `runs/**` — it does **not** include `README.md`. The README edit is authorized solely by the generated spec's "README Snapshot Policy." This is not scope drift in practice: README snapshots are an established, reviewed campaign convention (P19–P23 each merged a README update via PRs #201–#206). The edit is concise, factual, additive, and free of forbidden content. Ralph/the coordinator should stage `README.md` explicitly. Flagging the spec-vs-campaign.yaml allowed_paths divergence for awareness.

2. **`runs/**` appears in P24's `campaign.yaml` allowed_paths** but must never be committed per AGENTS.md and the spec's artifact policy. The spec and executor correctly resolved this as local-only and staged nothing. Ralph must stage by explicit path and confirm the staged set contains no `runs/` path before commit. (Known campaign-wide generation artifact, not introduced by this phase.)

3. **Smoke not independently re-run here** (`tools/verify.py --smoke` and `just frontier-plan` required approval in this review environment). Corroborated by the executor's reported PASS, plus passing `frontier-doctor` and all canaries on a docs-only change that touches no Python. Low risk.

## Conclusion
The document is an accurate, faithful, additive record of the already-configured DAG scheduler — every quantitative claim I could check against `campaign.yaml` and the phase metadata holds. Docs-only scope respected; no broker/live/paper/strategy scope, no destructive ops, no hidden failed runs, no test weakening, no `runs/` or forbidden path staged, no unsupported alpha/tradability claims. The only items are minor policy-hygiene warnings (README authorization path; `runs/**` staging discipline for the driver).

VERDICT: PASS_WITH_WARNINGS
