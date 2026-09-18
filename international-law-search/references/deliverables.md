# Deliverables

Use the shared source ledger as the single source of truth. Reader-facing and structured outputs must describe the same source records at the same export checkpoint. Deep-audit outputs additionally derive graph, coverage, and event details from canonical project state; quick and standard outputs do not require a graph or audit workspace.

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

## Separate substantive and retrieval gaps

A research gap must be stated by reviewed literature or supported by the reviewed body of sources. A retrieval gap records an unsearched or inaccessible language, platform, period, jurisdiction, source class, or branch. Never convert a retrieval gap into a claim that the literature is silent.

Report the stopping reason accurately. A budget stop is `Paused—not saturated`, not evidence of saturation. Never claim exhaustive or comprehensive coverage.

## Traceability and export checks

Before export, run `$SKILL_ROOT/scripts/validate_reader_report.py REPORT --language LANGUAGE --final`. It deterministically rejects unresolved template markers, unresolved manual-review items, declared synthesis without source citations, and a Chinese report that opens with machine-state sections. It does not judge legal correctness.

In deep-audit mode, also run `$SKILL_ROOT/scripts/validate_corpus.py` with `--sources` and, when graph data is enabled, the applicable edge input at the exact canonical checkpoint. Schema validation alone is not sufficient because it cannot enforce corpus-wide identity, endpoint, relationship, and retrieval-link invariants. Do not export while an applicable validator reports an error.

Before delivery, confirm that:

1. Every reported source resolves to one ledger or canonical source record.
2. Every description is supported by the recorded description basis and actual review extent.
3. Every declared source statement, multi-source trend, and cautious inference cites its supporting source IDs.
4. Availability, review extent, scope, gaps, and stopping reason match the export checkpoint.
5. All selected formats were generated from that same checkpoint.
6. Any optional relationship shown in a deep-audit attachment retains its endpoints, relation, status, and evidence location.
