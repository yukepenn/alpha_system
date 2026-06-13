# FUTSUB Kill-Shot Substrate-Invariant Audit — V2 (Post-RELOCK_V2 + Post-Re-Materialization)

- Date: `2026-06-13`
- Auditor: coordinator-dispatched read-only audit (re-run)
- Supersedes: `research/discovery_rigor_floor_v1/substrate_invariant/FUTSUB_KILL_SHOT_substrate_invariant_audit.md`
  (generated `2026-06-12T05:06Z`), whose Predicate 4 body cited the stale
  pre-RELOCK_V2 count of `4560` feature locks. This V2 audit re-runs every
  predicate against the live registry after `P110000_RELOCK_V2` (PR #405) and the
  2026-06-12 full-grid re-materialization of the `bbo_tradability` /
  `session_calendar` / `regime_volatility` families.
- Closes (re-run against V2): `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` row 9;
  `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 7.
- Run context: repo `main` post-#405; `ALPHA_DATA_ROOT=~/alpha_data/alpha_system`;
  FUTSUB run `2026-06-07T235209Z_...` remains STOPPED before P28; this audit
  performed zero writes to registries, values, run state, or git.
- Registries audited read-only (`sqlite3 ... mode=ro`): features.sqlite
  (2192 records: 1264 REGISTERED / 928 DEPRECATED), labels.sqlite (2373: 1368 /
  1005), datasets.sqlite (29 dataset_versions).
- This file is value-free: statuses, counts, ids, schema/column names, issue
  codes, commands, and code citations only.

## Supersession Note (count correction)

The prior audit cited `4560 feature + 840 label locks`; that was the
pre-`P110000_RELOCK_V2` (P022000) corpus. After RELOCK_V2 the committed locks sum
to **4112 feature + 840 label** lock handles, resolving to **1168 DISTINCT
feature versions + 96 DISTINCT label versions** (handles are duplicated across
sspecs and per-partition lock lists). The 2026-06-12 deprecate-first
re-materialization (backup
`registry/backups/pack_restore_deprecate_first_20260612T103233Z`) moved 168
predecessor feature versions to DEPRECATED and registered fresh REGISTERED
versions on the post-#401 minute grid; the V2 locks point only at the fresh
REGISTERED versions.

V1→V2 successor map (feat/label lock sums per kill-shot family, R-036 retired):
f6cbd88 480/96 (48 retired), 1604b06 480/96 (48), dec89a3 456/96 (48),
840e834 552/96 (48), c237c6a 552/96 (48), 533f665 600/96 (48). The other 4 V2
sspecs (19cbe3c 216/48, 40b1e1c 280/72, b0819e7 280/96, ce82701 216/48) add the
remainder. R-036 retired-lock total across all 10 sspecs = **448** (sum of
per-sspec `v2_relock_summary.dropped_feature_lock_count`), covering the two
no-replacement countdown features only.

## Predicate Verdicts (against V2 / live registry)

| # | Predicate | V2 Verdict | Key V2 counts |
|---:|---|---|---|
| 1 | No constant-valued flag columns | **PASS** | 1 flag-like name (`git_dirty`) only in 8 zero-row dataset tables; 0 constant flag columns in populated record tables |
| 2 | ≥2 session values per trading day | **PASS** | 1920/1920 kill-shot session-declaring locks role-marked; 17,055/17,073 trading-day cells with 2 sessions (carried forward — canonical partitions unchanged by value-only re-mat); 18 holiday/closure cells on 3 dates; vocabulary=2 |
| 3 | Role-marker WARN documented | **WARN (tolerated)** | 696 markerless non-session rows (552 REGISTERED + 144 DEPRECATED, no session field); 96 markerless session-declaring rows ALL DEPRECATED + 0 lock-referenced. Moved 648→696 (benign DEPRECATED growth from deprecate-first); resolver fallback `input_resolver.py:1824-1828` grants strictly-less permission, never more |
| 4 | Zero locks → DEPRECATED; all REGISTERED + resolvable | **PASS** | see below |

Predicate 4 evidence (the count-corrected core):
- Feature locks: 4112 handles → **1168 distinct fver**, all `REGISTERED`;
  0 DEPRECATED; 0 unresolved; 0 in `feature_deprecation_records`; **0
  missing-Parquet on disk; 0 content-hash mismatch** vs live registry.
  *(Independently spot-verified by coordinator query 2026-06-13T02:22 ET: 1168/1168
  present + REGISTERED, 0 missing, 0 not-registered.)*
- Label locks: 840 handles → **96 distinct lver**, all `REGISTERED`; 0
  DEPRECATED; 0 unresolved; 0 missing-Parquet; 0 hash mismatch. *(Spot-verified:
  96/96 present + REGISTERED.)*
- DatasetVersion locks: **24/24** distinct resolve; **19 ACCEPTED + 5
  ACCEPTED_WITH_WARNINGS; 0 BLOCKED; 0 missing-lock**; 0 acceptance_state
  mismatch across all lock entries. The registry's 2 BLOCKED + 2 no-lock dsv are
  unreferenced. Composition: 8 `ohlcv_1m` + 8 `ohlcv_dense_research_grid` + 8
  `bbo_1m`.
- Deprecate-first integrity: 168 fvers moved REGISTERED→DEPRECATED on 2026-06-12
  (120 session_calendar + 48 base_ohlcv) are **0-referenced** by any V2 lock; the
  fresh REGISTERED replacements are all V2-referenced.
- R-036 countdown: 48 distinct fvers (`session_calendar_roll_bars_to_roll` ×24 +
  `session_calendar_roll_minutes_to_roll` ×24) all DEPRECATED, **0-referenced**
  (448 retired lock slots across 10 sspecs).

## Bar-Grid Re-Materialization Check (post-#401)

PR #401 / `P085901` normalized bbo emission to `bar_end_ts` on reference
(`features/families/bbo/family.py`) and fast (`features/fast/bbo_tradability.py`)
paths, with a written contract in `docs/FACTOR_COMPUTE.md` and the registry grid
canary `governance/canaries/registry_event_ts_grid.py`. Direct on-disk
verification across **1,536 re-materialized bbo/session/regime packs
(4,135,758,940 rows)** referenced by the 6 kill-shot StudySpecs — including the
456 bbo packs in `sspec_533f665...` — off-grid `event_ts` (`second != 0`) = **0**;
unparseable = 0. The 3 committed V2 surrogate reports (regime_dec89a,
vwap_session_1604b0, vwap_session_f6cbd8) each record `Off-grid locked label
event_ts count: 0`.

Open items (reporting / debt, NOT substrate):
- Committed `*_real_calibration_v2.md` reports exist for 3/6 kill-shot families
  at audit time; bbo (533f665) + 2 liquidity_pa (840e83, c237c6) V2 reports land
  on calibration completion (~6:36 AM ET 2026-06-13). Their off-grid=0 fact is
  already confirmed directly on the registered packs above.
- The grid canary's `BBO_PENDING_RE_MATERIALIZATION` allowlist entry
  (`registry_event_ts_grid.py`) is now stale debt — bbo packs are on the minute
  grid and the exemption can be retired (follow-up).

## Roll-Up

Overall: **GREEN** (PASS, PASS, WARN-documented-tolerated, PASS). No FAIL. The
single WARN is the pre-existing, re-verified legacy role-marker gap — benign for
non-session rows and fail-closed/unreferenced for the markerless
session-declaring rows. No V2 sspec references a missing-Parquet or DEPRECATED
lock (hunted for explicitly; found none).

## Attestation

Value-free: statuses, counts, identifiers, schema/column names, calendar dates,
issue codes, commands, and code citations only. No feature/label values, returns,
prices, spreads, signals, or cost numbers. No alpha, profitability, tradability,
execution-quality, or production-readiness claim is made.
