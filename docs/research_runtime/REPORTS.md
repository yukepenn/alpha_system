# Runtime Reports

`alpha_system.runtime.reports` provides `RuntimeReportCard`, a deterministic
Markdown renderer for existing Research Runtime contract objects. It is a
presentation layer only: it consumes already-built summaries, diagnostics
reports, cost-sensitivity reports, rejection records, evidence drafts, and
reference handoffs through their value-free payloads.

## Renderer

Use `RuntimeReportCard().render(obj)` or `render_runtime_report_card(obj)` for
one object. Use `RuntimeReportCard().render_many([...])` for a small bundle.

The renderer accepts objects that expose `to_dict()`, mappings with the same
shape, and the lightweight `RuntimeRunSummary` helper. It does not compute
diagnostics, probe fills, cost stress, grid outcomes, evidence contents, or
handoff eligibility.

Rendered cards include only:

- statuses and next required gates;
- run, report, draft, handoff, manifest, version, and hash refs;
- scalar coverage, quality, label, and cost summaries;
- visible rejection reasons;
- artifact ids and content hashes, without local heavy file locations;
- limitations, normalized when upstream no-claim text would repeat banned
  wording.

## Language Rules

Report cards are descriptive only. They can say what status was recorded, what
coverage is available, what cost sensitivity was summarized, what reasons are
visible, and what gate remains next.

They must not turn a diagnostics pass into validation, a signal probe into a
runtime use decision, a bounded grid into advancement, an evidence draft into a
candidate, or a reference handoff into Reference validation. The most advanced
survivor state remains `REFERENCE_HANDOFF_READY`.

The renderer guards final Markdown against prohibited MVP state strings,
claim-oriented phrases, and raw/heavy data markers. If an input would force
those terms into the rendered card, rendering fails or the limitation text is
normalized to a neutral no-claim note.

## Local-Only Posture

Runtime report cards are intended for compact source-controlled summaries and
docs examples. Full report bundles, if a later workflow emits them, remain
local-only under the runtime artifact policy. They must not be committed when
they contain raw provider payloads, materialized feature/label values, local
DBs, logs, caches, or heavy formats.

The renderer performs no provider call, no data read, no broker action, no
paper/live operation, and no filesystem write.

## Templates

Template files live under `docs/research_runtime/templates/`:

- `runtime_report_card.md` for generic run-level cards;
- `diagnostics_report_card.md` for factor, label, split, cross-market, and cost
  diagnostics cards;
- `evidence_draft_card.md` for evidence draft summaries;
- `reference_handoff_card.md` for reference handoff package summaries.

Rendered scaffolds live under `docs/research_runtime/report_cards/`. They are
tiny examples only and contain no runtime values, provider rows, or heavy
artifact paths.
