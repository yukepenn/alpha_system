# Agent Context Map

> **Entry point is `CRITICAL.md` (repo root), not this file.** For live
> campaign/phase status run `just status-doctor`; do not treat any campaign names
> below as current — they may be historical. This page is static orientation only.

This is the single orientation page for any AI agent (Claude,
Codex, Ralph) or human working in `alpha_system`. It tells you what the project
is, what is done, what is next, what to read, and what never to do. It is a map,
not a contract — the authoritative contracts live where this page points.

`alpha_system` is a **local-first, research-only AI Alpha Research Factory**. It is
**not** a backtester, a strategy repo, a broker, or a paper/live trading system.
It must never introduce alpha, profitability, tradability, or production-readiness
claims without evidence and review.

## Where things stand (do not read it from this file)

This page carries **no campaign status on purpose** — a hand-maintained status
section rots within one campaign. Resolve status live:

- Completed/active campaigns: `campaigns/README.md` + `ACTIVE_CAMPAIGN.md`.
- Live in-flight phase: `python tools/frontier/status_doctor.py` (authoritative).
- Repository structure: [`SYSTEM_MAP.md`](SYSTEM_MAP.md) — **generated** from the
  code (anchors, packages, commands); CI fails when it drifts.

Standing data facts (stable, not status): Databento is the primary deep-history
research source (GLBX.MDP3 ES/NQ/RTY OHLCV-1m + BBO-1m, 2018–2026, canonicalized
to sparse provider truth + a derived dense research grid); IBKR is a read-only
broker-validation source with clientId `101`/`102` hard-blocked. All raw/canonical
data, registries, and reports stay **local-only under `ALPHA_DATA_ROOT`**; nothing
market-data is ever committed.

## Read these first (in order)

1. **This file** — orientation.
2. [`SYSTEM_MAP.md`](SYSTEM_MAP.md) — generated structure map (anchors, packages, commands).
3. [`../AGENTS.md`](../AGENTS.md) — the cross-agent constitution (roles, lanes, hard constraints).
4. [`../CLAUDE.md`](../CLAUDE.md) — Claude-specific operating notes.
5. [`../ACTIVE_CAMPAIGN.md`](../ACTIVE_CAMPAIGN.md) — the live campaign/phase pointer (Ralph-maintained).
6. [`README.md`](README.md) — the docs index (everything in `docs/`, grouped).
7. The relevant campaign contract under `campaigns/<ID>/` (GOAL/PHASE_PLAN/ACCEPTANCE).

Do **not** try to read all ~70 docs. Use [`README.md`](README.md) to jump to the few you need.

## Directory map

| Path | What it is |
| --- | --- |
| `src/alpha_system/` | Source. `data/foundation` (provider-agnostic canonical contracts + DatasetVersion/Quality/Coverage + registry), `data/databento` + `data/ibkr` (provider adapters), `governance`, `backtest`, `experiments`, `factors`/`labels`/`signals`/`strategies`/`portfolio` (domain layers), `cli`, etc. |
| `campaigns/<ID>/` | Approved campaign contracts (goal/phase plan/acceptance). See `campaigns/README.md`. |
| `specs/` | Phase-spec **template only**; live specs are generated into `runs/<id>/` (local-only). |
| `handoffs/` | Executor handoffs (commit-eligible). Convention in `handoffs/README.md`. |
| `reviews/` / `decisions/` | Commit-eligible reviews; architecture decision records (ADRs). |
| `docs/` | Durable documentation (this directory). `data_foundation/`, `governance/`, `_historical/`. |
| `tools/` | Harness control plane: `frontier/` (Workflow-2 driver), `hooks/` (guards), `verify.py`. |
| `configs/` / `templates/` | Per-domain config examples; campaign/object templates. |
| `evals/` | Safety canaries (must fail when guards are bypassed). |
| `factors/` + `strategies/` (top-level) | **Local researcher-output scaffolding** (`.gitkeep` category buckets) — NOT the code. The code is in `src/alpha_system/{factors,strategies}/`. |
| `data/` `metadata/` `artifacts/` `runs/` | **Local-only** runtime/output roots — only READMEs/.gitkeep are tracked; `runs/**` is never committed. |

## Data-layer entry points (for Feature/Label work)

- Resolve an accepted DatasetVersion: `alpha_system.data.foundation.version_registry.resolve_dataset_version(...)`.
- Canonical contracts (provider-agnostic, `available_ts >= bar_end` enforced):
  `CanonicalBarRecord` (`data/foundation/bars.py`), `CanonicalBBORecord`
  (`data/foundation/quotes.py`), and the dense research view `DenseGridBarRecord`
  (`data/foundation/grid.py`; synthetic no-trade rows are explicitly flagged and
  are **not** executable/tradability evidence).
- Consumption rules: [`data_foundation/DATASET_CONSUMPTION.md`](data_foundation/DATASET_CONSUMPTION.md);
  Databento specifics under [`data_foundation/databento/`](data_foundation/databento/).
- Partitions + locked-test contamination metadata: `DatasetPartitionPlan` /
  `require_governance_metadata_for_locked_partition_use` in `data/foundation/datasets.py`.
- **Use the canonical `data/foundation/*` layer**, not the older flat `data/*` layer
  (`data/contracts.py::OneMinuteBar`, `data/versions.py::DatasetVersion`, `data/sessions.py`)
  that predates it. Known deferred refactors (incl. the Databento→IBKR helper boundary)
  are tracked in [`STRUCTURAL_BACKLOG.md`](STRUCTURAL_BACKLOG.md).

## Governance entry points

Specs/gates/ledgers live in `src/alpha_system/governance/` (AlphaSpec, StudySpec,
LabelSpec, FeatureRequest, EvidenceBundle, TrialLedger, PromotionGate,
RejectedIdeaLedger). Docs in [`governance/`](governance/). Features/labels/alpha
must go through the appropriate spec/gate; no raw-provider access from research code.

## Verify / test commands

```bash
python tools/verify.py --smoke      # required-files / quick check
python tools/verify.py --all        # lint + typecheck + tests + boundaries + artifacts
python -m pytest                    # full suite (use CI=true to reproduce CI gating)
python tools/hooks/canary_runner.py # safety canaries (must all pass)
```

## Artifact rules (hard)

- Explicit staging only. **Never** `git add .` / `git add -A`. **Never** force push.
- Never commit raw/canonical data, registries/SQLite/DB, parquet/arrow/feather,
  `.dbn`/`.zst`, logs, caches, model artifacts, secrets, or anything under `runs/**`.
- `git ls-files runs` must return empty. Real data stays under `ALPHA_DATA_ROOT`.

## Never do

- No order/account/broker/paper/live/order-routing code or calls.
- No alpha/tradability/profitability/production claims without evidence + review.
- Do not weaken or game tests or guards; do not bypass governance gates.
- IBKR clientId `101`/`102` are hard-blocked; Databento API key is env-only (never logged/committed).

## How to find historical records (audit trail)

- Campaign contracts + closeouts: `campaigns/<ID>/` (index: `campaigns/README.md`).
- Executor handoffs: `handoffs/` (index + convention: `handoffs/README.md`).
- Architecture decisions: `decisions/` (index: `decisions/README.md`).
- Superseded docs: `docs/_historical/`.
- Per-run audit trail (local-only): `runs/<run_id>/`.
