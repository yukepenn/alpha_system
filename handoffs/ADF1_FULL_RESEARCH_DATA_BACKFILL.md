# ADF1 Full Research Data Backfill & Operator Fixes — Handoff

Status: **PASS_WITH_WARNINGS** (machinery production-hardened + proven on real data; full multi-year pull is operator-supervised, partial, resumable). No alpha/feature/label research. No real data committed.

## Headline data-availability finding (probed 2026-06-04, IBKR paper gateway 127.0.0.1:4002)
This IBKR **paper** account has **no deep history**. Windowable 1-minute historical backfill (which needs *dated* contracts — CONTFUT rejects `endDateTime` so it can't be paginated backward) is only available from the **2024-06 contracts onward (~2024-04 → present, ~2 years)** for all six roots. 2018/2020 is **unreachable from IBKR** (IBKR is not a deep historical 1-min futures vendor; expired-contract depth is capped). Deep history (e.g. 2018) requires a separate historical data vendor — a future task.

| Root | CONTFUT head (TRADES) | Earliest dated contract |
|---|---|---|
| ES | 2022-03-20 | 2024-06-21 |
| NQ / RTY | 2023-03-19 | 2024-06-21 |
| MES / MNQ / M2K | 2023-03-19 | 2024-06-21 |

Per the agreed scope, we materialize the **available** depth honestly (labeled with discovered start dates), not 2018.

## Machinery hardened & merged
- **PR #99** — runner production hardening: runtime pacing (sliding-window `max_requests_per_window`/`window_seconds` + per-identical `min_seconds_between_identical_requests`, injected clock/sleep), retry/backoff per chunk that continues the run (quarantine + INCOMPLETE, no silent gaps), IBKR-compliant **1-min day-level sub-chunking** of dated FUT (CONTFUT not sub-chunked; span clamped ≤1 day), `max_chunks` raises rather than truncating, guard/config errors fail fast. Micro MES/MNQ/M2K instrument config. PEP668/venv install docs.
- **PR #100** — materialization hardening: **session-aware coverage** (per-trading-session expected intervals; weekends/holidays not false gaps; within-session gaps still block — coverage is an independent backstop), **2024–2026 CME holiday/early-close calendar**, dated-FUT `includeExpired=True`, manifest `min_contract_expiry` filter.
- **PR #101** — two dated-FUT bugs found by **live IBKR validation** (unit fakes could not surface them): connector passed our internal `contract_ref` as `localSymbol` → IBKR "No security definition" → 0 bars (fixed: resolve via symbol + month + exchange + currency + includeExpired); sub-chunk `durationStr="1 D"` made IBKR return only ~1 hour (fixed: always emit `"{seconds} S"`; verified `"1 D"`→60 bars, `"86400 S"`→1440).

## Install (PEP668 system Python — no venv present)
`[ibkr]` optional extra exists (`ib_insync>=0.9.86`). Recommended: `python -m venv .venv && .venv/bin/pip install -e ".[ibkr]"`. Operator fallback used here: `python -m pip install --target ~/.alpha_ibkr_libs ib_insync tzdata` + run with `PYTHONPATH=src:~/.alpha_ibkr_libs`. **`tzdata` is required** in the ib_insync runtime or contract-details parsing crashes on `US/Eastern`.

## Live validation (proven end-to-end on real data)
Tiny validation pull of ES 202512 (expired contract) → daily sub-chunks each return **full 1440-bar days**, COMPLETE, 0 provider errors. Confirms the hardened runner + connector resolve dated/expired contracts, sub-chunk at day granularity, pace, and write content-addressed raw correctly.

## Mini backfill — LAUNCHED (operator-supervised, running, resumable)
- Manifest: `~/alpha_data/alpha_system/manifests/mini/full_backfill_manifest.json` — ES/NQ/RTY, **9 dated quarterly FUT contracts each (202406…202606)**, 1 min, TRADES, `min_contract_expiry=2024-06-01`. 27 specs → expands at runtime to ~2,400 day-sub-chunks.
- Env (no secrets): `ALPHA_DATA_PULL_AUTHORIZED/ALPHA_ALLOW_EXTERNAL_IBKR/ALPHA_IBKR_READ_ONLY_MODE/ALPHA_ALLOW_RAW_LOCAL_WRITE=1`, host 127.0.0.1, port 4002, clientId 201, `ALPHA_DATA_ROOT=~/alpha_data/alpha_system`.
- Launch / resume command (re-run to resume; raw is immutable, completed chunks skipped within a run; a fresh run re-pulls — for resume across runs, re-launch the same manifest after clearing nothing):
  ```
  PYTHONPATH=src:~/.alpha_ibkr_libs <auth env...> \
    python -m alpha_system.data.ibkr.backfill_connect \
      --manifest ~/alpha_data/alpha_system/manifests/mini/full_backfill_manifest.json \
      --pacing-policy configs/data/request_pacing_policy_to_be_verified.json
  ```
- Runtime: conservative pacing (45 req / 600 s) → ~2,400 requests ≈ **many hours** (partial in-session). All raw is local-only under `ALPHA_DATA_ROOT`; nothing committed. Early health: full 1440-bar days landing, 0 provider errors.

## Proven: first real dated-FUT DatasetVersion registered (in-session)
`dsv_ibkr_es_dated_202404_validation_v1` — ES dated FUT (`fcr_ibkr_es_fut_202406`), **April 2024, 24,840 canonical bars = 18 complete ETH sessions (18×1380)**, `coverage_status=PASSING`, quality WARNING (non-blocking), `validation_partition`, local-only registry. This proves the full hardened chain end-to-end on real multi-week dated data: dated/expired resolution → day-sub-chunked paced pull → session-aware coverage → accepted DatasetVersion.

**CRITICAL operator note — window alignment:** `--start-ts`/`--end-ts` MUST bracket WHOLE ETH sessions (open **22:00Z** → close **21:00Z** in CDT; 23:00Z→22:00Z in CST/winter). A window starting mid-session (e.g. 00:00Z) makes the edge session expect opening bars the filter excludes → `coverage_status=BLOCKING` (fail-closed, never silent). The fail-closed gate works: a mis-aligned or gappy window is refused (`registered:false`, non-zero exit), never registered.

## Per-partition materialization (next; as windows complete)
Materialize per trading-session window, per partition, into local-only DatasetVersions (session-aligned bounds, per the note above):
```
PYTHONPATH=src ALPHA_DATA_ROOT=~/alpha_data/alpha_system \
  python -m alpha_system.data.ibkr.materialize --symbols ES,NQ,RTY \
    --registry-path ~/alpha_data/alpha_system/registry/datasets.sqlite \
    --data-version <dsv_id> --partition <validation_partition|locked_test_candidate> \
    --instrument-config configs/data/ibkr_es_nq_rty_instruments.json \
    --start-ts <session-open Z> --end-ts <session-close Z>
```
Available data spans the **validation** (2024 portion) and **locked_test_candidate** (2025→present) partitions; the dev partition (2018-2022) is unreachable from this source.

## Micro batch (MES/MNQ/M2K) — separate batch
Generate a SEPARATE micro manifest and run after mini (do not mix): `manifest_builder --symbols MES,MNQ,M2K --full-start-date 2024-01-01 --full-end-date 2026-06-30 --min-contract-expiry 2024-06-01`, materialize with `configs/data/ibkr_mes_mnq_m2k_instruments.json` into separate micro DatasetVersions (role = execution_sizing_parity, not primary alpha truth). Micro earliest dated = 2024-06-21 (same limit); do NOT claim 2020 micro history from this source.

## Artifact / safety
- Read-only IBKR boundary intact; clientId 101/102 hard-blocked (used 201); no order/account/broker/paper/live surface; provider calls require authorization env + reachable gateway; never run in CI.
- All raw/canonical/registry data is local-only under `ALPHA_DATA_ROOT` (outside repo). `git ls-files runs` empty; no `*.raw|*.sqlite|*.parquet` committed.
- No alpha/feature/label/strategy/ML scope added. No tradability/profitability/live/paper/broker/production claims.

## Readiness for ALPHA_FEATURE_LABEL_FOUNDATION_V1
The production-hardened pipeline yields accepted, session-complete, quality+coverage-gated DatasetVersions for the available ~2024→present window (consume via `resolve_dataset_version`; see `docs/data_foundation/DATASET_CONSUMPTION.md`). Deep (2018) history is a separate data-vendor task and must not block Feature/Label, provided the available-depth DatasetVersions are accepted and the limit is explicit.
