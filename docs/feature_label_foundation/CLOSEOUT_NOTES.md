# Feature/Label Foundation Closeout Notes

## Status

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is closed out by `FLF-P31` with a campaign
verdict of `COMPLETE_WITH_WARNINGS`. The full verdict, gate audit, semantic
done-check, and residual warnings live in
`campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`.

This closeout records **research-substrate acceptance only**. It is not an alpha
result, a tradability or profitability finding, a strategy/backtest/portfolio
result, or broker/live/paper readiness.

## Durable Audit Notes

- **Phase coverage is complete.** `FLF-P00` … `FLF-P31` are covered exactly once
  by the nine acceptance gates; there are no RED phases. `FLF-P00`…`FLF-P30` are
  merged to `main` (PRs #112–#144; HEAD `9b2a0b3`) as a linear serial squash
  chain; `FLF-P31` is this closeout.
- **Verdicts are merge-eligible.** 5 `PASS` and 26 `PASS_WITH_WARNINGS` for
  `FLF-P00`…`FLF-P30`; no prior `BLOCKED`, `REWORK`, or `FAIL`.
- **Substrate boundary holds.** Feature/label code consumes accepted
  DatasetVersions only, through `features.consumption` over
  `resolve_accepted_dataset_version`, reconstructing canonical records via the
  `from_mapping` loaders; no raw provider file is read and no provider is called.
  Databento and IBKR DatasetVersions are never merged.
- **No-lookahead and leakage hold.** `available_ts` is required/validated on every
  feature value; `label_available_ts` on every label value; future/centered
  windows are contract-forbidden for live features; the label-leakage guard is
  consumed and fail-closed; the `tests/no_lookahead/feature_label` suite and the
  `governance_future_shift` / `governance_permuted_labels` /
  `governance_optimistic_fill` canaries pass.
- **BBO / no-trade semantics.** Missing/abnormal BBO is flagged
  (`missing_bbo` / `bbo_quarantined`) with no silent forward-fill; synthetic
  dense-grid no-trade rows stay distinct from real trade bars.
- **Governance consumed, not duplicated.** FeatureRequest, duplicate-exposure,
  LabelSpec, label-leakage, and the StudySpec Input Pack integrate with the
  existing governance modules without editing them; the StudySpec Input Pack is
  additive and leaves the StudySpec schema unchanged.
- **Stores are local-only.** Feature/label values, registries, raw/canonical
  data, and heavy artifacts remain uncommitted; the registries record
  metadata/lineage and duplicate-exposure/deprecation, not a dumping ground.
- **DAG metadata is sound.** `dag_wave`, `max_parallel_phases: 3`,
  `merge_queue: serial`, `update_active_campaign: coordinator_only`; merge is
  serial; no phase branch wrote `ACTIVE_CAMPAIGN.md`.

## Validation Resolution

Final validation on a clean worktree of `main` (HEAD `9b2a0b3`), in a shell
confirmed free of inherited Frontier Workflow-2 control variables:
`python tools/verify.py --all` → `2120 passed, 0 failed`; all 14 Frontier
canaries pass; artifact audits clean.

The earlier `FLF-P31` 13-test failure was reproduced and explained: with the
inherited control variables `FRONTIER_CREATE_PR=1`, `FRONTIER_ALLOW_AUTOMERGE=1`,
`FRONTIER_MERGE_DRY_RUN=0`, `FRONTIER_PARALLEL=1`, and
`FRONTIER_MAX_PARALLEL_PHASES=3` present, exactly 13 tests in
`tests/test_ralph_driver.py` and `tests/test_github_utils.py` fail on clean
`9b2a0b3` because the variables force PR/merge/parallel driver paths during tests.
No FeatureStore/LabelStore/substrate test is among them. Authoritative validation
must run without those ambient operational variables; with them removed, the suite
is green. Treat the inherited-env failure as a validation-environment warning, not
a substrate blocker.

## Warnings and Deferrals (summary)

The full, enumerated residual warnings are in `CLOSEOUT.md`. In brief: accepted
`PASS_WITH_WARNINGS` phase history; verdict-parser metadata artifacts (generic
warning placeholders and inaccurate `external_providers_called`/`network_used`
flags); a pre-existing repo-wide Ruff backlog and Workflow-2 driver/GitHub test
scaffold tracked as their own defects; the `FLF-P26` real-Databento operator run
deferred (spec-sanctioned, synthetic path proven); `FLF-P30` E2E wording vs
engine `dry_run` semantics; defensible substrate scoping nuances
(`resolve_dataset_version` lifecycle gating one layer up;
`LabelQualityReport`/`LabelCoverageReport` delivered in the diagnostics gate;
`FLF-P22` registry-from-engine); and minor hardening/cleanup follow-ups (add
`.parquet`/`.arrow` to the raw-provider guard token list; strengthen `P13`–`P15`
test breadth; small dead-code cleanups). None blocks acceptance.

## Next-Campaign Readiness

The substrate is ready to be consumed by separately-authorized downstream
campaigns. Readiness does not assert alpha, tradability, profitability, strategy,
backtest, portfolio, broker, paper, live, order, account, or production readiness.

- `ALPHA_AGENT_FACTORY_MVP` may consume the substrate after separate coordinator
  authorization.
- `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` may consume the substrate after separate
  coordinator authorization.

Carry forward the same boundaries: local-only data, accepted DatasetVersions
only, no raw-provider access, no external provider calls, no committed
feature/label values or registry DBs, contamination metadata for locked-test use,
and no alpha, tradability, profitability, strategy, backtest, portfolio, broker,
paper, live, order, account, or production-readiness claim.
