# RISK_REGISTER — ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

Severity/likelihood scale: Low / Med / High. Each risk lists detection,
mitigation, owner role, related phases, and the blocking condition that, if
triggered, halts merge/escalates per `campaign.yaml > stop_conditions`.

| ID | Risk | Sev | Likelihood | Owner | Related phases |
| --- | --- | --- | --- | --- | --- |
| R-001 | Pilot becomes scaled alpha mining | High | Med | Research Director | P02,P05,P12,P24 |
| R-002 | Agent bypasses Runtime | High | Med | Diagnostics Runner | P14,P16-P20 |
| R-003 | Raw provider data accessed | High | Low | Data Contract Auditor | P01,P03,P13,P16-P20 |
| R-004 | Wrong DatasetVersion / FeaturePack / LabelPack used | High | Low | Data Contract Auditor | P03,P13,P14 |
| R-005 | Parquet values not used for research-scale scans | Med | Med | Diagnostics Runner | P03,P16-P20 |
| R-006 | session_label guard regresses | High | Low | No-Lookahead Auditor | P02,P08,P17,P23 |
| R-007 | Same-bar optimism | High | Med | No-Lookahead Auditor | P14,P23 |
| R-008 | Label leakage | High | Med | No-Lookahead Auditor | P14,P23 |
| R-009 | No cost stress or weak cost stress | High | Med | Diagnostics Runner | P04,P21 |
| R-010 | 1-3m fragile horizon overclaimed | Med | Med | Statistical Reviewer | P02,P21,P22,P25 |
| R-011 | ETH thin-session alpha overclaimed | Med | Med | Statistical Reviewer | P21,P22,P25 |
| R-012 | Unbounded grid / variant explosion | High | Med | Research Director | P05,P14,P24 |
| R-013 | Rejected ideas not recorded | Med | Med | Librarian | P26 |
| R-014 | Duplicate exposure rediscovered | Med | Med | AlphaSpec Critic | P12,P26,P27 |
| R-015 | Cross-market timestamp misalignment | High | Med | No-Lookahead Auditor | P07,P16,P23 |
| R-016 | Synthetic/seed-smoke result mistaken for evidence | Med | Low | Statistical Reviewer | P01,P16-P20,P27 |
| R-017 | Runtime diagnostics mistaken for Reference validation | Med | Med | Statistical Reviewer | P27,P28,P29 |
| R-018 | Candidate research mistaken for live/paper readiness | High | Low | Statistical Reviewer | P28 |
| R-019 | Agent self-review or self-promotion | High | Low | Statistical Reviewer | P06,P12,P25,P28 |
| R-020 | Heavy artifacts committed | High | Low | Librarian | all |
| R-021 | No future Validation Governance handoff | Med | Low | Research Director | P29 |
| R-022 | Too few ideas / pilot underpowered | Low | Med | Research Director | P02,P07-P12 |
| R-023 | Too many ideas / pilot overexpanded | Med | Med | Research Director | P02,P12,P28 |
| R-024 | Session/horizon matrix omitted | Med | Low | Diagnostics Runner | P22 |
| R-025 | Factor family budget ignored | Med | Med | AlphaSpec Critic | P05,P12 |
| R-026 | Cost/capacity proxy overclaimed | Med | Med | Statistical Reviewer | P04,P21,P25 |
| R-027 | Event/regime effects ignored or overfit | Med | Med | Statistical Reviewer | P09,P18,P22 |
| R-028 | Core Alpha Pilot blocks on unnecessary infra | Med | Med | Research Director | P13,P15 |
| R-029 | Pilot outputs not FactorLibrary-ready | Med | Med | Librarian | P27,P29 |
| R-030 | Human capital/live boundary bypassed | High | Low | Statistical Reviewer | all |

## Detail

### R-001 — Pilot becomes scaled alpha mining

- **Severity**: High
- **Likelihood**: Med
- **Detection**: scope audit; budget audit; Claude review
- **Mitigation**: Finite idea/AlphaSpec/variant/survivor budgets; family quotas; no continuous runner
- **Owner**: Research Director
- **Related phases**: P02,P05,P12,P24
- **Blocking condition**: broad discovery or continuous runner appears -> block merge / repair / escalate per stop_conditions.

### R-002 — Agent bypasses Runtime

- **Severity**: High
- **Likelihood**: Med
- **Detection**: source/import audit; Claude review
- **Mitigation**: Diagnostics only via RuntimeToolResult/RuntimeRunSummary; runtime package not edited
- **Owner**: Diagnostics Runner
- **Related phases**: P14,P16-P20
- **Blocking condition**: diagnostics re-implemented outside runtime tools -> block merge / repair / escalate per stop_conditions.

### R-003 — Raw provider data accessed

- **Severity**: High
- **Likelihood**: Low
- **Detection**: source path audit; import audit; canaries
- **Mitigation**: Registry-resolved inputs only; resolve_dataset_version; no raw file reads
- **Owner**: Data Contract Auditor
- **Related phases**: P01,P03,P13,P16-P20
- **Blocking condition**: pilot code reads .dbn/.zst/parquet provider files -> block merge / repair / escalate per stop_conditions.

### R-004 — Wrong DatasetVersion / FeaturePack / LabelPack used

- **Severity**: High
- **Likelihood**: Low
- **Detection**: input pack lock audit; Claude review
- **Mitigation**: Lock packs by id/hash in P03; P13 audits each spec's inputs
- **Owner**: Data Contract Auditor
- **Related phases**: P03,P13,P14
- **Blocking condition**: study runs against an unlocked or wrong pack -> block merge / repair / escalate per stop_conditions.

### R-005 — Parquet values not used for research-scale scans

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: artifact audit; git ls-files heavy globs
- **Mitigation**: Parquet required for research scans; JSONL audit/smoke/small only
- **Owner**: Diagnostics Runner
- **Related phases**: P03,P16-P20
- **Blocking condition**: research-scale scan reads JSONL or arbitrary paths -> block merge / repair / escalate per stop_conditions.

### R-006 — session_label guard regresses

- **Severity**: High
- **Likelihood**: Low
- **Detection**: canary_runner; Claude review
- **Mitigation**: Session-context features point-in-time only; role-aware guard respected
- **Owner**: No-Lookahead Auditor
- **Related phases**: P02,P08,P17,P23
- **Blocking condition**: session feature used without point-in-time metadata -> block merge / repair / escalate per stop_conditions.

### R-007 — Same-bar optimism

- **Severity**: High
- **Likelihood**: Med
- **Detection**: P23 audit; canaries; Claude review
- **Mitigation**: Entry/label timestamps validated; no same-bar fills
- **Owner**: No-Lookahead Auditor
- **Related phases**: P14,P23
- **Blocking condition**: a study uses same-bar optimism -> block merge / repair / escalate per stop_conditions.

### R-008 — Label leakage

- **Severity**: High
- **Likelihood**: Med
- **Detection**: P23 audit; canaries; Claude review
- **Mitigation**: label_available_ts validity; no final-session aggregates intraday
- **Owner**: No-Lookahead Auditor
- **Related phases**: P14,P23
- **Blocking condition**: label leakage detected -> block merge / repair / escalate per stop_conditions.

### R-009 — No cost stress or weak cost stress

- **Severity**: High
- **Likelihood**: Med
- **Detection**: P21 consolidation; Claude review
- **Mitigation**: base/stress_1/stress_2/double_cost required; thin-session penalties
- **Owner**: Diagnostics Runner
- **Related phases**: P04,P21
- **Blocking condition**: survivor lacks full cost stress -> block merge / repair / escalate per stop_conditions.

### R-010 — 1-3m fragile horizon overclaimed

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P21/P22 review; Claude review
- **Mitigation**: Fragile horizons = diagnostics only with stricter gates
- **Owner**: Statistical Reviewer
- **Related phases**: P02,P21,P22,P25
- **Blocking condition**: fragile-horizon result presented as robust -> block merge / repair / escalate per stop_conditions.

### R-011 — ETH thin-session alpha overclaimed

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P21/P22 review; Claude review
- **Mitigation**: Thin-session stricter stress; ETH research-only not trading-approved
- **Owner**: Statistical Reviewer
- **Related phases**: P21,P22,P25
- **Blocking condition**: ETH result presented as tradable -> block merge / repair / escalate per stop_conditions.

### R-012 — Unbounded grid / variant explosion

- **Severity**: High
- **Likelihood**: Med
- **Detection**: P24 audit; Claude review
- **Mitigation**: VariantBudget per study; P24 reconciles actual vs declared
- **Owner**: Research Director
- **Related phases**: P05,P14,P24
- **Blocking condition**: study exceeds its variant budget -> block merge / repair / escalate per stop_conditions.

### R-013 — Rejected ideas not recorded

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P26 ledger audit; Claude review
- **Mitigation**: RejectedIdeaLedger required for every rejection with reason
- **Owner**: Librarian
- **Related phases**: P26
- **Blocking condition**: a rejection is hidden -> block merge / repair / escalate per stop_conditions.

### R-014 — Duplicate exposure rediscovered

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: duplicate-exposure check; P26 hints
- **Mitigation**: Duplicate-exposure check; rejected-idea memory consulted
- **Owner**: AlphaSpec Critic
- **Related phases**: P12,P26,P27
- **Blocking condition**: duplicate exposure not flagged -> block merge / repair / escalate per stop_conditions.

### R-015 — Cross-market timestamp misalignment

- **Severity**: High
- **Likelihood**: Med
- **Detection**: P16 alignment diagnostics; P23 audit
- **Mitigation**: Each cross-market spec declares alignment+missingness diagnostics
- **Owner**: No-Lookahead Auditor
- **Related phases**: P07,P16,P23
- **Blocking condition**: cross-market study misaligns instrument timestamps -> block merge / repair / escalate per stop_conditions.

### R-016 — Synthetic/seed-smoke result mistaken for evidence

- **Severity**: Med
- **Likelihood**: Low
- **Detection**: Claude review; report-language policy
- **Mitigation**: Dry-run/seed/smoke clearly labeled non-evidence
- **Owner**: Statistical Reviewer
- **Related phases**: P01,P16-P20,P27
- **Blocking condition**: seed/smoke output presented as alpha evidence -> block merge / repair / escalate per stop_conditions.

### R-017 — Runtime diagnostics mistaken for Reference validation

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: Claude review; promotion audit
- **Mitigation**: Fast-path != reference truth; handoff != validation
- **Owner**: Statistical Reviewer
- **Related phases**: P27,P28,P29
- **Blocking condition**: diagnostics presented as Reference validation -> block merge / repair / escalate per stop_conditions.

### R-018 — Candidate research mistaken for live/paper readiness

- **Severity**: High
- **Likelihood**: Low
- **Detection**: promotion audit; Claude review
- **Mitigation**: Candidate != capital/live; allowed states only
- **Owner**: Statistical Reviewer
- **Related phases**: P28
- **Blocking condition**: candidate treated as paper/live readiness -> block merge / repair / escalate per stop_conditions.

### R-019 — Agent self-review or self-promotion

- **Severity**: High
- **Likelihood**: Low
- **Detection**: role/permission audit; Claude review
- **Mitigation**: Separation of duties enforced fail-closed
- **Owner**: Statistical Reviewer
- **Related phases**: P06,P12,P25,P28
- **Blocking condition**: self-review or self-promotion detected -> block merge / repair / escalate per stop_conditions.

### R-020 — Heavy artifacts committed

- **Severity**: High
- **Likelihood**: Low
- **Detection**: artifact audit; git ls-files heavy globs; gitignore
- **Mitigation**: Explicit staging; never-commit globs; artifact audit before merge
- **Owner**: Librarian
- **Related phases**: all
- **Blocking condition**: raw/value/Parquet/DB artifact staged -> block merge / repair / escalate per stop_conditions.

### R-021 — No future Validation Governance handoff

- **Severity**: Med
- **Likelihood**: Low
- **Detection**: P29 review; Claude review
- **Mitigation**: P29 mandates concrete failure-mode handoffs
- **Owner**: Research Director
- **Related phases**: P29
- **Blocking condition**: closeout lacks downstream handoffs -> block merge / repair / escalate per stop_conditions.

### R-022 — Too few ideas / pilot underpowered

- **Severity**: Low
- **Likelihood**: Med
- **Detection**: P12 budget audit; Claude review
- **Mitigation**: Minimum draft target (20-40); family coverage
- **Owner**: Research Director
- **Related phases**: P02,P07-P12
- **Blocking condition**: fewer than the minimum drafts produced -> block merge / repair / escalate per stop_conditions.

### R-023 — Too many ideas / pilot overexpanded

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P12 budget audit; Claude review
- **Mitigation**: Caps: <=40 drafts, <=10 approved, <=3 survivors, <=2 watch/candidate
- **Owner**: Research Director
- **Related phases**: P02,P12,P28
- **Blocking condition**: caps exceeded -> block merge / repair / escalate per stop_conditions.

### R-024 — Session/horizon matrix omitted

- **Severity**: Med
- **Likelihood**: Low
- **Detection**: P22 review; Claude review
- **Mitigation**: Session x horizon matrix required output
- **Owner**: Diagnostics Runner
- **Related phases**: P22
- **Blocking condition**: matrix missing -> block merge / repair / escalate per stop_conditions.

### R-025 — Factor family budget ignored

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P12 budget audit; Claude review
- **Mitigation**: Family budget 40/20/15/15/10 enforced in P12
- **Owner**: AlphaSpec Critic
- **Related phases**: P05,P12
- **Blocking condition**: approved specs violate family budget -> block merge / repair / escalate per stop_conditions.

### R-026 — Cost/capacity proxy overclaimed

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P21 review; Claude review
- **Mitigation**: BBO-1m proxy + stress; execution/capacity proxy-only language
- **Owner**: Statistical Reviewer
- **Related phases**: P04,P21,P25
- **Blocking condition**: proxy presented as proven capacity -> block merge / repair / escalate per stop_conditions.

### R-027 — Event/regime effects ignored or overfit

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P18/P22 review; Claude review
- **Mitigation**: Regime splits required; stability checks; event-exclusion placeholder
- **Owner**: Statistical Reviewer
- **Related phases**: P09,P18,P22
- **Blocking condition**: regime effects ignored or overfit -> block merge / repair / escalate per stop_conditions.

### R-028 — Core Alpha Pilot blocks on unnecessary infra

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: scope audit; Claude review
- **Mitigation**: Only minimal P15 additions allowed; no new big infra blocker
- **Owner**: Research Director
- **Related phases**: P13,P15
- **Blocking condition**: a new large infra dependency is introduced -> block merge / repair / escalate per stop_conditions.

### R-029 — Pilot outputs not FactorLibrary-ready

- **Severity**: Med
- **Likelihood**: Med
- **Detection**: P27 review; Claude review
- **Mitigation**: Survivor outputs carry FactorCard/EvidenceDraft/TrialLedger/verdict refs
- **Owner**: Librarian
- **Related phases**: P27,P29
- **Blocking condition**: survivor output not FactorLibrary-ready -> block merge / repair / escalate per stop_conditions.

### R-030 — Human capital/live boundary bypassed

- **Severity**: High
- **Likelihood**: Low
- **Detection**: scope audit; Claude review; stop conditions
- **Mitigation**: Human owns capital/live; no paper/live/broker/order code
- **Owner**: Statistical Reviewer
- **Related phases**: all
- **Blocking condition**: an agent makes a capital/live decision -> block merge / repair / escalate per stop_conditions.

