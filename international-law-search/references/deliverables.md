# Deliverables

Use one validated round bundle as the single rendering checkpoint. Its source and claim selections resolve against the canonical ledgers, so reader-facing and structured outputs describe the same source set, current claims, round, budget, gaps, and next-round options. Deep-audit outputs additionally derive graph, coverage, and event details from canonical project state; quick and standard outputs do not require a graph or audit workspace.

## Default round artifact set

After every completed main or side round in Standard or Deep-audit mode, run `scripts/render_research_outputs.py` and publish all of the following from the same validated bundle:

- an **immutable round report** at `reports/<round-id>.md`;
- an immutable round presentation at `presentations/rounds/<round-id>.html`;
- a versioned **living synthesis** at `synthesis/synthesis-<checkpoint-id>.md` and the current pointer at `synthesis/current-synthesis.md`;
- a versioned static presentation at `presentations/versions/<checkpoint-id>.html` and the project hub at `presentations/index.html`; and
- the current `exports/bibliography.csv`.

The HTML must be a self-contained static file with embedded CSS, semantic headings, accessible tables, print rules, and no remote fonts, scripts, stylesheets, images, or other network-loaded assets. It may contain ordinary stable source hyperlinks. Generation must never open a browser automatically.

Quick mode renders this durable set only when the user asks for a durable report or upgrades the project. A later upgrade uses the existing ledgers and checkpoint history; it does not discard the quick result. The rendering script accepts only a completed round and writes all files through a sibling staging directory. It publishes immutable versions first and updates `current-synthesis.md` and `index.html` last. A validation or preflight failure must leave the last valid current files unchanged.

The bibliography CSV columns are stable source key, citation, type, language, scholarly importance, acquisition priority, availability, review extent, reading priority, stable links, and round membership. Do not add local paths, private-note identifiers, raw retrieval logs, or non-externalizable acquisition data.

## Confirm the user's output choices

Offer a reader-facing result in Word, Markdown, or HTML. Support OSCOLA, Bluebook, Chicago, and GB/T 7714 citation styles, plus a user-supplied style. Preserve normalized citations and stable links regardless of style.

The user may order material by theme, chronology, authority, relevance, reading priority, scholarly position, or source type. Default to **theme plus reading priority**, adding a timeline only when chronology materially helps understanding. Keep the main result concise enough for human review.

Offer, rather than automatically attach, structured files such as CSV or XLSX bibliography tables, BibTeX, RIS, JSONL, retrieval logs, validation results, graph data, and project state. The user's requested format controls delivery; mode alone does not force machine attachments.

## Choose the reader-facing product

### Retrieval archive

A retrieval archive organizes and describes sources individually. It may group sources by theme, source type, chronology, or discovery path, but it must not infer a shared trend, reconcile positions, identify a substantive literature gap from absence in the search, or provide cross-source synthesis.

For each selected source, explain in natural language:

- what the source addresses;
- why it is included;
- when the user should read it;
- its normalized citation and stable link;
- its reader-facing availability and actual review extent; and
- its stable source ID outside the opening sections.

### Research report

A research report may provide **source-grounded descriptive synthesis** of material actually reviewed. Lead with field understanding in this order: problem definition, research development, and principal positions or disputes. Put the recommended reading path before retrieval coverage and limitations. Keep source IDs, machine enums, validation state, and graph mechanics out of the opening.

The report must distinguish three statement types:

1. A source statement says what one identified source expresses.
2. A multi-source trend states only a pattern supported by every cited source.
3. A cautious inference identifies the assistant's limited inference and its evidentiary basis.

Give each such statement inline stable source citations. Do not use an abstract to characterize a full argument, and do not use metadata alone to describe a source's position. Do not present a dispute as settled, choose the user's thesis or argumentative position, synthesize an unsupported legal rule, or draft argumentative academic prose.

Use [`../templates/reader-report.md`](../templates/reader-report.md) for the paired research-report and retrieval-archive structures.

## Mixed requests

When the user requests an allowed research report together with thesis selection
or argumentative ghostwriting, accept the report portion and state the boundary
briefly. Offer neutral argument paths with their respective evidence and
limitations, but make clear that the user chooses the position. Do not reject
the entire request merely because one requested component crosses the boundary.

## Separate substantive and retrieval gaps

A research gap must be stated by reviewed literature or supported by the reviewed body of sources. A retrieval gap records an unsearched or inaccessible language, platform, period, jurisdiction, source class, or branch. Never convert a retrieval gap into a claim that the literature is silent.

Report the stopping reason accurately. A budget stop is `Paused—not saturated`, not evidence of saturation. Never claim exhaustive or comprehensive coverage.

## Traceability and export checks

Treat an external query, outbound log, subagent payload, and reader-facing
delivery as an export. Before any such action, create a JSONL or Markdown
manifest containing the exact outbound text, identifiers, and links. Each
JSONL item must declare `privacy_classification: public_citation_extract` for
published citation material or `privacy_classification: public_research_output`
for reader-facing prose derived only from externalizable public sources, plus
`externalizable: true`. A Markdown manifest must declare the applicable public
classification and `externalizable: true` in opening YAML-style front matter.
For Word or HTML, validate a JSONL or Markdown representation containing every
outward-facing text and link field.

Run `$SKILL_ROOT/scripts/validate_export_manifest.py MANIFEST` before the
outbound action. It rejects missing privacy declarations,
`private_note_reference`, `externalizable=false`, `file://` URIs, and absolute
local paths. Do not export when it reports an error, and do not weaken or omit
the manifest to obtain a passing result.

Before export, run `$SKILL_ROOT/scripts/validate_reader_report.py REPORT --language LANGUAGE --final`. It deterministically rejects unresolved template markers, unresolved manual-review items, declared synthesis without source citations, and a Chinese report that opens with machine-state sections. It does not judge legal correctness.

For a v3 checkpoint, first run `scripts/validate_source_ledger.py`,
`scripts/validate_claim_ledger.py`, and `scripts/validate_round_bundle.py`.
Rendering and export may proceed only when all applicable validators pass and
all selected formats come from that same checkpoint.

In deep-audit mode, also run `$SKILL_ROOT/scripts/validate_corpus.py` with `--sources` and, when graph data is enabled, the applicable edge input at the exact canonical checkpoint. Schema validation alone is not sufficient because it cannot enforce corpus-wide identity, endpoint, relationship, and retrieval-link invariants. Do not export while an applicable validator reports an error.

Before delivery, confirm that:

1. Every reported source resolves to one ledger or canonical source record.
2. Every description is supported by the recorded description basis and actual review extent.
3. Every declared source statement, multi-source trend, and cautious inference cites its supporting source IDs.
4. Availability, review extent, scope, gaps, and stopping reason match the export checkpoint.
5. All selected formats were generated from that same checkpoint.
6. Any optional relationship shown in a deep-audit attachment retains its endpoints, relation, status, and evidence location.
