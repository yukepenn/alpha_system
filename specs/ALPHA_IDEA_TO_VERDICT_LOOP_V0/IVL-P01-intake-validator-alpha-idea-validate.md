# ALPHA_IDEA_TO_VERDICT_LOOP_V0 — Phase Specs (IVL-P00 .. IVL-P06)

> Shape source: these specs follow the live phase-spec shape used by `specs/DIFFERENTIATED_KILLSHOT_V1/DK-P00..DK-P05` — YAML front-matter (`campaign_id, phase_id, lane, status, dependencies, executor, reviewer, verifier`) then the `tools/frontier/spec_schema.py:REQUIRED_SECTIONS` (Purpose, Context, Scope, Non-Goals, Expected Files, Forbidden Changes, Validation, Done Criteria, Handoff Requirements, Review Requirements) plus the DK convention sections (Interfaces/Contracts, Allowed Paths, Allowed Test Paths, Artifact Policy, Auto-Merge/Review Policy, Repair-or-Rollback). `REQUIRED_SECTIONS` is a review convention, not an automated gate; the enforced gates are `require_campaign_files` (6-file bundle), `load_campaign_yaml` + `parse_campaign_phases` (`just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0`), and a fresh mock run.
>
> Research-only language throughout: no alpha / profitability / tradability / production claims. Lanes GREEN/YELLOW only — no RED. Allowed verdict outputs: REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE. `runs/**` is local-only and never staged.
>
> **Shared `forbidden_paths` (YAML anchor in `campaign.yaml`):** `src/alpha_system/execution/**`, `broker/**`, `live/**`, `portfolio/**`, `management/**`, `backtest/**`, `l2/**`, `agent_factory/**`, `src/alpha_system/core/value_store.py` (import allowed, EDITS forbidden), `src/alpha_system/strategies/templates.py`, `src/alpha_system/research/conditional_probe.py` semantics (additive guard only — see IVL-P02), `src/alpha_system/research/track_a_scorer.py`, `tools/differentiated_killshot_v1/**`, `research/futures_substrate_scaleout_v1/**`, `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`.
> **Shared commit-eligible globs (every phase):** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`, `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`. `campaign.yaml` `allowed_paths` MAY list `runs/**`; the spec's Allowed Paths MUST NOT (local-only; `git ls-files runs` stays empty).

---
---

---

# IVL-P01 — Intake Validator + `alpha idea validate` (emit canonical objects; migrate the 8 Track-A cards)

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P01
lane: YELLOW
status: draft
dependencies: [IVL-P00]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Build the front door: a new canonical **IdeaDraft** intake wrapper + `alpha idea validate <idea.yaml>` that emits a canonical **AlphaSpec** (always) + **MechanismCard** (+ **SetupSpec** when `study_kind == context_not_equal_trigger`), carries the optional `study_kind` discriminator, links the sub-objects as lineage sidecars (not by schema mutation), and **fails closed** when any canonical field (`source`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure`) cannot be populated. Migrate the 8 Track-A cards' content into canonical fields, with `day_of_week_effect` as the live `main_effect` exemplar.

YELLOW: this is the trunk-construction engine + a real schema migration with a fail-closed contract.

## Context

Verified live:

- **Reusable governance constructors:** `governance/mechanism_card.py:151 create_mechanism_card` (keyword-only, `stamp` defaults `EXPLORATORY_STAMP`), `:198 validate_mechanism_card`, `:186 generate_mechanism_id`; `governance/setup_spec.py:157 create_setup_spec`, `:208 validate_setup_spec`; `governance/alpha_spec.py:160 validate_alpha_spec`, `:148 generate_alpha_spec_id` (**no** `create_alpha_spec` factory — construct payload → `generate_alpha_spec_id` → `validate_alpha_spec`). AlphaSpec links via `hypothesis_id`; the wrapper supplies/derives it.
- **Closed-schema hazard (from IVL-P00 ADR):** `study_kind` and all lineage links live on the NEW `IdeaDraft` wrapper, never on the three frozen dataclasses.
- **CLI registration pattern (mirror exactly):** `cli/main.py:8-20` imports `register_subparser as register_<domain>_subparser`; `:34` `subparsers = parser.add_subparsers(dest="command")`; `:35-48` calls each `register_*_subparser(subparsers)`. `cli/study.py:71` `register_subparser(...)` → `add_parser` → `add_subparsers(dest="study_command")` → `set_defaults(handler=...)`; `main()` dispatches via `getattr(args,"handler",None)`. `cli/idea.py` is absent (clean slate). Handlers delegate to library fns and wrap domain errors → exit 2 (`cli/study.py`, `cli/factor.py`).
- **Track-A cards (read-only refs):** 8 files `research/differentiated_substrate_v1/cards/*.json`, distinct schema; pure documents. Migration is content-map + structural enrichment per the IVL-P00 schema map. The kebab `mechanism_id` becomes `MechanismCard.source = "track_a:<slug>"` (canonical id minted fresh `mech_<24-hex>`); the STOPPED DK `dataset_scope['mechanism_id']` seam must stay unbroken.
- **Data partition:** `day_of_week_effect` (`existing_substrate`) is the sole live `main_effect` exemplar; the 5 `derivable_from_exchange_calendar` cards migrate as records whose testability is DATA_GAP (IVL-P02); `fomc_drift`/`cpi_surprise_reversion` (`needs_paid_data`) migrate as record-only (never tested).

## Scope

1. **New `IdeaDraft` wrapper** at `src/alpha_system/governance/idea_draft.py`: a validated intake object holding the optional `study_kind ∈ {main_effect, context_not_equal_trigger}` discriminator (validated; default/absence = `main_effect`), the source `idea.yaml` provenance, and the lineage references to the emitted AlphaSpec/MechanismCard(/SetupSpec) IDs. It is a NEW object — it does not mutate AlphaSpec/MechanismCard/SetupSpec. Fail closed on unknown `study_kind` or missing required intake fields.
2. **`alpha idea validate <idea.yaml>`** in new `src/alpha_system/cli/idea.py` (+ one import alias and one `register_idea_subparser(subparsers)` call in `cli/main.py`): parse `idea.yaml`, build the IdeaDraft, then emit:
   - **AlphaSpec** (always) via payload → `generate_alpha_spec_id` → `validate_alpha_spec`.
   - **MechanismCard** via `create_mechanism_card(...)` (`stamp=EXPLORATORY_STAMP`), satisfying the substantive-text gates.
   - **SetupSpec** via `create_setup_spec(...)` only when `study_kind == context_not_equal_trigger`.
   - A lineage sidecar record (the IdeaDraft) tying the IDs together.
   - **Fail closed** (non-zero exit, clear error) if any of `source`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure` cannot be populated from the idea.yaml — never synthesize a placebo value.
3. **Migrate the 8 Track-A cards** as the `main_effect` exemplar set: a migration mapper (library fn, e.g. under `governance/idea_draft.py` or a sibling `governance/track_a_migration.py`) that maps each card per the IVL-P00 field map, mints `mech_<24-hex>`, sets `source="track_a:<slug>"`, and writes canonical outputs under a NEW canonical dir (e.g. `research/idea_to_verdict_loop_v0/migrated_cards/**`) — **NOT** edits to `cards/*.json`. Multi-horizon cards apply the documented collapse rule. `day_of_week_effect` is the live exemplar; the 5 calendar cards + 2 paid-data cards migrate as records (their downstream testability/deferral is IVL-P02's call).
4. **Tests** (see Allowed Test Paths): IdeaDraft validation + `study_kind` routing; `alpha idea validate` emits the canonical set and registers in `build_parser()`; fail-closed on each of the 4 missing fields; a **canonical-vs-card parity test** asserting every migrated card's canonical fields match the field map (this test is the precondition for any future card retirement — retirement itself is out of V0 scope).

## Non-Goals

- Mutating AlphaSpec/MechanismCard/SetupSpec dataclasses or their REQUIRED_FIELDS/IDs.
- Editing `cards/*.json`, deleting them, or touching the STOPPED `tools/differentiated_killshot_v1/**` / `research/track_a_scorer.py` `dataset_scope` consumers.
- Running any real-data probe/metric, materialization, or testability gate (IVL-P02/P03).
- Implementing FeatureRequest materialization for the 5 calendar cards or sourcing paid data for fomc/cpi.
- Any promotion, FactorLibrary entry, or downstream-module charter.

## Expected Files (illustrative)

- `src/alpha_system/governance/idea_draft.py` — new (IdeaDraft wrapper + `study_kind` validation + lineage).
- `src/alpha_system/governance/track_a_migration.py` — new (card→canonical mapper) *(or folded into idea_draft.py)*.
- `src/alpha_system/cli/idea.py` — new (`register_subparser` with `validate` subcommand → handler).
- `src/alpha_system/cli/main.py` — edit (one import alias + one `register_idea_subparser(subparsers)` call).
- `research/idea_to_verdict_loop_v0/migrated_cards/**` — new (canonical migration outputs; value-free).
- `tests/unit/governance/test_idea_draft.py`, `tests/unit/governance/test_track_a_migration.py`, `tests/unit/cli/test_idea_cli.py` — new.
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`, `reviews/.../IVL-P01/**`.

USED unchanged: `governance/mechanism_card.py`, `governance/setup_spec.py`, `governance/alpha_spec.py` (called, not edited). `research/differentiated_substrate_v1/cards/*.json` read-only.

## Interfaces / Contracts

- **AlphaSpec construction:** payload over `ALPHA_SPEC_REQUIRED_FIELDS` (`alpha_spec.py:31-45`) → `generate_alpha_spec_id(payload)` → `validate_alpha_spec(payload)`. The conditioning/lookahead/orthogonality material maps into `timestamp_assumptions`/`exclusion_rules`/`expected_failure_modes`/`promotion_criteria`/`data_assumptions` per the IVL-P00 map.
- **MechanismCard:** `create_mechanism_card(... stamp=EXPLORATORY_STAMP, source="track_a:<slug>", variant_budget=<int>0>, cost_sensitivity={...}, duplicate_exposure={...} ...)`; substantive-text gates on `rationale`/`expected_mechanism` must pass or it fails closed.
- **SetupSpec (shape lane only):** `create_setup_spec(... entry_context={...}, event_trigger={...}, path_label="lspec_…|lset_…", stamp=EXPLORATORY_STAMP)`; distinctness is the author's responsibility (validator checks declared distinctness only).
- **CLI:** `cli/idea.py:register_subparser(subparsers)` adds `idea` → `idea_subparsers(dest="idea_command")` → `validate` subparser with `idea_yaml` positional + `set_defaults(handler=run_idea_validate)`; handler wraps domain validation errors → exit 2.
- **Fail-closed contract:** missing/invalid `source`/`cost_sensitivity`/`variant_budget`/`duplicate_exposure` ⇒ non-zero exit + explicit message; no fabricated value.

## Forbidden Changes

- Editing any path under `forbidden_paths`; editing the three governance dataclasses' schemas/IDs; editing or deleting `cards/*.json`; touching the STOPPED DK tooling or its `dataset_scope` seam.
- Adding a runtime dependency (`numpy`/`pandas`/`polars` stay unimportable); sourcing paid data; un-deferring fomc/cpi.
- Synthesizing placebo values for the 4 fail-closed fields; flipping any `promotion_eligible` to true; emitting a PromotionDecision/FactorLibrary entry.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls.
- Weakening, skipping, or adding visible test-only branches to existing tests/canaries.
- Any alpha/tradability/profitability claim or second-PnL truth.

## Validation

```bash
# 1) Narrowest meaningful tests first.
python -m pytest tests -k "idea or track_a or idea_draft" -q
# 2) CLI front door registers + validates a fixture idea.yaml.
python -m alpha_system.cli.main idea validate research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml
# 3) Repo smoke + canaries (planted_fake_alpha, true-alpha pair, governance_random_target,
#    forbidden_scope_drift, forbidden_exploratory_promotion, forbidden_second_pnl_truth).
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
# 4) No new dependency.
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"
# 5) Frozen dataclasses byte-unchanged (only called, not edited).
git diff -- src/alpha_system/governance/alpha_spec.py src/alpha_system/governance/mechanism_card.py src/alpha_system/governance/setup_spec.py
# 6) Cards untouched.
git diff -- research/differentiated_substrate_v1/cards
# 7) Run-artifact discipline.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared governance behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons in the handoff.

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`; review under `reviews/.../IVL-P01/**`. Migrated-card outputs are value-free (ids/counts/text only — no raw rows, parquet, registry, or DB). Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `src/alpha_system/governance/idea_draft.py`
- `src/alpha_system/governance/track_a_migration.py`
- `src/alpha_system/cli/idea.py`
- `src/alpha_system/cli/main.py`
- `research/idea_to_verdict_loop_v0/**`
- `tests/unit/governance/test_idea_draft.py`
- `tests/unit/governance/test_track_a_migration.py`
- `tests/unit/cli/test_idea_cli.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/unit/governance/test_idea_draft.py`, `tests/unit/governance/test_track_a_migration.py`, `tests/unit/cli/test_idea_cli.py`. Do not weaken/skip existing tests or add visible test-only branches.

## Done Criteria

- `IdeaDraft` wrapper exists with validated `study_kind` (greenfield, off the frozen dataclasses) and lineage refs.
- `alpha idea validate <idea.yaml>` registers in `build_parser()`, emits AlphaSpec (always) + MechanismCard (+ SetupSpec when shape-bearing) + lineage sidecar, and **fails closed** if any of `source`/`cost_sensitivity`/`variant_budget`/`duplicate_exposure` cannot populate.
- All 8 Track-A cards migrate into canonical fields (under the new canonical dir, not card edits): `mech_<24-hex>` minted, `source="track_a:<slug>"`, `day_of_week_effect` as the `main_effect` exemplar; multi-horizon collapse rule applied; STOPPED DK `dataset_scope` seam unbroken.
- Canonical-vs-card parity test passes (precondition for any future retirement — not done in V0).
- The three governance dataclasses + `cards/*.json` are byte-unchanged; `numpy`/`pandas`/`polars` unimportable; smoke + canaries pass; `git ls-files runs` empty; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`: scope delivered; exact validation commands + results; skipped checks + reasons; files changed by path; explicit confirmation that (a) `study_kind`/lineage live only on the new IdeaDraft wrapper (frozen dataclasses byte-unchanged), (b) AlphaSpec is always minted via `validate_alpha_spec`+`generate_alpha_spec_id`, (c) the 4 fail-closed fields fail closed (no placebo), (d) all 8 cards migrated with `mech_<24-hex>`+`source="track_a:<slug>"` and the DK `dataset_scope` seam is unbroken, (e) the parity test passes, (f) cards/*.json untouched, no paid data, `git ls-files runs` empty, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P01/**`. Reviewer adversarially confirms: `study_kind`/lineage are on the wrapper, not mutating any frozen schema/ID (diff proves byte-unchanged dataclasses); AlphaSpec always minted (graveyard-key precondition for IVL-P05 satisfied); the 4 fail-closed fields genuinely fail closed (no synthesized value); the migration is faithful to the IVL-P00 field map, mints `mech_<24-hex>`, preserves the slug as `source`, leaves `cards/*.json` and the STOPPED DK seam untouched, and the parity test actually compares fields (not a stub); no promotion / no paid data / research-only language; smoke + canaries pass; `git ls-files runs` empty; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy + human authorization.

## Repair-or-Rollback

- **In-scope repair only:** fix the wrapper, migration mapper, CLI wiring, or tests within Allowed Paths; no scope expansion.
- **Rollback:** additive new modules + one `main.py` edit + value-free outputs; revert to restore prior state with no migration/data change (the STOPPED-campaign data is untouched).
- **STOP / escalate:** any pressure to mutate a frozen dataclass/ID, edit/delete `cards/*.json`, touch the STOPPED DK tooling/`dataset_scope`, synthesize a placebo for a fail-closed field, add a dependency or paid data, or commit a `runs/`/data/secret artifact — surface to the user.

---
---

---

## ERRATA (coordinator review fix — mint HypothesisCard first)
Because AlphaSpec requires a HYPOTHESIS_CARD-kind `hypothesis_id`, the intake MUST mint (or accept) a **HypothesisCard FIRST**, then mint the AlphaSpec referencing its `hypothesis_id`. Reuse `governance/hypothesis_card.py`. `track_a_migration.py` (the card->canonical mapper) is in-scope here (allowed_paths) — or fold it into the intake module; either is acceptable.

